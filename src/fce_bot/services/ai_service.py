"""AI Assistant Service for natural language transit Q&A and trip planning."""

import logging
import re
from typing import Optional, Dict, Any, Tuple
import requests

from fce_bot.config import settings
from fce_bot.core.models import AIQueryResponse, TransportType, FilterType
from fce_bot.services.transit_service import transit_service
from fce_bot.services.documents_service import documents_service
from fce_bot.data.db import get_db, normalize_stop_name

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Sei l'assistente virtuale ufficiale della Ferrovia Circumetnea (FCE) e Metropolitana di Catania.
Il tuo compito è aiutare i viaggiatori a pianificare i loro spostamenti, indicando gli orari corretti, le fermate di partenza e arrivo e le informazioni su biglietti e linee.
REGOLE FONDAMENTALI DI RISPOSTA:
1. Rispondi sempre in lingua italiana, in modo cordiale, chiaro e naturale.
2. NON usare link markdown grezzi come [titolo](url) e non inserire URL completi o sintassi con parentesi quadre/tonde.
3. Se l'utente chiede informazioni su orari completi o documenti, dì semplicemente: "Puoi consultare e scaricare gli orari aggiornati ufficiali nella sezione dedicata in questa pagina o sul sito circumetnea.it".
4. Per i biglietti, indica che si possono acquistare nelle stazioni, alle emettitrici automatiche della metropolitana, nelle rivendite autorizzate (tabaccherie/edicole) e online tramite l'app ufficiale FCE o DropTicket.
5. Evita sintassi markdown complessa o asterischi multipli sparsi.
6. Basa le indicazioni di viaggio esclusivamente sui dati ufficiali indicati nel contesto.
"""


class ExtractedEntities(tuple):
    """Backwards-compatible tuple representing extracted query components.
    
    Can be unpacked as 4 items: (origin, destination, time, transport_type)
    or accessed with properties .origin, .destination, .time, .transport_type, .filter_type.
    """
    def __new__(cls, origin, destination, time_val, ttype, ftype=FilterType.DEPARTURE_AFTER):
        return super().__new__(cls, (origin, destination, time_val, ttype))

    def __init__(self, origin, destination, time_val, ttype, ftype=FilterType.DEPARTURE_AFTER):
        self.origin = origin
        self.destination = destination
        self.time = time_val
        self.transport_type = ttype
        self.filter_type = ftype


class AIService:
    """Natural Language processing and LLM-assisted trip advisor."""

    def __init__(self):
        self._all_stop_names_cache = None

    def _get_known_stops(self) -> list:
        if self._all_stop_names_cache is None:
            try:
                with get_db() as conn:
                    cur = conn.cursor()
                    rows = cur.execute("SELECT DISTINCT stop_name, normalized_name FROM stops").fetchall()
                    self._all_stop_names_cache = [(r["stop_name"], r["normalized_name"]) for r in rows]
            except Exception:
                self._all_stop_names_cache = []
        return self._all_stop_names_cache

    def _clean_entity(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return None
        c = name.strip()
        c = re.sub(r"^(?:stazione\s+di|fermata\s+di|stazione|fermata|comune\s+di|la\s+città\s+di)\s+", "", c, flags=re.I)
        c = re.sub(r"\s+(?:per\s+le|entro\s+le|alle|verso\s+le|verso|ore|domani|oggi|dopo|prima).*$", "", c, flags=re.I)
        c = re.sub(r"[\?\.!,;:]+$", "", c)
        return c.strip() or None

    def _map_query_with_llm(self, text: str) -> dict:
        """Generalized semantic mapper: calls Gemini to extract origin, destination, time, intent, and transport mode."""
        if not settings.GEMINI_API_KEY:
            return {}
        try:
            import json
            api_key = settings.GEMINI_API_KEY
            model = settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            prompt = (
                f"Sei l'assistente semantico ufficiale della Ferrovia Circumetnea e Metropolitana di Catania.\n"
                f"Analizza la richiesta dell'utente: \"{text}\"\n\n"
                "Estrai le informazioni di viaggio in formato JSON con questa struttura esatta:\n"
                "{\n"
                "  \"origin\": \"comune o stazione di partenza (oppure null se assente o domanda generica)\",\n"
                "  \"destination\": \"comune o stazione di arrivo (oppure null)\",\n"
                "  \"time\": \"orario specificato in formato HH:MM (es. 15:00) oppure null\",\n"
                "  \"is_arrival_time\": true se l'orario indicato è l'orario desiderato di arrivo (es. 'arrivare per le 15', 'essere a ... entro le 15'), false se è orario di partenza,\n"
                "  \"transport\": \"QUALSIASI\" | \"TRENO\" | \"METRO\" | \"BUS\",\n"
                "  \"is_general_info\": true se è una richiesta generale (es. acquisto biglietti, info pdf) senza itinerario specifico\n"
                "}"
            )
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.0, "maxOutputTokens": 200, "responseMimeType": "application/json"}
            }
            resp = requests.post(url, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                raw_json = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(raw_json)
        except Exception as e:
            logger.debug("LLM semantic extraction error: %s", e)
        return {}

    def _extract_rule_based(self, text: str) -> ExtractedEntities:
        """Deterministic rule-based parser used as offline fallback."""
        origin = None
        destination = None
        dep_time = None
        ttype = TransportType.QUALSIASI

        # 1. Detect transport type
        lower_text = text.lower()
        if "metro" in lower_text or "metropolitana" in lower_text:
            ttype = TransportType.METRO
        elif "treno" in lower_text or "littorina" in lower_text or "ferrovia" in lower_text:
            ttype = TransportType.TRENO
        elif "bus" in lower_text or "autobus" in lower_text or "pullman" in lower_text or "navetta" in lower_text or "autolinee" in lower_text:
            ttype = TransportType.BUS

        # 2. Detect arrival vs departure intent
        is_arrival = bool(re.search(
            r"\b(?:arrivare|arrivo|arrivando|essere\s+(?:a|ad)|entro\s+le|per\s+le|prima\s+delle)\b",
            text,
            re.IGNORECASE
        ))
        ftype = FilterType.ARRIVAL_BEFORE if is_arrival else FilterType.DEPARTURE_AFTER

        # 3. Extract time
        time_match = re.search(
            r"\b(?:alle\s+|verso\s+le\s+|entro\s+le\s+|per\s+le\s+|prima\s+delle\s+|dopo\s+le\s+|intorno\s+alle\s+|ore\s+)?([0-1]?[0-9]|2[0-3])[:.]([0-5][0-9])\b",
            text,
            re.IGNORECASE
        )
        if time_match:
            h, m = time_match.group(1), time_match.group(2)
            dep_time = f"{int(h):02d}:{int(m):02d}"
        else:
            hour_match = re.search(
                r"\b(?:alle\s+|verso\s+le\s+|entro\s+le\s+|per\s+le\s+|prima\s+delle\s+|dopo\s+le\s+|intorno\s+alle\s+|ore\s+)([0-1]?[0-9]|2[0-3])\b",
                text,
                re.IGNORECASE
            )
            if hour_match:
                h = hour_match.group(1)
                dep_time = f"{int(h):02d}:00"

        # 4. Patterns
        pat1 = re.search(
            r"\bda\s+([\w\'\s]+?)\s+(?:a|ad|verso|per)\s+([\w\'\s]+?)(?:\s+(?:alle|verso|entro|per\s+le|prima\s+delle|dopo|ore|domani|oggi|in|con|che)|\?|\.|$)",
            text,
            re.IGNORECASE
        )
        if pat1:
            origin = self._clean_entity(pat1.group(1))
            destination = self._clean_entity(pat1.group(2))

        if not origin or not destination:
            pat2 = re.search(
                r"\b(?:per|ad|a|verso)\s+([\w\'\s]+?)\s+(?:da|partendo\s+da)\s+([\w\'\s]+?)(?:\s+(?:alle|verso|entro|per\s+le|prima\s+delle|dopo|ore|domani|oggi|in|con|che)|\?|\.|$)",
                text,
                re.IGNORECASE
            )
            if pat2:
                destination = self._clean_entity(pat2.group(1))
                origin = self._clean_entity(pat2.group(2))

        if not origin or not destination:
            pat3 = re.search(
                r"([\w\'\s]+?)\s*[-–>]\s*([\w\'\s]+?)(?:\s+(?:alle|verso|entro|per\s+le|prima\s+delle|dopo|ore|domani|oggi)|\?|\.|$)",
                text
            )
            if pat3:
                origin = self._clean_entity(pat3.group(1))
                destination = self._clean_entity(pat3.group(2))

        # Dictionary matching fallback
        if not origin or not destination:
            found_stops = []
            norm_text = normalize_stop_name(text)
            for sname, norm_sname in self._get_known_stops():
                if len(norm_sname) >= 4 and f" {norm_sname} " in f" {norm_text} ":
                    if sname not in found_stops:
                        found_stops.append(sname)
            if len(found_stops) >= 2:
                if not origin:
                    origin = found_stops[0]
                if not destination:
                    destination = found_stops[1]

        return ExtractedEntities(origin, destination, dep_time, ttype, ftype)

    def extract_entities(self, text: str) -> ExtractedEntities:
        """Extract origin, destination, time, transport type and filter type from freeform text.
        
        Generalizes entity extraction using an intermediate LLM semantic parser when available,
        falling back to deterministic rule-based parsing if offline or unconfigured.
        """
        # 1. Primary generalized intermediate mapping via Gemini
        if settings.GEMINI_API_KEY:
            llm_data = self._map_query_with_llm(text)
            if llm_data:
                orig = self._clean_entity(llm_data.get("origin"))
                dest = self._clean_entity(llm_data.get("destination"))
                time_val = llm_data.get("time")
                is_arr = bool(llm_data.get("is_arrival_time"))
                ftype = FilterType.ARRIVAL_BEFORE if is_arr else FilterType.DEPARTURE_AFTER
                raw_t = llm_data.get("transport") or "QUALSIASI"
                ttype = TransportType.from_str(str(raw_t))
                if orig or dest or llm_data.get("is_general_info"):
                    return ExtractedEntities(orig, dest, time_val, ttype, ftype)

        # 2. Rule-based / dictionary fallback
        return self._extract_rule_based(text)

    def answer_query(self, user_question: str) -> AIQueryResponse:
        """Process user natural language query and formulate response."""
        entities = self.extract_entities(user_question)
        origin = entities.origin
        destination = entities.destination
        target_time = entities.time or "08:00"
        ttype = entities.transport_type
        ftype = entities.filter_type

        itineraries = []
        if origin and destination:
            itineraries = transit_service.find_trips(
                origin=origin,
                destination=destination,
                target_time=target_time,
                transport_type=ttype,
                filter_type=ftype,
                limit=5
            )
            # If no trips found with ARRIVAL_BEFORE, attempt DEPARTURE_AFTER as fallback
            if not itineraries and ftype == FilterType.ARRIVAL_BEFORE:
                itineraries = transit_service.find_trips(
                    origin=origin,
                    destination=destination,
                    target_time=target_time,
                    transport_type=ttype,
                    filter_type=FilterType.DEPARTURE_AFTER,
                    limit=5
                )

        # Build context for LLM or rule-based answering
        docs = documents_service.get_documents()

        # Try Gemini if API key configured
        if settings.GEMINI_API_KEY:
            try:
                llm_answer = self._call_gemini(
                    question=user_question,
                    origin=origin,
                    destination=destination,
                    target_time=target_time,
                    filter_type=ftype,
                    itineraries=itineraries,
                    docs=docs
                )
                if llm_answer:
                    return AIQueryResponse(
                        answer=llm_answer,
                        origin=origin,
                        destination=destination,
                        time=target_time,
                        itineraries_count=len(itineraries),
                        itineraries=[
                            {
                                "departure": it.departure_time,
                                "arrival": it.arrival_time,
                                "from": it.departure_stop,
                                "to": it.arrival_stop,
                                "direct": it.is_direct
                            }
                            for it in itineraries
                        ]
                    )
            except Exception as e:
                logger.error("Gemini call failed: %s, falling back to rule-based response", e)

        # Fallback rule-based answering
        answer = self._generate_rule_based_answer(
            user_question=user_question,
            origin=origin,
            destination=destination,
            target_time=target_time,
            filter_type=ftype,
            itineraries=itineraries,
            docs=docs
        )

        return AIQueryResponse(
            answer=answer,
            origin=origin,
            destination=destination,
            time=target_time,
            itineraries_count=len(itineraries),
            itineraries=[
                {
                    "departure": it.departure_time,
                    "arrival": it.arrival_time,
                    "from": it.departure_stop,
                    "to": it.arrival_stop,
                    "direct": it.is_direct
                }
                for it in itineraries
            ]
        )

    def _generate_rule_based_answer(
        self,
        user_question: str,
        origin: Optional[str],
        destination: Optional[str],
        target_time: str,
        filter_type: FilterType,
        itineraries: list,
        docs: Any
    ) -> str:
        """Fallback response generator providing clean text without broken markdown."""
        q_low = user_question.lower()

        # 1. Documents / PDF query
        if any(w in q_low for w in ["documenti", "pdf", "scarica", "tabella orari", "orario metro", "orario treni", "orario bus"]):
            return (
                "Puoi consultare e scaricare gli orari aggiornati ufficiali di Metropolitana, Treni di superficie e Autolinee Bus direttamente nella sezione 'Orari Ufficiali in PDF' in fondo alla pagina.\n\n"
                "Se desideri cercare una corsa specifica, puoi anche indicarmi la partenza, la destinazione e l'orario desiderato!"
            )

        # 2. Tickets query
        if any(w in q_low for w in ["bigliett", "ticket", "abbonament", "compra", "acquist", "tariffe", "costo"]):
            return (
                "I biglietti e gli abbonamenti della Ferrovia Circumetnea e della Metropolitana di Catania sono acquistabili:\n\n"
                "• Presso le biglietterie di stazione e le rivendite autorizzate (tabacchi ed edicole convenzionate).\n"
                "• Alle emettitrici automatiche attive in tutte le stazioni della metropolitana.\n"
                "• Tramite smartphone con l'app ufficiale FCE Catania o l'app DropTicket.\n"
                "• A bordo per le corse dei bus extraurbani (ove previsto).\n\n"
                "Puoi consultare e scaricare gli orari aggiornati ufficiali nella sezione dedicata in questa pagina."
            )

        # 3. No route query
        if not origin or not destination:
            return (
                "👋 Ciao! Sono l'assistente per la mobilità della Ferrovia Circumetnea e Metropolitana di Catania.\n\n"
                "Puoi chiedermi orari e percorsi scrivendo ad esempio:\n"
                "• Come vado da Catania a Bronte verso le 14:00?\n"
                "• Orari dei treni da Randazzo a Paternò\n"
                "• Metro da Monte Po a Stesicoro alle 09:30\n\n"
                "Dimmi pure: da dove vuoi partire e dove desideri arrivare?"
            )

        # 4. Route not found
        if not itineraries:
            desc = f"con arrivo entro le ore {target_time}" if filter_type == FilterType.ARRIVAL_BEFORE else f"a partire dalle ore {target_time}"
            return (
                f"Non ho trovato corse dirette o con cambio immediato da {origin} a {destination} {desc}.\n\n"
                "Suggerimenti:\n"
                "• Prova a modificare l'orario o verifica il nome esatto della fermata.\n"
                "• Puoi consultare e scaricare gli orari aggiornati ufficiali nella sezione dedicata in questa pagina."
            )

        # 5. Itineraries found
        desc = f"con arrivo entro le ore {target_time}" if filter_type == FilterType.ARRIVAL_BEFORE else f"a partire dalle ore {target_time}"
        lines = [
            f"Ho trovato {len(itineraries)} soluzioni da {origin} a {destination} {desc}:\n"
        ]
        for idx, it in enumerate(itineraries[:4], 1):
            lines.append(f"{idx}. {it.format_clean()}")

        lines.append("\nPuoi consultare e scaricare gli orari aggiornati ufficiali nella sezione 'Orari Ufficiali in PDF' in questa pagina.")
        return "\n".join(lines)

    def _call_gemini(
        self,
        question: str,
        origin: Optional[str],
        destination: Optional[str],
        target_time: str,
        filter_type: FilterType,
        itineraries: list,
        docs: Any
    ) -> Optional[str]:
        """Call Google Gemini (gemini-3.5-flash-lite) API via standard REST endpoint."""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return None

        # Build clean schedule context without Telegram asterisks
        schedule_ctx = ""
        if itineraries:
            schedule_ctx = "ORARI TROVATI DAL DATABASE GTFS:\n"
            for it in itineraries:
                schedule_ctx += it.format_clean() + "\n"
        else:
            schedule_ctx = "Nessuna corsa trovata dal database per i criteri specificati."

        criteria_str = f"Arrivo richiesto entro le {target_time}" if filter_type == FilterType.ARRIVAL_BEFORE else f"Partenza richiesta a partire dalle ore {target_time}"

        prompt = f"""Domanda del passeggero: "{question}"
Origine individuata: {origin or 'Non specificata'}
Destinazione individuata: {destination or 'Non specificata'}
Criterio orario: {criteria_str}

{schedule_ctx}

Linee guida per la risposta:
- Rispondi in italiano con tono cordiale, chiaro e conciso.
- NON inserire URL completi, link markdown grezzi come [testo](url), né sintassi con parentesi quadre/tonde.
- Se opportuno, puoi ricordare che il passeggero può consultare e scaricare gli orari aggiornati ufficiali nella sezione dedicata in questa pagina.
- Se l'utente chiede dove acquistare biglietti, spiega che sono acquistabili presso le stazioni, le rivendite autorizzate, le emettitrici automatiche della metro e online tramite app FCE o DropTicket.
"""

        model = settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]}
            ],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800}
        }
        resp = requests.post(url, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            logger.warning("Gemini API error (%d): %s", resp.status_code, resp.text[:200])

        return None


ai_service = AIService()

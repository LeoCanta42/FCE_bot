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
Il tuo compito è aiutare i viaggiatori a pianificare i loro spostamenti, indicando gli orari corretti, le fermate di partenza e arrivo, i cambi necessari e i documenti utili.
Rispondi sempre in italiano, in modo cordiale, chiaro e conciso.
Basa le tue risposte ESCLUSIVAMENTE sui dati ufficiali forniti nel contesto. Se un percorso o un orario non è disponibile, dillo con chiarezza e suggerisci un'alternativa se possibile.
Usa emoji di trasporto appropriate (🚌 bus, 🚆 treno, 🚇 metro, ⏱ durata, 📍 partenza, 🏁 arrivo).
"""


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

    def extract_entities(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str], TransportType]:
        """Extract origin, destination, time, and transport type from freeform text."""
        origin = None
        destination = None
        dep_time = None
        ttype = TransportType.QUALSIASI

        # Detect transport type
        lower_text = text.lower()
        if "metro" in lower_text or "metropolitana" in lower_text:
            ttype = TransportType.METRO
        elif "treno" in lower_text or "littorina" in lower_text or "ferrovia" in lower_text:
            ttype = TransportType.TRENO
        elif "bus" in lower_text or "autobus" in lower_text or "pullman" in lower_text or "navetta" in lower_text:
            ttype = TransportType.BUS

        # Extract time (e.g. 14:30, 8.00, alle 9, verso le 15, 17)
        time_match = re.search(r"\b(?:alle\s+|verso\s+le\s+|ore\s+)?([0-1]?[0-9]|2[0-3])[:.]([0-5][0-9])\b", text, re.IGNORECASE)
        if time_match:
            h, m = time_match.group(1), time_match.group(2)
            dep_time = f"{int(h):02d}:{int(m):02d}"
        else:
            hour_match = re.search(r"\b(?:alle\s+|verso\s+le\s+|ore\s+)([0-1]?[0-9]|2[0-3])\b", text, re.IGNORECASE)
            if hour_match:
                h = hour_match.group(1)
                dep_time = f"{int(h):02d}:00"

        # Regex patterns for Italian travel queries:
        # e.g., "da Catania a Bronte", "per Adrano da Paternò", "Catania - Randazzo"
        pat1 = re.search(r"\bda\s+([A-Za-z0-9'\s]+?)\s+(?:a|per)\s+([A-Za-z0-9'\s]+?)(?:\s+(?:alle|verso|ore|domani|oggi|in|con)|$)", text, re.IGNORECASE)
        if pat1:
            origin = pat1.group(1).strip()
            destination = pat1.group(2).strip()
        else:
            pat2 = re.search(r"\bper\s+([A-Za-z0-9'\s]+?)\s+da\s+([A-Za-z0-9'\s]+?)(?:\s+(?:alle|verso|ore|domani|oggi|in|con)|$)", text, re.IGNORECASE)
            if pat2:
                destination = pat2.group(1).strip()
                origin = pat2.group(2).strip()
            else:
                pat3 = re.search(r"([A-Za-z0-9'\s]+?)\s*[-–>]\s*([A-Za-z0-9'\s]+)", text)
                if pat3:
                    origin = pat3.group(1).strip()
                    destination = pat3.group(2).strip()

        # If origin/destination still not matched, scan against known stations
        if not origin or not destination:
            found_stops = []
            norm_text = normalize_stop_name(text)
            for sname, norm_sname in self._get_known_stops():
                # Avoid single letter / common words matches
                if len(norm_sname) >= 4 and norm_sname in norm_text:
                    if sname not in found_stops:
                        found_stops.append(sname)
            if len(found_stops) >= 2:
                if not origin:
                    origin = found_stops[0]
                if not destination:
                    destination = found_stops[1]

        return origin, destination, dep_time, ttype

    def answer_query(self, user_question: str) -> AIQueryResponse:
        """Process user natural language query and formulate response."""
        origin, destination, time_str, ttype = self.extract_entities(user_question)
        target_time = time_str or "08:00"

        itineraries = []
        if origin and destination:
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
        itineraries: list,
        docs: Any
    ) -> str:
        """Fallback response generator when no external AI key is available."""
        # Check for general document or timetable request
        q_low = user_question.lower()
        if any(w in q_low for w in ["documenti", "pdf", "scarica", "tabella orari", "orario metro", "orario treni", "orario bus"]):
            return (
                "Ecco i link ufficiali per consultare e scaricare gli orari in formato PDF:\n\n"
                f"🚇 *Orario Metropolitana:*\n{docs.metro_url}\n\n"
                f"🚆 *Orario Treni Circumetnea (Superficie):*\n{docs.train_url}\n\n"
                f"🚌 *Orario Autolinee (Bus):*\n{docs.bus_url}\n\n"
                "Puoi anche chiedermi uno spostamento specifico, ad esempio: `da Catania a Randazzo alle 10:00`!"
            )

        if not origin or not destination:
            return (
                "👋 Ciao! Sono l'assistente per la mobilità della **Ferrovia Circumetnea**.\n\n"
                "Puoi chiedermi orari e percorsi semplicemente scrivendo ad esempio:\n"
                "• _Come vado da Catania a Bronte verso le 14:00?_\n"
                "• _Orario treni da Randazzo a Paternò_\n"
                "• _Metro da Monte Po a Stesicoro alle 09:30_\n\n"
                "Dimmi pure: da dove vuoi partire e dove devi arrivare?"
            )

        if not itineraries:
            return (
                f"Non ho trovato corse dirette o con cambio immediato da *{origin}* a *{destination}* a partire dalle ore *{target_time}*.\n\n"
                "💡 *Suggerimenti:*\n"
                "• Prova a specificare un orario diverso o controlla l'esatto nome della fermata (es. `Catania Borgo`, `Nesima`, `Paternò`).\n"
                "• Consulta i documenti ufficiali con il comando /documenti."
            )

        lines = [
            f"✅ Ho trovato {len(itineraries)} soluzioni da *{origin}* a *{destination}* a partire dalle *{target_time}*:\n"
        ]
        for idx, it in enumerate(itineraries[:4], 1):
            lines.append(f"{idx}. {it.format_telegram()}")

        lines.append("Puoi acquistare i biglietti urbani online tramite l'app ufficiale FCE o DropTicket. Buon viaggio!")
        return "\n".join(lines)

    def _call_gemini(
        self,
        question: str,
        origin: Optional[str],
        destination: Optional[str],
        target_time: str,
        itineraries: list,
        docs: Any
    ) -> Optional[str]:
        """Call Google Gemini (gemini-3.5-flash-lite) API via standard REST endpoint."""
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return None

        # Build schedule context
        schedule_ctx = ""
        if itineraries:
            schedule_ctx = "ORARI TROVATI DAL DATABASE GTFS:\n"
            for it in itineraries:
                schedule_ctx += it.format_telegram() + "\n"
        else:
            schedule_ctx = "Nessuna corsa trovata dal database per i criteri specificati."

        prompt = f"""Domanda dell'utente: "{question}"
Origine individuata: {origin or 'Non specificata'}
Destinazione individuata: {destination or 'Non specificata'}
Orario desiderato: {target_time}

{schedule_ctx}

DOCUMENTI UFFICIALI PDF DISPONIBILI:
- Metro: {docs.metro_url}
- Treni: {docs.train_url}
- Bus: {docs.bus_url}

Rispondi all'utente in modo chiaro, utile e conciso con tutte le informazioni rilevanti."""

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

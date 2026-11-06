# 🌋 Ferrovia Circumetnea (FCE) Bot & Transit API

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![PTB](https://img.shields.io/badge/python--telegram--bot-v20%2B%20(async)-2ca5e0.svg)](https://python-telegram-bot.org/)
[![Vercel Ready](https://img.shields.io/badge/Vercel-Serverless%20%26%20Cron-black.svg)](https://vercel.com/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

Un assistente di viaggio moderno, modulare e completo per la **Ferrovia Circumetnea (FCE)** e la **Metropolitana di Catania**.

Questo progetto è una riscrittura completa e architetturale del bot originale: ora utilizza i dati aperti ufficiali in formato standard **GTFS (General Transit Feed Specification)** pubblicati da FCE, integra feed **RSS 2.0** per le notizie e gli avvisi in tempo reale, offre un **assistente AI** in linguaggio naturale (compatibile con Google Gemini e OpenAI), include una **Web Dashboard / REST API** ed è nativamente deployabile come funzione serverless su **Vercel** o come container **Docker** su qualsiasi VPS.

---

## ✨ Principali Caratteristiche

* **🚍 Dati Ufficiali GTFS (2025–2028):**
  * Oltre 580 fermate, 760 corse giornaliere e 14.000+ passaggi orari ufficiali per **Metropolitana**, **Treni di Superficie (Littorine)** e **Autolinee (Bus)**.
  * *Zero dipendenze da CloudConvert o parsing manuale di Excel:* tutto viene sincronizzato e indicizzato nativamente in SQLite.
* **🤖 Assistente di Viaggio AI (Google Gemini):**
  * Basato sul modello Google **`gemini-3.5-flash-lite`** (configurabile tramite `GEMINI_API_KEY`).
  * L'utente può scrivere semplicemente:
    > *"Come posso andare da Catania a Bronte oggi alle 14:00?"*
    > *"Metro da Monte Po a Stesicoro verso le 9:00"*
  * L'assistente estrae origine, destinazione e orario, consulta il database GTFS e formula una risposta chiara ed accurata. Include un motore NLP integrato che funziona automaticamente anche se la chiave API non è ancora inserita.
* **📢 Notizie e Avvisi in Tempo Reale:**
  * Monitoraggio automatico del feed RSS ufficiale `https://www.circumetnea.it/category/news/feed/`.
  * Rilevamento univoco degli articoli e trasmissione automatica al canale Telegram o agli utenti iscritti.
* **🌐 Web Dashboard & REST API:**
  * Interfaccia web interattiva per consultare orari, testare l'AI e scaricare i PDF ufficiali direttamente dal browser.
  * Endpoint REST documentati con Swagger/OpenAPI (`/api/timetable`, `/api/stops`, `/api/news`, `/api/documents`, `/api/ai/ask`).
* **☁️ Deploy Ibrido (Vercel Serverless & Docker/VPS):**
  * **Vercel:** Modalità Telegram Webhook (`/api/webhook`) e Vercel Cron (`/api/cron/news`) senza server dedicati sempre accesi.
  * **Docker / VPS / Locale:** Modalità Long Polling tradizionale (`python main.py bot`).

---

## 🏗️ Architettura del Progetto

```
FCE_bot/
├── api/                          # Entry point per Vercel Serverless Functions
│   └── index.py                  # Inizializzazione FastAPI (Webhook, Cron, REST API)
├── src/
│   └── fce_bot/
│       ├── config.py             # Gestione impostazioni (.env e pydantic-settings)
│       ├── core/                 # Modelli di dominio Pydantic & Dataclass
│       │   └── models.py         # Stop, Trip, Itinerary, NewsItem, TransportType
│       ├── data/                 # Ingestione e persistenza dati
│       │   ├── db.py             # Schema SQLite, indici e transazioni
│       │   ├── gtfs_loader.py    # Download, estrazione e sincronizzazione GTFS
│       │   └── users_repo.py     # Gestione utenti e iscritti alle notifiche
│       ├── services/             # Business Logic
│       │   ├── transit_service.py# Motore orari (corse dirette e con 1 cambio)
│       │   ├── news_service.py   # Parser RSS e monitoraggio avvisi
│       │   ├── documents_service.py # Risolutore link ufficiali PDF (Metro, Treni, Bus)
│       │   └── ai_service.py     # Assistente AI e NLP per pianificazione viaggi
│       ├── bot/                  # Telegram Bot (python-telegram-bot v20+)
│       │   ├── bot_app.py        # Costruzione Application e registrazione handler
│       │   ├── keyb.py           # Tastiere inline paginate
│       │   └── handlers/         # Moduli: start, timetable, news, documents, ai_chat, admin
│       ├── api/
│       │   └── router.py         # Router FastAPI e dashboard web
│       └── cli.py                # Interfaccia a riga di comando
├── tests/                        # Suite di test automatizzati (Pytest)
├── Dockerfile                    # Containerizzazione multi-stage
├── docker-compose.yml            # Configurazione Docker Compose
├── vercel.json                   # Configurazione deploy Vercel e Vercel Cron
├── requirements.txt              # Dipendenze Python
└── pyproject.toml                # Standard modern packaging
```

---

## 🚀 Guida Rapida all'Avvio Locale

### 1. Prerequisiti e Installazione
Assicurati di avere Python 3.10 o successivo installato.

```bash
# Clona il repository
git clone https://github.com/LeoCanta42/FCE_bot.git
cd FCE_bot

# Crea ed attiva l'ambiente virtuale
python3 -m venv .venv
source .venv/bin/activate

# Installa le dipendenze
pip install -r requirements.txt
```

### 2. Configurazione delle Variabili d'Ambiente
Copia il file di esempio `.env.example` in `.env`:

```bash
cp .env.example .env
```

Modifica `.env` inserendo il tuo token Telegram e le impostazioni desiderate:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHANNEL_ID=@il_tuo_canale_notizie  # Opzionale
ADMIN_USER_IDS=123456789                    # Il tuo ID Telegram (ottienilo con /chat_id)

# Assistente AI (Google Gemini - gemini-3.5-flash-lite)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

### 3. Sincronizzazione Orari GTFS
Il database `fce_lines.db` è già pre-popolato nel repository con gli orari attuali. Puoi aggiornarlo in qualsiasi momento scaricando il pacchetto GTFS più recente:

```bash
python main.py sync-gtfs
```

### 4. Avvio dei Servizi

#### Modalità Bot Telegram (Long Polling):
```bash
python main.py bot
```

#### Modalità Web Dashboard & REST API:
```bash
python main.py serve --port 8000
```
Apri il browser su [http://localhost:8000](http://localhost:8000) per visualizzare l'interfaccia interattiva!

#### Esecuzione in Background con Script Sicuri:
```bash
# Avvia bot in background (con file PID sicuro e log in bot.log)
./restarter.sh start

# Verifica stato
./restarter.sh status

# Arresta
./restarter.sh stop
```

---

## ☁️ Deploy su Vercel (Serverless)

Il progetto è nativamente predisposto per essere distribuito su **Vercel**.

### Come funziona su Vercel:
1. **Webhook Telegram:** Invece del continuous polling (incompatibile con il serverless), Telegram invia ogni evento via HTTP POST a `/api/webhook`.
2. **Vercel Cron:** La verifica delle notizie viene eseguita periodicamente (es. ogni ora) invocando l'endpoint `/api/cron/news`.
3. **Database SQLite GTFS:** Il file `fce_lines.db` viene impacchettato direttamente nel bundle serverless e letto a velocità nativa (<1ms).

### Passaggi per il Deploy:
1. Installa la CLI di Vercel (oppure collega il repository su [vercel.com](https://vercel.com)):
   ```bash
   npm i -g vercel
   vercel
   ```
2. Nelle impostazioni del progetto su Vercel (**Settings -> Environment Variables**), inserisci:
   * `TELEGRAM_BOT_TOKEN`: Il token del tuo bot Telegram.
   * `WEBHOOK_URL`: `https://tuo-progetto.vercel.app/api/webhook`
   * `WEBHOOK_SECRET`: Una stringa casuale segreta a tua scelta.
   * `CRON_SECRET`: Una stringa segreta per proteggere l'endpoint Cron.
   * `AI_API_KEY`: La tua chiave Google Gemini o OpenAI (opzionale).
3. Configura il Webhook su Telegram effettuando una chiamata GET al bot:
   ```bash
   curl -F "url=https://tuo-progetto.vercel.app/api/webhook" \
        -F "secret_token=la_tua_chiave_webhook_secret" \
        https://api.telegram.org/bot<TUO_TOKEN>/setWebhook
   ```
4. Fatto! Il tuo bot risponderà istantaneamente e controllerà le notizie tramite Vercel Cron.

---

## 🐳 Deploy con Docker & Docker Compose

È incluso un `Dockerfile` multi-stage e un file `docker-compose.yml`.

```bash
# Avvia sia il bot Telegram che la Web Dashboard
docker-compose up -d

# Visualizza i log
docker-compose logs -f
```

---

## 🤖 Comandi Telegram Disponibili

| Comando | Descrizione |
|---|---|
| `/start` | Mostra il menu principale e inizializza la sessione |
| `/viaggio <origine> - <destinazione> [ora]` | Scorciatoia rapida per cercare orari senza pulsanti |
| `/fermate <query>` | Cerca fermate o stazioni della rete FCE |
| `/news` | Mostra le ultime 3 notizie/avvisi ufficiali Circumetnea |
| `/documenti` | Link diretti per scaricare i PDF ufficiali (Metro, Treni, Bus) |
| `/chat_id` | Mostra l'ID univoco della chat corrente |
| `/help` | Guida completa alle funzionalità |
| `/stats` *(Admin)* | Statistiche su utenti e database GTFS |
| `/sync_gtfs` *(Admin)* | Risincronizza il database scaricando i dati da circumetnea.it |
| `/broadcast <testo>` *(Admin)* | Invia un annuncio a tutti gli utenti iscritti |

---

## 🧪 Esecuzione dei Test

La suite di test verifica il corretto funzionamento di query GTFS, scraping notizie, estrazione entità AI ed endpoint API:

```bash
PYTHONPATH=.:src pytest -v
```

---

## 📄 Licenza
Rilasciato sotto licenza [GNU General Public License v3.0](LICENSE).

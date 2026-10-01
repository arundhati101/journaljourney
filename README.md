# JournalJourney

JournalJourney is a personal journaling app that uses AI. It brings together
full-stack web development, Natural Language Processing (NLP, which means
teaching a computer to read text), and a Large Language Model (LLM, a big AI
model that writes text). Users write diary entries. The app then sorts each
entry into a group, gives it a sentiment score, and adds a main emotion. The
app also draws mood trends, counts journaling streaks, makes word clouds, and
writes weekly AI reflections with Google Gemini.

> Final-year B.Tech project — Computer Science & Engineering.

---

## Table of Contents

1. [Key Features](#key-features)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [System Architecture](#system-architecture)
5. [Database Design (ER)](#database-design-er)
6. [NLP Pipeline](#nlp-pipeline)
7. [Model Evaluation](#model-evaluation-vader-vs-textblob)
8. [REST API](#rest-api)
9. [Application Routes](#application-routes)
10. [Requirements Specification](#requirements-specification)
11. [Installation & Setup](#installation--setup)
12. [Testing](#testing)
13. [Literature Review](#literature-review)
14. [Limitations & Future Scope](#limitations--future-scope)
15. [Author](#author)

---

## Key Features

| Area | Feature |
|------|---------|
| Auth | Registration, login, logout; Bcrypt password hashing; session-based access control; CSRF-protected forms |
| Journaling | Create, **edit**, delete entries; full-text search; user-specific private journals |
| NLP | Tokenisation, then stopword removal, then lemmatisation; keyword categorisation; **VADER** sentiment (label + compound score); **NRCLex** dominant-emotion detection |
| Tagging | User-supplied custom tags stored alongside the auto-category (enables auto-vs-manual comparison) |
| Analytics | Mood dashboard (Chart.js) with 7-/30-day trend + rolling average; emotion breakdown bar chart; **journaling streak counter** |
| Visualisation | Per-user **word cloud** image generated on the fly |
| AI Insights | Weekly 3-paragraph reflection via Google Gemini, cached 7 days, manual refresh |
| Export | Download all entries as **CSV** or **PDF** |
| API | JSON **REST API** (`/api/...`) over the same models for future SPA/mobile clients |
| Robustness | Custom 404/500 error pages; migration-safe schema upgrades; graceful degradation when the LLM key or optional libraries are absent |

---

## Technology Stack

- **Language:** Python 3.13
- **Backend:** Flask (application-factory pattern + Blueprints), Flask-SQLAlchemy, Flask-WTF, Flask-Bcrypt
- **Frontend:** Jinja2, HTML5, CSS3, Chart.js
- **NLP:** NLTK (VADER, tokeniser, WordNet lemmatiser, stopwords), NRCLex, TextBlob (for evaluation)
- **LLM:** Google Gemini (`gemini-2.5-flash`) via `google-genai`
- **Visualisation / Export:** wordcloud, matplotlib, reportlab
- **Database:** SQLite (dev) via SQLAlchemy ORM — swappable for PostgreSQL in production
- **Testing:** pytest (31 unit + integration tests)
- **Config:** python-dotenv, truststore

---

## Project Structure

```text
journaljourney/
├── run.py                     # entry point → create_app()
├── requirements.txt
├── pytest.ini
├── .env                       # SECRET_KEY, GEMINI_API_KEY (not committed)
│
├── backend/                   # ── all server-side code ──
│   ├── __init__.py            # app factory, blueprints, error handlers, migrations
│   ├── config.py              # Config / TestConfig
│   ├── models.py              # User, DiaryEntry, WeeklyInsight
│   ├── forms.py               # WTForms
│   ├── nlp.py                 # preprocessing, category, sentiment, emotion
│   ├── ai.py                  # Gemini weekly-insight generation
│   ├── services.py            # streak calculation, word-cloud rendering
│   ├── routes/
│   │   ├── auth.py            # signup / login / logout
│   │   ├── journal.py         # entries CRUD, edit, word cloud
│   │   ├── dashboard.py       # mood + emotion analytics
│   │   ├── insights.py        # AI insights + refresh
│   │   ├── export.py          # CSV / PDF export
│   │   └── api.py             # JSON REST API
│   └── evaluation/
│       └── nlp_comparison.py  # VADER vs TextBlob accuracy harness
│
├── frontend/                  # ── all client-side code ──
│   ├── templates/             # index, entries, edit, dashboard, insights,
│   │                          #   wordcloud, login, signup, error
│   └── static/                # styles1/2/3.css
│
├── tests/                     # pytest suite
│   ├── conftest.py            # fixtures (app, client, auth_client)
│   ├── test_nlp.py            # NLP + streak unit tests
│   ├── test_routes.py         # auth + CRUD integration tests
│   └── test_api.py            # REST API tests
│
└── instance/
    └── site.db                # SQLite database (auto-created)
```

The code is split clearly into **backend** and **frontend** parts. It also uses
the **application-factory + Blueprint** design. This keeps each job separate.
Examiners often ask for this instead of one large single file.

---

## System Architecture

```text
                         Browser (HTML/CSS/Chart.js)  ┐
                                                      │  JSON
                         ▼                            ▼
        ┌───────────────────────────────────────────────────────┐
        │                 Flask app (create_app)                 │
        │  Blueprints:                                           │
        │   auth · journal · dashboard · insights · export · api │
        └───────┬───────────────┬───────────────┬───────────────┘
                │               │               │
                ▼               ▼               ▼
          NLP module       services         ai module
          (nlp.py)         (services.py)    (ai.py)
           ├ tokenise       ├ streak          └ Google Gemini
           ├ lemmatise      └ word cloud         (google-genai)
           ├ categorise
           ├ VADER sentiment
           └ NRCLex emotion
                │
                ▼
        SQLAlchemy ORM  ──►  SQLite (site.db)  [→ PostgreSQL in prod]
```

---

## Database Design (ER)

```text
┌────────────┐         ┌──────────────────────┐        ┌────────────────┐
│   User     │ 1     * │     DiaryEntry        │        │ WeeklyInsight  │
├────────────┤────────>├──────────────────────┤        ├────────────────┤
│ id (PK)    │         │ id (PK)               │  * 1   │ id (PK)        │
│ username   │         │ text                  │<───────│ insight_text   │
│ password   │         │ category              │        │ generated_on   │
└────────────┘         │ sentiment             │        │ user_id (FK)   │
       │               │ sentiment_score       │        └────────────────┘
       │ 1           * │ emotion               │               ▲
       └───────────────│ tags                  │               │
                       │ timestamp             │        (User 1 ─ * WeeklyInsight)
                       │ user_id (FK)          │───────────────┘
                       └──────────────────────┘
```

- **User to DiaryEntry**: one-to-many
- **User to WeeklyInsight**: one-to-many
- Every query uses `user_id`. This keeps one user's data apart from another user's data.

Schema upgrades are **migration-safe** (safe to change over time). `create_all()`
builds tables that are missing. `ALTER TABLE` adds columns (`sentiment_score`,
`emotion`, `tags`) that came after the first database was made.

---

## NLP Pipeline

The app does the following for every entry, when you create it and when you edit it:

1. **Preprocess** — make text lowercase, run `word_tokenize`, drop items that are
   not letters or numbers, drop stopwords, and WordNet-lemmatise.
2. **Categorise** — score the lemmas against five keyword lexicons
   (Work, Health, Relationships, Personal Development, Hobbies); pick the max,
   defaulting to *Personal Development*.
3. **Sentiment** — VADER gives a compound score, then a label: Positive (≥ 0.05) /
   Negative (≤ −0.05) / Neutral. The raw score (−1…+1) is stored for trend charts.
4. **Emotion** — NRCLex maps words to Plutchik emotions. The app stores the
   strongest clear emotion (joy, fear, anger, sadness, trust, …). It skips the
   general positive/negative groups, because VADER already covers those.

---

## Model Evaluation (VADER vs TextBlob)

There is an evaluation harness (`backend/evaluation/nlp_comparison.py`). It runs
both models over a set of journal-style sentences that were labelled by hand:

```bash
python -m backend.evaluation.nlp_comparison
```

Result on the current 15-sentence set:

| Model | Overall accuracy | Positive | Neutral | Negative |
|-------|:---:|:---:|:---:|:---:|
| **VADER (NLTK)** | **100 %** (15/15) | 5/5 | 5/5 | 5/5 |
| TextBlob | 80 % (12/15) | 4/5 | 4/5 | 4/5 |

**Decision:** The app uses VADER in production. VADER is rule-based, so it needs
no training data. It is tuned for short, informal text. It also did better than
TextBlob on the journal-style test set. This shows the design choice with clear
proof, not just a guess. (The categoriser still uses simple keyword matching. See
[Future Scope](#limitations--future-scope) for the TF-IDF / BERT upgrade path.)

---

## REST API

This is a JSON API that uses the login session. It returns `401` when the user is
not logged in, instead of an HTML redirect. It is useful for a future
React/Flutter client.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/entries` | List the current user's entries |
| POST | `/api/entries` | Create an entry (`{"text": "...", "tags": "a,b"}`) — runs the full NLP pipeline |
| GET | `/api/entries/<id>` | Fetch a single entry |
| DELETE | `/api/entries/<id>` | Delete an entry |
| GET | `/api/stats` | Totals, average sentiment, streak, category & emotion distributions |

Example:

```bash
curl -X POST http://127.0.0.1:5000/api/entries \
     -H "Content-Type: application/json" \
     -d '{"text": "Tough day at work but I pushed through", "tags": "work"}'
```

---

## Application Routes

| Route | Method | Auth | Description |
|-------|--------|:---:|-------------|
| `/signup` | GET/POST | No | Create account |
| `/login` | GET/POST | No | Authenticate |
| `/logout` | GET | Yes | End session |
| `/` | GET/POST | Yes | Write entry (with streak, tags) |
| `/entries` | GET | Yes | List / search entries |
| `/edit_entry/<id>` | GET/POST | Yes | Edit an entry (re-runs NLP) |
| `/delete_entry/<id>` | POST | Yes | Delete an entry |
| `/dashboard` | GET | Yes | Mood and emotion dashboard |
| `/wordcloud`, `/wordcloud.png` | GET | Yes | Word-cloud page and image |
| `/insights`, `/insights/refresh` | GET/POST | Yes | AI weekly insight |
| `/export/csv`, `/export/pdf` | GET | Yes | Download entries |
| `/api/...` | Various | Yes | JSON REST API |

---

## Requirements Specification

### Functional Requirements

| # | Requirement |
|---|-------------|
| FR1 | The system shall allow a user to register with a unique username and password. |
| FR2 | The system shall authenticate users and maintain a session. |
| FR3 | The system shall let an authenticated user create, edit, search, and delete their own entries. |
| FR4 | The system shall automatically categorise each entry and compute its sentiment and dominant emotion. |
| FR5 | The system shall allow user-defined tags on entries. |
| FR6 | The system shall visualise mood trends and emotion distribution and compute a journaling streak. |
| FR7 | The system shall generate a weekly AI reflection and cache it for 7 days. |
| FR8 | The system shall export entries as CSV and PDF. |
| FR9 | The system shall expose a JSON REST API for entries and statistics. |
| FR10 | A user shall never be able to read or modify another user's entries. |

### Non-Functional Requirements

| # | Requirement |
|---|-------------|
| NFR1 | **Security** — passwords hashed with Bcrypt; forms CSRF-protected; secret key from environment. |
| NFR2 | **Portability** — runs on Windows/Linux/macOS; DB URL configurable (SQLite to PostgreSQL). |
| NFR3 | **Reliability** — migration-safe schema; graceful degradation when the LLM key or optional libs are missing. |
| NFR4 | **Maintainability** — modular backend/frontend split, Blueprints, 31 automated tests. |
| NFR5 | **Usability** — responsive, consistent themed UI with clear navigation. |
| NFR6 | **Performance** — AI insights cached weekly to minimise API cost and latency. |

---

## Installation & Setup

```bash
# 1. Clone and enter
git clone <repository-url>
cd journaljourney

# 2. Create & activate a virtual environment
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure secrets in .env  (never commit this file)
#    GEMINI_API_KEY=your_key_here          (from https://aistudio.google.com/apikey)
#    SECRET_KEY=a_long_random_string
#    DATABASE_URL=sqlite:///site.db         (optional; use a Postgres DSN in prod)

# 5. Run
python run.py
```

Then open <http://127.0.0.1:5000>. If `GEMINI_API_KEY` is missing, the app still
runs. Only the AI Insights page will say that the feature is not available.

---

## Testing

```bash
pytest            # 31 tests: NLP units, auth, CRUD, access control, REST API
```

The tests use an in-memory SQLite database (`TestConfig`) and Flask's test
client. This makes them fast, and they leave no files behind. The tests cover the
NLP functions, the streak algorithm, authentication, keeping each user's data
apart, entry editing, CSV export, error pages, and every API endpoint.

---

## Literature Review

1. Hutto, C.J. & Gilbert, E. (2014). *VADER: A Parsimonious Rule-based Model for
   Sentiment Analysis of Social Media Text.* ICWSM. — basis for the sentiment engine.
2. Mohammad, S. & Turney, P. (2013). *Crowdsourcing a Word–Emotion Association
   Lexicon (NRC).* Computational Intelligence. — basis for NRCLex emotion detection.
3. Pennebaker, J.W. (1997). *Writing about Emotional Experiences as a Therapeutic
   Process.* Psychological Science. — evidence for the mental-health value of journaling.
4. Loria, S. (2018). *TextBlob: Simplified Text Processing.* — baseline compared against VADER.
5. Devlin, J. et al. (2019). *BERT: Pre-training of Deep Bidirectional Transformers
   for Language Understanding.* NAACL. — proposed future upgrade for categorisation.
6. Bird, S., Klein, E. & Loper, E. (2009). *Natural Language Processing with Python
   (NLTK).* O'Reilly. — toolkit underpinning the preprocessing pipeline.
7. Grinberg, M. (2018). *Flask Web Development, 2nd ed.* O'Reilly. — application-factory
   and Blueprint patterns used here.

---

## Limitations & Future Scope

**Current limitations**

- The categoriser uses **naive keyword matching**. So an entry with no lexicon
  words defaults to *Personal Development*.
- SQLite allows only one writer at a time. This is fine for a demo, but not for
  many users at once.
- Emotion detection is lexicon-based. It misses sarcasm and negation.

**Future scope**

- Replace keyword categorisation with **TF-IDF + Logistic Regression** or a
  **fine-tuned BERT** classifier, evaluated against the user tags already collected.
- **PostgreSQL** + Alembic migrations for production.
- Decoupled **React/Flutter** front end consuming the existing REST API.
- **Voice-to-text** journaling and daily email/push reminders (Flask-Mail).
- On-device / **federated** NLP for stronger privacy.
- Configurable insight cadence and richer trend analytics.

---

## Author

**Arundhati Chaudhuri**
Bachelor of Technology, Computer Science & Engineering — KIIT University

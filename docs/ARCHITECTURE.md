# Architecture

This document explains how JournalJourney is built. It shows the layers, the job
of each module, the design patterns used, and how the system behaves when it runs.

The matching vector diagram is [architecture.svg](architecture.svg).

## 1. Architectural Style

JournalJourney uses a **layered (n-tier) architecture**. This means the code is
split into layers, one on top of another. It is built as a server-rendered Flask
application. It also has an extra JSON API surface. The layers are:

1. **Presentation layer** — Jinja2 templates with CSS and Chart.js in the
   browser. It also has a machine-readable JSON interface for API clients. It
   also makes the CSV/PDF export outputs.
2. **Application layer** — the Flask application made by the
   `create_app()` factory. Six Blueprints handle HTTP concerns. Business logic
   lives in its own domain/service modules.
3. **Data layer** — the SQLAlchemy ORM (a tool that lets Python code talk to
   the database). It maps three models onto a SQLite database. You can swap
   SQLite for PostgreSQL through `DATABASE_URL`.
4. **External services** — the Google Gemini API. It is called only from the
   insights feature.
5. **Cross-cutting concerns** — security, configuration, error handling, and
   testing. These apply across all layers.

## 2. Layer and Component Responsibilities

### 2.1 Presentation Layer

| Component | Responsibility |
|-----------|----------------|
| `frontend/templates/*.html` | Jinja2 views for every page (auth, journal, edit, dashboard, insights, word cloud, error). |
| `frontend/static/styles*.css` | Page styling, shared across templates. |
| Chart.js (CDN) | Renders the mood-trend line chart and the emotion-breakdown bar chart from JSON injected into the page. |

The Flask app reads templates and static assets from the `frontend/` directory.
It does this with `template_folder` and `static_folder`. This keeps the client
code physically separate from the server code.

### 2.2 Application Layer

The application is put together by `backend/__init__.py::create_app()`. It creates
the Flask instance. It starts the SQLAlchemy and Bcrypt extensions. It registers
the Blueprints and error handlers. It also runs the schema-migration and backfill
routines inside an application context.

**Blueprints (HTTP routing):**

| Blueprint | File | Responsibility |
|-----------|------|----------------|
| `auth` | `routes/auth.py` | Registration, login, logout, session management. |
| `journal` | `routes/journal.py` | Create, edit, delete, list, and search entries; word-cloud page and image. |
| `dashboard` | `routes/dashboard.py` | Aggregate sentiment and emotion data; compute streak; build chart datasets. |
| `insights` | `routes/insights.py` | Weekly AI reflection with 7-day caching and manual refresh. |
| `export` | `routes/export.py` | CSV and PDF export of a user's entries. |
| `api` | `routes/api.py` | JSON REST API over the same models. |

**Domain / service modules (business logic):**

| Module | Responsibility |
|--------|----------------|
| `nlp.py` | Text preprocessing (tokenise, remove stopwords, lemmatise), keyword categorisation, VADER sentiment, NRCLex emotion. |
| `services.py` | Journaling-streak calculation and word-cloud image rendering. |
| `ai.py` | Builds the Gemini prompt from recent entries and calls the LLM; degrades gracefully when the key is absent. |
| `forms.py` | WTForms definitions with validators and CSRF protection. |
| `models.py` | SQLAlchemy models and their serialisation helpers. |

We keep routing thin. We push the logic into `nlp`, `services`, and `ai`. This
means the HTML views, the REST API, and the test suite all reuse the same
functions. There is no duplication.

### 2.3 Data Layer

The SQLAlchemy ORM maps three models — `User`, `DiaryEntry`, and
`WeeklyInsight` — onto relational tables. Every entry and insight query is
scoped by `user_id`. This keeps each user's data strictly apart. The full
schema is documented in [DATABASE.md](DATABASE.md).

### 2.4 External Services

`ai.py` is the only module that reaches outside the process. It builds a
`google-genai` client and calls `gemini-2.5-flash`. TLS trust is handled by
the operating-system certificate store through `truststore`. This lets the call
work behind corporate proxies that intercept HTTPS.

### 2.5 Cross-Cutting Concerns

| Concern | Implementation |
|---------|----------------|
| Authentication | Session cookie set on login; every protected view and API endpoint checks `session['user_id']`. |
| Password security | Bcrypt hashing via Flask-Bcrypt. |
| CSRF protection | Flask-WTF issues and validates CSRF tokens on all HTML forms. |
| Configuration | `config.py` reads secrets and the database URL from the environment through `python-dotenv`. |
| Error handling | Central 404/500 handlers return themed HTML pages, or JSON for `/api/` paths. |
| Testing | `pytest` suite with an in-memory database fixture (`TestConfig`). |

## 3. Design Patterns

- **Application Factory** — `create_app(config_class)` builds a fresh, fully
  configured app instance. This makes testing clean. You get a separate
  `TestConfig` with an in-memory database. You also get many configurations
  with no global state.
- **Blueprint modularisation** — each functional area is its own Blueprint.
  This gives separation of concerns and clear URL grouping.
- **Model-View-Template (MVT)** — Flask's version of MVC. Models go in
  `models.py`. Views (controllers) go in `routes/`. Templates go in
  `frontend/templates/`.
- **Repository-style access through the ORM** — we save data with
  SQLAlchemy queries, not raw SQL. This keeps the rest of the code separate
  from the storage engine.
- **Graceful degradation** — some features are optional (LLM insights, word
  cloud, PDF export, emotion detection). If a key or library is missing, they
  return a helpful message instead of crashing.

## 4. Runtime Behaviour

### 4.1 Application Startup

1. `run.py` calls `create_app()`.
2. Extensions (`db`, `bcrypt`) are started against the app.
3. Blueprints and error handlers are registered.
4. Inside an app context, `_ensure_schema()` creates any missing tables. It
   uses `ALTER TABLE` to add columns that came after an existing database was
   made (`sentiment_score`, `emotion`, `tags`).
5. `_backfill_sentiment_scores()` computes scores for any old entries that
   came before the sentiment-score column.
6. NLTK corpora are checked once when `nlp.py` is imported. They are
   downloaded only if they are missing.

### 4.2 Writing an Entry (end to end)

1. The browser submits the entry form (CSRF-protected).
2. The `journal.index` view calls `categorize_entry`, `analyze_sentiment`, and
   `analyze_emotion` from `nlp.py`.
3. A `DiaryEntry` is saved through the ORM with its derived labels and
   optional user tags.
4. The user is sent to the entries list. It shows the new entry.

### 4.3 Generating a Weekly Insight

1. `insights.insights` first looks for a `WeeklyInsight` made in the last
   seven days. If it finds one, it is served from cache.
2. If not, the last seven entries are formatted into a structured prompt by
   `ai.generate_weekly_insight` and sent to Gemini.
3. The response is stored as a new `WeeklyInsight` and shown. A manual
   refresh deletes the cached insight and makes it again.

## 5. Design Decisions and Rationale

| Decision | Rationale |
|----------|-----------|
| VADER for sentiment | Rule-based, needs no training data, and is tuned for short informal text; it also outperformed TextBlob on the project's labelled evaluation set (see `backend/evaluation/nlp_comparison.py`). |
| NRCLex for emotion | Provides specific Plutchik emotions (joy, fear, anger, sadness, trust, and others) beyond VADER's valence, deepening the analysis with a lightweight lexicon. |
| Caching AI insights | Gemini calls cost money and add latency; a seven-day cache limits calls to at most one per user per week. |
| SQLite by default | Zero-configuration for demonstration and grading, while `DATABASE_URL` allows a production PostgreSQL deployment with no code change. |
| Session-based auth for the API | Reuses the existing login flow; a token scheme is noted as future work for fully decoupled clients. |

## 6. Known Limitations

- Categorisation is naive keyword matching. So entries with no lexicon words
  default to *Personal Development*.
- SQLite has one writer at a time. It is not fit for high concurrency.
- Emotion and sentiment are lexicon-based. They do not model sarcasm or complex
  negation.

Planned improvements (TF-IDF or fine-tuned BERT categorisation, PostgreSQL with
Alembic migrations, a decoupled front end, and voice journaling) are listed in
the root [../README.md](../README.md) and in [STATUS_REPORT.md](STATUS_REPORT.md).

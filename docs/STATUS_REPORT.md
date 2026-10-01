# Project Status Report

Date: 2026-07-30

This report shows how far JournalJourney has come against the final-year B.Tech
project plan. It lists what is built and checked, and what is left as optional or
future work.

## 1. Summary

All planned features and academic deliverables are built and checked. The
automated test suite passes (31 tests). A live end-to-end run against the running
server passed all 15 checks. No required tasks are left.

The only items not built are optional extras. They need outside credentials or
infrastructure to work (see Section 4).

## 2. Completed and Verified

### 2.1 Code structure and quality

| Item | Status | Notes |
|------|--------|-------|
| Backend/frontend separation | Done | `backend/` and `frontend/` folders. |
| Application-factory pattern | Done | `create_app()` in `backend/__init__.py`. |
| Blueprint modularisation | Done | auth, journal, dashboard, insights, export, api. |
| Secret key moved to environment | Done | `SECRET_KEY` read from `.env`. |
| Configurable database URL | Done | `DATABASE_URL`, SQLite default, PostgreSQL-ready. |
| Error handlers (404/500) | Done | HTML pages, JSON for `/api/`. |

### 2.2 Features

| Item | Status | Notes |
|------|--------|-------|
| Authentication (Bcrypt, sessions, CSRF) | Done | Existing, retained. |
| Entry create / list / search / delete | Done | Existing, retained. |
| Entry editing | Done | `/edit_entry/<id>`, re-runs NLP. |
| Sentiment analysis (VADER) | Done | Label plus numeric compound score. |
| Emotion detection (NRCLex) | Done | Dominant emotion per entry. |
| Custom tags | Done | Stored alongside the auto category. |
| Mood dashboard (Chart.js) | Done | 7/30-day trend, rolling average. |
| Emotion breakdown chart | Done | Bar chart on the dashboard. |
| Journaling streak counter | Done | Home and dashboard. |
| Word cloud | Done | Per-user PNG generated on request. |
| CSV export | Done | `/export/csv`. |
| PDF export | Done | `/export/pdf` via reportlab. |
| AI weekly insights (Gemini) | Done | 7-day cache, manual refresh. |
| REST API (JSON) | Done | `/api/entries`, `/api/stats`. |

### 2.3 Academic deliverables

| Item | Status | Location |
|------|--------|----------|
| NLP model comparison (VADER vs TextBlob) | Done | `backend/evaluation/nlp_comparison.py` (VADER 100 percent vs TextBlob 80 percent on the labelled set). |
| Automated tests | Done | `tests/` — 31 unit and integration tests. |
| Architecture documentation | Done | `docs/ARCHITECTURE.md` + `docs/architecture.svg`. |
| Data-flow documentation | Done | `docs/DATAFLOW.md`. |
| Database / ER documentation | Done | `docs/DATABASE.md`. |
| API documentation | Done | `docs/API.md`. |
| Requirements specification | Done | Root `README.md`. |
| Literature review | Done | Root `README.md`. |
| Future scope | Done | Root `README.md` and this report. |

## 3. Verification Evidence

- Unit and integration tests: `pytest` reports 31 passed.
- Live end-to-end run: signup, login, add/edit entries, tags, emotion display,
  dashboard, streak, word-cloud image, CSV export, PDF export, and all REST API
  endpoints returned the expected results (15 of 15 checks passed).
- NLP evaluation: `python -m backend.evaluation.nlp_comparison` runs and
  reports per-class accuracy.

Commands to reproduce:

```bash
pytest
python -m backend.evaluation.nlp_comparison
python run.py     # then exercise the UI at http://127.0.0.1:5000
```

## 4. Optional / Future Work (not blocking)

These are choices about scope, not faults. Each one needs outside setup that
sits outside the core academic deliverable.

| Item | Why deferred | Effort to add |
|------|--------------|---------------|
| Email reminders (Flask-Mail) | Needs SMTP credentials and a scheduler (for example APScheduler or a cron job). | Small to medium. |
| Token-based API auth (JWT) | Session auth is enough for the current same-origin use. Tokens matter only for a fully decoupled client. | Medium. |
| ML-based categorisation (TF-IDF or BERT) | The keyword categoriser is written down as a known limitation. A trained model needs a labelled dataset. The user tags now being collected are a start. | Medium to large. |
| PostgreSQL + Alembic migrations | SQLite is enough for a demo. The code already supports `DATABASE_URL`. | Small to medium. |
| Voice-to-text journaling | Needs a speech-to-text service and more front-end work. | Medium. |
| Screenshots in documentation | Best taken from a live demo environment. | Small. |

## 5. Conclusion

The project is feature-complete and checked against its plan. No required tasks
are left. The items in Section 4 are optional extras. You can add them if the
scope grows. Each one is already noted in the future-scope parts of the
documentation.

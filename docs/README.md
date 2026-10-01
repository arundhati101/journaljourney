# JournalJourney — Documentation

This folder holds the full technical documentation for **JournalJourney**. It
is an AI-assisted personal journaling platform (an app for writing a diary). It
is built with Flask, NLTK/VADER, NRCLex, and the Google Gemini API. It is made
as a final-year B.Tech project in Computer Science and Engineering.

## Document Index

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | This overview and index. |
| [SETUP.md](SETUP.md) | How to install, configure, and run the project and its commands (Windows/PowerShell). |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture, layers, components, design patterns, and the annotated architecture diagram. |
| [DATAFLOW.md](DATAFLOW.md) | Data-flow diagrams (context, level-1, level-2), the request lifecycle, and the NLP data path. |
| [DATABASE.md](DATABASE.md) | Entity-relationship model, table schemas, relationships, and the migration strategy. |
| [API.md](API.md) | REST API reference: endpoints, request/response formats, status codes, and examples. |
| [INTERVIEW_PREP.md](INTERVIEW_PREP.md) | Viva and presentation reference: every likely question (in several phrasings) with detailed, code-grounded answers. |
| [PROJECT_INTERVIEW_GUIDE.md](PROJECT_INTERVIEW_GUIDE.md) | Beginner-first project walkthrough and honest interview preparation, including the attached viva questions and implementation caveats. |
| [STATUS_REPORT.md](STATUS_REPORT.md) | What is done and verified, and what is left as optional or future work. |
| [architecture.svg](architecture.svg) | Vector diagram of the layered architecture (referenced by ARCHITECTURE.md). |

## What the System Does

A registered user writes diary entries. The app works on each entry by itself.
For each entry it does these steps:

- it sorts the entry into one of five life areas (Work, Health, Relationships,
  Personal Development, Hobbies);
- it scores the entry for sentiment (the mood or feeling of the text) with
  VADER. This gives a label and a number called the compound score;
- it marks the entry with the main emotion, using the NRC emotion lexicon (a
  word list that links words to emotions).

The user can then search, edit, and delete entries. The user can also see mood
trends and how emotions are spread out over time. The app tracks journaling
streaks (how many days in a row you write). It makes a word cloud. It exports
entries as CSV or PDF. It also gives an AI-made weekly reflection. Google
Gemini makes this reflection.

## Technology Summary

| Concern | Technology |
|---------|------------|
| Language | Python 3.13 |
| Web framework | Flask (application-factory pattern with Blueprints) |
| ORM / Database | SQLAlchemy over SQLite (PostgreSQL-ready) |
| Templating | Jinja2, HTML5, CSS3 |
| Charts | Chart.js |
| NLP | NLTK (VADER, tokeniser, WordNet lemmatiser, stopwords), NRCLex |
| LLM | Google Gemini (gemini-2.5-flash) via google-genai |
| Visualisation / export | wordcloud, matplotlib, reportlab |
| Testing | pytest (31 unit and integration tests) |
| Configuration | python-dotenv, truststore |

## Repository Layout

```text
journaljourney/
  run.py                  entry point (create_app)
  requirements.txt
  pytest.ini
  backend/                all server-side code
    __init__.py           app factory, blueprints, error handlers, migrations
    config.py             Config / TestConfig
    models.py             User, DiaryEntry, WeeklyInsight
    forms.py              WTForms
    nlp.py                preprocessing, category, sentiment, emotion
    ai.py                 Gemini weekly-insight generation
    services.py           streak calculation, word-cloud rendering
    routes/               auth, journal, dashboard, insights, export, api
    evaluation/           nlp_comparison.py (VADER vs TextBlob)
  frontend/               all client-side code
    templates/            index, entries, edit, dashboard, insights,
                          wordcloud, login, signup, error
    static/               styles1/2/3.css
  tests/                  conftest, test_nlp, test_routes, test_api
  docs/                   this documentation set
  instance/site.db        SQLite database (auto-created)
```

## Running the Project

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
# create .env with GEMINI_API_KEY and SECRET_KEY
python run.py                     # serves http://127.0.0.1:5000
pytest                            # run the test suite
python -m backend.evaluation.nlp_comparison   # NLP model evaluation
```

To see the project-level quick start, feature list, requirements
specification, literature review, and future scope, look at the root
[../README.md](../README.md).

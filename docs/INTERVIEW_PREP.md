# Interview Prep — JournalJourney

An AI-assisted personal journaling platform. It is a full-stack Flask app. It has
a real NLP pipeline (sentiment, emotion, categorisation). It uses an LLM (a large
language model, a program that understands and writes text) called Google Gemini
for weekly reflections. It has analytics dashboards and a JSON REST API. This
document is the one reference for the presentation and viva.

How to use this: each topic gives the question in a few ways ("asked as"). It
gives a spoken answer. Where it helps, it gives the exact implementation detail.
This way you can defend your answer under follow-up questions.

---

## 1. The short pitch

**Asked as:**
- "Explain your project in a minute."
- "What does JournalJourney do?"
- "What problem does it solve?"
- "Give me the elevator pitch."

**Answer:**
- **The problem:** people journal to understand their moods. But a plain text
  diary gives no feedback. You cannot see patterns. You cannot tell if this week
  was better than last. And you get no guidance.
- **What it does:** the user writes a diary entry. The app understands it by
  itself. It sorts the entry into a life area. It scores its sentiment. It finds
  the main emotion. Then it turns weeks of entries into a mood dashboard, a
  journaling streak, a word cloud, and an AI-written weekly reflection.
- **What makes it more than a form:** it joins three kinds of intelligence. First,
  classical NLP (VADER, NRCLex, NLTK). Second, a large language model (Google
  Gemini for the weekly insight). Third, data visualisation (Chart.js trends). All
  of this runs over a secure backend with many users.
- **The key idea:** cheap, deterministic NLP runs on every entry. The costly LLM
  is used only where you truly need to generate language (the weekly reflection).
  And it degrades gracefully to a helpful message when the API key is missing.

---

## 2. Why this project — why is it non-trivial?

**Asked as:**
- "Why is this a good final-year project?"
- "What is technically challenging here?"
- "Isn't this just a CRUD app with a database?"
- "What is the depth in this?"

**Answer:**
- It is **not** just CRUD. Every entry goes through a real NLP pipeline before it
  is stored (tokenise, remove stopwords, lemmatise, categorise, VADER sentiment,
  NRCLex emotion).
- It joins **many systems that work together**: authentication and sessions, an
  ORM-backed database, an NLP layer, an LLM layer, a charting layer, export, and a
  REST API. All of this sits in one app that fits together.
- It shows a real engineering decision: **where to use a language model and where
  not to**. This controls cost, speed, and reproducibility.
- It follows **production patterns**: the Flask application-factory, Blueprints,
  environment-based configuration, migration-safe schema upgrades, graceful
  degradation, custom error pages, and an automated test suite (31 tests).
- It has an **evaluation artifact**. This is a script that measures VADER against
  TextBlob on a labelled set. So the model choice is backed by numbers, not just
  assumed.

---

## 3. Technology stack and why each piece

**Asked as:**
- "What technologies did you use and why?"
- "Why Flask and not Django?"
- "Justify your tech choices."
- "Walk me through the stack."

**Answer:**
- **Language — Python 3.13:** the natural choice. The NLP ecosystem (NLTK, NRCLex,
  TextBlob) and the Gemini SDK are all Python.
- **Web framework — Flask (application-factory + Blueprints):** it is light and
  clear. I wanted to structure the app myself. I did not want Django's heavier
  conventions. The factory pattern makes testing clean.
- **ORM / database — SQLAlchemy over SQLite:** SQLite needs no setup for a demo.
  SQLAlchemy (an ORM, a tool that lets Python code talk to the database) hides the
  database. So the same code runs on PostgreSQL by changing one environment
  variable.
- **Templating — Jinja2 + HTML/CSS; charts — Chart.js:** the server builds the
  pages. There is only a little client-side JavaScript, and only for the
  interactive charts.
- **NLP — NLTK (VADER, tokeniser, WordNet lemmatiser, stopwords) and NRCLex:**
  these are mature and rule/lexicon-based. They need no training data or GPU.
- **LLM — Google Gemini (gemini-2.5-flash) via google-genai:** used only for the
  weekly reflection, where real text generation is needed.
- **Security — Flask-Bcrypt, Flask-WTF:** Bcrypt password hashing and automatic
  CSRF protection on forms.
- **Visualisation / export — wordcloud, matplotlib, reportlab:** the word-cloud
  image and CSV/PDF export.
- **Testing — pytest:** 31 unit and integration tests over an in-memory database.
- **Config — python-dotenv, truststore:** secrets come from a `.env` file.
  truststore makes HTTPS to Gemini work behind corporate proxies.

---

## 4. Architecture — how is the code organised?

**Asked as:**
- "Describe your architecture."
- "How is the project structured?"
- "What design patterns did you use?"
- "Why split backend and frontend?"

**Answer:**
- It is a **layered architecture**. The layers are: presentation (Jinja2/Chart.js
  and the JSON API), application (Flask with six Blueprints and domain modules),
  data (SQLAlchemy over SQLite), and one external service (Gemini).
- **Application-factory pattern:** `create_app(config_class)` in
  `backend/__init__.py` builds a fresh, fully configured app. This lets the test
  suite build the app with a separate in-memory configuration and no global state.
- **Blueprints** split the routes by concern: `auth`, `journal`, `dashboard`,
  `insights`, `export`, `api`. Each one is its own module.
- **Domain/service modules** hold the logic so routes stay thin: `nlp.py`
  (language processing), `services.py` (streak, word cloud), `ai.py` (Gemini). The
  HTML views, the API, and the tests all reuse the same functions. So behaviour
  never drifts between them.
- **Backend/frontend split on disk:** all Python is in `backend/`. All templates
  and CSS are in `frontend/`. Flask is pointed at the `frontend/` folders through
  `template_folder` and `static_folder`. This gives clean separation of concerns.
  Examiners often ask for this over a single large file.
- **Design patterns present:** Application Factory, Blueprint modularisation,
  Model-View-Template (Flask's MVC), repository-style ORM access, and graceful
  degradation.

**Implementation detail:**
- `run.py` is the entry point. It calls `create_app()` and runs it.
- On startup the factory starts the `db` and `bcrypt` extensions. It registers the
  six Blueprints and the error handlers. Then it runs `_ensure_schema()` and
  `_backfill_sentiment_scores()` inside an application context.

---

## 5. The NLP pipeline — what happens to an entry (the core)

**Asked as:**
- "Walk me through your NLP pipeline."
- "What processing happens when a user saves an entry?"
- "How do you analyse the text?"
- "What NLP techniques did you actually implement?"

**Answer (walk it in order — this is your strongest technical section):**

When an entry is submitted, `routes/journal.py` calls three functions from
`nlp.py` before saving. The pipeline has four stages:

- **Stage 1 — Preprocess (`preprocess_text`).** First, lowercase the text. Then
  tokenise it with NLTK's `word_tokenize`. Drop non-alphanumeric tokens and
  English stopwords. Then lemmatise each remaining word with the WordNet
  lemmatiser, so "meetings" becomes "meeting". This gives a clean list of
  root-form tokens.
- **Stage 2 — Categorise (`categorize_entry`).** Score those tokens against five
  keyword lexicons — Work, Health, Relationships, Personal Development, Hobbies.
  Each matching token adds one to that category's score. The highest score wins.
  If nothing matches, it defaults to "Personal Development".
- **Stage 3 — Sentiment (`analyze_sentiment`).** Run VADER on the raw text to get
  a compound score in the range -1 to +1. Map it to a label: at least 0.05 is
  Positive, at most -0.05 is Negative, otherwise Neutral. It returns both the label
  and the numeric score. The score is what the dashboard trend is built on.
- **Stage 4 — Emotion (`analyze_emotion`).** Run NRCLex over the text. It maps
  words to NRC emotions (joy, fear, anger, sadness, trust, and so on). I ignore
  the generic positive/negative buckets, because VADER already covers valence. It
  returns the single strongest specific emotion, or "neutral" if nothing fires.

The four outputs — category, sentiment label, sentiment score, emotion — are
stored on the `DiaryEntry` row along with any user tags.

**Implementation detail:**
- The tokeniser, stopwords, lemmatiser, and the VADER analyzer are created once at
  module load, not per request.
- `_ensure_nltk_data()` checks the five required NLTK corpora (punkt, punkt_tab,
  stopwords, wordnet, vader_lexicon). It downloads only the missing ones. This is
  wrapped in try/except, so the app still starts offline once the data has been
  fetched.
- The same pipeline runs on **edit** as well as create. So labels stay consistent
  with edited text.

---

## 6. Sentiment analysis with VADER — how and why

**Asked as:**
- "How does your sentiment analysis work?"
- "What is VADER and why did you choose it?"
- "Why not a deep-learning sentiment model?"
- "What does the compound score mean?"

**Answer:**
- **VADER** (Valence Aware Dictionary and sEntiment Reasoner) is a rule-based,
  lexicon-driven sentiment model from NLTK. Each word has a valence. VADER
  combines them with rules for punctuation, capitalisation, and negation. This
  gives a **compound score**, scaled between -1 (most negative) and +1 (most
  positive).
- I threshold that score: at least 0.05 is Positive, at most -0.05 is Negative,
  the band in between is Neutral. These are VADER's standard cut-offs.
- **Why VADER:** it is tuned for short, informal text (which is exactly what a
  diary entry is). It needs no training data or GPU. It is fast enough to run on
  every entry. And it is deterministic, so the same entry always gets the same
  score.
- **Why not deep learning:** a transformer would need training data. It would be
  far heavier to run on every save. And it would be overkill for a journaling app.
  My evaluation script confirms VADER is accurate on this kind of text.

**Implementation detail:**
- `analyze_sentiment` returns a tuple `(label, compound)`. `score_text` returns
  just the compound, and the legacy-backfill routine reuses it.

---

## 7. Emotion detection with NRCLex — how and why

**Asked as:**
- "How do you detect emotions, and how is that different from sentiment?"
- "What is NRCLex?"
- "Why add emotion on top of sentiment?"
- "Which emotions can it detect?"

**Answer:**
- **Sentiment** is one axis: positive to negative. **Emotion** is more detailed —
  joy, fear, anger, sadness, trust, anticipation, surprise, disgust. So two
  negative entries can be told apart as "sad" versus "angry".
- **NRCLex** uses the NRC Word-Emotion Association Lexicon. It looks up each word
  and counts which emotions it links to. This gives a frequency for each emotion in
  the text.
- I take the strongest specific emotion and store it. I choose to **ignore the
  positive/negative buckets** NRCLex also returns. This is because VADER already
  measures valence more precisely. NRCLex adds the categorical emotion that VADER
  cannot.
- This deepens the analysis for very little cost. It is still lexicon-based. There
  is no model call and no training.

**Implementation detail:**
- API usage in NRCLex 4.x: create `NRCLex()`, then `load_raw_text(text)`, then
  read `affect_frequencies`. Filter out `positive`/`negative`. Return the emotion
  with the maximum frequency, or "neutral" when the dictionary is empty.
- The whole thing is wrapped. So if the library is missing, it returns "neutral"
  instead of crashing.

---

## 8. Automatic categorisation — how it works and its limits

**Asked as:**
- "How do you categorise an entry?"
- "How accurate is the categoriser?"
- "What are the limitations of your categorisation?"
- "How would you improve it?"

**Answer:**
- Categorisation is **keyword scoring**. I keep five keyword lists (Work, Health,
  Relationships, Personal Development, Hobbies). After preprocessing, I count how
  many tokens fall into each category and pick the highest.
- If no keyword matches, it defaults to "Personal Development". So every entry
  always gets a category.
- **I am honest about the limitation.** This is naive lexical matching. An entry
  about a topic outside the keyword lists gets the default category. It cannot
  understand context or synonyms it does not list.
- **How I would improve it:** move to TF-IDF features with a Logistic Regression
  classifier, or a fine-tuned BERT model. I would train and evaluate it against the
  **user tags** the app already collects. Collecting those tags now is the first
  step toward that supervised upgrade. This is stated in my future scope.

**Implementation detail:**
- The keyword map is `CATEGORY_KEYWORDS` in `nlp.py`. The same preprocessing that
  feeds the categoriser is reused, so lemmatised tokens match lemmatised keywords.

---

## 9. Tags — and why they matter beyond a feature

**Asked as:**
- "What are tags for?"
- "How do tags relate to the auto-category?"
- "Why let users tag if you already auto-categorise?"
- "What is the ML significance of tags?"

**Answer:**
- Tags are optional, comma-separated labels the user adds to an entry (for example
  "exams, gratitude").
- They are stored **alongside** the automatic category, not instead of it. This is
  on purpose. It gives two labelling schemes for the same entry: the machine's
  guess and the human's truth.
- This is the seed of a proper machine-learning evaluation. The user tags act as
  ground-truth labels. Later I can use them to train and measure a real classifier
  against the current keyword baseline. It shows ML-evaluation awareness, not just
  a UI feature.

**Implementation detail:**
- Stored as a single `tags` string. The `DiaryEntry.tag_list` property splits and
  cleans it into a list for display and for the JSON API.

---

## 10. The LLM (Gemini) — where it is used and why only there

**Asked as:**
- "Where do you use the language model?"
- "Why not use the LLM for everything?"
- "How does the weekly insight work?"
- "How do you control LLM cost?"

**Answer:**
- The LLM is used in **exactly one place**: generating the **weekly reflection**
  on the Insights page. That is real natural-language generation. Classical NLP
  cannot do it.
- **Everything else is deterministic** — sentiment, emotion, categorisation,
  streak, charts, search. Those are cheap, instant, and reproducible. Sending them
  to a model would be slower, cost money, and give a different answer each time.
- **How the insight works:** I take the user's last seven entries. I format each
  as a line with its date, category, sentiment, score, and a text snippet. Then I
  build a structured prompt. It asks Gemini for exactly three short paragraphs: an
  emotional pattern, two or three recurring themes, and one actionable suggestion.
  The response is stored and shown.
- **Cost control through caching:** an insight is cached for seven days per user. A
  second visit within the week serves the stored copy instead of calling the API
  again. A manual "Refresh now" button deletes the cache and regenerates it.

**Implementation detail:**
- `ai.generate_weekly_insight(entries, api_key, model)` builds the prompt and
  calls `genai.Client(api_key).models.generate_content(model, contents=prompt)`.
- Model is `gemini-2.5-flash`, configurable via `GEMINI_MODEL`.
- Guard conditions: fewer than three entries returns a "write more" message and is
  **not** cached (so it disappears as soon as the user qualifies). A missing key
  returns a clear "unavailable" message. Any API exception returns a try-again
  message. The run never crashes.

---

## 11. The LLM-versus-deterministic split — the key design decision

**Asked as:**
- "What was your most important design decision?"
- "How did you decide what the model does versus plain code?"
- "Why is this cheaper and more reliable than an all-LLM approach?"
- "How do you keep results reproducible?"

**Answer:**
- The principle: **use the model only for judgement/generation. Use plain code for
  everything measurable.**
- Sentiment, emotion, and category are measurable. So they are lexicon/rule based:
  deterministic, instant, free, and identical on every run.
- The weekly reflection truly needs to compose fluent, personalised prose. So that
  one task goes to Gemini.
- **Result:** the model spends effort only on the single task that needs it. It
  works over already-structured inputs (entries with their scores and categories
  already attached). This is cheaper. It also produces a better-grounded reflection
  than handing it raw text and asking for everything.

---

## 12. Resilience — what happens when something is missing?

**Asked as:**
- "What if there is no Gemini API key?"
- "What if the model is down or a library is not installed?"
- "How resilient is the app?"
- "Does it crash if a dependency is missing?"

**Answer:**
- The design principle is **degrade, never crash.**
- **No API key or a Gemini error:** the Insights page shows a clear message instead
  of failing. Every other feature keeps working.
- **NRCLex not installed:** emotion detection returns "neutral" instead of
  erroring.
- **wordcloud/matplotlib not available, or no usable words:** the word-cloud
  endpoint returns nothing. The page shows a friendly "not enough words yet"
  message.
- **reportlab not installed:** the PDF export flashes a message telling the user to
  install it. Then it redirects back rather than throwing.
- **NLTK data unavailable offline:** downloads are tried only for missing corpora
  and wrapped in try/except. So once fetched, the app starts offline.
- Every optional capability checks for its dependency and falls back. So the core
  journaling flow is always available.

---

## 13. Database design

**Asked as:**
- "Explain your database schema."
- "What are your tables and relationships?"
- "How do you keep one user's data private from another?"
- "How do you handle schema changes?"

**Answer:**
- **Three tables.** `User` (id, unique username, Bcrypt password hash);
  `DiaryEntry` (id, text, category, sentiment, sentiment_score, emotion, tags,
  timestamp, user_id); `WeeklyInsight` (id, insight_text, generated_on, user_id).
- **Relationships:** one User has many DiaryEntries and many WeeklyInsights. Each
  entry and insight belongs to exactly one user via a foreign key.
- **Privacy:** every entry and insight query is filtered by the logged-in
  `user_id`. So no user can ever read or modify another user's data. This is
  enforced in every route, including the API.
- **Migration-safe schema:** on startup `create_all()` builds missing tables. It
  never alters existing tables. So I also issue `ALTER TABLE ADD COLUMN` for the
  columns added during development (`sentiment_score`, `emotion`, `tags`). A
  backfill routine then works out sentiment scores for any old entries created
  before that column existed. So they still appear on the trend chart.

**Implementation detail:**
- `DiaryEntry.to_dict()` serialises a row for the JSON API. This includes the split
  tag list and the ISO timestamp.
- For production I note Alembic migrations plus PostgreSQL as the proper upgrade.

---

## 14. Authentication and security

**Asked as:**
- "How does login work?"
- "How are passwords stored?"
- "What security measures are in place?"
- "What is CSRF and how do you handle it?"

**Answer:**
- **Registration/login** use WTForms with validators. On signup the password is
  hashed with **Bcrypt**. Only the hash is stored, never the plaintext.
- **Login** checks the password against the hash. On success the user id and name
  are placed in the Flask **session** cookie, which is signed with the secret key.
- **Access control:** every protected route checks for `user_id` in the session
  and redirects to login if it is absent. The API returns a 401 JSON error instead
  of a redirect.
- **CSRF:** Flask-WTF puts a hidden CSRF token in every form and checks it on
  submission. This stops cross-site request forgery.
- **Secret management:** the secret key and API key come from a `.env` file that is
  gitignored. So secrets are never committed. A `.env.example` documents the
  required variables.

---

## 15. Analytics — dashboard, trend, streak, emotion breakdown

**Asked as:**
- "How does the mood dashboard work?"
- "How do you compute the trend line?"
- "How is the streak calculated?"
- "What does the rolling average do?"

**Answer:**
- The dashboard pulls the last 30 days of entries once. It then works out both a
  7-day and a 30-day view from them in Python. Then it sends the data to Chart.js.
- **Bucketing:** entries are grouped by calendar day. It keeps each day's list of
  sentiment scores, category counts, and entry count.
- **Trend line:** for each day it plots the average sentiment score. Missing days
  are included, so the x-axis is a true, gap-free calendar.
- **Rolling average:** a 7-day rolling average over the daily averages smooths the
  line. So a single bad day does not dominate the trend.
- **Summary stats:** total entries, average mood, and most common category for the
  window.
- **Streak:** `services.current_streak` counts consecutive days ending today (or
  yesterday, so a streak stays "alive" until the day is missed) on which at least
  one entry exists.
- **Emotion breakdown:** the counts of each dominant emotion over the window are
  drawn as a bar chart beside the trend line.

**Implementation detail:**
- The y-axis is fixed to the -1..+1 sentiment range. The gridlines are labelled
  Positive (+0.5), Neutral (0), Negative (-0.5). Both datasets are injected as JSON
  in a script tag and switched client-side without a page reload.

---

## 16. Word cloud

**Asked as:**
- "How is the word cloud generated?"
- "Where does that image come from?"
- "How do you avoid meaningless words in it?"
- "Is it precomputed or on demand?"

**Answer:**
- The word cloud is generated **on demand** as a PNG image. It is built from all of
  the user's entries combined.
- Words are lowercased and filtered to alphabetic tokens. Stopwords are removed, so
  filler words like "the" do not dominate. The remaining words are counted, and the
  frequencies drive the cloud.
- The image is streamed straight to the browser. If there are no usable words (or
  the library is missing), the page shows a friendly fallback message.

**Implementation detail:**
- `services.build_wordcloud_png` uses the `wordcloud` library (900x450, OrRd
  colormap). It writes to an in-memory PNG buffer. The `journal.wordcloud_image`
  route returns it with `send_file`. The first request is slower because matplotlib
  builds its font cache once. After that, requests are fast.

---

## 17. Export (CSV and PDF)

**Asked as:**
- "How does export work?"
- "What formats can the user export?"
- "How do you generate the PDF?"
- "Why is export useful?"

**Answer:**
- The user can download all their entries as **CSV** or **PDF**.
- **CSV** is built with Python's `csv` module. It has a header row, then one row per
  entry with date, category, sentiment, score, emotion, tags, and text. It is
  streamed as a file attachment.
- **PDF** is built with **reportlab**. It is a titled document with each entry's
  metadata line and body text laid out as flowables.
- It shows file I/O. It also gives the user real ownership of their data. They can
  keep a copy outside the app.

---

## 18. REST API

**Asked as:**
- "You mentioned a REST API — describe it."
- "Why add an API to a server-rendered app?"
- "How is the API secured?"
- "What endpoints are there?"

**Answer:**
- Alongside the HTML pages there is a JSON API under `/api`. So the same data and
  NLP pipeline can drive a future single-page app or mobile client.
- **Endpoints:** list entries, create an entry (runs the full NLP pipeline), get
  one entry, delete an entry, and a stats endpoint. The stats endpoint returns
  totals, average sentiment, streak, and category/emotion distributions.
- **Security:** it reuses the session. An unauthenticated call gets a 401 JSON
  error rather than an HTML redirect. Every query is scoped to the caller's user
  id.
- **Consistency:** the API calls the exact same `nlp`, `services`, and `models`
  code as the web views. So the two surfaces can never diverge in behaviour.

**Implementation detail:**
- An `api_login_required` decorator holds the 401 behaviour in one place. Errors
  under `/api/` are always returned as JSON by the global error handlers. Browser
  routes get HTML error pages.

---

## 19. Error handling

**Asked as:**
- "What happens on a 404 or a server error?"
- "How do you handle errors?"
- "Do API errors look different from page errors?"

**Answer:**
- There are central 404 and 500 handlers. For normal pages they render a themed
  error template. For any path under `/api/` they return a JSON error object with
  the right status code.
- The 500 handler also rolls back the database session. So a failed request cannot
  leave a half-written transaction behind.

---

## 20. Testing

**Asked as:**
- "How did you test this?"
- "What does your test suite cover?"
- "How do you test without touching the real database?"
- "How many tests and what kind?"

**Answer:**
- **31 automated tests** with pytest, split into unit and integration tests.
- **Unit tests** cover the NLP functions (preprocessing, categorisation, sentiment
  for positive/negative/neutral, emotion) and the streak algorithm. They include
  edge cases (a gap breaks the streak, no recent entry gives zero).
- **Integration tests** drive the real HTTP stack with Flask's test client:
  signup, login, wrong password, add/edit/delete an entry, search, CSV export, the
  404 page, and — importantly — that **one user cannot see another user's
  entries**.
- **API tests** cover every endpoint: auth required (401), create with the NLP
  result, validation (400 on empty text), get, delete, and stats.
- Tests run against an **in-memory SQLite database**. A separate `TestConfig`
  builds it, with CSRF disabled. So they are fast and isolated and leave no
  artifacts.

**Implementation detail:**
- Fixtures in `conftest.py` provide a fresh app, a test client, a seeded user, and
  a pre-authenticated client. Run with `pytest`.

---

## 21. Model evaluation — VADER vs TextBlob

**Asked as:**
- "How do you know VADER is the right choice?"
- "Did you compare any models?"
- "What accuracy did you get?"
- "How did you evaluate your NLP?"

**Answer:**
- I wrote an evaluation harness. It runs **VADER and TextBlob** over a
  hand-labelled set of journal-style sentences. It reports overall and per-class
  accuracy.
- On the current 15-sentence set, **VADER scored 100 percent and TextBlob 80
  percent**. VADER got all positives, neutrals, and negatives right. TextBlob
  missed one in each class.
- This backs the design choice with numbers. VADER is chosen because it is
  rule-based, needs no training data, is tuned for short informal text, and beat
  TextBlob here in a measurable way.
- I am clear that this is a small set. The honest framing is that it is a
  demonstration of the evaluation method. The set can be extended with real
  anonymised entries to strengthen the claim.

**Implementation detail:**
- `python -m backend.evaluation.nlp_comparison` runs it and prints the table.

---

## 22. End-to-end flow — start to finish

**Asked as:**
- "Walk me through the whole system from a user's first click."
- "Trace one entry end to end."
- "What is the full request lifecycle?"
- "Show me how everything connects."

**Answer (walk it in order):**

- **Step 0 — Startup.** `run.py` calls `create_app()`. The factory wires the
  extensions, registers the six Blueprints and the error handlers, creates or
  upgrades the schema, and backfills any missing sentiment scores.
- **Step 1 — Sign up / log in.** The user registers. The password is Bcrypt hashed
  and stored. On login the credentials are checked. The user id and name go into
  the signed session cookie. Every later request is authenticated by that cookie.
- **Step 2 — Write an entry.** The user submits the diary form (CSRF-protected).
  The `journal.index` view runs the NLP pipeline: preprocess, categorise, VADER
  sentiment (label + score), NRCLex emotion.
- **Step 3 — Persist.** A `DiaryEntry` is written through the ORM with the four
  derived fields and any tags, scoped to the user id.
- **Step 4 — Review entries.** The entries page lists the user's entries newest
  first, with category, sentiment, emotion, tags, and edit/delete actions. It also
  supports text search.
- **Step 5 — Dashboard.** The dashboard pulls 30 days of entries. It buckets them
  by day. It computes daily averages, a 7-day rolling average, summary stats, the
  streak, and the emotion breakdown. Then it hands JSON to Chart.js to draw the
  trend and bar charts.
- **Step 6 — Word cloud.** On request, the word-cloud route combines all entries,
  strips stopwords, and streams a PNG frequency cloud.
- **Step 7 — Weekly insight.** The insights page checks for a cached insight from
  the last seven days. If none, it formats the last seven entries into a structured
  prompt and calls Gemini for a three-paragraph reflection, stores it, and shows
  it. Refresh clears the cache and regenerates it.
- **Step 8 — Export / API.** At any time the user can export CSV or PDF. Or a
  client can use the JSON API for the same data and stats.
- **The invariant (a rule that always holds):** cheap deterministic NLP runs on
  every entry. The LLM is used only for the weekly reflection and always degrades
  to a message if unavailable. And every read and write is isolated per user.

---

## 23. Hardest part and what you learned

**Asked as:**
- "What was the hardest part?"
- "What would you do differently?"
- "What are you most proud of?"
- "What did you learn?"

**Answer (say it in your own words — sample):**
- **Hardest part:** getting the NRCLex integration right. The library's API changed
  between versions. So I had to inspect it and adapt (construct, then
  `load_raw_text`, then read frequencies). I also decided to ignore its
  positive/negative buckets, so it complemented VADER instead of duplicating it.
- **A close second:** the dashboard aggregation. I had to build a gap-free calendar
  and a correct rolling average from sparse daily data. I also had to backfill
  scores for legacy entries so old data still appears.
- **What I would do differently:** treat graceful degradation as a first-class
  concern from the start. Several early issues were really just missing optional
  data or libraries. They should have been reported as a fallback, not crashed on.
- **What I am proudest of:** the clean separation. Deterministic NLP does the
  measurable work. The LLM is used only where it earns its cost. There is a modular
  backend/frontend structure and a real test suite. So the project is both
  academically honest and genuinely runnable.

---

## 24. Limitations and future scope

**Asked as:**
- "What are the limitations?"
- "What would you add next?"
- "How would you take this to production?"
- "How does it scale?"

**Answer:**
- **Limitations I acknowledge:** categorisation is naive keyword matching. SQLite
  is single-writer and not for high concurrency. Sentiment and emotion are
  lexicon-based, so they miss sarcasm and complex negation.
- **Future scope:** replace keyword categorisation with TF-IDF + Logistic
  Regression or a fine-tuned BERT, trained against the user tags already collected.
  Move to PostgreSQL with Alembic migrations. Add a decoupled React/Flutter front
  end on the existing REST API. Add voice-to-text journaling and daily email/push
  reminders. Explore on-device or federated NLP for stronger privacy. And make the
  insight cadence configurable.

---

## Quick-fire follow-ups

- **"What exactly is the LLM for?"** — One thing only: writing the weekly
  reflection. Everything else is deterministic NLP.
- **"Which model?"** — Google Gemini, `gemini-2.5-flash`, through the google-genai
  client, with a graceful fallback message when there is no key.
- **"Sentiment vs emotion — the difference?"** — Sentiment is one axis (positive to
  negative, from VADER). Emotion is a category (joy, fear, anger, and so on, from
  NRCLex).
- **"Why VADER over TextBlob?"** — Tuned for short informal text, and it scored 100
  percent vs 80 percent on my labelled set.
- **"How do you keep users' data separate?"** — Every query is filtered by the
  session user id. A test explicitly proves one user cannot see another's data.
- **"How is the AI insight kept cheap?"** — Cached per user for seven days.
  Regenerated only on demand.
- **"Is it production-ready?"** — The structure is (factory, Blueprints, config,
  tests, error handling). For real production I would switch to PostgreSQL with
  Alembic and add token-based API auth.
- **"How many tests?"** — 31, unit and integration, on an in-memory database.
- **"What happens offline?"** — It degrades: insights and word cloud show
  fallbacks. All core journaling still works.
- **"Could this idea generalise?"** — Yes. The pattern of cheap deterministic
  analysis on every item, an LLM only for the one task that needs generation, and
  graceful degradation, fits many "analyse and assist" applications.

---

## One-line summaries to memorise

- **Project:** an AI-assisted journal that auto-analyses every entry (category,
  sentiment, emotion) and turns weeks of entries into trends, a streak, a word
  cloud, and a Gemini-written weekly reflection.
- **Architecture:** layered Flask app, application-factory + six Blueprints,
  backend/frontend split, SQLAlchemy over SQLite.
- **NLP:** NLTK preprocessing, VADER sentiment (score -1..+1), NRCLex emotion,
  keyword categorisation.
- **LLM:** Gemini for the weekly insight only, cached 7 days, degrades gracefully.
- **Key decision:** deterministic NLP for measurable work, LLM only for generation
  — cheaper, faster, reproducible.
- **Quality:** 31 pytest tests, a VADER-vs-TextBlob evaluation, custom error pages,
  migration-safe schema.

---

## Appendix — The Full Stages in Detail

Each stage below is described with its input, its output, how it works, and why it
exists. Read these when you need to explain any single part of the pipeline in
depth. The stages run in this order for a full user journey.

### Stage 1 — Application Startup and Initialisation

**Input:** the command `python run.py`, plus the `.env` file holding `SECRET_KEY`,
`GEMINI_API_KEY`, and the optional `DATABASE_URL`.
**Output:** a fully configured, running Flask application listening on port 5000.
**How:** `run.py` calls `create_app()` in `backend/__init__.py`. The factory loads
configuration. It starts the SQLAlchemy and Bcrypt extensions against the app. It
registers the six Blueprints (auth, journal, dashboard, insights, export, api) and
the 404/500 error handlers. Then, within an application context, it runs
`_ensure_schema()` (creates missing tables and adds any new columns via ALTER
TABLE) and `_backfill_sentiment_scores()` (fills scores for legacy entries).
**Why:** the application-factory pattern builds the app from scratch each time.
This keeps configuration clear, avoids global state, and lets the test suite create
an isolated in-memory version. Doing schema setup at startup means the database is
always ready without a manual migration step for the demo.

### Stage 2 — Registration and Authentication

**Input:** a username and password submitted through the signup or login form.
**Output:** a stored user with a hashed password (signup), or a signed session
cookie carrying the user id and name (login).
**How:** WTForms checks the fields. On signup, the app checks the username is
unique. Then it hashes the password with Bcrypt and stores only the hash. On login,
it looks up the user and checks the password against the hash with Bcrypt. On
success it writes `user_id` and `username` into the Flask session cookie, which is
cryptographically signed with the secret key. Every protected route checks for
`user_id` before proceeding.
**Why:** passwords must never be stored or compared in plaintext. So Bcrypt one-way
hashing protects them even if the database leaks. Session cookies let the server
recognise the user on later requests without re-sending credentials. Signing stops
tampering. This stage is the gate that makes every later stage private and
per-user.

### Stage 3 — Entry Intake

**Input:** the diary text and optional comma-separated tags submitted from the home
page form (with a CSRF token).
**Output:** the raw text and tags handed to the NLP pipeline, still unprocessed.
**How:** the `journal.index` view accepts the POST. It reads `diary_entry` and
`tags` from the form. It confirms the user is authenticated via the session. The
CSRF token embedded by Flask-WTF is checked automatically before the handler runs.
The raw text is then passed to the three NLP functions in turn.
**Why:** this is the single entry point where user language enters the system. So
it must be authenticated and CSRF-protected to stop forged submissions. Keeping
intake thin — just collecting and forwarding — means the actual analysis lives in
reusable functions that the API and tests also call. So behaviour never differs
between the web form and the API. Separating intake from analysis is what keeps the
route readable and the logic testable in isolation.

### Stage 4 — Text Preprocessing

**Input:** the raw entry text.
**Output:** a clean list of lower-case, root-form tokens with stopwords removed.
**How:** `preprocess_text` in `nlp.py` lower-cases the text. It tokenises it with
NLTK's `word_tokenize`. It keeps only alphanumeric tokens. It drops English
stopwords (the, is, and, and similar). Then it lemmatises each remaining token with
the WordNet lemmatiser, so inflected forms collapse to their root (for example
"meetings" becomes "meeting").
**Why:** raw text is noisy. Punctuation, casing, and filler words carry no
categorisation signal and would dilute keyword matching. Reducing words to their
lemma means a single keyword like "meeting" matches "meetings", "meet", and "met".
This makes the downstream categoriser far more reliable without a bigger keyword
list. This stage is deterministic and runs in microseconds over thousands of words.
That is exactly why it is plain NLTK code and not a model call. Its output feeds the
categoriser. The sentiment and emotion stages read the raw text instead, because
they have their own internal handling of casing and negation.

### Stage 5 — Categorisation

**Input:** the preprocessed token list.
**Output:** one category label — Work, Health, Relationships, Personal
Development, or Hobbies.
**How:** `categorize_entry` scores the tokens against five keyword lexicons held in
`CATEGORY_KEYWORDS`. Each token that appears in a category's keyword list adds one
to that category's score. The category with the highest score wins. If no token
matches any list, it defaults to "Personal Development", so every entry always
receives a category.
**Why:** categorising entries lets the dashboard report the user's most common life
area. It also lets entries be grouped in a meaningful way. Keyword scoring is
simple, clear, and instant. This suits a lightweight app and is easy to explain and
defend. I am open about its limitation — it cannot understand context or words
outside the lists. And I propose a TF-IDF or fine-tuned BERT classifier, trained on
the user tags collected in Stage 3, as the supervised upgrade. Using the lemmatised
tokens from Stage 4 means the keywords match a wide range of word forms. This
improves accuracy at no extra cost.

### Stage 6 — Sentiment Analysis (VADER)

**Input:** the raw entry text.
**Output:** a sentiment label (Positive, Neutral, or Negative) and a numeric
compound score between -1 and +1.
**How:** `analyze_sentiment` runs NLTK's VADER `SentimentIntensityAnalyzer` on the
text to get the compound score. This score blends per-word valences with rules for
punctuation, capitalisation, and negation. It thresholds the score: at least 0.05
is Positive, at most -0.05 is Negative, and the band between is Neutral. Both the
label and the raw score are returned and stored.
**Why:** sentiment is the backbone of the whole app. It drives the mood trend, the
summary statistics, and part of the AI prompt. VADER is chosen because it is tuned
for short, informal text like diary entries. It needs no training data or GPU. It
runs instantly on every entry. And it is deterministic, so results are
reproducible. The numeric score is stored (not just the label) because the
dashboard needs a continuous value to plot a trend line and compute a rolling
average. A three-way label alone could not support that.

### Stage 7 — Emotion Detection (NRCLex)

**Input:** the raw entry text.
**Output:** a single dominant emotion label such as joy, fear, anger, sadness, or
trust, or "neutral" when nothing matches.
**How:** `analyze_emotion` constructs an `NRCLex` object, calls
`load_raw_text(text)`, and reads `affect_frequencies` — the proportion of words
mapping to each NRC emotion. It discards the generic positive and negative buckets.
It returns the specific emotion with the highest frequency. If the dictionary is
empty it returns "neutral". The whole call is wrapped, so a missing library degrades
to "neutral" instead of crashing.
**Why:** sentiment is only one axis (positive to negative). So two negative entries
look identical to it. Emotion tells "sad" apart from "angry", which is far more
useful for self-reflection. I ignore NRCLex's positive/negative buckets on purpose,
because VADER already measures valence more precisely. NRCLex adds the categorical
emotion VADER cannot. It is still lexicon-based, so it costs almost nothing and
needs no model. This keeps this stage cheap and reproducible like the others.

### Stage 8 — Persistence

**Input:** the four derived fields (category, sentiment label, sentiment score,
emotion) plus the raw text, tags, and the current user id.
**Output:** a committed `DiaryEntry` row in the database.
**How:** the view creates a `DiaryEntry` model instance with all fields and the
`user_id` from the session. It adds it to the SQLAlchemy session and commits. The
timestamp defaults to the current time. The user is then redirected to the entries
list.
**Why:** storing the derived labels alongside the text means the expensive-ish
analysis runs once at write time, not every time the entry is displayed or charted.
So reads stay fast. Stamping every row with the owner's `user_id` is what enforces
privacy. Every later query filters by it, so no user can ever reach another user's
data. Storing the tags next to the auto-category keeps both the machine label and
the human label for the same entry. This is the ground truth needed for a future
supervised classifier. The commit is the point at which the entry becomes durable
and available to all the analytics stages.

### Stage 9 — Retrieval and Search

**Input:** the logged-in user id and an optional search query string.
**Output:** the user's entries, newest first, optionally filtered to those
containing the query.
**How:** `journal.entries` builds a SQLAlchemy query filtered by `user_id` and
ordered by timestamp descending. If a search term is present, it adds a
`text.contains(term)` filter. The results render in the entries template with
category, sentiment, emotion, tags, and edit and delete controls.
**Why:** users need to revisit, find, edit, and remove past entries. So retrieval
is the read side of the CRUD model. Scoping the query by `user_id` guarantees
isolation. Ordering newest-first matches how a journal is naturally read. Search is
a simple substring match rather than full-text indexing, because the per-user data
volume is small and a `LIKE`-style filter is instant at this scale. If the data
grew, a full-text index would be the upgrade. Editing an entry from this screen
re-runs Stages 4 to 7, so the stored labels always match the current text. This
prevents stale analysis.

### Stage 10 — Dashboard Aggregation and Analytics

**Input:** the user's entries from the last 30 days.
**Output:** two JSON datasets (7-day and 30-day), each with daily average scores, a
7-day rolling average, and summary statistics, plus an emotion-count map.
**How:** `dashboard.dashboard` fetches 30 days of entries once and buckets them by
calendar day. It keeps each day's scores, category counts, and entry count. A helper
builds each dataset over a gap-free list of calendar days. For each day it computes
the average sentiment. Then it computes a 7-day rolling average over those daily
averages, plus totals, mean mood, and the most common category. Emotion counts are
tallied across the window.
**Why:** the dashboard turns weeks of raw entries into an at-a-glance picture of
mood over time. This is the app's main value. Building a continuous calendar
(including empty days) keeps the x-axis honest. The rolling average smooths out
single-day spikes, so the real trend is visible. Aggregating in Python and sending
compact JSON to Chart.js keeps the browser light. It also means one database read
powers both time ranges and both charts.

### Stage 11 — Streak Computation

**Input:** all of the user's entries and today's date.
**Output:** an integer — the number of consecutive days, ending today or yesterday,
on which the user journaled.
**How:** `services.current_streak` collects the set of distinct entry dates. If the
user wrote today, it starts counting from today. If not, but they wrote yesterday,
it starts from yesterday (so a streak stays alive until a day is actually missed).
Otherwise the streak is zero. It then walks backwards one day at a time, counting
while each successive day is present in the set.
**Why:** streaks are a well-known behavioural mechanic. Showing "a 5-day streak"
encourages the habit of daily journaling, which is the point of the app. It is a
pure function of timestamps with no storage needed. So it is computed on demand and
shown on both the home page and the dashboard. The today-or-yesterday rule is a
deliberate design choice. It avoids punishing the user the moment a new day begins,
before they have had a chance to write. But it still breaks honestly once a full day
is skipped.

### Stage 12 — Word Cloud Generation

**Input:** all of the user's entry text, combined.
**Output:** a PNG image where word size reflects frequency, streamed to the browser.
**How:** `services.build_wordcloud_png` lower-cases and splits the combined text. It
keeps alphabetic words, removes stopwords, and counts frequencies. It feeds the
counts to the `wordcloud` library (900x450, OrRd colour map). It renders to an
in-memory PNG buffer. The `journal.wordcloud_image` route returns it with
`send_file`. If there are no usable words or the library is missing, it returns
nothing and the page shows a fallback message.
**Why:** a word cloud is an immediate, visually striking summary of what the user
writes about most. It is excellent for a demo and genuinely informative. Generating
it on demand from the live entries means it is always current without extra storage.
Removing stopwords first is essential. Otherwise "the" and "and" would dominate and
drown out meaningful words. The first request is slightly slow because matplotlib
builds a font cache once. Every request after that is fast. So warming it before a
live demo is worth doing.

### Stage 13 — Weekly AI Insight (Gemini)

**Input:** the user's last seven entries (each with date, category, sentiment,
score, and a text snippet), the API key, and the model name.
**Output:** a three-paragraph written reflection, cached for seven days.
**How:** `insights.insights` first looks for a `WeeklyInsight` generated within the
last seven days and serves it if found. Otherwise `ai.generate_weekly_insight`
formats the seven entries into a structured prompt. It asks Gemini for exactly three
paragraphs — emotional pattern, recurring themes, one actionable suggestion — and
calls `gemini-2.5-flash`. The result is stored as a `WeeklyInsight` and shown.
"Refresh now" deletes the cache and regenerates it.
**Why:** this is the only stage that needs true language generation. So it is the
only place the LLM is used. Everything measurable stays deterministic. Caching for
seven days limits the app to at most one paid API call per user per week. This
controls cost and latency. Guard conditions keep it safe: fewer than three entries
returns a prompt to write more (and is not cached), a missing key returns a clear
message, and any API error returns a try-again message. So the page never crashes.

### Stage 14 — Export (CSV and PDF)

**Input:** all of the user's entries.
**Output:** a downloadable CSV or PDF file of those entries.
**How:** the CSV route uses Python's `csv` module to write a header and one row per
entry (date, category, sentiment, score, emotion, tags, text) into an in-memory
buffer, streamed as an attachment. The PDF route uses reportlab to build a titled
document with each entry's metadata line and body as flowables. If reportlab is not
installed, the PDF route flashes a message and redirects rather than failing.
**Why:** export gives the user real ownership of their data. They can keep a copy
outside the app, print it, or move it elsewhere. This matters for something as
personal as a journal. Supporting both a machine-readable format (CSV, openable in
Excel or re-importable) and a human-readable one (PDF, nicely formatted for reading
or archiving) covers both use cases. Generating both on demand from the live
database means exports always reflect the current state. Streaming from memory
avoids writing temporary files to disk.

### Stage 15 — REST API Layer

**Input:** authenticated JSON HTTP requests under the `/api` prefix.
**Output:** JSON responses — entries, a created entry, statistics, or an error
object with the correct status code.
**How:** the `api` Blueprint exposes list, create, get, delete, and stats endpoints.
An `api_login_required` decorator returns a 401 JSON error when the session is
absent, instead of redirecting to an HTML page. Create runs the full Stage 4 to 7
NLP pipeline and returns the stored entry. Stats returns totals, average sentiment,
streak, and category and emotion distributions. Every query is scoped to the
caller's user id.
**Why:** the API exposes the same data and intelligence as the web pages in a
machine-readable form. So the app could later be driven by a separate React or
Flutter front end or a mobile client, without rewriting the backend. Reusing the
exact same `nlp`, `services`, and `models` code as the HTML views guarantees the two
surfaces can never behave differently. Returning JSON errors (not HTML redirects)
under `/api` is what makes it a proper programmatic interface. And the per-user
scoping enforces the same privacy guarantee everywhere.

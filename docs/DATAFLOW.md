# Data Flow

This document shows how data moves through JournalJourney. It uses the
Data-Flow Diagram (DFD) style. A DFD shows four things: external entities,
processes, data stores, and data flows. The diagrams are drawn with ASCII
(plain text characters) so they work anywhere. The layered component view is
in [architecture.svg](architecture.svg).

DFD notation used below:

- External entity: `[ Name ]`
- Process: `( n. Name )`
- Data store: `|| Dn Name ||`
- Flow: `--- label --->`

## 1. Context Diagram (Level 0)

This shows the whole system as one process. It also shows the external
entities (people or systems outside the app).

```text
        registration / login / entries / tag input
   [ User ] ---------------------------------------------> ( 0. JournalJourney )
   [ User ] <--- pages, charts, insights, CSV/PDF, JSON --- ( 0. JournalJourney )

                                   |  entry text of last 7 days
                                   v
                          [ Google Gemini API ]
                                   |  weekly reflection text
                                   v
                          ( 0. JournalJourney )
```

External entities:

- **User** — the logged-in person who writes and reads entries.
- **Google Gemini API** — an outside LLM (large language model, an AI text
  system) that returns weekly reflections.

## 2. Level-1 DFD

This shows the main processes. It also shows the data stores they read and
write.

```text
 [ User ]
    |  credentials
    v
 ( 1. Authenticate ) --- create/verify --->  || D1 User ||
    |  session (user_id)
    v
 ( 2. Manage Entries )
    |   raw text (+ tags)
    |----------------------> ( 3. Analyse Text (NLP) )
    |                                |  category, sentiment, score, emotion
    |   entry + labels               v
    |<-------------------------------+
    |  persist / read / update / delete
    v
 || D2 DiaryEntry ||
    |
    |  read entries
    v
 ( 4. Build Analytics ) --- datasets, streak, emotions ---> [ User ] (dashboard)
    |
    |  read last 7 entries
    v
 ( 5. Generate Insight ) --- prompt ---> [ Google Gemini API ]
    |                    <--- reflection ---
    |  cache / read
    v
 || D3 WeeklyInsight ||

 ( 6. Export )  --- read entries --->  || D2 DiaryEntry ||
    |  CSV / PDF file
    v
 [ User ]

 ( 7. Word Cloud ) --- read entries ---> || D2 DiaryEntry ||
    |  PNG image
    v
 [ User ]
```

Data stores:

- **D1 User** — accounts and hashed passwords.
- **D2 DiaryEntry** — entries with NLP labels and user tags.
- **D3 WeeklyInsight** — saved AI reflections.

## 3. Level-2 DFD — Text Analysis (expansion of process 3)

```text
 raw entry text
      |
      v
 ( 3.1 Preprocess )
   - lowercase
   - word_tokenize
   - drop stopwords / non-alphanumerics
   - WordNet lemmatise
      |
      +--> tokens --> ( 3.2 Categorise )
      |                  - score tokens against 5 keyword lexicons
      |                  - pick max, else default "Personal Development"
      |                        |
      |                        v  category
      |
      +--> raw text --> ( 3.3 VADER Sentiment )
      |                  - compound score in [-1, +1]
      |                  - label: Positive / Neutral / Negative
      |                        |
      |                        v  sentiment + score
      |
      +--> raw text --> ( 3.4 NRCLex Emotion )
                          - map words to NRC emotions
                          - ignore positive/negative buckets
                          - pick strongest, else "neutral"
                               |
                               v  emotion

 outputs: { category, sentiment, sentiment_score, emotion }
```

## 4. Request Lifecycle (HTML page)

```text
Browser
  |  1. HTTP request (cookie)
  v
Flask routing --> Blueprint view
  |  2. session check (user_id present?)  --no--> redirect /login
  |  3. call domain module (nlp / services / ai)
  |  4. ORM query / commit  <----> SQLite
  |  5. render Jinja2 template with data
  v
Browser  <-- 6. HTML (+ embedded JSON for Chart.js)
```

## 5. Request Lifecycle (JSON API)

```text
Client
  |  1. HTTP request (cookie, JSON body)
  v
api Blueprint  --> api_login_required
  |  2. not authenticated? --> 401 JSON
  |  3. validate body (e.g. non-empty text) --> 400 JSON on failure
  |  4. run NLP pipeline / ORM operation
  v
Client  <-- 5. JSON response (200 / 201 / 404 as appropriate)
```

## 6. Sentiment Trend Data Flow (dashboard)

```text
DiaryEntry rows (last 30 days)
      |
      v
 bucket by calendar day  -->  { day: [scores], categories, count }
      |
      +--> build 7-day dataset  (daily average, 7-day rolling average, stats)
      +--> build 30-day dataset (same shape)
      +--> compute current streak (consecutive days ending today/yesterday)
      +--> count emotions across the window
      |
      v
 JSON injected into dashboard.html
      |
      v
 Chart.js renders line chart (mood) + bar chart (emotions)
```

## 7. Trust and Privacy Notes

- Passwords are never stored as plain text. Process 1 turns them into a
  Bcrypt-hashed (scrambled and unreadable) form before they reach store D1.
- Only the entry text and its labels for the last seven entries leave the
  system. They go only to the Gemini API, and only when an insight is made.
- Every read of D2 and D3 is filtered by `user_id`. So one user's data never
  flows to another user.

# JournalJourney: Simple Project and Interview Guide

This guide explains the project in simple language. It is written so you can understand what the app does and practise explaining it in an interview. Read a section, then try to explain it without reading the words exactly.

## 1. What is JournalJourney?

JournalJourney is a website where people can keep a personal diary. A user can make an account, sign in, write diary entries, edit them, search them, and delete them.

When a person saves an entry, the app also looks at the words and adds:

- A topic, such as Work, Health, or Hobbies.
- A mood result: Positive, Neutral, or Negative.
- One main emotion, such as joy, sadness, or fear.

The app saves these results with the diary entry. It can then show mood charts, count how many days in a row someone has written, make a word cloud, and download entries as CSV or PDF. There is also an optional feature that asks Google Gemini to write a weekly reflection.

### Short answer for an interview

> My project is called JournalJourney. It is a diary website built with Python and Flask. Users can save and manage diary entries. The app checks each entry for its topic, mood, and main emotion, then shows summaries and charts. It can also make a weekly reflection with Google Gemini and export the entries as files.

## 2. Technology words explained simply

| Name | What it means in everyday words | What it does in this project |
|---|---|---|
| Python | A programming language. | Most of the app's backend code is written in Python. |
| Flask | A tool for building websites with Python. | Receives browser requests and decides which Python code should handle them. |
| Route | A piece of code connected to a web address or button action. | One route shows entries; another saves a new entry. |
| Blueprint | A way to group related routes together. | Login, diary, dashboard, exports, and other features have separate groups of routes. |
| HTML | The basic structure of a web page. | Used for the pages the user sees. |
| CSS | Rules that control how a page looks. | Styles the pages. |
| Jinja | A tool that puts data into HTML pages. | Flask uses it to show a user's entries and dashboard information. |
| Database | A place where an app saves information. | Stores user accounts, diary entries, and weekly reflections. |
| SQLite | A simple database saved as a file. | The project uses it by default, so a separate database server is not needed to try the app. |
| SQLAlchemy | A tool that lets Python work with database information using Python objects. | Saves and finds users, entries, and reflections. |
| NLTK | A Python package with tools for working with human language. | Helps split and clean words; it also includes VADER for mood scoring. |
| Tokenizing | Splitting a sentence into words. | The app does this before checking words against its topic lists. |
| Stopwords | Very common words such as “the”, “is”, and “and”. | The topic checker and word cloud remove these so they focus more on useful words. |
| Lemmatizing | Changing a word to its basic form. | For example, it can change “meetings” to “meeting”, making it easier to match a topic word. |
| Word list (lexicon) | A prepared list that connects words to scores or labels. | VADER and NRCLex use word lists. The topic checker also uses simple lists of topic words. |
| VADER | A ready-made tool that estimates whether text sounds positive, neutral, or negative. | Gives each entry a score from -1 (negative) to +1 (positive). |
| NRCLex | A tool that looks up words in a list connected to emotions. | Finds the main emotion in an entry, for example joy or sadness. |
| Sentiment / mood | The general direction of the text: positive, neutral, or negative. | Calculated with VADER. |
| Emotion | A more specific feeling, such as joy, fear, or anger. | Calculated with NRCLex. |
| Gemini | Google's AI service that can write text in response to instructions. | Writes the optional weekly reflection. |
| API | A way for one piece of software to ask another piece of software for information. | The project has a small API that returns entry information as JSON. |
| JSON | A common text format for sending structured information between programs. | Used for responses from the project's API and for chart data. |
| Password hashing | Turning a password into a protected value that cannot simply be changed back into the original password. | Bcrypt protects passwords before they are saved. |
| CSRF protection | A check that helps stop another website from secretly making a logged-in user submit a form. | Login and signup use protected Flask-WTF forms; some other forms still need this protection. |
| Test | Code that checks whether a feature behaves as expected. | pytest tests individual functions and website/API requests. |
| Unit test | A test of one small piece of code. | Tests the text analysis and journaling streak functions. |
| Integration test | A test of multiple parts working together. | Uses Flask's test browser to test login and diary pages. |

## 3. Where the main code lives

- `run.py` starts the website.
- `backend/__init__.py` builds the Flask app and connects its parts.
- `backend/config.py` reads settings such as the database address and Gemini key.
- `backend/models.py` describes the information saved in the database.
- `backend/forms.py` defines the login and signup forms.
- `backend/nlp.py` cleans text and works out topics, mood, and emotion.
- `backend/ai.py` sends the reflection request to Gemini.
- `backend/services.py` calculates writing streaks and creates word clouds.
- `backend/routes/` contains the code for login, entries, dashboard, insights, exports, and the API.
- `frontend/templates/` contains the HTML pages.
- `frontend/static/` contains the page styles.
- `tests/` contains the automated checks.

The pages are made by Flask using HTML templates. This is not a separate React or mobile application. Chart.js is used in the browser to draw the dashboard charts.

## 4. Simple block diagram

```text
Person using a web browser
          |
          v
       Flask app
          |
          +---- Login and account pages
          +---- Diary entry pages
          +---- Dashboard and exports
          +---- JSON API
          |
          +---- Text checks: topic, mood, emotion
          +---- Extra work: streak and word cloud
          +---- Weekly reflection request ------> Google Gemini
          |
          v
      SQLAlchemy
          |
          v
  SQLite database file

Flask sends HTML pages back to the browser.
Chart.js draws the charts in the browser.
```

### How to explain the diagram

> The browser sends a request to the Flask app. Flask checks which page or action was requested. The app can analyse the diary text and save it in the database. It then sends a page or data back to the browser. Gemini is only used for the weekly written reflection.

## 5. What happens when someone saves an entry?

1. The signed-in user writes a diary entry and may add their own tags.
2. The app checks the text for topic words. It counts matches for five topics: Work, Health, Relationships, Personal Development, and Hobbies.
3. VADER reads the original text and gives it a mood score and label.
4. NRCLex checks the original text and picks the strongest emotion it finds.
5. The app saves the entry and these results with the signed-in user's account.
6. The entries page can show the saved entry. The dashboard can use its saved mood score in charts.
7. If the user edits the entry, the app checks the new text again and updates the topic, mood, and emotion.

A useful detail: topic matching uses cleaned-up words. Mood and emotion checking use the original text.

## 6. How the text checks work

### Topic

The app has five lists of words, one list for each topic. For example, “meeting” and “deadline” are in the Work list. The app counts how many words from the entry match each list. The topic with the most matches is chosen. If there are no matches, the app chooses Personal Development.

This is a simple word-matching method. It does not understand the full meaning of a sentence. For example, it may not understand a new word or a word used in an unusual way.

### Mood with VADER

VADER is a ready-made text checker that looks at words and some writing clues, such as punctuation and negation. It gives a number from -1 to +1:

- -1 means strongly negative.
- 0 means neutral or mixed.
- +1 means strongly positive.

This project uses these cut-offs: 0.05 or higher is Positive; -0.05 or lower is Negative; values between those are Neutral.

The number is saved as well as the label. The dashboard can average the numbers to show a trend over time.

### Emotion with NRCLex

NRCLex uses a prepared list connecting words to emotions. It counts the emotion matches and returns the strongest one, such as joy, sadness, anger, or fear. If no emotion is found, the app returns “neutral”. It keeps one main emotion, not every emotion in the entry.

Mood and emotion are different. Mood is the broad positive-to-negative result. Emotion gives a more specific feeling. A negative entry could have sadness as its main emotion, or anger.

### Important limit of both tools

These tools match words and patterns. They do not understand every sentence the way a person does. They may get sarcasm, complicated sentences, or words whose meaning depends on context wrong.

## 7. Dashboard, streak, Gemini, and exports

### Dashboard

The dashboard looks at the signed-in user's entries from the last 30 days. It calculates each day's average mood score and a seven-day average to make the trend easier to see. It also shows the total entries, average score, most common topic, emotion counts, and a seven-day or 30-day chart.

### Writing streak

A streak is the number of calendar days in a row on which the user wrote at least one entry. The project still counts the streak if the most recent entry was yesterday. If the user missed both today and yesterday, the streak is zero.

### Weekly Gemini reflection

The app takes up to seven of the user's latest entries and sends a short part of each entry, its date, topic, and mood results to Gemini. Gemini is asked to write three short paragraphs: one about the week's feelings, one about repeated topics, and one with a practical suggestion. The app saves the result and usually shows it again for seven days instead of asking Gemini every time.

Because entry text is sent to an outside service for this feature, do not say that all journal information stays only on the user's computer. The code uses the latest seven entries, which are not necessarily all from the last seven calendar days.

### Database

The project saves three kinds of information:

- **User:** username and protected password value.
- **Diary entry:** text, topic, mood, score, emotion, tags, date, and owner.
- **Weekly reflection:** Gemini's text, date, and owner.

Most entry and reflection searches include the signed-in user's id. SQLite is used by default. The setting can be changed to another database, but changing that setting alone does not make the project ready for a large live service.

### API and files

The API returns information in JSON. It can list entries, add an entry, get one entry, delete an entry, and return basic statistics. It uses the same browser sign-in session. It does not have an edit-entry API action or a separate token-based login system.

CSV is a table-like file that spreadsheet programs can open. PDF is a document that is easy to read or print. The app can download either format. It can also make a word cloud from the user's saved entries.

## 8. Why these tools and choices make sense

| Choice | Simple reason | What to keep in mind |
|---|---|---|
| Flask | It lets Python handle website pages and requests. | The developer must decide how to organize and protect the app. |
| Separate route groups | Login code and diary code are easier to find when kept apart. | The website and API have some similar work in separate places. |
| HTML templates | The server can build pages without a separate frontend project. | Pages and server code are closely connected. |
| SQLite | Easy to run locally; no separate database service is needed. | Not a good choice for many people writing at the same time. |
| Save analysis with each entry | The app does not need to repeat the same checks whenever it shows an entry. | If the analysis rules change later, old results may need to be recalculated. |
| Word lists for topics | Easy to understand, quick, and does not need examples for training. | It can miss words and misunderstand context. |
| VADER for mood | Ready to use, quick, and made for short informal text. | It is not always right; it needs better testing on realistic examples. |
| NRCLex for emotion | Adds a specific emotion, not just positive or negative. | It looks at word matches and may miss the meaning of a full sentence. |
| Gemini for reflections | It can write a readable summary in ordinary language. | It needs the internet, may cost money, and receives parts of the user's writing. |
| Save reflections for seven days | Avoids making the same Gemini request every time the page opens. | The current app also saves error messages, which should be improved. |
| Test database in memory | Tests do not need to use or change the normal database file. | Passing tests does not prove the app is ready for a real public launch. |

## 9. Things to improve (know these if asked)

It is good to know what the project does not yet handle well. You can explain these as future improvements.

- Some forms that change data do not have CSRF checks. I would add protection to every form that changes or deletes information.
- The app turns off HTTPS certificate checking in its startup code. That is unsafe for real use. I would remove that setting and keep normal certificate checking enabled.
- Logging out uses a web link. It would be better to make logout a protected form action.
- If Gemini is unavailable, the error text can be saved like a successful reflection. I would only save a real generated reflection.
- The mood comparison checks just 15 short examples written and labelled for the script. This is too small to prove how accurate VADER is in general. I would test it on many more realistic examples.
- The project contains 31 test functions. That does not tell us whether they pass; the tests must be run to know that.
- The topic checker uses fixed word lists. A future version could learn from examples that people have labelled, but that would need enough good examples and careful testing.
- SQLite and the simple database update code are suitable for a small project, not a large service with many active users.
- The API is small and uses the browser session. It needs more work before a separate mobile or frontend app could rely on it fully.

### A good answer about improvements

> First, I would improve security by checking all forms and keeping HTTPS certificate checks on. Then I would run the test suite, add more real examples to test the mood checker, and improve the topic checker using labelled examples. I would also use a proper database upgrade tool if the project grew.

## 10. Answers to the questions in the attached sheet

### Summary of the project

> JournalJourney is a diary website. It lets people save and manage entries. It checks each entry for a topic, general mood, and main emotion. It then shows charts and summaries, and it can write a weekly reflection using Gemini.

### Why did you choose this project?

> People can write a lot in a diary, but it can be hard to notice changes and repeated topics by rereading everything. This project uses simple text checks and charts to help show those patterns. It also brings together a website, a database, text analysis, and an optional AI feature.

Only use this as your personal reason if it matches why you chose the project.

### What was your role? (individual project)

> This was an individual project. The finished app includes user accounts, diary entries, text checks, a dashboard, file downloads, and a weekly Gemini reflection. I can explain how the pieces work together and what I would improve.

If asked exactly which parts you personally wrote or changed, answer that part honestly. Do not guess or claim work you cannot explain.

### What tools did you use, and why?

> I used Python and Flask for the website. I used SQLite to save the data and SQLAlchemy to work with it from Python. NLTK and VADER check the general mood, and NRCLex checks the main emotion. HTML and CSS make the pages, and Chart.js draws the charts. Gemini writes the optional weekly reflection. Bcrypt protects saved passwords, and pytest checks parts of the app.

### Explain the block diagram

> A user works in a browser. The browser sends a request to Flask. Flask handles sign-in, diary entries, the dashboard, or downloads. It uses the database to save or find information. Text-checking code works out topic, mood, and emotion. Gemini is only contacted for the weekly reflection. Flask sends the result back to the browser.

### Explain the project

> A user signs in and writes an entry. The app checks its topic, mood, and main emotion, then saves the entry and those results. The user can later search or edit entries, see mood charts, download their writing, or ask for a weekly reflection. If an entry is edited, its topic and mood results are checked again.

### What did you learn?

> I learned how a website sends requests to Python code, how information is saved in a database, and how different parts of an app can be kept in separate files. I also learned the difference between broad mood and a more specific emotion, and that word-list checks have limits. The dashboard showed me how saved results can be turned into useful summaries.

Only say you learned a point if you understand it well enough to explain it.

### Which labs or companies did you visit?

> I did not visit a lab or company for this project. It was an individual software project.

Change this if you did make a visit.

### Which books or websites did you follow?

Name the sources you truly used. These official sites can help you study the tools now:

- Flask: https://flask.palletsprojects.com/
- NLTK: https://www.nltk.org/
- pytest: https://docs.pytest.org/
- Google Gen AI SDK: https://googleapis.github.io/python-genai/
- NRCLex: https://pypi.org/project/NRCLex/

Do not say you followed a source during development unless you actually did.

### What are the results?

> The project includes diary entry management, saved text-check results, a dashboard, downloads, a word cloud, a small JSON API, and an optional Gemini reflection. There are 31 test functions in the project, but the tests need to be run to check whether they pass. The mood comparison script uses only 15 examples, so I would not use it as proof of general accuracy.

### How can this help people or a company?

> It can help a person look back at their writing and notice mood or topic patterns. Similar ideas could help summarize feedback or personal notes. This is a learning project, not a medical tool. Diary entries are sensitive, so a real public version would need stronger security and clear privacy protections.

### What are the limitations?

> The topic checker depends on a small set of words. Mood and emotion checks can misunderstand context or sarcasm. The mood comparison uses very few examples. The project uses a simple local database, and parts of the security and API need improvement. Also, the weekly reflection sends some diary text to Gemini.

### What steps did you follow?

> The app takes an entry, checks it for topic, mood, and emotion, saves it, and uses the saved information to make dashboard summaries. Other features let the user search, edit, delete, or download entries. The weekly reflection is made separately with Gemini when requested.

If asked about how you personally worked on the project, explain your real process separately.

### What problems did you face?

A possible technical answer, if it matches your experience:

> One challenge is that the app uses several language tools, and each needs the right language data and setup. Another is making a useful mood chart when some days have no entries. External services such as Gemini can also fail, so the app needs to show a message rather than stop working.

Do not say you personally faced these problems unless you did. You can instead call them challenges the project needs to handle.

### What software model or approach did you use?

> The app is built in layers. Flask handles website requests. Separate route groups handle different features. Helper files check text and calculate summaries. SQLAlchemy saves and reads information from SQLite. The HTML templates show the pages.

### What testing method did you use?

> The project uses pytest. Some tests check small functions, such as mood checks and writing streaks. Other tests use Flask's test browser to check sign-in, diary pages, and the JSON API. The tests use a temporary in-memory database so they do not need the normal saved database. There are 31 test functions in the files; I would run them and report the actual result before saying they pass.

### Questions about the technology

**Why use VADER?**

> VADER is quick and ready to use. It gives a number for how positive or negative a short piece of writing sounds. It does not need examples from this project to be trained. It can still make mistakes, so I would test it with more examples.

**Why use NRCLex too?**

> VADER gives the broad mood, such as positive or negative. NRCLex tries to give a more specific feeling, such as joy or anger. They answer different questions.

**Why not ask Gemini to analyse every entry?**

> That would mean more waiting, more internet use, and possibly more cost. The simple checks can run inside the app, so Gemini is saved for writing the reflection.

**Is the topic checker machine learning?**

> No. It counts matches with fixed word lists. It is a simple rule-based method, not a model trained on examples. Gemini is the generative AI part of the project.

**Is the project ready for a real company or public users?**

> It is a working project, but I would not call it ready for a public launch yet. I would improve the form security, keep HTTPS certificate checks enabled, improve testing, and use a stronger database upgrade system first.

## 11. A simple study plan

1. Run the app and check that you can sign in, save an entry, edit it, and see the dashboard.
2. Practise explaining what happens when an entry is saved. Use Section 5.
3. Learn the plain meanings of VADER, NRCLex, and the word-list topic checker.
4. Practise the short answers in Section 10. Use your own words; do not try to memorize every sentence.
5. Be ready to name one limitation and one improvement. This shows that you understand what the app can and cannot do.

After installing the project packages, these commands start the app, run its tests, and compare the mood tools:

```powershell
python run.py
python -m pytest
python -m backend.evaluation.nlp_comparison
```

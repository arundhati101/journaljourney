# Setup and Run Guide

This guide shows you how to run JournalJourney on Windows (PowerShell). It
covers the daily quick start (for when the virtual environment already exists).
It also covers the one-time setup for a new machine.

## 1. Quick Start (environment already set up)

Use this when the `.venv` folder already exists in the project. This is the
common case on the development machine. (A venv is a private, separate space
for the project's Python packages.)

### 1.1 Open a terminal in the project folder

```powershell
cd c:\Users\2513929\Downloads\journaljourney
```

### 1.2 Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

PowerShell may show an error that says running scripts is turned off. If it
does, run this one time in the current window. Then try the activate command
again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

When it is active, the prompt starts with `(.venv)`.

### 1.3 Run the application

```powershell
python run.py
```

Then open a browser and go to:

```text
http://127.0.0.1:5000
```

Press `Ctrl + C` in the terminal to stop the server.

## 2. Fresh Machine Setup (one time)

Use this the first time you run the project on a new computer. Also use it if
the `.venv` folder is missing.

```powershell
# 1. Go to the project folder
cd c:\Users\2513929\Downloads\journaljourney

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create the .env file (see Section 4) with your keys

# 6. Run
python run.py
```

The database (`instance\site.db`) is made by itself on the first run. So you do
not need to set up the database by hand.

## 3. Other Useful Commands

Run these with the virtual environment active.

Run the test suite (31 unit and integration tests):

```powershell
python -m pytest
```

Run the NLP model comparison (VADER vs TextBlob):

```powershell
python -m backend.evaluation.nlp_comparison
```

## 4. Environment Variables (.env)

Create a file named `.env` in the project root. Put these keys in it:

```text
GEMINI_API_KEY=your_key_here
SECRET_KEY=a_long_random_string
DATABASE_URL=sqlite:///site.db
```

- `GEMINI_API_KEY` — needed only for the AI Insights page. Get a free key at
  <https://aistudio.google.com/apikey>. Every other feature works without it.
- `SECRET_KEY` — used to sign sessions. Any long random string is fine for
  development.
- `DATABASE_URL` — optional. It defaults to SQLite. Set a PostgreSQL DSN here to
  use PostgreSQL instead.

The `.env` file is listed in `.gitignore`. So your keys are never committed.

## 5. Notes and Troubleshooting

- You activate the virtual environment one time per terminal window. If you
  close the terminal, do Steps 1.1 and 1.2 again.
- If `python` is not found after you activate, call the interpreter directly:

  ```powershell
  .\.venv\Scripts\python.exe run.py
  ```

- If port 5000 is already in use, stop the other process. Or change the port in
  `run.py` (for example `app.run(debug=True, port=5001)`).
- The first word-cloud request can take a few seconds. This is because the
  plotting library builds its font cache. It is fast on the next requests.
- Dependencies are already installed in the existing `.venv`. So you need
  `pip install` only on a fresh machine, or after you move the project.

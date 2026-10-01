# REST API Reference

JournalJourney gives you a JSON API under the `/api` prefix. It uses the same
models and NLP pipeline [the code that reads and labels your text] as the HTML
interface. So an entry made through the API is categorised, scored, and
emotion-tagged in the same way as one made in the browser.

## 1. Base URL

```text
http://127.0.0.1:5000/api
```

## 2. Authentication

The API uses the same session cookie [a small file that proves you are logged
in] as the normal login flow (`POST /login`). A request with no valid session
gets back this:

```json
{ "error": "Authentication required" }
```

The HTTP status is `401`. Login is a CSRF-protected [protected against fake
requests] HTML form. So an API client must first log in through `/login` to
get a session cookie. A token-based way for fully separate clients is planned
for later.

## 3. Content Type

All request bodies and responses use `application/json`.

## 4. Endpoints

### 4.1 List entries

```text
GET /api/entries
```

Returns the logged-in user's entries, newest first.

Response `200`:

```json
{
  "entries": [
    {
      "id": 12,
      "text": "Great gym session, feeling strong",
      "category": "Health",
      "sentiment": "Positive",
      "sentiment_score": 0.6249,
      "emotion": "joy",
      "tags": ["fitness"],
      "timestamp": "2026-07-30T09:05:11"
    }
  ]
}
```

### 4.2 Create an entry

```text
POST /api/entries
```

Request body:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | string | yes | The entry body. Whitespace-only text is rejected. |
| tags | string | no | Comma-separated tags. |

The server runs the full NLP pipeline and saves the labels it finds.

Response `201`:

```json
{
  "entry": {
    "id": 13,
    "text": "Tough day at work but I pushed through",
    "category": "Work",
    "sentiment": "Positive",
    "sentiment_score": 0.2732,
    "emotion": "trust",
    "tags": ["work"],
    "timestamp": "2026-07-30T18:22:04"
  }
}
```

Error `400` when `text` is missing or empty:

```json
{ "error": "'text' is required" }
```

### 4.3 Get a single entry

```text
GET /api/entries/<id>
```

Response `200`:

```json
{ "entry": { "id": 13, "text": "...", "category": "Work", "...": "..." } }
```

Response `404` when the entry does not exist or belongs to another user:

```json
{ "error": "Not found" }
```

### 4.4 Delete an entry

```text
DELETE /api/entries/<id>
```

Response `200`:

```json
{ "deleted": 13 }
```

Response `404` when the entry does not exist or is not owned by the caller.

### 4.5 Statistics

```text
GET /api/stats
```

Response `200`:

```json
{
  "total_entries": 24,
  "average_sentiment": 0.1832,
  "streak": 5,
  "categories": { "Work": 10, "Health": 6, "Hobbies": 8 },
  "emotions": { "joy": 9, "fear": 4, "trust": 6, "sadness": 5 }
}
```

| Field | Meaning |
|-------|---------|
| total_entries | Count of the user's entries. |
| average_sentiment | Mean VADER compound score across scored entries. |
| streak | Consecutive days (ending today or yesterday) with at least one entry. |
| categories | Entry count per auto-assigned category. |
| emotions | Entry count per dominant emotion. |

## 5. Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success. |
| 201 | Entry created. |
| 400 | Malformed request (for example, missing `text`). |
| 401 | Not authenticated. |
| 404 | Resource not found or not owned by the caller. |
| 500 | Server error (returned as JSON for `/api/` paths). |

## 6. Examples

Log in and save the session cookie. Then use it for your API calls:

```bash
# 1. Obtain a session cookie (requires a valid CSRF token in a real client).
#    For scripted use, prefer a browser session or a test client.

# 2. Create an entry.
curl -X POST http://127.0.0.1:5000/api/entries \
     -H "Content-Type: application/json" \
     --cookie "session=<cookie>" \
     -d '{"text": "Learned something new today", "tags": "learning"}'

# 3. Fetch statistics.
curl --cookie "session=<cookie>" http://127.0.0.1:5000/api/stats
```

Python (using the test client pattern from the suite):

```python
from backend import create_app
app = create_app()
client = app.test_client()
# ... log in via client.post('/login', ...) ...
resp = client.post('/api/entries', json={'text': 'A productive morning'})
print(resp.get_json())
```

## 7. Design Notes

- The API is kept thin on purpose. It hands the work to the same `nlp`,
  `services`, and `models` code as the HTML views. So the two ways of using the
  app always behave the same.
- Every endpoint filters by the logged-in `user_id`. This makes sure API
  clients can only see or change their own data.
- Errors under `/api/` are always JSON. The same handlers underneath return
  HTML pages for browser routes.

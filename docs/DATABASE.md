# Database Design

JournalJourney saves data with the SQLAlchemy ORM (a tool that lets code work
with a database). The default engine is SQLite (`instance/site.db`). It is made
for you on the first run. You can set the `DATABASE_URL` environment variable to
a PostgreSQL DSN. This changes the engine. You do not need to change any code.

## 1. Entity-Relationship Diagram

```text
+------------------+           +----------------------------+
|      User        |           |        DiaryEntry          |
+------------------+           +----------------------------+
| id (PK)          | 1       * | id (PK)                    |
| username (unique)|-----------| text                       |
| password (hash)  |           | category                   |
+------------------+           | sentiment                  |
        |                      | sentiment_score            |
        |                      | emotion                    |
        | 1                    | tags                       |
        |                      | timestamp                  |
        |                      | user_id (FK -> User.id)    |
        |                      +----------------------------+
        |
        | *
+---------------------------+
|      WeeklyInsight        |
+---------------------------+
| id (PK)                   |
| insight_text             |
| generated_on             |
| user_id (FK -> User.id)  |
+---------------------------+
```

Cardinality:

- One `User` has many `DiaryEntry` rows (1..*).
- One `User` has many `WeeklyInsight` rows (1..*).
- `DiaryEntry` and `WeeklyInsight` each belong to exactly one `User`.

## 2. Table Schemas

### 2.1 user

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary key | Surrogate identifier. |
| username | String(20) | Unique, not null | Login name. |
| password | String(60) | Not null | Bcrypt hash (never plaintext). |

### 2.2 diary_entry

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary key | Surrogate identifier. |
| text | Text | Not null | The journal entry body. |
| category | String(50) | Not null | Auto-assigned life area. |
| sentiment | String(20) | Not null | Positive / Neutral / Negative. |
| sentiment_score | Float | Nullable | VADER compound score in [-1, +1]. |
| emotion | String(20) | Nullable | Dominant NRC emotion. |
| tags | String(200) | Nullable | Comma-separated user tags. |
| timestamp | DateTime | Default now | Creation time. |
| user_id | Integer | Foreign key -> user.id, not null | Owner. |

### 2.3 weekly_insight

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | Primary key | Surrogate identifier. |
| insight_text | Text | Not null | Gemini-generated reflection. |
| generated_on | DateTime | Default now | When it was produced (drives the 7-day cache). |
| user_id | Integer | Foreign key -> user.id, not null | Owner. |

## 3. Derived and Computed Fields

Some values in the UI are computed. They are not stored:

- **tag_list** — a model property. It splits the `tags` string into a clean
  list. The list is used for display and for the JSON API.
- **Journaling streak** — computed when needed from entry timestamps
  (`services.current_streak`). It is not stored.
- **Dashboard datasets and emotion counts** — added up for each request from
  `diary_entry` rows. They are not stored.

## 4. Migration Strategy

The app is migration-safe for the extra columns added during development. When
the app starts, `backend/__init__.py::_ensure_schema()` does this:

1. `db.create_all()` — creates any missing tables. It never changes a table
   that already exists.
2. Column backfill — it looks at `diary_entry`. It runs `ALTER TABLE ... ADD
   COLUMN` for any of `sentiment_score`, `emotion`, or `tags` that are missing.
   This upgrades an older database that was created before these features
   existed.

Also, `_backfill_sentiment_scores()` computes and stores the VADER compound
score for any old entries whose `sentiment_score` is null. Then they show
correctly on the trend chart.

For a production PostgreSQL deployment, use a dedicated migration tool such as
Alembic instead of the simple `ALTER TABLE` approach. This is listed as future
work.

## 5. Indexing and Integrity

- Primary keys are indexed automatically.
- `user.username` has a unique constraint. This stops duplicate accounts.
- Foreign keys (`diary_entry.user_id`, `weekly_insight.user_id`) enforce
  referential integrity to `user.id`.
- Application-level access control adds `WHERE user_id = :current_user` to every
  entry and insight query. So no user can read or change another user's rows.

## 6. Example Records

`user`

| id | username | password |
|----|----------|----------|
| 1 | arundhati | $2b$12$... (bcrypt) |

`diary_entry`

| id | text | category | sentiment | sentiment_score | emotion | tags | user_id |
|----|------|----------|-----------|-----------------|---------|------|---------|
| 1 | "Great gym session, feeling strong" | Health | Positive | 0.6249 | joy | fitness | 1 |
| 2 | "Stressful deadline with my manager" | Work | Negative | -0.4019 | fear | work | 1 |

`weekly_insight`

| id | insight_text | generated_on | user_id |
|----|--------------|--------------|---------|
| 1 | "This week your mood rose as ..." | 2026-07-30 09:12 | 1 |

"""Integration tests covering auth, entry CRUD, and access control."""


def test_signup_creates_account(client):
    resp = client.post('/signup', data={'username': 'newbie', 'password': 'secret12'},
                        follow_redirects=True)
    assert resp.status_code == 200
    from backend.models import User
    assert User.query.filter_by(username='newbie').first() is not None


def test_login_required_redirects_to_login(client):
    resp = client.get('/', follow_redirects=False)
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']


def test_login_success(auth_client):
    resp = auth_client.get('/')
    assert resp.status_code == 200
    assert b'JournalJourney' in resp.data


def test_login_wrong_password(client, user):
    resp = client.post('/login', data={'username': 'tester', 'password': 'wrong'},
                       follow_redirects=True)
    assert b'Invalid Username or Password' in resp.data


def test_add_and_view_entry(auth_client):
    auth_client.post('/', data={'diary_entry': 'Today I went to the gym and felt great',
                                'tags': 'health, mood'},
                     follow_redirects=True)
    resp = auth_client.get('/entries')
    assert b'went to the gym' in resp.data
    assert b'Health' in resp.data          # auto category
    assert b'health' in resp.data          # user tag


def test_edit_entry(auth_client):
    auth_client.post('/', data={'diary_entry': 'A dull neutral note'}, follow_redirects=True)
    from backend.models import DiaryEntry
    entry = DiaryEntry.query.first()
    auth_client.post(f'/edit_entry/{entry.id}',
                     data={'diary_entry': 'I am absolutely thrilled and joyful now', 'tags': ''},
                     follow_redirects=True)
    from backend import db
    updated = db.session.get(DiaryEntry, entry.id)
    assert 'thrilled' in updated.text
    assert updated.sentiment == 'Positive'


def test_delete_entry(auth_client):
    auth_client.post('/', data={'diary_entry': 'Delete me please'}, follow_redirects=True)
    from backend.models import DiaryEntry
    entry = DiaryEntry.query.first()
    auth_client.post(f'/delete_entry/{entry.id}', follow_redirects=True)
    from backend import db
    assert db.session.get(DiaryEntry, entry.id) is None


def test_user_cannot_see_others_entries(client, app):
    from backend import db, bcrypt
    from backend.models import User, DiaryEntry
    with app.app_context():
        hashed = bcrypt.generate_password_hash('pw').decode('utf-8')
        a = User(username='alice', password=hashed)
        b = User(username='bob', password=hashed)
        db.session.add_all([a, b])
        db.session.commit()
        db.session.add(DiaryEntry(text="alice secret", category="Work",
                                  sentiment="Neutral", sentiment_score=0.0, user_id=a.id))
        db.session.commit()

    client.post('/login', data={'username': 'bob', 'password': 'pw'}, follow_redirects=True)
    resp = client.get('/entries')
    assert b'alice secret' not in resp.data


def test_dashboard_accessible(auth_client):
    assert auth_client.get('/dashboard').status_code == 200


def test_export_csv(auth_client):
    auth_client.post('/', data={'diary_entry': 'A day to export'}, follow_redirects=True)
    resp = auth_client.get('/export/csv')
    assert resp.status_code == 200
    assert resp.mimetype == 'text/csv'
    assert b'A day to export' in resp.data


def test_404_returns_error_page(auth_client):
    resp = auth_client.get('/no-such-page')
    assert resp.status_code == 404
    assert b'404' in resp.data


def test_insights_retries_instead_of_using_cached_gemini_error(auth_client, monkeypatch):
    from backend import db
    from backend.models import WeeklyInsight

    db.session.add(WeeklyInsight(
        insight_text=("Could not generate your insight right now. Please try again later. "
                      "(404 NOT_FOUND: retired model)"),
        user_id=1,
    ))
    db.session.commit()
    monkeypatch.setattr(
        'backend.routes.insights.generate_weekly_insight',
        lambda entries, api_key, model: 'A fresh reflection.',
    )

    response = auth_client.get('/insights')

    assert b'A fresh reflection.' in response.data
    assert WeeklyInsight.query.count() == 1
    assert WeeklyInsight.query.first().insight_text == 'A fresh reflection.'


def test_insights_does_not_save_new_gemini_error(auth_client, monkeypatch):
    from backend import db
    from backend.models import WeeklyInsight

    monkeypatch.setattr(
        'backend.routes.insights.generate_weekly_insight',
        lambda entries, api_key, model: 'Could not generate your insight right now. (API error)',
    )

    response = auth_client.get('/insights')

    assert b'Could not generate your insight right now.' in response.data
    assert WeeklyInsight.query.count() == 0

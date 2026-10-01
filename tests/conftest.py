import pytest
from backend import create_app, db, bcrypt
from backend.config import TestConfig
from backend.models import User


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    with app.app_context():
        hashed = bcrypt.generate_password_hash('password123').decode('utf-8')
        u = User(username='tester', password=hashed)
        db.session.add(u)
        db.session.commit()
        return {'username': 'tester', 'password': 'password123', 'id': u.id}


@pytest.fixture
def auth_client(client, user):
    client.post('/login', data={
        'username': user['username'],
        'password': user['password'],
    }, follow_redirects=True)
    return client

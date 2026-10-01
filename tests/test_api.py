"""Tests for the JSON REST API."""


def test_api_requires_auth(client):
    resp = client.get('/api/entries')
    assert resp.status_code == 401
    assert resp.get_json()['error']


def test_api_create_and_list(auth_client):
    create = auth_client.post('/api/entries', json={'text': 'API entry about work and my manager',
                                                    'tags': 'work'})
    assert create.status_code == 201
    body = create.get_json()['entry']
    assert body['category'] == 'Work'
    assert body['tags'] == ['work']

    listing = auth_client.get('/api/entries')
    assert listing.status_code == 200
    assert len(listing.get_json()['entries']) == 1


def test_api_create_requires_text(auth_client):
    resp = auth_client.post('/api/entries', json={'text': '   '})
    assert resp.status_code == 400


def test_api_get_single(auth_client):
    created = auth_client.post('/api/entries', json={'text': 'single entry'}).get_json()['entry']
    resp = auth_client.get(f"/api/entries/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()['entry']['text'] == 'single entry'


def test_api_delete(auth_client):
    created = auth_client.post('/api/entries', json={'text': 'to delete'}).get_json()['entry']
    resp = auth_client.delete(f"/api/entries/{created['id']}")
    assert resp.status_code == 200
    assert auth_client.get(f"/api/entries/{created['id']}").status_code == 404


def test_api_stats(auth_client):
    auth_client.post('/api/entries', json={'text': 'I feel wonderful and happy'})
    auth_client.post('/api/entries', json={'text': 'This is a terrible awful day'})
    resp = auth_client.get('/api/stats')
    data = resp.get_json()
    assert data['total_entries'] == 2
    assert 'average_sentiment' in data
    assert 'categories' in data


def test_api_404_is_json(auth_client):
    resp = auth_client.get('/api/entries/99999')
    assert resp.status_code == 404
    assert resp.is_json

import pytest
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json == {"message": "Bienvenue sur iTransfer API"}

def test_upload_no_file(client):
    response = client.post('/upload', data={})
    assert response.status_code == 400
    assert "error" in response.json

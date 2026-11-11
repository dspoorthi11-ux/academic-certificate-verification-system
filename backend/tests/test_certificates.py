from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_certificates_list():
    response = client.get('/api/certificates')
    assert response.status_code in {200, 401}

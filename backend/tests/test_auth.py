from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app

def test_register_and_login():
    email = f"demo-{uuid4().hex}@example.com"
    with TestClient(app) as client:
        response = client.post('/api/auth/register', json={
            'email': email,
            'password': 'Password123',
            'full_name': 'Demo User',
            'role': 'student',
        })
        assert response.status_code in {200, 201}

        login = client.post('/api/auth/login', json={
            'email': email,
            'password': 'Password123',
        })
        assert login.status_code == 200
        assert 'access_token' in login.json()

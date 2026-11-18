from uuid import uuid4
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from jose import jwt
from app.main import app
from app.db.session import SessionLocal
from app.core.config import get_settings
from app.models.user import User


def test_registration_login_and_protected_profile():
    email = f'{uuid4().hex}@example.com'
    with TestClient(app) as client:
        registered = client.post('/api/v1/auth/register', json={'name': 'Test User', 'email': email, 'password': 'correct horse battery staple'})
        assert registered.status_code == 201
        token = registered.json()['access_token']

        duplicate = client.post('/api/v1/auth/register', json={'name': 'Test User', 'email': email, 'password': 'correct horse battery staple'})
        assert duplicate.status_code == 409

        wrong_password = client.post('/api/v1/auth/login', json={'email': email, 'password': 'wrong password'})
        assert wrong_password.status_code == 401

        logged_in = client.post('/api/v1/auth/login', json={'email': email, 'password': 'correct horse battery staple'})
        assert logged_in.status_code == 200
        assert logged_in.json()['token_type'] == 'bearer'

        profile = client.get('/api/v1/profile/me', headers={'Authorization': f'Bearer {token}'})
        assert profile.status_code == 200
        assert profile.json()['email'] == email

        unauthenticated = client.get('/api/v1/profile/me')
        assert unauthenticated.status_code == 401
        expired_token = jwt.encode(
            {'sub': email, 'exp': datetime.now(timezone.utc) - timedelta(minutes=1)},
            get_settings().jwt_secret,
            algorithm=get_settings().jwt_algorithm,
        )
        expired = client.get('/api/v1/profile/me', headers={'Authorization': f'Bearer {expired_token}'})
        assert expired.status_code == 401
        short_password = client.post('/api/v1/auth/register', json={'name': 'Test User', 'email': f'{uuid4().hex}@example.com', 'password': 'short'})
        assert short_password.status_code == 422
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
            db.commit()

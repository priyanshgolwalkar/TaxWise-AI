from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.document import Document
from app.models.user import User


def register(client, name):
    email = f'{uuid4().hex}@example.com'
    response = client.post('/api/v1/auth/register', json={'name': name, 'email': email, 'password': 'test-password'})
    return response.json()['access_token'], email


def test_document_upload_persists_metadata_and_extraction(monkeypatch):
    stored = []
    monkeypatch.setattr('app.api.routers.documents.storage.save', lambda content, filename, content_type: stored.append(content) or f'documents/{uuid4().hex}.png')
    monkeypatch.setattr('app.api.routers.documents.extract_fields', lambda path: {'document_type': 'financial_document', 'fields': {'annual_income': {'value': '1000000', 'confidence': 'detected', 'needs_review': True}}, 'raw_text': 'income', 'missing_fields': ['tds'], 'validation_errors': [], 'requires_user_verification': True})
    with TestClient(app) as client:
        token, email = register(client, 'Uploader')
        response = client.post('/api/v1/documents/upload', headers={'Authorization': f'Bearer {token}'}, files={'file': ('salary.png', b'valid-image-bytes', 'image/png')})
        assert response.status_code == 201
        body = response.json()
        assert body['status'] == 'needs_review'
        assert body['extracted_data']['missing_fields'] == ['tds']
        assert stored == [b'valid-image-bytes']
        listed = client.get('/api/v1/documents', headers={'Authorization': f'Bearer {token}'})
        assert listed.status_code == 200
        assert listed.json()[0]['filename'] == 'salary.png'
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
            db.commit()


def test_document_upload_rejects_invalid_type():
    with TestClient(app) as client:
        token, _ = register(client, 'Invalid Type User')
        response = client.post('/api/v1/documents/upload', headers={'Authorization': f'Bearer {token}'}, files={'file': ('notes.txt', b'not allowed', 'text/plain')})
        assert response.status_code == 415


def test_document_upload_requires_authentication():
    with TestClient(app) as client:
        response = client.post('/api/v1/documents/upload', files={'file': ('salary.png', b'bytes', 'image/png')})
        assert response.status_code == 401


def test_documents_are_isolated_by_user(monkeypatch):
    monkeypatch.setattr('app.api.routers.documents.storage.save', lambda content, filename, content_type: f'documents/{uuid4().hex}.png')
    monkeypatch.setattr('app.api.routers.documents.extract_fields', lambda path: {'document_type': 'financial_document', 'fields': {}, 'raw_text': '', 'missing_fields': ['annual_income', 'tds'], 'validation_errors': [], 'requires_user_verification': True})
    with TestClient(app) as client:
        first_token, first_email = register(client, 'First User')
        second_token, second_email = register(client, 'Second User')
        upload = client.post('/api/v1/documents/upload', headers={'Authorization': f'Bearer {first_token}'}, files={'file': ('first.png', b'bytes', 'image/png')})
        assert upload.status_code == 201
        assert client.get('/api/v1/documents', headers={'Authorization': f'Bearer {second_token}'}).json() == []
    with SessionLocal() as db:
        for email in (first_email, second_email):
            user = db.query(User).filter(User.email == email).first()
            if user:
                db.delete(user)
        db.commit()

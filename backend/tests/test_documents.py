from pathlib import Path
from uuid import uuid4
from fastapi.testclient import TestClient
import pytest
from pdf2image.exceptions import PDFInfoNotInstalledError
from pytesseract import TesseractNotFoundError
from app.main import app
from app.db.session import SessionLocal
from app.models.document import Document
from app.models.user import User
from app.services.document_processing.pipeline import DocumentProcessingUnavailable, extract_fields, preprocess_image


def register(client, name):
    email = f'{uuid4().hex}@example.com'
    response = client.post('/api/v1/auth/register', json={'name': name, 'email': email, 'password': 'test-password'})
    return response.json()['access_token'], email


def test_document_upload_persists_metadata_and_extraction(monkeypatch):
    stored = []
    temporary_paths = []
    monkeypatch.setattr('app.api.routers.documents.storage.save', lambda content, filename, content_type: stored.append(content) or f'documents/{uuid4().hex}.png')
    def extract(path):
        temporary_paths.append(Path(path))
        return {'document_type': 'financial_document', 'fields': {'annual_income': {'value': '1000000', 'confidence': 'detected', 'needs_review': True}}, 'raw_text': 'income', 'missing_fields': ['tds'], 'validation_errors': [], 'requires_user_verification': True}
    monkeypatch.setattr('app.api.routers.documents.extract_fields', extract)
    with TestClient(app) as client:
        token, email = register(client, 'Uploader')
        response = client.post('/api/v1/documents/upload', headers={'Authorization': f'Bearer {token}'}, files={'file': ('salary.png', b'valid-image-bytes', 'image/png')})
        assert response.status_code == 201
        body = response.json()
        assert body['status'] == 'needs_review'
        assert body['extracted_data']['missing_fields'] == ['tds']
        assert stored == [b'valid-image-bytes']
        assert temporary_paths and all(not path.exists() for path in temporary_paths)
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


def test_document_upload_reports_storage_failure(monkeypatch):
    monkeypatch.setattr('app.api.routers.documents.extract_fields', lambda path: {'fields': {}, 'raw_text': '', 'missing_fields': [], 'validation_errors': [], 'requires_user_verification': True})
    def fail_storage(content, filename, content_type):
        raise OSError('private local storage detail')
    monkeypatch.setattr('app.api.routers.documents.storage.save', fail_storage)
    with TestClient(app) as client:
        token, email = register(client, 'Storage Failure User')
        response = client.post('/api/v1/documents/upload', headers={'Authorization': f'Bearer {token}'}, files={'file': ('salary.png', b'bytes', 'image/png')})
        assert response.status_code == 503
        assert response.json()['detail'] == 'Document storage is unavailable.'
        assert 'private local storage detail' not in response.text
        assert client.get('/api/v1/documents', headers={'Authorization': f'Bearer {token}'}).json() == []
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
            db.commit()


def test_pdf_processing_reports_missing_poppler(monkeypatch, tmp_path):
    def missing_poppler(*args, **kwargs):
        raise PDFInfoNotInstalledError('private executable path')
    monkeypatch.setattr('app.services.document_processing.pipeline.convert_from_path', missing_poppler)

    with pytest.raises(DocumentProcessingUnavailable, match='Poppler'):
        preprocess_image(str(tmp_path / 'document.pdf'))


def test_ocr_extraction_preserves_review_flags_and_missing_fields(monkeypatch):
    monkeypatch.setattr('app.services.document_processing.pipeline.preprocess_image', lambda path: object())
    monkeypatch.setattr('app.services.document_processing.pipeline.pytesseract.image_to_string', lambda image: 'Gross salary 1,850,000 TDS 20,000 PAN ABCDE1234F')

    extracted = extract_fields('document.png')

    assert extracted['fields']['annual_income']['value'] == '1850000'
    assert extracted['fields']['tds']['value'] == '20000'
    assert extracted['fields']['pan']['value'] == 'ABCDE1234F'
    assert extracted['missing_fields'] == []
    assert extracted['fields']['annual_income']['needs_review'] is True
    assert extracted['fields']['tds']['needs_review'] is True
    assert extracted['requires_user_verification'] is True


def test_ocr_extraction_reports_missing_tesseract(monkeypatch):
    monkeypatch.setattr('app.services.document_processing.pipeline.preprocess_image', lambda path: object())
    def missing_tesseract(image):
        raise TesseractNotFoundError()
    monkeypatch.setattr('app.services.document_processing.pipeline.pytesseract.image_to_string', missing_tesseract)

    with pytest.raises(DocumentProcessingUnavailable, match='Tesseract'):
        extract_fields('document.png')


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

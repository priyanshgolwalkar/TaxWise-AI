from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.user import User

TAX_INPUT = {
    'assessment_year': '2025-26',
    'annual_income': 1850000,
    'standard_deduction': 0,
    'deductions_80c': 100000,
    'deductions_80d': 25000,
    'home_loan_interest': 0,
    'hra_exemption': 0,
}


def remove_user(email):
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
            db.commit()


def test_authenticated_planning_journey_persists_user_data(monkeypatch):
    email = f'{uuid4().hex}@example.com'
    password = 'test-password'
    try:
        with TestClient(app) as client:
            assert client.get('/health').json() == {'status': 'ok', 'service': 'taxwise-api'}
            registered = client.post('/api/v1/auth/register', json={'name': 'Journey User', 'email': email, 'password': password})
            assert registered.status_code == 201
            token = registered.json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}

            assert client.get('/api/v1/dashboard/', headers=headers).json()['summary']['total_documents'] == 0
            comparison = client.post('/api/v1/tax/compare', headers=headers, json=TAX_INPUT)
            assert comparison.status_code == 200

            recommendation_input = {**TAX_INPUT, 'regime': comparison.json()['recommended_regime']}
            recommendation = client.post('/api/v1/recommendations/', headers=headers, json=recommendation_input)
            assert recommendation.status_code == 200
            repeated = client.post('/api/v1/recommendations/', headers=headers, json=recommendation_input)
            assert repeated.json() == recommendation.json()

            monkeypatch.setattr('app.api.routers.documents.storage.save', lambda content, filename, content_type: f'documents/{uuid4().hex}.png')
            monkeypatch.setattr('app.api.routers.documents.extract_fields', lambda path: {'document_type': 'financial_document', 'fields': {'annual_income': {'value': '1850000', 'confidence': 'review', 'needs_review': True}}, 'raw_text': '', 'missing_fields': ['tds'], 'validation_errors': [], 'requires_user_verification': True})
            upload = client.post('/api/v1/documents/upload', headers=headers, files={'file': ('income.png', b'image-bytes', 'image/png')})
            assert upload.status_code == 201
            assert upload.json()['status'] == 'needs_review'
            assert upload.json()['extracted_data']['requires_user_verification'] is True

            dashboard = client.get('/api/v1/dashboard/', headers=headers).json()
            assert dashboard['user_profile']['name'] == 'Journey User'
            assert dashboard['summary']['total_documents'] == 1
            assert dashboard['summary']['documents_needing_verification'] == 1
            assert dashboard['recommendations']['items'] == recommendation.json()['items']

            report = client.post('/api/v1/reports/', headers=headers)
            assert report.status_code == 201
            assert report.json()['content']['regime_comparison'] == comparison.json()

            with patch('app.api.routers.assistant.get_ai_service') as factory:
                service = factory.return_value
                service.respond = AsyncMock(return_value=('Your saved comparison recommends the configured lower-liability regime.', []))
                chat = client.post('/api/v1/assistant/chat', headers=headers, json={'message': 'Explain my saved comparison'})
            assert chat.status_code == 200
            assert chat.json()['conversation_id']
            messages = client.get(f"/api/v1/assistant/conversations/{chat.json()['conversation_id']}/messages", headers=headers)
            assert [message['role'] for message in messages.json()] == ['user', 'assistant']

            assert client.get('/api/v1/profile/me').status_code == 401
            logged_in = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
            assert logged_in.status_code == 200
            relogin_headers = {'Authorization': f"Bearer {logged_in.json()['access_token']}"}
            assert client.get('/api/v1/tax/latest', headers=relogin_headers).json()['comparison'] == comparison.json()
            assert client.get('/api/v1/assistant/conversations', headers=relogin_headers).json()[0]['id'] == chat.json()['conversation_id']
    finally:
        remove_user(email)

from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User

PAYLOAD = {'assessment_year': '2025-26', 'annual_income': 1850000, 'standard_deduction': 75000, 'deductions_80c': 100000, 'deductions_80d': 25000, 'home_loan_interest': 0, 'hra_exemption': 0}


def register(client, name):
    email = f'{uuid4().hex}@example.com'
    response = client.post('/api/v1/auth/register', json={'name': name, 'email': email, 'password': 'test-password'})
    return response.json()['access_token'], email


def cleanup(emails):
    with SessionLocal() as db:
        for email in emails:
            user = db.query(User).filter(User.email == email).first()
            if user:
                db.delete(user)
        db.commit()


def test_tax_comparison_is_persisted_and_drives_dashboard_report():
    with TestClient(app) as client:
        token, email = register(client, 'Planner')
        headers = {'Authorization': f'Bearer {token}'}
        comparison = client.post('/api/v1/tax/compare', headers=headers, json=PAYLOAD)
        assert comparison.status_code == 200
        latest = client.get('/api/v1/tax/latest', headers=headers)
        assert latest.status_code == 200
        assert latest.json()['comparison']['recommended_regime'] == comparison.json()['recommended_regime']
        dashboard = client.get('/api/v1/dashboard/summary', headers=headers)
        assert dashboard.status_code == 200
        assert dashboard.json()['estimated_tax'] is not None
        report = client.get('/api/v1/reports/latest', headers=headers)
        assert report.status_code == 200
        assert report.json()['content']['regime_comparison']['recommended_regime'] == comparison.json()['recommended_regime']
    cleanup([email])


def test_recommendation_api_is_authenticated_and_user_scoped():
    with TestClient(app) as client:
        first_token, first_email = register(client, 'First Planner')
        second_token, second_email = register(client, 'Second Planner')
        first_headers = {'Authorization': f'Bearer {first_token}'}
        second_headers = {'Authorization': f'Bearer {second_token}'}
        unauthenticated = client.post('/api/v1/recommendations', json={**PAYLOAD, 'regime': 'old'})
        assert unauthenticated.status_code == 401
        created = client.post('/api/v1/recommendations/', headers=first_headers, json={**PAYLOAD, 'regime': 'old'})
        assert created.status_code == 200
        assert created.json()['regime'] == 'old'
        assert created.json()['items'][0]['applicable_regime'] == 'old'
        assert created.json()['items'][0]['explanation']
        assert created.json()['items'][0]['impact'] >= 0
        assert client.get('/api/v1/recommendations/latest', headers=second_headers).json() is None
    cleanup([first_email, second_email])


def test_dashboard_structured_response_and_report_isolation():
    with TestClient(app) as client:
        first_token, first_email = register(client, 'Dashboard Owner')
        second_token, second_email = register(client, 'Dashboard Other')
        first_headers = {'Authorization': f'Bearer {first_token}'}
        second_headers = {'Authorization': f'Bearer {second_token}'}
        assert client.get('/api/v1/dashboard/').status_code == 401
        empty_dashboard = client.get('/api/v1/dashboard/', headers=second_headers)
        assert empty_dashboard.status_code == 200
        assert empty_dashboard.json()['summary']['total_documents'] == 0
        client.post('/api/v1/tax/compare', headers=first_headers, json=PAYLOAD)
        dashboard = client.get('/api/v1/dashboard/', headers=first_headers)
        assert dashboard.status_code == 200
        assert dashboard.json()['summary']['old_regime_tax'] is not None
        report = client.post('/api/v1/reports/', headers=first_headers)
        assert report.status_code == 201
        report_id = report.json()['id']
        assert client.get(f'/api/v1/reports/{report_id}', headers=first_headers).status_code == 200
        assert client.get(f'/api/v1/reports/{report_id}', headers=second_headers).status_code == 404
        assert client.get('/api/v1/reports/', headers=second_headers).json() == []
    cleanup([first_email, second_email])

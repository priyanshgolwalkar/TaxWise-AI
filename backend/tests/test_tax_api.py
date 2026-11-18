from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User


def test_tax_compare_requires_authentication_and_returns_both_regimes():
    email = f'{uuid4().hex}@example.com'
    payload = {'assessment_year': '2025-26', 'annual_income': 1850000, 'standard_deduction': 0, 'deductions_80c': 100000, 'deductions_80d': 25000, 'home_loan_interest': 0, 'hra_exemption': 0}
    with TestClient(app) as client:
        unauthenticated = client.post('/api/v1/tax/compare', json=payload)
        assert unauthenticated.status_code == 401
        registered = client.post('/api/v1/auth/register', json={'name': 'Tax User', 'email': email, 'password': 'test-password'})
        token = registered.json()['access_token']
        response = client.post('/api/v1/tax/compare', headers={'Authorization': f'Bearer {token}'}, json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body['old_regime']['deduction_breakdown']['standard_deduction'] == 50000
        assert body['new_regime']['deduction_breakdown']['standard_deduction'] == 75000
        assert body['recommended_regime'] in {'old', 'new'}
        saved = client.get('/api/v1/tax/latest', headers={'Authorization': f'Bearer {token}'})
        assert 'standard_deduction' not in saved.json()['input_data']
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
            db.commit()


def test_tax_api_validates_unknown_rules_regime_and_amounts():
    email = f'{uuid4().hex}@example.com'
    payload = {'assessment_year': '2025-26', 'annual_income': 0, 'deductions_80c': 0}
    with TestClient(app) as client:
        registered = client.post('/api/v1/auth/register', json={'name': 'Tax User', 'email': email, 'password': 'test-password'})
        headers = {'Authorization': f"Bearer {registered.json()['access_token']}"}

        assert client.post('/api/v1/tax/compare', headers=headers, json={**payload, 'assessment_year': '2099-00'}).status_code == 422
        assert client.post('/api/v1/tax/calculate?regime=invalid', headers=headers, json=payload).status_code == 422
        assert client.post('/api/v1/tax/compare', headers=headers, json={**payload, 'annual_income': -1}).status_code == 422

        zero_income = client.post('/api/v1/tax/compare', headers=headers, json=payload)
        assert zero_income.status_code == 200
        assert zero_income.json()['old_regime']['final_liability'] == 0
        assert zero_income.json()['new_regime']['final_liability'] == 0

    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
            db.commit()

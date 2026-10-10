from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User


def test_tax_compare_requires_authentication_and_returns_both_regimes():
    email = f'{uuid4().hex}@example.com'
    payload = {'assessment_year': '2025-26', 'annual_income': 1850000, 'standard_deduction': 75000, 'deductions_80c': 100000, 'deductions_80d': 25000, 'home_loan_interest': 0, 'hra_exemption': 0}
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
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if user:
            db.delete(user)
            db.commit()

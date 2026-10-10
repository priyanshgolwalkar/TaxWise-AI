from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.dashboard import build_dashboard

router = APIRouter(prefix='/dashboard', tags=['dashboard'])

@router.get('/')
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return build_dashboard(user, db)

@router.get('/summary', include_in_schema=False)
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = build_dashboard(user, db)
    return {
        'calculation': data['latest_tax_calculation']['comparison'] if data['latest_tax_calculation'] else None,
        'recommended_regime': data['summary']['recommended_regime'],
        'estimated_tax': data['summary']['estimated_tax'],
        'potential_savings': data['summary']['potential_savings'],
        'documents': data['document_summary'][:5],
        'recommendations': data['recommendations'],
    }

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.planning import Report
from app.models.user import User
from app.services.reports import generate_report, serialize_report
from app.models.planning import TaxCalculationRecord

router = APIRouter(prefix='/reports', tags=['reports'])

@router.post('/', status_code=status.HTTP_201_CREATED)
def create_report(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return generate_report(user, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get('/')
def list_reports(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(Report).filter(Report.user_id == user.id).order_by(Report.created_at.desc()).all()
    return [serialize_report(report) for report in reports]

@router.get('/latest', include_in_schema=False)
def latest_report(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.user_id == user.id).order_by(Report.created_at.desc()).first()
    if report is None and db.query(TaxCalculationRecord).filter(TaxCalculationRecord.user_id == user.id).first():
        return generate_report(user, db)
    return serialize_report(report) if report else {'title': 'Tax Planning Report', 'status': 'empty', 'sections': [], 'generated_at': None}

@router.get('/{report_id}')
def get_report(report_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == user.id).first()
    if report is None:
        raise HTTPException(status_code=404, detail='Report not found')
    return serialize_report(report)

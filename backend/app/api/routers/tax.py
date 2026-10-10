from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.planning import TaxCalculationRecord
from app.schemas.common import TaxInput
from app.services.tax_engine import calculate_tax, compare_regimes
router = APIRouter(prefix='/tax', tags=['tax'])
@router.post('/calculate')
def calculate(payload: TaxInput, regime: str = 'old', user: User = Depends(get_current_user)): return calculate_tax(payload.model_dump(), regime)
@router.post('/compare')
def compare(payload: TaxInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
	comparison = compare_regimes(payload.model_dump())
	db.add(TaxCalculationRecord(user_id=user.id, assessment_year=payload.assessment_year, input_data=payload.model_dump(), comparison=comparison))
	db.commit()
	return comparison

@router.get('/latest')
def latest(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	return db.query(TaxCalculationRecord).filter(TaxCalculationRecord.user_id == user.id).order_by(TaxCalculationRecord.created_at.desc()).first()

@router.get('/history')
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	return db.query(TaxCalculationRecord).filter(TaxCalculationRecord.user_id == user.id).order_by(TaxCalculationRecord.created_at.desc()).limit(20).all()

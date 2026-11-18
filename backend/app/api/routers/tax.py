from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.planning import TaxCalculationRecord
from app.schemas.common import TaxInput
from app.services.tax_engine import TaxRuleError, calculate_tax, compare_regimes
router = APIRouter(prefix='/tax', tags=['tax'])

@router.post('/calculate')
def calculate(payload: TaxInput, regime: Literal['old', 'new'] = 'old', user: User = Depends(get_current_user)):
    try:
        return calculate_tax(payload.model_dump(), regime)
    except TaxRuleError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.post('/compare')
def compare(payload: TaxInput, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        comparison = compare_regimes(payload.model_dump())
    except TaxRuleError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.add(TaxCalculationRecord(user_id=user.id, assessment_year=payload.assessment_year, input_data=payload.model_dump(), comparison=comparison))
    db.commit()
    return comparison

@router.get('/latest')
def latest(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	return db.query(TaxCalculationRecord).filter(TaxCalculationRecord.user_id == user.id).order_by(TaxCalculationRecord.created_at.desc()).first()

@router.get('/history')
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	return db.query(TaxCalculationRecord).filter(TaxCalculationRecord.user_id == user.id).order_by(TaxCalculationRecord.created_at.desc()).limit(20).all()

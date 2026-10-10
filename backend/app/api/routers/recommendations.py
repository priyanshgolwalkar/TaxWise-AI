from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.planning import RecommendationRecord
from app.models.user import User
from app.schemas.common import RecommendationRequest
from app.services.recommendations import get_recommendations
router = APIRouter(prefix='/recommendations', tags=['recommendations'])
@router.post('/')
def recommendations(payload: RecommendationRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
	result = get_recommendations(payload.model_dump())
	db.add(RecommendationRecord(user_id=user.id, regime=payload.regime, input_data=payload.model_dump(), recommendations=result))
	db.commit()
	return result

@router.get('/latest')
def latest(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	return db.query(RecommendationRecord).filter(RecommendationRecord.user_id == user.id).order_by(RecommendationRecord.created_at.desc()).first()

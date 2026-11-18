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
	input_data = payload.model_dump()
	existing = db.query(RecommendationRecord).filter(
		RecommendationRecord.user_id == user.id,
		RecommendationRecord.regime == payload.regime,
	).order_by(RecommendationRecord.created_at.desc()).all()
	match = next((record for record in existing if record.input_data == input_data), None)
	if match:
		return match.recommendations
	result = get_recommendations(input_data)
	db.add(RecommendationRecord(user_id=user.id, regime=payload.regime, input_data=input_data, recommendations=result))
	db.commit()
	return result

@router.get('/latest')
def latest(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	return db.query(RecommendationRecord).filter(RecommendationRecord.user_id == user.id).order_by(RecommendationRecord.created_at.desc()).first()

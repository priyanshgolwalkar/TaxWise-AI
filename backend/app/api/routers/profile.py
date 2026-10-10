from fastapi import APIRouter, Depends
from app.schemas.auth import UserProfile
from app.core.security import get_current_user
from app.models.user import User
router = APIRouter(prefix='/profile', tags=['profile'])
@router.get('/me', response_model=UserProfile)
def profile(user: User = Depends(get_current_user)): return user

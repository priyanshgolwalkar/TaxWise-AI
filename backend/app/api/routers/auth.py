from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, Token
from app.core.security import create_access_token, hash_password, verify_password
router = APIRouter(prefix='/auth', tags=['authentication'])
@router.post('/register', response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
	if db.query(User).filter(User.email == payload.email).first():
		raise HTTPException(status_code=409, detail='An account with this email already exists')
	user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password))
	db.add(user); db.commit()
	return {'access_token': create_access_token(payload.email), 'token_type': 'bearer'}
@router.post('/login', response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
	user = db.query(User).filter(User.email == payload.email).first()
	if user is None or not verify_password(payload.password, user.password_hash):
		raise HTTPException(status_code=401, detail='Incorrect email or password')
	return {'access_token': create_access_token(user.email), 'token_type': 'bearer'}

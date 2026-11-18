from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')

def hash_password(password: str) -> str: return pwd_context.hash(password)
def verify_password(password: str, hashed: str) -> bool: return pwd_context.verify(password, hashed)
def create_access_token(subject: str) -> str:
    settings = get_settings(); expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({'sub': subject, 'exp': expires}, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid authentication credentials', headers={'WWW-Authenticate': 'Bearer'})
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        email = payload.get('sub')
        if not email:
            raise credentials_error
    except JWTError as exc:
        raise credentials_error from exc
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_error
    return user

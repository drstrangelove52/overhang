from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os

from app.models.database import get_db
from app.models.models import User

router = APIRouter(prefix='/api/auth', tags=['auth'])

SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
ALGORITHM = 'HS256'
TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login')


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    is_admin: bool


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS)
    return jwt.encode({'sub': str(user_id), 'username': username, 'exp': expire}, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload['sub'])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Ungültiger Token',
                            headers={'WWW-Authenticate': 'Bearer'})
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Benutzer nicht gefunden')
    return user


@router.post('/register', response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(User).where(User.username == req.username))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, 'Benutzername bereits vergeben')
    if len(req.password) < 8:
        raise HTTPException(400, 'Passwort muss mindestens 8 Zeichen haben')

    # First registered user becomes admin
    count = (await db.execute(select(User))).scalars().first()
    is_admin = count is None

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        is_admin=is_admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(
        access_token=create_token(user.id, user.username),
        token_type='bearer',
        username=user.username,
        is_admin=user.is_admin,
    )


@router.post('/login', response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.username == form.username))).scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Falscher Benutzername oder Passwort')
    return TokenResponse(
        access_token=create_token(user.id, user.username),
        token_type='bearer',
        username=user.username,
        is_admin=user.is_admin,
    )


@router.get('/me')
async def me(user: User = Depends(get_current_user)):
    return {'id': user.id, 'username': user.username, 'email': user.email, 'is_admin': user.is_admin}

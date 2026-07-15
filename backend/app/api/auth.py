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


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    is_admin: bool
    user_id: int


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
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Account nicht freigeschaltet')
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin-Rechte erforderlich')
    return user


@router.post('/register')
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = (await db.execute(select(User).where(User.username == req.username))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, 'Benutzername bereits vergeben')
    if len(req.password) < 8:
        raise HTTPException(400, 'Passwort muss mindestens 8 Zeichen haben')

    # First registered user becomes admin and is immediately active
    first_user = (await db.execute(select(User))).scalars().first()
    is_first = first_user is None

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        is_admin=is_first,
        is_active=is_first,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    if not user.is_active:
        return {'pending': True, 'message': 'Dein Account wartet auf Freischaltung durch den Administrator.'}

    return TokenResponse(
        access_token=create_token(user.id, user.username),
        token_type='bearer',
        username=user.username,
        is_admin=user.is_admin,
        user_id=user.id,
    )


@router.post('/login', response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.username == form.username))).scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Falscher Benutzername oder Passwort')
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Dein Account wurde noch nicht freigeschaltet. Bitte wende dich an den Administrator.')
    return TokenResponse(
        access_token=create_token(user.id, user.username),
        token_type='bearer',
        username=user.username,
        is_admin=user.is_admin,
        user_id=user.id,
    )


@router.get('/me')
async def me(user: User = Depends(get_current_user)):
    return {'id': user.id, 'username': user.username, 'email': user.email, 'is_admin': user.is_admin}


@router.post('/change-password')
async def change_password(req: ChangePasswordRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not verify_password(req.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Aktuelles Passwort ist falsch')
    if len(req.new_password) < 8:
        raise HTTPException(400, 'Neues Passwort muss mindestens 8 Zeichen haben')
    user.hashed_password = hash_password(req.new_password)
    await db.commit()
    return {'ok': True}

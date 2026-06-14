from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import os, shutil

from app.models.database import get_db
from app.models.models import User, Model
from app.api.auth import require_admin, hash_password

router = APIRouter(prefix='/api/admin', tags=['admin'])
admin_auth = Depends(require_admin)


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    is_admin: bool = False


class UserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    password: Optional[str] = None
    email: Optional[str] = None


def _user_to_dict(u: User) -> dict:
    return {
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'is_admin': u.is_admin,
        'is_active': u.is_active,
        'created_at': u.created_at.isoformat() if u.created_at else None,
    }


@router.get('/users')
async def list_users(db: AsyncSession = Depends(get_db), _admin: User = admin_auth):
    users = (await db.execute(select(User).order_by(User.created_at))).scalars().all()
    return [_user_to_dict(u) for u in users]


@router.post('/users', status_code=201)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db), _admin: User = admin_auth):
    if len(body.password) < 8:
        raise HTTPException(400, 'Passwort muss mindestens 8 Zeichen haben')
    existing = (await db.execute(select(User).where(User.username == body.username))).scalar_one_or_none()
    if existing:
        raise HTTPException(400, 'Benutzername bereits vergeben')
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        is_admin=body.is_admin,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _user_to_dict(user)


@router.patch('/users/{user_id}')
async def update_user(user_id: int, body: UserUpdate, db: AsyncSession = Depends(get_db), admin: User = admin_auth):
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, 'Benutzer nicht gefunden')
    # Prevent admin from removing their own admin rights
    if body.is_admin is False and user.id == admin.id:
        raise HTTPException(400, 'Du kannst dir selbst nicht die Admin-Rechte entziehen')
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.is_admin is not None:
        user.is_admin = body.is_admin
    if body.password:
        if len(body.password) < 8:
            raise HTTPException(400, 'Passwort muss mindestens 8 Zeichen haben')
        user.hashed_password = hash_password(body.password)
    if body.email is not None:
        user.email = body.email
    await db.commit()
    return _user_to_dict(user)


@router.delete('/users/{user_id}', status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), admin: User = admin_auth):
    if user_id == admin.id:
        raise HTTPException(400, 'Du kannst dich nicht selbst löschen')
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, 'Benutzer nicht gefunden')

    # Delete storage files for this user's models
    storage_root = Path(os.getenv('STORAGE_PATH', '/app/storage'))
    model_ids = (await db.execute(select(Model.id).where(Model.user_id == user_id))).scalars().all()
    for mid in model_ids:
        model_dir = storage_root / str(mid)
        if model_dir.exists():
            shutil.rmtree(model_dir, ignore_errors=True)

    await db.delete(user)
    await db.commit()

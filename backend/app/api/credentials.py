from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.models.database import get_db
from app.models.models import PlatformCredential, User
from app.api.auth import get_current_user
from app.utils.crypto import encrypt, decrypt

router = APIRouter(prefix='/api/credentials', tags=['credentials'])
auth = Depends(get_current_user)


class CredentialIn(BaseModel):
    token: str


@router.get('/thingiverse')
async def get_thingiverse(db: AsyncSession = Depends(get_db), _user: User = auth):
    row = (await db.execute(select(PlatformCredential).where(PlatformCredential.platform == 'thingiverse'))).scalar_one_or_none()
    return {'configured': row is not None}


@router.put('/thingiverse')
async def save_thingiverse(body: CredentialIn, db: AsyncSession = Depends(get_db), _user: User = auth):
    existing = (await db.execute(select(PlatformCredential).where(PlatformCredential.platform == 'thingiverse'))).scalar_one_or_none()
    data = encrypt({'token': body.token})
    if existing:
        existing.credential_data = data
    else:
        db.add(PlatformCredential(platform='thingiverse', credential_data=data))
    await db.commit()
    return {'ok': True}


@router.delete('/thingiverse', status_code=204)
async def delete_thingiverse(db: AsyncSession = Depends(get_db), _user: User = auth):
    row = (await db.execute(select(PlatformCredential).where(PlatformCredential.platform == 'thingiverse'))).scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()


@router.post('/thingiverse/test')
async def test_thingiverse(db: AsyncSession = Depends(get_db), _user: User = auth):
    row = (await db.execute(select(PlatformCredential).where(PlatformCredential.platform == 'thingiverse'))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, 'Kein API Token gespeichert')
    import httpx
    token = decrypt(row.credential_data)['token']
    try:
        resp = await httpx.AsyncClient().get(
            'https://api.thingiverse.com/users/me',
            headers={'Authorization': f'Bearer {token}'},
            timeout=15,
        )
        if resp.status_code == 200:
            name = resp.json().get('name', '')
            return {'ok': True, 'message': f'Verbunden als {name}'}
        return {'ok': False, 'message': 'Token ungültig'}
    except Exception as e:
        return {'ok': False, 'message': str(e)}

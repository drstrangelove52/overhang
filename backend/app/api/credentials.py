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

SUPPORTED = ['printables', 'thingiverse', 'makerworld']


class CredentialIn(BaseModel):
    username: str
    password: str


@router.get('')
async def list_credentials(db: AsyncSession = Depends(get_db), _user: User = auth):
    rows = (await db.execute(select(PlatformCredential))).scalars().all()
    return [
        {'platform': r.platform, 'username': decrypt(r.credential_data).get('username', ''), 'updated_at': r.updated_at.isoformat()}
        for r in rows
    ]


@router.put('/{platform}')
async def save_credential(platform: str, body: CredentialIn, db: AsyncSession = Depends(get_db), _user: User = auth):
    if platform not in SUPPORTED:
        raise HTTPException(400, f'Plattform nicht unterstützt: {platform}')
    existing = (await db.execute(select(PlatformCredential).where(PlatformCredential.platform == platform))).scalar_one_or_none()
    data = encrypt({'username': body.username, 'password': body.password})
    if existing:
        existing.credential_data = data
    else:
        db.add(PlatformCredential(platform=platform, credential_data=data))
    await db.commit()
    return {'ok': True}


@router.delete('/{platform}', status_code=204)
async def delete_credential(platform: str, db: AsyncSession = Depends(get_db), _user: User = auth):
    row = (await db.execute(select(PlatformCredential).where(PlatformCredential.platform == platform))).scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()


@router.post('/{platform}/test')
async def test_credential(platform: str, db: AsyncSession = Depends(get_db), _user: User = auth):
    row = (await db.execute(select(PlatformCredential).where(PlatformCredential.platform == platform))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, 'Keine Credentials gespeichert')
    creds = decrypt(row.credential_data)
    try:
        if platform == 'makerworld':
            token = await _test_makerworld(creds['username'], creds['password'])
            return {'ok': True, 'message': f'Login erfolgreich'}
        elif platform == 'thingiverse':
            ok = await _test_thingiverse(creds['password'])  # password = API token
            return {'ok': ok, 'message': 'Token gültig' if ok else 'Token ungültig'}
        elif platform == 'printables':
            ok = await _test_printables(creds['username'], creds['password'])
            return {'ok': ok, 'message': 'Login erfolgreich' if ok else 'Login fehlgeschlagen'}
    except Exception as e:
        return {'ok': False, 'message': str(e)}


async def _test_makerworld(email: str, password: str) -> str:
    import httpx
    resp = await httpx.AsyncClient().post(
        'https://api.bambulab.com/v1/user-service/user/login',
        json={'account': email, 'password': password},
        timeout=15,
    )
    data = resp.json()
    if not data.get('accessToken'):
        raise Exception(data.get('message', 'Login fehlgeschlagen'))
    return data['accessToken']


async def _test_thingiverse(api_token: str) -> bool:
    import httpx
    resp = await httpx.AsyncClient().get(
        'https://api.thingiverse.com/users/me',
        headers={'Authorization': f'Bearer {api_token}'},
        timeout=15,
    )
    return resp.status_code == 200


async def _test_printables(email: str, password: str) -> bool:
    import httpx
    # Printables uses a token-based login via their API
    resp = await httpx.AsyncClient().post(
        'https://api.printables.com/graphql/',
        json={'query': 'mutation Login($email:String!,$password:String!){login(username:$email,password:$password){token}}',
              'variables': {'email': email, 'password': password}},
        timeout=15,
    )
    data = resp.json()
    return bool(data.get('data', {}).get('login', {}).get('token'))

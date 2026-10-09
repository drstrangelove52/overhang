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


class CookieIn(BaseModel):
    cookies: str


async def _get_makerworld(db: AsyncSession):
    return (await db.execute(select(PlatformCredential).where(PlatformCredential.platform == 'makerworld'))).scalar_one_or_none()


@router.get('/makerworld')
async def get_makerworld(db: AsyncSession = Depends(get_db), _user: User = auth):
    return {'configured': await _get_makerworld(db) is not None}


@router.put('/makerworld')
async def save_makerworld(body: CookieIn, db: AsyncSession = Depends(get_db), _user: User = auth):
    from app.utils.browser import parse_cookies
    try:
        cookies = parse_cookies(body.cookies)
    except ValueError:
        raise HTTPException(400, 'Cookies konnten nicht gelesen werden (ungültiges JSON)')
    if not cookies:
        raise HTTPException(400, 'Keine Cookies für makerworld.com / bambulab.com gefunden')
    data = encrypt({'cookies': cookies})
    existing = await _get_makerworld(db)
    if existing:
        existing.credential_data = data
    else:
        db.add(PlatformCredential(platform='makerworld', credential_data=data))
    await db.commit()
    return {'ok': True, 'count': len(cookies)}


@router.delete('/makerworld', status_code=204)
async def delete_makerworld(db: AsyncSession = Depends(get_db), _user: User = auth):
    row = await _get_makerworld(db)
    if row:
        await db.delete(row)
        await db.commit()


@router.post('/makerworld/test')
async def test_makerworld(db: AsyncSession = Depends(get_db), _user: User = auth):
    row = await _get_makerworld(db)
    if not row:
        raise HTTPException(404, 'Keine Sitzung gespeichert')
    from app.utils.browser import makerworld_page, wait_for_cloudflare
    cookies = decrypt(row.credential_data)['cookies']
    # MakerLab pages require a login: without a valid session MakerWorld redirects to the Bambu Lab sign-in
    try:
        async with makerworld_page(cookies) as page:
            await page.goto('https://makerworld.com/makerlab/community/fold-up-box-generator',
                            wait_until='domcontentloaded', timeout=45000)
            await wait_for_cloudflare(page)
            await page.wait_for_timeout(3000)
            url, title = page.url, await page.title()
    except Exception as e:
        return {'ok': False, 'message': f'Browser-Fehler: {e}'}
    if 'sign-in' in url or 'bambulab.com' in url:
        return {'ok': False, 'message': 'Sitzung abgelaufen oder ungültig — bitte Cookies neu exportieren'}
    return {'ok': True, 'message': f'Sitzung gültig (geladen: {title})'}


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

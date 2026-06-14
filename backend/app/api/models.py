from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional
from celery.result import AsyncResult
from pathlib import Path
import os, shutil, zipfile, io

from app.models.database import get_db
from app.models.models import Model, ModelFile, Tag, ModelTag, User, Collection, CollectionModel
from app.tasks.celery_app import celery_app
from app.scrapers.detect import detect_platform
from app.api.auth import get_current_user

router = APIRouter(prefix='/api/models', tags=['models'])
auth = Depends(get_current_user)

class ImportRequest(BaseModel):
    url: str

class ImportResponse(BaseModel):
    job_id: str
    platform: str
    message: str

class JobStatus(BaseModel):
    job_id: str
    state: str
    result: Optional[dict] = None
    error: Optional[str] = None

@router.post('/import', response_model=ImportResponse)
async def import_model(req: ImportRequest, db: AsyncSession = Depends(get_db), _user: User = auth):
    platform = detect_platform(req.url)
    if platform == 'unknown':
        raise HTTPException(400, 'URL nicht erkannt. Unterstützt: printables.com, thingiverse.com, makerworld.com')

    existing = (await db.execute(select(Model).where(Model.source_url == req.url))).scalar_one_or_none()
    if existing:
        raise HTTPException(409, f'Bereits importiert: „{existing.title}"')

    from app.tasks.scrape import scrape_model
    job = scrape_model.delay(req.url)
    return ImportResponse(job_id=job.id, platform=platform, message=f'Import gestartet ({platform})')

@router.get('/jobs/{job_id}', response_model=JobStatus)
async def job_status(job_id: str, _user: User = auth):
    result = AsyncResult(job_id, app=celery_app)
    if result.state == 'FAILURE':
        return JobStatus(job_id=job_id, state='FAILURE', error=str(result.result))
    if result.state == 'SUCCESS':
        return JobStatus(job_id=job_id, state='SUCCESS', result=result.result)
    return JobStatus(job_id=job_id, state=result.state, result=result.info if isinstance(result.info, dict) else None)

@router.get('')
async def list_models(
    q: Optional[str] = None,
    platform: Optional[str] = None,
    tag: Optional[str] = None,
    skip: int = 0,
    limit: int = 48,
    db: AsyncSession = Depends(get_db),
    _user: User = auth,
):
    stmt = select(Model).options(
        selectinload(Model.files),
        selectinload(Model.model_tags).selectinload(ModelTag.tag),
    ).order_by(Model.created_at.desc())

    if q:
        stmt = stmt.where(or_(
            Model.title.ilike(f'%{q}%'),
            Model.description.ilike(f'%{q}%'),
            Model.author.ilike(f'%{q}%'),
        ))
    if platform:
        stmt = stmt.where(Model.source_platform == platform)
    if tag:
        stmt = stmt.join(ModelTag).join(Tag).where(Tag.name == tag.lower())

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar()

    models = (await db.execute(stmt.offset(skip).limit(limit))).scalars().all()

    return {
        'total': total,
        'items': [_model_to_dict(m) for m in models],
    }

@router.get('/{model_id}')
async def get_model(model_id: int, db: AsyncSession = Depends(get_db), _user: User = auth):
    stmt = select(Model).where(Model.id == model_id).options(
        selectinload(Model.files),
        selectinload(Model.model_tags).selectinload(ModelTag.tag),
    )
    model = (await db.execute(stmt)).scalar_one_or_none()
    if not model:
        raise HTTPException(404, 'Modell nicht gefunden')
    return _model_to_dict(model)

_IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
_ALLOWED_EXTS = {'.stl', '.3mf', '.gcode', '.bgcode', '.step', '.obj'} | _IMAGE_EXTS


def _classify(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == '.3mf':
        return '3mf'
    if ext == '.stl':
        return 'stl'
    if ext in _IMAGE_EXTS:
        return 'image'
    return 'other'


def _save_file_record(db, model_id: int, filename: str, data: bytes, storage_path_root: Path) -> ModelFile:
    file_type = _classify(filename)
    dest_dir = storage_path_root / str(model_id) / ('images' if file_type == 'image' else 'files')
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename
    dest.write_bytes(data)
    return ModelFile(
        model_id=model_id,
        filename=filename,
        file_type=file_type,
        storage_path=str(dest.relative_to(storage_path_root)),
        file_size=len(data),
        is_primary_preview=False,
    )


@router.post('/{model_id}/files', status_code=201)
async def upload_file(model_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), _user: User = auth):
    model = (await db.execute(select(Model).where(Model.id == model_id))).scalar_one_or_none()
    if not model:
        raise HTTPException(404, 'Modell nicht gefunden')

    storage_root = Path(os.getenv('STORAGE_PATH', '/app/storage'))
    raw = await file.read()

    # ZIP: extract and store each allowed file individually
    if file.filename.lower().endswith('.zip'):
        try:
            zf = zipfile.ZipFile(io.BytesIO(raw))
        except zipfile.BadZipFile:
            raise HTTPException(400, 'Ungültige ZIP-Datei')

        saved = []
        for entry in zf.infolist():
            # skip directories and macOS metadata
            if entry.is_dir() or Path(entry.filename).name.startswith('__MACOSX') or Path(entry.filename).name.startswith('._'):
                continue
            ext = Path(entry.filename).suffix.lower()
            if ext not in _ALLOWED_EXTS:
                continue
            # prevent path traversal
            safe_name = Path(entry.filename).name
            if not safe_name:
                continue
            data = zf.read(entry.filename)
            mf = _save_file_record(db, model_id, safe_name, data, storage_root)
            db.add(mf)
            saved.append(mf)

        await db.commit()
        for mf in saved:
            await db.refresh(mf)
        return {
            'extracted': len(saved),
            'files': [{'id': mf.id, 'filename': mf.filename, 'file_type': mf.file_type, 'file_size': mf.file_size, 'url': '/api/files/' + mf.storage_path} for mf in saved],
        }

    # Single file upload
    mf = _save_file_record(db, model_id, file.filename, raw, storage_root)
    db.add(mf)
    await db.commit()
    await db.refresh(mf)
    return {'id': mf.id, 'filename': mf.filename, 'file_type': mf.file_type, 'file_size': mf.file_size, 'url': '/api/files/' + mf.storage_path}


@router.patch('/{model_id}/tags')
async def set_model_tags(model_id: int, body: dict, db: AsyncSession = Depends(get_db), _user: User = auth):
    model = (await db.execute(select(Model).where(Model.id == model_id))).scalar_one_or_none()
    if not model:
        raise HTTPException(404, 'Modell nicht gefunden')
    existing = (await db.execute(select(ModelTag).where(ModelTag.model_id == model_id))).scalars().all()
    for mt in existing:
        await db.delete(mt)
    await db.flush()
    for name in body.get('tags', []):
        name = name.strip().lower()[:100]
        if not name:
            continue
        tag = (await db.execute(select(Tag).where(Tag.name == name))).scalar_one_or_none()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            await db.flush()
        db.add(ModelTag(model_id=model_id, tag_id=tag.id))
    await db.commit()
    return {'ok': True}


@router.patch('/{model_id}/notes')
async def set_model_notes(model_id: int, body: dict, db: AsyncSession = Depends(get_db), _user: User = auth):
    model = (await db.execute(select(Model).where(Model.id == model_id))).scalar_one_or_none()
    if not model:
        raise HTTPException(404, 'Modell nicht gefunden')
    model.notes = body.get('notes', '')
    await db.commit()
    return {'ok': True}


@router.delete('/{model_id}', status_code=204)
async def delete_model(model_id: int, db: AsyncSession = Depends(get_db), _user: User = auth):
    stmt = select(Model).where(Model.id == model_id)
    model = (await db.execute(stmt)).scalar_one_or_none()
    if not model:
        raise HTTPException(404, 'Modell nicht gefunden')
    await db.delete(model)
    await db.commit()

def _model_to_dict(m: Model) -> dict:
    preview = next((f for f in m.files if f.is_primary_preview and f.file_type == 'image'), None)
    return {
        'id': m.id,
        'title': m.title,
        'description': m.description,
        'source_url': m.source_url,
        'source_platform': m.source_platform,
        'author': m.author,
        'author_url': m.author_url,
        'license': m.license,
        'print_settings': m.print_settings,
        'notes': m.notes or '',
        'created_at': m.created_at.isoformat() if m.created_at else None,
        'preview_image': ('/api/files/' + preview.storage_path) if preview else None,
        'tags': [mt.tag.name for mt in m.model_tags if mt.tag],
        'files': [
            {
                'id': f.id,
                'filename': f.filename,
                'file_type': f.file_type,
                'file_size': f.file_size,
                'url': '/api/files/' + f.storage_path,
                'is_primary_preview': f.is_primary_preview,
            }
            for f in m.files
        ],
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional

from app.models.database import get_db
from app.models.models import Collection, CollectionModel, Model, ModelFile, ModelTag, Tag, User
from app.api.auth import get_current_user

router = APIRouter(prefix='/api/collections', tags=['collections'])
auth = Depends(get_current_user)


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None


def _col_to_dict(c: Collection, include_models: bool = False) -> dict:
    d = {
        'id': c.id,
        'name': c.name,
        'description': c.description,
        'model_count': len(c.collection_models),
        'created_at': c.created_at.isoformat() if c.created_at else None,
    }
    if include_models:
        items = sorted(c.collection_models, key=lambda cm: cm.position)
        d['models'] = [_cm_to_dict(cm) for cm in items]
    else:
        previews = []
        model_ids = []
        for cm in sorted(c.collection_models, key=lambda x: x.position):
            if cm.model:
                model_ids.append(cm.model.id)
            if len(previews) < 4 and cm.model and cm.model.files:
                img = next((f for f in cm.model.files if f.is_primary_preview and f.file_type == 'image'), None)
                if img:
                    previews.append('/api/files/' + img.storage_path)
        d['previews'] = previews
        d['model_ids'] = model_ids
    return d


def _cm_to_dict(cm: CollectionModel) -> dict:
    m = cm.model
    if not m:
        return {}
    preview = next((f for f in m.files if f.is_primary_preview and f.file_type == 'image'), None)
    return {
        'id': m.id,
        'title': m.title,
        'source_platform': m.source_platform,
        'author': m.author,
        'preview_image': ('/api/files/' + preview.storage_path) if preview else None,
        'tags': [mt.tag.name for mt in m.model_tags if mt.tag],
        'position': cm.position,
    }


@router.get('')
async def list_collections(db: AsyncSession = Depends(get_db), user: User = auth):
    result = await db.execute(
        select(Collection).where(Collection.user_id == user.id).options(
            selectinload(Collection.collection_models)
            .selectinload(CollectionModel.model)
            .selectinload(Model.files)
        ).order_by(Collection.name)
    )
    return [_col_to_dict(c) for c in result.scalars().all()]


@router.post('', status_code=201)
async def create_collection(body: CollectionCreate, db: AsyncSession = Depends(get_db), user: User = auth):
    c = Collection(user_id=user.id, name=body.name.strip(), description=body.description)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return {'id': c.id, 'name': c.name, 'description': c.description, 'model_count': 0, 'previews': []}


@router.get('/{col_id}')
async def get_collection(col_id: int, db: AsyncSession = Depends(get_db), user: User = auth):
    c = (await db.execute(
        select(Collection).where(Collection.id == col_id, Collection.user_id == user.id).options(
            selectinload(Collection.collection_models)
            .selectinload(CollectionModel.model)
            .options(
                selectinload(Model.files),
                selectinload(Model.model_tags).selectinload(ModelTag.tag),
            )
        )
    )).scalar_one_or_none()
    if not c:
        raise HTTPException(404, 'Sammlung nicht gefunden')
    return _col_to_dict(c, include_models=True)


@router.patch('/{col_id}')
async def update_collection(col_id: int, body: CollectionCreate, db: AsyncSession = Depends(get_db), user: User = auth):
    c = (await db.execute(select(Collection).where(Collection.id == col_id, Collection.user_id == user.id))).scalar_one_or_none()
    if not c:
        raise HTTPException(404, 'Sammlung nicht gefunden')
    c.name = body.name.strip()
    c.description = body.description
    await db.commit()
    return {'ok': True}


@router.delete('/{col_id}', status_code=204)
async def delete_collection(col_id: int, db: AsyncSession = Depends(get_db), user: User = auth):
    c = (await db.execute(select(Collection).where(Collection.id == col_id, Collection.user_id == user.id))).scalar_one_or_none()
    if not c:
        raise HTTPException(404, 'Sammlung nicht gefunden')
    await db.delete(c)
    await db.commit()


@router.post('/{col_id}/models/{model_id}', status_code=201)
async def add_model_to_collection(col_id: int, model_id: int, db: AsyncSession = Depends(get_db), user: User = auth):
    c = (await db.execute(select(Collection).where(Collection.id == col_id, Collection.user_id == user.id))).scalar_one_or_none()
    if not c:
        raise HTTPException(404, 'Sammlung nicht gefunden')
    m = (await db.execute(select(Model).where(Model.id == model_id, Model.user_id == user.id))).scalar_one_or_none()
    if not m:
        raise HTTPException(404, 'Modell nicht gefunden')
    existing = (await db.execute(
        select(CollectionModel).where(CollectionModel.collection_id == col_id, CollectionModel.model_id == model_id)
    )).scalar_one_or_none()
    if existing:
        return {'ok': True, 'already_present': True}
    max_pos = (await db.execute(
        select(CollectionModel).where(CollectionModel.collection_id == col_id)
    )).scalars().all()
    pos = max((cm.position for cm in max_pos), default=-1) + 1
    db.add(CollectionModel(collection_id=col_id, model_id=model_id, position=pos))
    await db.commit()
    return {'ok': True}


@router.delete('/{col_id}/models/{model_id}', status_code=204)
async def remove_model_from_collection(col_id: int, model_id: int, db: AsyncSession = Depends(get_db), user: User = auth):
    cm = (await db.execute(
        select(CollectionModel).where(CollectionModel.collection_id == col_id, CollectionModel.model_id == model_id)
    )).scalar_one_or_none()
    if cm:
        await db.delete(cm)
        await db.commit()

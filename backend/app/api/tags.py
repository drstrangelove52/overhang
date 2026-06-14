from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.models.database import get_db
from app.models.models import Tag, ModelTag, Model, User
from app.api.auth import get_current_user

router = APIRouter(prefix='/api/tags', tags=['tags'])
auth = Depends(get_current_user)


@router.get('')
async def list_tags(db: AsyncSession = Depends(get_db), user: User = auth):
    """Tags used by the current user's models."""
    result = await db.execute(
        select(Tag, func.count(ModelTag.model_id).label('count'))
        .join(ModelTag)
        .join(Model, ModelTag.model_id == Model.id)
        .where(Model.user_id == user.id)
        .group_by(Tag.id)
        .order_by(Tag.name)
    )
    return [{'id': t.id, 'name': t.name, 'count': count} for t, count in result.all()]


@router.post('/{model_id}')
async def add_tag(model_id: int, req: BaseModel, db: AsyncSession = Depends(get_db), _user: User = auth):
    raise HTTPException(405, 'Use PATCH /api/models/{id}/tags')


@router.patch('/models/{model_id}')
async def set_model_tags(model_id: int, body: dict, db: AsyncSession = Depends(get_db), _user: User = auth):
    tags_raw: list[str] = body.get('tags', [])
    model = (await db.execute(select(Model).where(Model.id == model_id))).scalar_one_or_none()
    if not model:
        raise HTTPException(404, 'Modell nicht gefunden')

    # Remove existing tags
    existing = (await db.execute(select(ModelTag).where(ModelTag.model_id == model_id))).scalars().all()
    for mt in existing:
        await db.delete(mt)
    await db.flush()

    # Add new tags
    for name in tags_raw:
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

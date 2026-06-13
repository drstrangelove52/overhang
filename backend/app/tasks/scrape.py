import os
import asyncio
import httpx
import mimetypes
from pathlib import Path
from celery import shared_task
from app.tasks.celery_app import celery_app
from app.scrapers.detect import detect_platform

STORAGE_PATH = os.getenv('STORAGE_PATH', '/app/storage')

@celery_app.task(bind=True, name='scrape_model')
def scrape_model(self, url: str) -> dict:
    return asyncio.run(_scrape_model_async(self, url))

async def _scrape_model_async(task, url: str) -> dict:
    platform = detect_platform(url)

    if platform == 'printables':
        from app.scrapers.printables import scrape
    elif platform == 'thingiverse':
        from app.scrapers.thingiverse import scrape
    else:
        raise ValueError(f'Plattform nicht unterstützt: {platform} ({url})')

    task.update_state(state='PROGRESS', meta={'step': 'scraping', 'platform': platform})
    scraped = await scrape(url)

    # Insert into DB (sync via aiomysql through SQLAlchemy async)
    from app.models.database import AsyncSessionLocal
    from app.models.models import Model, ModelFile, Tag, ModelTag
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        model = Model(
            title=scraped.title,
            description=scraped.description,
            source_url=scraped.source_url,
            source_platform=scraped.source_platform,
            author=scraped.author,
            author_url=scraped.author_url,
            license=scraped.license,
            print_settings=scraped.print_settings or {},
        )
        db.add(model)
        await db.flush()
        model_id = model.id

        storage_dir = Path(STORAGE_PATH) / str(model_id)
        img_dir = storage_dir / 'images'
        files_dir = storage_dir / 'files'
        img_dir.mkdir(parents=True, exist_ok=True)
        files_dir.mkdir(parents=True, exist_ok=True)

        task.update_state(state='PROGRESS', meta={'step': 'downloading', 'model_id': model_id})

        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            # Download images
            for i, img in enumerate(scraped.images[:10]):
                try:
                    resp = await client.get(img.url)
                    resp.raise_for_status()
                    dest = img_dir / img.filename
                    dest.write_bytes(resp.content)
                    db.add(ModelFile(
                        model_id=model_id,
                        filename=img.filename,
                        file_type='image',
                        storage_path=str(dest.relative_to(STORAGE_PATH)),
                        file_size=len(resp.content),
                        is_primary_preview=(i == 0),
                    ))
                except Exception as e:
                    print(f'Bild-Download fehlgeschlagen {img.url}: {e}')

            # Download 3D files
            for f in scraped.files:
                if not f.url:
                    continue
                try:
                    resp = await client.get(f.url)
                    resp.raise_for_status()
                    dest = files_dir / f.filename
                    dest.write_bytes(resp.content)
                    db.add(ModelFile(
                        model_id=model_id,
                        filename=f.filename,
                        file_type=f.file_type,
                        storage_path=str(dest.relative_to(STORAGE_PATH)),
                        file_size=len(resp.content),
                        is_primary_preview=False,
                    ))
                except Exception as e:
                    print(f'Datei-Download fehlgeschlagen {f.url}: {e}')

        # Tags
        for tag_name in scraped.tags:
            tag_name = tag_name.strip().lower()[:100]
            if not tag_name:
                continue
            result = await db.execute(select(Tag).where(Tag.name == tag_name))
            tag = result.scalar_one_or_none()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                await db.flush()
            db.add(ModelTag(model_id=model_id, tag_id=tag.id))

        await db.commit()

    return {'status': 'done', 'model_id': model_id, 'title': scraped.title}

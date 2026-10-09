import re
from urllib.parse import urlparse
from app.scrapers.base import ScrapedModel, ScrapedFile
from app.scrapers.detect import detect_platform, normalize_url


def _title_from_url(url: str) -> str:
    p = urlparse(url)
    segments = [s for s in p.path.split('/') if s]
    slug = segments[-1] if segments else p.netloc
    slug = re.sub(r'\.\w{2,5}$', '', slug)  # drop file extension like .html
    title = re.sub(r'[-_+]+', ' ', slug).strip()
    return title.title() if title else p.netloc


async def _makerlab_meta(url: str, cookies: list[dict]) -> dict:
    """Best-effort OpenGraph metadata from the MakerLab page via the logged-in browser."""
    from app.utils.browser import makerworld_page
    async with makerworld_page(cookies) as page:
        await page.goto(url, wait_until='domcontentloaded', timeout=45000)
        await page.wait_for_function("document.title !== 'Just a moment...'", timeout=30000)
        return await page.evaluate(
            "() => { const m = n => document.querySelector(`meta[property='${n}']`)?.content || '';"
            " return {title: m('og:title') || document.title, description: m('og:description'), image: m('og:image')} }"
        )


async def scrape(url: str, credentials: dict | None = None) -> ScrapedModel:
    """Link-only entry for MakerLab generators and any unrecognized site.

    The title is derived from the URL slug. With an imported MakerWorld session,
    MakerLab pages additionally get title, description and cover image.
    Files can be attached manually afterwards.
    """
    platform = detect_platform(url)
    source_url = normalize_url(url, platform)
    title, description, images = _title_from_url(source_url), '', []

    cookies = (credentials or {}).get('cookies')
    if platform == 'makerlab' and cookies:
        try:
            meta = await _makerlab_meta(source_url, cookies)
            title = meta.get('title') or title
            description = meta.get('description') or ''
            if meta.get('image'):
                name = meta['image'].split('/')[-1].split('?')[0]
                if not re.search(r'\.(jpe?g|png|webp|gif)$', name, re.I):
                    name = 'cover.jpg'
                images.append(ScrapedFile(url=meta['image'], filename=name, file_type='image'))
        except Exception as e:
            print(f'MakerLab-Metadaten fehlgeschlagen {source_url}: {e}')

    return ScrapedModel(
        title=title,
        description=description,
        source_url=source_url,
        source_platform=platform,
        author='MakerLab' if platform == 'makerlab' else '',
        tags=['generator'] if platform == 'makerlab' else [],
        images=images,
    )

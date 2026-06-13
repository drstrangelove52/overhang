import httpx
import re
import json
from bs4 import BeautifulSoup
from app.scrapers.base import ScrapedModel, ScrapedFile

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36',
    'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
}

def _extract_id(url: str) -> str | None:
    m = re.search(r'/thing:(\d+)', url)
    return m.group(1) if m else None

async def scrape(url: str) -> ScrapedModel:
    thing_id = _extract_id(url)
    if not thing_id:
        raise ValueError(f'Konnte keine Thing-ID aus URL extrahieren: {url}')

    async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=HEADERS) as client:
        page = await client.get(url)
        page.raise_for_status()

    soup = BeautifulSoup(page.text, 'html.parser')

    next_data = soup.find('script', id='__NEXT_DATA__')
    if next_data:
        try:
            data = json.loads(next_data.string)
            props = data.get('props', {}).get('pageProps', {})
            thing = props.get('thing') or props.get('model') or {}
            if thing:
                return _parse_from_next_data(thing, thing_id, url)
        except (json.JSONDecodeError, AttributeError):
            pass

    return _parse_from_html(soup, thing_id, url)

def _parse_from_next_data(thing: dict, thing_id: str, url: str) -> ScrapedModel:
    creator = thing.get('creator') or {}
    creator_name = creator.get('name', '')

    images = [
        ScrapedFile(
            url=img.get('url', ''),
            filename=(img.get('url', '').split('/')[-1].split('?')[0] or f'image_{i}.jpg'),
            file_type='image',
        )
        for i, img in enumerate(thing.get('images') or [])
        if img.get('url')
    ]

    files = [
        ScrapedFile(
            url=(f.get('direct_url') or f.get('download_url', '')),
            filename=f.get('name', f'file_{i}'),
            file_type=('3mf' if f.get('name', '').lower().endswith('.3mf') else 'stl'),
        )
        for i, f in enumerate(thing.get('files') or [])
        if (f.get('direct_url') or f.get('download_url'))
    ]

    tags = [t.get('name', '') for t in (thing.get('tags') or []) if t.get('name')]

    return ScrapedModel(
        title=thing.get('name', ''),
        description=(thing.get('description') or thing.get('details', '')),
        source_url=url,
        source_platform='thingiverse',
        author=creator_name,
        author_url=('https://www.thingiverse.com/' + creator_name),
        license=thing.get('license', ''),
        tags=tags,
        images=images,
        files=files,
    )

def _parse_from_html(soup: BeautifulSoup, thing_id: str, url: str) -> ScrapedModel:
    title = ''
    t = soup.find('meta', property='og:title')
    if t:
        title = t.get('content', '')

    description = ''
    d = soup.find('meta', property='og:description')
    if d:
        description = d.get('content', '')

    image_url = ''
    img_tag = soup.find('meta', property='og:image')
    if img_tag:
        image_url = img_tag.get('content', '')

    images = []
    if image_url:
        images.append(ScrapedFile(url=image_url, filename=('preview_' + thing_id + '.jpg'), file_type='image'))

    return ScrapedModel(
        title=title,
        description=description,
        source_url=url,
        source_platform='thingiverse',
        images=images,
        files=[],
    )

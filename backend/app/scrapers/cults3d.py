import httpx
import json
import re
from bs4 import BeautifulSoup
from app.scrapers.base import ScrapedModel, ScrapedFile

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


async def scrape(url: str, credentials: dict | None = None) -> ScrapedModel:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=HEADERS) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, 'html.parser')

    # JSON-LD structured data (most reliable source)
    ld = _extract_json_ld(soup)

    title = _meta(soup, 'og:title') or (ld.get('name') if ld else None) or _text(soup, 'h1') or ''
    # Remove site suffix like " - Cults"
    title = re.sub(r'\s*[-|]\s*Cults.*$', '', title).strip()

    description = (ld.get('description') if ld else None) or _meta(soup, 'og:description') or ''

    # Author
    author = ''
    author_url = ''
    if ld and ld.get('author'):
        a = ld['author']
        author = a.get('name', '') if isinstance(a, dict) else str(a)
    if not author:
        # Try creator link on page: <a href="/en/users/...">
        creator_link = soup.select_one('a[href*="/en/users/"]') or soup.select_one('a[href*="/fr/users/"]')
        if creator_link:
            author = creator_link.get_text(strip=True)
            author_url = 'https://cults3d.com' + creator_link['href']

    # License
    license_str = ''
    if ld and ld.get('license'):
        license_str = ld['license'] if isinstance(ld['license'], str) else ''
    if not license_str:
        license_tag = soup.select_one('[itemprop="license"], .license')
        if license_tag:
            license_str = license_tag.get_text(strip=True)

    # Tags — from keywords meta or tag links
    tags = []
    keywords = _meta(soup, 'keywords')
    if keywords:
        tags = [t.strip().lower() for t in keywords.split(',') if t.strip()]
    if not tags:
        for a in soup.select('a[href*="/tag/"], a[href*="/3d-model/"][class*="tag"]'):
            t = a.get_text(strip=True).lower()
            if t and t not in tags:
                tags.append(t)

    # Images — og:image first, then gallery
    images = []
    seen_urls = set()

    og_img = _meta(soup, 'og:image')
    if og_img and og_img not in seen_urls:
        seen_urls.add(og_img)
        images.append(ScrapedFile(
            url=og_img,
            filename=_filename_from_url(og_img, 'cover.jpg'),
            file_type='image',
        ))

    # Gallery images
    for img in soup.select('picture img[src], .creation-media img[src], .gallery img[src], figure img[src]'):
        src = img.get('src') or img.get('data-src', '')
        if not src or src in seen_urls:
            continue
        if 'cults3d.com' not in src and not src.startswith('https://files'):
            continue
        # Skip tiny thumbnails
        if any(x in src for x in ['/mini/', '/thumb/', '50x50', '100x100']):
            continue
        seen_urls.add(src)
        images.append(ScrapedFile(
            url=src,
            filename=_filename_from_url(src, f'image_{len(images)}.jpg'),
            file_type='image',
        ))

    return ScrapedModel(
        title=title,
        description=description,
        source_url=url,
        source_platform='cults3d',
        author=author,
        author_url=author_url,
        license=license_str,
        tags=tags,
        images=images,
        files=[],  # Cults3d requires login for file downloads — upload manually via drag & drop
    )


def _extract_json_ld(soup: BeautifulSoup) -> dict | None:
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            data = json.loads(script.string or '')
            # May be a list or single object
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get('@type') in ('Product', 'CreativeWork', '3DModel'):
                        return item
                # Fallback: first item
                return data[0] if data else None
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, TypeError):
            continue
    return None


def _meta(soup: BeautifulSoup, prop: str) -> str:
    tag = soup.find('meta', property=prop) or soup.find('meta', attrs={'name': prop})
    return (tag.get('content') or '').strip() if tag else ''


def _text(soup: BeautifulSoup, selector: str) -> str:
    tag = soup.select_one(selector)
    return tag.get_text(strip=True) if tag else ''


def _filename_from_url(url: str, fallback: str) -> str:
    name = url.split('?')[0].split('/')[-1]
    return name if name and '.' in name else fallback

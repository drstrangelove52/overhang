import httpx
import re
import json
from bs4 import BeautifulSoup
from app.scrapers.base import ScrapedModel, ScrapedFile

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}
TV_API = "https://api.thingiverse.com"


def _extract_id(url: str):
    m = re.search(r"/thing:(\d+)", url)
    return m.group(1) if m else None


async def scrape(url: str, credentials: dict | None = None) -> ScrapedModel:
    thing_id = _extract_id(url)
    if not thing_id:
        raise ValueError(f"Konnte keine Thing-ID aus URL extrahieren: {url}")

    api_token = credentials.get('password') if credentials else None  # Thingiverse uses API token as "password"

    # With API token: use REST API for full metadata + file downloads
    if api_token:
        return await _scrape_with_api(thing_id, url, api_token)

    # Without token: scrape HTML
    return await _scrape_html(thing_id, url)


async def _scrape_with_api(thing_id: str, url: str, api_token: str) -> ScrapedModel:
    headers = {**HEADERS, "Authorization": f"Bearer {api_token}"}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=headers) as client:
        r_thing = await client.get(f"{TV_API}/things/{thing_id}")
        r_thing.raise_for_status()
        thing = r_thing.json()

        r_files = await client.get(f"{TV_API}/things/{thing_id}/files/")
        files_data = r_files.json() if r_files.status_code == 200 else []

        r_images = await client.get(f"{TV_API}/things/{thing_id}/images/")
        images_data = r_images.json() if r_images.status_code == 200 else []

    creator = thing.get("creator") or {}
    creator_name = creator.get("name", "")

    images = [
        ScrapedFile(
            url=img.get("url", ""),
            filename=img.get("url", "").split("/")[-1].split("?")[0] or f"image_{i}.jpg",
            file_type="image",
        )
        for i, img in enumerate(images_data)
        if img.get("url")
    ]

    files = []
    for f in (files_data if isinstance(files_data, list) else []):
        dl_url = f.get("download_url") or f.get("direct_url", "")
        if not dl_url:
            continue
        name = f.get("name", f"file_{f.get('id', 0)}")
        ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
        file_type = "3mf" if ext == "3mf" else "stl" if ext == "stl" else "other"
        files.append(ScrapedFile(url=dl_url, filename=name, file_type=file_type))

    tags = [t.get("name", "") for t in (thing.get("tags") or []) if t.get("name")]

    return ScrapedModel(
        title=thing.get("name", ""),
        description=thing.get("description") or thing.get("details", ""),
        source_url=url,
        source_platform="thingiverse",
        author=creator_name,
        author_url=f"https://www.thingiverse.com/{creator_name}" if creator_name else "",
        license=thing.get("license", ""),
        tags=tags,
        images=images,
        files=files,
    )


async def _scrape_html(thing_id: str, url: str) -> ScrapedModel:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True, headers=HEADERS) as client:
        page = await client.get(url)
        page.raise_for_status()

    soup = BeautifulSoup(page.text, "html.parser")
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data:
        try:
            data = json.loads(next_data.string)
            props = data.get("props", {}).get("pageProps", {})
            thing = props.get("thing") or props.get("model") or {}
            if thing:
                return _parse_from_next_data(thing, thing_id, url)
        except (json.JSONDecodeError, AttributeError):
            pass

    return _parse_from_og(soup, thing_id, url)


def _parse_from_next_data(thing: dict, thing_id: str, url: str) -> ScrapedModel:
    creator = thing.get("creator") or {}
    creator_name = creator.get("name", "")

    images = [
        ScrapedFile(
            url=img.get("url", ""),
            filename=img.get("url", "").split("/")[-1].split("?")[0] or f"image_{i}.jpg",
            file_type="image",
        )
        for i, img in enumerate(thing.get("images") or [])
        if img.get("url")
    ]

    files = [
        ScrapedFile(
            url=f.get("direct_url") or f.get("download_url", ""),
            filename=f.get("name", f"file_{i}"),
            file_type="3mf" if f.get("name", "").lower().endswith(".3mf") else "stl",
        )
        for i, f in enumerate(thing.get("files") or [])
        if f.get("direct_url") or f.get("download_url")
    ]

    tags = [t.get("name", "") for t in (thing.get("tags") or []) if t.get("name")]

    return ScrapedModel(
        title=thing.get("name", ""),
        description=thing.get("description") or thing.get("details", ""),
        source_url=url,
        source_platform="thingiverse",
        author=creator_name,
        author_url=f"https://www.thingiverse.com/{creator_name}" if creator_name else "",
        license=thing.get("license", ""),
        tags=tags,
        images=images,
        files=files,
    )


def _parse_from_og(soup: BeautifulSoup, thing_id: str, url: str) -> ScrapedModel:
    title = (soup.find("meta", property="og:title") or {}).get("content", "")
    description = (soup.find("meta", property="og:description") or {}).get("content", "")
    image_url = (soup.find("meta", property="og:image") or {}).get("content", "")
    images = [ScrapedFile(url=image_url, filename=f"preview_{thing_id}.jpg", file_type="image")] if image_url else []
    return ScrapedModel(title=title, description=description, source_url=url, source_platform="thingiverse", images=images, files=[])

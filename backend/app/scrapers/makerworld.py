import httpx
import re
from app.scrapers.base import ScrapedModel, ScrapedFile

API_BASE = "https://makerworld.com/api/v1/design-service/design"


def _extract_id(url: str) -> str | None:
    # Supports: /de/models/40146-slug, /en/models/40146, /models/40146
    m = re.search(r"/models/(\d+)", url)
    return m.group(1) if m else None


async def scrape(url: str) -> ScrapedModel:
    model_id = _extract_id(url)
    if not model_id:
        raise ValueError(f"Konnte keine Modell-ID aus URL extrahieren: {url}")

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://makerworld.com/",
    }

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        resp = await client.get(f"{API_BASE}/{model_id}")
        resp.raise_for_status()
        d = resp.json()

    if not d.get("id"):
        raise ValueError(f"Modell {model_id} nicht gefunden auf MakerWorld")

    creator = d.get("designCreator") or {}
    handle = creator.get("handle") or creator.get("name", "")
    author_url = f"https://makerworld.com/u/{handle}" if handle else ""

    # Collect images: cover + all instance pictures (deduplicated)
    seen_urls: set[str] = set()
    images: list[ScrapedFile] = []

    def _add_image(img_url: str) -> None:
        if img_url and img_url not in seen_urls:
            seen_urls.add(img_url)
            images.append(ScrapedFile(
                url=img_url,
                filename=img_url.split("/")[-1].split("?")[0],
                file_type="image",
            ))

    _add_image(d.get("coverUrl"))

    for inst in d.get("instances", []):
        _add_image(inst.get("cover"))
        for pic in inst.get("pictures", []):
            _add_image(pic.get("url"))
        # Plate thumbnails
        mi = (inst.get("extention") or {}).get("modelInfo") or {}
        for plate in mi.get("plates", []):
            _add_image((plate.get("thumbnail") or {}).get("url"))

    # Tags
    tags = [t for t in (d.get("tags") or []) if t]

    # License: MakerWorld uses short codes like BY-ND, BY, CC0, etc.
    license_str = d.get("license", "")

    # Print settings from default instance
    print_settings: dict = {}
    default_inst_id = d.get("defaultInstanceId")
    for inst in d.get("instances", []):
        if inst.get("id") == default_inst_id or not print_settings:
            filaments = inst.get("instanceFilaments") or []
            if filaments:
                print_settings["filaments"] = [
                    f.get("type", "") for f in filaments if f.get("type")
                ]
            pred = inst.get("prediction")
            if pred:
                minutes = pred // 60
                print_settings["print_time"] = f"{minutes // 60}h {minutes % 60}min" if minutes >= 60 else f"{minutes}min"

    # No file downloads available without auth — store source URL for reference
    files: list[ScrapedFile] = []

    canonical_url = f"https://makerworld.com/models/{model_id}"

    return ScrapedModel(
        title=d.get("title", ""),
        description=d.get("summary") or "",
        source_url=canonical_url,
        source_platform="makerworld",
        author=handle,
        author_url=author_url,
        license=license_str,
        tags=tags,
        print_settings=print_settings,
        images=images,
        files=files,
    )

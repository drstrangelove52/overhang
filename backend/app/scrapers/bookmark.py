import re
from urllib.parse import urlparse
from app.scrapers.base import ScrapedModel
from app.scrapers.detect import detect_platform, normalize_url


def _title_from_url(url: str) -> str:
    p = urlparse(url)
    segments = [s for s in p.path.split('/') if s]
    slug = segments[-1] if segments else p.netloc
    slug = re.sub(r'\.\w{2,5}$', '', slug)  # drop file extension like .html
    title = re.sub(r'[-_+]+', ' ', slug).strip()
    return title.title() if title else p.netloc


async def scrape(url: str, credentials: dict | None = None) -> ScrapedModel:
    """Link-only entry: no network access, title derived from the URL slug.

    Used for MakerLab generators and any unrecognized site. Title, description
    and files can be added manually afterwards.
    """
    platform = detect_platform(url)
    source_url = normalize_url(url, platform)
    return ScrapedModel(
        title=_title_from_url(source_url),
        source_url=source_url,
        source_platform=platform,
        author='MakerLab' if platform == 'makerlab' else '',
        tags=['generator'] if platform == 'makerlab' else [],
    )

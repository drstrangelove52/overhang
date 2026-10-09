import re
from urllib.parse import urlparse, urlunparse

_LOCALE = re.compile(r'^/[a-z]{2}(?:-[a-z]{2})?(?=/)', re.I)


def detect_platform(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if 'printables.com' in host:
        return 'printables'
    if 'thingiverse.com' in host:
        return 'thingiverse'
    if 'makerworld.com' in host:
        # MakerLab generators/tools have no model ID and no downloadable files
        if '/makerlab' in parsed.path.lower():
            return 'makerlab'
        return 'makerworld'
    if 'cults3d.com' in host:
        return 'cults3d'
    if parsed.scheme in ('http', 'https') and host:
        return 'bookmark'
    return 'unknown'


def normalize_url(url: str, platform: str) -> str:
    """Strip tracking query and locale prefix for link-only entries so duplicates are detected."""
    if platform != 'makerlab':
        return url
    p = urlparse(url)
    path = _LOCALE.sub('', p.path).rstrip('/')
    return urlunparse((p.scheme, p.netloc, path, '', '', ''))

from urllib.parse import urlparse

def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if 'printables.com' in host:
        return 'printables'
    if 'thingiverse.com' in host:
        return 'thingiverse'
    if 'makerworld.com' in host:
        return 'makerworld'
    if 'cults3d.com' in host:
        return 'cults3d'
    return 'unknown'

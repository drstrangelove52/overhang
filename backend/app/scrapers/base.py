from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ScrapedFile:
    url: str
    filename: str
    file_type: str  # stl, 3mf, image, other

@dataclass
class ScrapedModel:
    title: str
    description: str = ''
    source_url: str = ''
    source_platform: str = ''
    author: str = ''
    author_url: str = ''
    license: str = ''
    tags: list[str] = field(default_factory=list)
    print_settings: dict = field(default_factory=dict)
    files: list[ScrapedFile] = field(default_factory=list)
    images: list[ScrapedFile] = field(default_factory=list)

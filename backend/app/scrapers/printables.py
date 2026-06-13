import httpx
import re
from app.scrapers.base import ScrapedModel, ScrapedFile

GRAPHQL_URL = 'https://api.printables.com/graphql/'

QUERY = '''
query PrintDetail(: ID!) {
  print(id: ) {
    id
    name
    slug
    description
    license { name }
    user { publicUsername handle }
    tags { name }
    category { namePath }
    stls { name fileSize filePreviewPath downloadUrl }
    images { filePath }
    summary
  }
}
'''

def _extract_id(url: str) -> str | None:
    m = re.search(r'/model/(\d+)', url)
    return m.group(1) if m else None

async def scrape(url: str) -> ScrapedModel:
    model_id = _extract_id(url)
    if not model_id:
        raise ValueError(f'Konnte keine Modell-ID aus URL extrahieren: {url}')

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GRAPHQL_URL,
            json={'query': QUERY, 'variables': {'id': model_id}},
            headers={'Content-Type': 'application/json', 'User-Agent': 'Overhang/1.0'},
        )
        resp.raise_for_status()
        data = resp.json()

    p = data.get('data', {}).get('print')
    if not p:
        raise ValueError(f'Printables API hat kein Ergebnis zurückgegeben für ID {model_id}')

    user = p.get('user') or {}
    handle = user.get('handle') or user.get('publicUsername', '')

    images = [
        ScrapedFile(
            url=fhttps://media.printables.com/{img[filePath]},
            filename=img['filePath'].split('/')[-1],
            file_type='image',
        )
        for img in (p.get('images') or [])
        if img.get('filePath')
    ]

    stl_files = [
        ScrapedFile(
            url=f[downloadUrl],
            filename=f[name],
            file_type='3mf' if f['name'].lower().endswith('.3mf') else 'stl',
        )
        for f in (p.get('stls') or [])
        if f.get('downloadUrl')
    ]

    tags = [t['name'] for t in (p.get('tags') or []) if t.get('name')]

    return ScrapedModel(
        title=p.get('name', ''),
        description=p.get('description') or p.get('summary') or '',
        source_url=url,
        source_platform='printables',
        author=handle,
        author_url=f'https://www.printables.com/@{handle}' if handle else '',
        license=(p.get('license') or {}).get('name', ''),
        tags=tags,
        images=images,
        files=stl_files,
    )

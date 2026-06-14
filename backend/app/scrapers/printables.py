import httpx
import re
from app.scrapers.base import ScrapedModel, ScrapedFile

GRAPHQL_URL = "https://api.printables.com/graphql/"
CDN_BASE = "https://media.printables.com/"

QUERY = """
query PrintDetail($id: ID!) {
  print(id: $id) {
    id name description
    license { name }
    user { handle publicUsername }
    tags { name }
    stls { id name filePreviewPath fileSize }
    images { filePath }
    summary
  }
}
"""

def _extract_id(url: str):
    m = re.search(r"/model/(\d+)", url)
    return m.group(1) if m else None

def _stl_download_url(file_preview_path: str, filename: str) -> str | None:
    """Derive download URL from filePreviewPath.

    Only works for the pattern: media/prints/{id}/stls/{file_id_uuid}/{name}_preview.png
    Returns None for hash-based preview paths (newer models), where the URL can't be derived.
    """
    parts = file_preview_path.split("/")
    if len(parts) < 4 or parts[2] != "stls":
        return None
    dir_path = "/".join(parts[:-1])
    return CDN_BASE + dir_path + "/" + filename

async def _get_token(username: str, password: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                GRAPHQL_URL,
                json={'query': 'mutation Login($e:String!,$p:String!){login(username:$e,password:$p){token}}',
                      'variables': {'e': username, 'p': password}},
                headers={"Content-Type": "application/json"},
            )
            return resp.json().get('data', {}).get('login', {}).get('token')
    except Exception:
        return None


async def scrape(url: str, credentials: dict | None = None) -> ScrapedModel:
    model_id = _extract_id(url)
    if not model_id:
        raise ValueError(f"Konnte keine Modell-ID aus URL extrahieren: {url}")

    token = None
    if credentials:
        token = await _get_token(credentials['username'], credentials['password'])

    gql_headers = {"Content-Type": "application/json", "User-Agent": "Overhang/1.0"}
    if token:
        gql_headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GRAPHQL_URL,
            json={"query": QUERY, "variables": {"id": model_id}},
            headers=gql_headers,
        )
        resp.raise_for_status()
        data = resp.json()

    p = data.get("data", {}).get("print")
    if not p:
        raise ValueError(f"Modell {model_id} nicht gefunden auf Printables (privat oder geloescht?)")

    user = p.get("user") or {}
    handle = user.get("handle") or user.get("publicUsername", "")

    images = [
        ScrapedFile(
            url=CDN_BASE + img["filePath"],
            filename=img["filePath"].split("/")[-1],
            file_type="image",
        )
        for img in (p.get("images") or [])
        if img.get("filePath")
    ]

    stl_files = []
    for f in (p.get("stls") or []):
        if not f.get("name"):
            continue
        dl_url = _stl_download_url(f.get("filePreviewPath", ""), f["name"]) if f.get("filePreviewPath") else None
        if dl_url:
            stl_files.append(ScrapedFile(
                url=dl_url,
                filename=f["name"],
                file_type="3mf" if f["name"].lower().endswith(".3mf") else "stl",
            ))

    tags = [t["name"] for t in (p.get("tags") or []) if t.get("name")]

    return ScrapedModel(
        title=p.get("name", ""),
        description=p.get("description") or p.get("summary") or "",
        source_url=url,
        source_platform="printables",
        author=handle,
        author_url=f"https://www.printables.com/@{handle}" if handle else "",
        license=(p.get("license") or {}).get("name", ""),
        tags=tags,
        images=images,
        files=stl_files,
    )

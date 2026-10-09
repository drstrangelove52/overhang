import json
import re
from contextlib import asynccontextmanager

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/129.0.0.0 Safari/537.36"
)
_ALLOWED_DOMAINS = ('makerworld.com', 'bambulab.com')
_SAMESITE = {'strict': 'Strict', 'lax': 'Lax', 'none': 'None', 'no_restriction': 'None'}


def parse_cookies(raw: str) -> list[dict]:
    """Accept a cookie-extension JSON export, a `name=value; …` header string or a bare token.

    Only cookies for makerworld.com / bambulab.com are kept.
    """
    raw = (raw or '').strip()
    if not raw:
        return []

    cookies: list[dict] = []
    if raw[0] in '[{':
        data = json.loads(raw)
        if isinstance(data, dict):
            data = data.get('cookies', [data])
        for c in data:
            if not c.get('name') or c.get('value') is None:
                continue
            item = {
                'name': c['name'],
                'value': str(c['value']),
                'domain': c.get('domain') or '.makerworld.com',
                'path': c.get('path') or '/',
                'secure': bool(c.get('secure', True)),
                'httpOnly': bool(c.get('httpOnly', False)),
            }
            exp = c.get('expirationDate', c.get('expires'))
            if isinstance(exp, (int, float)) and exp > 0:
                item['expires'] = exp
            ss = _SAMESITE.get(str(c.get('sameSite', '')).lower())
            if ss:
                item['sameSite'] = ss
            cookies.append(item)
    elif '=' in raw:
        for part in re.split(r';\s*', raw):
            if '=' not in part:
                continue
            name, value = part.split('=', 1)
            cookies.append({'name': name.strip(), 'value': value.strip(), 'domain': '.makerworld.com',
                            'path': '/', 'secure': True})
    else:
        cookies.append({'name': 'token', 'value': raw, 'domain': '.makerworld.com', 'path': '/', 'secure': True})

    return [c for c in cookies if any(d in c['domain'] for d in _ALLOWED_DOMAINS)]


@asynccontextmanager
async def makerworld_page(cookies: list[dict] | None):
    """Headless Chromium on makerworld.com with the given session cookies, past the Cloudflare check."""
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=['--no-sandbox'])
        try:
            ctx = await browser.new_context(user_agent=UA, locale='de-DE')
            if cookies:
                await ctx.add_cookies(cookies)
            page = await ctx.new_page()
            await page.goto('https://makerworld.com/en/', wait_until='domcontentloaded', timeout=45000)
            await page.wait_for_function("document.title !== 'Just a moment...'", timeout=30000)
            yield page
        finally:
            await browser.close()


async def fetch_json(page, url: str) -> tuple[int, dict | None]:
    res = await page.evaluate(
        "async u => { const r = await fetch(u, {credentials: 'include', headers: {Accept: 'application/json'}});"
        " return {status: r.status, text: await r.text()} }",
        url,
    )
    try:
        return res['status'], json.loads(res['text'])
    except ValueError:
        return res['status'], None

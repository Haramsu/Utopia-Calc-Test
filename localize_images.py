from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import re

root = Path('_site')
page = root / 'index.html'
text = page.read_text(encoding='utf-8')
urls = sorted(set(re.findall(r'https://raw\.githubusercontent\.com/[^\s"\'<>]+?\.png', text)))
folder = root / 'img' / 'external'
folder.mkdir(parents=True, exist_ok=True)

def download(url):
    file = folder / (sha256(url.encode()).hexdigest()[:16] + '-' + Path(urlparse(url).path).name)
    request = Request(url, headers={'User-Agent': 'UtopiaPagesBuilder/1.0'})
    with urlopen(request, timeout=25) as response:
        content = response.read()
    if not content.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Not a PNG: ' + url)
    file.write_bytes(content)
    return url, './img/external/' + file.name

errors = []
with ThreadPoolExecutor(max_workers=10) as pool:
    tasks = {pool.submit(download, url): url for url in urls}
    for future in as_completed(tasks):
        try:
            url, local = future.result()
            text = text.replace(url, local)
        except Exception as e:
            errors.append((tasks[future], str(e)))
if errors:
    for url, error in errors:
        print('FAILED', url, error)
    raise SystemExit(f'{len(errors)} of {len(urls)} required image downloads failed; not publishing an incomplete version.')
page.write_text(text, encoding='utf-8')
print(f'{len(urls)} external image URLs converted to local website assets.')

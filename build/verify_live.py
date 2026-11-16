#!/usr/bin/env python3
"""Check that the live site serves exactly what is in dist/.

    python3 build/verify_live.py dist [https://getfort.io]

Every page, stylesheet, script, asset and download is fetched and compared byte
for byte; an unknown path must return 404 with the not-found page. Retries for a
while, since a new deployment takes a few seconds to reach every edge.
The one thing removed before comparing is the Cloudflare Web Analytics beacon,
which Cloudflare adds to some HTML responses itself.
"""
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


# Cloudflare Web Analytics adds its beacon to some HTML responses at the edge; it is
# not part of the deployed files, so it is removed before comparing.
BEACON = re.compile(rb'<script [^>]*src="https://static\.cloudflareinsights\.com/[^"]*"[^>]*></script>\n?')


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'fort-site-verify'})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, BEACON.sub(b'', response.read(), count=1)
    except urllib.error.HTTPError as err:
        return err.code, BEACON.sub(b'', err.read(), count=1)


def url_for(base, rel):
    if rel == 'index.html' or rel.endswith('/index.html'):
        rel = rel[:-len('index.html')]
    return f'{base}/{rel}'


def mismatches(dist, base):
    problems = []
    for path in sorted(p for p in dist.rglob('*') if p.is_file()):
        rel = path.relative_to(dist).as_posix()
        if rel == '404.html':
            continue
        status, body = fetch(url_for(base, rel))
        if status != 200 or body != path.read_bytes():
            problems.append(f'{url_for(base, rel)}: HTTP {status}, {"differs" if status == 200 else "not served"}')
    status, body = fetch(f'{base}/no-such-page-{int(time.time())}')
    if status != 404 or body != (dist / '404.html').read_bytes():
        problems.append(f'unknown path: HTTP {status}, expected 404 with 404.html')
    return problems


def main():
    dist = Path(sys.argv[1])
    base = (sys.argv[2] if len(sys.argv) > 2 else 'https://getfort.io').rstrip('/')
    for attempt in range(1, 7):
        problems = mismatches(dist, base)
        if not problems:
            print(f'{base} serves dist/ exactly ({sum(1 for p in dist.rglob("*") if p.is_file())} files).')
            return
        print(f'attempt {attempt}: {len(problems)} mismatches', file=sys.stderr)
        time.sleep(15)
    sys.exit('live site does not match dist/:\n' + '\n'.join(problems))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Tell Bing and the other IndexNow search engines about new or changed pages.

    python3 tools/indexnow.py                 # every URL in sitemap.xml
    python3 tools/indexnow.py --today         # only URLs whose lastmod is today
    python3 tools/indexnow.py <url> …         # just these

Run it after the change is live on GitHub Pages (the key file must be reachable).
The key file is /64af010eee27bcf9e593fd53ddb305cc.txt at the repo root; it only proves that we own the site.
"""
import datetime
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = 'not-yet.app'
KEY = '64af010eee27bcf9e593fd53ddb305cc'


def sitemap_urls(only_today):
    entries = re.findall(r'<loc>(.*?)</loc>\s*<lastmod>(.*?)</lastmod>', (ROOT / 'sitemap.xml').read_text())
    today = datetime.date.today().isoformat()
    return [u for u, d in entries if not only_today or d == today]


def main(args):
    urls = [a for a in args if a.startswith('https://')] or sitemap_urls('--today' in args)
    if not urls:
        sys.exit('No URLs to submit.')
    body = json.dumps({'host': HOST, 'key': KEY, 'keyLocation': f'https://{HOST}/{KEY}.txt', 'urlList': urls}).encode()
    req = urllib.request.Request('https://api.indexnow.org/indexnow', data=body,
                                 headers={'Content-Type': 'application/json; charset=utf-8'})
    with urllib.request.urlopen(req) as r:  # 200 or 202 means accepted
        print(r.status, f'{len(urls)} URLs submitted')


if __name__ == '__main__':
    main(sys.argv[1:])

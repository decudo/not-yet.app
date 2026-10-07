#!/usr/bin/env python3
"""Build every language version of not-yet.app.

Pages come from tools/i18n/templates/, texts from tools/i18n/<code>.json.
The generated HTML files (index.html, de/index.html, …, 404.html, t/index.html)
and sitemap.xml are committed; GitHub Pages serves them as they are.

    python3 tools/build-i18n.py         # pages + sitemap
    python3 tools/build-i18n.py --og    # also og.png / og-<code>.png (needs Google Chrome)

Template syntax:
    {{ns.key}}                   text from the language file (may contain inline HTML)
    {{@name}}                    value computed here (see builtins)
    <!--if ns.key-->…<!--/if-->  kept only when the text is not empty
    <!--each-lang-->…<!--/each-lang-->  repeated once per language (404 and tag page)
"""
import datetime
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / 'tools' / 'i18n'
SITE = 'https://not-yet.app/'
LANGS = ['en', 'de', 'es', 'fr', 'it', 'pt', 'ja', 'ko']  # en at /, the rest at /<code>/
PAGES = {'index': '', 'privacy': 'privacy/', 'imprint': 'imprint/', 'support': 'support/'}
NOINDEX = {'privacy', 'imprint'}  # meta robots noindex in their templates, left out of the sitemap
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
TESTFLIGHT = 'https://testflight.apple.com/join/B2FAqBDZ'  # public link, website-only tester group (100 seats)


def load(code):
    data = json.loads((I18N / f'{code}.json').read_text())
    flat = {f'{ns}.{k}': v for ns, kv in data.items() if ns != '_meta' for k, v in kv.items()}
    return data['_meta'], flat


META, TEXT = {}, {}
for c in LANGS:
    META[c], TEXT[c] = load(c)


def root(code):
    return '/' if code == 'en' else f'/{code}/'


def url(code, path):
    return SITE + root(code)[1:] + path


def mailto(subject):
    return 'mailto:info@not-yet.app?subject=' + urllib.parse.quote(subject)


def lang_menu(code, path):
    m, t = META[code], TEXT[code]
    items = []
    for c in LANGS:
        attrs = f'href="{root(c)}{path}" hreflang="{META[c]["hreflang"]}" lang="{META[c]["html_lang"]}"'
        if c == code:
            attrs += ' aria-current="true"'
        else:
            attrs += (f' data-lang="{c}" data-umami-event="language-switch"'
                      f' data-umami-event-from="{code}" data-umami-event-to="{c}"')
        items.append(f'<li><a {attrs}>{META[c]["name"]}</a></li>')
    return ('<details class="lang"><summary><span class="sr-only">' + t['common.language'] + ': ' + m['name']
            + '</span><span aria-hidden="true">' + code.upper() + '</span></summary><ul>' + ''.join(items) + '</ul></details>')


def builtins(code, page, path):
    m, t = META[code], TEXT[code]
    alternates = [f'<link rel="alternate" hreflang="{META[c]["hreflang"]}" href="{url(c, path)}">' for c in LANGS]
    alternates.append(f'<link rel="alternate" hreflang="x-default" href="{url("en", path)}">')
    locales = [f'<meta property="og:locale" content="{m["og_locale"]}">']
    locales += [f'<meta property="og:locale:alternate" content="{META[c]["og_locale"]}">' for c in LANGS if c != code]
    other = [f'<a href="{root(c)}{path}" hreflang="{c}" lang="{c}">{TEXT[code]["common." + n]}</a>'
             for c, n in (('en', 'english_version'), ('de', 'german_version')) if c != code]
    return {
        'lang': m['html_lang'],
        'langname': m['name'],
        'code': code,
        'root': root(code),
        'url': url(code, path),
        'alternates': '\n'.join(alternates),
        'og_locale': '\n'.join(locales),
        'og_image': SITE + ('og.png' if code == 'en' else f'og-{code}.png'),
        'langmenu': lang_menu(code, path),
        'testflight': TESTFLIGHT,
        'mailto_support': mailto(t['support.mail_subject']),
        'docmeta_links': ''.join(other),
        'redirect': '<script src="/assets/js/lang-redirect.js"></script>\n' if (code, page) == ('en', 'index') else '',
        'hidden_unless_en': '' if code == 'en' else ' hidden',
    }


def render(tpl, code, page, path):
    t, b = TEXT[code], builtins(code, page, path)

    def text(m):
        if m.group(1) not in t:
            sys.exit(f'{code}: missing text {m.group(1)}')
        return t[m.group(1)]

    def builtin(m):
        name, place = m.group(1), m.group(2)
        if name == 'ev':  # a TestFlight join link, counted by Umami
            return f'data-umami-event="testflight-invite" data-umami-event-lang="{code}" data-umami-event-place="{place}"'
        return b[name]

    out = re.sub(r'<!--if ([\w.]+)-->(.*?)<!--/if-->\n?', lambda m: m.group(2) if t.get(m.group(1)) else '', tpl, flags=re.S)
    out = re.sub(r'\{\{([a-z_]+\.\w+)\}\}', text, out)
    out = re.sub(r'\{\{@(\w+)(?::(\w+))?\}\}', builtin, out)  # after the texts: they may contain {{@…}} too
    if META[code].get('no_spaces'):  # Japanese: no spaces between sentences that the template joins
        out = re.sub(r'([。、！？」](?:</span>)?) (<span)', r'\1\2', out)
    if '{{' in out:
        sys.exit(f'{code} {page}: unresolved ' + re.search(r'\{\{[^}]*\}\}', out).group(0))
    return out


def check():
    """Every language has exactly the English keys; no straight quotes outside tags (texts go into attributes)."""
    ok = True
    for c in LANGS:
        missing = TEXT['en'].keys() - TEXT[c].keys()
        extra = TEXT[c].keys() - TEXT['en'].keys()
        if missing or extra:
            print(f'{c}: missing {sorted(missing)} extra {sorted(extra)}')
            ok = False
        for k, v in TEXT[c].items():
            if '"' in re.sub(r'<[^>]*>|\{\{[^}]*\}\}', '', v):
                print(f'{c}: {k} contains a straight double quote, use typographic quotes')
                ok = False
    if not ok:
        sys.exit(1)


def write(rel, html):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html)


def build():
    check()
    for page, path in PAGES.items():
        tpl = (I18N / 'templates' / f'{page}.html').read_text()
        for c in LANGS:
            write(root(c)[1:] + path + 'index.html', render(tpl, c, page, path))
    for name, rel in (('404', '404.html'), ('t', 't/index.html')):
        tpl = (I18N / 'templates' / f'{name}.html').read_text()
        tpl = re.sub(r'<!--each-lang-->\n(.*?)<!--/each-lang-->\n',
                     lambda m: ''.join(render(m.group(1), c, name, '') for c in LANGS), tpl, flags=re.S)
        write(rel, render(tpl, 'en', name, ''))
    today = datetime.date.today().isoformat()
    # Plain URL list; the language alternates (hreflang) live in every page's <head>.
    urls = [f'  <url>\n    <loc>{url(c, path)}</loc>\n    <lastmod>{today}</lastmod>\n  </url>'
            for page, path in PAGES.items() if page not in NOINDEX for c in LANGS]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + '\n'.join(urls) + '\n</urlset>\n')
    print(f'Built {len(PAGES) * len(LANGS)} pages, 404.html, t/index.html and sitemap.xml for {", ".join(LANGS)}.')


def og():
    """Screenshot tools/i18n/og.html once per language (1200×630)."""
    tpl = (I18N / 'og.html').read_text()
    for c in LANGS:
        tmp = I18N / f'.og-{c}.html'
        tmp.write_text(render(tpl, c, 'og', ''))
        out = ROOT / ('og.png' if c == 'en' else f'og-{c}.png')
        subprocess.run([CHROME, '--headless', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                        '--window-size=1200,630', f'--screenshot={out}', tmp.as_uri()],
                       check=True, capture_output=True)
        tmp.unlink()
        print('wrote', out.name)


if __name__ == '__main__':
    build()
    if '--og' in sys.argv:
        og()

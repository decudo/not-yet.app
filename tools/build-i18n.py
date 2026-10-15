#!/usr/bin/env python3
"""Build every language version of not-yet.app.

Pages come from tools/i18n/templates/, texts from tools/i18n/<code>.json.
Feature pages (FEATURES) share templates/feature.html; their texts live in the namespace
named after the page and are read through {{page.key}}.
The generated HTML files (index.html, de/index.html, …, 404.html, t/index.html)
and sitemap.xml are committed; GitHub Pages serves them as they are.

    python3 tools/build-i18n.py         # pages + sitemap
    python3 tools/build-i18n.py --og    # also og.jpg / og-<code>.jpg (needs Google Chrome)

Template syntax:
    {{ns.key}}                   text from the language file (may contain inline HTML)
    {{@name}}                    value computed here (see builtins)
    {{@page:alarm}}              link to a feature page in the current language
    <!--if ns.key-->…<!--/if-->  kept only when the text is not empty
    <!--each-lang-->…<!--/each-lang-->  repeated once per language (404 and tag page)
"""
import datetime
import html
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
# Feature pages: one template, texts in the namespace of the same name, a slug per language.
FEATURES = {
    'alarm': {'en': 'alarm/', 'de': 'wecker/', 'es': 'despertador/', 'fr': 'reveil/', 'it': 'sveglia/',
              'pt': 'despertador/', 'ja': 'alarm/', 'ko': 'alarm/'},
    'applock': {'en': 'app-lock/', 'de': 'app-sperre/', 'es': 'bloquear-apps/', 'fr': 'blocage-apps/',
                'it': 'blocco-app/', 'pt': 'bloqueio-de-apps/', 'ja': 'app-lock/', 'ko': 'app-lock/'},
    'routines': {'en': 'routines/', 'de': 'routinen/', 'es': 'rutinas/', 'fr': 'routines/', 'it': 'routine/',
                 'pt': 'rotinas/', 'ja': 'routines/', 'ko': 'routines/'},
    'nights': {'en': 'nights/', 'de': 'abendroutine/', 'es': 'rutina-de-noche/', 'fr': 'routine-du-soir/',
               'it': 'routine-serale/', 'pt': 'rotina-noturna/', 'ja': 'nights/', 'ko': 'nights/'},
    'week': {'en': 'week/', 'de': 'wochenplaner/', 'es': 'planificador-semanal/', 'fr': 'planning-hebdomadaire/',
             'it': 'planner-settimanale/', 'pt': 'planner-semanal/', 'ja': 'week/', 'ko': 'week/'},
}
# Phones on a feature page ({{@shot:hero}}, {{@shot:s1}} … {{@shot:s3}}): screen from assets/img/<code>/, alt text page.alt_<place>.
SHOTS = {'alarm': {'hero': 'alarm', 's1': 'lock'}, 'applock': {'hero': 'focus', 's2': 'nights'},
         'routines': {'hero': 'boss', 's2': 'lock', 's3': 'piggy'}, 'nights': {'hero': 'nights', 's2': 'alarm'},
         'week': {'hero': 'week', 's1': 'home'}}
NOINDEX = {'privacy', 'imprint'}  # meta robots noindex in their templates, left out of the sitemap
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
TESTFLIGHT = 'https://testflight.apple.com/join/B2FAqBDZ'  # public link, website-only tester group (100 seats)
APP_STORE = 'https://apps.apple.com/app/id6815270832'  # Apple's official badge per language: assets/img/app-store-badge-<code>.svg


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


def path_of(page, code):
    """The page's path below the language root ('' for home, 404 and the tag page)."""
    return FEATURES[page][code] if page in FEATURES else PAGES.get(page, '')


def mailto(subject):
    return 'mailto:info@not-yet.app?subject=' + urllib.parse.quote(subject)


def lang_menu(code, page):
    m, t = META[code], TEXT[code]
    items = []
    for c in LANGS:
        attrs = f'href="{root(c)}{path_of(page, c)}" hreflang="{META[c]["hreflang"]}" lang="{META[c]["html_lang"]}"'
        if c == code:
            attrs += ' aria-current="true"'
        else:
            attrs += (f' data-lang="{c}" data-umami-event="language-switch"'
                      f' data-umami-event-from="{code}" data-umami-event-to="{c}"')
        items.append(f'<li><a {attrs}>{META[c]["name"]}</a></li>')
    return ('<details class="lang"><summary><span class="sr-only">' + t['common.language'] + ': ' + m['name']
            + '</span><span aria-hidden="true">' + code.upper() + '</span></summary><ul>' + ''.join(items) + '</ul></details>')


def shot(code, page, place):
    """A phone with one of the language's App Store screens, or nothing if the page has none there."""
    name = SHOTS.get(page, {}).get(place)
    if not name:
        return ''
    src = f'/assets/img/{code}/{name}'
    load = 'fetchpriority="high"' if place == 'hero' else 'loading="lazy"'
    return (f'<div class="art"><div class="iphone"><div class="bezel"><div class="glass"><img src="{src}-720.webp" '
            f'srcset="{src}-360.webp 360w, {src}-720.webp 720w" sizes="(max-width: 760px) 220px, 300px" '
            f'alt="{TEXT[code][f"{page}.alt_{place}"]}" width="720" height="1565" {load} decoding="async"></div></div></div></div>')


def faq(page_html):
    """The FAQ as it is visible on the page: every <details><summary>Q</summary><p>A</p></details>, as plain text."""
    plain = lambda s: html.unescape(re.sub(r'<[^>]+>', '', s)).strip()
    return [{'@type': 'Question', 'name': plain(q), 'acceptedAnswer': {'@type': 'Answer', 'text': plain(a)}}
            for q, a in re.findall(r'<details><summary>(.*?)</summary><p>(.*?)</p></details>', page_html, re.S)]


def jsonld(code, page, page_html):
    """Structured data. Home: the site, its publisher, the app and the FAQ (no offers or ratings, P83).
    Feature pages: breadcrumb and FAQ."""
    if page in FEATURES:
        crumbs = [(TEXT[code]['common.home_crumb'], url(code, '')), (TEXT[code][page + '.crumb'], url(code, path_of(page, code)))]
        graph = [{'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(crumbs)]}]
        if questions := faq(page_html):
            graph.append({'@type': 'FAQPage', '@id': crumbs[1][1] + '#faq', 'inLanguage': META[code]['html_lang'],
                          'mainEntity': questions})
        data = {'@context': 'https://schema.org', '@graph': graph}
        return json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    app_langs = [META[c]['html_lang'] for c in LANGS]
    data = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'WebSite', '@id': SITE + '#website', 'name': 'Not Yet', 'url': SITE,
         'inLanguage': app_langs, 'publisher': {'@id': SITE + '#publisher'}},
        {'@type': 'Person', '@id': SITE + '#publisher', 'name': 'Lars Keggenhoff', 'url': SITE + 'imprint/'},
        {'@type': ['SoftwareApplication', 'MobileApplication'], '@id': SITE + '#app', 'name': 'Not Yet',
         'url': url(code, ''), 'description': TEXT[code]['home.description'],
         'operatingSystem': 'iOS 26, watchOS 26', 'applicationCategory': 'ProductivityApplication',
         'inLanguage': app_langs, 'image': SITE + 'apple-touch-icon.png',
         'screenshot': [f'{SITE}assets/img/{code}/{s}-720.webp' for s in ('home', 'alarm', 'week', 'nights')],
         'downloadUrl': APP_STORE, 'installUrl': APP_STORE, 'sameAs': APP_STORE,
         'publisher': {'@id': SITE + '#publisher'}},
        {'@type': 'FAQPage', '@id': url(code, '') + '#faq', 'inLanguage': META[code]['html_lang'],
         'mainEntity': faq(page_html)},
    ]}
    return json.dumps(data, ensure_ascii=False).replace('</', '<\\/')


def builtins(code, page, path):
    m, t = META[code], TEXT[code]
    alternates = [f'<link rel="alternate" hreflang="{META[c]["hreflang"]}" href="{url(c, path_of(page, c))}">' for c in LANGS]
    alternates.append(f'<link rel="alternate" hreflang="x-default" href="{url("en", path_of(page, "en"))}">')
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
        'og_image': SITE + ('og.jpg' if code == 'en' else f'og-{code}.jpg'),
        'langmenu': lang_menu(code, page),
        'testflight': TESTFLIGHT,
        'appstore': APP_STORE,
        'mailto_support': mailto(t['support.mail_subject']),
        'docmeta_links': ''.join(other),
        'redirect': '<script src="/assets/js/lang-redirect.js"></script>\n' if (code, page) == ('en', 'index') else '',
        'hidden_unless_en': '' if code == 'en' else ' hidden',
        'jsonld': '<!--jsonld-->',  # filled in after rendering, from the visible FAQ
    }


def render(tpl, code, page, path):
    t, b = TEXT[code], builtins(code, page, path)
    if page in FEATURES:  # {{page.key}} reads the page's own namespace
        t = t | {'page.' + k.split('.', 1)[1]: v for k, v in t.items() if k.startswith(page + '.')}

    def text(m):
        if m.group(1) not in t:
            sys.exit(f'{code}: missing text {m.group(1)}')
        return t[m.group(1)]

    def builtin(m):
        name, place = m.group(1), m.group(2)
        if name == 'ev':  # a TestFlight join link, counted by Umami
            return f'data-umami-event="testflight-invite" data-umami-event-lang="{code}" data-umami-event-place="{place}"'
        if name == 'evs':  # an App Store link, counted by Umami
            return f'data-umami-event="app-store" data-umami-event-lang="{code}" data-umami-event-place="{place}"'
        if name == 'page':  # link to a feature page in this language
            return root(code) + FEATURES[place][code]
        if name == 'shot':  # a phone on a feature page
            return shot(code, page, place)
        return b[name]

    out = re.sub(r'<!--if ([\w.]+)-->(.*?)<!--/if-->\n?', lambda m: m.group(2) if t.get(m.group(1)) else '', tpl, flags=re.S)
    out = re.sub(r'\{\{([a-z_]+\.\w+)\}\}', text, out)
    out = re.sub(r'\{\{@(\w+)(?::(\w+))?\}\}', builtin, out)  # after the texts: they may contain {{@…}} too
    if META[code].get('no_spaces'):  # Japanese: no spaces between sentences that the template joins
        out = re.sub(r'([。、！？」](?:</span>|</b>)?) (<span|[^\x00-\x7f])', r'\1\2', out)
    if '{{' in out:
        sys.exit(f'{code} {page}: unresolved ' + re.search(r'\{\{[^}]*\}\}', out).group(0))
    return out.replace('<!--jsonld-->', jsonld(code, page, out) if page == 'index' or page in FEATURES else '')


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


def write(rel, text):
    """Write a generated file; returns False when it was already exactly like this."""
    p = ROOT / rel
    if p.exists() and p.read_text() == text:
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return True


def sitemap(changed):
    """Plain URL list; the language alternates (hreflang) live in every page's <head>.
    A URL keeps its old lastmod unless its page was rewritten in this build."""
    old = dict(re.findall(r'<loc>(.*?)</loc>\s*<lastmod>(.*?)</lastmod>', (ROOT / 'sitemap.xml').read_text()))
    today = datetime.date.today().isoformat()
    urls = [f'  <url>\n    <loc>{u}</loc>\n    <lastmod>{today if c or u not in old else old[u]}</lastmod>\n  </url>'
            for u, c in changed.items()]
    write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + '\n'.join(urls) + '\n</urlset>\n')


def build():
    check()
    changed = {}  # indexable URL -> rewritten in this build
    for page, path in PAGES.items():
        tpl = (I18N / 'templates' / f'{page}.html').read_text()
        for c in LANGS:
            new = write(root(c)[1:] + path + 'index.html', render(tpl, c, page, path))
            if page not in NOINDEX:
                changed[url(c, path)] = new
    for page, paths in FEATURES.items():
        tpl = (I18N / 'templates' / 'feature.html').read_text()
        for c in LANGS:
            changed[url(c, paths[c])] = write(root(c)[1:] + paths[c] + 'index.html', render(tpl, c, page, paths[c]))
    for name, rel in (('404', '404.html'), ('t', 't/index.html')):
        tpl = (I18N / 'templates' / f'{name}.html').read_text()
        tpl = re.sub(r'<!--each-lang-->\n(.*?)<!--/each-lang-->\n',
                     lambda m: ''.join(render(m.group(1), c, name, '') for c in LANGS), tpl, flags=re.S)
        write(rel, render(tpl, 'en', name, ''))
    sitemap(changed)
    print(f'Built {(len(PAGES) + len(FEATURES)) * len(LANGS)} pages, 404.html, t/index.html and sitemap.xml for {", ".join(LANGS)}.')


def og():
    """Screenshot tools/i18n/og.html once per language (1200×630), saved as JPEG (quality 82, about 65 KB)."""
    from PIL import Image
    tpl = (I18N / 'og.html').read_text()
    for c in LANGS:
        tmp = I18N / f'.og-{c}.html'
        png = I18N / f'.og-{c}.png'
        tmp.write_text(render(tpl, c, 'og', ''))
        out = ROOT / ('og.jpg' if c == 'en' else f'og-{c}.jpg')
        subprocess.run([CHROME, '--headless', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                        '--window-size=1200,630', f'--screenshot={png}', tmp.as_uri()],
                       check=True, capture_output=True)
        Image.open(png).convert('RGB').save(out, 'JPEG', quality=82, optimize=True, progressive=True)
        tmp.unlink()
        png.unlink()
        print('wrote', out.name)


if __name__ == '__main__':
    build()
    if '--og' in sys.argv:
        og()

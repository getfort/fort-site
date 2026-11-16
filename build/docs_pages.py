"""Assemble full docs pages: shared chrome (docs-page.html) + sidebar + Markdown body."""
import html
import re
from pathlib import Path

from site_markdown import MarkdownError, check_safe, front_matter, inline, link_item, render

TEMPLATE = (Path(__file__).with_name('docs-page.html')).read_text()
SITE = 'https://getfort.io/docs/'
PAGE_KEYS = {'title', 'description', 'skip', 'contents', 'og_title', 'og_description'}
SIDEBAR_KEYS = {'summary', 'home', 'note_label', 'note'}


def attr(value):
    return html.escape(value)


def sidebar(source, docs, page):
    """The docs navigation. Links are written relative to the docs root.

    The current page is the longest fragment-free link that is a prefix of the
    page path, so a guide's reference page highlights the guide; failing that,
    the first link into this page (for pages listed only by section).
    """
    meta, body = front_matter(source)
    missing = SIDEBAR_KEYS - meta.keys()
    if missing or meta.keys() - SIDEBAR_KEYS:
        raise MarkdownError(f'_sidebar.md front matter must be exactly {sorted(SIDEBAR_KEYS)}')
    entries = []
    for line in filter(str.strip, body.split('\n')):
        if line.startswith('## '):
            entries.append(('label', line[3:], None))
        elif line.startswith('- '):
            label, href = link_item(line[2:])
            entries.append(('link', label, href))
        else:
            raise MarkdownError(f'_sidebar.md: expected "## label" or "- [link](path)": {line}')
    links = [h for kind, _, h in entries if kind == 'link']
    candidates = [h for h in links if '#' not in h and page.startswith(h)]
    same_page = [h for h in links if h.split('#')[0] == page]
    current = max(candidates, key=len, default=same_page[0] if same_page else None)
    nav = []
    for kind, label, href in entries:
        if kind == 'label':
            nav.append(f'<p class="sidebar-label">{inline(label)}</p>')
        else:
            mark = ' aria-current="page"' if href == current else ''
            nav.append(f'<a href="{attr(docs + href)}"{mark}>{inline(label)}</a>')
    return (
        '<aside class="docs-sidebar"><details class="docs-navigation" open>'
        f'<summary>{inline(meta["summary"])}</summary>'
        f'<a class="docs-home" href="{attr(docs)}">{inline(meta["home"])}</a>'
        f'<nav aria-label="Documentation">{"".join(nav)}</nav>'
        f'<div class="sidebar-note"><span class="status-dot"></span> {inline(meta["note_label"])}'
        f'<p>{inline(meta["note"])}</p></div></details></aside>'
    )


def page(source, page_path, sidebar_source):
    """Render one page. `page_path` is relative to /docs/, e.g. 'gcp/reference/' or ''."""
    meta, body = front_matter(source)
    unknown = meta.keys() - PAGE_KEYS
    missing = {'title', 'description', 'skip'} - meta.keys()
    if unknown or missing:
        raise MarkdownError(f'front matter: unknown {sorted(unknown)}, missing {sorted(missing)}')
    depth = page_path.count('/')
    docs = '../' * depth
    root = '../' * (depth + 1)
    canonical = SITE + page_path
    og = ''
    if 'og_title' in meta:
        og = (f'<meta property="og:title" content="{attr(meta["og_title"])}">'
              f'<meta property="og:description" content="{attr(meta["og_description"])}">'
              f'<meta property="og:url" content="{attr(canonical)}">')
    main = render(body)
    if meta.get('contents'):
        links = ''.join(f'<a href="{attr(h)}">{inline(t)}</a>' for t, h in map(link_item, meta['contents']))
        main = f'<nav class="page-contents" aria-label="On this page"><span>On this page</span>{links}</nav>\n{main}'
    side = sidebar(sidebar_source, docs, page_path)
    for fragment in (main, side, inline(meta['skip'])):
        check_safe(fragment)
    values = {
        'canonical': attr(canonical), 'og': og, 'description': attr(meta['description']),
        'title': html.escape(meta['title'], quote=False), 'skip': inline(meta['skip']),
        'root': root, 'docs': docs, 'docs_link': docs or './',
        'sidebar': side, 'main': main,
    }
    # One pass, so text in a page can never be read as a placeholder.
    return re.sub(r'\{\{(\w+)\}\}', lambda m: values[m.group(1)], TEMPLATE)

"""Write the files AI agents and crawlers look for, from the pages that were just built.

- index.md next to every page: its Markdown twin (html_markdown.py).
- /llms.txt, /docs/llms.txt, /llms-full.txt: what Fort is, when to use it, and every page.
- /agents.md: the same guidance as /llms.txt, where agents look for instructions.
- /sitemap.xml and /robots.txt.
- /.well-known/ard.json: the list of all of the above (Agentic Resource Discovery).
- /.well-known/agent-skills/: one skill that tells an agent how to answer questions about Fort.

Nothing here has its own copy of the docs: the text comes from the built pages, and the
fixed words about Fort come from agents/about.md and agents/skill.md, which name no
page themselves: the page lists are filled in from the pages built.
"""
import hashlib
import html
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from html_markdown import twin
from site_markdown import link_item

SITE = Path(__file__).resolve().parents[1]
ORIGIN = 'https://getfort.io/'
SKILL = 'fort-docs'
SKILLS_SCHEMA = 'https://schemas.agentskills.io/discovery/0.2.0/schema.json'
# Sent with the home page and every docs page, so an agent that only reads headers finds these.
LINKS = ('</sitemap.xml>; rel="sitemap", </llms.txt>; rel="describedby"; type="text/plain", '
         '<{twin}>; rel="alternate"; type="text/markdown", </.well-known/ard.json>; rel="ard", '
         '</.well-known/agent-skills/index.json>; rel="describedby"; type="application/json"')


class Page:
    """One published page: `path` is '' for the home page, 'docs/gcp/' for a docs page."""

    def __init__(self, path, title, description):
        self.path, self.title, self.description = path, title, description
        self.url = ORIGIN + path
        self.twin = self.url + 'index.md'
        self.name = re.sub(r' — Fort( Docs)?$', '', title)


def head_meta(page_html):
    """(title, description) as the page's <head> states them."""
    title = re.search(r'<title>(.*?)</title>', page_html, re.S)
    description = re.search(r'<meta name="description" content="([^"]*)"', page_html)
    if not title or not description:
        raise ValueError('a page needs a <title> and a meta description')
    return html.unescape(title.group(1)), html.unescape(description.group(1))


def ordered(paths, sidebar):
    """Docs page paths in the order the docs navigation lists them; unlisted pages follow."""
    listed = []
    for line in sidebar.split('\n'):
        if line.startswith('- '):
            href = 'docs/' + link_item(line[2:])[1].split('#')[0]
            if href in paths and href not in listed:
                listed.append(href)
    return ['docs/'] + [p for p in listed if p != 'docs/'] + sorted(set(paths) - set(listed) - {'docs/'})


def page_list(pages):
    return '\n'.join(f'- [{p.name}]({p.twin}): {p.description}' for p in pages)


def llms(about, home, docs):
    guides = [p for p in docs if not p.path.endswith('/reference/')]
    reference = [p for p in docs if p.path.endswith('/reference/')]
    return (f'{about.strip()}\n\n## Docs\n\n{page_list([home] + guides)}\n\n## Optional\n\n'
            f'{page_list(reference)}\n- [Everything in one file]({ORIGIN}llms-full.txt): '
            'this page followed by every page above.\n')


def docs_llms(docs):
    return ('# Fort documentation\n\n> How to understand, deploy and operate Fort: security and '
            'governance for AI agents, run in your own cloud.\n\n'
            f'What Fort is and when to use it: {ORIGIN}llms.txt\n\n## Docs\n\n{page_list(docs)}\n')


def sitemap(pages):
    urls = ''.join(f'<url><loc>{escape(p.url)}</loc></url>' for p in pages)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')


def skills_index(skill_md):
    front = re.match(r'---\n(.*?)\n---\n', skill_md, re.S)
    meta = dict(line.split(': ', 1) for line in front.group(1).split('\n')) if front else {}
    if meta.get('name') != SKILL or not meta.get('description'):
        raise ValueError(f'agents/skill.md front matter needs name: {SKILL} and a description')
    return json.dumps({'$schema': SKILLS_SCHEMA, 'skills': [{
        'name': SKILL, 'type': 'skill-md', 'description': meta['description'],
        'url': f'/.well-known/agent-skills/{SKILL}/SKILL.md',
        'digest': 'sha256:' + hashlib.sha256(skill_md.encode()).hexdigest(),
    }]}, indent=1) + '\n'


def ard(home, docs, skill_description):
    """/.well-known/ard.json (Agentic Resource Discovery): what this site has for agents."""
    def entry(name, display, kind, url, description, queries):
        return {'identifier': f'urn:air:getfort.io:{name}', 'displayName': display, 'type': kind,
                'url': url, 'description': description, 'representativeQueries': queries}
    entries = [
        entry('llms-txt', 'Fort: what it is, when to use it, every page', 'text/plain', ORIGIN + 'llms.txt',
              home.description, ['what is Fort', 'when should I use Fort for AI agents', 'list the Fort pages']),
        entry('docs/llms-txt', 'Fort documentation index', 'text/plain', ORIGIN + 'docs/llms.txt',
              'Every Fort documentation page as Markdown, with a one-line summary.',
              ['find the Fort documentation', 'how do I deploy Fort']),
        entry(f'skills/{SKILL}', SKILL, 'application/agent-skills+md',
              f'{ORIGIN}.well-known/agent-skills/{SKILL}/SKILL.md', skill_description,
              ['answer a question about Fort', 'how does Fort govern AI agents']),
    ]
    for page in docs:
        entries.append(entry(page.path.rstrip('/'), page.name, 'text/markdown', page.twin, page.description,
                             [f'{page.name} for Fort', f'read the Fort page "{page.name}"']))
    return json.dumps({'entries': entries}, indent=1, ensure_ascii=False) + '\n'


def headers(pages):
    """Lines for Cloudflare's _headers file: discovery links on every page."""
    rules = []
    for page in pages:
        link = LINKS.format(twin='/' + page.path + 'index.md')
        rules.append(f'/{page.path}\n  Link: {link}\n')
    return ''.join(rules) + '/.well-known/*\n  Access-Control-Allow-Origin: *\n'


def write(out, docs_meta, sidebar):
    """Write every agent file into out/. `docs_meta` maps a docs path ('gcp/') to (title, description).

    Returns the pages, home page first.
    """
    home = Page('', *head_meta((out / 'index.html').read_text()))
    home.name = 'Fort home page'
    by_path = {'docs/' + path: Page('docs/' + path, *meta) for path, meta in docs_meta.items()}
    docs = [by_path[path] for path in ordered(list(by_path), sidebar)]
    pages = [home] + docs
    footer = f'Every Fort page as Markdown: {ORIGIN}llms.txt'
    twins = []
    for page in pages:
        text = twin((out / page.path / 'index.html').read_text(), page.url, page.title,
                    page.description, f'Source: {page.url} · {footer}')
        (out / page.path / 'index.md').write_text(text)
        twins.append(text)
    about = (SITE / 'agents' / 'about.md').read_text()
    skill = (SITE / 'agents' / 'skill.md').read_text().replace('{{pages}}', page_list(docs))
    files = {
        'llms.txt': llms(about, home, docs),
        'docs/llms.txt': docs_llms(docs),
        'llms-full.txt': about.strip() + '\n\n---\n\n' + '\n---\n\n'.join(twins),
        'sitemap.xml': sitemap(pages),
        'robots.txt': f'User-agent: *\nAllow: /\n\nSitemap: {ORIGIN}sitemap.xml\n',
        f'.well-known/agent-skills/{SKILL}/SKILL.md': skill,
        '.well-known/agent-skills/index.json': skills_index(skill),
    }
    files['agents.md'] = files['llms.txt']  # the same guidance, where agents look for instructions
    description = json.loads(files['.well-known/agent-skills/index.json'])['skills'][0]['description']
    files['.well-known/ard.json'] = ard(home, docs, description)
    for name, text in files.items():
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_text(text)
    return pages

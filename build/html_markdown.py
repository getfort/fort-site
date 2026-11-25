"""Turn a published page's <main> into plain Markdown, for agents that read text.

Every page gets a Markdown twin next to it (index.md). It is made from the HTML that
is published, so the two can never say different things. Decoration is left out:
drawings, navigation, anything hidden or aria-hidden, buttons, and blocks marked data-agent="skip".
"""
import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin

VOID = {'br', 'img', 'input', 'hr', 'meta', 'link', 'source', 'wbr'}
SKIP = {'svg', 'script', 'style', 'button', 'template', 'img', 'input', 'hr', 'nav'}
HEADINGS = {'h1': 2, 'h2': 3, 'h3': 4, 'h4': 5}  # the twin's own title is the only level 1
BLOCKS = set(HEADINGS) | {'p', 'div', 'section', 'article', 'ul', 'ol', 'li', 'table', 'pre', 'figure',
                          'figcaption', 'details', 'summary', 'nav', 'aside', 'main', 'small'}
MARKS = {'strong': '**', 'b': '**', 'em': '*', 'i': '*'}


class Node:
    def __init__(self, tag, attrs):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def hidden(self):
        return (self.tag in SKIP or 'hidden' in self.attrs or self.attrs.get('aria-hidden') == 'true'
                or self.attrs.get('data-agent') == 'skip')


class _Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('root', [])
        self.open = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.open[-1].children.append(node)
        if tag not in VOID:
            self.open.append(node)

    def handle_startendtag(self, tag, attrs):
        self.open[-1].children.append(Node(tag, attrs))

    def handle_endtag(self, tag):
        for depth in range(len(self.open) - 1, 0, -1):
            if self.open[depth].tag == tag:
                del self.open[depth:]
                return

    def handle_data(self, data):
        self.open[-1].children.append(data)


def find(node, tag):
    """The first <tag> element under node, or None."""
    for child in node.children:
        if isinstance(child, Node):
            if child.tag == tag:
                return child
            found = find(child, tag)
            if found:
                return found
    return None


def squeeze(value):
    return re.sub(r'\s+', ' ', value).strip()


def raw_text(node):
    return ''.join(c if isinstance(c, str) else raw_text(c) for c in node.children)


def has_block(node):
    return any(isinstance(c, Node) and not c.hidden() and (c.tag in BLOCKS or has_block(c))
               for c in node.children)


class Writer:
    def __init__(self, url):
        self.url = url

    def inline(self, node):
        """The node's content on one line."""
        parts, after_element = [], False
        for child in node.children:
            if isinstance(child, str):
                parts.append(re.sub(r'\s+', ' ', child))
                after_element = False
                continue
            if child.hidden():
                continue
            piece = self.inline_element(child)
            # Two elements written back to back (<strong>a</strong><span>b</span>) are
            # separate things on the page; keep them apart in text too.
            if piece and (after_element or child.tag in BLOCKS) and parts and not parts[-1].endswith(' '):
                parts.append(' ')
            parts.append(piece)
            if child.tag in BLOCKS:
                parts.append(' ')
            after_element = bool(piece)
        return squeeze(''.join(parts))

    def inline_element(self, node):
        if node.tag == 'br':
            return ' '
        if node.tag == 'code':
            return f'`{squeeze(raw_text(node))}`'
        body = self.inline(node)
        if not body:
            return ''
        if node.tag in MARKS:
            return f'{MARKS[node.tag]}{body}{MARKS[node.tag]}'
        if node.tag == 'a' and node.attrs.get('href'):
            return self.link(node, body)
        return body

    def link(self, node, body):
        return f'[{body}]({urljoin(self.url, node.attrs["href"])})'

    def card(self, node):
        """A link wrapped around a whole card: the card's heading becomes the link."""
        parts, linked = [], False
        for child in node.children:
            if isinstance(child, Node) and child.hidden():
                continue
            piece = squeeze(child) if isinstance(child, str) else self.inline(child)
            if piece and isinstance(child, Node) and child.tag in HEADINGS and not linked:
                piece, linked = f'**{self.link(node, piece)}**', True
            if piece:
                parts.append(piece)
        return ' '.join(parts) if linked else self.link(node, ' '.join(parts))

    def blocks(self, node):
        """The node as a list of Markdown blocks."""
        if node.hidden():
            return []
        tag = node.tag
        if tag in HEADINGS:
            body = self.inline(node)
            return [f'{"#" * HEADINGS[tag]} {body}'] if body else []
        if tag == 'pre':
            return ['```\n' + raw_text(node).strip('\n') + '\n```']
        if tag in ('ul', 'ol'):
            items = [self.inline(c) for c in node.children if isinstance(c, Node) and c.tag == 'li']
            marks = [f'{n}.' if tag == 'ol' else '-' for n in range(1, len(items) + 1)]
            return ['\n'.join(f'{mark} {item}' for mark, item in zip(marks, items) if item)]
        if tag == 'table':
            return self.table(node)
        if tag == 'a' and has_block(node):
            return [self.card(node)]
        if not has_block(node):
            body = self.inline(node)
            return [body] if body else []
        out, run = [], Node('run', [])
        for child in node.children + [None]:
            if child is not None and (isinstance(child, str) or not (child.tag in BLOCKS or has_block(child))):
                run.children.append(child)
                continue
            body = self.inline(run)
            if body:
                out.append(body)
            run = Node('run', [])
            if child is not None:
                out += self.blocks(child)
        return out

    def table(self, node):
        rows = []
        for row in self.rows(node):
            cells = [self.inline(c).replace('|', '\\|') for c in row.children
                     if isinstance(c, Node) and c.tag in ('th', 'td')]
            rows.append('| ' + ' | '.join(cells) + ' |')
            if len(rows) == 1:
                rows.append('|' + ' --- |' * len(cells))
        return ['\n'.join(rows)] if rows else []

    def rows(self, node):
        for child in node.children:
            if isinstance(child, Node):
                if child.tag == 'tr':
                    yield child
                else:
                    yield from self.rows(child)


def parse(page_html):
    tree = _Tree()
    tree.feed(page_html)
    tree.close()
    return tree.root


def body(page_html, url):
    """The Markdown blocks of the page's <main>."""
    main = find(parse(page_html), 'main')
    if main is None:
        raise ValueError(f'{url}: the page has no <main>')
    return Writer(url).blocks(main)


def twin(page_html, url, title, description, footer):
    """The Markdown twin of one page: front matter, title, summary, content, then where it came from."""
    title, description = squeeze(title), squeeze(description)
    front = '\n'.join(['---', f'title: {json.dumps(title, ensure_ascii=False)}',
                       f'description: {json.dumps(description, ensure_ascii=False)}', f'canonical: {url}', '---'])
    parts = [f'# {title}', f'> {description}', *body(page_html, url), '---', footer]
    return front + '\n\n' + '\n\n'.join(parts) + '\n'

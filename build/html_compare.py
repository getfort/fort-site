"""Compare two HTML pages as the browser reads them.

Entities are decoded, attributes sorted, whitespace runs collapsed, and
whitespace-only text next to a block-level tag dropped. <pre> content is exact.
"""
import re
from html.parser import HTMLParser

BLOCK = set('html head body header footer main nav aside section div p h1 h2 h3 h4 ul ol li figure '
            'figcaption pre table thead tbody tr td th details summary meta link title script'.split())


class Tokens(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.toks, self.pre = [], 0

    def handle_starttag(self, tag, attrs):
        self.toks.append(('start', tag, tuple(sorted((k, v or '') for k, v in attrs))))
        if tag == 'pre':
            self.pre += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        self.toks.append(('end', tag))
        if tag == 'pre':
            self.pre -= 1

    def handle_data(self, data):
        if self.pre:
            self.toks.append(('pre', data))
        else:
            self.toks.append(('text', re.sub(r'\s+', ' ', data)))


def tokens(source):
    parser = Tokens()
    parser.feed(source)
    raw = parser.toks
    merged = []
    for tok in raw:  # merge adjacent text
        if merged and tok[0] in ('text', 'pre') and merged[-1][0] == tok[0]:
            merged[-1] = (tok[0], merged[-1][1] + tok[1])
        else:
            merged.append(tok)
    out = []
    for i, tok in enumerate(merged):
        if tok[0] == 'text' and not tok[1].strip():
            prev = merged[i - 1] if i else None
            nxt = merged[i + 1] if i + 1 < len(merged) else None
            if (prev is None or prev[1] in BLOCK) or (nxt is None or nxt[1] in BLOCK):
                continue
        out.append(tok)
    return out


def compare(a, b):
    ta, tb = tokens(a), tokens(b)
    for i, (x, y) in enumerate(zip(ta, tb)):
        if x != y:
            return f'first difference at {x!r} / {y!r}, after {ta[max(0, i - 3):i]}'
    if len(ta) != len(tb):
        return f'length {len(ta)} != {len(tb)}; extra: {(ta[len(tb):] or tb[len(ta):])[:3]}'
    return None

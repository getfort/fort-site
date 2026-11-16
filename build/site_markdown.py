"""Render the docs Markdown kept in the Fort repo (docs/site/) as page HTML.

The dialect is deliberately small and strict; anything it does not understand
stops the build instead of publishing a broken page. See docs/MARKDOWN.md.
"""
import html
import re


class MarkdownError(Exception):
    """The Markdown uses syntax this renderer does not support."""


ATTR_TOKEN = re.compile(r'#[\w-]+|\.[\w-]+|[\w-]+="[^"]*"|[\w-]+')
TRAILING_ATTRS = re.compile(r'^(.*?)\s+\{([^{}]*)\}$')
HEADING = re.compile(r'^(#{1,3}) (.+)$')
BULLET = re.compile(r'^- (.*)$')
NUMBERED = re.compile(r'^\d+\. (.*)$')
CONTAINER = re.compile(r'^::: (section|div)(?: \{([^{}]*)\})?$')
INLINE = re.compile(r'''
    (?P<esc>\\[\\`*\[\]{}<&])
  | (?P<code>`[^`]+`)
  | (?P<tag></?[a-zA-Z][^<>]*>)
  | (?P<link>\[(?P<ltext>(?:[^\[\]\\]|\\.)*)\]\((?P<href>[^()\s]*)\)(?:\{(?P<lattrs>[^{}]*)\})?)
  | (?P<strong>\*\*(?P<stext>.+?)\*\*)
  | (?P<em>\*(?P<etext>[^*]+?)\*)
  | (?P<entity>&(?:[a-zA-Z]+|\#[0-9]+|\#x[0-9a-fA-F]+);)
''', re.X)


def text(value):
    """Escape plain text for HTML."""
    return html.escape(value, quote=False)


def attrs(spec, first=()):
    """Turn `#id .class key="value" flag` into an HTML attribute string.

    The id and classes come first, then `first` (for example a link's href),
    then the remaining attributes in the order written.
    """
    ident, classes, rest = None, [], []
    for token in ATTR_TOKEN.findall(spec or ''):
        if token.startswith('#'):
            ident = token[1:]
        elif token.startswith('.'):
            classes.append(token[1:])
        elif '=' in token:
            key, value = token.split('=', 1)
            rest.append((key, value[1:-1]))
        else:
            rest.append((token, None))
    if ' '.join(ATTR_TOKEN.findall(spec or '')) != ' '.join((spec or '').split()):
        raise MarkdownError(f'cannot read attributes {{{spec}}}')
    pairs = ([('id', ident)] if ident else []) + ([('class', ' '.join(classes))] if classes else [])
    pairs += list(first) + rest
    return ''.join(f' {k}' if v is None else f' {k}="{html.escape(v)}"' for k, v in pairs)


def inline(source):
    """Render inline Markdown: code, links, strong, em, raw tags and entities."""
    out, pos = [], 0
    for match in INLINE.finditer(source):
        out.append(text(source[pos:match.start()]))
        pos = match.end()
        if match.group('esc'):
            out.append(text(match.group('esc')[1]))
        elif match.group('code'):
            out.append(f'<code>{text(match.group("code")[1:-1])}</code>')
        elif match.group('tag') or match.group('entity'):
            out.append(match.group('tag') or match.group('entity'))
        elif match.group('link'):
            href = [('href', match.group('href'))]
            out.append(f'<a{attrs(match.group("lattrs"), href)}>{inline(match.group("ltext"))}</a>')
        elif match.group('strong'):
            out.append(f'<strong>{inline(match.group("stext"))}</strong>')
        else:
            out.append(f'<em>{inline(match.group("etext"))}</em>')
    out.append(text(source[pos:]))
    return ''.join(out)


def split_attrs(lines):
    """Take a closing `{...}` (own line or end of the last line) off a block."""
    if re.match(r'^\{[^{}]*\}$', lines[-1]):
        return lines[:-1], lines[-1][1:-1]
    match = TRAILING_ATTRS.match(lines[-1])
    if match:
        return lines[:-1] + [match.group(1)], match.group(2)
    return lines, ''


def code_figure(info, body):
    """A fenced block: ``` caption | second caption {attrs}."""
    match = TRAILING_ATTRS.match(info)
    info, pre_attrs = (match.group(1), match.group(2)) if match else (info, '')
    parts = [p.strip() for p in info.split(' | ')] if info else []
    if len(parts) > 2:
        raise MarkdownError(f'a code caption has at most two parts: {info}')
    caption = ''.join(f'<span>{text(p)}</span>' for p in parts) if len(parts) == 2 else text(info)
    pre = attrs(pre_attrs, [('tabindex', '0')])
    code = f'<pre{pre}><code>{text(chr(10).join(body))}</code></pre>'
    if not info:
        return code
    return f'<figure class="docs-code"><figcaption>{caption}</figcaption>{code}</figure>'


def raw_html(lines):
    """Raw HTML: lines joined with nothing, except inside <pre> where newlines stay."""
    out, in_pre = [], False
    for line in lines:
        if in_pre:
            out.append('\n' + line)
        else:
            out.append(line.lstrip() if '<pre' in line else line.strip())
        if '<pre' in line:
            in_pre = True
        if '</pre>' in line:
            in_pre = False
    return ''.join(out)


def take_block(lines, i):
    """Lines of one block: up to a blank line or a ::: line (blank lines inside <pre> stay)."""
    start, open_pre = i, 0
    while i < len(lines) and (open_pre or (lines[i].strip() and not lines[i].startswith(':::'))):
        if lines[start].startswith('<'):
            open_pre += lines[i].count('<pre') - lines[i].count('</pre>')
        i += 1
    return lines[start:i], i


def render_list(block):
    items = []
    tag = 'ol' if NUMBERED.match(block[0]) else 'ul'
    marker = NUMBERED if tag == 'ol' else BULLET
    block, spec = split_attrs(block)
    for line in block:
        match = marker.match(line)
        if match:
            items.append(match.group(1))
        elif line.startswith('  ') and items:
            items[-1] += ' ' + line.strip()
        else:
            raise MarkdownError(f'unexpected line in a list: {line}')
    body = ''.join(f'<li>{inline(item)}</li>' for item in items)
    return f'<{tag}{attrs(spec)}>{body}</{tag}>'


def render(source):
    """Render a page body; returns HTML with one top-level block per line."""
    lines = source.split('\n')
    stack, out, i = [], [[]], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        container = CONTAINER.match(line)
        if container:
            stack.append(container.group(1))
            out.append([f'<{container.group(1)}{attrs(container.group(2))}>'])
            i += 1
        elif line == ':::':
            if not stack:
                raise MarkdownError(f'line {i + 1}: ::: closes nothing')
            inner = out.pop()
            out[-1].append(''.join(inner) + f'</{stack.pop()}>')
            i += 1
        elif line.startswith(':::'):
            raise MarkdownError(f'line {i + 1}: expected "::: section {{...}}", "::: div {{...}}" or ":::"')
        elif line.startswith('```'):
            end = next((j for j in range(i + 1, len(lines)) if lines[j] == '```'), None)
            if end is None:
                raise MarkdownError(f'line {i + 1}: code block is never closed')
            out[-1].append(code_figure(line[3:].strip(), lines[i + 1:end]))
            i = end + 1
        else:
            block, i = take_block(lines, i)
            out[-1].append(render_block(block))
    if stack:
        raise MarkdownError(f'::: {stack[-1]} is never closed')
    return '\n'.join(out[0])


def render_block(block):
    first = block[0]
    if first.startswith('<'):
        return raw_html(block)
    if BULLET.match(first) or NUMBERED.match(first):
        return render_list(block)
    block, spec = split_attrs(block)
    heading = HEADING.match(block[0])
    if heading:
        if len(block) > 1:
            raise MarkdownError(f'a heading is one line: {block[0]}')
        level = len(heading.group(1))
        return f'<h{level}{attrs(spec)}>{inline(heading.group(2))}</h{level}>'
    if first.startswith(('#', '>', '|', '* ', '+ ')):
        raise MarkdownError(f'unsupported Markdown: {first}')
    return f'<p{attrs(spec)}>{inline(" ".join(line.strip() for line in block))}</p>'


def front_matter(source):
    """Split `---` front matter (key: value, and `key:` followed by `- item` lines)."""
    lines = source.split('\n')
    if lines[0] != '---':
        raise MarkdownError('a page starts with --- front matter')
    end = lines.index('---', 1)
    meta, key = {}, None
    for line in lines[1:end]:
        if line.startswith('- ') and key:
            meta[key].append(line[2:])
        elif ': ' in line:
            key, value = line.split(': ', 1)
            meta[key] = value
        elif line.endswith(':'):
            key = line[:-1]
            meta[key] = []
        elif line.strip():
            raise MarkdownError(f'cannot read front matter line: {line}')
    return meta, '\n'.join(lines[end + 1:])


LINK_ITEM = re.compile(r'^\[(.+)\]\(([^()\s]*)\)$')


def link_item(item):
    match = LINK_ITEM.match(item)
    if not match:
        raise MarkdownError(f'expected a [label](link) item: {item}')
    return match.group(1), match.group(2)

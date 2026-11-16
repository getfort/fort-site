#!/usr/bin/env python3
"""Build getfort.io into dist/ from this repository plus one Fort commit.

    python3 build/build.py --fort ../fort --ref origin/main

The docs pages are rendered from docs/site/ and the Terraform download is packed
from deploy/terraform/customer/, both read from that exact Fort commit. Nothing
here keeps its own copy of either.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from docs_pages import page
from fort_source import FortCommit, FortSourceError
from package_terraform import PackageError, write as write_package
from site_markdown import MarkdownError

SITE = Path(__file__).resolve().parents[1]
DOCS = 'docs/site/'
# Site files published as they are; everything else in this repository stays out.
STATIC = ['index.html', '404.html', 'styles.css', 'script.js', 'warden.css', 'warden.js',
          'arrivals.js', 'additions.css', 'docs/docs.css', 'docs/docs.js']
STATIC_DIRS = ['assets']
# Files whose links get a content hash (?v=...) so browsers fetch new versions.
STAMPED = ['styles.css', 'script.js', 'warden.css', 'warden.js', 'arrivals.js', 'additions.css',
           'docs/docs.css', 'docs/docs.js', 'assets/fort.svg', 'assets/favicon.svg']


class BuildError(Exception):
    pass


def docs_pages(fort):
    """Map of output path (under dist/docs/) to Markdown source, plus the sidebar."""
    pages, sidebar = {}, None
    for mode, path in fort.files(DOCS):
        rel = path[len(DOCS):]
        if mode != '100644':
            raise BuildError(f'{path}: mode {mode} is not a regular file')
        if rel == '_sidebar.md':
            sidebar = fort.read(path).decode()
        elif rel == 'README.md':
            continue
        elif rel == 'index.md' or rel.endswith('/index.md'):
            pages[rel[:-len('index.md')]] = fort.read(path).decode()
        else:
            raise BuildError(f'{path}: only <page>/index.md, _sidebar.md and README.md are supported')
    if sidebar is None or '' not in pages:
        raise BuildError(f'{DOCS} needs _sidebar.md and index.md')
    return pages, sidebar


def stamp(dist):
    pages = sorted(dist.rglob('*.html'))
    for asset in STAMPED:
        version = hashlib.md5((dist / asset).read_bytes()).hexdigest()[:10]
        name = asset.rsplit('/', 1)[-1]
        for html_file in pages:
            text = html_file.read_text()
            html_file.write_text(text.replace(f'{name}"', f'{name}?v={version}"'))


def build(fort_repo, ref, out):
    index = (SITE / 'index.html').read_text()
    if 'href="EARLY_ACCESS_URL"' in index:
        raise BuildError('index.html still has the EARLY_ACCESS_URL placeholder')
    fort = FortCommit(fort_repo, ref)
    if out.exists():
        shutil.rmtree(out)
    for name in STATIC:
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SITE / name, out / name)
    for name in STATIC_DIRS:
        shutil.copytree(SITE / name, out / name)
    pages, sidebar = docs_pages(fort)
    for path, source in sorted(pages.items()):
        try:
            rendered = page(source, path, sidebar)
        except MarkdownError as err:
            raise BuildError(f'{DOCS}{path}index.md: {err}') from err
        target = out / 'docs' / path / 'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered)
    checksum, entries = write_package(fort, out / 'downloads')
    stamp(out)
    # /build.json names the commits this build came from. Fort's site-dispatch reads
    # fort_sha to tell whether main has docs or Terraform changes the live site lacks.
    record = {'fort_sha': fort.sha, 'fort_site_sha': site_sha()}
    (out / 'build.json').write_text(json.dumps(record, sort_keys=True) + '\n')
    # Workers Static Assets reads _headers and does not publish it.
    (out / '_headers').write_text('/build.json\n  Cache-Control: no-cache\n')
    return fort.sha, sorted(pages), checksum, entries


def site_sha():
    try:
        sha = subprocess.check_output(['git', '-C', str(SITE), 'rev-parse', 'HEAD'], text=True).strip()
    except (OSError, subprocess.CalledProcessError) as err:
        raise BuildError(f'cannot read this repository\'s commit: {err}') from err
    return sha


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--fort', required=True, help='path to a Fort git checkout')
    parser.add_argument('--ref', default='HEAD', help='Fort commit to build from (default HEAD)')
    parser.add_argument('--out', default=str(SITE / 'dist'), help='output directory (default dist/)')
    args = parser.parse_args()
    try:
        sha, pages, checksum, entries = build(args.fort, args.ref, Path(args.out))
    except (BuildError, FortSourceError, PackageError) as err:
        sys.exit(f'build failed: {err}')
    print(f'Fort commit: {sha}')
    print(f'Docs pages ({len(pages)}): ' + ', '.join('/docs/' + p for p in pages))
    print(f'Terraform download ({len(entries)} files): {checksum}')
    for name in sorted(entries):
        print(f'  {name}')


if __name__ == '__main__':
    main()

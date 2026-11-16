"""Read Fort's files for one exact commit: git blobs, or a fresh checkout without .git."""
import re
import subprocess
from pathlib import Path


class FortSourceError(Exception):
    """The Fort checkout or commit cannot be read as expected."""


class FortCommit:
    def __init__(self, repo, ref):
        self.repo = str(repo)
        self.sha = self._git('rev-parse', '--verify', f'{ref}^{{commit}}').decode().strip()

    def _git(self, *args):
        try:
            return subprocess.check_output(['git', '-C', self.repo, *args], stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as err:
            raise FortSourceError(f'git {" ".join(args)}: {err.stderr.decode().strip()}') from err

    def files(self, prefix):
        """Every tracked path under `prefix` with its mode, e.g. ('100644', 'docs/site/index.md')."""
        out = self._git('ls-tree', '-r', '-z', '--full-tree', self.sha, '--', prefix)
        entries = []
        for record in filter(None, out.split(b'\0')):
            meta, path = record.decode().split('\t', 1)
            mode, kind, _ = meta.split(' ')
            if kind != 'blob':
                raise FortSourceError(f'{path} is a {kind}, not a file')
            entries.append((mode, path))
        if not entries:
            raise FortSourceError(f'nothing tracked under {prefix} at {self.sha}')
        return entries

    def read(self, path):
        return self._git('show', f'{self.sha}:{path}')


class FortTree:
    """The files of a fresh checkout whose .git is not available (Workers Builds).

    Only for a clean clone made by the build service: every file on disk under a
    prefix counts, with git-style modes, and `sha` is the commit the service names.
    """

    def __init__(self, root, sha):
        self.root = Path(root).resolve()
        if not re.fullmatch(r'[0-9a-f]{40}', sha or ''):
            raise FortSourceError(f'the checkout commit must be a full 40-hex sha, got {sha!r}')
        self.sha = sha

    def files(self, prefix):
        base = self.root / prefix
        entries = []
        for path in sorted(base.rglob('*')) if base.is_dir() else []:
            rel = path.relative_to(self.root).as_posix()
            if path.is_symlink():
                entries.append(('120000', rel))
            elif path.is_file():
                entries.append(('100755' if path.stat().st_mode & 0o111 else '100644', rel))
        if not entries:
            raise FortSourceError(f'nothing under {prefix} in {self.root}')
        return entries

    def read(self, path):
        target = self.root / path
        if target.is_symlink() or not target.is_file():
            raise FortSourceError(f'{path} is not a regular file')
        return target.read_bytes()

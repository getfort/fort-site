"""Read files from one exact Fort commit: git blobs only, never working files."""
import subprocess


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

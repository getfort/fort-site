"""Pack Fort's customer Terraform templates into the public download.

Every tracked file under deploy/terraform/customer/ at the Fort commit goes in,
except Fort's own tests and .gitignore. The build stops on executables, symlinks,
files over 1 MB, and any tracked tfvars, state, .terraform/ or key file. The ZIP is
deterministic: the same commit always gives the same bytes and checksum.
"""
import hashlib
import zipfile
from pathlib import Path

BASE = 'deploy/terraform/customer/'
NAME = 'fort-terraform-customer'
HERE = Path(__file__).parent
MAX_BYTES = 1024 * 1024
# Files the packer adds itself; Fort may not track a file of the same name at the top.
ADDED = {'license', 'start_here.txt', 'source_manifest.sha256'}


class PackageError(Exception):
    """The customer templates cannot be packed safely."""


def forbidden(rel):
    """Why a tracked path must never be near the public download, or None.

    Applies to every tracked file under BASE, shipped or not: real variables,
    Terraform state, provider caches and keys stop the build.
    """
    if '\\' in rel or rel.startswith('/') or '..' in rel.split('/') or '' in rel.split('/'):
        return 'an unsafe path'
    parts = rel.lower().split('/')
    name = parts[-1]
    if len(parts) == 1 and name in ADDED:
        return f'a file named like the packaging addition {name}'
    if name.endswith('.tfvars') or ('.tfvars.' in name and not name.endswith('.tfvars.example')):
        return 'a tfvars file (only *.tfvars.example may be tracked)'
    if '.tfstate' in name:
        return 'Terraform state'
    if '.terraform' in parts[:-1]:
        return 'a .terraform/ directory'
    if name.endswith(('.pem', '.key')):
        return 'a key or certificate file'
    return None


def shipped(rel):
    """Whether a path (relative to BASE) belongs in the customer download."""
    parts = rel.split('/')
    return 'tests' not in parts[:-1] and parts[-1] != '.gitignore'


def contents(fort):
    """The archive entries (name -> bytes) for one Fort commit."""
    entries = {}
    for mode, path in fort.files(BASE):
        rel = path[len(BASE):]
        reason = forbidden(rel)
        if reason:
            raise PackageError(f'refusing {path}: {reason} is tracked')
        if not shipped(rel):
            continue
        if mode != '100644':
            raise PackageError(f'refusing {path}: mode {mode}, only regular non-executable files ship')
        data = fort.read(path)
        if len(data) > MAX_BYTES:
            raise PackageError(f'refusing {path}: {len(data)} bytes, over the 1 MB limit')
        entries[rel] = data
    if 'README.md' not in entries:
        raise PackageError(f'{BASE}README.md is missing at {fort.sha}')
    manifest = ''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name, data in sorted(entries.items()))
    entries['SOURCE_MANIFEST.sha256'] = manifest.encode()
    entries['LICENSE'] = (HERE / 'APACHE-2.0.txt').read_bytes()
    entries['START_HERE.txt'] = (HERE / 'START_HERE.txt').read_text().format(commit=fort.sha).encode()
    return entries


def write(fort, out_dir):
    """Write the ZIP and its .sha256 into out_dir; returns (checksum, entries)."""
    entries = contents(fort)
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f'{NAME}.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED) as z:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(f'{NAME}/{name}', (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{checksum}  {archive.name}\n')
    return checksum, entries

#!/usr/bin/env python3
"""Package only reviewed, tracked customer-module blobs; never read working files."""
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

COMMIT = '7836c5389ff674a924b8092ae52b83cbf1751864'
BASE = 'deploy/terraform/customer/'
FILES = [BASE + 'README.md']
for cloud in ('aws', 'gcp'):
    FILES += [BASE + cloud + '/' + name for name in (
        '.terraform.lock.hcl', 'README.md', 'fort.tf', 'main.tf', 'outputs.tf',
        'terraform.tfvars.example', 'variables.tf', 'versions.tf')]
FILES += [BASE + 'shared/' + name for name in (
    'bootstrap.py', 'bootstrap.sh.tftpl', 'main.tf', 'outputs.tf', 'variables.tf')]
repo = Path(sys.argv[1]) if len(sys.argv) == 2 else None
if repo is None:
    sys.exit('Usage: package-terraform.py /path/to/fort')

def git(*args):
    return subprocess.check_output(['git', '-C', str(repo), *args])

entries = {}
for source in FILES:
    tree = git('ls-tree', COMMIT, '--', source).decode().strip()
    if not tree.startswith('100644 blob ') or tree.split('\t')[-1] != source:
        sys.exit(f'Refusing missing, non-regular or unreviewed file: {source}')
    target = source.removeprefix(BASE)
    entries[target] = git('show', f'{COMMIT}:{source}')
source_manifest = ''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name, data in sorted(entries.items()))
entries['SOURCE_MANIFEST.sha256'] = source_manifest.encode()
entries['LICENSE'] = Path(__file__).with_name('APACHE-2.0.txt').read_bytes()
entries['START_HERE.txt'] = f'''Fort early-access Terraform templates
Source commit: {COMMIT}

Keep aws/, gcp/ and shared/ together. Choose your cloud:
https://getfort.io/docs/aws/
https://getfort.io/docs/gcp/

Inside aws/ or gcp/, copy terraform.tfvars.example to terraform.tfvars.
Replace every placeholder. Read README.md for prerequisites and operations.
The source README uses deploy/terraform/customer paths: in this download,
that directory is the extracted fort-terraform-customer directory.
References to the Fort source checkout, tests and qualified binaries require
separately supplied source/builds; those are not bundled here.

No binaries or credentials are included. Company OIDC sign-in is required.
Do not place private keys, client secrets or live state in shared files.
Source files are included unchanged; SOURCE_MANIFEST.sha256 lists those blobs only.
START_HERE and SOURCE_MANIFEST are packaging additions. LICENSE is supplemental
standard Apache-2.0 text from https://www.apache.org/licenses/LICENSE-2.0.txt;
the source commit has no tracked root LICENSE. Fort declares Apache-2.0 terms.
'''.encode()
out = Path(__file__).resolve().parents[1] / 'downloads'
out.mkdir(exist_ok=True)
archive = out / 'fort-terraform-customer.zip'
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED) as z:
    for name, data in sorted(entries.items()):
        info = zipfile.ZipInfo('fort-terraform-customer/' + name, (2026, 1, 1, 0, 0, 0))
        info.create_system = 3
        info.external_attr = 0o100644 << 16
        z.writestr(info, data)
checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256').write_text(f'{checksum}  {archive.name}\n')
print(f'{checksum}  {archive.name} ({len(entries)} files)')

"""Tests for the docs renderer and the Terraform packer."""
import io
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docs_pages import page  # noqa: E402
from html_compare import compare  # noqa: E402
from package_terraform import PackageError, contents, shipped, write  # noqa: E402
from site_markdown import MarkdownError, inline, render  # noqa: E402

SIDEBAR = '''---
summary: Documentation navigation
home: Documentation home
note_label: Early access
note: Ask for a build.
---
## Deploy Fort
- [Choose](deploy/)
- [GCP](gcp/)
## Operations
- [Agents](operations/#agents)
- [Evidence](operations/#evidence)
'''


class Markdown(unittest.TestCase):
    def test_blocks(self):
        source = ('::: section {#prepare .doc-intro}\n\nEyebrow {.eyebrow}\n\n# Deploy on<br>*GCP.*\n\n'
                  '- Terraform < 2.0 & `a<b`\n- [Ref](reference/#x){.text-link}\n\n'
                  '``` Inside gcp | bash\nterraform init\n```\n\n<div class="x">\n<span>a</span>\n</div>\n\n:::')
        self.assertEqual(render(source), (
            '<section id="prepare" class="doc-intro"><p class="eyebrow">Eyebrow</p>'
            '<h1>Deploy on<br><em>GCP.</em></h1>'
            '<ul><li>Terraform &lt; 2.0 &amp; <code>a&lt;b</code></li>'
            '<li><a class="text-link" href="reference/#x">Ref</a></li></ul>'
            '<figure class="docs-code"><figcaption><span>Inside gcp</span><span>bash</span></figcaption>'
            '<pre tabindex="0"><code>terraform init</code></pre></figure>'
            '<div class="x"><span>a</span></div></section>'))

    def test_link_attributes_stay_on_the_link(self):
        self.assertEqual(render('[Get it](a.zip){.button download}'),
                         '<p><a class="button" href="a.zip" download>Get it</a></p>')

    def test_raw_pre_keeps_blank_lines(self):
        self.assertEqual(render('<pre><code>a\n\nb</code></pre>'), '<pre><code>a\n\nb</code></pre>')

    def test_entities_and_escapes(self):
        self.assertEqual(inline(r'Settings &rsaquo; \*not em\* it’s'), 'Settings &rsaquo; *not em* it’s')

    def test_unknown_syntax_fails(self):
        for bad in ('> quote', '| a | b |', '::: aside', '::: section\n\ntext', ':::', '```\ncode'):
            with self.assertRaises(MarkdownError, msg=bad):
                render(bad)


class Pages(unittest.TestCase):
    def render(self, path, body='Text'):
        return page(f'---\ntitle: T & U\ndescription: D\nskip: Skip\n---\n{body}\n', path, SIDEBAR)

    def test_relative_paths_and_current_page(self):
        out = self.render('gcp/reference/')
        self.assertIn('<link rel="canonical" href="https://getfort.io/docs/gcp/reference/">', out)
        self.assertIn('<link rel="stylesheet" href="../../../styles.css">', out)
        self.assertIn('<a href="../../gcp/" aria-current="page">GCP</a>', out)
        self.assertIn('<title>T &amp; U</title>', out)

    def test_section_only_page_marks_its_first_link(self):
        out = self.render('operations/')
        self.assertIn('<a href="../operations/#agents" aria-current="page">', out)
        self.assertNotIn('#evidence" aria-current', out)

    def test_docs_home_has_no_current_nav_link(self):
        out = self.render('')
        self.assertNotIn('" aria-current="page">Choose', out)
        self.assertIn('<a href="./" aria-current="page">Docs</a>', out)

    def test_unknown_front_matter_fails(self):
        with self.assertRaises(MarkdownError):
            page('---\ntitle: T\ndescription: D\nskip: S\ncolour: red\n---\n', '', SIDEBAR)


class Compare(unittest.TestCase):
    def test_same_page_despite_bytes(self):
        self.assertIsNone(compare('<p>A &amp; B</p>\n<p class="x" id="y">C</p>',
                                  '<p>A & B</p><p id="y" class="x">C</p>'))

    def test_text_and_inline_spaces_count(self):
        self.assertIsNotNone(compare('<p>A B</p>', '<p>A C</p>'))
        self.assertIsNotNone(compare('<p><b>a</b> <i>b</i></p>', '<p><b>a</b><i>b</i></p>'))
        self.assertIsNotNone(compare('<pre>a\n b</pre>', '<pre>a\nb</pre>'))


class FakeFort:
    sha = 'c0ffee' * 6 + 'c0ff'

    def __init__(self, files):
        self._files = files

    def files(self, prefix):
        return [(mode, path) for path, (mode, _) in sorted(self._files.items()) if path.startswith(prefix)]

    def read(self, path):
        return self._files[path][1]


BASE = 'deploy/terraform/customer/'


class Package(unittest.TestCase):
    def fort(self, **extra):
        files = {BASE + 'README.md': ('100644', b'readme'), BASE + 'gcp/main.tf': ('100644', b'tf'),
                 BASE + 'gcp/tests/launch.tftest.hcl': ('100644', b'test'),
                 BASE + 'tests/check.sh': ('100755', b'#!'), BASE + '.gitignore': ('100644', b'*.tfstate')}
        files.update(extra)
        return FakeFort(files)

    def test_ships_everything_but_tests_and_gitignore(self):
        self.assertFalse(shipped('aws/tests/launch.tftest.hcl'))
        self.assertFalse(shipped('.gitignore'))
        self.assertTrue(shipped('shared/bootstrap.py'))
        names = sorted(contents(self.fort()))
        self.assertEqual(names, ['LICENSE', 'README.md', 'SOURCE_MANIFEST.sha256', 'START_HERE.txt', 'gcp/main.tf'])

    def test_records_the_commit_and_manifest(self):
        entries = contents(self.fort())
        self.assertIn(f'Source commit: {FakeFort.sha}', entries['START_HERE.txt'].decode())
        self.assertIn('  gcp/main.tf\n', entries['SOURCE_MANIFEST.sha256'].decode())
        self.assertNotIn('LICENSE', entries['SOURCE_MANIFEST.sha256'].decode())

    def test_refuses_executables_and_symlinks(self):
        for mode in ('100755', '120000'):
            with self.assertRaises(PackageError):
                contents(self.fort(**{BASE + 'aws/run.sh': (mode, b'x')}))

    def test_refuses_secrets_state_keys_and_large_files(self):
        for path in ('gcp/terraform.tfvars', 'gcp/prod.tfvars.json', 'terraform.tfstate',
                     'gcp/terraform.tfstate.backup', 'gcp/.terraform/providers/p', 'shared/tls.key',
                     'shared/ca.pem', 'tests/fixtures/client.key'):
            with self.assertRaises(PackageError, msg=path):
                contents(self.fort(**{BASE + path: ('100644', b'x')}))
        with self.assertRaises(PackageError):
            contents(self.fort(**{BASE + 'gcp/big.tf': ('100644', b'x' * (1024 * 1024 + 1))}))

    def test_keeps_examples_and_lock_files(self):
        names = contents(self.fort(**{BASE + 'gcp/terraform.tfvars.example': ('100644', b'x'),
                                      BASE + 'gcp/.terraform.lock.hcl': ('100644', b'x')}))
        self.assertIn('gcp/terraform.tfvars.example', names)
        self.assertIn('gcp/.terraform.lock.hcl', names)

    def test_deterministic(self):
        import tempfile
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            one, _ = write(self.fort(), Path(a))
            two, _ = write(self.fort(), Path(b))
            self.assertEqual(one, two)
            names = zipfile.ZipFile(io.BytesIO((Path(a) / 'fort-terraform-customer.zip').read_bytes())).namelist()
            self.assertTrue(all(n.startswith('fort-terraform-customer/') for n in names))


if __name__ == '__main__':
    unittest.main()

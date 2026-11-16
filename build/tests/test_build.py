"""Tests for the docs renderer and the Terraform packer."""
import io
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docs_pages import page  # noqa: E402
from html_compare import compare  # noqa: E402
from live_guard import decide  # noqa: E402
from package_terraform import PackageError, contents, shipped, write  # noqa: E402
from site_markdown import MarkdownError, check_safe, inline, render  # noqa: E402

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


class Safety(unittest.TestCase):
    def test_refuses_active_content(self):
        for bad in ('<script>x</script>', '<iframe src="https://x"></iframe>', '<form></form>',
                    '<a href="javascript:alert(1)">x</a>', '<a href="java&#x09;script:x">x</a>',
                    '<a href=" JavaScript:x">x</a>', '<img src="data:image/png;base64,AA">',
                    '<span onclick="x">x</span>', '<base href="https://evil">', '<style>x</style>',
                    '<noscript><p title="</noscript><img src=x onerror=alert(1)>"></p></noscript>',
                    '<!--> <img src=x onerror=alert(1)> -->', '<?x ?>', '<p style="x">x</p>',
                    '<plaintext>', '</x <img src=x onerror=alert(1)>>', '<span title="t">x</span>',
                    '<a href="https://x" target="_top">x</a>', '<span class="a'):
            with self.assertRaises(MarkdownError, msg=bad):
                check_safe(render(bad))
        for bad in ('[x](javascript:alert)', '[x](#a){onclick="x"}', 'text <svg onload=x>'):
            with self.assertRaises(MarkdownError, msg=bad):
                check_safe(render(bad))

    def test_allows_normal_links(self):
        check_safe(render('[a](https://x.io/) [b](../gcp/#x) [c](#y) [d](reference/){.button download}'))

    def test_page_runs_the_check(self):
        with self.assertRaises(MarkdownError):
            page('---\ntitle: T\ndescription: D\nskip: S\n---\n<script>x</script>\n', '', SIDEBAR)

    def test_page_text_is_not_a_placeholder(self):
        out = page('---\ntitle: T\ndescription: D\nskip: S\n---\nLiteral {{sidebar}}\n', '', SIDEBAR)
        self.assertIn('Literal {{sidebar}}', out)


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


def deployment(version, when, message=None):
    annotations = {'workers/message': message} if message is not None else {}
    return {'versions': [{'version_id': version}], 'created_on': when, 'annotations': annotations}


class LiveGuard(unittest.TestCase):
    def test_deploys_over_a_fort_site_deploy(self):
        listed = [deployment('old', '1', None), deployment('new', '2', 'fort-site abc + fort def')]
        self.assertTrue(decide(listed, '')[0])

    def test_stops_on_a_manual_deploy_or_rollback(self):
        listed = [deployment('a', '1', 'fort-site abc + fort def'), deployment('b', '2', None)]
        ok, why = decide(listed, '')
        self.assertFalse(ok)
        self.assertIn('LIVE_VERSION_REVIEWED=b', why)
        self.assertFalse(decide(listed, 'a')[0])

    def test_deploys_once_that_live_version_was_reviewed(self):
        self.assertTrue(decide([deployment('b', '2', 'manual')], 'b')[0])

    def test_stops_when_nothing_is_listed(self):
        self.assertFalse(decide([], 'b')[0])


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

    def test_refuses_any_case_unsafe_names_and_clashes(self):
        for path in ('gcp/PROD.TFVARS', 'shared/TLS.KEY', 'gcp/Terraform.TFSTATE', 'gcp/../x.tf',
                     'gcp\\x.tf', 'LICENSE', 'START_HERE.txt', 'source_manifest.sha256'):
            with self.assertRaises(PackageError, msg=path):
                contents(self.fort(**{BASE + path: ('100644', b'x')}))
        self.assertIn('gcp/LICENSE', contents(self.fort(**{BASE + 'gcp/LICENSE': ('100644', b'x')})))

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

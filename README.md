# getfort.io

The Fort website: its look and its build. Plain static HTML, CSS and JavaScript,
hosted on Cloudflare Workers Static Assets (Worker `fort-web`) at https://getfort.io.

**This repo has no docs text and no Terraform download of its own.** Both come from
the Fort repo (`spawningpool/fort`) at the exact commit being built:

- the docs pages at `/docs/` are rendered from Markdown in Fort's `docs/site/`;
- `/downloads/fort-terraform-customer.zip` (and its `.sha256`) is packed from Fort's
  `deploy/terraform/customer/`.

The live site is always Fort `main` built with the fort-site commit that Fort pins in
`docs/site/_build/SITE_VERSION`. Cloudflare Workers Builds, connected to the Fort repo,
builds and deploys on every change to `main` (see `docs/DEPLOY.md`). This repo deploys
nothing itself; a change here reaches the live site only through a reviewed Fort PR that
moves the pin.

## What is here

- `index.html`, `404.html`: the landing page and the not-found page.
- `styles.css`, `script.js`, `warden.css`, `warden.js`, `arrivals.js`, `additions.css`:
  landing-page styles and behaviour (theme, navigation, the Warden example, the hero arrival).
- `docs/docs.css`, `docs/docs.js`: docs layout, navigation and contents.
- `assets/`: logo and favicon.
- `build/`: the build.
  - `build.py`: assembles `dist/`, the only directory that is published, including
    `/build.json` with the Fort and fort-site commits it was built from.
  - `docs-page.html`: the shared docs page frame (header, sidebar slot, footer).
  - `site_markdown.py`, `docs_pages.py`: render Fort's docs Markdown into that frame.
    The Markdown syntax is described in `docs/MARKDOWN.md`. The build refuses scripts,
    frames, forms, event attributes and non-http(s) links in docs pages.
  - `package_terraform.py`: packs the Terraform ZIP. Every tracked file under
    `deploy/terraform/customer/` goes in, except Fort's own `tests/` and `.gitignore`.
    The build stops on executables, symlinks, files over 1 MB, and any tracked tfvars,
    Terraform state, `.terraform/` or key file. It adds `SOURCE_MANIFEST.sha256`
    (hashes of the packed source files), `START_HERE.txt` (records the Fort commit) and
    `LICENSE` (standard Apache-2.0 text, `build/APACHE-2.0.txt`). The ZIP is
    deterministic: one commit always gives the same bytes.
  - `verify_live.py`: compares `dist/` with the live site (`--report` lists the
    differences; without it, it checks that the live site serves `dist/` exactly).
  - `tests/`: unit tests (`python3 -m unittest discover -s build/tests`).
- `.github/workflows/site.yml`: tests on every PR and push. It deploys nothing.
- `package.json` and `package-lock.json` pin wrangler, the deploy tool that Fort's
  `docs/site/_build/deploy.sh` runs; the site itself has no npm dependencies.
- `PRODUCT.md`: who the site is for and what it says.

Early-access buttons lead to the Fort Typeform (`twrlRIKM`).
The Warden panel is an illustrative example, not a connected environment.

## Build and preview locally

From a Fort checkout, with Python 3.10+ (no packages):

```bash
FORT_SITE_REPO=~/Work/fort-site bash docs/site/_build/build.sh
python3 -m http.server 8003 --directory docs/site/_build/dist
```

`FORT_SITE_REPO` points the build at a local fort-site checkout instead of GitHub, to
preview a fort-site change before it is pinned; it is refused inside Workers Builds. The
build reads committed Fort files only, so commit docs edits on a branch first. Or run
this repo's build directly: `python3 build/build.py --fort ~/Work/fort --ref <branch>`.

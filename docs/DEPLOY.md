# Deploying getfort.io

The site is hosted on **Cloudflare Workers Static Assets**.

| | |
|---|---|
| Worker name | `fort-web` |
| Live URLs | https://getfort.io, https://www.getfort.io |
| workers.dev URL | off: with custom domains in `routes`, Wrangler disables `workers.dev` |
| Cloudflare account | `7be48c17ff1b7cfb0a4b65cae4cb8ad3` |
| Config | [`wrangler.jsonc`](../wrangler.jsonc) |

It is a Worker, not a Pages project: `wrangler pages deploy` is the wrong command.

## How it deploys

Only GitHub Actions deploys (`.github/workflows/site.yml`), and every deploy is
**this repo's `main` plus Fort's `main`**:

- a push to this repo's `main` builds and deploys;
- a push to Fort's `main` that changes `docs/site/**` or `deploy/terraform/customer/**`
  runs Fort's `site-dispatch` workflow, which starts this workflow with the Fort commit.
  This workflow still builds from Fort's current `main`, and fails if that does not
  contain the commit that asked, so an older commit can never replace a newer one;
- a pull request here builds and checks, and does not deploy.

Runs queue one at a time. Each deploy's message names both commits, so
`npx wrangler deployments list --name fort-web` shows what is live.

Every build lists its differences from the live site in the run summary ("Compare with
live"). The deploy job then checks who deployed the live version (`build/live_guard.py`):
if it was not this workflow (a manual deploy, a rollback, or the first deploy after the
move from `web-pages`), it stops. Read the comparison, make sure nothing live is missing
from git, and run the workflow on `main` with `live_version_reviewed` set to the version
id the job printed.

### Secrets

Set by the owner in this repo's settings (Settings → Secrets and variables → Actions):

| Secret | What it is |
|---|---|
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token from the "Edit Cloudflare Workers" template, limited to the account above and the `getfort.io` zone. |
| `FORT_READ_TOKEN` | GitHub fine-grained token, resource owner `spawningpool`, repository `spawningpool/fort` only, permission **Contents: Read-only**. |

Only the deploy job sees `CLOUDFLARE_API_TOKEN`. It is also the deploy switch: without
it, runs on `main` build and check, and deploy nothing.

Fort's repo holds `FORT_SITE_DISPATCH_TOKEN`: a fine-grained token for
`spawningpool/fort-site` only, permission **Actions: Read and write**, with an expiry.

## Domains

`wrangler.jsonc` attaches `getfort.io` and `www.getfort.io` as custom domains on the
`getfort.io` zone. Wrangler creates the DNS records and certificates on deploy; it fails if
either hostname already has an A, AAAA or CNAME record.

## What is published

`build/build.py` assembles `dist/`, the only directory that gets published: the landing
page, `404.html`, the CSS/JavaScript, `assets/`, the docs pages rendered from Fort's
`docs/site/`, and the Terraform ZIP and checksum packed from Fort's
`deploy/terraform/customer/`. This file, `docs/MARKDOWN.md` and `PRODUCT.md` stay out.
The build adds content hashes to every CSS/JavaScript file, the logo and the favicon.
Unknown paths serve `404.html`.

When adding a landing-page file, add it to `STATIC` in `build/build.py`. A new docs page
is a new `docs/site/<page>/index.md` in Fort; it needs no change here.

## Verify after deployment

The workflow checks every docs page and the download after each deploy. By hand:

- Open https://getfort.io and https://www.getfort.io.
- Check the logo, CSS and JavaScript load without browser errors.
- Check `/docs/` and each guide, their cross-links and section navigation, desktop and
  mobile navigation, the Warden example and the early-access link.
- Visit an unknown path and confirm an HTTP 404 with the Fort not-found page.
- Confirm `/downloads/fort-terraform-customer.zip` matches its `.sha256` and that its
  `START_HERE.txt` names the current Fort `main` commit.

## Roll back

A rollback changes the live Worker, not Git, and the next push to either `main` will
deploy again. Prefer fixing forward on `main`. In an emergency:

```bash
npx wrangler deployments list --name fort-web
```

```bash
npx wrangler rollback --name fort-web
```

Then fix `main` before anything else merges.

## Copy

The page describes the product in the Fort repo (`docs/SPEC.md`). Fort is pre-launch
and its repo is private until launch: don't claim it is generally available or that the
code is public yet, and keep every control the page names in line with SPEC §3 (v0
controls only; budgets and spend limits are never the pitch).

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
live"). The deploy job then checks who deployed the live version (`build/live_guard.py`).
If it was not this workflow (a manual deploy, a rollback, or the first deploy after the
move from `web-pages`), it stops. An admin then reads the comparison, makes sure nothing
live is missing from git, sets the version id the job printed as the `production`
environment variable `LIVE_VERSION_REVIEWED`, and reruns the workflow. Only admins can set
environment variables; the dispatch token cannot.

Wrangler comes from `package-lock.json` (`npm ci --ignore-scripts`), installed before the
Cloudflare token is in any step's environment.

## Owner setup

Done once by the owner in GitHub and Cloudflare. No agent creates, sees or handles a token.

1. **Branch protection on `main`** (Settings → Branches): require a pull request and the
   `site / build` check, and block force pushes and deletion.
2. **`production` environment** (Settings → Environments → New environment):
   - Deployment branches and tags: **Selected branches**, `main` only.
   - Environment secret `CLOUDFLARE_API_TOKEN`: a Cloudflare custom token with
     Account → **Workers Scripts: Edit** (account `7be48c17ff1b7cfb0a4b65cae4cb8ad3`) and
     Zone → **Workers Routes: Edit** and **DNS: Edit**, for the zone `getfort.io` only.
     Adding it turns deploys on: without it, runs on `main` build, check and deploy nothing.
   - Optional: **Required reviewers** set to yourself. Every deploy then waits for your
     click, including docs changes from Fort `main`.
   - For the first deploy only: environment variable `LIVE_VERSION_REVIEWED`, set to the
     version id the deploy job printed, once the comparison has been checked.
3. **Repository secret `FORT_READ_TOKEN`** (Settings → Secrets and variables → Actions): a
   GitHub fine-grained token, resource owner `spawningpool`, repository `spawningpool/fort`
   only, **Contents: Read-only**, with an expiry.
4. **In the Fort repo, repository secret `FORT_SITE_DISPATCH_TOKEN`:** a fine-grained token,
   repository `spawningpool/fort-site` only, **Actions: Read and write**, with an expiry.

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

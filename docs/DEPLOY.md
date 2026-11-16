# Deploying getfort.io

The site is hosted on **Cloudflare Workers Static Assets**.

| | |
|---|---|
| Worker name | `fort-web` |
| Live URLs | https://getfort.io, https://www.getfort.io |
| workers.dev URL | off: with custom domains in `routes`, Wrangler disables `workers.dev` |
| Cloudflare account | `7be48c17ff1b7cfb0a4b65cae4cb8ad3` |
| Worker config | Fort repo, `docs/site/_build/wrangler.jsonc` |

It is a Worker, not a Pages project: `wrangler pages deploy` is the wrong command.

## How it deploys

**Cloudflare Workers Builds**, connected to the Fort repo (`spawningpool/fort`) through
Cloudflare's GitHub app, builds and deploys on every push to Fort `main` that changes the
docs, the customer Terraform or the build entry. Nothing else deploys: not this repo, not
a laptop. The live site is Fort `main` built with the fort-site commit Fort pins.

- Fort's `docs/site/_build/build.sh` fetches this repo at the commit in
  `docs/site/_build/SITE_VERSION` (a full 40-hex sha), runs its tests, builds `dist/`
  from that Fort checkout, and installs wrangler from this repo's `package-lock.json`
  (`npm ci --ignore-scripts`).
- Fort's `docs/site/_build/deploy.sh` runs that wrangler with Fort's
  `docs/site/_build/wrangler.jsonc`. It refuses to run outside Workers Builds.
- A change here goes live only when a reviewed Fort PR moves `SITE_VERSION` to it.

Every deploy publishes `/build.json` (`fort_sha`, `fort_site_sha`, and `dist_sha256`, a
digest of every published path and its content), served with `Cache-Control: no-cache`
through `_headers`, so anyone can see what is live.

## Workers Builds settings

Set once by the owner in the Cloudflare dashboard: Workers & Pages → `fort-web` →
Settings → Builds → Connect, then the GitHub repository `spawningpool/fort`.

| Setting | Value |
|---|---|
| Production branch | `main` |
| Non-production branch builds | off |
| Root directory | `/` (the repository root) |
| Build watch paths, include | `docs/site/**`, `deploy/terraform/customer/**` |
| Build command | `bash docs/site/_build/build.sh` |
| Deploy command | `bash docs/site/_build/deploy.sh` |
| Build variables and secrets | none |
| API token | the one Workers Builds creates |

The build image (Ubuntu 24.04) has Python 3.14, Node.js and git; the build installs no
Python packages. Cloudflare's GitHub app gets read access to the Fort repo; the owner
accepted that on 2026-11-16.

**First deploy:** connect the repository only after a local build of the Fort head that
will be live has been compared with the live site (see "Compare with live").

## Compare with live

From a Fort checkout:

```bash
FORT_SITE_REPO=~/Work/fort-site bash docs/site/_build/build.sh
python3 ~/Work/fort-site/build/verify_live.py --report docs/site/_build/dist
```

`--report` lists every file that differs from https://getfort.io, saying when a page only
differs in bytes but reads the same. Without `--report` it checks that the live site
serves `dist/` exactly (the check to run after a deploy).

## Domains

`wrangler.jsonc` attaches `getfort.io` and `www.getfort.io` as custom domains on the
`getfort.io` zone. Wrangler creates the DNS records and certificates on deploy; it fails if
either hostname already has an A, AAAA or CNAME record.

## What is published

`build/build.py` assembles `dist/`, the only directory that gets published: the landing
page, `404.html`, the CSS/JavaScript, `assets/`, the docs pages rendered from Fort's
`docs/site/`, `/build.json`, and the Terraform ZIP and checksum packed from Fort's
`deploy/terraform/customer/`. This repo's docs, `PRODUCT.md` and `build/` stay out, as
does Fort's `docs/site/_build/`. Unknown paths serve `404.html`.

When adding a landing-page file, add it to `STATIC` in `build/build.py`. A new docs page
is a new `docs/site/<page>/index.md` in Fort; it needs no change here.

## Roll back

Prefer fixing forward on Fort `main`. In an emergency, Cloudflare's dashboard
(Workers & Pages → `fort-web` → Deployments) or `npx wrangler rollback --name fort-web`
restores an earlier version. A rollback changes the live Worker, not Git, and the next
build of `main` deploys again, so fix `main` straight after.

## Copy

The page describes the product in the Fort repo (`docs/SPEC.md`). Fort is pre-launch
and its repo is private until launch: don't claim it is generally available or that the
code is public yet, and keep every control the page names in line with SPEC §3 (v0
controls only; budgets and spend limits are never the pitch).

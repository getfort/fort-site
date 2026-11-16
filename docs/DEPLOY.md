# Deploying Fort

The site is a static page hosted on **Cloudflare Workers Static Assets**, set up the same
way as Cyclops and Spawning Pool.

| | |
|---|---|
| Worker name | `fort-web` |
| Live URLs | https://getfort.io, https://www.getfort.io |
| First deployed | 2026-10-23 |
| workers.dev URL | off: with custom domains in `routes`, Wrangler disables `workers.dev` |
| Cloudflare account | `Mahmoudnashef@gmail.com's Account` (`7be48c17ff1b7cfb0a4b65cae4cb8ad3`) |
| Config | [`wrangler.jsonc`](../wrangler.jsonc) |

It is a Worker, not a Pages project: `wrangler pages deploy` is the wrong command.

## Early-access form

The `#access` section links to the existing **Fort early access** Typeform
(`https://form.typeform.com/to/twrlRIKM`) in a new tab. Edit questions in Typeform.
To change the form, update the external early-access link in `index.html`.

## Domains

`wrangler.jsonc` attaches `getfort.io` and `www.getfort.io` as custom domains on the
`getfort.io` zone. Wrangler creates the DNS records and certificates on deploy; it fails if
either hostname already has an A, AAAA or CNAME record.

## Deploy

Prerequisites: Node.js/npm and access to the Cloudflare account above. Authenticate
with `npx wrangler login` if needed; `npx wrangler whoami` checks the active account.
Do not put authentication tokens in this repository.

Use a branch from current `main`, preview the change, and open a PR with its source.
Deployment and merging are separate actions. If deployment is authorized before
merge, mark the PR as already deployed and record the source commit and version ID.

From `sites/fort/`:

```bash
./build.sh
for file in script.js warden.js arrivals.js docs/docs.js; do node --check "$file"; done
npx wrangler deploy
```

`build.sh` assembles `dist/`, the only directory that gets published: `index.html`,
`404.html`, the landing-page CSS/JavaScript, `assets/`, and the documentation home and shared assets
`docs/index.html`, `docs/docs.css`, and `docs/docs.js`. Public guides use
`index.html` in `docs/understand/`, `docs/deploy/`, `docs/policy/`,
`docs/operations/`, `docs/aws/`, `docs/gcp/`, `docs/oci/`, and `docs/tools/`, their `reference/` pages, and the two allowlisted Terraform
ZIP/checksum files in `downloads/`. Internal `docs/*.md` files
are excluded. The build adds content hashes to every public CSS/JavaScript file,
the logo and favicon, including references from the Docs page.
Unknown paths serve `404.html`.

When adding a public file, add it to the copy list in `build.sh`. Check the production
title and description, remove preview-only `noindex`, and use the real early-access
form URL. Do not include comparison previews in the published output.

## Verify after deployment

- Open https://getfort.io and https://www.getfort.io and confirm the selected version.
- Check the logo, CSS and JavaScript load without browser errors.
- Check `/docs/`, `/docs/understand/`, `/docs/deploy/`, `/docs/policy/`,
  `/docs/operations/`, `/docs/aws/`, `/docs/gcp/`, `/docs/oci/`, `/docs/tools/`, their cross-links and section navigation, the policy and approval links, desktop/mobile navigation, the
  Warden example and the early-access link.
  Check old `/docs/#policies` and `/docs/#agents` deep links, the shared
  documentation navigation disclosure on mobile, and local page contents.
  No form submission is needed to verify its destination.
- Visit an unknown path and confirm an HTTP 404 with the Fort not-found page.
- Verify `/docs/DEPLOY.md` is not published (HTTP 404).
- Record the returned Cloudflare version ID and validation results in the PR.

## Roll back

Run these commands from `sites/fort/`. Inspect the history before rolling back:


```bash
npx wrangler deployments list --name fort-web
```

```bash
npx wrangler rollback --name fort-web
```

After rollback, verify the domains again. Rollback changes the live Worker, not Git;
record it in the PR and reconcile the source before the next deployment.

## Local preview

From the web-pages root (or run the `fort` entry in `.claude/launch.json`):

```bash
python3 -m http.server 8003 --directory sites/fort
```

Then open http://localhost:8003.

## Copy

The page describes the product in the Fort repo (`docs/SPEC.md` in `~/Work/fort`). Fort
is pre-launch and its repo is private until launch: don't claim it is generally available or
that the code is public yet, and keep every control the page names in line with SPEC §3 (v0
controls only; budgets and spend limits are never the pitch).

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

The `#access` section embeds the Typeform **Fort early access** (`twrlRIKM`), a copy of the
Cyclops form with Fort's questions and its own brown theme. Edit the questions and theme in
Typeform, not here. To swap forms, change `data-tf-widget` and the `<noscript>` link in
`index.html`.

## Domains

`wrangler.jsonc` attaches `getfort.io` and `www.getfort.io` as custom domains on the
`getfort.io` zone. Wrangler creates the DNS records and certificates on deploy; it fails if
either hostname already has an A, AAAA or CNAME record.

## Deploy

From `sites/fort/`:

```bash
./build.sh && npx wrangler deploy
```

`build.sh` assembles `dist/`, the only directory that gets published: `index.html`,
`404.html`, `styles.css` and `script.js` (with content-hash cache-busting) and `assets/`.
Unknown paths serve `404.html`.

## Roll back

```bash
npx wrangler deployments list --name fort-web
```

```bash
npx wrangler rollback --name fort-web
```

## Local preview

From the web-pages root (or run the `fort` entry in `.claude/launch.json`):

```bash
python3 -m http.server 8003 --directory sites/fort
```

Then open http://localhost:8003.

## Copy

The page describes the product in the Fort repo (`docs/SPEC.md` in `~/Work/arcology`). Fort
is pre-launch and its repo is private until launch: don't claim it is generally available or
that the code is public yet, and keep every control the page names in line with SPEC §3 (v0
controls only; budgets and spend limits are never the pitch).

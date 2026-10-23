# Deploying Fort

The site is a static page hosted on **Cloudflare Workers Static Assets**, set up the same
way as Cyclops and Spawning Pool.

| | |
|---|---|
| Worker name | `fort-web` |
| Live URLs | not deployed yet; will be https://getfort.io and https://www.getfort.io |
| workers.dev URL | off: with custom domains in `routes`, Wrangler disables `workers.dev` |
| Cloudflare account | `Mahmoudnashef@gmail.com's Account` (`7be48c17ff1b7cfb0a4b65cae4cb8ad3`) |
| Config | [`wrangler.jsonc`](../wrangler.jsonc) |

It is a Worker, not a Pages project: `wrangler pages deploy` is the wrong command.

## Before the first deploy

1. **Early-access link.** The button in `#access` has the placeholder
   `href="EARLY_ACCESS_URL"`. Point it at the form (a Typeform like Cyclops, or a mailto).
   `build.sh` refuses to build while the placeholder is there.
2. **Domain.** `wrangler.jsonc` attaches `getfort.io` and `www.getfort.io` as custom domains
   on the `getfort.io` zone. Wrangler creates the DNS records and certificates on deploy; it
   fails if either hostname already has an A, AAAA or CNAME record, so remove any parking
   records first.

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

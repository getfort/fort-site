# fort

Landing page for Fort: secure environments for your agents. "Any agent. Any harness. Your controls."

Plain static HTML/CSS/JS, no build tooling beyond [`build.sh`](build.sh). Hosted on
Cloudflare Workers Static Assets.

```
index.html     the page
404.html       served for unknown paths
styles.css     light theme, grey stone and forest greens; the colour tokens are at the top
script.js      the hero demo (an agent walks tool calls to the gate; Warden allows, asks, denies)
assets/        fort.svg (the logo: a grey tower with eyes in the doorway) and favicon.svg
build.sh       assembles dist/ (the only thing published)
wrangler.jsonc Worker config
docs/          internal docs — never published
```

The hero scene is inline SVG in `index.html`. The creatures are agents, one per sandbox tent;
the one with the helmet is Warden. Deploying, the pre-deploy checklist and rollback:
[docs/DEPLOY.md](docs/DEPLOY.md).

# Fort landing page

Fort's illustrated, text-led landing page. Plain static HTML, CSS and JavaScript,
hosted on Cloudflare Workers Static Assets at https://getfort.io.

- `index.html`: the selected shorter-copy landing page, with inline vector forts and agents.
- `styles.css`: off-white, sage and forest-green theme; responsive layouts and reduced-motion support.
- `script.js`: shared mobile navigation.
- `warden.js` / `warden.css`: the interactive sandbox, agent and Warden example.
- `arrivals.js`: the hero agent enters the fort and remains inside.
- `additions.css`: problem statement, human oversight and audit sections.
- `docs/index.html`, `docs/docs.css`, `docs/docs.js`: public documentation at `/docs/`; Markdown files in that directory are internal and excluded from publication.
- `assets/`: the existing Fort logo and favicon.
- `404.html`: matching not-found page.
- `build.sh`: assembles the published `dist/` and adds content hashes to CSS and JavaScript.

Early-access buttons lead to the existing Fort Typeform (`twrlRIKM`).
The Warden panel is an illustrative example, not a connected environment.

See `docs/DEPLOY.md` for deployment and rollback instructions.

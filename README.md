# Fort landing page

Fort's illustrated, text-led landing page. Plain static HTML, CSS and JavaScript,
hosted on Cloudflare Workers Static Assets at https://getfort.io.

- `index.html`: the selected shorter-copy landing page, with inline vector forts and agents.
- `styles.css`: off-white, sage and forest-green theme; responsive layouts and reduced-motion support.
- `script.js`: shared mobile navigation.
- `warden.js` / `warden.css`: the interactive sandbox, agent and Warden example.
- `arrivals.js`: the hero agent enters the fort and remains inside.
- `additions.css`: problem statement, human oversight and audit sections.
- `docs/index.html`: task-oriented documentation home at `/docs/`.
- `docs/understand/`, `docs/deploy/`, `docs/policy/`, `docs/operations/`: focused concepts, deployment choices, policy/approvals and operations reference. Original `/docs/#section` links route to these pages with linked fallbacks.
- `docs/docs.css`, `docs/docs.js`: shared responsive documentation navigation, local contents and presentation. Markdown files remain internal and excluded from publication.
- `docs/tools/index.html`: practical agent/tool-server separation, managed-container deployment, client setup and first-call verification.
- `docs/aws/index.html`, `docs/gcp/index.html`: Terraform deployment guides for early-access customer installations; keep examples aligned with Fort’s customer modules.
- `assets/`: the existing Fort logo and favicon.
- `404.html`: matching not-found page.
- `build.sh`: assembles the published `dist/` and adds content hashes to CSS and JavaScript.

Early-access buttons lead to the existing Fort Typeform (`twrlRIKM`).
The Warden panel is an illustrative example, not a connected environment.

See `docs/DEPLOY.md` for deployment and rollback instructions.

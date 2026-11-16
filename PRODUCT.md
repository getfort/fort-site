# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Security and platform leaders: CISOs, security architects and platform teams who are being asked to let autonomous AI agents act on real systems (production infrastructure, internal APIs, data), and who must be able to show a regulator or auditor how those agents are controlled. Global, with a specific Japan audience (FSA, METI/MIC guidance). They arrive deciding whether Fort is a credible way to run agents safely, and the job is to request early access.

## Product Purpose

Fort is AI agent trust and security: "a trusted security foundation for the agentic AI era". It governs AI agents as autonomous, non-human digital actors, inside the customer's own cloud. Every agent gets its own locked sandbox and can only do what the customer allows. Success for this site: a qualified security or platform leader understands the three pillars and requests early access.

## Positioning

Know your agent. Control what it does. Trust every interaction. Fort covers agent identity (KYA), governance and protection (policy, a person approving risky actions, containment), and secure communication and audit (credentials outside the agent, every call authorized, a tamper-evident record), on a locked per-agent sandbox built on NVIDIA OpenShell. It runs in the customer's cloud with no SaaS and no phone-home, works with any agent and harness, and needs no changes to the agents.

## Operating Context

Visitors read this as a buyer evaluating risk: they look for the controls, the evidence and the frameworks they answer to (EU AI Act, NIST AI RMF, ISO/IEC 42001, OWASP; in Japan the AI Promotion Act, the AI Guidelines for Business (METI/MIC) and the FSA AI Discussion Paper). The A3/A4 one-pager (~/Work/fort/artifacts/one-pager/fort-one-pager-a3.html) contains the fuller message. On 2026-11-07 the owner selected the shorter illustrated website; it summarizes the same product without reproducing every one-pager section.

## Capabilities and Constraints

- Pre-launch: early access only. Never claim general availability.
- Do not mention open source on the site for now (owner decision, 2026-10-26).
- "Coming soon" items stay labelled as coming soon: model and runtime attestation, provenance, trust and risk scoring; prompt-injection and anomaly detection, vulnerability scanning; secure agent-to-agent (A2A) communication; ready-made control maps and evidence packs.
- Never claim certification or compliance with a framework; Fort is "built for the human oversight and record-keeping these frameworks call for".
- The interactive demo (an SRE agent's tool calls: allow, ask with a person approving, deny) is illustrative and labelled "Example".
- Primary action: request early access through a link to the existing Typeform "Fort early access" (twrlRIKM).

## Brand Commitments

- Name: Fort. Domain: getfort.io. Decision component named Warden in product messages.
- Current selected version (owner, 2026-11-07): the shorter illustrated landing page, chosen after comparing it with a version using the live site's full wording and sections. Headline (owner, 2026-11-13): "Trust between your enterprise / and its autonomous agents." with a line break before "and" and natural wrapping on smaller screens. Hero lede: "Run AI agents in your cloud. Control what they can do, require approval for risky actions, and keep an audit trail."
- Latest approved page flow (2026-11-07): hero with an agent entering one guarded fort; compact problem statement; identity, control and evidence; animated Warden and human oversight; audit/governance; early access. The owner removed the entire four-step deployment section.
- Public Docs at `/docs/` hold the longer material: three pillars, sandbox isolation, YAML policy backed by Cedar, approvals, audit controls, deployment concepts and roadmap. Human oversight and the exact regulator/auditor paragraph also remain on the landing page.
- Warden is a distinct guard character. The agent works inside its sandbox, brings a request to Warden, and returns inside. Only allowed requests reach tools; risky requests wait for a named person. Preserve the existing typography, palette, logo and restrained illustrations.
- Approved look (owner, 2026-10-26): grey stone fort, forest greens, no brown. The A3 uses the same palette tokens. Logo: the grey stone fort in assets/fort.svg (the A3's tower icon is not used on the site).
- Current illustration direction (owner, 2026-11-07): restrained vector forts and small agents, with subtle motion and reduced-motion support. Keep the existing grey logo. Avoid pixel art, realistic 3D backgrounds, brown palettes and oversized decorative scenes.

## Evidence on Hand

- The A3 one-pager (content source) and the Fort spec in ~/Work/fort/docs/SPEC.md.
- No customers, testimonials, benchmarks, pricing or press exist. Never fabricate them.

## Product Principles

1. Trust comes from things a buyer can check, not promises: show the mechanism (allow, ask, deny, the record) rather than adjectives.
2. Honest scope: what ships in v0 is stated plainly, what comes later is labelled "Coming soon".
3. The customer stays in control: their cloud, their policies, their approvers.

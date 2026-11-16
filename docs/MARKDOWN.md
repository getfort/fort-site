# Docs Markdown

The docs pages are written in Fort's `docs/site/`, one folder per page, mirroring the
URL: `docs/site/gcp/reference/index.md` is https://getfort.io/docs/gcp/reference/.
`docs/site/_sidebar.md` is the docs navigation. `docs/site/README.md` is not published.

The renderer (`build/site_markdown.py`) supports a small, strict set of Markdown.
Anything else stops the build, so a typo never publishes a broken page.

## Front matter

```
---
title: Deploy Fort on Google Cloud — Fort Docs
description: Deploy Fort on Google Cloud: Fort early-access documentation.
skip: Skip to deployment guide
contents:
- [Prerequisites](#prepare)
- [Configure](#configure)
---
```

`title`, `description` and `skip` (the skip-link text) are required. `contents` is the
"On this page" list. `og_title` and `og_description` add social-preview tags.

## Blocks

Separate blocks with a blank line.

| Write | Get |
|---|---|
| `# Title`, `## Title`, `### Title` | headings |
| a paragraph | `<p>` |
| `- item` lines | a bulleted list |
| `1. item` lines | a numbered list |
| `::: section {#id .class}` … `:::` | a `<section>` around the blocks inside |
| `::: div {.class}` … `:::` | a `<div>` around the blocks inside |
| ` ``` Caption ` … ` ``` ` | a code figure with that caption |
| ` ``` File name \| Language ` … ` ``` ` | a code figure with a two-part caption |
| a block starting with `<` | raw HTML, published as written |

Add an id or classes to a heading or paragraph with ` {#id .class}` at its end, and to a
list with a `{.class}` line after its last item. A code figure takes attributes for its
`<pre>` after the caption: ` ``` Caption {aria-label="Example"} `.

Raw HTML is for the page components (cards, diagrams, tables): its lines are joined
without spaces, except inside `<pre>`, where line breaks are kept.

## Inline

`` `code` ``, `**strong**`, `*emphasis*`, `[text](link)` and `[text](link){.button download}`.
Inline HTML tags such as `<br>` and `<span aria-hidden="true">↗</span>` pass through.
Write `&`, `<` and quotes as plain characters; they are escaped for you. A backslash
escapes `` \` \* \[ \] \{ \} \< \& \\ ``.

Links are written as they appear on the published page, relative to it.

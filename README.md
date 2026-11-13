# AI-Augmented Data Engineering Roadmap

A project-led, 24-week curriculum for learning data engineering and adding AI to analytics workflows with explicit quality, security, and evaluation boundaries. The site itself is a lightweight Python-built, Markdown-first static learning platform.

## Curriculum

The curriculum is organized around three eight-week phases:

| Phase | Weeks | Focus | Main outcome |
|---|---:|---|---|
| Core Foundation | 1-8 | Platform architecture, OLTP/OLAP, storage formats, ingestion/CDC, modeling, quality, orchestration | A reproducible analytics warehouse |
| Modern Analytics + AI Bridge | 9-16 | Governance, data products, BI/serving, query engines, metrics, semantic models, Text2SQL | A bounded, governed analytics assistant |
| AI-Native Workflows | 17-24 | RAG, structured extraction, evaluation, agent boundaries, lifecycle operations | An integrated and operable AI data platform |

Start at [the learning homepage](content/index.md) and follow each phase in order. The project briefs build on one another; the skill pages are references for concepts used by those projects.

The site includes a complete Vietnamese edition. Open [trang chủ tiếng Việt](content/vi/index.md), or use the language switch on any generated page to move to its counterpart. Vietnamese pages are generated under `dist/vi/`; search results stay within the current language.

For source material that is not bundled with its website repository, use the [Data Engineering reading map](content/skills/references/data-engineering-reading-map.md). It preserves source links and maps them to original local lessons rather than mirroring external note text.

## Content map

- `content/roadmap/`: week-by-week study plans, outcomes, and phase exit criteria.
- `content/skills/sql/`: analytical SQL and query performance.
- `content/skills/python/`: reliable ingestion and pipeline practices.
- `content/skills/data-engineering/`: architecture, storage, ingestion/CDC, modeling, governance, BI serving, query performance, lifecycle, contracts, orchestration, cloud access.
- `content/skills/ai/`: semantic modeling, Text2SQL, RAG, evaluation, observability, and bounded agents.
- `content/skills/field-guide/`: original long-form chapters covering the full learning map, infrastructure, processing, analytics, technologies, and career practice.
- `content/skills/references/`: attributed external reading maps linking source notes to local lessons.
- `content/projects/`: five linked project briefs from a warehouse to an integrated capstone.

Each project defines a goal, architecture or workflow, deliverables, and acceptance criteria. These are implementation briefs, not claims that production security or reliability follows automatically from using a particular model or framework.

## Features

- Read many `.md` files from `content/`
- Build static HTML into `dist/`
- Sidebar generated from Markdown metadata
- Static search index generated as `search-index.json`
- Dark mode
- No database required for MVP
- Good performance because Markdown is parsed at build time, not runtime
- Nested Markdown content is published as standalone HTML pages

## Repository layout

```text
assets/       Search and site styles
content/      Markdown lessons, roadmaps, and project briefs
templates/    Shared page template
build.py      Markdown and frontmatter to static HTML build
dist/         Generated site output (created by the build)
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Build

```bash
python build.py
```

Output will be generated in:

```txt
dist/
```

## Preview locally

```bash
cd dist
python -m http.server 8000
```

Open:

```txt
http://localhost:8000
```

## Add or update a lesson

Create a new Markdown file under `content/`:

```md
---
title: My Lesson
description: Short description.
order: 1
tags: [sql, python]
---

# My Lesson

Write content here.
```

Keep the frontmatter keys consistent with existing pages. Use a unique `order` within the section and add descriptive tags because these fields feed the generated sidebar and search index. Prefer practical examples, edge cases, exercises, and explicit completion criteria over topic-only summaries.

Then rebuild:

```bash
python build.py
```

Check that the page appears in `dist/`, that nested links resolve from the generated page location, and that the browser search index contains its title, tags, and text.

## Content conventions

- State assumptions, data grain, units, and time boundaries where they affect the result.
- Use examples that can be inspected and checked; label illustrative schemas and pseudocode clearly.
- Distinguish tool-specific behavior from general principles.
- Include failure modes, validation, and recovery alongside the happy path.
- For AI workflows, describe evaluation, provenance, access boundaries, and human escalation.
- Do not imply that a fluent answer or a passing schema check alone proves correctness.

## Build and preview

The build requires the Python packages in `requirements.txt`. It removes and recreates `dist/`, then writes HTML pages, static assets, and `search-index.json`. Keep source material under `content/`; do not edit generated pages in `dist/` by hand.

## Deployment

You can deploy the `dist/` folder to GitHub Pages, Cloudflare Pages, Netlify, or Vercel.

## Related

- [Modern Data Engineering Deck](https://github.com/duan-n2d/modern-data-stack) — a slide-based companion covering 23 data engineering layers, with an interactive knowledge graph ([live](https://duan-n2d.github.io/modern-data-stack/)).
- [Dylxn Assistant](https://github.com/duan-n2d/dylxn-assistant) — a local RAG assistant for asking questions over data-engineering notes.

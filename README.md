# AI-Augmented Data Engineering Roadmap

A Python-built, Markdown-first static learning platform.

## Features

- Read many `.md` files from `content/`
- Build static HTML into `dist/`
- Sidebar generated from Markdown metadata
- Static search index generated as `search-index.json`
- Dark mode
- No database required for MVP
- Good performance because Markdown is parsed at build time, not runtime

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

## Add a new lesson

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

Then rebuild:

```bash
python build.py
```

## Recommended deployment

You can deploy the `dist/` folder to GitHub Pages, Cloudflare Pages, Netlify, or Vercel.

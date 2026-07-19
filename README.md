# ordivon-web

The public website and internet entrypoint for Ordivon.

Current public site: <https://lab.ordivon.com>

## Current scope

This repository contains a deliberately small static site:

- no framework;
- no package manager;
- no database;
- no analytics or cookies;
- no external fonts, scripts, or image dependencies;
- deployable from the repository root with GitHub Pages.

The core Ordivon governance project remains separate at
[`zycxfyh/Ordivon`](https://github.com/zycxfyh/Ordivon).

## Local preview

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Verification

Run the same dependency-free contract used by CI:

```bash
python3 scripts/check_site.py
```

The check validates required files, local runtime assets, internal links and
fragments, basic HTML metadata, the `lab.ordivon.com` CNAME, and the absence of
selected analytics/tracking patterns.

## Files

```text
index.html                    public landing page
404.html                      static not-found page
assets/styles.css             visual system and responsive layout
assets/app.js                 minimal progressive enhancement
assets/mark.svg               site mark and favicon
scripts/check_site.py         dependency-free release contract
docs/operations.md            deployment and recovery runbook
.github/workflows/site-check.yml
                              pull-request and main-branch verification
.nojekyll                     disable Jekyll processing on GitHub Pages
CNAME                         GitHub Pages custom-domain claim
```

## Deployment boundary

GitHub Pages publishes from `main` and the repository root. The custom domain is
`lab.ordivon.com`; the apex `ordivon.com` and `www.ordivon.com` remain separately
managed by the existing GoDaddy Website Builder configuration.

A normal content release or rollback must not modify DNS. See
[`docs/operations.md`](docs/operations.md) before changing Pages settings,
`CNAME`, or any GoDaddy record.

# ordivon-web

The public website and internet entrypoint for Ordivon.

Current public site: <https://lab.ordivon.com>

## Public identity

Ordivon is a long-term public laboratory and umbrella for systems, knowledge,
research, and trustworthy action in the AI era.

The site distinguishes the umbrella from its current public work:

- [`zycxfyh/Ordivon`](https://github.com/zycxfyh/Ordivon) is the explicit
  epistemic and AI-governance foundation;
- [`zycxfyh/FinHarness`](https://github.com/zycxfyh/FinHarness) is an applied
  system that carries evidence, authority, review, receipt, and irreversible-action
  governance into personal-capital decisions.

Future documentation, notes, applications, APIs, and MCP services are not presented
as available until a maintained public service actually exists.

## Current scope

This repository contains a deliberately small static site:

- no framework;
- no package manager;
- no database;
- no analytics or cookies;
- no external fonts, scripts, or image dependencies;
- deployable from the repository root with GitHub Pages.

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
assets/styles.css             base visual system and responsive layout
assets/root-ready.css         root-ready information architecture components
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

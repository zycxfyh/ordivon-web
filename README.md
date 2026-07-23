# ordivon-web

The public website and internet entrypoint for Ordivon.

Current public site: <https://ordivon.com>

## Current scope

This repository contains a deliberately small multi-page static site:

- no frontend framework or runtime package manager;
- pinned npm development dependencies only for browser, accessibility, and Lighthouse CI;
- no database, accounts, or backend;
- no analytics, cookies, or contact-data collection;
- no external fonts, scripts, or image dependencies;
- deployable from the repository root with GitHub Pages.

The site provides thin, useful surfaces for Home, Projects, Notes, Current, About, and
Contact. Project implementation and technical documentation remain in their
canonical repositories.

## Public routes

```text
/                                      research and project publishing entrypoint
/work/                                 maintained engineering project directory
/work/ordivon-runtime/                 durable agent execution and recovery runtime
/work/finharness/                      personal capital review and decision system
/work/ordivon-web/                     public publishing and deployment surface
/notes/                                chronological authored notes and release records
/feed.xml                              Atom feed for published notes
/notes/ordivon-runtime-release/        Ordivon Runtime M0–M7 core release note
/notes/why-ordivon/                    first substantive design note
/now/                                  current activity and explicit non-offerings
/about/                                scope, relationships, and ownership boundary
/contact/                              public discussion and reporting routes
```

## Local preview

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

## Verification

Run the fast dependency-free contract:

```bash
python3 scripts/check_site.py
```

The check validates:

- required pages and metadata;
- nested local links, runtime assets, shared navigation, and Home routes;
- canonical URLs, `sitemap.xml`, `robots.txt`, `site.webmanifest`, and Atom feed;
- Open Graph, Twitter Card, JSON-LD, and local 1200×630 social images;
- the exact `ordivon.com` CNAME;
- the absence of selected analytics, tracking, cookie-writing, and external-network patterns.

Install the pinned development-only verification tools and run the browser layer:

```bash
npm ci
npx playwright install chromium
npm run test:browser
npm run test:links
```

The browser workflow checks all maintained public routes across desktop, tablet,
and mobile viewports. It verifies keyboard navigation, target sizes, horizontal
overflow, browser-console errors, and serious or critical axe findings. Selected
full-page screenshots and informational Lighthouse reports are uploaded as CI
Artifacts rather than committed as visual baselines.

## Main files

```text
index.html                    public landing page
work/                         project directory and project detail pages
notes/                        notes index, release records, and authored articles
now/                          time-bounded current activity
about/                        scope and operating model
contact/                      public contact routes
404.html                      static not-found page
assets/styles.css             base visual system and responsive layout
assets/umbrella.css           multi-page components
assets/app.js                 minimal progressive enhancement
assets/mark.svg               site mark and favicon
assets/social/                local social-preview PNG files
feed.xml                      Atom feed for Notes
site.webmanifest              install/display metadata
sitemap.xml                   explicit maintained-route map
robots.txt                    crawler guidance
scripts/check_site.py         dependency-free release contract
scripts/check_external_links.py
                              bounded external-link sampling
playwright.config.mjs         browser project and local-server configuration
tests/browser/site.spec.js    responsive, keyboard, accessibility, and screenshot checks
package.json / package-lock.json
                              pinned development-only browser verification dependencies
docs/operations.md            deployment and recovery runbook
.github/workflows/site-check.yml
                              fast pull-request and main-branch verification
.github/workflows/browser-check.yml
                              browser evidence and informational Lighthouse reports
.nojekyll                     disable Jekyll processing on GitHub Pages
CNAME                         GitHub Pages custom-domain claim
```

## Deployment boundary

GitHub Pages publishes from `main` and the repository root with `ordivon.com` as
the canonical custom domain. Cloudflare is the authoritative DNS provider;
`www.ordivon.com` resolves through GitHub Pages and `lab.ordivon.com` is a
Cloudflare-managed permanent redirect to the matching path on the apex domain.

A normal content release or rollback must not modify DNS. See
[`docs/operations.md`](docs/operations.md) before changing Pages settings,
`CNAME`, Cloudflare DNS, or redirect rules.

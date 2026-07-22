# ordivon-web

The public website and internet entrypoint for Ordivon.

Current public site: <https://lab.ordivon.com>

## Current scope

This repository contains a deliberately small multi-page static site:

- no framework or package manager;
- no database, accounts, or backend;
- no analytics, cookies, or contact-data collection;
- no external fonts, scripts, or image dependencies;
- deployable from the repository root with GitHub Pages.

The site provides thin, useful surfaces for Home, Work, Notes, Now, About, and
Contact. Project implementation and technical documentation remain in their
canonical repositories.

## Public routes

```text
/                         umbrella entrypoint
/work/                    verified project and research directory
/work/ordivon-runtime/    durable agent execution and recovery runtime
/work/finharness/          personal capital review and decision system
/work/ordinary-prosperity/ comparative economic research program
/work/ordivon-web/         public publishing and deployment surface
/notes/                   authored public notes
/notes/why-ordivon/       first substantive note
/now/                     current activity and explicit non-offerings
/about/                   scope, relationships, and ownership boundary
/contact/                 public discussion and reporting routes
```

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

The check validates:

- required pages and metadata;
- nested local links, runtime assets, shared navigation, and Home routes;
- canonical URLs, `sitemap.xml`, `robots.txt`, and `site.webmanifest`;
- the exact `lab.ordivon.com` CNAME;
- the absence of selected analytics, tracking, cookie-writing, and external-network patterns.

## Main files

```text
index.html                    public landing page
work/                         project directory and project detail pages
notes/                        notes index and authored articles
now/                          time-bounded current activity
about/                        scope and operating model
contact/                      public contact routes
404.html                      static not-found page
assets/styles.css             base visual system and responsive layout
assets/umbrella.css           multi-page components
assets/app.js                 minimal progressive enhancement
assets/mark.svg               site mark and favicon
site.webmanifest              install/display metadata
sitemap.xml                   explicit maintained-route map
robots.txt                    crawler guidance
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

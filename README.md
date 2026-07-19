# ordivon-web

The public website and internet entrypoint for Ordivon.

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
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Files

```text
index.html          public landing page
404.html            static not-found page
assets/styles.css   visual system and responsive layout
assets/app.js       minimal progressive enhancement
assets/mark.svg     site mark and favicon
.nojekyll            disable Jekyll processing on GitHub Pages
```

## Deployment boundary

The first deployment should use the GitHub Pages project URL. Do not change the
current `ordivon.com` GoDaddy root records until the project URL has been reviewed
and HTTPS is working.

A custom subdomain such as `lab.ordivon.com` should be connected only in a later,
separately verified step.

# Ordivon Web Operations

This runbook describes the current public-site deployment only. It does not govern
Ordivon Core, email, APIs, databases, MCP services, or the root-domain GoDaddy site.

## Current topology

```text
GitHub repository: zycxfyh/ordivon-web
Publishing source: main / repository root
Default Pages URL: https://zycxfyh.github.io/ordivon-web/
Custom site URL: https://lab.ordivon.com
```

DNS remains hosted by GoDaddy on the existing authoritative nameservers:

```text
ns75.domaincontrol.com
ns76.domaincontrol.com
```

Relevant records at the time this runbook was written:

```text
A      @       WebsiteBuilder Site       # existing root-domain site
CNAME  www     ordivon.com                # existing www route
CNAME  lab     zycxfyh.github.io          # this GitHub Pages site
TXT    _github-pages-challenge-zycxfyh    # account-level domain verification
```

The TXT value is intentionally not copied into this repository. Preserve that
verification record while GitHub Pages subdomains under `ordivon.com` are in use.

## Normal release path

1. Create a branch from the current `main` head.
2. Make one bounded site change.
3. Run the local verifier:

   ```bash
   python3 scripts/check_site.py
   ```

4. Open a pull request.
5. Require the `Verify static site` check to pass.
6. Review public claims, local assets, mobile layout, and links.
7. Merge the exact reviewed head.
8. Wait for the GitHub Pages deployment to complete.
9. Verify both:

   ```text
   https://lab.ordivon.com
   https://zycxfyh.github.io/ordivon-web/
   ```

10. Confirm that `https://ordivon.com` still serves its separately managed root site.

A normal content release must not require a DNS change.

## What the automated check proves

The repository verifier checks that:

- required static files exist;
- `CNAME` is exactly `lab.ordivon.com`;
- HTML declares a language, title, and viewport;
- fragment targets and local file links resolve;
- runtime scripts, stylesheets, images, icons, frames, audio, and video remain local;
- CSS does not import external runtime assets;
- selected analytics, tracking, and cookie-writing patterns are absent.

It does not prove visual quality, factual correctness of every public claim,
external-link availability, DNS propagation, certificate issuance, or browser
compatibility. Those remain review and post-deployment checks.

## Content rollback

Use this when a merged page change is wrong but GitHub Pages and DNS are healthy.

1. Identify the last known-good commit on `main`.
2. Create a revert commit on a new branch; do not force-push `main`.
3. Open a pull request containing only the rollback.
4. Run the same site check and review the resulting diff.
5. Merge the rollback and verify the Pages deployment.

Do **not** edit GoDaddy DNS for an ordinary content rollback. DNS points to the
publishing service, not to a particular site revision.

## Deployment failure triage

Check in this order:

1. **Repository contract** — run `python3 scripts/check_site.py`.
2. **Pull-request check** — inspect the `Site checks` workflow.
3. **Pages deployment** — inspect the Pages build/deployment run in GitHub Actions.
4. **Publishing source** — confirm Pages still uses `main` and `/(root)`.
5. **Custom-domain file** — confirm `CNAME` contains only `lab.ordivon.com`.
6. **DNS** — confirm the sole `lab` CNAME points to `zycxfyh.github.io`.
7. **TLS** — confirm GitHub Pages reports DNS success and Enforce HTTPS is enabled.

Do not change the root `@` record or `www` record while diagnosing a `lab` outage.
They belong to the separate GoDaddy root site.

## DNS or custom-domain recovery

For a temporary DNS problem:

- restore `CNAME lab -> zycxfyh.github.io`;
- keep the repository custom domain as `lab.ordivon.com`;
- keep the account-level GitHub Pages verification TXT record;
- wait for DNS propagation and re-run the Pages DNS check;
- verify HTTPS after GitHub provisions or renews the certificate.

For an intentional permanent detachment from GitHub Pages, avoid leaving a DNS
record pointing at a Pages service that no longer claims the domain. Follow the
current GitHub Pages custom-domain guidance and use this order:

1. remove or replace the public `lab` DNS record;
2. wait until public DNS no longer sends `lab.ordivon.com` to GitHub Pages;
3. remove the custom domain from repository Pages settings;
4. confirm the project remains reachable only at its intended replacement/default URL;
5. retain the root-domain verification TXT record when other GitHub Pages subdomains
   still depend on it.

Current GitHub guidance:

- <https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site>
- <https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages>

## Promotion gate for the root domain

Do not move `ordivon.com` or `www.ordivon.com` to this repository merely because
`lab.ordivon.com` works. Root-domain promotion requires a separate decision covering:

- the long-term public identity and content scope;
- redirects between apex and `www`;
- rollback and outage behavior;
- certificate and DNS verification;
- the fate of the existing GoDaddy Website Builder site;
- email records and other services that must remain untouched;
- an independently reviewed migration plan.

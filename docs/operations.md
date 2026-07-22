# Ordivon Web Operations

This runbook governs the public static site only. It does not govern Ordivon
Runtime, email, APIs, databases, MCP services, Cloudflare Access, or Tunnel.

## Current topology

```text
GitHub repository: zycxfyh/ordivon-web
Publishing source: main / repository root
Default Pages URL: https://zycxfyh.github.io/ordivon-web/
Canonical site URL: https://ordivon.com
Authoritative DNS: Cloudflare
www.ordivon.com: GitHub Pages alternate hostname
lab.ordivon.com: Cloudflare 301 redirect to https://ordivon.com/$path
```

The root and `www` records remain DNS-only while GitHub validates the custom
domain and provisions TLS. The `lab` record is proxied because Cloudflare must
receive the request to apply the redirect rule. Preserve all unrelated records,
especially MCP, Tunnel, Access, mail, and GitHub domain-verification TXT records.

## Normal release path

1. Create a branch from the current `main` head.
2. Make one bounded site change.
3. Run `python3 scripts/check_site.py`.
4. Open a pull request and require `Verify static site` to pass.
5. Review public claims, local assets, mobile layout, and links.
6. Merge the exact reviewed head.
7. Wait for GitHub Pages deployment.
8. Verify `https://ordivon.com` and `https://www.ordivon.com`.
9. Verify `https://lab.ordivon.com/<path>?query` returns a permanent redirect to
   the same path and query on `https://ordivon.com`.

A normal content release must not require DNS changes.

## What the automated check proves

The repository verifier checks that required files exist, `CNAME` is exactly
`ordivon.com`, local links and assets resolve, canonical URLs use the apex
domain, sitemap and robots metadata agree, and selected tracking or external
runtime patterns are absent.

It does not prove visual quality, factual correctness, external-link
availability, DNS propagation, certificate issuance, redirect behavior, or
browser compatibility. Those remain review and post-deployment checks.

## Content rollback

Revert the bad site commit through a reviewed pull request. Do not change DNS
for an ordinary content rollback; DNS points to the publishing service, not a
specific revision.

## Deployment failure triage

Check in this order:

1. `python3 scripts/check_site.py`.
2. GitHub Actions `Site checks` and Pages deployment.
3. Pages publishing source remains `main` and `/(root)`.
4. `CNAME` contains only `ordivon.com`.
5. Apex has the four GitHub Pages A records and `www` points to
   `zycxfyh.github.io`; both remain DNS-only during validation.
6. GitHub Pages reports the custom-domain DNS check as successful.
7. `Enforce HTTPS` is enabled after certificate issuance.
8. `lab` is proxied and the Cloudflare redirect rule preserves path and query.

Do not modify `mcp.ordivon.com` or any Tunnel/Access configuration while
triaging the public site.

## DNS or custom-domain recovery

For GitHub Pages recovery, restore the documented apex A records, the `www`
CNAME, and repository `CNAME`; then rerun GitHub's DNS check and wait for TLS.
Keep GitHub's account-level domain-verification TXT record when present.

For redirect recovery, restore a proxied `lab` DNS record and the Cloudflare
301 rule. A temporary `lab` outage must not be repaired by assigning `lab` as a
second GitHub Pages custom domain.

Current references:

- <https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site>
- <https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages>
- <https://developers.cloudflare.com/rules/url-forwarding/single-redirects/>

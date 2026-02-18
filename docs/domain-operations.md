# Domain Operations (Cloudflare + Canonical .com)

This document is the operator runbook for StateLock public domains.

## Domain Role Matrix

| Domain | Role | Behavior |
|---|---|---|
| `statelockengine.com` | Canonical public site | Serves real content |
| `www.statelockengine.com` | Alias | 301 redirect to apex `.com` |
| `statelockengine.dev` | Redirect-only | 301 redirect to `.com` (path/query preserved) |
| `statelockengine.io` | Redirect-only | 301 redirect to `.com` (path/query preserved) |

## Canonical Rules

1. Public links must use `https://statelockengine.com/...`.
2. Force HTTPS on all hostnames.
3. Redirect all non-canonical hosts to apex `.com`.
4. Preserve path and query params in redirects.

## Cloudflare Checklist

## Phase 1: Foundation

1. Add all domains to Cloudflare:
   - `statelockengine.com`
   - `statelockengine.dev`
   - `statelockengine.io`
2. Update registrar nameservers for each domain to Cloudflare nameservers.
3. Enable SSL/TLS:
   - Always Use HTTPS: `On`
   - Automatic HTTPS Rewrites: `On`
4. If origin-backed service is used (not Pages), set SSL mode to `Full (strict)`.

## Phase 2: Pages Project

1. Create Cloudflare Pages project tied to your website repo.
2. Attach custom domains:
   - `statelockengine.com` (primary)
   - `www.statelockengine.com` (alias, redirected)
3. Deploy minimal v1 routes:
   - `/`
   - `/docs`
   - `/install`
   - `/github` (redirect)
   - `/changelog` (optional redirect)

## Phase 3: Redirect Rules

Use Cloudflare Bulk Redirects or Redirect Rules. See `infra/cloudflare/redirects.csv`.

Required rules:

- `http://statelockengine.com/*` -> `https://statelockengine.com/:splat` (301)
- `http://www.statelockengine.com/*` -> `https://statelockengine.com/:splat` (301)
- `https://www.statelockengine.com/*` -> `https://statelockengine.com/:splat` (301)
- `http://statelockengine.dev/*` -> `https://statelockengine.com/:splat` (301)
- `https://statelockengine.dev/*` -> `https://statelockengine.com/:splat` (301)
- `http://statelockengine.io/*` -> `https://statelockengine.com/:splat` (301)
- `https://statelockengine.io/*` -> `https://statelockengine.com/:splat` (301)

## Phase 4: SEO Consolidation

1. Add canonical tags to all indexable pages.
2. Publish `sitemap.xml` and `robots.txt` on `.com`.
3. Add `statelockengine.com` to Google Search Console.
4. Optionally add `.dev`/`.io` as moved properties for monitoring.

## Phase 5: Email Authentication

Choose one provider and apply records from `infra/cloudflare/dns-template.md`.

Minimum DNS posture on `.com`:

1. MX records for selected provider
2. SPF TXT
3. DKIM records
4. DMARC TXT with ramp-up policy:
   - Start: `p=none`
   - Then: `p=quarantine`
   - Finally: `p=reject`

Recommended sending identity: `@statelockengine.com` only.

## Phase 6: Hardening

1. Cloudflare analytics enabled.
2. Uptime monitor on canonical homepage.
3. Enable HSTS preload only after redirects and certs are stable.

## Verification Commands

## DNS and TLS

```bash
dig +short statelockengine.com

dig +short statelockengine.dev

dig +short statelockengine.io

# Inspect certificates / redirect chain
curl -I https://statelockengine.com
curl -I https://www.statelockengine.com
```

## Redirect correctness

```bash
curl -I "http://statelockengine.dev/foo?x=1"
curl -I "https://statelockengine.io/docs"
curl -I "https://www.statelockengine.com"
```

Expected: HTTP `301` and `Location` pointing to `https://statelockengine.com/...`.

## Email auth checks

```bash
# SPF
nslookup -type=TXT statelockengine.com

# DMARC
nslookup -type=TXT _dmarc.statelockengine.com

# DKIM selector example (replace selector)
nslookup -type=TXT selector1._domainkey.statelockengine.com
```

## Rollout Timeline (Default)

1. Day 1: Cloudflare onboarding + Pages on `.com`
2. Day 1: Redirects for `www`, `.dev`, `.io`
3. Day 1: SPF/DKIM/DMARC baseline
4. Day 2: Analytics, sitemap, Search Console
5. Day 2+: DMARC enforcement tightening

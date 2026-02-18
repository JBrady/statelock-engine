# Website Routing Contract

This document defines public URL behavior for `statelockengine.com`.

## Canonical Host

- Canonical host: `statelockengine.com`
- Canonical scheme: `https`

All non-canonical hostnames must 301 redirect to canonical apex.

## Route Contract (v1)

1. `/`
   - Purpose: product positioning and primary CTAs.
2. `/docs`
   - Purpose: documentation entrypoint.
   - Can be native docs page or redirect to docs repo/docs site.
3. `/install`
   - Purpose: quickstart install instructions.
4. `/github`
   - Purpose: convenience redirect to GitHub repository.
   - Redirect type: 302 (temporary) acceptable, 301 also acceptable once stable.
5. `/changelog`
   - Purpose: release notes.
   - Can redirect to GitHub Releases.

## Canonicalization Rules

Apply these redirects in Cloudflare:

- `http://statelockengine.com/*` -> `https://statelockengine.com/:splat` (301)
- `http://www.statelockengine.com/*` -> `https://statelockengine.com/:splat` (301)
- `https://www.statelockengine.com/*` -> `https://statelockengine.com/:splat` (301)
- `http(s)://statelockengine.dev/*` -> `https://statelockengine.com/:splat` (301)
- `http(s)://statelockengine.io/*` -> `https://statelockengine.com/:splat` (301)

Preserve path and query string.

## SEO Requirements

1. Every indexable page includes canonical link tag:

```html
<link rel="canonical" href="https://statelockengine.com/<path>" />
```

2. `sitemap.xml` contains only `https://statelockengine.com/*` URLs.
3. `robots.txt` references canonical sitemap URL.
4. `.dev` and `.io` should not serve indexable content.

## robots.txt Template

```txt
User-agent: *
Allow: /

Sitemap: https://statelockengine.com/sitemap.xml
```

## sitemap.xml Template (minimal)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://statelockengine.com/</loc></url>
  <url><loc>https://statelockengine.com/docs</loc></url>
  <url><loc>https://statelockengine.com/install</loc></url>
</urlset>
```

## Acceptance Checks

```bash
curl -I https://www.statelockengine.com/docs
curl -I https://statelockengine.dev/install
curl -I https://statelockengine.io/github
```

Expected: redirect to `https://statelockengine.com/...` with same path/query.

# Cloudflare DNS Template (Website + Email Auth)

Use this as a template and replace placeholders with your provider-specific values.

## Domains in scope

- `statelockengine.com` (canonical)
- `statelockengine.dev` (redirect-only)
- `statelockengine.io` (redirect-only)

## Website DNS (minimum)

For Cloudflare Pages custom domains, Cloudflare auto-manages required DNS records.
If manual records are needed, keep proxied mode enabled where applicable.

## Email DNS Baseline (`statelockengine.com`)

## MX (example placeholders)

| Type | Name | Value | Priority |
|---|---|---|---|
| MX | `@` | `mx1.mail-provider.example` | `10` |
| MX | `@` | `mx2.mail-provider.example` | `20` |

## SPF

| Type | Name | Value |
|---|---|---|
| TXT | `@` | `v=spf1 include:mail-provider.example ~all` |

## DKIM (example selectors)

| Type | Name | Value |
|---|---|---|
| CNAME | `selector1._domainkey` | `selector1-statelockengine-com._domainkey.mail-provider.example` |
| CNAME | `selector2._domainkey` | `selector2-statelockengine-com._domainkey.mail-provider.example` |

Some providers use TXT-based DKIM keys; use provider instructions if so.

## DMARC

Start in monitor mode:

| Type | Name | Value |
|---|---|---|
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:dmarc@statelockengine.com; adkim=s; aspf=s; pct=100` |

Tightening policy after validation:

1. `p=none` (monitor)
2. `p=quarantine` (partial enforcement)
3. `p=reject` (full enforcement)

## Optional forwarding aliases

- `hello@statelockengine.com`
- `support@statelockengine.com`
- `security@statelockengine.com`

Keep sender identity on `.com`. Use `.dev`/`.io` only for redirects, not primary email identities.

## Validation Commands

```bash
# MX
nslookup -type=MX statelockengine.com

# SPF
nslookup -type=TXT statelockengine.com

# DMARC
nslookup -type=TXT _dmarc.statelockengine.com

# DKIM selector example
nslookup -type=TXT selector1._domainkey.statelockengine.com
```

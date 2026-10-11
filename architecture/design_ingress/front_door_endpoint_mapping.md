# Azure Front Door – Endpoint and Route Mapping

**Context:** Ingress Option 2 (Azure Front Door Premium → Private Link → App Service). Customers get a wildcard domain per environment (see [domain_name_design.md](../design_domain/domain_name_design.md)), each customer can run multiple apps, and each app runs on its own App Service.

`acme`, `contoso`, `fabrikam`, `crm` and `portal` are example names.

---

## 1. Structure

| Profile | Endpoint | Endpoint type | Route | Custom domain | Rule set | Host name | Origin group |
|---|---|---|---|---|---|---|---|
| `afd-plt-prd` | `fde-acme-prd` | Dedicated | `rt-acme-prd` | `*.acme.plt.msdhn.com` | `rsacmeprd` | `crm.acme.plt.msdhn.com` | `og-acme-crm-prd` |
| `afd-plt-prd` | `fde-acme-prd` | Dedicated | `rt-acme-prd` | `*.acme.plt.msdhn.com` | `rsacmeprd` | `portal.acme.plt.msdhn.com` | `og-acme-portal-prd` |
| `afd-plt-prd` | `fde-acme-prd` | Dedicated | `rt-acme-prd` | `*.acme.plt.msdhn.com` | `rsacmeprd` | Any other host (no match) | Redirect to not-found page |
| `afd-plt-prd` | `fde-grp01-prd` | Shared (up to 10 customers) | `rt-contoso-prd` | `*.contoso.plt.msdhn.com` | `rscontosoprd` | `hr.contoso.plt.msdhn.com` | `og-contoso-hr-prd` |
| `afd-plt-prd` | `fde-grp01-prd` | Shared (up to 10 customers) | `rt-fabrikam-prd` | `*.fabrikam.plt.msdhn.com` | `rsfabrikamprd` | `intranet.fabrikam.plt.msdhn.com` | `og-fabrikam-intranet-prd` |
| `afd-plt-prd` | `fde-grp02-prd` | Shared (next group) | … | … | … | … | … |
| `afd-plt-np` | `fde-acme-np` | Dedicated | `rt-acme-dev` | `*.acme.dev.plt-np.msdhn.com` | `rsacmedev` | `crm.acme.dev.plt-np.msdhn.com` | `og-acme-crm-dev` |
| `afd-plt-np` | `fde-acme-np` | Dedicated | `rt-acme-tst` | `*.acme.tst.plt-np.msdhn.com` | `rsacmetst` | `crm.acme.tst.plt-np.msdhn.com` | `og-acme-crm-tst` |
| `afd-plt-np` | `fde-acme-np` | Dedicated | `rt-acme-acc` | `*.acme.acc.plt-np.msdhn.com` | `rsacmeacc` | `crm.acme.acc.plt-np.msdhn.com` | `og-acme-crm-acc` |

Profiles: `afd-plt-prd` (Premium, prod, `plt.msdhn.com`) and `afd-plt-np` (Premium, non-prod, `plt-np.msdhn.com`). Each route's own origin group is `og-default-prd` / `og-default-np`, only reached when no rule matches.

| Level | One per | Example |
|---|---|---|
| Profile | Environment group (prod, non-prod) | `afd-plt-prd`, `afd-plt-np` |
| Endpoint | Large customer (dedicated) or group of up to 10 customers (shared) | `fde-acme-prd`, `fde-grp01-prd` |
| Custom domain | Customer and environment | `*.acme.plt.msdhn.com` |
| Route | Customer and environment | `rt-acme-prd` |
| Rule set | Customer and environment | `rsacmeprd` |
| Origin group | App and environment | `og-acme-crm-prd` |
| Origin | App and environment | `or-acme-crm-prd` (App Service via Private Link) |
| Security policy + WAF policy | Customer | `sp-acme-prd` + `wafacmeprd` |

---

## 2. Endpoint grouping

| Customer type | Endpoint | Reason |
|---|---|---|
| Large or regulated customer | Dedicated endpoint (`fde-<customer>-<env>`) | Own Front Door host name, logs and on/off switch |
| Other customers | Shared group endpoint (`fde-grpNN-<env>`), filled up to 10 customers | Keeps the 25-endpoint limit per profile out of reach |

The assignment lives in Pulumi configuration, so onboarding places each customer automatically:

```yaml
customers:
  acme:
    endpoint: dedicated
    apps: [crm, portal]
  contoso:
    endpoint: grp01
    apps: [hr]
  fabrikam:
    endpoint: grp01
    apps: [intranet]
```

A customer can move to another endpoint by re-attaching the route's custom domain to a route on the new endpoint and updating the customer's DNS CNAME.

---

## 3. Endpoint settings

| Setting | Value |
|---|---|
| Name | `fde-acme-prd` / `fde-grp01-prd` |
| Enabled state | Enabled |
| Auto-generated host name | `fde-acme-prd-<hash>.z01.azurefd.net` (used only as CNAME target) |
| Name reuse scope | `TenantReuse` (default), so a redeployed endpoint keeps the same host name and existing CNAMEs stay valid |

---

## 4. Custom domain settings

| Setting | Value |
|---|---|
| Host name | `*.acme.plt.msdhn.com` |
| Certificate type | Bring your own certificate |
| Certificate source | Platform Key Vault in the Front Door subscription (copy of the certificate in the customer's Key Vault, see section 8) |
| Certificate version | Latest (renewals are picked up automatically) |
| Minimum TLS version | TLS 1.2 |
| Validation | Automatic, because the certificate name matches the domain |

**DNS:** `*.acme.plt.msdhn.com` CNAME → `fde-acme-prd-<hash>.z01.azurefd.net`. A customer on a shared endpoint points to that group's host name, for example `*.contoso.plt.msdhn.com` CNAME → `fde-grp01-prd-<hash>.z01.azurefd.net`.

---

## 5. Route settings

| Setting | Value |
|---|---|
| Name | `rt-acme-prd` |
| Endpoint | `fde-acme-prd` |
| Domains | `*.acme.plt.msdhn.com` only; the endpoint's default `azurefd.net` domain is **not** linked |
| Patterns to match | `/*` |
| Accepted protocols | HTTP and HTTPS |
| Redirect | HTTP → HTTPS |
| Origin group | `og-default-prd` (only reached when no rule matches) |
| Origin path | Empty |
| Forwarding protocol | HTTPS only |
| Caching | Disabled |
| Rule set | `rsacmeprd` |

---

## 6. Rule set (host name → app)

Rule set `rsacmeprd`, evaluated in order:

| Order | Rule | Condition | Action | Stop evaluating |
|---|---|---|---|---|
| 1 | `crm` | Host name equals `crm.acme.plt.msdhn.com` | Route configuration override → origin group `og-acme-crm-prd`, forwarding protocol HTTPS only, caching disabled | Yes |
| 2 | `portal` | Host name equals `portal.acme.plt.msdhn.com` | Route configuration override → origin group `og-acme-portal-prd`, forwarding protocol HTTPS only, caching disabled | Yes |
| 99 | `notfound` | Any request (no earlier match) | URL redirect (302) → `https://www.plt.msdhn.com/not-found` | Yes |

Unknown host names under the wildcard (for example `typo.acme.plt.msdhn.com`) end at the `notfound` rule and never reach an app.

---

## 7. Origin group and origin settings

**Origin group** `og-acme-crm-prd`

| Setting | Value |
|---|---|
| Session affinity | Disabled |
| Health probe | Disabled while there is one origin; with a second origin: `HEAD /health`, HTTPS, 60 seconds |
| Load balancing | Sample size 4, successful samples 3, latency sensitivity 50 ms |

**Origin** `or-acme-crm-prd`

| Setting | Value |
|---|---|
| Origin type | App services |
| Host name | `app-acme-crm-prd.azurewebsites.net` |
| Origin host header | Empty, so `crm.acme.plt.msdhn.com` is passed through |
| HTTPS port | 443 |
| Certificate subject name validation | Enabled |
| Private Link | Enabled; target sub-resource `sites`; region West Europe |
| Private Link approval | On the App Service (post-deployment step) |

**Default origin group** `og-default-prd`: one origin per profile pointing to a small static "not found" site, so a route always has a valid target.

---

## 8. Certificates

| Component | Reads the certificate from |
|---|---|
| App Service | Customer Key Vault (same subscription) |
| Azure Front Door | Platform Key Vault in the Front Door subscription; Front Door only supports Key Vaults in its own subscription |

- An Event Grid subscription on the customer Key Vault (certificate new version created) triggers an automation that copies the new version to the platform Key Vault.
- Front Door's managed identity has **Key Vault Secrets User** on each copied certificate only.
- Platform Key Vault: "Allow trusted Microsoft services" enabled if network access is restricted.
- Certificates: full chain, RSA key (elliptic-curve keys are not supported by Front Door), exportable key.

---

## 9. Limits per Premium profile

| Limit | Value | Consumed by | Effect |
|---|---|---|---|
| Endpoints | 25 | 1 per dedicated customer or per group of up to 10 customers | Not a constraint with grouping |
| Custom domains | 500 | 1 per customer (prod), 3 per customer (non-prod) | Not a constraint |
| Routes | 200 | 1 per customer domain | 200 customers (prod), about 66 (non-prod) |
| Origin groups | 200 | 1 per app per environment, plus 1 default | **About 200 apps (prod), about 66 apps (non-prod)** |
| Rule sets | 200 | 1 per customer domain | Same as routes |
| Rules per rule set | 100 | 1 per app, plus the not-found rule | 99 apps per customer per environment |
| WAF policies | 100 per subscription | 1 per customer | **100 customers per subscription** |
| Profiles | 500 per subscription | 1 per environment group, plus scale-out | Not a constraint |

When a profile approaches 200 origin groups, a second profile is added (`afd-plt-prd-02`, about €290 per month base fee). For non-prod, an alternative is one profile per environment (dev, tst, acc).

---

## Sources

- [Endpoints in Azure Front Door (Microsoft Learn)](https://learn.microsoft.com/azure/frontdoor/endpoint)
- [Front Door limits (Microsoft Docs, GitHub)](https://github.com/MicrosoftDocs/azure-docs/blob/main/includes/front-door-limits.md)
- [Front Door routing limits (Microsoft Docs, GitHub)](https://github.com/MicrosoftDocs/azure-docs/blob/main/articles/frontdoor/front-door-routing-limits.md)
- [Configure HTTPS on a Front Door custom domain (Microsoft Learn)](https://learn.microsoft.com/azure/frontdoor/standard-premium/how-to-configure-https-custom-domain)
- [Use managed identities to access Key Vault certificates (Azure Front Door)](https://learn.microsoft.com/azure/frontdoor/managed-identity)
- [Connect Azure Front Door Premium to an App Service origin with Private Link (Microsoft Learn)](https://learn.microsoft.com/azure/frontdoor/standard-premium/how-to-enable-private-link-web-app)

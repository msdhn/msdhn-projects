# Domain Name Design

## Context

- `msdhn.com` is the organization's root domain; the platform can only use subdomains of it.
- The platform runs on Azure in a hub-spoke topology: every spoke serves one customer, the hub holds central services.
- Each customer can run multiple applications, each on its own App Service.
- Azure Front Door is the public entry point.
- Prod and non-prod must be separated.

> `plt` is used as a placeholder for the platform name throughout this document.

## Base structure

Two sibling subdomains are delegated from `msdhn.com`:

| Environment | Subdomain | DNS zone / subscription |
|---|---|---|
| Prod | `plt.msdhn.com` | Prod zone, prod subscription |
| Non-prod | `plt-np.msdhn.com` | Non-prod zone, non-prod subscription |

Non-prod environments: `dev`, `tst`, `acc`.

**Why siblings instead of nesting non-prod under prod**

- Only two NS delegations are needed from the organization's DNS team; the platform team owns everything below them.
- Prod and non-prod zones live in separate subscriptions with separate RBAC, so non-prod pipelines cannot touch prod records.
- Cookies set on `.plt.msdhn.com` never reach non-prod hosts, and vice versa.

**Reserved names** (cannot be used as customer slugs): `api`, `portal`, `auth`, `admin`, `status`, `www`, `dev`, `tst`, `acc`.

---

## Option A: Per-customer namespace

### Pattern

- Prod: `<app>.<customer>.plt.msdhn.com`
- Non-prod: `<app>.<customer>.<env>.plt-np.msdhn.com`

### Examples

```
Customer acme (3 apps)
  crm.acme.plt.msdhn.com
  portal.acme.plt.msdhn.com
  billing.acme.plt.msdhn.com
  crm.acme.acc.plt-np.msdhn.com
  crm.acme.tst.plt-np.msdhn.com

Customer contoso (2 apps)
  hr.contoso.plt.msdhn.com
  intranet.contoso.plt.msdhn.com
```

### How it's set up

- **Cert:** `*.acme.plt.msdhn.com`, plus one per non-prod environment (`*.acme.acc.plt-np.msdhn.com`), stored in the customer's own Key Vault.
- **Front Door:** one wildcard custom domain per customer and environment, plus a host-name rule per app pointing to that app's origin group.
- **DNS (optional):** a delegated zone per customer (`acme.plt.msdhn.com`).
- **Onboarding a new customer:** cert, Front Door domain, and DNS zone or records.
- **Adding an app:** a host rule and the App Service binding; no new cert.

### Pros

- **Strong isolation:** separate cert, Key Vault and, optionally, DNS zone per customer.
- **Small blast radius:** an expired or compromised cert affects one customer only.
- **Readable hierarchy:** the app sits under the customer, which looks professional to customers.
- **Tenant-wide cookie scope is possible,** for example SSO across one customer's apps.
- **Clean offboarding:** delete the zone, cert and Front Door domain, and nothing is left behind.
- **No naming restrictions:** customer slugs can contain hyphens.
- **Fits customer-managed or BYO certificates** for enterprise customers.

### Cons

- **One cert per customer and environment** to issue, renew and monitor, so automation is mandatory.
- **Cost:** a commercial wildcard per customer runs a few hundred euros per year. ACME (Let's Encrypt) is free but takes engineering effort.
- **Front Door domain limit** per profile (about 100 on Standard, about 500 on Premium). At scale you need extra profiles, each with a base fee and a WAF policy.
- **More onboarding steps,** so more places where provisioning can fail.
- **Long non-prod hostnames,** for example `crm.acme.acc.plt-np.msdhn.com`.

---

## Option B: Flat shared namespace

### Pattern

- Prod: `<customer>-<app>.plt.msdhn.com`
- Non-prod: `<customer>-<app>.<env>.plt-np.msdhn.com`

### Examples

```
Customer acme (3 apps)
  acme-crm.plt.msdhn.com
  acme-portal.plt.msdhn.com
  acme-billing.plt.msdhn.com
  acme-crm.acc.plt-np.msdhn.com

Customer contoso (2 apps)
  contoso-hr.plt.msdhn.com
  contoso-intranet.plt.msdhn.com
```

### How it's set up

- **Cert:** one `*.plt.msdhn.com` for prod and one per non-prod environment, stored in a central platform Key Vault.
- **Front Door:** one wildcard custom domain shared by everyone, plus a host-name rule per app.
- **DNS:** one platform zone; no per-customer records needed.
- **Onboarding a new customer or app:** just a host rule and the App Service binding.

### Pros

- **Minimal operations:** one cert per environment, with nothing to renew per customer.
- **Instant onboarding,** with no DNS or cert work.
- **Scales to thousands** of customers and apps, with no Front Door domain-limit issues.
- **Lowest cost:** one cert, one Front Door domain.
- **Every app is still its own origin,** so browser isolation between apps holds.
- **Shorter hostnames.**

### Cons

- **Large blast radius:** one expired or leaked cert breaks every customer.
- **Weaker isolation:** all customers share one cert and Key Vault, which can fail enterprise or regulatory requirements.
- **No tenant-wide cookies:** cross-app SSO has to go through the identity provider (better practice anyway).
- **Naming rules to enforce:** no hyphens in customer slugs, and a 63-character limit on `customer-app`.
- **Flat and less branded:** the URL doesn't feel like the customer's own space.
- **No per-customer DNS delegation,** and offboarding means cleaning up individual rules and bindings.

---

## When to choose which

| Situation | Option |
|---|---|
| Fewer customers (tens), enterprise or regulated, isolation is a selling point | **A** |
| Many customers (hundreds or more), self-service onboarding, lowest operational cost | **B** |
| Mixed customer base | B by default; A or vanity domains for premium customers |

## Decision: Option A

- Prod: `<app>.<customer>.plt.msdhn.com`
- Non-prod: `<app>.<customer>.<env>.plt-np.msdhn.com`

### Front Door

- One wildcard custom domain per customer and environment (`*.acme.plt.msdhn.com`), using the customer's cert from Key Vault (latest version, for automatic rotation).
- One origin group per app (one App Service per origin group).
- A rule set with one host-name rule per app, overriding the route to the app's origin group.
- Origin host header = public hostname (for example `crm.acme.plt.msdhn.com`).

### App Service (platform configuration only, no application-level settings)

- Custom domain binding for the public hostname.
- Domain verification TXT record `asuid.<hostname>`; the CNAME keeps pointing to Front Door.
- Customer's wildcard cert imported from Key Vault and bound to the hostname. App Service managed certificates do not work here, because the CNAME points to Front Door.
- Access restricted to Front Door: `AzureFrontDoor.Backend` service tag plus an `X-Azure-FDID` header filter (or Private Link with Front Door Premium).
- Because the host header is preserved, redirects, OAuth callbacks, cookies and Easy Auth work without application changes.

### Certificates and Key Vault

- Each customer's cert lives in that customer's own Key Vault.
- **Access is scoped to the certificate, not the vault**, because the vault also holds the customer's app secrets:
  - App Service resource provider: Key Vault Secrets User on the cert.
  - Front Door managed identity: Key Vault Secrets User on the cert.
  - Renewal identity (pipeline or ACME automation): Key Vault Certificates Officer on the cert or vault.
- Key Vault networking: enable "Allow trusted Microsoft services" for App Service cert sync; verify Front Door retrieval against a locked-down vault.
- Ownership must be documented per customer: platform-managed (platform issues and renews) or customer-managed (BYO cert).
- Expiry alerts (Key Vault `CertificateNearExpiry` via Event Grid) go to the platform team.
- With purge protection enabled, use unique or versioned cert names so re-onboarding a customer doesn't clash with a soft-deleted cert.

### Optional

- Delegated DNS zone per customer (`acme.plt.msdhn.com`) for clean offboarding.
- Vanity domains: customers can CNAME their own domain (for example `crm.acme.com`) to their platform hostname; Front Door issues a managed cert for it.

## Watch-outs

- Front Door custom domains per profile are limited (about 100 on Standard, about 500 on Premium); plan an additional profile before reaching the limit.
- One cert per customer and environment: automated renewal and per-cert expiry alerts are mandatory.
- Cert renewal should happen at least two weeks before expiry, so App Service (daily sync) and Front Door (latest version, picked up within days) both catch up.
- Labels are limited to 63 characters; keep customer and app slugs short, lowercase and stable (not legal company names).

# Domain Name Design

## Context

- `msdhn.com` is the organization's root domain; the platform can only use subdomains of it.
- The platform runs on Azure in a hub-spoke topology: every spoke serves one customer, the hub holds central services.
- Each customer can run multiple applications, each on its own App Service.
- Azure Front Door is the public entry point.
- Prod and non-prod must be separated.

> `plt` is used as a placeholder for the platform name throughout this document.

## Scope

This document covers the **production** design. The non-prod design (`dev`, `tst`, `acc`) is handled in a separate section, still to be written; see [Non-prod](#non-prod).

---

## Option A: Per-application subdomain

Every application gets its own subdomain directly under `msdhn.com`. The customer is not part of the hostname and plays no role in the domain design.

### Pattern

- Prod: `<app>.msdhn.com`

### Examples

```
kim.msdhn.com
kom.msdhn.com
```

A customer with several applications simply has several unrelated hostnames; nothing in the name shows which customer an application belongs to.

### How it's set up

- **Cert:** one single-name cert per app (`kim.msdhn.com`), stored in the Key Vault used by Front Door.
- **Front Door:** one custom domain per app attached directly to Front Door. The public hostname is terminated at Front Door only; the App Service does not own a custom domain.
- **DNS:** per app, the `msdhn.com` zone needs the records required by the public hostname that Front Door exposes. In this design, the only DNS validation record required is the Front Door one: `_dnsauth.kim`. There is no `asuid.kim` because the hostname is not bound to App Service.
- **Adding an app:** cert, public DNS record(s), and the Front Door domain/route. There is no App Service custom-domain binding in this model.
- **Onboarding a new customer:** nothing on the domain side until the customer's first app.

| DNS name | Purpose | Required | When it is required |
|---|---|---|---|
| `kim` CNAME | Public hostname points to Front Door | Yes | Always, because Front Door is the public entry point |
| `_dnsauth.kim` TXT | Front Door domain ownership validation | Yes | When attaching `kim.msdhn.com` to Front Door |
| `asuid.kim` TXT | App Service custom-domain verification | No | Only if the public hostname is also bound directly to App Service |


### Pros

- **Shortest, most branded hostnames:** `kim.msdhn.com`.
- **Smallest blast radius:** an expired or compromised cert affects one app only.
- **Hostname is independent of the customer:** renaming a customer or moving an app to another spoke does not change its URL.
- **Simple Front Door model:** one domain, one route, one origin group per app.
- **No wildcard certs,** so a leaked key cannot be used for any other hostname.
- **Clean offboarding per app:** delete the app's records, cert and Front Door domain, and nothing is left behind.

### Cons

- **Every new app needs records in the `msdhn.com` zone,** which the organization's DNS team owns. Without write access for the platform's pipeline this is a manual, cross-team step per app.
- **One cert per app** to issue, renew and monitor, so automation is mandatory.
- **Shared namespace with the whole organization:** app names compete with every other host under `msdhn.com` (`www`, `mail`, …), so each name needs a uniqueness check and an owner.
- **Front Door domain limit** per profile (about 100 on Standard, about 500 on Premium) is consumed per app, not per customer, so it is reached sooner.
- **No tenant-wide cookie scope:** cross-app SSO has to go through the identity provider. An app that sets a cookie on `.msdhn.com` would share it with every site of the organization, so apps must use host-only cookies.
- **No grouping by customer** in DNS, certs or Front Door; the link between an app and its customer lives only in the platform's configuration.

---

## Option B: Flat shared namespace

One subdomain, `plt.msdhn.com`, is delegated from `msdhn.com` to a zone that the platform team owns.

### Pattern

- Prod: `<customer>-<app>.plt.msdhn.com`

### Examples

```
Customer acme (3 apps)
  acme-crm.plt.msdhn.com
  acme-portal.plt.msdhn.com
  acme-billing.plt.msdhn.com

Customer contoso (2 apps)
  contoso-hr.plt.msdhn.com
  contoso-intranet.plt.msdhn.com
```

### How it's set up

- **Cert:** one `*.plt.msdhn.com`, stored in a central platform Key Vault.
- **Front Door:** one wildcard custom domain shared by everyone, plus a host-name rule per app.
- **DNS:** one platform zone; no per-customer records needed.
- **Onboarding a new customer or app:** just a host rule and the App Service binding.

### Pros

- **Minimal operations:** one cert, with nothing to renew per app or customer.
- **Instant onboarding,** with no DNS or cert work and no dependency on the organization's DNS team after the one-time delegation.
- **Scales to thousands** of customers and apps, with no Front Door domain-limit issues.
- **Lowest cost:** one cert, one Front Door domain.
- **Every app is still its own origin,** so browser isolation between apps holds.

### Cons

- **Large blast radius:** one expired or leaked cert breaks every customer.
- **Weaker isolation:** all customers share one cert and Key Vault, which can fail enterprise or regulatory requirements.
- **No tenant-wide cookies:** cross-app SSO has to go through the identity provider (better practice anyway).
- **Naming rules to enforce:** no hyphens in customer slugs, and a 63-character limit on `customer-app`.
- **Longer, less branded hostnames** than Option A.
- **Offboarding** means cleaning up individual rules and bindings.

---

## When to choose which

| Situation | Option |
|---|---|
| Fewer apps (tens), each app is a product in its own right, short branded URLs matter | **A** |
| Many apps (hundreds or more), self-service onboarding, lowest operational cost | **B** |
| Mixed | B by default; A for selected apps |

## Decision: Option A

- Prod: `<app>.msdhn.com` (for example `kim.msdhn.com`, `kom.msdhn.com`)

### Front Door

- One custom domain per app (`kim.msdhn.com`), using the app's cert from Key Vault (latest version, for automatic rotation).
- One origin group per app (one App Service per origin group).
- One route per app, linking the app's custom domain to its origin group.
- Origin host header = public hostname (for example `kim.msdhn.com`).

### App Service (platform configuration only, no public custom domain)

- The App Service does not receive a custom-domain binding for the public hostname.
- No `asuid.<app>` TXT record is required, because the hostname is not assigned to App Service.
- Front Door owns the public custom domain and routes traffic to the App Service origin.
- Access restricted to Front Door: `AzureFrontDoor.Backend` service tag plus an `X-Azure-FDID` header filter (or Private Link with Front Door Premium).
- Because the host header is preserved, redirects, OAuth callbacks, cookies and Easy Auth work without application changes.

### DNS

- All records live in the `msdhn.com` zone for the public hostname that Front Door exposes.
- Required in this design: CNAME `<app>` → Front Door endpoint and TXT `_dnsauth.<app>` for Front Door validation.
- Not required in this design: TXT `asuid.<app>` because the public hostname is not bound to App Service.
- **Open prerequisite:** the platform's pipeline needs a way to create these records without a request to the organization's DNS team per app. Until that is agreed, adding an app is not fully automated.
- App names are unique across the whole of `msdhn.com`; the platform checks a requested name against the existing records before it is assigned.

### Certificates and Key Vault

- Each app's cert lives in the Key Vault of the spoke that hosts the app.
- **Access is scoped to the certificate, not the vault**, because the vault also holds app secrets:
  - App Service resource provider: Key Vault Secrets User on the cert.
  - Front Door managed identity: Key Vault Secrets User on the cert.
  - Renewal identity (pipeline or ACME automation): Key Vault Certificates Officer on the cert or vault.
- Key Vault networking: enable "Allow trusted Microsoft services" for App Service cert sync; verify Front Door retrieval against a locked-down vault.
- Ownership must be documented per app: platform-managed (platform issues and renews) or customer-managed (BYO cert).
- Expiry alerts (Key Vault `CertificateNearExpiry` via Event Grid) go to the platform team.
- With purge protection enabled, use unique or versioned cert names so re-creating an app doesn't clash with a soft-deleted cert.

### Optional

- Vanity domains: customers can CNAME their own domain (for example `crm.acme.com`) to their app's hostname; Front Door issues a managed cert for it.

## Non-prod

To be designed in a separate section. Nothing in the production design above depends on it.

## Watch-outs

- Front Door custom domains per profile are limited (about 100 on Standard, about 500 on Premium), and every app uses one; plan an additional profile before reaching the limit.
- One cert per app: automated renewal and per-cert expiry alerts are mandatory.
- Cert renewal should happen at least two weeks before expiry, so App Service (daily sync) and Front Door (latest version, picked up within days) both catch up.
- Labels are limited to 63 characters; keep app names short, lowercase and stable.
- Apps must not set cookies on `.msdhn.com`; they would be sent to every other site of the organization.

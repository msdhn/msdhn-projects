# Public Exposure of Spoke Web Applications – Option Comparison

**Context:** Hub-spoke topology with one spoke per customer. Each spoke hosts an Azure App Service and Azure Databricks with private endpoints in a subnet of the spoke VNet. The hub hosts Azure Firewall, and all outbound traffic from the spokes is forced through it. Spokes cannot reach each other.

**Options evaluated:**

- **Option 1:** Azure Front Door → Private Link → private Application Gateway (hub) → App Service private endpoint (spoke)
- **Option 2:** Azure Front Door → Private Link → App Service
- **Option 3:** Public Application Gateway → App Service

**Recommendation:** Option 2, unless a requirement exists for hub-owned inbound inspection or Application Gateway-only features (Option 1). Option 3 is the weakest fit for a hub-spoke design with forced tunnelling.

---

## Architecture Diagrams

All three diagrams share the same building blocks:

- Hub VNet and spoke VNet (one per customer), connected by VNet peering
- App Service as a public PaaS service with public network access disabled. It has a private endpoint and a VNet integration (delegated) subnet in the spoke.
- All outbound traffic: App Service → VNet integration → peering → Azure Firewall (hub) → internet
- Front Door (Options 1 and 2) always connects through an AFD-managed private endpoint in a Microsoft-managed network, using Private Link

Legend: solid grey arrows show inbound traffic, dashed grey arrows show Private Link, and amber dashed arrows show outbound traffic. The SVG files must sit in the same folder as this markdown file.

### Option 1: AFD → Private Link → private App Gateway (hub) → App Service PE (spoke)

![Option 1: Front Door to private Application Gateway](option1-afd-private-appgw.svg)

### Option 2: AFD → Private Link → App Service

![Option 2: Front Door directly to App Service](option2-afd-app-service.svg)

### Option 3: Public Application Gateway → App Service

![Option 3: Public Application Gateway](option3-public-appgw.svg)

---

## Pros and Cons

### Option 1: AFD → Private Link → private App Gateway (hub) → App Service PE (spoke)

**Pros**

- Two inspection layers: global WAF at the edge plus regional WAF in the hub
- Central, hub-owned ingress aligns with a hub-controlled governance model
- Application Gateway-only features available: rewrite rules, client mTLS, path-based routing to non-App Service backends
- Application Gateway has no public IP; nothing in the VNets is publicly exposed
- Global anycast edge, CDN caching and DDoS absorption at the edge

**Cons**

- Highest cost: Front Door Premium plus Application Gateway WAF_v2 (roughly double the base ingress cost)
- Most complex: two WAFs to tune (duplicate false positives), two certificate chains, two health-probe layers
- Front Door Private Link to Application Gateway is newer than the App Service integration; some Microsoft docs still mark it as preview and portal support was missing, so GA status and IaC support need verification per region
- Shared hub Application Gateway is a blast radius for all customers and subject to listener and backend limits as customers grow
- Extra hop adds latency
- Application Gateway → spoke private endpoint traffic crosses peering; UDRs on the gateway subnet and firewall rules need care to avoid asymmetric routing

### Option 2: AFD → Private Link → App Service

**Pros**

- Simplest design: fewest components and network hops
- No public exposure of the origin; App Service reachable only via Private Link
- Fits the per-customer spoke model: one Front Door profile, one origin group and WAF policy per customer
- Independent of hub routing, peering and firewall for inbound traffic; no UDR or asymmetric routing issues
- Global edge, CDN, managed certificates and DDoS protection at the edge
- Lowest cost and operational effort of the Front Door options

**Cons**

- Inbound traffic bypasses the hub, Azure Firewall and any regional WAF; Front Door WAF is the only inbound inspection (may conflict with an "all ingress via hub" policy)
- Requires Front Door Premium (Private Link is Premium-only)
- One private endpoint approval per App Service; additional endpoints and approvals if multiple Front Door profiles are used
- Front Door Private Link available only in regions with Availability Zone support
- No client-to-edge mTLS; fewer L7 rewrite and routing options than Application Gateway
- Less control over Front Door edge IPs and behaviour

### Option 3: Public Application Gateway → App Service

**Pros**

- No Front Door cost
- Single, well-documented regional component
- Full Application Gateway feature set (mTLS, rewrites, WebSockets, long timeouts)
- Lower latency for users within a single region
- Traffic stays entirely within the VNets (Application Gateway → App Service private endpoint)

**Cons**

- Public IP inside the network; DDoS Network or IP Protection required to match Front Door edge protection (additional cost)
- Regional only: no global edge, CDN or anycast; multi-region failover needs Traffic Manager or similar
- Conflicts with forced tunnelling: a 0.0.0.0/0 UDR to the firewall on the gateway subnet breaks a public Application Gateway unless routing is designed carefully (e.g. dedicated subnet with an Internet route)
- In the hub it is a shared blast radius for all customers; per spoke it means N gateways and N times the cost
- Scaling, capacity units and certificates are self-managed

---

## Criteria Comparison

| Criterion | Option 1: AFD → PL → private App GW → App Service PE | Option 2: AFD → PL → App Service | Option 3: Public App GW → App Service |
|---|---|---|---|
| Public attack surface in the VNets | None | None | Application Gateway public IP |
| Edge DDoS / global WAF | Yes | Yes | No (regional WAF; DDoS plan needed) |
| Inbound traffic passes through the hub | Yes (Application Gateway) | No | Yes, if gateway is placed in the hub |
| Fit with forced tunnelling | Fine (private gateway) | Best (not affected) | Awkward |
| Customer isolation | Shared gateway | Per origin, per WAF policy | Shared, or N gateways |
| Complexity | High | Low | Medium |
| Approximate base cost | Front Door Premium + App GW WAF_v2 | Front Door Premium | App GW WAF_v2 + DDoS protection |
| Feature maturity | AFD → App GW Private Link GA status to be verified | Mature (GA for years) | Mature |

*Cost figures are relative base costs, excluding traffic and request charges.*

---

## Decision Guidance

| Option | When to choose | Notes |
|---|---|---|
| **Option 2 (preferred)** | App Service is the only component exposed per customer and the Front Door WAF satisfies the security policy | App Service public network access disabled so only the Front Door private endpoint can reach it; outbound traffic continues through the hub firewall via VNet integration and UDR |
| **Option 1** | A hub-owned inbound inspection point is mandated, client mTLS or Application Gateway rewrite rules are needed, or non-App Service backends will be exposed from the spokes later | Plan one Application Gateway per group of customers if listener limits or blast radius become a concern |
| **Option 3** | All users are in a single region, Front Door is to be avoided, and DDoS protection plus forced-tunnelling routing exceptions are acceptable | Weakest fit for a hub-spoke design with forced tunnelling |

---

## Sources

- [Secure your origin with Private Link in Azure Front Door Premium (Microsoft Learn)](https://learn.microsoft.com/azure/frontdoor/private-link)
- [Front Door private link docs (GitHub)](https://github.com/MicrosoftDocs/azure-docs/blob/main/articles/frontdoor/private-link.md)
- [Azure Front Door origin security (Microsoft Learn)](https://learn.microsoft.com/en-us/azure/frontdoor/origin-security)
- [Front Door private link (Azure China docs)](https://docs.azure.cn/en-us/frontdoor/private-link)

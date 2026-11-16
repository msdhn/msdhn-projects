# MSDHN Platform Observability – Design

> **Status:** Brainstorm / draft — decisions marked ✅, open points marked ❓
> **Scope:** Observability of the whole MSDHN platform: Core Hub, Data Hub, customer spokes and capability stacks.

---

## 1. Context

- The MSDHN platform is a hub-and-spoke data analytics and AI platform on Azure, provisioned with Pulumi (Python).
- **Core Hub** (one subscription): Azure Firewall, Private DNS Resolver, shared services.
- **Spoke** (one subscription per customer): the customer's Databricks workspace, databases and other capabilities.
- **Capability stacks**: each capability (Databricks, SQL Database, AI Search, …) is its own Pulumi stack per customer.
- **Many deployers**: several platform teams each build and deploy capabilities with Pulumi, and customers deploy their own applications on their spokes.

## 2. Goals

1. Collect diagnostics from every Azure resource on the platform without relying on each team to remember.
2. Answer one question at any time: **"Is the whole platform healthy? If not, what changed and who owns it?"**
3. Let customers see their own logs and only their own logs.
4. Keep ingestion cost under control and allocate it per customer.
5. Keep everything as code (Pulumi + Azure Policy).

## 3. Key decisions

| # | Decision | Status |
|---|----------|--------|
| D1 | All diagnostic logs go to a **central Log Analytics workspace** | ✅ |
| D2 | Collection is **enforced by Azure Policy** (DeployIfNotExists), not by Pulumi in each team's stack | ✅ |
| D3 | Central observability resources live in a **central management subscription** | ✅ |
| D4 | **Every spoke also has its own Log Analytics workspace** | ✅ (purpose still open, see §5.2) |
| D5 | Central workspace uses access mode **"Use resource or workspace permissions"** (resource-context RBAC) | ✅ proposed |
| D6 | **Azure Workbooks** for dashboards first; Managed Grafana later if needed | ✅ proposed |
| D7 | Dashboards, alerting and wider use of the logs come **later**; collection comes first | ✅ |

## 4. Subscription and resource layout

```
Management subscription (central)
├── rg-observability
│   ├── Central Log Analytics workspace (later: Sentinel?)
│   ├── Workbooks + workbook templates
│   ├── Log search alert rules + action groups
│   ├── Data Collection Rules
│   ├── Azure Monitor Private Link Scope (AMPLS)
│   └── (later) Azure Managed Grafana
└── Managed identity for policy assignments

Management group (MSDHN)
└── Policy assignments → diagnostics to central workspace

Core Hub subscription  ──diagnostics──►  central workspace
Data Hub               ──diagnostics──►  central workspace
Spoke subscription (per customer)
├── Spoke Log Analytics workspace (see §5.2)
└── Resources ──diagnostics (policy)──►  central workspace
```

- Diagnostic settings can write to a workspace in another subscription in the same tenant, so spokes need nothing extra.
- **Pulumi:** a new management stack deploys the workspace, workbooks, alerts and action groups, and **exports the workspace ID**. Spoke and capability stacks read it through a `StackReference`.

## 5. Log collection

### 5.1 Policy-enforced diagnostics (central)

- Assign the built-in initiative **"Enable allLogs category group resource logging for supported resources to Log Analytics"** at the **MSDHN management group**.
- Add a separate policy for **Activity Log** at subscription level ("Configure Azure Activity logs to stream to specified Log Analytics workspace").
- The policy assignment's managed identity needs **Monitoring Contributor** and **Log Analytics Contributor** on the management group / central workspace.
- Run **remediation tasks** for resources that already exist. New resources get their setting roughly 10–15 minutes after deployment.
- Metrics are not collected by default; Azure Monitor metrics / managed Prometheus are enough for now. ❓
- Network logs: VNet flow logs and Azure Firewall logs also go to the central workspace.

**Rules for teams**
- Pulumi stacks **must not define diagnostic settings** themselves. The policy owns them; defining them in Pulumi as well causes duplicates or drift. A resource allows at most 5 diagnostic settings.
- **Databricks managed resource group**: deny assignments can block the policy there. Target the Databricks workspace resource itself and use Databricks **system tables** for job, audit and billing data.
- **AMPLS does not cover diagnostic settings**: they go over the Azure backbone. AMPLS covers agents, App Insights and queries.

### 5.2 Spoke Log Analytics workspace ❓

Every spoke has its own workspace. Its purpose still needs to be decided:

- **Option A – clean split (recommended):**
  - Central workspace: all resource diagnostics, Activity Log, network and security logs (platform-owned).
  - Spoke workspace: customer workload telemetry only — App Insights, custom application logs, AI app traces.
  - Nothing lands in both. Use cross-workspace KQL when both are needed.
- **Option B – diagnostics in both:**
  - Two diagnostic settings per resource and two policy assignments (management-group level → central; spoke subscription → spoke workspace).
  - Each assignment needs a **distinct diagnostic setting name**, and the policy `existenceCondition` must match on the workspace ID.
  - Ingestion is paid twice, so send only a reduced category set to one side.

If the spoke workspace exists only so customers can see their logs, resource-context RBAC on the central workspace (§6) already gives them that.

## 6. Access model (multi-customer)

- Central workspace access mode: **resource or workspace permissions**.
- **Platform team:** workspace-level read on the central workspace.
- **Customer teams:** no access on the central workspace itself. They query their own resources' logs through **resource-context** queries, scoped by their RBAC on their spoke subscription.
- **Workbooks in the management subscription:** queries use **resource type = Subscription** pointing at the spoke subscription, not the workspace. Customers need:
  - **Workbook Reader** on the workbook (or its resource group)
  - **Reader** on their own spoke subscription
- **Limitation:** resource-context only covers tables with `_ResourceId`. Custom logs without a resource ID are not visible to customers.
- ❓ Data sensitivity: some logs contain customer content (for example Databricks SQL query text). Check whether customer agreements allow this in a shared workspace.

## 7. Visualization

| | Azure Workbooks | Azure Managed Grafana |
|---|---|---|
| Cost | Free | Per instance + per active user |
| Access | Azure RBAC; resource-context works | Separate Entra roles on Grafana |
| Data sources | Log Analytics, Resource Graph, metrics, ARM, ADX | Many, including Prometheus and other clouds |
| As code | JSON in `azure-native.insights.Workbook` | Grafana Pulumi provider |
| Use for | Customer self-service, per-spoke views | Platform operations across sources |

**Plan**
- One shared **"Spoke Health" workbook** in the management subscription with a subscription parameter. Customers pick their own subscription and see only their own data.
- Workbook JSON lives in the repo and is deployed by Pulumi. The repo is the source of truth; portal edits are redeployed over.
- Add Grafana once Prometheus metrics or an operations view across sources is needed.

## 8. Platform health with many deployers

Many teams deploy capabilities and customers deploy apps, so health is built from **standard contracts** that roll up into one view, not by watching each deployment.

### 8.1 Health layers

| Layer | Owner | Examples |
|---|---|---|
| Foundation | Platform team | Firewall, DNS, Core Hub / Data Hub connectivity, identity, central log ingestion |
| Shared capabilities | Each capability team | Databricks, SQL Database, AI Search, Key Vault, storage |
| Spoke landing zone | Platform team | Spoke → hub path, private endpoints, policy compliance |
| Customer apps | Customer | Their app; the platform only watches guardrails and platform-caused impact |

### 8.2 Building blocks

1. **Automatic tagging (Pulumi)**
   - A shared stack transform adds `owner`, `capability`, `pulumi-stack`, `spoke` (and `environment`) to every resource.
   - Azure Policy **denies** resources without these tags, which also covers customer deployments.
2. **Deployment events**
   - Each pipeline (teams and customers) posts one event — stack, team, spoke, version, result, timestamp — to a custom table (`PlatformDeployments_CL`) through the **Logs Ingestion API** and a DCR.
   - Activity Log is the fallback for anything that skips this.
   - Workbooks overlay deployment events on health charts ("red started right after stack X deployed").
3. **Health function per capability**
   - Each capability team publishes a saved KQL function in the central workspace, for example `Health_Databricks()`.
   - Every function returns the same columns: `Capability, Spoke, Status, Reason, TimeGenerated`.
   - A **platform health workbook** unions all functions into a capability × spoke grid (green / amber / red).
4. **Synthetic checks**
   - **Network Watcher Connection Monitor** from each spoke to DNS, the firewall, key private endpoints and other platforms such as `Team_Airflow`.
   - **App Insights standard tests** on platform endpoints.
5. **Drift and guardrails**
   - The Azure Policy compliance score per spoke is a health signal.
   - Scheduled `pulumi preview` / drift detection per stack, with the result logged.
   - **Pulumi CrossGuard** policy packs in every team's CI.
   - Spoke teams and customers get no RBAC on hub resources; hub stacks are separate; critical hub resources get resource locks.
6. **Ownership-based alert routing**
   - Alerts use the `owner` / `capability` tag to pick the action group.

**Start with:** building blocks 1 + 2, then one health function per capability.

## 9. Cost control

- Ingestion is the main cost driver.
- Move high-volume tables (firewall, flow logs, verbose diagnostics) to the **Basic / Auxiliary** table plans.
- Filter at the Data Collection Rule where possible.
- Set **retention per table**; consider a commitment tier once volume is known.
- Chargeback per customer: `_BilledSize` grouped by subscription from `_ResourceId`.

## 10. Later (deferred)

- **Alerting:** log search alerts (Databricks job failures, Key Vault denies, firewall denies, Azure OpenAI 429s); Activity Log alerts (role assignments, policy exemptions, deletions, NSG/UDR changes); action groups to Teams / email / ITSM.
- **Security:** Microsoft Sentinel on the central workspace, or forwarding to the organization's central SOC ❓.
- **Compliance retention:** long-term retention / archive tier, or export to storage; lock down log deletion and purge.
- **Automation:** alerts triggering Logic Apps / Functions; export logs to ADLS for analysis in Databricks.
- **AI observability:** token usage, latency and tracing for AI apps (OpenTelemetry).

## 11. Open questions

1. What is the purpose of the spoke Log Analytics workspace — Option A or B (§5.2)?
2. Does a central SOC expect these logs, or is security monitoring the platform team's job?
3. Which metrics, if any, should go to Log Analytics?
4. May customer-content logs (for example query text) be stored in a shared workspace?
5. Retention requirements (regulatory) per log category?
6. Where does the management subscription sit in the management group hierarchy, and who owns it?

## 12. Next steps

1. Decide on §5.2 and §11.
2. Create the management Pulumi project (`projects/core/management/project`) with an `observability` package (`base.py`, `azure.py`, `factory.py`): central workspace, AMPLS, exports.
3. Policy assignments at management-group level + remediation.
4. Shared Pulumi tagging transform + tag policy.
5. Deployment event table (DCR + custom table) and pipeline step.
6. First "Spoke Health" workbook.

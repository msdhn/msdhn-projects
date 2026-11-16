# Spike: MSDHN Platform Observability

> **Related design:** [design.md](./design.md)
> **Timebox:** 1–2 sprints
> **Environment:** sandbox subscription(s) and a test management group

---

## Goal

Work out and prove the observability approach for the whole MSDHN platform across four main topics:

- **Log collection** to the central Log Analytics workspace
- **Workbooks / dashboards**, central and per spoke
- **Alerts** on the collected logs
- **Health check implementation** for the platform

**Approach:** build a proof of concept manually in the **Azure portal**, in a sandbox management group with a management subscription and at least two spoke subscriptions. Capture all configuration (resource JSON, policy parameters, KQL, workbook JSON, alert settings) and findings along the way.

**Outcome:**

- A **technical design document** that:
  - records the decisions for each point to analyze
  - describes every component with its configuration, RBAC and dependencies
  - maps each component to the Pulumi project, stack and component that will implement it
  - includes PoC findings, cost estimate and open issues
- **User stories** for implementing the design as infrastructure as code, created in the backlog with:
  - a description and acceptance criteria
  - a reference to the matching section of the technical design document
  - dependencies between stories
  - a size estimate

The spike does not build the production solution.

---

## Points to analyze

### Before you start
- Which landing zone policies, enterprise workspace or SIEM are already enforced?
- Environments: separate setup for prod and non-prod?
- Management subscription: where it sits in the management group hierarchy, and who owns it.

### Log collection
- Policy-enforced diagnostics to the central workspace: does it work across subscriptions, how long does it take, does remediation work, and does the Activity Log policy work?
- Pulumi coexistence: no drift with diagnostic settings created by the policy.
- Databricks managed resource group, and Databricks system tables.
- What the spoke workspace is for: only customer workload logs, or diagnostics in both workspaces.
- AMPLS and private DNS in the Core Hub, and the impact on peered and other platforms.
- Customer app telemetry (App Insights): which workspace it goes to, and whether ingestion is private.
- Retention, customer-content logs, and which metrics to collect.
- Cost: ingestion volume, Basic/Auxiliary tables, daily cap, chargeback per spoke.

### Workbooks and dashboards
- Workbooks only, or Grafana as well.
- Customer isolation: resource-context access in a shared workbook in the management subscription.
- Capability team access across spokes (granular RBAC).
- Content of the central view and the spoke view, deployed with Pulumi.

### Alerts
- First alert set, severities and notification channels.
- Routing to the owning team by tag, and one rule covering all spokes.
- Service Health and Resource Health alerts.
- Operating model: who responds, runbook per alert, testing alerts.
- Customer notifications: whether customers get alerts about their own spoke, and through which action group.

### Health check
- Health layers and the definition of green, amber and red.
- Tag standard, applied by a Pulumi transform and enforced by a deny policy.
- Deployment events table, with a pipeline step for platform teams and customers.
- Health query contract per capability, rolled up in one workbook.
- Synthetic checks (Connection Monitor) and drift detection.

### Cross-cutting
- Monitoring the monitoring: ingestion gaps and policy compliance.
- Spoke onboarding automation for all of the above.
- Protecting the workspace: locks, and who can delete or purge data.

> **Priority:** analyze the existing landing zone policies, the environment split, and AMPLS with private DNS first, because they could change the rest of the design.

---

## Out of scope

- Microsoft Sentinel / SOC integration
- Long-term compliance retention and archive
- AI observability (token usage, tracing)
- Automation on alerts (Logic Apps / Functions)

---

## Acceptance criteria

### 1. Working proof of concept

The PoC runs in the sandbox and is demonstrated end to end:

- **Log collection:** a new resource in a spoke subscription sends diagnostics to the central workspace through policy, without Pulumi changes.
- **Workbooks:** a customer identity sees only its own spoke's data in a shared workbook; the platform team sees all spokes.
- **Alerts:** at least one alert fires and reaches the owning team through tag-based routing.
- **Health:** the health workbook shows the status per capability and spoke, with recent deployments.

### 2. Detailed technical design

A technical design document, reviewed by the team, that:

- records a decision for every point to analyze (or links to an ADR)
- describes every component with its configuration, naming, RBAC and dependencies
- maps each component to the Pulumi project, stack and component that will implement it
- includes the KQL, workbook JSON and alert definitions from the PoC
- includes PoC findings, cost estimate and open issues
- is detailed enough to implement as infrastructure as code without repeating the PoC

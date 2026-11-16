# Platform Observability Spike

## Goal

Work out how to observe the whole MSDHN platform (Core Hub, Data Hub, customer spokes and capability stacks) across four topics:

- **Log collection** to a central Log Analytics workspace in the management subscription
- **Workbooks / dashboards**, central and per spoke
- **Alerts** on the collected logs
- **Health check** for the whole platform, with many teams and customers deploying

**Approach:** build a proof of concept manually in the **Azure portal**, in a sandbox management group with a management subscription and at least two spoke subscriptions. Capture all configuration (resource JSON, policy parameters, KQL, workbook JSON, alert settings) and findings along the way.

**Outcome:** a **technical design document** that:

- records the decisions for each point below
- describes every component with its configuration, RBAC and dependencies
- maps each component to the Pulumi project, stack and component that will implement it
- includes PoC findings, cost estimate and open issues

The design document is the input for implementing the solution as infrastructure as code. The spike does not build the production solution.

## Log collection

- Policy-enforced diagnostics to the central workspace: does it work across subscriptions, how long does it take, does remediation work, and does the Activity Log policy work?
- Pulumi coexistence: no drift with diagnostic settings created by the policy.
- Databricks managed resource group, and Databricks system tables.
- What the spoke workspace is for: only customer workload logs, or diagnostics in both workspaces.
- AMPLS and private DNS in the Core Hub, and the impact on peered and other platforms.
- Customer app telemetry (App Insights): which workspace it goes to, and whether ingestion is private.
- Retention, customer-content logs, and which metrics to collect.
- Cost: ingestion volume, Basic/Auxiliary tables, daily cap, chargeback per spoke.

## Workbooks and dashboards

- Workbooks only, or Grafana as well.
- Customer isolation: resource-context access in a shared workbook in the management subscription.
- Capability team access across spokes (granular RBAC).
- Content of the central view and the spoke view, deployed with Pulumi.

## Alerts

- First alert set, severities and notification channels.
- Routing to the owning team by tag, and one rule covering all spokes.
- Service Health and Resource Health alerts.
- Operating model: who responds, runbook per alert, testing alerts.

## Health check

- Health layers and the definition of green, amber and red.
- Tag standard, applied by a Pulumi transform and enforced by a deny policy.
- Deployment events table, with a pipeline step for platform teams and customers.
- Health query contract per capability, rolled up in one workbook.
- Synthetic checks (Connection Monitor) and drift detection.

## Cross-cutting

- Monitoring the monitoring: ingestion gaps and policy compliance.
- Spoke onboarding automation for all of the above.
- Protecting the workspace: locks, and who can delete or purge data.

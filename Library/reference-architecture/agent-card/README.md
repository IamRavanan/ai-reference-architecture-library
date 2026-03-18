# FSI Agent Card Schema


## Table of Contents

- [Overview](#overview)
- [What is an Agent Card?](#what-is-an-agent-card)
- [Why a Financial Institution Requires More Than the Standard Agent Card](#why-a-financial-institution-requires-more-than-the-standard-agent-card)
- [Agent Autonomy Levels](#agent-autonomy-levels)
- [Schema Structure](#schema-structure)
- [Agent Card and Registry: Where Each Field Belongs](#agent-card-and-registry-where-each-field-belongs)
  - [Why the FSI Agent Card Carries Governance Fields](#why-the-fsi-agent-card-carries-governance-fields)
  - [The Two-Layer Model: Card and Registry](#the-two-layer-model-card-and-registry)
  - [Agent Onboarding Process](#agent-onboarding-process)
  - [Where Should the Agent Card Live?](#where-should-the-agent-card-live)
- [Field Reference](#field-reference)
  - [Core Fields (Standard A2A)](#core-fields-standard-a2a)
  - [A Note on securitySchemes and security](#a-note-on-securityschemes-and-security)
  - [Provider Object](#provider-object)
  - [Skills Object](#skills-object)
  - [Governance Block](#governance-block)
  - [Data Handling Block](#data-handling-block)
  - [Compliance Block](#compliance-block)
  - [Agent Security Block](#agent-security-block)
  - [Dependencies Block](#dependencies-block)
- [Production Registration Rules](#production-registration-rules)
- [Best Practices](#best-practices)
- [Suggested Extensions](#suggested-extensions)
- [Regulatory Mapping](#regulatory-mapping)
- [File Reference](#file-reference)
- [References](#references)
- [Glossary](#glossary)

---

## Overview

This document defines the **FSI Agent Card**: an extended version of the Agent2Agent (A2A) Protocol Agent Card specification, adapted for AI agents deployed within financial institutions.

The FSI Agent Card provides a standardized, machine-readable format through which agents can be discovered, understood, and governed in a manner that satisfies the requirements of regulators, model risk managers, compliance functions, and security operations teams. It extends the standard A2A Agent Card with four governance-oriented blocks covering agent oversight, data handling, regulatory compliance, and operational security.

The security posture fields in this schema are grounded in the MAESTRO threat model for the multi-agent reference architecture (`tm_ma_ref_arch_mar_2026.md`), which identifies 48 threats across the full architectural stack. The `agentSecurity` and `dependencies` blocks in particular map directly to controls for the highest-risk threat vectors identified in that model, including indirect prompt injection (T15), excessive agency (T17), MCP capability escalation (T37), and agent-to-agent impersonation (T18).

> **Grounding in the A2A Protocol.** The A2A Protocol is an open standard originally developed by Google and subsequently donated to the Linux Foundation. It defines how AI agents communicate with one another in a decentralised, interoperable manner. The Agent Card is a foundational primitive of the A2A Protocol: a JSON document served at a well-known URL that functions as the machine-readable identity document of an agent.
>
> References: [A2A Protocol Specification](https://a2a-protocol.org/specification/) and [Google Cloud, Vertex AI Agent Engine: Develop an Agent2Agent Agent](https://docs.cloud.google.com/agent-builder/agent-engine/develop/a2a).

---

## What is an Agent Card?

An Agent Card is a JSON document published by an agent that describes its identity, capabilities, authentication requirements, and supported skills. It is the primary mechanism through which agents are discovered and understood in the A2A Protocol.

As defined in the [A2A Protocol specification](https://a2a-protocol.org/specification/), the Agent Card conveys the agent's identity, the skills it can perform, the content types it accepts and produces, and the authentication mechanisms a client must satisfy before initiating a task.

An Agent Card is served at a well-known path on the agent's domain:

```
GET /.well-known/agent-card.json
```

Orchestrators, registries, and peer agents retrieve this document before delegating any task. In doing so, the Agent Card serves four purposes in the A2A architecture.

**Automatic Discovery.** Agents and registries can locate and index agents without manual configuration or bilateral agreements.

**Authentication Negotiation.** Clients determine the required authentication scheme before attempting to connect, avoiding failed calls and unnecessary credential exposure.

**Capability Verification.** Orchestrating agents confirm what a remote agent can do before delegating a sub-task, which is a prerequisite for safe multi-agent composition at A3 and above.

**Protocol Interoperability.** Agents built on different frameworks, such as LangGraph, CrewAI, Semantic Kernel, or custom implementations, communicate through a shared contract rather than proprietary interfaces.


[↑ Back to contents](#table-of-contents)

---

## Why a Financial Institution Requires More Than the Standard Agent Card

The standard A2A Agent Card answers three questions: what the agent can do, how to communicate with it, and who built it. Those answers are sufficient for general software engineering purposes. They are not sufficient for a regulated financial institution.

Regulators, model risk managers, and internal audit functions require answers to a considerably broader set of questions before an agent may be approved for use in a production environment.

| Regulatory or Governance Question | Standard Agent Card | FSI Agent Card | FSI Schema Field |
|:---|:---:|:---:|:---|
| What level of autonomy does this agent operate at? | No | Yes | `governance.autonomyLevel` |
| Who is the accountable business owner? | No | Yes | `provider.businessOwner` |
| What model risk tier applies under SR 11-7? | No | Yes | `governance.modelRiskTier` |
| Is there a human in the loop, and at what points? | No | Yes | `governance.humanOversightModel` |
| What actions is this agent permitted to take? | No | Yes | `governance.approvedActionList` |
| Which other agents may it delegate to? | No | Yes | `governance.approvedAgentRegistry` |
| Has it been registered in the model inventory? | No | Yes | `governance.modelRisk.modelInventoryId` |
| When was it last validated by the model risk team? | No | Yes | `governance.modelRisk.lastValidationDate` |
| What data domains is it  authorized to access? | No | Yes | `dataHandling.permittedDataDomains` |
| Where is data permitted to reside? | No | Yes | `dataHandling.dataResidency` |
| Which regulations apply, and which specific provisions? | No | Yes | `compliance.applicableRegulations` |
| Is there an immutable audit trail? | No | Yes | `compliance.auditTrail` |
| Can decisions be explained after the fact? | No | Yes | `compliance.explainability` |
| Can the agent be halted immediately? | No | Yes | `compliance.incidentResponse.killSwitchEndpoint` |
| Is the Agent Card signed and verifiable? | No | Yes | `agentSecurity.cardSigning` |
| Are prompt injection controls in place? | No | Yes | `agentSecurity.promptInjectionControls` |
| Is the agent endpoint network-restricted? | No | Yes | `agentSecurity.networkAccessControl` |


[↑ Back to contents](#table-of-contents)

---

## Agent Autonomy Levels

The FSI Agent Card incorporates the **FINOS AI Reference Architecture Agent Autonomy Taxonomy**, which classifies agents on a scale from A0 to A4. The full specification is maintained at the [FINOS AI Reference Architecture Library](https://github.com/finos-labs/ai-reference-architecture-library/blob/main/Library/reference-architecture/agent-autonomy/agent_autonomy_levels.md).

A central principle of this taxonomy is that autonomy level is a design decision, not an intrinsic property of the underlying model. The same model may operate at different autonomy levels depending on how the surrounding system constrains its actions and enforces human oversight.

| Level | Name | Human Role | Action Scope | Regulatory Risk Tier |
|:---:|:---|:---|:---|:---:|
| A0 | No Agency | Executes all actions manually | None; the agent produces output only | Minimal |
| A1 | Tool-Calling Agent | Approves every action before execution | Single-step, pre-approved tools only | Low |
| A2 | Workflow / Playbook Agent | Reviews the agent's work at defined checkpoints | Fixed, pre-approved action list | Moderate |
| A3 | Goal-Directed Agent | Sets the objective and reviews at agreed milestones | Dynamic selection within approved limits | High |
| A4 | Self-Directing Agent | Sets the initial objective; receives exception alerts only | Self-determined within defined policy bounds | Critical |

The `governance.autonomyLevel` field must be consistent with `governance.humanOversightModel` and, for A2 and above, `governance.approvedActionList`. Inconsistency between these fields is a validation error.


[↑ Back to contents](#table-of-contents)

---

## Schema Structure

The FSI Agent Card extends the standard A2A Agent Card with four additional top-level blocks.

```
FSI Agent Card
|
+-- Standard A2A Fields
|   +-- name, description, url, version
|   +-- provider              (extended with business ownership fields)
|   +-- capabilities
|   +-- defaultInputModes / defaultOutputModes
|   +-- securitySchemes       (OpenAPI 3.0 Security Scheme Object, reproduced verbatim)
|   +-- security              (OpenAPI 3.0 Security Requirement Object, reproduced verbatim)
|   +-- skills                (extended with requiresHumanApproval and specReference)
|
+-- governance                (FSI extension)
|   +-- autonomyLevel         A0 through A4
|   +-- autonomyLevelJustification
|   +-- modelRiskTier
|   +-- humanOversightModel
|   +-- approvedActionList
|   +-- approvedAgentRegistry
|   +-- escalationContacts
|   +-- changeApprovalReference
|   +-- modelRisk             (modelInventoryId, lastValidationDate, nextReviewDate)
|
+-- dataHandling              (FSI extension)
|   +-- dataClassification
|   +-- permittedDataDomains
|   +-- dataResidency
|   +-- retentionPolicy       (inputRetentionDays, outputRetentionDays, policyReference)
|   +-- piiHandling
|
+-- compliance                (FSI extension)
|   +-- applicableRegulations
|   +-- auditTrail            (enabled, immutable, retentionDays, reference)
|   +-- explainability
|   +-- incidentResponse
|
+-- agentSecurity             (FSI extension)
|   +-- cardSigning
|   +-- promptInjectionControls
|   +-- inputOutputValidation
|   +-- networkAccessControl
|   +-- agentIdentityVerification
|   +-- rateLimiting
|
+-- dependencies              (FSI extension)
|   +-- mcpServers            (each MCP server connection, with data domain scope and approval reference)
|   +-- agentSkills           (each Agent Skills package, with source, executable code flag, and review reference)
|   +-- additionalProtocols   (extensible array for future protocols beyond A2A and MCP)
|
+-- extensions                (free-form; institution-specific fields)
```


[↑ Back to contents](#table-of-contents)

---

## Agent Card and Registry: Where Each Field Belongs

### Why the FSI Agent Card Carries Governance Fields

A common and reasonable question when reviewing this schema is: why do governance record fields such as `modelRisk.lastValidationDate` or `provider.businessOwner` appear in the Agent Card at all? Those fields live in HR systems, model inventories, and risk registers. Why duplicate them here?

The answer is that the Agent Card is not a record-keeping system. It is a **self-contained trust signal** consumed at the moment a decision is being made. An orchestrator delegating a task, a gateway enforcing a policy, or a CI/CD pipeline approving a promotion cannot call multiple internal systems to reconstruct the full picture before acting. The card needs to be useful in isolation.

The table below explains why each FSI extension field belongs in the card. It is honest about how each field can be used.

**How to read the "How it is used" column:**

- **Runtime decision:** An orchestrator or gateway can read this field from the card at call time and make an automated trust or routing decision from its value alone.
- **Deployment gate:** A CI/CD pipeline or onboarding checklist can check this field during promotion and block or flag the deployment based on its value.
- **Provisioning:** A platform or system reads this field once at setup time to configure itself (log storage, monitoring thresholds, DLP rules). It does not need to be read again on every call.
- **Informational:** This field declares a fact (who owns this agent, which regulations apply, what legal basis governs data processing). Automated enforcement requires separate systems configured independently. The card provides the declaration; it does not substitute for the governance process.

Many fields serve more than one purpose. Where that is the case, all purposes are listed.

> **Important:** Whether any of these fields produces an automated control in your environment depends entirely on what your orchestration platform, gateway, and CI/CD tooling support. The table describes what is *possible* given the field's content. It does not imply that every institution will or should implement every control listed.

| Field | Why this field belongs in the card | How it is used |
|:---|:---|:---|
| `governance.autonomyLevel` | An orchestrator routing a task to this agent needs to know its autonomy ceiling before delegating. A gateway cannot safely route a task requiring A1 oversight to an A4 agent without this value. | **Runtime decision** and **Deployment gate**: Orchestrators and gateways can enforce maximum autonomy level per task class. Promotion gates can block agents above a permitted ceiling for a given environment. |
| `governance.autonomyLevelJustification` | A reviewer challenging the assigned level needs this to evaluate whether the implementation actually enforces what the level claims. It is not enough to assert A2; the reasoning must be present. | **Informational**: Used by model risk teams, governance reviewers, and auditors during assessment. Not machine-enforceable from the card alone. |
| `governance.modelRiskTier` | Tier determines the intensity of validation, monitoring, and change management the institution must apply. Callers in environments that enforce tier-based access policies need this value. | **Runtime decision** (in environments with tier-based routing policies) and **Informational** (for risk and audit teams reading the card). Deployment gates can require a corresponding model inventory entry. |
| `governance.humanOversightModel` | Callers and orchestrators must understand the oversight pattern to configure their own human-in-the-loop controls correctly before integrating with this agent. | **Runtime decision** and **Deployment gate**: Human oversight platforms configure checkpoint workflows from this value. Deployment gates validate consistency with `autonomyLevel`. |
| `governance.approvedActionList` | Without a machine-readable scope boundary, no external system can verify that the agent is acting within its  authorized remit. | **Runtime decision** and **Deployment gate**: Orchestrators can validate proposed actions against this list before delegation. Gates verify it is present and non-empty for A2 and above. |
| `governance.approvedAgentRegistry` | In multi-agent architectures, delegation decisions must be checked against a known-good list. Querying a separate registry at delegation time introduces latency and a dependency that may be unavailable. | **Runtime decision** and **Deployment gate**: Orchestrators verify delegation targets against this list. Gates verify each entry has a formal approval reference for A3 and above. |
| `governance.escalationContacts` | When an incident occurs, the time to locate the right contact must be seconds, not minutes. The card must carry this, not just a registry that may be unreachable or require separate authentication. | **Provisioning**: SIEM and alerting platforms configure routing from this at setup and **Informational**: consumed directly by humans during incidents. |
| `governance.changeApprovalReference` | Links the deployed version to its approved change record. Without this, there is no way to verify from the card alone that the agent was properly promoted. | **Deployment gate**: Verified as present before production promotion. **Informational** for audit. |
| `governance.modelRisk.modelInventoryId` | Connects this agent to its SR 11-7 validation record. An orchestrator enforcing model risk policy must know whether a valid inventory entry exists. | **Deployment gate**: Must be populated before any production deployment this is the single hardest gate in the schema. **Provisioning**: Monitoring platforms link performance telemetry to the inventory record using this ID. |
| `governance.modelRisk.lastValidationDate` | A stale validation date is a material risk signal that can be read directly from the card, without querying the model inventory. | **Runtime decision** (orchestrators with a maximum validation age policy can decline to delegate) and **Deployment gate** (gates can enforce a minimum validation recency requirement). |
| `governance.modelRisk.nextReviewDate` | Allows monitoring platforms and governance dashboards to track approaching review deadlines without querying the model inventory directly. | **Provisioning**: Monitoring platforms schedule review reminders from this value. **Informational** for governance teams. Not a blocking deployment gate on its own. |
| `dataHandling.dataClassification` | The highest data classification this agent can process. Callers must know this to apply the correct data segregation controls at routing time. | **Runtime decision** and **Deployment gate**: Orchestrators enforce classification-compatible routing. Gates verify consistency with `permittedDataDomains`. |
| `dataHandling.permittedDataDomains` | The definitive list of data domains this agent is  authorized to access. Without this, no system can verify that data being passed to the agent is within its approved scope. | **Runtime decision**: Orchestrators verify domain compatibility before passing data. **Deployment gate**: Gates validate the declared domains are consistent with the data handling approval. **Provisioning**: DLP tools configure scanning rules from this list. |
| `dataHandling.dataResidency.permittedRegions` | Data sovereignty obligations vary by jurisdiction. Infrastructure automation needs the permitted regions at provisioning time; runtime routing may also use it where agents are deployed across multiple regions. | **Provisioning**: Cloud infrastructure and traffic routing systems enforce region placement at setup. **Informational** for compliance review. Runtime enforcement depends on whether your orchestration platform supports region-aware routing. |
| `dataHandling.dataResidency.restrictedRegions` | Explicit prohibitions are as important as permissions. Negative controls must be machine-readable to be enforceable. | **Provisioning** and **Informational**: Used to configure network and data policies at setup time. Same caveats as `permittedRegions` for runtime use. |
| `dataHandling.retentionPolicy` | The data platform storing agent inputs and outputs must be configured with the correct retention periods. Having this in the card means the platform can read it at provisioning time. | **Provisioning**: Storage lifecycle automation reads this at setup. **Informational** for data governance and compliance review. Not enforced at call time. |
| `dataHandling.piiHandling.piiTypesHandled` | A generic "handles PII" flag is insufficient for GDPR Article 30 records of processing. The specific types determine what subject rights apply and what downstream handling is required. | **Provisioning**: Privacy engineering platforms configure type-specific controls (masking, encryption, access logging) from this list at setup. **Informational** for compliance. |
| `dataHandling.piiHandling.legalBasis` | The legal basis for processing determines which conditions must be met and which data subject rights apply. This must be declared to satisfy GDPR Article 6 obligations. | **Informational**: Consumed by compliance and legal teams. The declaration is the control; enforcement requires the institution's broader data governance programme. |
| `compliance.applicableRegulations` | Callers and governance teams need to know which obligations apply without querying a separate compliance system. This also drives configuration of regulation-specific monitoring. | **Provisioning**: Compliance monitoring platforms configure regulation-specific checks from this list. **Informational**: Consumed by audit and legal teams. **Deployment gate**: Gates require at least one entry. |
| `compliance.auditTrail.enabled` | Audit capability is a prerequisite for regulated deployments. Callers that require a verifiable audit trail must be able to confirm it is active from the card. | **Deployment gate**: Must be true for all production deployments. **Provisioning**: SIEM platforms verify the audit stream before accepting events. |
| `compliance.auditTrail.immutable` | A write-once audit log is a specific regulatory requirement distinct from simply having logging enabled. A mutable log provides no forensic guarantee. | **Deployment gate**: Must be true for A1 and above. **Provisioning**: WORM storage configuration is verified at setup. |
| `compliance.auditTrail.retentionDays` | The log storage platform must be configured with the correct retention period. Regulatory minimums vary and this value may differ from the input/output retention policy. | **Provisioning**: Log storage lifecycle policies are configured from this value at setup. **Informational** for compliance review. |
| `compliance.explainability.supported` | The EU AI Act and SR 11-7 require that decisions made by high-risk AI systems can be explained to qualified parties. An orchestrator routing a high-stakes decision can check this before delegating. | **Runtime decision** (in environments that enforce explainability requirements per task class). **Informational** for model risk and audit review. |
| `compliance.explainability.method` | The method determines what artefacts are produced and how to query them. Systems that consume explanations need to know the method to configure their queries. | **Provisioning**: Explainability tooling configures capture from this value. **Informational** if no automated explainability platform is in place. |
| `compliance.incidentResponse.killSwitchEndpoint` | In a live incident, locating the kill switch must take seconds. It must be in the card itself reachable without querying a registry that may be unavailable or slow during an incident. | **Runtime** (incident response automation and SOAR playbooks call this endpoint directly during containment). **Deployment gate**: Required for A3 and above; the endpoint must be verified as reachable and agent-independent before promotion. |
| `compliance.incidentResponse.incidentContactEmail` | Alert routing systems need the correct team contact at the moment an event fires, not after a registry lookup. | **Provisioning**: SIEM alert routing is configured from this address at setup. **Deployment gate**: Verified as a shared team inbox, not an individual email. |
| `compliance.incidentResponse.planReference` | Incident responders need the plan reference at the start of an incident, not as a search exercise. | **Informational**: Surfaced in incident tickets and runbooks. **Deployment gate**: Verified as present and resolving to a reachable document before production promotion. |
| `agentSecurity.cardSigning` | A caller in a zero-trust environment must be able to verify the card has not been tampered with in transit before trusting any of its fields. | **Runtime decision**: Callers verify the signature using the JWKS before processing the card. Unsigned cards can be rejected by gateways that enforce card integrity. **Deployment gate**: Signing should be active for all production deployments. |
| `agentSecurity.promptInjectionControls` | Prompt injection is the highest-likelihood attack vector for agents that process external data (OWASP LLM01). Callers routing sensitive data to this agent need to know controls are in place. | **Informational** primarily: declares the control posture. The actual enforcement is in the agent runtime, not derivable from the card. **Deployment gate**: `controlsInPlace` must be true for production; `reference` must be populated so the claim is evidenced. |
| `agentSecurity.inputOutputValidation` | Unvalidated inputs and outputs are a primary path to data exfiltration and injection attacks (OWASP LLM02). The card declares the validation posture so callers can factor it into trust decisions. | **Informational** primarily: the actual validation runs inside the agent. **Deployment gate**: Both `inputValidationEnabled` and `outputValidationEnabled` must be true for production. |
| `agentSecurity.networkAccessControl` | The network access policy determines which callers can reach the agent. An orchestrator routing from a public context to a `private-network-only` agent will fail. Knowing this in advance prevents misconfigured integrations. | **Provisioning**: Network security automation enforces placement at setup. **Informational** for callers assessing integration feasibility. **Deployment gate**: Verifies the policy is appropriate for the agent's data classification. |
| `agentSecurity.agentIdentityVerification` | Agent-to-agent impersonation is a real attack vector in multi-agent systems (OWASP LLM08). Callers extending trust to this agent should know whether mutual authentication is in place. | **Informational** and **Provisioning**: mTLS configuration is set up at deployment time, not re-read on every call. Strongly recommended for A3 and above. **Deployment gate**: Advisory flag if absent at A3 and above. |
| `agentSecurity.rateLimiting` | Agents at A2 and above may be called programmatically by orchestrators at high volume. A caller needs to know rate limiting is active before designing a high-throughput integration. | **Informational** and **Provisioning**: Rate limiting is configured at the gateway or API management layer at setup. **Deployment gate**: `enabled` must be true for production deployments. |
| `dependencies.mcpServers` | Every MCP connection is a trust boundary. Callers and security teams need to know what external tool connections this agent has to assess its full attack surface and third-party risk exposure. | **Informational** and **Deployment gate**: Security teams review this list as part of the onboarding approval. Gates require `approvalReference` for all entries; third-party servers must reference a vendor risk assessment per DORA Article 28. Runtime scanning requires a separate security posture tool the card alone cannot enforce MCP security. |
| `dependencies.agentSkills` | Skills containing executable code run at the agent's privilege level. This list makes the supply chain risk visible to security teams at deployment time. | **Deployment gate**: Security review gates require `approvalReference` for all skills; `securityReviewReference` is required for skills with executable code or from third-party sources. **Informational** for security operations monitoring the agent post-deployment. |
| `dependencies.additionalProtocols` | Novel protocols introduce trust boundaries and attack surfaces that may not be covered by existing security tooling. Declaring them makes the exposure visible and governable without requiring a schema change. | **Informational** and **Deployment gate**: Requires `approvalReference` for all entries. Advisory review is recommended for any protocol not in the institution's approved standard list. |

### The Two-Layer Model: Card and Registry

The Agent Card and the agent registry serve different audiences and operate at different points in the agent lifecycle. Understanding this distinction answers the question of whether the card carries too much information.

**The Agent Card** is a runtime document. It is served at a well-known URL, consumed by machines at call time, and designed to be self-contained. Its primary consumers are orchestrators, gateways, peer agents, and CI/CD pipelines. It answers the question: "can I trust this agent with this task right now?"

**The Agent Registry** is a governance system. It holds the full lifecycle record for every agent: who approved it, when it was validated, what versions were deployed and when, what incidents were raised, and when it was decommissioned. Its primary consumers are the AI governance function, model risk teams, internal audit, and compliance. It answers the question: "has this agent been properly governed over its full lifecycle?"

The two layers are linked through `registryRef`. Every Agent Card carries a URI pointing to its registry record. Every registry record carries a link back to the Agent Card URL. Neither is complete without the other, but each serves its audience without requiring access to the other system at runtime.

```
┌─────────────────────────────────────┐         ┌──────────────────────────────────────┐
│           AGENT CARD                │         │          AGENT REGISTRY              │
│   Served at /.well-known/           │         │   Managed by AI Governance           │
│   agent-card.json                   │         │                                      │
│                                     │         │                                      │
│  Runtime trust signal:              │  ──────▶│  Governance lifecycle record:        │
│  • Identity and capabilities        │registryRef  • Full approval history            │
│  • Autonomy level and oversight     │         │  • Validation dates and outcomes     │
│  • Approved actions and agents      │         │  • Change and incident history       │
│  • Data domains and residency       │         │  • Decommission record               │
│  • Security posture                 │◀────────│  • Links back to card URL            │
│  • Dependencies                     │         │                                      │
└─────────────────────────────────────┘         └──────────────────────────────────────┘
         consumed by                                      consumed by
   orchestrators, gateways,                     AI governance, model risk,
   peer agents, CI/CD pipelines                  internal audit, compliance
```

Fields that appear in both layers serve different functions at each layer. `governance.modelRisk.lastValidationDate` in the card is a real-time trust signal that an orchestrator can act on. The same data in the registry is a historical record with the full validation report attached. The card carries the current state; the registry carries the history.

---

### Agent Onboarding Process

Onboarding an agent to production in an FSI context should follow a structured process with defined gates. The Agent Card is produced during this process, not before it. Its fields should be populated by the teams that own the information, not by the development team working from assumptions.

The following six-stage process reflects the governance requirements of SR 11-7, the EU AI Act, and DORA.

**Stage 1: Intent Registration**

Before any build work begins, the requesting team registers the intended use case with the AI Governance function. Required inputs: proposed agent name and description, target autonomy level, data domains requested, business owner, and a plain-language justification for the autonomy level. The governance function assigns a preliminary risk classification and opens a registry record. The `governance.modelRisk.modelInventoryId` is reserved at this stage.

**Stage 2: Design and Architecture Review**

The development team produces the Agent Card draft. Architecture review covers agent collaboration patterns, dependency declarations (all MCP servers and Agent Skills), and trust boundaries. The threat model (cross-referenced to the MAESTRO Threat Model for this architecture) is reviewed for threats relevant to the proposed design. The `dependencies` block is populated at this stage from the architecture review output, not retrofitted after build.

**Stage 3: Model Risk Assessment**

Parallel to design review, the model risk team classifies the agent under SR 11-7 and the firm's internal model risk framework. The model risk team, not the development team, populates `governance.modelRiskTier`, `governance.modelRisk.lastValidationDate`, and `governance.modelRisk.nextReviewDate`. An agent that has not completed model risk assessment must not proceed to staging.

**Stage 4: Security Review**

The `agentSecurity` block is evidenced. Prompt injection controls are tested and a reference to the test evidence is recorded in `agentSecurity.promptInjectionControls.reference`. Network access controls are configured. For every third-party MCP server, a vendor risk assessment is completed and its reference is recorded in `dependencies.mcpServers[].approvalReference`. The `agentSecurity.cardSigning` fields are populated once the signed card is issued.

**Stage 5: Staged Deployment with Checkpoint Gates**

The agent moves through three environments in sequence: development, staging, and production. Each promotion requires a named approver, a change ticket, and a passing result against the Production Registration Rules in this document.

One deliberate practice worth highlighting: a team may start the agent with tighter human oversight than its final design requires, then relax that oversight as the agent proves reliable. For example, an agent ultimately designed to operate at A3 (where a human reviews at agreed milestones) might be deployed to staging at A1 (where a human approves every action). This gives the team direct evidence of reliable behaviour before they reduce oversight frequency. The autonomy level that is active at any point must be accurately reflected in the Agent Card. The `governance.changeApprovalReference` is updated on each promotion to link the current deployed version to its approved change record.

This graduated approach is a risk management practice, not a schema requirement.

**Stage 6: Operational Handoff and Ongoing Monitoring**

On production promotion the registry record is marked active. The operations team receives a runbook linked from `documentationUrl`. Monitoring thresholds are configured from the `compliance.auditTrail` and `agentSecurity` fields. The model risk team's review schedule is set from `governance.modelRisk.nextReviewDate`. Decommission criteria and the process for updating or revoking the Agent Card are agreed with the AI governance function before the handoff is signed off.

---

### Where Should the Agent Card Live?

The A2A Protocol specifies that the Agent Card is served at `/.well-known/agent-card.json` on the agent's domain. That answers *how* a caller finds the card. It does not answer *what system manages the card's content and keeps it current*.

A static file committed to a source repository is a common starting point during development. It is not the right long-term answer for a production FSI environment. Agent Card fields change at different rates and are owned by different teams: a URL may be stable for months, while a `changeApprovalReference` changes on every deployment and a `lastValidationDate` changes on the model risk team's schedule. Managing these through standard code review processes creates friction and risks drift between what the card declares and what is actually deployed.

**What a queryable registry gives you instead**

An agent registry is a service with an API that stores agent metadata centrally, enforces governance rules at registration time, and serves Agent Cards on demand. Callers and orchestrators can query it by capability, skill, data domain, or autonomy level to find available agents. The registry can also enforce onboarding rules for example, rejecting a registration if `modelRisk.modelInventoryId` is absent, or if a third-party MCP server lacks a vendor risk assessment reference.

Platforms that implement this pattern already exist. Microsoft Azure API Center supports A2A agent registration and discovery. The Microsoft Entra Agent Registry treats agents with the same identity controls applied to employees. The A2A project community has published proposals and reference implementations for enterprise agent registries. Backstage-based internal developer portals can serve this role for institutions that already use that platform.

> **This schema does not mandate a specific registry product or hosting approach.** The FSI Agent Card schema standardize what fields are declared, not how they are managed or where the card is served. Those decisions belong to each institution's architecture team, who are best placed to assess existing platforms, integration patterns, and operational constraints.

The one constant is regardless of hosting approach, the agent card must be served at the A2A well-known endpoint so that it is discoverable by any A2A-compliant caller.


[↑ Back to contents](#table-of-contents)

---

## Field Reference

### Core Fields (Standard A2A)

| Field | Mandatory | Description |
|:---|:---:|:---|
| `schemaVersion` | Yes | Version of the FSI Agent Card schema, e.g. `"1.0.0"`. This is the schema version, not the agent version. |
| `name` | Yes | Human-readable display name of the agent. |
| `description` | Yes | Description of the agent's purpose, scope, and what it does not do. |
| `url` | Yes | Primary A2A endpoint URL. Must use HTTPS in all production environments. |
| `version` | Yes | Semantic version of the agent software, e.g. `"2.3.1"`. |
| `provider` | Yes | Provider information, including business ownership fields. |
| `capabilities` | Yes | A2A protocol capabilities: streaming, push notifications, and state transition history. |
| `defaultInputModes` | Yes | Default input MIME types, e.g. `["application/json", "text/plain"]`. |
| `defaultOutputModes` | Yes | Default output MIME types. |
| `securitySchemes` | Yes | Authentication schemes. Defined by A2A and OpenAPI 3.0. Must not be modified. |
| `security` | Yes | Declares which securitySchemes are required to call this agent. |
| `skills` | Yes | List of discrete, auditable capabilities this agent can perform. |
| `documentationUrl` | No | URL to internal documentation or a runbook for this agent. |
| `lastUpdated` | No | ISO 8601 timestamp of the last Agent Card update. Must be kept current on every change. |
| `tags` | No | Keywords for discovery and categorization. |
| `registryRef` | No | URI pointing to this agent's record in the institution's agent registry. Links the runtime card to the full governance record. See the Agent Card and Registry section below. |

### A Note on `securitySchemes` and `security`

These fields are **reproduced verbatim from the A2A Protocol specification**, which itself mirrors the [OpenAPI 3.0 Security Scheme Object](https://spec.openapis.org/oas/v3.0.3#security-scheme-object) and [Security Requirement Object](https://spec.openapis.org/oas/v3.0.3#security-requirement-object). The field names, type values, and structural requirements come from that standard and must not be altered by FSI extensions.

The `securitySchemes` map defines what authentication mechanisms the agent supports. The `security` array declares which of those schemes are required to call the agent. This separation follows the OpenAPI convention and allows an agent to advertise multiple schemes while specifying which are actually enforced.

Supported scheme types: `apiKey`, `http`, `oauth2`, `openIdConnect`, `mutualTLS`.

For FSI production deployments, `oauth2` or `mutualTLS` are the appropriate choices. The `apiKey` scheme is acceptable for internal service-to-service calls with a well-managed key lifecycle. Public endpoints without authentication are not appropriate for any agent that accesses non-public data.

### Provider Object

The FSI Agent Card extends the standard `provider` object with business ownership fields that establish accountable ownership, a prerequisite under SR 11-7 and equivalent frameworks.

| Field | Mandatory | Description |
|:---|:---:|:---|
| `provider.name` | Yes | Name of the providing organization or team. |
| `provider.businessLine` | Yes | Business line that owns this agent. |
| `provider.department` | Yes | Specific department or team that operates this agent. |
| `provider.businessOwner.name` | Yes | Full name of the accountable business owner. |
| `provider.businessOwner.email` | Yes | Email address of the business owner. |
| `provider.businessOwner.role` | No | Job title of the business owner. |
| `provider.teamContact` | Yes | Team inbox or service desk address for operational support. Must be a shared address. |

### Skills Object

Each skill represents a discrete, auditable capability. Defining skills at this level of granularity allows orchestrators and audit functions to understand the agent's exact scope and supports access control policies applied per skill.

| Field | Mandatory | Description |
|:---|:---:|:---|
| `skills[].id` | Yes | Unique identifier for this skill. |
| `skills[].name` | Yes | Human-readable skill name. |
| `skills[].description` | Yes | What the skill does and what it does not do. Include constraints and side-effect declarations. |
| `skills[].requiresHumanApproval` | No | Must be `true` for any skill that mutates external system state. |
| `skills[].specReference` | No | Reference to the skill specification. May be a URL, a document ID, or an OpenAPI path reference. |
| `skills[].tags` | No | Searchable labels. |
| `skills[].examples` | No | Example prompts or inputs. |
| `skills[].inputModes` | No | MIME types accepted by this skill. Inherited from the A2A standard. Populate only when this skill accepts input types that differ from the agent's `defaultInputModes`. Leave absent in all other cases. |
| `skills[].outputModes` | No | MIME types produced by this skill. Inherited from the A2A standard. Populate only when this skill produces output types that differ from the agent's `defaultOutputModes`. Leave absent in all other cases. |

### Governance Block

| Field | Mandatory | Description |
|:---|:---:|:---|
| `governance.autonomyLevel` | Yes | `A0` through `A4` per the FINOS taxonomy. |
| `governance.autonomyLevelJustification` | No | Reasoned explanation of the level assignment, the constraints that enforce it, and how human oversight is implemented in this specific deployment. A restatement of the level name or oversight model name is not acceptable. |
| `governance.modelRiskTier` | Yes | `Minimal`, `Low`, `Moderate`, `High`, or `Critical`. |
| `governance.humanOversightModel` | Yes | The oversight pattern in use. Must be consistent with `autonomyLevel`. |
| `governance.approvedActionList` | Conditional | Required for A2 and above. Enumerates every permitted action. |
| `governance.approvedAgentRegistry` | Conditional | Required for A3 and above. Lists pre-approved delegate agents. |
| `governance.escalationContacts` | Yes | Ordered list of escalation contacts with specific triggers. |
| `governance.changeApprovalReference` | No | Change management ticket for the current deployed version. |
| `governance.modelRisk.modelInventoryId` | No | ID in the firm's model inventory. Must be populated before production deployment. |
| `governance.modelRisk.lastValidationDate` | No | Date of the most recent model validation review. |
| `governance.modelRisk.nextReviewDate` | No | Scheduled date for the next periodic model review. |

**Required mapping between `humanOversightModel` and `autonomyLevel`:**

| `humanOversightModel` | Required `autonomyLevel` |
|:---|:---:|
| `human-executes-all-actions` | A0 |
| `human-approves-every-action` | A1 |
| `human-reviews-at-checkpoints` | A2 |
| `human-reviews-at-milestones` | A3 |
| `human-receives-exception-alerts-only` | A4 |

### Data Handling Block

| Field | Mandatory | Description |
|:---|:---:|:---|
| `dataHandling.dataClassification` | Yes | `Public`, `Internal`, `Confidential`, or `Restricted`. |
| `dataHandling.permittedDataDomains` | Yes | Data domains this agent is  authorized to access. See the domain reference table below. |
| `dataHandling.dataResidency.permittedRegions` | Yes | ISO 3166-1 alpha-2 codes specifying where data may reside. |
| `dataHandling.dataResidency.restrictedRegions` | No | Regions explicitly prohibited. |
| `dataHandling.retentionPolicy` | No | Retention periods in days for agent inputs and outputs. Audit log retention is declared in `compliance.auditTrail.retentionDays`. |
| `dataHandling.piiHandling` | Conditional | Required when `PII` is listed in `permittedDataDomains`. |
| `dataHandling.piiHandling.legalBasis` | Conditional | GDPR Article 6 legal basis for processing personal data. |

**Permitted `permittedDataDomains` values:**

| Value | Description |
|:---|:---|
| `PII` | Personally identifiable information |
| `MNPI` | Material non-public information |
| `TradeData` | Trade and order records |
| `MarketData` | Market prices and reference data |
| `CustomerFinancials` | Customer account and financial data |
| `RegulatoryReporting` | Data prepared for regulatory submission |
| `KYC_AML` | Know Your Customer and Anti-Money Laundering data |
| `CreditRisk` | Credit scoring and risk data |
| `OperationalRisk` | Operational risk events and loss data |
| `InternalAudit` | Internal audit findings and reports |
| `HRData` | Employee and HR data |
| `PublicData` | Publicly available data with no classification requirements |

### Compliance Block

| Field | Mandatory | Description |
|:---|:---:|:---|
| `compliance.applicableRegulations` | Yes | Regulations and policies with specific applicability notes and compliance owners. |
| `compliance.auditTrail.enabled` | Yes | Whether audit logging is active. |
| `compliance.auditTrail.immutable` | Yes | Whether logs are write-once and tamper-evident. Must be `true` for A1 and above. |
| `compliance.auditTrail.retentionDays` | No | Number of days audit logs must be retained. Declared here rather than in `dataHandling.retentionPolicy` because audit log retention is a compliance obligation, not a data management decision. |
| `compliance.auditTrail.reference` | No | Reference to the audit logging specification. |
| `compliance.explainability.supported` | Yes | Whether the agent can produce a human-readable explanation of its decisions. |
| `compliance.explainability.method` | No | The method used to produce explanations. |
| `compliance.incidentResponse.killSwitchEndpoint` | Conditional | Required for A3 and above. Must be agent-independent. |
| `compliance.incidentResponse.incidentContactEmail` | Yes | Team inbox for incident reporting. |
| `compliance.incidentResponse.planReference` | Yes | Reference to the incident response plan. |

### Agent Security Block

This block captures the operational security posture of the agent. It is distinct from the compliance block, which records regulatory obligations. The fields map to specific controls in the [OWASP Top 10 for Large Language Model Applications (2025)](https://owasp.org/www-project-top-10-for-large-language-model-applications/) and to threat vectors identified in the MAESTRO threat model for this architecture. Where relevant, OWASP control references are noted inline.

| Field | Mandatory | Description |
|:---|:---:|:---|
| `agentSecurity.cardSigning.signed` | Yes | Whether the Agent Card is signed using JWS per RFC 7515. Supports supply chain integrity; addresses OWASP LLM03. |
| `agentSecurity.cardSigning.jwksUrl` | Conditional | URL of the JWKS used to verify the card signature. Required when `signed` is true; callers need this to verify the signature. The JWKS endpoint publishes public keys only; this URL is not a secret. |
| `agentSecurity.promptInjectionControls.controlsInPlace` | Yes | Whether prompt injection controls are active. Addresses OWASP LLM01, the highest-likelihood threat vector for agents that process external data. |
| `agentSecurity.promptInjectionControls.reference` | No | Reference to the control specification or test evidence. Required when controlsInPlace is true. |
| `agentSecurity.inputOutputValidation.inputValidationEnabled` | Yes | Whether all inputs are validated before processing. Addresses OWASP LLM02. |
| `agentSecurity.inputOutputValidation.outputValidationEnabled` | Yes | Whether all outputs are validated before passing to callers or downstream systems. Addresses OWASP LLM02 and LLM05. |
| `agentSecurity.inputOutputValidation.reference` | No | Reference to the validation specification or schema. |
| `agentSecurity.networkAccessControl.accessPolicy` | Yes | One of: `private-network-only`, `vpn-required`, `ip-allowlist`, `public-with-authentication`. In FSI deployments, public internet exposure of agent endpoints is a material risk. |
| `agentSecurity.networkAccessControl.reference` | No | Reference to the network access control specification or firewall rule set. |
| `agentSecurity.agentIdentityVerification.mutualAuthenticationEnabled` | No | Whether mutual TLS or equivalent is in use for agent-to-agent calls. Addresses OWASP LLM08 and agent impersonation threats in multi-agent patterns. |
| `agentSecurity.agentIdentityVerification.trustModel` | No | Description of the trust model in use (e.g. `internal PKI with mTLS`, `OAuth2 client credentials per agent identity`). |
| `agentSecurity.rateLimiting.enabled` | Yes | Whether rate limiting is active on this agent's endpoint. Addresses OWASP LLM10; prevents a compromised orchestrator from exhausting downstream agent capacity. |
| `agentSecurity.rateLimiting.reference` | No | Reference to the rate limiting configuration or policy document. |

---

### Dependencies Block

Every external system, protocol, and capability package an agent depends on at runtime must be declared in this block. Each dependency represents a trust boundary. Undeclared dependencies cannot be assessed for risk, included in third-party risk programmes, or monitored for supply chain integrity.

The block covers three categories. An agent that has no dependencies in a given category should declare an empty array, not omit the field. The explicit empty declaration confirms the assessment was made rather than skipped.

**A note on `permittedDataDomains` at three levels**

`permittedDataDomains` appears in `dataHandling`, in each `mcpServers[]` entry, and in each `agentSkills[]` entry. This is intentional and each instance serves a distinct enforcement purpose. The agent-level field in `dataHandling` is the ceiling: it defines the broadest set of data domains the agent may ever handle. The per-dependency fields are subsets of that ceiling, scoped to only the data domains that need to flow through a specific MCP server or skill. A reviewer auditing a single MCP connection does not need to consult the agent-level field to understand what data can cross that boundary. Least-privilege is enforced at the connection level, not only at the agent level.

**MCP Servers (`dependencies.mcpServers`)**

Each MCP server the agent connects to is a tool boundary through which the agent can read data, write to systems, or invoke external APIs. From a security standpoint, every MCP connection is simultaneously a prompt injection surface (OWASP LLM01), a supply chain risk (OWASP LLM03), and a potential excessive agency vector if tool permissions are broader than necessary (OWASP LLM08). Under DORA Article 28, third-party MCP servers are ICT third-party service providers and require a vendor risk assessment before use.

The `permittedDataDomains` field on each MCP server entry must be a subset of `dataHandling.permittedDataDomains`. This enforces least-privilege at the connection level: the agent may be  authorized to handle TradeData and MarketData in aggregate, but an individual MCP server connection should be scoped to only the domains it needs.

| Field | Mandatory | Description |
|:---|:---:|:---|
| `mcpServers[].id` | Yes | Unique identifier for this connection within this agent card. |
| `mcpServers[].name` | Yes | Human-readable name of the MCP server. |
| `mcpServers[].transport` | Yes | `stdio`, `sse`, or `http` per the MCP specification. |
| `mcpServers[].endpoint` | Conditional | Required for `sse` and `http` transports. |
| `mcpServers[].providerType` | Yes | `internal` or `third-party`. |
| `mcpServers[].vendor` | Conditional | Required when `providerType` is `third-party`. |
| `mcpServers[].permittedDataDomains` | Yes | Data domains permitted to flow through this connection. Must be a subset of the agent's `dataHandling.permittedDataDomains`. |
| `mcpServers[].approvalReference` | Yes | Approval record reference. Third-party servers must reference a vendor risk assessment. |
| `mcpServers[].securityReviewReference` | No | Reference to the security review for this server. |

**Agent Skills (`dependencies.agentSkills`)**

Agent Skills is an open standard introduced by Anthropic for packaging reusable agent workflows as folders of instructions, scripts, and resources. An agent loads skills dynamically at runtime. Skills are distinct from MCP servers: MCP connects an agent to external tools, while Agent Skills extend the agent's own reasoning and workflow capabilities.

The critical governance consideration is that skills containing executable code run with the agent's permissions. A skill that has been modified by a malicious actor, or sourced from an unvetted third party, can introduce un authorized instructions that execute at the agent's privilege level. This makes installed skills a configuration control item requiring formal approval and, for any skill with executable code, a security review regardless of source.

Pin skill versions explicitly in production. Floating version references allow a skill update to change agent behaviour without a corresponding change approval, which is a governance control failure.

| Field | Mandatory | Description |
|:---|:---:|:---|
| `agentSkills[].id` | Yes | Unique identifier for this skill within this agent card. |
| `agentSkills[].name` | Yes | Human-readable name of the skill package. |
| `agentSkills[].version` | No | Version installed. Should be pinned to a specific version in production. |
| `agentSkills[].source` | Yes | `internal`, `anthropic-marketplace`, or `third-party`. |
| `agentSkills[].containsExecutableCode` | Yes | Whether the skill includes scripts or code that execute with the agent's permissions. |
| `agentSkills[].permittedDataDomains` | No | Data domains this skill is permitted to access. Must be a subset of `dataHandling.permittedDataDomains`. |
| `agentSkills[].approvalReference` | Yes | Formal approval record for installing this skill. |
| `agentSkills[].securityReviewReference` | No | Security review reference. Required for third-party skills and recommended for any skill with executable code. |
| `agentSkills[].skillCardReference` | No | Reference to the skill's SKILL.md or specification document. |

**Additional Protocols (`dependencies.additionalProtocols`)**

This field accommodates protocols beyond A2A and MCP that the agent participates in. It is designed to be extensible so that protocols that do not yet exist at the time of schema publication can be declared and governed without requiring schema changes. Each entry requires a name, version, the agent's role (client, server, or both), and an approval reference.

| Field | Mandatory | Description |
|:---|:---:|:---|
| `additionalProtocols[].name` | Yes | Protocol name (e.g. `ANP`, `ACP`, `agntcy`). |
| `additionalProtocols[].version` | Yes | Protocol version in use. |
| `additionalProtocols[].role` | Yes | `client`, `server`, or `both`. |
| `additionalProtocols[].specificationUrl` | No | URL of the public protocol specification. |
| `additionalProtocols[].approvalReference` | Yes | Formal approval record for adopting this protocol. |
| `additionalProtocols[].integrationReference` | No | Reference to the institution's integration specification. |


[↑ Back to contents](#table-of-contents)

---

## Production Registration Rules

The following rules must be satisfied before an agent may be registered in a production environment.

1. `governance.humanOversightModel` must be consistent with `governance.autonomyLevel` per the mapping table above.
2. `governance.approvedActionList` is required for A2 and above. Every permitted action must be listed explicitly.
3. `governance.approvedAgentRegistry` is required for A3 and above. Each entry must include a formal approval reference.
4. `compliance.incidentResponse.killSwitchEndpoint` is required for A3 and above. The endpoint must be independent of the agent process.
5. `compliance.auditTrail.immutable` must be `true` for A1 and above.
6. `dataHandling.piiHandling` must be completed when `PII` appears in `permittedDataDomains`.
7. `governance.modelRisk.modelInventoryId` must be populated before production deployment.
8. `url` must use HTTPS for all production deployments.
9. `securitySchemes` must contain at least one entry. The scheme `"none"` is not acceptable for any agent that accesses non-public data.
10. `provider.teamContact` must be a shared team address, not an individual's personal email.
11. `dependencies.mcpServers[].permittedDataDomains` must be a subset of `dataHandling.permittedDataDomains` for every entry. A connection may not be granted access to a data domain the agent itself is not  authorized to handle.
12. `dependencies.mcpServers[].approvalReference` must reference a vendor risk assessment for any entry where `providerType` is `third-party`.
13. `dependencies.agentSkills[].approvalReference` is required for all skill entries regardless of source.
14. `dependencies.agentSkills[].securityReviewReference` is required for any skill where `containsExecutableCode` is `true` or `source` is `third-party`.
15. Skill versions in `dependencies.agentSkills[].version` must be pinned to a specific version in production deployments. Floating version references are not acceptable.


[↑ Back to contents](#table-of-contents)

---

## Best Practices

**Write skill descriptions that include constraints as well as capabilities.** A description should state what the skill will not do as clearly as what it will do. This precision serves orchestrators, who need to select the correct agent, and auditors, who need to verify the agent acted within its defined scope.

**Set `requiresHumanApproval: true` on every skill that writes to an external system.** Do not rely on calling systems to enforce this. Declaring it in the Agent Card makes the oversight requirement machine-readable and auditable.

**Treat `governance.approvedActionList` as a binding contract.** The implementation must enforce this list at runtime. If an action is not on the list, the agent must escalate rather than proceed.

**Keep `lastUpdated` current.** Every modification to the Agent Card must be reflected in this field. It is a key audit artefact and a control point in the change management process.

**Populate `governance.modelRisk.modelInventoryId` before deployment.** An agent that is not registered in the model inventory cannot be subject to SR 11-7 validation, monitored for performance, or included in aggregate model risk reporting.

**Structure escalation contacts in layers.** List contacts in order from first responder to senior escalation. For each contact, specify the conditions that trigger escalation to that level. Escalation paths that are vague are a governance control failure.

**Do not include sensitive credentials or internal system details in the Agent Card.** The Agent Card may be retrieved by any agent or registry with network access to the endpoint. Authentication requirements reference token endpoints and scope identifiers, not the credentials themselves.

**Use `specReference` for skills rather than embedding full schemas.** Embedding large JSON Schema objects in the Agent Card creates maintenance problems. A reference to a specification document or an OpenAPI path is sufficient for the card and keeps it readable.


[↑ Back to contents](#table-of-contents)

---

## Suggested Extensions

The `extensions` block is available for institution-specific fields. The following categories represent common areas where individual institutions may wish to extend the core schema. These are suggestions, not requirements.

**Operational**
- Deployment environment (`production`, `staging`, `sandbox`)
- Hosting platform and region
- Performance SLAs and availability targets
- Dependency declarations (upstream systems, data feeds, external APIs)

**Risk**
- Specific model assumptions and known limitations
- Back-testing or monitoring results references
- Concentration risk flags (e.g. number of business processes depending on this agent)

**Legal and Contractual**
- Third-party AI model usage declarations (particularly relevant under the EU AI Act for high-risk systems)
- Intellectual property ownership statements
- Cross-border data transfer agreements

**Product and Business**
- Cost centre and charge-back references
- Business capability mapping
- Approved use cases with corresponding approval references


[↑ Back to contents](#table-of-contents)

---

## Regulatory Mapping

### SR 11-7: Supervisory Guidance on Model Risk Management (Federal Reserve / OCC)

SR 11-7 is the primary model risk management framework for US-regulated banking organizations. The full guidance is available at the [Federal Reserve SR 11-7 Cover Letter](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm) and the [SR 11-7 Guidance Attachment](https://www.federalreserve.gov/supervisionreg/srletters/sr1107a1.pdf).

- `governance.modelRiskTier` addresses the requirement to assess and categorize model risk based on complexity, breadth of use, and potential impact. See [SR 11-7 Attachment, Section III](https://www.federalreserve.gov/supervisionreg/srletters/sr1107a1.pdf).
- `governance.modelRisk.modelInventoryId` implements the comprehensive model inventory requirement. See [SR 11-7 Attachment, Section VI](https://www.federalreserve.gov/supervisionreg/srletters/sr1107a1.pdf).
- `governance.modelRisk.lastValidationDate` and `nextReviewDate` evidence the ongoing monitoring requirement. See [SR 11-7 Attachment, Section IV](https://www.federalreserve.gov/supervisionreg/srletters/sr1107a1.pdf).
- `provider.businessOwner` implements the board and senior management accountability requirement. See [SR 11-7 Attachment, Section VI](https://www.federalreserve.gov/supervisionreg/srletters/sr1107a1.pdf).
- `compliance.explainability` addresses the requirement that model outputs be capable of being understood and challenged by qualified parties.
- `compliance.auditTrail` supports the recordkeeping requirements for model decisions and outcomes.

### EU AI Act (Regulation (EU) 2024/1689)

- `governance.autonomyLevel` and `governance.humanOversightModel` map to [Article 14: Human Oversight](https://artificialintelligenceact.eu/article/14/).
- `governance.modelRisk` maps to [Article 9: Risk Management System](https://artificialintelligenceact.eu/article/9/).
- `compliance.explainability` maps to [Article 13: Transparency and Provision of Information to Deployers](https://artificialintelligenceact.eu/article/13/).
- `compliance.applicableRegulations` documents the institution's compliance assessment, supporting conformity obligations under [Article 43](https://artificialintelligenceact.eu/article/43/).

### DORA: Digital Operational Resilience Act (Regulation (EU) 2022/2554)

DORA has applied to EU financial entities since 17 January 2025.

- `compliance.incidentResponse` addresses [Article 17: ICT-related Incident Management Process](https://www.digital-operational-resilience-act.com/Article_17.html).
- `provider.businessOwner` and the `governance` block address management accountability under [Article 5: Governance and organization](https://eur-lex.europa.eu/eli/reg/2022/2554/oj/eng).
- `compliance.auditTrail` addresses recordkeeping obligations under [Article 6: ICT Risk Management Framework](https://eur-lex.europa.eu/eli/reg/2022/2554/oj/eng).

### MAS Technology Risk Management Guidelines

- The `governance` block addresses senior management accountability under [MAS TRM Guidelines, Section 3](https://www.mas.gov.sg/regulation/guidelines/technology-risk-management-guidelines).
- `dataHandling.dataResidency` addresses data localisation requirements for customer data held in Singapore.
- `compliance.auditTrail` addresses audit logging obligations under [MAS TRM Guidelines, Section 9](https://www.mas.gov.sg/regulation/guidelines/technology-risk-management-guidelines).

### MiFID II and Market Abuse Regulation (MAR)

MiFID II (Directive 2014/65/EU) and MAR (Regulation (EU) 596/2014) impose specific obligations on AI agents involved in trade execution, recordkeeping, and market-facing communications.

- `dataHandling.permittedDataDomains` controls access to `TradeData` and `MNPI`, the two domains most directly implicated in MiFID II and MAR obligations.
- `governance.approvedActionList` documents every action the agent may take in a trading context. Any action not on this list must trigger escalation, not execution. This directly addresses the MAR requirement that automated systems not engage in behaviour that could constitute market manipulation.
- `compliance.auditTrail` addresses trade and order record-keeping obligations under [MiFID II Article 25](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:32014L0065), including the requirement to retain records for at least five years.
- `governance.humanOversightModel` and `compliance.incidentResponse.killSwitchEndpoint` together address the requirements for real-time human oversight and immediate halting capability for algorithmic trading systems under [MiFID II Article 17](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:32014L0065).
- For agents that handle MNPI, the combination of `governance.approvedAgentRegistry` and `dependencies.mcpServers[].permittedDataDomains` enforces information barrier controls at the agent delegation and tool connection level.

### GDPR (Regulation (EU) 2016/679) and CCPA

- `dataHandling.permittedDataDomains` documents the categories of personal data processed, required under [GDPR Article 30](https://gdpr-info.eu/art-30-gdpr/).
- `dataHandling.piiHandling.legalBasis` records the legal basis for processing, required under [GDPR Article 6](https://gdpr-info.eu/art-6-gdpr/).
- `dataHandling.retentionPolicy` evidences compliance with the storage limitation principle under [GDPR Article 5(1)(e)](https://gdpr-info.eu/art-5-gdpr/).
- `dataHandling.dataResidency.restrictedRegions` supports documentation of cross-border transfer restrictions under [GDPR Chapter V](https://gdpr-info.eu/chapter-5/).


[↑ Back to contents](#table-of-contents)

---

## File Reference

| File | Description |
|:---|:---|
| `agent-card-schema.json` | JSON Schema (Draft 2020-12) defining all fields, types, and validation rules. |
| `agent-card-sample.json` | Fully populated example for a Trade Reconciliation Agent operating at A2. |
| `README.md` | This document. |


[↑ Back to contents](#table-of-contents)

---

## References

| Resource | URL |
|:---|:---|
| A2A Protocol Official Documentation | https://a2a-protocol.org/ |
| A2A Protocol Specification | https://a2a-protocol.org/specification/ |
| Google Cloud: Develop an Agent2Agent Agent | https://docs.cloud.google.com/agent-builder/agent-engine/develop/a2a |
| A2A Python SDK | https://github.com/a2aproject/a2a-python |
| OpenAPI 3.0 Security Scheme Object | https://spec.openapis.org/oas/v3.0.3#security-scheme-object |
| FINOS AI Reference Architecture Library | https://github.com/finos-labs/ai-reference-architecture-library |
| FINOS Agent Autonomy Levels Taxonomy | https://github.com/finos-labs/ai-reference-architecture-library/blob/main/Library/reference-architecture/agent-autonomy/agent_autonomy_levels.md |
| OWASP Top 10 for LLM Applications | https://owasp.org/www-project-top-10-for-large-language-model-applications/ |
| RFC 7515: JSON Web Signature | https://www.rfc-editor.org/rfc/rfc7515 |
| Federal Reserve SR 11-7 Cover Letter | https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm |
| Federal Reserve SR 11-7 Guidance Attachment | https://www.federalreserve.gov/supervisionreg/srletters/sr1107a1.pdf |
| EU AI Act Article 9: Risk Management System | https://artificialintelligenceact.eu/article/9/ |
| EU AI Act Article 13: Transparency | https://artificialintelligenceact.eu/article/13/ |
| EU AI Act Article 14: Human Oversight | https://artificialintelligenceact.eu/article/14/ |
| EU AI Act Full Text | https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng |
| DORA Article 17: ICT Incident Management | https://www.digital-operational-resilience-act.com/Article_17.html |
| DORA Full Text | https://eur-lex.europa.eu/eli/reg/2022/2554/oj/eng |
| MAS Technology Risk Management Guidelines | https://www.mas.gov.sg/regulation/guidelines/technology-risk-management-guidelines |
| GDPR Article 5: Principles | https://gdpr-info.eu/art-5-gdpr/ |
| GDPR Article 6: Lawfulness of Processing | https://gdpr-info.eu/art-6-gdpr/ |
| GDPR Article 30: Records of Processing | https://gdpr-info.eu/art-30-gdpr/ |
| MiFID II Directive 2014/65/EU | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:32014L0065 |
| Market Abuse Regulation (EU) 596/2014 | https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0596 |
| FINOS AI Governance Framework Risk Catalogue | https://air-governance-framework.finos.org |
| MAESTRO Threat Model for Multi-Agent Reference Architecture | tm_ma_ref_arch_mar_2026.md (this repository) |

---



[↑ Back to contents](#table-of-contents)

---


## Glossary

This glossary defines key terms used in this document. Terms are listed in the order they tend to be encountered when reading the schema for the first time.

**Agent Card**
A JSON document published by an AI agent at a well-known URL (`/.well-known/agent-card.json`). It describes the agent's identity, capabilities, authentication requirements, and in the FSI extension governance and security posture. It is the primary discovery mechanism in the A2A Protocol.

**A2A Protocol (Agent-to-Agent Protocol)**
An open communication standard, originally developed by Google and now hosted by the Linux Foundation, that defines how AI agents discover and interact with each other. The Agent Card is a foundational component of the A2A Protocol.

**Orchestrator**
An AI agent or automated system that coordinates the work of other agents. It reads Agent Cards to determine which agents to call, what tasks to delegate, and what trust decisions to make before each call.

**Autonomy Level (A0–A4)**
A classification from the FINOS AI Reference Architecture taxonomy that describes how independently an agent acts and how much human oversight it requires. A0 requires a human to execute every action; A4 operates almost entirely without human involvement. The level is a design decision, not an intrinsic property of the underlying model.

**Human-in-the-Loop (HITL)**
A design pattern in which a human is required to review, approve, or override an agent's output or proposed action before it takes effect. The `governance.humanOversightModel` field declares which HITL pattern is in use.

**Model Risk Tier**
A classification of the risk posed by a model or agent, consistent with the firm's model risk framework and SR 11-7 guidance. Tiers range from Minimal to Critical and drive the intensity of validation, monitoring, and change management required.

**Model Inventory**
A centralised register of all models and agents in use at a financial institution, required by SR 11-7. Each entry tracks the model's purpose, owner, validation status, and risk tier. The `governance.modelRisk.modelInventoryId` field links the Agent Card to this register.

**SR 11-7**
Supervisory Guidance on Model Risk Management issued by the US Federal Reserve and OCC. It establishes the framework for identifying, assessing, and managing the risks posed by models used in financial decision-making.

**EU AI Act**
Regulation (EU) 2024/1689, which establishes a risk-based regulatory framework for artificial intelligence systems deployed in the European Union. High-risk AI systems are subject to obligations including risk management, human oversight, transparency, and conformity assessment.

**DORA (Digital Operational Resilience Act)**
Regulation (EU) 2022/2554, which requires financial entities in the EU to manage ICT risks, including those introduced by third-party ICT service providers. Third-party MCP servers are subject to DORA Article 28 vendor risk assessment obligations.

**MCP (Model Context Protocol)**
An open standard introduced by Anthropic that defines how AI agents connect to external tools and data sources. Each MCP server exposes a set of tools the agent can call. Every MCP connection is a trust boundary and a potential attack surface.

**Agent Skills**
An open standard for packaging reusable agent workflows as folders of instructions, scripts, and resources. An agent loads skills dynamically at runtime. Skills containing executable code carry supply chain risk and require security review regardless of source.

**OWASP LLM Top 10**
A list published by the Open Worldwide Application Security Project identifying the ten most critical security risks for applications built on large language models. LLM01 (Prompt Injection) and LLM06 (Excessive Agency) are the risks most directly addressed by the FSI Agent Card schema.

**Prompt Injection**
An attack in which malicious instructions embedded in content processed by an AI agent such as a retrieved document, a tool response, or a counterparty message manipulate the agent's behaviour. Declared in the Agent Card via `agentSecurity.promptInjectionControls`.

**MNPI (Material Non-Public Information)**
Information that is not available to the general public and that a reasonable investor would consider important in making an investment decision. Handling MNPI is subject to strict regulatory controls under MAR and MiFID II. The `MNPI` data domain in `dataHandling.permittedDataDomains` flags agents that may process this type of information.

**JWS (JSON Web Signature)**
A standard (RFC 7515) for digitally signing JSON documents. The FSI Agent Card uses JWS to allow callers to verify that the card has not been tampered with in transit. The signing key is managed separately; only the public key URL (JWKS endpoint) appears in the card.

**JWKS (JSON Web Key Set)**
A JSON document containing one or more public cryptographic keys, served at a well-known URL. Callers fetch the JWKS to verify a JWS signature. The JWKS URL is not a secret it publishes only public keys.

**mTLS (Mutual TLS)**
A variant of the TLS protocol in which both parties the caller and the server authenticate each other using certificates. Used in the `agentSecurity.agentIdentityVerification` block to declare whether agent-to-agent calls require mutual authentication.

**SPIFFE / SVID**
Secure Production Identity Framework for Everyone (SPIFFE) is a standard for issuing cryptographic identities to workloads. An SVID (SPIFFE Verifiable Identity Document) is the credential issued to a workload. The `agentSecurity` and `dependencies` blocks reference SPIFFE SVIDs as the recommended workload identity mechanism.

**WORM (Write-Once, Read-Many)**
A storage configuration in which data can be written once and then read repeatedly, but cannot be modified or deleted. Required for immutable audit logs under DORA, MiFID II, and SR 11-7.

**Kill Switch**
An endpoint that, when called, immediately halts an agent's operation. Required for agents at autonomy level A3 and above. The `compliance.incidentResponse.killSwitchEndpoint` field declares this endpoint. It must be independent of the agent process so that it remains callable even if the agent itself is compromised.

**Data Domain**
A category of data that an agent is  authorized to handle, as declared in `dataHandling.permittedDataDomains`. Examples include `TradeData`, `MNPI`, `PII`, and `KYC_AML`. Declaring data domains enables least-privilege access control at the agent, MCP server, and Agent Skills levels.

**Agent Registry**
A centralised service that stores, governs, and makes discoverable the Agent Cards and lifecycle records of all agents in an institution. Distinct from the Agent Card itself: the card is the runtime document; the registry holds the full governance history.

**CI/CD Pipeline**
Continuous Integration / Continuous Deployment an automated pipeline that builds, tests, and deploys software changes. In the context of the Agent Card, a CI/CD pipeline can enforce the Production Registration Rules before promoting an agent to a higher environment.

**Zero-Trust**
A security model in which no caller, network location, or agent is trusted by default. Every request must be authenticated and  authorized regardless of where it originates. The Agent Card's security fields (`securitySchemes`, `agentSecurity`) are designed to support zero-trust enforcement.

[↑ Back to contents](#table-of-contents)

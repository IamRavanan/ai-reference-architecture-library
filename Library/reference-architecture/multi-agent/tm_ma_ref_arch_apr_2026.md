# Threat Model: Multi-Agent Reference Architecture

This document provides a threat model for the FINOS Multi-Agent Reference Architecture. It maps 36 controls to 43 threats across 8 architectural layers, plus a set of cross-layer threats specific to FSI deployments.

---

## Table of Contents

- [1. Controls Definition](#1-controls-definition)
- [2. Threats and Mitigations](#2-threats-and-mitigations)
  - [User Interaction Layer](#user-interaction-layer)
  - [Agent Gateway Layer](#agent-gateway-layer)
  - [Agent Layer](#agent-layer)
  - [Knowledge Layer](#knowledge-layer)
  - [LLM Layer](#llm-layer)
  - [MCP Layer](#mcp-layer)
  - [Evaluation Layer](#evaluation-layer)
  - [Observability Layer](#observability-layer)
  - [Cross-Layer and FSI-Specific Threats](#cross-layer-and-fsi-specific-threats)

---

## 1. Controls Definition

| Control ID | Control Description |
|---|---|
| C1 | Implement input validation libraries and custom rules at the application layer |
| C2 | Use a specialised AI security tool, integrated as part of a gateway (Agent, MCP, or LLM) or as a standalone firewall, to inspect, validate, and sanitise prompts and responses for content-based threats |
| C3 | Design workflows to require human approval for high-risk actions |
| C4 | Integrate with an enterprise Identity Provider (IDP) enforcing Multi-Factor Authentication (MFA) |
| C5 | Feed user activity and agent logs into a security analytics platform (SIEM) for behavioural analytics and anomaly detection |
| C6 | Configure rate limiting and throttling on API endpoints |
| C7 | Deploy a Web Application Firewall (WAF) with rulesets to block common attack vectors |
| C8 | Use a Policy-as-Code engine to enforce Attribute-Based Access Control (ABAC) policies for write access |
| C9 | Log all critical changes to a centralised, write-once, read-many (WORM) system |
| C10 | Implement automated configuration scanning to detect unauthorised changes |
| C11 | Use platform-native network policies (Kubernetes network policies, security groups) to enforce micro-segmentation |
| C12 | Enforce mutual TLS (mTLS) for all connections using strong, verifiable workload identities (SPIFFE SVIDs) |
| C13 | Manage and version-control all security policies (authorisation, content, behaviour) as code in a version control system |
| C14 | Use sandboxing or containerisation technologies to isolate agent processes and tool execution |
| C15 | Implement runtime monitoring to detect and alert on anomalous agent behaviour or goal deviation |
| C16 | Ensure child agents are created with a scoped, delegated workload identity and a subset of the parent agent's permissions |
| C17 | Grant just-in-time, task-scoped permissions for tool execution |
| C18 | Implement automated data validation and sanitisation pipelines for knowledge sources |
| C19 | Integrate with Data Loss Prevention (DLP) solutions to scan agent outputs for sensitive data |
| C20 | Ensure logs contain full cryptographic workload identity and rich contextual details for forensic investigation |
| C21 | Implement automated response playbooks (SOAR) for high-confidence alerts |
| C22 | Implement resource quotas and limits (CPU, memory, execution time) within the agent runtime environment |
| C23 | Sanitise all agent-generated output to remove or neutralise malicious code before it is displayed to users or passed to other systems |
| C24 | Encrypt sensitive data, including models, both at rest and in transit |
| C25 | Implement a strict vetting and scanning process for all new models and components before they are registered in the platform |
| C26 | Enforce strict, non-bypassable workflows for tasks that require human supervision |
| C27 | Implement a multi-source feedback engine that aggregates and weights signals from diverse sources to generate a trusted score for agent interactions |
| C28 | Implement network egress filtering to restrict agent outbound connections to an approved destination allowlist |
| C29 | Use a dedicated secrets management platform for all credentials, API keys, and certificates; never inject secrets as environment variables accessible to the agent process |
| C30 | Enforce cryptographic signing and integrity verification for all registered models; validate signatures at load time and reject any model whose signature cannot be verified |
| C31 | Maintain a Software Bill of Materials (SBOM) for all agent components, dependencies, and models; integrate SBOM generation and vulnerability scanning into the CI/CD pipeline |
| C32 | Enforce data minimisation at the agent runtime layer; pass only the data fields required for each tool call and strip all fields not needed for the immediate task before dispatch |
| C33 | Apply RAG-specific validation; validate and sanitise retrieved documents before injection into the agent context window and monitor retrieval patterns for anomalous query distributions |
| C34 | Enforce strict cross-session isolation in long-term memory; cryptographically bind all memory entries to the originating user and session identity |
| C35 | Enforce strict parameter schema validation for all MCP tool calls; reject any call where parameters contain data from domains not authorised for that tool |
| C36 | Require signed Agent Card verification for all agent-to-agent calls; reject connections from agents presenting unverifiable, expired, or revoked identities; use a short-lived credential rotation policy |

---

## 2. Threats and Mitigations

### User Interaction Layer

| Threat ID | Threat | Description | Mitigations | Controls |
|---|---|---|---|---|
| T-UIL-01 | Malicious User Input | A user intentionally submits crafted inputs, including prompt injection, jailbreak attempts, or instruction-carrying payloads, to exploit the agent system or cause harmful downstream actions. Applies to interactive users and automated calling systems. | Apply input validation and sanitisation at the application layer. Use the AI security gateway to inspect and classify prompts before they reach the agent layer. Enforce human-in-the-loop checkpoints for high-risk action classes. | C1, C2, C3 |
| T-UIL-02 | User Impersonation | An attacker compromises or forges credentials to impersonate a legitimate user, inheriting their permissions, context, and agent-delegated authority. | Enforce strong authentication with MFA at the enterprise identity provider. Monitor for anomalous behavioural signals, including location, time, request volume, and action patterns, that deviate from the established user baseline. | C4, C5 |
| T-UIL-03 | Application Session Hijacking | An attacker intercepts or steals a valid application session token to issue requests to the agent system under an authenticated user's identity. | Enforce short session token lifetimes with automatic expiry. Bind sessions to client fingerprint. Apply HttpOnly and Secure cookie attributes. Forward all session anomalies to the SIEM. | C4, C5, C9 |
| T-UIL-04 | Denial of Service | An attacker floods the application with a high volume of requests to exhaust system capacity, degrade response quality, or trigger runaway agent execution chains. | Apply network-layer DDoS protection for volumetric attacks and a WAF for application-layer attacks. Enforce per-user and per-session rate limiting. | C6, C7 |
| T-UIL-05 | Insecure Output Handling | An agent generates output containing executable content, such as XSS payloads or script injection, or sensitive data that is returned to the user interface without sanitisation. | Sanitise all agent output at the application layer before rendering. Scan all output with DLP before delivery. Apply output schema validation to enforce the expected response structure. | C19, C23 |
| T-UIL-06 | HITL Workflow Manipulation | An attacker manipulates the human-in-the-loop approval interface through social engineering, UI spoofing, or prompt crafting so that a reviewer unknowingly approves a harmful or policy-violating agent action. | Present full, unmodified agent action context to the reviewer in the HITL interface. Enforce non-bypassable approval workflows at the platform layer. Log every approval decision with reviewer identity and the complete action payload. | C3, C9, C26 |

---

### Agent Gateway Layer

| Threat ID | Threat | Description | Mitigations | Controls |
|---|---|---|---|---|
| T-AGL-01 | Agent Registry Poisoning | An attacker gains write access to the Agent Registry and inserts a malicious agent entry so the gateway routes legitimate requests to an agent under the attacker's control. | Enforce ABAC with least-privilege write access on the registry. Log all registry mutations to an immutable, write-once audit store. Run automated scanning on all new registry entries before they become routable. | C8, C9, C10 |
| T-AGL-02 | Gateway Bypass | An attacker discovers a direct network path to an agent instance, bypassing the gateway and all associated authentication, authorisation, and policy enforcement. | Implement zero-trust network architecture so that no agent instance is reachable except through the gateway. Enforce mTLS with SPIFFE SVIDs for all internal communications so that agents reject unauthenticated connections regardless of network position. | C11, C12 |
| T-AGL-03 | Guardrail and Policy Evasion | An attacker crafts requests that are syntactically valid but semantically designed to evade the gateway's guardrail policy rules, passing through controls while carrying malicious or out-of-scope instructions. | Continuously update and adversarially test policy rulesets. Employ semantic behavioural anomaly detection in addition to rule-based filtering. Do not rely on syntactic pattern matching alone. | C5, C13 |
| T-AGL-04 | Agent Identity Spoofing at Gateway | An attacker presents a forged or stolen agent identity to the gateway to inherit the permissions, routing rules, or trust level of a legitimate registered agent. Particularly relevant where agent-to-agent calls pass through the gateway. | Require signed Agent Card verification for all agent identities presented at the gateway. Enforce mTLS with short-lived SPIFFE SVIDs. Reject any identity whose cryptographic proof cannot be verified against the authorised key registry. | C12, C36 |

---

### Agent Layer

This layer is subdivided by component group to reflect the structure of the Unified Agent Runtime.

#### Agent Collaboration Patterns

| Threat ID | Threat | Description | Mitigations | Controls |
|---|---|---|---|---|
| T-AL-01 | Supervisor Agent Compromise | An attacker gains control of the supervisor agent in a Supervisor/Worker pattern, enabling them to issue arbitrary instructions to all subordinate worker agents and control the entire agent graph from a single point. | Enforce strict runtime and network isolation for supervisor agents. Apply least privilege so the supervisor holds no permissions beyond its immediate coordination tasks. Monitor all inter-agent communication from the supervisor for anomalous instruction patterns. | C11, C14, C16 |
| T-AL-02 | Goal Manipulation via Skill Routing | An attacker exploits the Skills-Based Routing mechanism by crafting requests that cause the router to dispatch a sensitive task to a low-trust or compromised agent. | Validate that the routed agent's declared skills and trust level are consistent with the task's data domain and required permissions before dispatch. Never route solely on declared capability without registry verification. | C8, C10, C15 |
| T-AL-03 | Agent-as-a-Tool Abuse | An attacker exploits the Agent-as-a-Tool pattern to cause a high-privilege agent to invoke a compromised or malicious agent as a sub-tool, granting it access to the caller's permissions and context. | Require signed Agent Card verification for all agent-to-agent invocations. Enforce that the invoked agent's trust level and permitted data domains are a strict subset of the invoking agent's. Log all agent-to-agent invocations with full identity attribution. | C9, C16, C36 |
| T-AL-04 | Agent Collusion | Two or more compromised agents coordinate to circumvent a control that neither could bypass independently. A representative example is one agent generating a recommendation and a colluding agent approving it, bypassing a four-eyes control. | Enforce independent verification paths so that approval agents do not share context, memory, or instruction sources with the agents they are approving. Monitor for correlated anomalous behaviour across multiple agents. Periodically audit agent communication graphs for unexpected coordination patterns. | C5, C9, C16 |

#### Unified Agent Runtime

| Threat ID | Threat | Description | Mitigations | Controls |
|---|---|---|---|---|
| T-AL-05 | Goal Manipulation | An attacker manipulates an agent's goal or objective through crafted input so that the agent pursues an unintended task while appearing to operate normally. | Validate all external inputs that could influence the agent's goal state before they are admitted to the reasoning loop. Monitor agent behaviour at runtime for deviations from the expected task plan. Isolate agent runtimes so a compromised agent cannot influence the goal state of its peers. | C1, C14, C15 |
| T-AL-06 | Indirect Prompt Injection | An attacker embeds malicious instructions in external data consumed by the agent, including retrieved documents, tool responses, web content, and counterparty messages, to manipulate agent reasoning without any malicious action by the human user. | Sanitise all content retrieved from external sources before it enters the agent context window. Treat all externally sourced content as untrusted regardless of retrieval mechanism. Use the AI security gateway to inspect tool responses, not only user inputs. Enforce that agent instructions may only originate from authorised principals. | C2, C14, C33 |
| T-AL-07 | Multi-Hop Prompt Injection | A successful injection in a sub-agent propagates malicious instructions upstream to the supervisor, which then propagates them to the rest of the agent graph. The initial injection point may be low-privilege, but the impact extends to the entire graph. | Sanitise all inter-agent message payloads at the receiving agent before they are admitted to its reasoning loop. Treat peer-agent messages with the same scrutiny as untrusted external inputs. Implement message provenance tracking so the origin of every instruction is auditable. | C2, C14, C16, C36 |
| T-AL-08 | Excessive Agency and Scope Expansion | An agent autonomously expands its own scope, takes irreversible real-world actions, or executes an action chain whose cumulative effect was not authorised even though each individual action appeared permitted. In FSI deployments, this is the vector most likely to produce a regulatory incident. | Enforce an explicit approved action list for every agent. Any action not on the list must trigger escalation rather than execution. Implement checkpoint approval for all irreversible actions regardless of autonomy level. Monitor cumulative action sequences, not only individual tool calls. | C3, C15, C26 |
| T-AL-09 | Agent Resource Exhaustion | An attacker tricks an agent into executing a computationally expensive, long-running, or infinitely recursive task that exhausts CPU, memory, or time quotas and starves other agents of execution capacity. | Implement per-agent resource quotas covering CPU, memory, and execution time. Enforce maximum iteration counts on all loops and refinement cycles. Monitor resource consumption in real time and terminate agents that exceed their allocation. | C15, C22 |
| T-AL-10 | Secrets Exfiltration from Agent Runtime | A compromised agent reads environment variables, mounted secrets, service account tokens, or credentials accessible within its execution environment and exfiltrates them to an attacker-controlled endpoint. | Never inject credentials as environment variables. Use a dedicated secrets management platform with just-in-time, task-scoped credential issuance. Enforce network egress filtering to block exfiltration to unapproved endpoints. | C14, C28, C29 |
| T-AL-11 | Adaptive Learning Poisoning | An attacker manipulates the execution outcomes, user feedback, or error rate signals used by the Adaptive Learning component to cause the system to learn degraded prompt templates, miscalibrated agent configurations, or poor tool selection strategies. Unlike one-time feedback manipulation, this attack corrupts the persistent learning state. | Treat all Adaptive Learning signals as untrusted inputs and validate them before they influence system configuration. Require human review for any configuration change generated by adaptive learning that exceeds a defined sensitivity threshold. Maintain versioned snapshots of all learned configurations to enable rollback. | C9, C15, C27 |
| T-AL-12 | Workspace File System Abuse | A compromised agent writes malicious content to the shared Workspace File System that is subsequently read and acted upon by another agent or human user, propagating compromise through the file layer rather than the messaging layer. | Enforce strict write permissions on the workspace so that agents may only write to paths designated for their current task. Scan all files written to the workspace before they become readable by other agents. Log all file system operations with full agent identity attribution. | C8, C9, C14, C19 |
| T-AL-13 | State Hijacking via Pause and Resume | An attacker manipulates the serialised task state during a pause or handoff operation so that when the task is resumed, the agent operates with attacker-controlled goal state, memory, or credentials. | Cryptographically sign and integrity-check all serialised state before storage and before loading. Validate state provenance at resume time. Reject any state whose signature cannot be verified. | C9, C12, C20 |
| T-AL-14 | Inter-Agent Compromise via Shared State | A compromised agent attacks, manipulates, or exfiltrates data from peer agents in the same environment by exploiting shared memory, state, or collaboration and handoff channels. | Enforce strict runtime and network isolation between all agent instances. Restrict access to shared memory and state to governed, authenticated handoff mechanisms only. Monitor inter-agent communication channels for anomalous access patterns. | C5, C11, C14 |

#### Tools Layer

| Threat ID | Threat | Description | Mitigations | Controls |
|---|---|---|---|---|
| T-AL-15 | Shell Tool Abuse | A compromised agent invokes the Shell Tool with attacker-controlled command arguments to execute arbitrary system commands, write malicious files, or escalate privileges within the runtime. | Sandbox the Shell Tool in a restricted execution environment with an explicit command allowlist. Grant just-in-time, task-scoped permissions for every Shell Tool invocation. Monitor all shell command sequences for patterns that deviate from the agent's approved action list. | C1, C14, C17 |
| T-AL-16 | I/O Tool Abuse | A compromised agent uses the I/O Tool to read files outside its designated workspace paths, exfiltrate data to the workspace for collection by another process, or write malicious content that poisons subsequent agent reads. | Enforce strict path-scoped read and write permissions on the I/O Tool. Log all I/O operations with full agent identity and file path attribution. Scan all written content before it becomes readable by other agents or users. | C8, C9, C14 |
| T-AL-17 | Web Search Tool Manipulation | An attacker places adversarially crafted content at URLs likely to be returned by the Web Search Tool so that the agent retrieves and acts on attacker-controlled information. The agent has no inherent basis to distrust search results, making this a reliable indirect injection vector. | Treat all web search results as untrusted external input and sanitise before injection into the context window. Restrict the Web Search Tool to an approved domain allowlist where operationally feasible. Monitor for unexpected behavioural changes in the agent following web retrieval operations. | C2, C28, C33 |
| T-AL-18 | MCP Client Misuse | A compromised agent exploits the MCP Client to invoke unauthorised MCP servers or pass sensitive runtime data as tool call parameters to an attacker-controlled endpoint. | Enforce that the MCP Client may only connect to servers registered in the approved MCP Server Registry. Apply strict parameter schema validation before dispatch. Enforce data minimisation by stripping all fields not required for the tool's declared function. | C28, C32, C35 |

#### Memory

| Threat ID | Threat | Description | Mitigations | Controls |
|---|---|---|---|---|
| T-AL-19 | Context Window Poisoning | An attacker injects adversarial content into the agent's in-session context window via tool responses, retrieved documents, or inter-agent messages so that the in-session context manager propagates the malicious content through summarisation or trimming into the agent's active reasoning. | Sanitise all content before it enters the context window regardless of source. Treat all context inputs as untrusted. Monitor for context manipulation patterns such as instruction-containing content arriving via non-user channels. | C2, C14, C33 |
| T-AL-20 | Long-Term Memory Poisoning | An attacker injects crafted content into session summaries or user and task personalisation stores that persists across sessions and systematically biases future agent behaviour, affecting every future session that retrieves the poisoned entries. | Validate and sanitise all content before it is written to long-term memory. Treat long-term memory writes with the same scrutiny as knowledge base ingestion. Maintain a versioned, auditable history of memory state changes to enable rollback and forensic investigation. | C9, C18, C34 |
| T-AL-21 | Cross-Session Memory Leakage | Information from one user's or session's interactions, stored in session summaries or personalisation data, is retrieved and exposed in a subsequent session belonging to a different user. Particularly relevant in multi-tenant deployments. | Cryptographically bind all long-term memory entries to their originating user and session identity. Require re-authentication before any cross-session memory read. Enforce strict cross-session isolation so that memory written in one session cannot be retrieved in another under any circumstances. | C8, C24, C34 |

---

### Knowledge Layer

| Threat ID | Threat | Description | Mitigations | Controls |
|---|---|---|---|---|
| T-KL-01 | Data Poisoning | An attacker injects false, misleading, or maliciously crafted information into source bases or vector databases so that agents ground their reasoning in attacker-controlled content. Includes targeted poisoning of specific document types and bulk poisoning of ingestion pipelines. | Enforce strict ABAC on all data source write paths. Validate and sanitise all new data before ingestion. Maintain cryptographic hashes of knowledge base contents for integrity verification. Audit ingestion pipelines for unauthorised modifications. | C8, C18 |
| T-KL-02 | RAG Retrieval Manipulation | An attacker crafts content that scores highly in semantic similarity search so it is consistently retrieved and injected into the agent context ahead of legitimate authoritative content, without requiring write access to the knowledge base. This threat exploits the retrieval mechanism itself. | Monitor retrieval patterns for anomalous query distributions or the consistent high-scoring of specific content. Implement retrieval diversity controls to prevent single-source dominance. Apply source trust weighting that favours authoritative internal sources over externally sourced content at equal embedding distance. | C15, C33 |
| T-KL-03 | Data Leakage from Knowledge Layer | An agent retrieves and exposes data from the knowledge layer to an unauthorised caller through over-broad retrieval queries, or is manipulated into returning data beyond the scope of the legitimate request. | Enforce granular ABAC on all knowledge retrieval paths. Apply DLP scanning to all retrieved content before it is returned to the agent context. Encrypt sensitive knowledge sources at rest. Log all retrieval operations with full query and result attribution. | C8, C19, C24 |
| T-KL-04 | Embedding Inversion Attack | An attacker gains access to the raw vector database and reconstructs original source documents from stored embeddings, exposing knowledge base content that may be confidential or regulated, without requiring access to the original document store. | Restrict access to the raw vector database to the minimum required set of principals. Apply differential privacy techniques to embeddings where the knowledge base contains sensitive content. Encrypt the vector database at rest using keys that are not accessible to the retrieval service. | C8, C24 |

---

### LLM Layer

| Threat ID | Threat | Description | Mitigations | Controls |
|---|---|---|---|---|
| T-LLM-01 | Malicious Model Registration | An attacker registers a backdoored or adversarially fine-tuned model in the Model Registry that behaves normally under standard inputs but produces attacker-controlled outputs for specific trigger sequences. | Implement a strict vetting, signing, and approval process for all new model registrations. Enforce cryptographic signature verification at model load time. Conduct adversarial input testing before any model is approved for production use. | C10, C25, C30 |
| T-LLM-02 | Model Theft | An attacker gains unauthorised access to the Model Registry or inference infrastructure and exfiltrates proprietary model weights, causing intellectual property loss and enabling offline adversarial analysis. | Enforce strict ABAC on the Model Registry. Encrypt all model artefacts at rest and in transit. Monitor for anomalous access patterns, including bulk model downloads and access outside business hours. | C5, C8, C24 |
| T-LLM-03 | Prompt Injection at LLM Inference | An attacker crafts a prompt that causes the LLM to ignore its system instructions, override guardrails at the inference layer, or generate policy-violating output. May be delivered directly by a user or indirectly through content that has reached the inference endpoint. | Deploy the AI security gateway to validate and sanitise all prompts before they reach the inference endpoint. Apply output filtering at the LLM gateway layer, not only at the agent layer. Monitor for jailbreak patterns and system instruction override attempts. | C2 |
| T-LLM-04 | System Prompt Leakage | An attacker manipulates the LLM into revealing its system prompt, which may contain confidential workflow logic, tool configurations, or security controls that can be exploited in subsequent attacks. | Instruct models explicitly not to reveal system prompt contents. Apply output filtering at the LLM gateway to detect and redact system prompt disclosure. Never embed secrets, credentials, or policy logic in the system prompt; these belong in the secrets management platform and policy engine respectively. | C2, C13, C29 |
| T-LLM-05 | LLM Gateway Guardrail Bypass | An attacker crafts inputs or exploits misconfiguration to bypass the LLM Gateway's guardrails, including input validation, output filtering, and access controls, causing the gateway to forward harmful content or unauthorised requests to the model. | Continuously test LLM guardrails against adversarial inputs. Enforce policy-as-code so guardrail rules are version-controlled and cannot be silently modified. Alert on any guardrail failure at the gateway layer. | C5, C13, C21 |

---

### MCP Layer

| Threat ID | Threat | Description | Mitigations | Controls |
|---|---|---|---|---|
| T-MCP-01 | MCP Registry Poisoning | An attacker gains write access to the MCP Server Registry and inserts a malicious server entry so that agents connect to an attacker-controlled server when they believe they are using an authorised enterprise tool. | Enforce strict ABAC on MCP Registry write operations. Maintain an immutable audit log of all registry changes. Require cryptographic signing of all MCP server entries. Scan the registry regularly for unauthorised additions. | C8, C9, C10 |
| T-MCP-02 | Compromised MCP Server | An attacker compromises a legitimate MCP server to intercept tool call requests, manipulate responses returned to the agent, or pivot to connected enterprise systems using the server's service account credentials. | Enforce mTLS for all MCP connections. Isolate MCP servers from each other and from the agent runtime using network micro-segmentation. Encrypt all data at rest on MCP servers. Monitor all MCP server traffic for anomalous patterns. | C10, C11, C12, C24 |
| T-MCP-03 | MCP Gateway Bypass | An attacker discovers a direct network path to an MCP server that bypasses the MCP Gateway and all associated authentication, authorisation, and policy enforcement. | Implement zero-trust network segmentation so that MCP servers reject all connections that do not originate from the MCP Gateway. Enforce mTLS with SPIFFE SVIDs on all MCP server inbound connections. | C11, C12 |
| T-MCP-04 | Tool Name Shadowing | An attacker registers a malicious MCP server that declares a tool with the same name as a legitimate authorised tool on a different server so that routing resolves to the malicious server when an agent requests the tool by name. | Enforce globally unique, namespaced tool identifiers that include the originating server identity. Resolve tool names by server identity, not by tool name alone. Monitor for duplicate tool name registrations as a high-severity registry anomaly. | C8, C9, C10 |
| T-MCP-05 | Data Exfiltration via Tool Parameters | An agent is manipulated into passing sensitive data as parameters to an MCP tool call that routes them to an attacker-controlled or unapproved third-party server. The data leaves the trust boundary embedded in the call parameters. | Enforce strict parameter schema validation at the MCP Gateway and reject calls whose parameters contain data from domains not authorised for the target tool. Apply data minimisation by stripping all fields not required for the tool's declared function before dispatch. Enforce egress filtering at the network layer. | C19, C28, C32, C35 |
| T-MCP-06 | MCP Capability Escalation | A registered MCP server advertises capabilities or data access permissions broader than those approved in its security review, leading agents to request operations they are not authorised to perform. | Validate all MCP server capability declarations against the approved capability list at registration time. Reject capability updates that were not separately approved. Log all capability declaration changes as high-severity events requiring manual review. | C8, C10, C13 |

---

### Evaluation Layer

| Threat ID | Threat | Description | Mitigations | Controls |
|---|---|---|---|---|
| T-EVL-01 | Feedback Manipulation | An attacker provides systematically false or adversarially crafted feedback to the Feedback Engine so that the system learns incorrect behaviours, lowers safety thresholds, or increases confidence in attacker-desired outputs over time. | Verify the identity and authority of all feedback providers. Use a diverse, multi-source feedback aggregation strategy so that no single source can materially shift the aggregate score. Employ anomaly detection to flag feedback distributions that deviate statistically from the established baseline. | C5, C27 |
| T-EVL-02 | Bypassing Human Supervision | An attacker identifies a code path, configuration state, or race condition that allows actions requiring human approval to execute without going through the Human Supervision workflow. In FSI deployments, this directly produces governance and regulatory failures. | Implement human supervision workflows as non-bypassable enforcement at the platform layer, not as an advisory layer. Maintain a complete, immutable audit trail of every supervision decision and every action authorised. Verify that supervision outcomes are cryptographically bound to the action they authorise before the action is permitted to proceed. | C9, C26 |
| T-EVL-03 | Runtime Protection Evasion | An attacker crafts agent outputs or action sequences that individually pass Runtime Protection monitoring rules but in aggregate represent a policy violation or unsafe action, exploiting the stateless nature of most rule-based runtime monitors. | Implement stateful behavioural analysis in Runtime Protection so that action sequences are evaluated, not only individual actions. Maintain a sliding window of recent agent actions and alert on patterns that individually appear benign but collectively represent a prohibited behaviour. | C5, C15, C21 |

---

### Observability Layer

| Threat ID | Threat | Description | Mitigations | Controls |
|---|---|---|---|---|
| T-OBL-01 | Log Tampering | An attacker modifies or deletes existing log entries after gaining access to an agent or gateway to conceal activity, obstruct forensic investigation, or prevent audit trail reconstruction. | Implement write-once, read-many (WORM) log storage so that no process can modify or delete log entries after they are written. Ensure all logs carry full cryptographic workload identity, including agent ID and SPIFFE SVID, and sufficient contextual detail for forensic reconstruction. | C9, C20 |
| T-OBL-02 | Log Injection | A compromised agent crafts log entries containing false attribution, forged agent identities, fabricated timestamps, or content designed to confuse Correlation Engine rules or mislead forensic investigators. The log store is written correctly; the content itself is adversarial. | Enforce structured log schemas at the point of emission and reject or sanitise any log entry whose fields do not conform to the declared schema. Bind log entries cryptographically to the emitting agent's workload identity. Validate log provenance at SIEM ingestion before correlation is applied. | C9, C20 |
| T-OBL-03 | Alert Fatigue | An attacker generates a sustained high volume of low-fidelity alerts to desensitise operators so that genuine high-severity events are missed or deprioritised. This may also occur organically through poor alert tuning. | Continuously tune alerting rules and evaluate false positive rates. Use the Correlation Engine to group related signals before surfacing them as alerts. Deploy SOAR playbooks for high-confidence alert classes to ensure consistent and timely response. | C21 |
| T-OBL-04 | Trace Poisoning | A compromised agent injects fabricated or tampered trace spans into the distributed trace for a request so that operators reconstruct a false view of the request lifecycle, masking the actual path taken by a compromised request. | Cryptographically sign all trace spans at emission. Validate span provenance at the trace aggregation layer. Reject any span whose signature cannot be verified against the emitting workload's identity. | C9, C20 |
| T-OBL-05 | Anomaly Detection Evasion | An attacker operates at or just below anomaly detection thresholds through techniques such as slow exfiltration, incremental privilege escalation, or gradual drift in agent behaviour, maintaining persistence without triggering the Anomaly Detection component. | Implement stateful, longitudinal anomaly baselines that detect gradual drift, not only point-in-time threshold breaches. Use multi-signal correlation across logs, traces, metrics, and events. Periodically recalibrate baselines to account for legitimate operational change. | C5, C15, C21 |

---

### Cross-Layer and FSI-Specific Threats

These threats span multiple architectural layers or arise from FSI-specific regulatory and operational contexts. They require coordinated mitigations across layers.

| Threat ID | Threat | Description | Layers | Mitigations | Controls |
|---|---|---|---|---|---|
| T-XL-01 | MNPI Leakage Across Agent Boundaries | Material Non-Public Information handled by an agent authorised for restricted data is passed, intentionally or inadvertently, to an agent or tool not authorised to handle it. In a Supervisor/Worker pattern, a supervisor with broad data access may pass MNPI to a worker whose permitted data domains do not include MNPI. This constitutes a wall-crossing violation and a potential MAR breach. | Agent Layer, Knowledge Layer, MCP Layer | Enforce data domain checks at every agent-to-agent handoff so that the receiving agent's permitted data domains include every domain present in the payload. Apply DLP scanning on all inter-agent message payloads. Log all cross-boundary data transfers with full attribution for regulatory audit. | C8, C16, C19, C32 |
| T-XL-02 | Regulatory Reporting Manipulation | An agent that produces output used for regulatory submissions generates false, altered, or incomplete output through a successful attack or goal manipulation, and the result is submitted to a regulator without the manipulation being detected. | Agent Layer, Evaluation Layer | Enforce human review with explicit sign-off for all agent-generated content that feeds regulatory submissions. Maintain a cryptographically signed, immutable record of the exact output submitted alongside the complete agent trace that produced it. Implement independent validation of regulatory output against source data before submission. | C3, C9, C26 |
| T-XL-03 | Supply Chain Compromise | An attacker introduces a backdoored model, library, dataset, or MCP server into the system through the CI/CD or onboarding pipeline, creating a persistent compromise that bypasses runtime controls. | LLM Layer, MCP Layer, Agent Layer | Maintain an SBOM for all agent components, dependencies, and models. Integrate SBOM generation and vulnerability scanning into the CI/CD pipeline on every build. Enforce cryptographic signing and integrity verification for all registered components. | C25, C30, C31 |
| T-XL-04 | Cascade Failure Propagation | A failure, resource exhaustion, or compromise in one agent or dependency, such as an MCP server, LLM endpoint, or knowledge source, propagates through agent dependencies and results in system-wide unavailability or degraded behaviour. | Agent Layer, LLM Layer, MCP Layer | Implement circuit breaker patterns at all inter-agent and agent-to-dependency communication boundaries. Define and enforce graceful degradation behaviours for every agent so that dependency failures produce bounded, predictable outcomes. Test failure scenarios through regular chaos engineering exercises. | C15, C21, C22 |

---
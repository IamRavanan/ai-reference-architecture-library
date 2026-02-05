# LLM Model Registry – Scope Definition

## In-Scope

The LLM Model Registry provides a centralized, authoritative inventory and governance layer for Large Language Models and foundation models used within the organization, whether internally hosted, fine-tuned, or consumed via third-party APIs. Its purpose is to support regulatory compliance, risk management, operational control, and transparency across the full LLM lifecycle.

In scope are:

### LLM Inventory & Classification
- Unique identification of each LLM and variant (base model, fine-tuned model, adapter, prompt-tuned model).
- Model provenance (vendor, open-source project, internal development).
- Deployment modality (SaaS API, private cloud, on-prem, edge).
- Intended use and business domain.

### Versioning & Lineage
- Base model version, fine-tuning checkpoints, adapters, and prompt templates.
- Training and fine-tuning datasets (references and hashes, not raw data).
- Tooling and framework versions (e.g., inference stack, safety layers).

### Governance & Compliance Metadata
- Regulatory classification (e.g., EU AI Act GPAI, systemic risk GPAI, model materiality tier).
- Model cards, system cards, and risk assessments.
- Approval status for environments (development, UAT, production).
- Human accountability (model owner, risk owner, compliance approver).

### Safety, Risk & Control Evidence
- Evaluations for hallucination, bias, toxicity, robustness, and prompt injection.
- Red-teaming results and mitigation status.
- Alignment and guardrail configurations (policy filters, refusal rules, RAG constraints).

### Operational State & Monitoring References
- Performance and cost characteristics (latency, throughput, context window, token limits).
- Drift and behavior change indicators across model updates.
- Incident, vulnerability, and deprecation notices.

### Interoperability & Auditability
- APIs for integration with MLOps, LLMOps, GRC, and security platforms.
- Immutable audit trail of model onboarding, updates, approvals, and retirement.

---

## Out-of-Scope

The LLM Model Registry does not directly perform the following, though it may reference or integrate with systems that do:

### LLM Training & Fine-Tuning Execution
- Pre-training, fine-tuning, reinforcement learning, prompt optimization, or embedding generation.

### Inference & Serving
- Runtime request handling, load balancing, caching, or routing.
- RAG pipelines, vector search, or tool execution.

### Prompt & Application Logic Management
- Application-level prompt orchestration, agent workflows, or business rules.

### Data Management
- Storage of training corpora, conversation logs, vector databases, or retrieval indices (only metadata and lineage references).

### Safety Enforcement Engines
- Real-time content moderation, policy filtering, or jailbreak detection (only configuration and evaluation records).

### Security & Access Control Systems
- API key management, identity, secrets, or network security (only ownership and policy metadata).

### Regulatory Decision Automation
- Automated go/no-go, model blocking, or risk scoring engines (registry records status, not enforcement).

# ROADMAP

## 1. Overview

This roadmap defines the phased development plan for a governed multi-tenant agentic RAG platform for internal use in a financial institution.

The roadmap is designed to evolve the project from a secure foundation into a production-grade AI platform with:

* Multi-tenant isolation
* Secure RAG
* Structured tool calling
* Strict graph-based agent runtime
* AI Gateway
* Local and API model support
* Human-in-the-loop workflows
* LLMOps and MLOps governance
* Observability
* Auditability
* Evaluation harness
* CI/CD gates
* Production scalability

The project must not start by building an unconstrained agent. The first milestones must establish the trusted control plane: tenant context, authentication, authorization, AI Gateway, audit, and policy enforcement.

---

## 2. Roadmap Principles

The roadmap follows these principles:

1. **Security before autonomy**
   Agentic behavior is added only after tenant isolation, audit, authorization, and policy enforcement exist.

2. **Governance before scale**
   The system must be explainable, versioned, auditable, and measurable before being scaled.

3. **RAG before tools**
   The platform first proves secure retrieval and grounded answering before allowing tool execution.

4. **Tool proposals before tool actions**
   The LLM may propose actions, but the runtime must validate and authorize execution.

5. **Strict runtime before agent framework**
   CrewAI and other agent frameworks must be integrated behind adapters, not used as security boundaries.

6. **Fail-safe by default**
   The system must refuse, escalate, or degrade safely whenever security, policy, grounding, or runtime constraints fail.

7. **Production path from day one**
   Even the MVP should be structured so that it can evolve into a production-grade platform.

---

## 3. Phases Summary

```txt id="ky1xkx"
Phase 0  - Architecture and Threat Model
Phase 1  - Project Foundation
Phase 2  - Security, Tenant Context, and Audit
Phase 3  - AI Gateway
Phase 4  - Secure Document Ingestion
Phase 5  - Tenant-Safe RAG
Phase 6  - Grounded Answering
Phase 7  - Structured Tool Calling
Phase 8  - Strict Agent Runtime
Phase 9  - Human-in-the-Loop
Phase 10 - Governance Registries
Phase 11 - Evaluation Harness
Phase 12 - Observability and Cost Control
Phase 13 - CI/CD Production Gates
Phase 14 - Hardening and Load Testing
Phase 15 - Production Readiness
Phase 16 - Advanced Enterprise Features
```

---

# Phase 0 — Architecture and Threat Model

## Goal

Define the system before writing production code.

The goal of this phase is to establish the architectural, security, governance, and operational foundation of the platform.

## Key Questions

```txt id="o3yut6"
What are the tenants?
What data can each tenant access?
What models can each tenant use?
What tools can each tenant use?
What data can leave the institution boundary?
Which actions require human approval?
What is the safe failure behavior?
What are the main abuse cases?
What are the non-functional requirements?
```

## Deliverables

```txt id="y79h2b"
docs/ARCHITECTURE.md
docs/SPEC.md
docs/STACK.md
docs/ROADMAP.md
docs/IMPLEMENTATION_PLAN.md
docs/THREAT_MODEL.md
docs/TENANT_MODEL.md
docs/DATA_FLOW.md
docs/SECURITY_PRINCIPLES.md
```

## Acceptance Criteria

```txt id="7vrd0v"
Architecture defines trusted and untrusted components.
Tenant isolation strategy is documented.
AI Gateway responsibility is documented.
Vector Access Gateway responsibility is documented.
Tool calling model is documented.
HITL triggers are documented.
Fail-safe behavior is documented.
Initial technology stack is documented.
```

---

# Phase 1 — Project Foundation

## Goal

Create the initial repository, development environment, project layout, and baseline application.

This phase creates the technical skeleton of the platform.

## Scope

```txt id="9xqkzp"
Repository structure
Python project setup
FastAPI application
Docker Compose
PostgreSQL
Redis
Basic health checks
Basic configuration management
Initial test setup
Initial CI pipeline
```

## Deliverables

```txt id="o1p9oe"
apps/api
packages/security
packages/agent_runtime
packages/ai_gateway
packages/rag
packages/tools
packages/governance
packages/observability
packages/evaluation
infra/docker
tests/unit
tests/integration
```

## Initial Endpoints

```txt id="grk033"
GET /health
GET /ready
GET /version
```

## Acceptance Criteria

```txt id="u1ixkx"
Application starts locally with Docker Compose.
API health check works.
PostgreSQL is available.
Redis is available.
Test suite runs.
CI pipeline runs lint and tests.
Project structure matches the architecture.
Configuration is environment-based.
```

---

# Phase 2 — Security, Tenant Context, and Audit

## Goal

Establish the trusted execution context required by every sensitive operation.

This is the first real platform milestone.

## Scope

```txt id="od4udx"
JWT validation
Tenant Context creation
RBAC scaffolding
ABAC scaffolding
Request ID generation
Trace ID generation
Audit event model
Basic audit persistence
Security middleware
Tenant-aware service base classes
```

## Deliverables

```txt id="swi85q"
JWT validation module
TenantContext model
Authorization service
Audit service
Request context middleware
Tenant enforcement tests
Audit record table
```

## Initial Policies

```txt id="mxd1c1"
Reject missing authentication.
Reject missing tenant context.
Reject inactive tenant.
Reject inactive user.
Reject missing required scope.
Audit all denied requests.
```

## Acceptance Criteria

```txt id="kxf3rc"
Every request receives request_id and trace_id.
Authenticated request creates Tenant Context.
Invalid JWT is rejected.
Missing tenant context is rejected.
Sensitive service methods require Tenant Context.
Audit record is created for request lifecycle.
Tenant isolation tests exist.
```

## Critical Test

```txt id="tml315"
A request without a valid Tenant Context cannot call model, retrieval, tool execution, cache, or audit lookup.
```

---

# Phase 3 — AI Gateway

## Goal

Create the only approved path for model and embedding calls.

The AI Gateway is the foundation for model governance, fallback, token control, observability, and provider abstraction.

## Scope

```txt id="i435s9"
AI Gateway interface
Provider adapter interface
Mock provider
OpenAI/Azure OpenAI adapter
Ollama/local adapter
Embedding adapter interface
Token accounting
Tenant token bucket
Timeouts
Retries
Fallback chain
Model Registry baseline
Model call audit events
```

## Deliverables

```txt id="qa3vp4"
packages/ai_gateway/interface.py
packages/ai_gateway/providers/
packages/ai_gateway/routing/
packages/ai_gateway/token_bucket/
packages/ai_gateway/fallback/
packages/ai_gateway/cache/
```

## Initial Capabilities

```txt id="qo6l2s"
generate_text
generate_structured_output
generate_embedding
route_model
apply_token_budget
apply_fallback
record_usage
```

## Acceptance Criteria

```txt id="pkb48c"
No direct model call exists outside AI Gateway.
Tenant model permissions are enforced.
Token usage is recorded by tenant.
Fallback is supported.
Model call emits trace event.
Model call emits audit event.
Model unavailable returns safe error or approved fallback.
```

## Critical Tests

```txt id="e4ml3d"
Tenant cannot use unapproved model.
Token budget exceeded blocks or downgrades request according to policy.
Fallback never routes sensitive request to unapproved provider.
```

---

# Phase 4 — Secure Document Ingestion

## Goal

Build the governed ingestion pipeline for internal documents.

Documents must become versioned, classified, chunked, embedded, and indexed artifacts.

## Scope

```txt id="xql0wm"
Document Registry
Document versioning
Document metadata validation
Document parser
Chunking pipeline
Chunking strategy versioning
Embedding generation through AI Gateway
Document status lifecycle
Background ingestion jobs
Object storage abstraction
```

## Document Lifecycle

```txt id="rfvbia"
draft
ingestion_queued
processing
indexed
active
deprecated
expired
revoked
archived
failed
```

## Deliverables

```txt id="h0m4zb"
POST /v1/documents
GET /v1/documents/{document_id}
POST /v1/documents/{document_id}/versions/{version}/activate
Document registry tables
Chunk registry tables
Ingestion worker
Embedding job
```

## Acceptance Criteria

```txt id="1nwxmh"
Document requires tenant_id.
Document requires classification.
Document requires version.
Document receives content hash.
Chunks receive chunk IDs.
Chunks include document version.
Embedding model version is recorded.
Inactive documents are not retrievable.
Ingestion emits audit events.
```

## Critical Tests

```txt id="qv6x0z"
Document from tenant A cannot be activated under tenant B.
Revoked document cannot be retrieved.
Chunk metadata preserves tenant_id, document_id, and document_version.
```

---

# Phase 5 — Tenant-Safe RAG

## Goal

Implement secure retrieval through the Vector Access Gateway.

This phase proves that the system can retrieve knowledge without violating tenant boundaries.

## Scope

```txt id="kdnq93"
Vector Access Gateway
Tenant filter injection
Document ACL filtering
Document status filtering
Classification filtering
User clearance filtering
Semantic retrieval
Retrieval audit
Retrieval traces
Cross-tenant leakage tests
```

## Deliverables

```txt id="b452w3"
packages/rag/vector_access_gateway.py
packages/rag/retriever.py
POST /v1/rag/search
Retrieval audit events
Tenant-safe retrieval tests
```

## Acceptance Criteria

```txt id="1694yv"
All vector search goes through Vector Access Gateway.
Gateway injects tenant_id server-side.
Client cannot widen access through filters.
Inactive documents are excluded.
Unauthorized documents are excluded.
Retrieved chunks include source metadata.
Retrieval event is audited.
```

## Critical Tests

```txt id="9miqti"
Tenant A query cannot retrieve Tenant B chunks.
User without required role cannot retrieve restricted document.
Client-supplied tenant filter is ignored or rejected.
```

---

# Phase 6 — Grounded Answering

## Goal

Generate answers grounded in authorized retrieved documents.

This phase turns secure retrieval into useful RAG responses.

## Scope

```txt id="gvw40i"
RAG Orchestrator
Context assembly
Citation builder
Prompt template for grounded answering
Grounding validator
Unsupported claim handling
Safe refusal for insufficient evidence
Output validation baseline
```

## Deliverables

```txt id="79als8"
POST /v1/ai/requests with mode=rag_agent
Citation response schema
Grounding validator
Safe refusal template
RAG answer audit events
```

## Acceptance Criteria

```txt id="zcikj1"
Answer includes citations when required.
Citation includes document_id.
Citation includes document_version.
Citation includes chunk_id.
Answer is generated through AI Gateway.
Unsupported answers are refused or escalated.
Grounding failures are audited.
```

## Critical Tests

```txt id="7figex"
Answer cannot cite unauthorized document.
Answer without supporting chunks fails validation.
Expired document cannot support production answer.
```

---

# Phase 7 — Structured Tool Calling

## Goal

Allow the LLM to propose tools using structured JSON, while the runtime validates and executes tools safely.

## Scope

```txt id="wzhgxp"
Tool Registry
Tool schema definition
Tool proposal schema
Tool validation
Tool authorization
Tool Executor
Tool result schema
Tool error schema
Tool audit events
Initial read-only tools
```

## Initial Tools

```txt id="z1swxq"
retrieve_documents
summarize_document
compare_documents
get_document_metadata
request_human_review
```

## Deliverables

```txt id="3si23e"
packages/tools/registry.py
packages/tools/executor.py
packages/tools/schemas.py
packages/tools/builtin/
Tool registry tables
Tool execution audit events
```

## Acceptance Criteria

```txt id="b4owav"
LLM may only propose tool calls.
Tool proposal must be valid JSON.
Tool proposal must match schema.
Tool must exist in registry.
Tool must be active.
Tenant must be authorized.
User must have required scope.
Tool result is structured.
Tool execution is audited.
```

## Critical Tests

```txt id="hz8gyi"
Invalid JSON tool call is rejected.
Unknown tool is rejected.
Unauthorized tenant cannot execute tool.
Tool with invalid arguments is rejected.
```

---

# Phase 8 — Strict Agent Runtime

## Goal

Implement the strict graph-based agent runtime with bounded loops, policy hooks, and controlled tool execution.

This phase turns the platform into an agentic RAG system.

## Scope

```txt id="gr7t5y"
AgentState
GraphRunner
Graph nodes
State transitions
Step budget
Token budget
Cost budget
Tool call budget
Retry policy
Loop exit conditions
Policy hooks
Audit hooks
Observability hooks
CrewAI adapter baseline
```

## Required Nodes

```txt id="lww4vv"
START
LOAD_CONTEXT
AUTHORIZATION_CHECK
PII_PREPROCESSING
INTENT_CLASSIFICATION
RISK_CLASSIFICATION
PLANNING
POLICY_CHECK
RETRIEVAL
TOOL_CALL_PROPOSAL
TOOL_SCHEMA_VALIDATION
TOOL_AUTHORIZATION
TOOL_EXECUTION
OBSERVATION
GROUNDING
OUTPUT_VALIDATION
HITL_CHECK
FINAL_RESPONSE
AUDIT_LOG
END
```

## Deliverables

```txt id="1gu7dv"
packages/agent_runtime/state.py
packages/agent_runtime/graph.py
packages/agent_runtime/nodes/
packages/agent_runtime/runner.py
packages/agent_runtime/policies.py
packages/agent_runtime/adapters/crewai.py
```

## Acceptance Criteria

```txt id="tqsmim"
Runtime executes approved graph nodes.
State transitions are traceable.
Loop is bounded by max_steps.
Tool calls are bounded.
Token and cost budgets are enforced.
Invalid state fails safely.
Runtime emits audit events.
CrewAI can be used through adapter.
```

## Critical Tests

```txt id="rbexqm"
Agent cannot execute infinite loop.
Agent cannot bypass Tool Executor.
Agent cannot call AI provider outside AI Gateway.
Agent cannot retrieve vector data outside Vector Access Gateway.
```

---

# Phase 9 — Human-in-the-Loop

## Goal

Add human approval workflows for high-risk, uncertain, or policy-restricted cases.

## Scope

```txt id="eyl5yw"
HITL task model
HITL task queue
Reviewer permissions
Approval flow
Rejection flow
Edit-before-release flow
HITL audit records
HITL API
Basic review UI or admin endpoint
```

## HITL Triggers

```txt id="et4l5c"
High risk level
Low grounding confidence
Conflicting evidence
Sensitive PII
Financial impact
Regulatory impact
Tool requires approval
Prompt injection suspicion
Policy uncertainty
Output validator requires review
```

## Deliverables

```txt id="81cso4"
GET /v1/hitl/tasks
POST /v1/hitl/tasks/{task_id}/review
HITL task table
HITL decision table
Reviewer authorization
```

## Acceptance Criteria

```txt id="v6bac9"
Runtime can pause execution for HITL.
Reviewer can approve, reject, or edit.
Final answer is not released before required approval.
HITL decision is audited.
Reviewer access is tenant-scoped.
```

## Critical Tests

```txt id="0v7dz8"
High-risk request triggers HITL.
Unauthorized reviewer cannot approve task.
Rejected HITL task does not release final answer.
Edited answer preserves audit trail.
```

---

# Phase 10 — Governance Registries

## Goal

Implement versioned registries for all critical AI artifacts.

## Scope

```txt id="80rg5k"
Prompt Registry
Model Registry
Embedding Registry
Tool Registry versioning
Policy Registry
Document Registry improvements
Agent Graph Registry
Evaluation Dataset Registry
Approval workflow baseline
```

## Versioned Artifacts

```txt id="z0ncvk"
prompts
models
embedding models
documents
chunking strategies
retrieval strategies
tool schemas
policies
agent graphs
evaluation datasets
output validators
```

## Deliverables

```txt id="mv4n4k"
Prompt registry CRUD
Model registry CRUD
Policy registry CRUD
Artifact status lifecycle
Approval metadata
Production artifact enforcement
```

## Artifact Lifecycle

```txt id="pwkcgn"
draft
staging
approved
production
deprecated
revoked
```

`approved` means governance-approved and eligible for promotion.
`production` means live for production execution and must already have recorded approval metadata.

## Acceptance Criteria

```txt id="xxvsow"
Production flow uses artifacts with status `production`.
Promotion to `production` requires recorded approval metadata.
Artifact version is recorded in audit.
Deprecated artifacts are blocked in production.
Revoked artifacts are blocked globally.
```

## Critical Tests

```txt id="n881el"
Artifact without approval metadata cannot be promoted to `production`.
Artifact without status `production` cannot be selected by production flows.
Policy decision records policy version.
```

---

# Phase 11 — Evaluation Harness

## Goal

Create automated evaluation for RAG quality, safety, governance, and regression control.

## Scope

```txt id="0bxete"
Golden datasets
RAG evaluation
Grounding evaluation
Citation evaluation
Tenant isolation tests
PII leakage tests
Prompt injection tests
Indirect prompt injection tests
Tool misuse tests
Policy enforcement tests
Latency tests
Cost tests
CI integration
```

## Evaluation Categories

```txt id="9ry140"
answer correctness
citation precision
citation recall
faithfulness
retrieval relevance
tenant isolation
PII leakage
prompt injection resistance
tool call validity
policy enforcement
fallback correctness
latency
cost
```

## Deliverables

```txt id="8779th"
packages/evaluation/harness.py
tests/evals/golden/
tests/evals/security/
tests/evals/rag/
tests/evals/tools/
Evaluation report output
CI evaluation step
```

## Acceptance Criteria

```txt id="v9viox"
Evaluation can run locally.
Evaluation can run in CI.
Critical security evaluations block deployment.
RAG regression threshold is configurable.
Evaluation results are stored.
Prompt changes can be evaluated before promotion.
```

## Critical Tests

```txt id="b893j6"
Cross-tenant leakage test must pass.
PII leakage test must pass.
Prompt injection critical suite must pass.
Tool authorization bypass test must pass.
```

---

# Phase 12 — Observability and Cost Control

## Goal

Make the system observable, measurable, and cost-aware.

## Scope

```txt id="0gqj21"
OpenTelemetry instrumentation
Structured logging
Metrics collection
Dashboard baseline
Cost tracking
Tenant usage tracking
Fallback tracking
Token tracking
Graph node latency tracking
Security event metrics
```

## Deliverables

```txt id="dklf6z"
OpenTelemetry integration
Prometheus metrics
Grafana dashboard
Structured logs
Tenant usage endpoint
Cost usage endpoint
Trace lookup endpoint
```

## Required Dashboards

```txt id="u34kpj"
Tenant usage
Token usage
Cost by tenant
Latency by graph node
Model latency
Retrieval latency
Tool success/failure
Fallback rate
HITL rate
Policy denial rate
Prompt injection attempts
PII masking count
Grounding failure rate
```

## Acceptance Criteria

```txt id="bqfqol"
Every request has trace_id.
Model calls emit token metrics.
Retrieval emits latency metrics.
Tool execution emits success/failure metrics.
Policy denials are visible.
Cost can be grouped by tenant.
Logs are structured and sanitized.
```

---

# Phase 13 — CI/CD Production Gates

## Goal

Make quality, safety, and governance enforceable through automated pipelines.

## Scope

```txt id="hqy8mv"
Lint
Format check
Type check
Unit tests
Integration tests
Security tests
Tenant isolation tests
Policy tests
Tool schema tests
RAG regression tests
Prompt injection tests
PII leakage tests
Evaluation harness
Docker build
Vulnerability scan
Deployment smoke tests
```

## Blocking Conditions

```txt id="vn6w1w"
Tenant isolation test fails.
PII leakage test fails.
Critical prompt injection test fails.
Tool authorization test fails.
Policy enforcement test fails.
Grounding regression exceeds threshold.
Critical vulnerability is detected.
Production prompt is unapproved.
Production model is unapproved.
Production policy is unapproved.
```

## Deliverables

```txt id="z2bbyc"
.github/workflows/ci.yml
.github/workflows/security.yml
.github/workflows/evaluation.yml
Docker build pipeline
Test reports
Evaluation reports
Security reports
```

## Acceptance Criteria

```txt id="h0v847"
Pull requests run test suite.
Security scan runs automatically.
Evaluation harness runs automatically.
Critical failures block merge.
Docker image builds successfully.
Smoke tests run after deployment.
```

---

# Phase 14 — Hardening and Load Testing

## Goal

Prepare the platform for high request volume and failure scenarios.

## Scope

```txt id="6ynlnu"
Load testing
Stress testing
Chaos testing
Provider failure simulation
Vector DB latency simulation
Redis failure simulation
Database connection pressure
Backpressure
Circuit breakers
Rate limits
Retry tuning
Index tuning
Cache tuning
```

## Test Scenarios

```txt id="4zqbg3"
High concurrent RAG requests
High concurrent agentic requests
Tenant burst traffic
Token budget exhaustion
Model provider unavailable
Vector DB unavailable
Redis unavailable
Slow tool execution
Prompt injection burst
Large document ingestion
Long-running HITL workflow
```

## Deliverables

```txt id="fak3qj"
k6 tests
Locust scenarios
Load test reports
Latency baseline
Throughput baseline
Failure mode report
Performance tuning notes
```

## Acceptance Criteria

```txt id="nkl3sk"
System handles target concurrent load.
System applies backpressure under overload.
Provider outage triggers approved fallback.
No unsafe response under dependency failure.
No tenant leakage under load.
p95 and p99 latency are measured.
```

---

# Phase 15 — Production Readiness

## Goal

Finalize the platform for production-like deployment.

## Scope

```txt id="krj908"
Kubernetes manifests
Helm charts
Secrets management
Environment separation
Runbooks
Backup strategy
Restore strategy
Monitoring alerts
Incident response workflow
Production configuration
Access control review
Data retention rules
```

## Deliverables

```txt id="ak0gax"
infra/k8s
infra/helm
infra/terraform or infra/opentofu
docs/RUNBOOKS.md
docs/OPERATIONS.md
docs/DEPLOYMENT.md
docs/SECURITY_REVIEW.md
docs/PRODUCTION_CHECKLIST.md
```

## Acceptance Criteria

```txt id="tqpmyj"
Application deploys to staging.
Secrets are not stored in code.
Health checks are production-ready.
Alerts are configured.
Backup and restore are documented.
Runbooks exist.
Access control is reviewed.
Production checklist is complete.
```

---

# Phase 16 — Advanced Enterprise Features

## Goal

Expand the platform beyond the first production-ready version.

## Potential Features

```txt id="9ylm2k"
Advanced policy-as-code with OPA
Temporal-based durable workflows
Advanced HITL reviewer console
Advanced governance dashboard
Advanced prompt experimentation
Multi-model evaluation dashboard
Reranking service
Hybrid search with OpenSearch
Qdrant or Milvus migration
Advanced PII classifier
Dedicated prompt injection classifier
Red-team automation
Canary prompt deployments
Canary model deployments
Tenant self-service admin
Cost forecasting
Document lineage graph
Knowledge freshness monitoring
Model drift monitoring
Embedding drift monitoring
Automated document expiration alerts
Advanced MLOps integration
```

## Acceptance Criteria

Defined per feature.

---

# 4. MVP Roadmap

The MVP should focus on proving the critical enterprise architecture without overbuilding.

## MVP Phase A — Secure Foundation

Includes:

```txt id="7hjkwc"
Project setup
FastAPI
PostgreSQL
Redis
JWT validation
Tenant Context
Audit log
Basic policy enforcement
```

Success criteria:

```txt id="v0x70s"
Authenticated requests work.
Tenant Context is mandatory.
Audit events are recorded.
Unauthorized requests fail closed.
```

---

## MVP Phase B — AI Gateway

Includes:

```txt id="0cn8i5"
AI Gateway interface
OpenAI/Azure adapter
Local adapter placeholder
Token accounting
Tenant token bucket
Fallback baseline
Model usage audit
```

Success criteria:

```txt id="mtqvet"
All model calls go through AI Gateway.
Tenant model permissions are enforced.
Token usage is tracked.
Fallback is auditable.
```

---

## MVP Phase C — Secure RAG

Includes:

```txt id="w41y3n"
Document ingestion
Document Registry
Chunking
Embeddings
pgvector
Vector Access Gateway
Tenant-safe retrieval
Grounded answer generation
Citations
```

Success criteria:

```txt id="luhwrr"
Tenant A cannot retrieve Tenant B documents.
Answer includes valid citations.
Inactive documents are not used.
Grounding failure is handled safely.
```

---

## MVP Phase D — Governed Tool Calling

Includes:

```txt id="57c3dv"
Tool Registry
Structured JSON tool proposals
Tool schema validation
Tool authorization
Tool Executor
Read-only initial tools
Tool audit
```

Success criteria:

```txt id="6rrbk0"
Invalid tool calls are rejected.
Unauthorized tools are blocked.
Tool execution is audited.
Agent cannot execute tools directly.
```

---

## MVP Phase E — Strict Agent Runtime

Includes:

```txt id="iwrzq1"
Agent State
GraphRunner
Bounded loop
Policy hooks
Tool loop
Output validation
CrewAI adapter baseline
```

Success criteria:

```txt id="1aukgq"
Agent workflow follows strict graph.
Loop limits are enforced.
Tool calls go through Tool Executor.
Model calls go through AI Gateway.
Retrieval goes through Vector Access Gateway.
```

---

## MVP Phase F — HITL, Evaluation, Observability

Includes:

```txt id="6keymn"
HITL task creation
Basic reviewer flow
Evaluation harness
Prompt injection tests
PII leakage tests
OpenTelemetry
Prometheus metrics
Grafana dashboard
CI/CD gates
```

Success criteria:

```txt id="qruq90"
High-risk cases trigger HITL.
Critical evals run in CI.
Observability shows traces and metrics.
Unsafe deployments are blocked.
```

---

# 5. Suggested Milestone Order

```txt id="efmm37"
M1 - Repository and local environment
M2 - Auth, Tenant Context, and Audit
M3 - AI Gateway with token control
M4 - Document Registry and ingestion
M5 - Vector Access Gateway and tenant-safe retrieval
M6 - Grounded RAG answers with citations
M7 - Tool Registry and Tool Executor
M8 - Strict Agent Runtime
M9 - HITL workflow
M10 - Governance registries
M11 - Evaluation harness
M12 - Observability dashboards
M13 - CI/CD gates
M14 - Load testing and hardening
M15 - Production readiness
```

---

# 6. Recommended First Sprint

The first sprint should not implement CrewAI or a complex agent.

The first sprint should create the foundation that makes the rest safe.

## Sprint 1 Goal

Build the secure backend skeleton with tenant context and audit.

## Sprint 1 Scope

```txt id="08q35r"
Project structure
FastAPI app
Docker Compose
PostgreSQL
Redis
Configuration management
JWT validation placeholder
TenantContext model
Request context middleware
Audit event model
Basic policy service
Health endpoints
Initial tests
Initial CI
```

## Sprint 1 Deliverables

```txt id="so75wj"
GET /health
GET /ready
TenantContext model
AuditEvent model
RequestContext middleware
PolicyDecision model
Base test suite
Docker Compose
CI workflow
```

## Sprint 1 Critical Acceptance Criteria

```txt id="n48205"
A request without valid Tenant Context fails closed.
Every accepted request receives request_id and trace_id.
Every denied request creates an audit event.
No AI, RAG, or tool operation can be called without Tenant Context.
```

---

# 7. Recommended Second Sprint

## Sprint 2 Goal

Build the AI Gateway baseline.

## Sprint 2 Scope

```txt id="ry210j"
AI Gateway interface
Mock provider
OpenAI/Azure provider adapter
Local provider placeholder
Model Registry baseline
Tenant token bucket
Usage tracking
Fallback baseline
Model call audit
Model call traces
```

## Sprint 2 Critical Acceptance Criteria

```txt id="exq9t1"
All model calls go through AI Gateway.
Tenant cannot use unapproved model.
Token budget is enforced.
Model call is audited.
Fallback is recorded.
```

---

# 8. Recommended Third Sprint

## Sprint 3 Goal

Build secure document ingestion and tenant-safe retrieval.

## Sprint 3 Scope

```txt id="l8crzg"
Document Registry
Document ingestion endpoint
Chunking
Embedding through AI Gateway
pgvector index
Vector Access Gateway
Tenant filter injection
Retrieval endpoint
Cross-tenant retrieval tests
```

## Sprint 3 Critical Acceptance Criteria

```txt id="qu3mj2"
Tenant A cannot retrieve Tenant B chunks.
Inactive documents are excluded.
Vector search cannot run outside Vector Access Gateway.
Retrieved chunks include document version.
```

---

# 9. Recommended Fourth Sprint

## Sprint 4 Goal

Generate grounded RAG answers with citations.

## Sprint 4 Scope

```txt id="tzm8l0"
RAG Orchestrator
Context assembly
Grounded answer prompt
Citation builder
Grounding validator
Output validator baseline
Safe refusal
RAG answer endpoint
```

## Sprint 4 Critical Acceptance Criteria

```txt id="a1it2k"
Answer includes citations.
Citation includes document_id, document_version, and chunk_id.
Unsupported answer fails grounding validation.
Grounding failure is audited.
```

---

# 10. Recommended Fifth Sprint

## Sprint 5 Goal

Add structured tool calling and Tool Executor.

## Sprint 5 Scope

```txt id="kg1n2e"
Tool Registry
Tool schema model
Tool proposal parser
Tool authorization
Tool Executor
Read-only tools
Tool audit events
Tool tests
```

## Sprint 5 Critical Acceptance Criteria

```txt id="gu4v0f"
Invalid tool JSON is rejected.
Unauthorized tool is blocked.
Tool execution is audited.
LLM cannot execute tools directly.
```

---

# 11. Recommended Sixth Sprint

## Sprint 6 Goal

Implement strict graph-based Agent Runtime.

## Sprint 6 Scope

```txt id="cfwxg2"
AgentState
GraphRunner
Runtime nodes
Bounded loop
Policy hooks
Tool loop
Retrieval node
Grounding node
Output validation node
CrewAI adapter baseline
```

## Sprint 6 Critical Acceptance Criteria

```txt id="ddumw4"
Runtime follows approved graph.
Loop cannot exceed max_steps.
Tool call budget is enforced.
Token and cost budgets are enforced.
Invalid state fails safely.
```

---

# 12. Recommended Seventh Sprint

## Sprint 7 Goal

Add HITL and evaluation baseline.

## Sprint 7 Scope

```txt id="418lwo"
HITL task model
HITL API
Reviewer decision model
High-risk trigger
Evaluation harness baseline
Prompt injection tests
PII leakage tests
Tenant leakage tests
CI eval step
```

## Sprint 7 Critical Acceptance Criteria

```txt id="how7gy"
High-risk requests create HITL task.
Final answer waits for approval when required.
Critical security evals run in CI.
Failed critical eval blocks deployment.
```

---

# 13. Recommended Eighth Sprint

## Sprint 8 Goal

Add observability, dashboards, and production gates.

## Sprint 8 Scope

```txt id="0hrggv"
OpenTelemetry traces
Prometheus metrics
Grafana dashboard
Structured logs
Cost dashboard
Tenant usage endpoint
CI/CD hardening
Security scans
Load test baseline
```

## Sprint 8 Critical Acceptance Criteria

```txt id="xpez7n"
Trace exists for every request.
Metrics show latency, tokens, cost, fallback, HITL, and errors.
Logs are structured and sanitized.
Security scans run in CI.
Load test baseline exists.
```

---

# 14. Definition of Done

A feature is only considered complete when:

```txt id="qw0y7w"
Code is implemented.
Unit tests exist.
Integration tests exist when applicable.
Tenant isolation is tested when applicable.
Security behavior is tested when applicable.
Audit events are emitted when applicable.
Traces are emitted when applicable.
Metrics are emitted when applicable.
Documentation is updated.
Failure behavior is defined.
CI passes.
```

For AI-related features, also require:

```txt id="vniuiy"
Prompt version recorded.
Model version recorded.
Policy version recorded.
Evaluation added or updated.
Grounding behavior tested when applicable.
PII behavior tested when applicable.
Prompt injection behavior tested when applicable.
```

---

# 15. Critical Risks

## Risk 1 — Building agents before security

If agents are built before tenant enforcement, the system may become difficult to secure later.

Mitigation:

```txt id="9q82zf"
Build Tenant Context, AI Gateway, Vector Access Gateway, and Tool Executor before complex agents.
```

---

## Risk 2 — Framework lock-in

If CrewAI or another framework owns execution control, governance becomes weaker.

Mitigation:

```txt id="4eyv8q"
Use frameworks behind adapters.
Keep policy, tool execution, retrieval, audit, and model access in internal platform code.
```

---

## Risk 3 — Cross-tenant leakage

The most critical failure mode for a multi-tenant banking platform is data leakage across tenants.

Mitigation:

```txt id="170nq4"
Enforce tenant isolation at API, service, database, vector, cache, and audit layers.
Add cross-tenant leakage tests to CI.
```

---

## Risk 4 — Unsafe tool execution

Agentic tools can create business and security risk if not governed.

Mitigation:

```txt id="sdu2qo"
LLM proposes tool calls only.
Runtime validates.
Tool Executor executes.
Policy Engine authorizes.
HITL gates high-risk tools.
```

---

## Risk 5 — Poor grounding

RAG systems may generate plausible unsupported answers.

Mitigation:

```txt id="06b2g2"
Require citations.
Validate grounding.
Refuse or escalate insufficiently supported answers.
Evaluate RAG regressions in CI.
```

---

## Risk 6 — Invisible cost growth

Agent loops and large-context retrieval can become expensive.

Mitigation:

```txt id="ot5sb5"
Token buckets, cost budgets, model routing, caching, fallback, and usage dashboards.
```

---

## Risk 7 — Prompt injection

User input or retrieved documents may attempt to override system behavior.

Mitigation:

```txt id="0q4je5"
Input scanner, retrieved content sanitizer, tool firewall, output validator, and security evals.
```

---

# 16. Roadmap Summary

The platform should be built in this order:

```txt id="9ft94x"
1. Architecture and threat model
2. Project foundation
3. Tenant Context, security, and audit
4. AI Gateway
5. Document ingestion
6. Tenant-safe retrieval
7. Grounded RAG answers
8. Structured tool calling
9. Strict graph Agent Runtime
10. HITL
11. Governance registries
12. Evaluation harness
13. Observability and cost control
14. CI/CD gates
15. Load testing and hardening
16. Production readiness
17. Advanced enterprise features
```

The most important roadmap decision is to build the trusted platform first and agentic autonomy second.

The system should evolve from:

```txt id="ylr1ap"
Secure AI request platform
        |
        v
Tenant-safe RAG platform
        |
        v
Governed tool-calling platform
        |
        v
Strict agentic RAG runtime
        |
        v
Enterprise AI operating platform
```

This roadmap ensures that the final system is not only intelligent, but also secure, auditable, governable, scalable, and maintainable.

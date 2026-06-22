# STACK

## 1. Overview

This document defines the recommended technology stack for the governed multi-tenant agentic RAG platform.

The stack is designed for an internal financial institution use case, with emphasis on:

* Security
* Tenant isolation
* Maintainability
* Observability
* Auditability
* Scalability
* LLMOps/MLOps governance
* Local and API-based model support
* Structured tool calling
* Strict agent graph execution
* Production readiness

The system must not be built as a simple chatbot application. The stack must support a governed AI platform where models, tools, retrieval, tenants, prompts, documents, policies, and human approvals are controlled through explicit runtime boundaries.

---

## 2. Stack Principles

The technology choices follow these principles:

1. **Security-first**
   All sensitive operations must enforce authentication, authorization, tenant context, audit logging, and policy validation.

2. **AI provider abstraction**
   The system must support both API-based and local models through a controlled AI Gateway.

3. **Framework independence**
   Agent frameworks such as CrewAI, LangChain, or LangGraph may be used, but must not become the core security boundary.

4. **Replaceable infrastructure**
   The platform should allow replacement of vector database, model provider, embedding provider, orchestration framework, and observability backend.

5. **Production observability**
   Logs, metrics, traces, audit events, cost metrics, and evaluation results must be first-class features.

6. **Tenant-aware by design**
   Every layer must support tenant isolation.

7. **Fail-safe behavior**
   The system must fail closed when security, policy, grounding, tenant, or authorization checks fail.

---

## 3. Recommended Core Stack

### 3.1 Language

```txt id="p1ab07"
Python 3.12+
```

Python is the main language for the platform because of its strong AI ecosystem, mature API frameworks, data tooling, agent frameworks, evaluation libraries, and integration support.

Used for:

* Backend API
* Agent Runtime
* RAG pipeline
* AI Gateway adapters
* Tool Executor
* Evaluation Harness
* Document ingestion
* Observability instrumentation
* Security and policy workflows

---

### 3.2 Backend API

```txt id="5dzj88"
FastAPI
Pydantic v2
Uvicorn
Gunicorn
```

FastAPI is the primary backend framework.

Used for:

* Public internal API
* Tenant-aware AI request endpoints
* Document ingestion endpoints
* HITL endpoints
* Admin and governance endpoints
* Trace and audit lookup endpoints
* Health checks
* Usage reporting

Pydantic v2 is used for:

* Request validation
* Response validation
* Tool schemas
* Agent state schemas
* Policy input/output schemas
* AI Gateway contracts
* RAG contracts

---

### 3.3 Application Architecture

Recommended pattern:

```txt id="0kjm5m"
Modular Monolith first
Service-ready package boundaries
```

The first version should be implemented as a modular monolith with strict internal boundaries. This reduces distributed system complexity while preserving a clean path to microservices if scale demands it.

Suggested modules:

```txt id="7ow4ak"
apps/api
packages/security
packages/agent_runtime
packages/ai_gateway
packages/rag
packages/tools
packages/governance
packages/observability
packages/evaluation
packages/ingestion
```

Later, high-load components can be extracted into independent services.

---

## 4. Database Stack

### 4.1 Primary Relational Database

```txt id="b1v6q9"
PostgreSQL 16+
```

PostgreSQL is the primary system database.

Used for:

* Tenants
* Users
* Roles
* Scopes
* Sessions
* Requests
* Audit records
* Prompt registry
* Model registry
* Tool registry
* Policy registry
* Document registry
* HITL tasks
* Usage records
* Evaluation results

PostgreSQL is also useful because it supports:

* Strong relational integrity
* JSONB fields
* Row-level security
* Mature indexing
* Transactional consistency
* Enterprise deployment compatibility

---

### 4.2 ORM and Migrations

```txt id="03y20c"
SQLAlchemy 2.x
Alembic
asyncpg
```

Used for:

* Async database access
* Schema migrations
* Tenant-aware query patterns
* Transaction control
* Repository layer
* Audit writes
* Registry persistence

---

### 4.3 Row-Level Security

```txt id="ehznbx"
PostgreSQL Row-Level Security
```

RLS should be considered for sensitive tenant-scoped tables.

Used for:

* Defense-in-depth tenant isolation
* Preventing accidental cross-tenant access
* Database-level policy enforcement

Application-level tenant enforcement is still required. RLS is an additional layer, not a replacement.

---

## 5. Vector Database Stack

### 5.1 Recommended MVP Vector Store

```txt id="t5rkam"
PostgreSQL + pgvector
```

This is the recommended first implementation for a strong MVP.

Advantages:

* Simpler deployment
* Same database family as core data
* Easier local development
* Transactional metadata alignment
* Good enough for early production-like RAG workloads
* Easier demonstration of tenant filtering and document versioning

Used for:

* Document chunk embeddings
* Tenant-scoped vector search
* Metadata filtering
* Document version-aware retrieval

---

### 5.2 Scale-Oriented Vector Store Options

For higher scale, the architecture should support replacing or extending pgvector with:

```txt id="uxiyjs"
Qdrant
Milvus
Weaviate
OpenSearch Vector Search
```

Recommended production upgrade path:

```txt id="ql4nap"
MVP: PostgreSQL + pgvector
Scale phase: Qdrant or OpenSearch
Enterprise search phase: hybrid OpenSearch + vector DB
```

---

### 5.3 Vector Access Rule

No application component should access the vector database directly except:

```txt id="c6t43e"
Vector Access Gateway
```

All vector search must pass through this layer to enforce:

* Tenant ID
* ACLs
* Document status
* Document version
* Classification
* User clearance
* Role scopes

---

## 6. Cache and Rate Limit Stack

### 6.1 Cache

```txt id="93v3hq"
Redis 7+
```

Redis is used for:

* Tenant token buckets
* Request rate limiting
* Short-lived session state
* Embedding cache
* Retrieval cache
* Safe response cache
* Tool result cache
* Distributed locks
* Background job coordination

---

### 6.2 Cache Rules

Cache keys must include tenant and policy context.

Required key components:

```txt id="xnsds8"
tenant_id
user_scope_hash
query_hash
prompt_version
model_version
embedding_model_version
document_version
policy_version
classification_level
```

Global cache must not be used for sensitive responses.

---

## 7. Background Jobs and Workflow Engine

### 7.1 MVP Recommendation

```txt id="grgd1j"
Celery
Redis or RabbitMQ
```

Used for:

* Document ingestion
* Embedding generation
* Batch evaluation
* Audit export
* Scheduled maintenance
* Async HITL notifications
* Re-indexing jobs

---

### 7.2 Enterprise Workflow Option

```txt id="sb1evk"
Temporal
```

Temporal is recommended for more advanced workflow orchestration.

Used for:

* Long-running workflows
* Durable HITL processes
* Retryable tool workflows
* Stateful approval chains
* Reliable document processing
* Enterprise-grade orchestration

Recommended path:

```txt id="ydbb80"
MVP: Celery
Advanced production: Temporal
```

---

## 8. Agent and Orchestration Stack

### 8.1 Agent Framework

```txt id="xvhte8"
CrewAI
```

CrewAI may be used for:

* Agent definitions
* Crew definitions
* Task composition
* Agent collaboration patterns
* High-level workflow abstractions

However, CrewAI must not be the trusted security boundary.

Recommended integration pattern:

```txt id="ai495c"
CrewAI
  |
  v
CrewAI Adapter
  |
  v
Internal Agent Runtime
  |
  v
Policy Engine, Tool Executor, AI Gateway, RAG Orchestrator
```

CrewAI should be treated as an orchestration aid, not as the authority for:

* Authorization
* Tenant enforcement
* Tool execution
* Model access
* Audit
* HITL
* Policy validation

---

### 8.2 Strict Graph Runtime

Recommended options:

```txt id="ss166n"
Custom GraphRunner
LangGraph
Hybrid: LangGraph concepts + internal runtime
```

For this project, the safest recommendation is:

```txt id="mgk3yo"
Custom internal GraphRunner first
Framework adapters around it
```

Why:

* Full control over state transitions
* Easier security enforcement
* Explicit budget control
* Easier auditability
* Avoids framework lock-in
* Better for enterprise governance

The graph runtime should implement:

* Graph nodes
* State transitions
* Step budget
* Tool call budget
* Token budget
* Cost budget
* Retry policy
* HITL gates
* Failure handling
* Audit hooks
* Observability hooks

---

### 8.3 Agent Runtime Core Dependencies

```txt id="zrg3pa"
Pydantic v2
tenacity
networkx optional
orjson
structlog
```

Used for:

* State modeling
* Retry policies
* Graph definition
* Fast JSON serialization
* Structured logging

---

## 9. AI Gateway Stack

### 9.1 Recommended Gateway Strategy

```txt id="krwo5y"
Internal AI Gateway abstraction
Optional LiteLLM adapter
```

The project should define its own AI Gateway interface. LiteLLM or similar tools may be used behind the gateway, but the internal contract must belong to the platform.

The AI Gateway is responsible for:

* Model routing
* Provider abstraction
* Local/API model support
* Token bucket enforcement
* Cost tracking
* Fallback
* Retry
* Timeout
* Circuit breaker
* Request normalization
* Response normalization
* Cache policy
* Observability
* Audit metadata

---

### 9.2 API Model Providers

Initial supported providers may include:

```txt id="54rbkf"
Azure OpenAI
OpenAI API
Anthropic
AWS Bedrock
Google Vertex AI
```

For financial institutions, Azure OpenAI is often a strong enterprise default because of cloud enterprise alignment, private networking options, and governance integration.

---

### 9.3 Local Model Runtime

Recommended options:

```txt id="qxkqod"
vLLM
Ollama
llama.cpp
Text Generation Inference
```

Recommended path:

```txt id="kek6f4"
MVP local development: Ollama
Production local serving: vLLM
CPU/offline fallback: llama.cpp
```

Local models are useful for:

* Lower sensitivity workloads
* Cost control
* Offline fallback
* Internal experimentation
* Embeddings
* Specific classification tasks
* PII detection support
* Prompt injection classification support

---

### 9.4 Embedding Providers

The platform must support both API and local embeddings.

API options:

```txt id="q4z36x"
OpenAI embeddings
Azure OpenAI embeddings
Cohere embeddings
Voyage embeddings
```

Local options:

```txt id="84fqvw"
sentence-transformers
BGE embeddings
E5 embeddings
Nomic embeddings
```

Recommended MVP path:

```txt id="zrr8ha"
API embeddings first for quality and speed
Local embeddings adapter included from the beginning
```

---

## 10. RAG Stack

### 10.1 RAG Pipeline Components

```txt id="g04vzv"
Document parser
Chunker
Embedding generator
Vector indexer
Retriever
Reranker
Citation builder
Grounding validator
```

---

### 10.2 Document Parsing

Recommended libraries:

```txt id="rta8wj"
pypdf
PyMuPDF
unstructured
python-docx
beautifulsoup4
markdown
```

Used for:

* PDF parsing
* DOCX parsing
* HTML parsing
* Markdown parsing
* Plain text parsing

For production financial documents, parsing must preserve:

* Page numbers
* Section titles
* Tables when possible
* Source metadata
* Document version
* Content hash

---

### 10.3 Chunking

Recommended approach:

```txt id="66pxaa"
Custom chunking strategy
Recursive text splitting
Structure-aware chunking where possible
```

The chunking strategy must be versioned.

Chunk metadata must include:

```txt id="ea0wz7"
document_id
document_version
tenant_id
chunk_id
chunk_index
page
section
content_hash
chunking_strategy_version
embedding_model_version
classification
status
```

---

### 10.4 Retrieval

Supported retrieval modes:

```txt id="m55pdq"
semantic
keyword
hybrid
reranked hybrid
```

Recommended MVP:

```txt id="3x6thk"
semantic + metadata filters
```

Recommended production evolution:

```txt id="bkmmu4"
hybrid search + reranking + grounding validation
```

---

### 10.5 Reranking

Recommended options:

```txt id="a13nib"
Cohere Rerank
BGE reranker
Cross-encoder reranker
Local reranking model
```

Reranking should be introduced after the first secure RAG baseline is working.

Security must remain in the Vector Access Gateway before reranking.

---

## 11. Tool Execution Stack

### 11.1 Tool Schema

```txt id="8tkakt"
Pydantic v2
JSON Schema
```

Every tool must have:

* Input schema
* Output schema
* Version
* Risk level
* Required scopes
* Allowed tenants
* Timeout
* Idempotency flag
* HITL requirement
* Audit level

---

### 11.2 Tool Executor

The Tool Executor should be implemented internally.

Responsibilities:

* Validate tool proposal
* Validate input schema
* Authorize tool call
* Enforce timeout
* Execute tool
* Capture result
* Capture error
* Emit audit events
* Emit traces
* Return structured result

---

### 11.3 Sandboxing

For tools that execute dynamic code or external actions, consider:

```txt id="k5fpzc"
Restricted execution environment
Containerized execution
Network policy restrictions
Timeouts
Resource limits
Allowlisted destinations
```

The MVP should avoid arbitrary code execution tools.

---

## 12. Policy and Authorization Stack

### 12.1 Authorization Model

Recommended approach:

```txt id="2p0tvj"
JWT + RBAC + ABAC + Policy Engine
```

RBAC handles broad permissions.

ABAC handles contextual rules such as:

* Tenant
* Department
* Clearance level
* Data classification
* Risk level
* Tool sensitivity
* Environment
* Request mode

---

### 12.2 Policy Engine Options

Recommended options:

```txt id="neyjt4"
Open Policy Agent
Casbin
Custom policy service
```

Recommended MVP:

```txt id="jypz2c"
Custom policy engine with explicit Python rules
```

Recommended production evolution:

```txt id="eb8i22"
OPA for externalized policy-as-code
```

Policy decisions must be versioned and auditable.

---

### 12.3 JWT and Identity

Recommended libraries:

```txt id="ftdzbg"
python-jose
PyJWT
Authlib
```

JWT validation must include:

* Signature validation
* Issuer validation
* Audience validation
* Expiration validation
* Required claims validation
* JWKS support

---

## 13. PII and Security Guardrails Stack

### 13.1 PII Detection

Recommended options:

```txt id="05f11l"
Microsoft Presidio
Custom regex detectors
spaCy optional
Local classifier optional
```

Recommended approach:

```txt id="pbh7fu"
Custom Brazilian financial regex detectors + Presidio-style abstraction
```

The system should detect:

* CPF
* CNPJ
* E-mail
* Phone number
* Account identifiers
* Agency identifiers
* Address-like patterns
* Internal customer identifiers

---

### 13.2 Prompt Injection Detection

Recommended components:

```txt id="nelugr"
Rule-based scanner
LLM-based classifier through AI Gateway
Prompt injection test suite
Output validator
Retrieved content sanitizer
```

Recommended MVP:

```txt id="lesiv0"
Rule-based scanner + risk classifier prompt
```

Recommended production evolution:

```txt id="w68l0w"
Dedicated classifier model + adversarial test suite
```

---

### 13.3 Output Validation

Output validation should be internal and policy-driven.

Components:

```txt id="rvajxk"
PII scanner
Citation validator
Grounding validator
Policy validator
Secret scanner
Unsafe instruction detector
```

Possible libraries:

```txt id="1lzvxv"
detect-secrets
presidio-style detectors
custom validators
```

---

## 14. Human-in-the-Loop Stack

### 14.1 HITL Backend

```txt id="yw4u3b"
FastAPI
PostgreSQL
Redis
Celery or Temporal
```

Used for:

* Review task creation
* Review task assignment
* Approval workflow
* Rejection workflow
* Edit-before-release workflow
* Audit trail

---

### 14.2 HITL Frontend

Recommended options:

```txt id="ds9fiw"
React
Next.js
Internal admin console
```

The initial HITL UI can be basic.

Required features:

* List pending reviews
* Inspect draft answer
* Inspect citations
* Inspect retrieved sources
* Inspect tool proposal
* Approve
* Reject
* Edit
* Add notes
* View trace ID

---

## 15. Observability Stack

### 15.1 Tracing

```txt id="7ydzjr"
OpenTelemetry
Tempo or Jaeger
```

OpenTelemetry should be the standard instrumentation layer.

Used for:

* Request tracing
* Agent graph node tracing
* LLM call tracing
* Retrieval tracing
* Tool execution tracing
* HITL tracing
* Policy decision tracing

---

### 15.2 Metrics

```txt id="kax46x"
Prometheus
Grafana
```

Used for:

* Latency
* Throughput
* Tokens
* Cost
* Tenant usage
* Fallback rate
* HITL rate
* Retrieval performance
* Tool errors
* Policy denials
* Prompt injection attempts

---

### 15.3 Logs

```txt id="kxcww1"
structlog
Loki
Grafana
```

Logs must be:

* Structured
* Sanitized
* Tenant-aware
* Correlated with trace ID
* Free from raw sensitive data unless stored in protected audit channel

---

### 15.4 Error Tracking

```txt id="v2g7fz"
Sentry
```

Used for:

* Application exceptions
* Runtime errors
* Failed background jobs
* API errors
* Tool execution failures

---

## 16. Audit Stack

### 16.1 Audit Storage

Recommended MVP:

```txt id="vqnopr"
PostgreSQL append-only audit table
```

Recommended production evolution:

```txt id="pahhvf"
Append-only audit store
Object storage archive
WORM-compatible storage if required
```

Audit records should be protected from normal application modification.

---

### 16.2 Audit Format

Recommended format:

```txt id="oqppkk"
Structured JSON event
```

Audit events must include:

* Tenant ID
* User ID
* Request ID
* Trace ID
* Event type
* Resource type
* Resource ID
* Policy version
* Timestamp
* Sanitized event payload

---

## 17. Evaluation and Testing Stack

### 17.1 Unit and Integration Testing

```txt id="iinyef"
pytest
pytest-asyncio
httpx
respx
factory_boy
faker
```

Used for:

* API tests
* Agent runtime tests
* Tool validation tests
* Tenant isolation tests
* Policy tests
* AI Gateway mock tests
* RAG tests

---

### 17.2 Evaluation Harness

Recommended options:

```txt id="ejlphu"
custom eval harness
promptfoo
RAGAS
DeepEval
```

Recommended approach:

```txt id="fd7v1n"
Custom evaluation harness as primary
External libraries as adapters
```

The evaluation harness should test:

* RAG quality
* Citation correctness
* Grounding
* Prompt regressions
* Prompt injection resistance
* Cross-tenant leakage
* PII leakage
* Tool misuse
* Policy enforcement
* Cost and latency

---

### 17.3 Load Testing

```txt id="ug0fje"
k6
Locust
```

Recommended:

```txt id="wk11os"
k6 for API-level load tests
Locust for scenario-based agent workflows
```

---

### 17.4 Security Testing

Recommended tools:

```txt id="upmn9g"
Bandit
pip-audit
Semgrep
detect-secrets
Trivy
OWASP ZAP optional
```

Used for:

* Python static security checks
* Dependency vulnerabilities
* Secret detection
* Container scanning
* API security testing

---

## 18. CI/CD Stack

### 18.1 Source Control

```txt id="1lav9c"
Git
GitHub
```

---

### 18.2 CI/CD

Recommended options:

```txt id="bo9g3g"
GitHub Actions
GitLab CI
Azure DevOps Pipelines
```

For financial institutions, Azure DevOps may be common. For portfolio/open-source development, GitHub Actions is simpler.

Recommended project default:

```txt id="v4ue8l"
GitHub Actions
```

---

### 18.3 CI Pipeline Steps

```txt id="z9ss52"
lint
format check
type check
unit tests
integration tests
security tests
tenant isolation tests
policy tests
tool schema tests
RAG regression tests
prompt injection tests
PII leakage tests
evaluation harness
Docker build
container vulnerability scan
deployment smoke tests
```

---

### 18.4 Formatting and Typing

```txt id="q7kbxy"
ruff
black optional
mypy
pyright optional
```

Recommended:

```txt id="gq2zzd"
ruff for linting and formatting
mypy for static typing
```

---

## 19. Containerization and Deployment Stack

### 19.1 Containers

```txt id="q9xdd4"
Docker
Docker Compose
```

Docker Compose is used for local development.

Local services:

```txt id="8hzkcc"
api
worker
postgres
redis
vector-db
observability
local-llm optional
```

---

### 19.2 Production Orchestration

```txt id="7f4dfz"
Kubernetes
Helm
```

Used for:

* API scaling
* Worker scaling
* AI Gateway scaling
* RAG service scaling
* Tool Executor isolation
* Observability deployment
* Config and secret management

---

### 19.3 Infrastructure as Code

Recommended options:

```txt id="ske3w0"
Terraform
OpenTofu
Helm
```

Recommended:

```txt id="2e5l5x"
Terraform/OpenTofu for cloud infrastructure
Helm for Kubernetes application deployment
```

---

## 20. Secrets Management

Recommended options:

```txt id="vafqjc"
HashiCorp Vault
Azure Key Vault
AWS Secrets Manager
Kubernetes Secrets with external secret operator
```

For financial institutions, use cloud-native or enterprise-approved secret management.

Recommended abstraction:

```txt id="lujk1g"
SecretProvider interface
```

This allows local `.env` development while supporting Vault or cloud secret managers in production.

---

## 21. Configuration Management

Recommended:

```txt id="trssjt"
Pydantic Settings
environment variables
typed config objects
```

Configuration should support:

* Environment
* Tenant defaults
* Model providers
* Token budgets
* Cache settings
* Database URLs
* Secret references
* Policy versions
* Feature flags

Avoid hardcoded model names, API keys, tenant IDs, or provider-specific configuration in business logic.

---

## 22. Frontend Stack

### 22.1 Internal Portal

Recommended:

```txt id="kn5lpi"
React
Next.js
TypeScript
Tailwind CSS
```

Used for:

* Chat interface
* Source/citation viewer
* HITL review console
* Admin console
* Usage dashboards
* Trace viewer
* Governance views

---

### 22.2 Alternative Lightweight Admin UI

For MVP, an internal admin UI may be built with:

```txt id="n7fqmo"
Streamlit
Gradio
FastAPI templates
```

Recommended path:

```txt id="3wmbcy"
MVP: simple internal admin UI
Production: React/Next.js admin console
```

---

## 23. Development Tooling

Recommended:

```txt id="619nms"
Poetry or uv
pre-commit
ruff
mypy
pytest
Docker Compose
Makefile
```

Recommended package manager:

```txt id="fyi414"
uv
```

Alternative:

```txt id="6t6l5c"
Poetry
```

For a portfolio project, `uv` gives fast dependency management and modern Python workflow.

---

## 24. Recommended Repository Stack Layout

```txt id="h2c9o7"
sentinel-graph/
  apps/
    api/
    worker/
    admin/

  packages/
    security/
    agent_runtime/
    ai_gateway/
    rag/
    tools/
    governance/
    observability/
    evaluation/
    ingestion/

  infra/
    docker/
    k8s/
    terraform/
    helm/

  tests/
    unit/
    integration/
    security/
    evals/
    load/

  docs/
    ARCHITECTURE.md
    THREAT_MODEL.md
    TENANT_MODEL.md
    DATA_FLOW.md
    SECURITY_PRINCIPLES.md
    STACK.md
    SPEC.md
    ROADMAP.md
    IMPLEMENTATION_PLAN.md
```

---

## 25. Recommended MVP Stack

The MVP should use a stack that is powerful enough to demonstrate enterprise architecture without becoming unnecessarily complex.

```txt id="te8dth"
Python 3.12+
FastAPI
Pydantic v2
PostgreSQL 16+
pgvector
Redis
SQLAlchemy 2.x
Alembic
Celery
CrewAI behind adapter
Custom GraphRunner
Custom AI Gateway interface
OpenAI/Azure OpenAI adapter
Ollama local adapter
sentence-transformers local embedding adapter
OpenTelemetry
Prometheus
Grafana
structlog
pytest
RAGAS or custom eval harness
GitHub Actions
Docker Compose
```

---

## 26. Recommended Production Stack

A production-grade version may evolve into:

```txt id="ul1n42"
Python 3.12+
FastAPI
PostgreSQL 16+
Redis Cluster
Qdrant or OpenSearch Vector Search
Kubernetes
Helm
Terraform/OpenTofu
Temporal
Azure OpenAI / OpenAI / Bedrock / Vertex adapters
vLLM for local model serving
OpenTelemetry
Prometheus
Grafana
Loki
Tempo or Jaeger
Sentry
Vault or cloud secret manager
OPA
React/Next.js admin console
k6
Semgrep
Trivy
detect-secrets
custom eval harness
```

---

## 27. Technology Decision Matrix

| Area          | MVP Choice                 | Production Evolution   | Reason                                   |
| ------------- | -------------------------- | ---------------------- | ---------------------------------------- |
| Language      | Python                     | Python                 | Best AI ecosystem                        |
| API           | FastAPI                    | FastAPI                | Async, typed, production-ready           |
| Database      | PostgreSQL                 | PostgreSQL             | Strong relational and governance support |
| Vector Store  | pgvector                   | Qdrant/OpenSearch      | Simpler MVP, scalable later              |
| Cache         | Redis                      | Redis Cluster          | Token buckets, cache, coordination       |
| Jobs          | Celery                     | Temporal               | MVP simplicity, durable workflows later  |
| Agents        | CrewAI adapter             | CrewAI/custom hybrid   | Avoid framework lock-in                  |
| Graph Runtime | Custom GraphRunner         | Custom/Temporal hybrid | Security and audit control               |
| AI Gateway    | Custom interface           | Custom + adapters      | Provider abstraction                     |
| Local LLM     | Ollama                     | vLLM                   | Easy local dev, scalable serving         |
| Embeddings    | API + local adapter        | API/local hybrid       | Flexibility and cost control             |
| Policy        | Custom Python rules        | OPA                    | Faster MVP, policy-as-code later         |
| Observability | OpenTelemetry + Prometheus | OTel + Grafana stack   | Standard production observability        |
| Logs          | structlog                  | Loki/Grafana           | Structured logs                          |
| Frontend      | Minimal UI                 | React/Next.js          | Start simple, scale UX later             |
| CI/CD         | GitHub Actions             | GitHub/Azure DevOps    | Easy automation                          |
| Load Testing  | k6                         | k6 + Locust            | API and scenario testing                 |
| Security      | Bandit/Semgrep/Trivy       | Full security pipeline | Defense-in-depth                         |

---

## 28. Initial Implementation Stack

The first implementation should use the following stack:

```txt id="r5wfxa"
Python 3.12
FastAPI
Pydantic v2
PostgreSQL 16
pgvector
Redis
SQLAlchemy 2.x
Alembic
Celery
Docker Compose
OpenTelemetry
Prometheus
Grafana
structlog
pytest
ruff
mypy
GitHub Actions
Custom Agent Runtime
Custom AI Gateway
Custom Tool Executor
Custom Vector Access Gateway
CrewAI Adapter
OpenAI/Azure OpenAI provider adapter
Ollama local provider adapter
```

This gives the project enough strength to demonstrate senior-level enterprise architecture while keeping the first implementation realistic.

---

## 29. Explicit Non-Choices

The following choices should be avoided in the initial version:

### 29.1 No Direct LLM Calls in Business Logic

Do not call OpenAI, Azure OpenAI, Anthropic, Ollama, or any other provider directly from business services.

All calls must go through:

```txt id="mkjozw"
AI Gateway
```

---

### 29.2 No Direct Vector DB Calls from Agents

Agents must not query pgvector, Qdrant, OpenSearch, or any vector database directly.

All retrieval must go through:

```txt id="dp5b63"
Vector Access Gateway
```

---

### 29.3 No Tool Execution by the LLM

The LLM must not execute tools.

The LLM may only propose structured tool calls.

Execution must happen through:

```txt id="4qg1ur"
Tool Executor
```

---

### 29.4 No Security Logic Only in Prompts

Prompts may guide behavior, but security must be enforced in application code and policy layers.

---

### 29.5 No Framework Lock-In

Do not make CrewAI, LangChain, LangGraph, or any other framework the central security authority.

Frameworks must be behind adapters.

---

## 30. Stack Summary

The recommended stack is centered on:

```txt id="latdlx"
Python
FastAPI
PostgreSQL
pgvector
Redis
Custom AI Gateway
Custom Agent Runtime
Custom Tool Executor
Custom Vector Access Gateway
CrewAI adapter
OpenTelemetry
Prometheus
Grafana
pytest
Docker
GitHub Actions
```

The most important architectural decision is not the individual library choice. It is the separation of trusted control layers from untrusted AI behavior.

The stack must support the following invariant:

> Models reason, but the platform governs.

Every technology choice must preserve this invariant.

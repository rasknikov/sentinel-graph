# TENANT_MODEL

## 1. Overview

This document defines the tenant model for the governed multi-tenant agentic RAG platform.

The platform is designed for internal use in a financial institution and must support multiple internal departments, business units, or organizational domains while preserving strict isolation across data, documents, tools, prompts, model access, audit records, cache entries, vector search, usage budgets, and human approval workflows.

The tenant model is a core security boundary.

The system must assume that:

* Tenant isolation cannot be delegated to the LLM.
* Tenant identity cannot be inferred from natural language.
* Tenant identity cannot be trusted from request body parameters.
* Tenant isolation must be enforced server-side.
* Tenant checks must exist across application, database, vector, cache, model, tool, audit, and HITL layers.
* Cross-tenant leakage is a critical failure mode.

The central rule is:

> Tenant is resolved from trusted identity context and enforced by the platform. The model never chooses, modifies, or bypasses tenant context.

---

## 2. Tenant Definition

A tenant represents an isolated internal organizational boundary.

In this platform, a tenant may represent:

```txt id="30hnuw"
department
business unit
internal domain
risk area
compliance area
credit area
operations area
legal area
finance area
technology area
```

Example tenants:

```txt id="e7osua"
tenant_credit
tenant_compliance
tenant_legal
tenant_operations
tenant_risk
tenant_it
tenant_hr
```

A tenant owns or controls:

```txt id="qisv58"
documents
document chunks
embeddings
tools
prompts
policies
model permissions
usage budgets
audit records
HITL tasks
cache entries
sessions
requests
evaluation datasets
```

---

## 3. Tenant Security Principle

The system follows this tenant security principle:

> A request without a valid Tenant Context must not be able to call models, retrieve documents, execute tools, access cache, create HITL tasks, read audit records, or produce a final AI response.

This principle applies to:

```txt id="vnt4zn"
API routes
Agent Runtime
AI Gateway
RAG Orchestrator
Vector Access Gateway
Tool Executor
Policy Engine
Document Registry
Prompt Registry
Model Registry
Cache Layer
Audit Service
HITL Service
Evaluation Harness
```

---

## 4. Tenant Context

Tenant Context is the trusted runtime object that carries tenant and authorization metadata throughout the system.

It must be created once at request entry and propagated through every sensitive operation.

Conceptual structure:

```json id="9faksf"
{
  "tenant_id": "tenant_credit",
  "user_id": "user_123",
  "roles": ["analyst"],
  "scopes": ["rag:query", "tool:retrieve_documents"],
  "department": "credit",
  "clearance_level": "internal",
  "session_id": "session_abc",
  "request_id": "req_xyz",
  "trace_id": "trace_789",
  "environment": "production"
}
```

Required fields:

```txt id="sp3m7w"
tenant_id
user_id
roles
scopes
session_id
request_id
trace_id
environment
```

Optional fields:

```txt id="bqn03d"
department
clearance_level
business_unit
cost_center
region
auth_provider
identity_type
```

---

## 5. Tenant Resolution

Tenant resolution must happen at the backend boundary after authentication.

Allowed tenant sources:

```txt id="gj2fme"
validated JWT claims
trusted identity provider claims
server-side user directory lookup
trusted service-to-service identity
```

Disallowed tenant sources:

```txt id="qg9vv3"
request body
query string
HTTP header supplied by client without gateway validation
LLM output
tool call argument
retrieved document content
prompt text
natural language user request
cache key supplied by client
```

The system must not accept this as trusted:

```json id="zvjvpz"
{
  "tenant_id": "tenant_compliance"
}
```

unless the tenant value is validated against trusted identity and authorization context.

---

## 6. Tenant in JWT

A JWT may contain tenant-related claims, but the backend must validate the token before using them.

Example JWT claims:

```json id="pp3nuf"
{
  "sub": "user_123",
  "email": "analyst@example.com",
  "tenant_id": "tenant_credit",
  "roles": ["analyst"],
  "scopes": ["rag:query", "tool:retrieve_documents"],
  "department": "credit",
  "clearance_level": "internal",
  "iss": "https://identity.example.com",
  "aud": "sentinelgraph-ai",
  "exp": 1790000000,
  "iat": 1789990000
}
```

Required JWT validation:

```txt id="1plyje"
signature validation
issuer validation
audience validation
expiration validation
required claims validation
tenant status validation
user status validation
role and scope normalization
```

The tenant claim must be treated as trusted only after:

```txt id="yqd7hf"
JWT signature is valid
issuer is trusted
audience is expected
token is not expired
user is active
tenant is active
user is allowed to operate under that tenant
```

---

## 7. Tenant and User Relationship

A user may belong to one or more tenants depending on institutional design.

Supported models:

```txt id="61ci77"
single-tenant user
multi-tenant user with explicit active tenant
service account with scoped tenant access
platform admin with restricted cross-tenant governance access
```

### 7.1 Single-Tenant User

The simplest model.

```json id="ng3guj"
{
  "user_id": "user_123",
  "tenant_id": "tenant_credit",
  "roles": ["analyst"]
}
```

The user always operates under one tenant.

---

### 7.2 Multi-Tenant User

A user may have access to multiple tenants, but only one active tenant should be resolved per request.

Example:

```json id="iqygne"
{
  "user_id": "user_789",
  "allowed_tenants": ["tenant_credit", "tenant_risk"],
  "active_tenant": "tenant_credit"
}
```

Rules:

```txt id="u7qhmk"
active tenant must be explicitly selected through trusted UI/backend flow
active tenant must be validated server-side
tenant switching must be audited
request body cannot silently switch tenant
LLM cannot switch tenant
```

---

### 7.3 Platform Admin

A platform admin may manage platform-wide configuration, but this does not automatically grant access to tenant content.

Platform admin access should be separated into:

```txt id="oljxs2"
platform configuration access
tenant content access
audit access
model registry access
policy registry access
operations access
```

Cross-tenant content access must be explicit, audited, and policy-approved.

---

### 7.4 Service Account

Service accounts may operate on behalf of a tenant or platform service.

Required fields:

```txt id="yjqfov"
service_account_id
allowed_tenants
allowed_scopes
allowed_operations
expiration or rotation policy
owner
```

Service accounts must not have broad cross-tenant privileges unless strictly required and audited.

---

## 8. Tenant Lifecycle

A tenant may have the following lifecycle states:

```txt id="1mphp3"
draft
active
suspended
disabled
archived
deleted
```

### 8.1 draft

Tenant exists but cannot serve production AI requests.

Allowed:

```txt id="gsg51c"
configuration
document setup
admin preparation
```

Blocked:

```txt id="b9y9ks"
production AI requests
production retrieval
production tool execution
```

---

### 8.2 active

Tenant can use approved platform capabilities.

Allowed:

```txt id="prgbp0"
AI requests
RAG retrieval
tool execution
HITL
usage tracking
audit recording
```

---

### 8.3 suspended

Tenant is temporarily blocked from new AI execution.

Allowed:

```txt id="z0d329"
admin access
audit review
data export if authorized
configuration review
```

Blocked:

```txt id="0aovml"
new AI requests
new model calls
new tool execution
new document activation
```

---

### 8.4 disabled

Tenant is administratively disabled.

Allowed:

```txt id="49d4yp"
audit retention
governance review
controlled archival
```

Blocked:

```txt id="0ctu67"
all normal execution
```

---

### 8.5 archived

Tenant is no longer operational but records are retained.

Allowed:

```txt id="2e3all"
audit lookup by authorized governance users
retention-compliant archival
```

Blocked:

```txt id="23q732"
new requests
new ingestion
retrieval
tool execution
model calls
```

---

## 9. Tenant Data Ownership

Each tenant owns or controls its own data domain.

Tenant-owned resources include:

```txt id="h9xrlp"
documents
document versions
document chunks
embeddings
sessions
requests
HITL tasks
usage records
audit records
tenant-specific prompts
tenant-specific tools
tenant-specific policies
tenant-specific evaluation datasets
```

Every tenant-owned resource must include:

```txt id="f63dhg"
tenant_id
created_at
updated_at
status
owner or source metadata when applicable
```

For sensitive resources, also include:

```txt id="yvlba5"
classification
access policy
version
content_hash when applicable
```

---

## 10. Tenant Isolation Layers

Tenant isolation must be enforced in multiple layers.

```txt id="8qp6pu"
Identity Layer
API Layer
Application Service Layer
Policy Layer
Database Layer
Vector Layer
Cache Layer
AI Gateway Layer
Tool Execution Layer
Audit Layer
HITL Layer
Observability Layer
```

No single layer is sufficient by itself.

---

## 11. API Layer Tenant Rules

API routes that perform sensitive operations must require Tenant Context.

Examples of sensitive routes:

```txt id="ni59p7"
POST /v1/ai/requests
GET /v1/ai/requests/{request_id}
POST /v1/rag/search
POST /v1/documents
GET /v1/hitl/tasks
POST /v1/hitl/tasks/{task_id}/review
GET /v1/traces/{trace_id}
GET /v1/tenants/{tenant_id}/usage
```

Rules:

```txt id="5b5ghl"
request body tenant_id is not trusted
query string tenant_id is not trusted
route tenant_id must match TenantContext unless platform policy allows otherwise
missing TenantContext fails closed
tenant switch requires explicit trusted flow
```

Example safe check:

```txt id="lzga7f"
if route_tenant_id != tenant_context.tenant_id:
    require platform_admin_scope
    require explicit cross_tenant_policy
    audit cross_tenant_access_attempt
```

---

## 12. Application Service Layer Rules

All service methods that touch sensitive data must require `TenantContext`.

Example pattern:

```python id="5veuaa"
async def search_documents(
    tenant_context: TenantContext,
    query: str,
    filters: RetrievalFilters,
) -> RetrievalResult:
    ...
```

Avoid unsafe pattern:

```python id="hufbqz"
async def search_documents(
    tenant_id: str,
    query: str,
) -> RetrievalResult:
    ...
```

The unsafe pattern allows tenant ID to be passed from untrusted sources.

Preferred pattern:

```txt id="e079wq"
pass TenantContext object
never pass raw tenant_id alone for sensitive operations
derive tenant_id internally from TenantContext
```

---

## 13. Database Tenant Model

All tenant-owned tables must include `tenant_id`.

Examples:

```txt id="43e914"
documents
document_versions
document_chunks
requests
sessions
audit_events
hitl_tasks
usage_records
tool_permissions
model_permissions
prompt_permissions
policy_assignments
cache_metadata
evaluation_runs
```

Example relational schema:

```sql id="6zxmul"
CREATE TABLE documents (
    document_id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    title TEXT NOT NULL,
    source_system TEXT NOT NULL,
    classification TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

Recommended indexes:

```sql id="6ufzje"
CREATE INDEX idx_documents_tenant_status
ON documents (tenant_id, status);

CREATE INDEX idx_document_chunks_tenant_document
ON document_chunks (tenant_id, document_id);
```

---

## 14. Row-Level Security

PostgreSQL Row-Level Security may be used as defense in depth.

Example:

```sql id="91llno"
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_documents
ON documents
USING (tenant_id = current_setting('app.current_tenant_id'));
```

RLS is not a replacement for application-level tenant checks.

RLS should be treated as an additional protection layer.

Required rule:

```txt id="l0rr97"
application tenant enforcement remains mandatory even when RLS is enabled
```

---

## 15. Vector Database Tenant Model

Vector entries must include tenant metadata.

Each vector chunk must include:

```json id="83bps8"
{
  "tenant_id": "tenant_credit",
  "document_id": "doc_123",
  "document_version": "v4",
  "chunk_id": "chunk_456",
  "classification": "internal",
  "status": "active",
  "allowed_roles": ["analyst", "reviewer"],
  "embedding_model_version": "embedding_v3",
  "chunking_strategy_version": "chunker_v2"
}
```

Mandatory metadata:

```txt id="mv2ykj"
tenant_id
document_id
document_version
chunk_id
classification
status
embedding_model_version
```

Recommended metadata:

```txt id="fnbpng"
allowed_roles
allowed_scopes
department
source_system
effective_date
expiration_date
content_hash
```

---

## 16. Vector Access Gateway Tenant Rules

All vector search must pass through the Vector Access Gateway.

The gateway must inject server-side filters:

```txt id="xk8x38"
tenant_id
document status
classification limit
document version policy
role/scope constraints
user clearance constraints
```

Example mandatory filter:

```json id="j9nhqu"
{
  "tenant_id": "tenant_credit",
  "status": "active",
  "classification": {
    "lte": "internal"
  },
  "allowed_roles": {
    "contains_any": ["analyst"]
  }
}
```

Rules:

```txt id="xmly91"
LLM cannot provide tenant filter
user cannot provide tenant filter
client filters can narrow results but cannot widen access
gateway must validate returned chunks
cross-tenant result must be discarded and audited
```

Unsafe:

```json id="u3eaay"
{
  "filters": {
    "tenant_id": "tenant_compliance"
  }
}
```

Safe behavior:

```txt id="7r50m5"
ignore client tenant filter
or reject request as suspicious
audit if tenant override attempt is detected
```

---

## 17. Cache Tenant Model

All cache entries that may depend on tenant, permissions, documents, policies, prompts, or models must use tenant-aware keys.

Required cache key components:

```txt id="zl5e7t"
tenant_id
user_scope_hash
query_hash or input_hash
prompt_version
model_version
policy_version
document_version or document_index_version
classification_level
```

Example cache key:

```txt id="li00fq"
rag:tenant_credit:scope_abc:query_123:prompt_v3:model_gpt4:policy_v2:index_v5
```

Unsafe cache key:

```txt id="lh0kmh"
rag:query_123
```

Rules:

```txt id="i4xrlf"
no global cache for sensitive responses
cache must be invalidated on document revocation
cache must be invalidated on policy change
cache must be invalidated on prompt/model version change where relevant
cache read must require TenantContext
cache write must require TenantContext
```

---

## 18. AI Gateway Tenant Model

The AI Gateway must enforce model access by tenant.

Each tenant may have:

```txt id="p6cvz3"
allowed LLMs
allowed embedding models
allowed local models
allowed external API providers
data class restrictions
token budgets
cost budgets
fallback chains
max context size
max output tokens
concurrency limits
```

Example tenant model policy:

```json id="rdt2dd"
{
  "tenant_id": "tenant_credit",
  "allowed_models": ["azure-gpt-4.1", "azure-gpt-4.1-mini", "local-llama"],
  "allowed_embedding_models": ["azure-embedding-v3", "local-bge"],
  "allowed_data_classes": ["public", "internal"],
  "daily_token_budget": 1000000,
  "monthly_cost_budget": 5000.00,
  "max_concurrent_requests": 20,
  "fallback_chain": ["azure-gpt-4.1-mini", "local-llama"]
}
```

Rules:

```txt id="5o4g6g"
tenant must be authorized for model
data class must be authorized for model
fallback must be tenant-approved
fallback must not downgrade security
usage must be recorded per tenant
budget must be enforced per tenant
```

---

## 19. Tool Tenant Model

Tools may be global, tenant-scoped, or tenant-specific.

### 19.1 Global Tool

A global tool is available to multiple tenants but still requires tenant and scope authorization.

Example:

```txt id="1j7p9z"
retrieve_documents
summarize_document
compare_documents
request_human_review
```

### 19.2 Tenant-Scoped Tool

A tenant-scoped tool is available only to specific tenants.

Example:

```json id="i0j3cq"
{
  "tool_name": "credit_policy_lookup",
  "allowed_tenants": ["tenant_credit"],
  "required_scopes": ["tool:credit_policy_lookup"]
}
```

### 19.3 Tenant-Specific Tool

A tenant-specific tool is implemented for a single tenant or business domain.

Example:

```txt id="uyt9xg"
credit_risk_rule_lookup
compliance_obligation_extract
legal_contract_clause_lookup
```

Rules:

```txt id="48g78u"
LLM can only propose tool call
Tool Executor validates tenant access
Tool Executor validates user scope
Tool Executor validates policy
Tool Executor enforces HITL if required
Tool result is tenant-scoped
Tool audit includes tenant_id
```

Tool arguments must not be allowed to override tenant.

Unsafe:

```json id="043758"
{
  "tool_name": "retrieve_documents",
  "arguments": {
    "tenant_id": "tenant_compliance",
    "query": "compliance policy"
  }
}
```

Safe behavior:

```txt id="4w7r07"
reject or ignore tenant_id in tool arguments
derive tenant from TenantContext
audit suspicious argument
```

---

## 20. Prompt Tenant Model

Prompts may be:

```txt id="zw2b3s"
global
tenant-scoped
use-case-scoped
risk-scoped
environment-scoped
```

Example prompt metadata:

```json id="peeq5c"
{
  "prompt_id": "rag_answer_prompt",
  "version": "v3",
  "scope": "tenant",
  "allowed_tenants": ["tenant_credit", "tenant_compliance"],
  "status": "production",
  "risk_class": "medium"
}
```

Rules:

```txt id="239ryo"
promotion to status `production` requires recorded approval metadata
tenant must be allowed to use prompt
prompt version must be recorded in audit
revoked prompt cannot be used
tenant-specific prompt cannot be used by another tenant
```

Prompts must not contain tenant secrets or tenant-specific sensitive data unless explicitly approved.

---

## 21. Document Tenant Model

Documents must belong to exactly one tenant unless explicitly marked as shared.

Default rule:

```txt id="rgtbaw"
document belongs to one tenant
```

Required fields:

```txt id="kigys7"
document_id
tenant_id
document_version
classification
status
owner
source_system
content_hash
```

Shared documents require explicit policy.

Example shared document:

```json id="yg5q1r"
{
  "document_id": "doc_shared_001",
  "tenant_id": "platform",
  "shared_with_tenants": ["tenant_credit", "tenant_compliance"],
  "classification": "internal",
  "status": "active"
}
```

Shared document rules:

```txt id="doqk28"
sharing must be explicit
sharing must be policy-approved
sharing must be audited
shared document must still obey classification and role rules
citations must indicate shared source
```

Avoid implicit sharing.

---

## 22. HITL Tenant Model

HITL tasks are tenant-scoped.

A HITL task must include:

```txt id="s8cvqs"
task_id
tenant_id
request_id
trace_id
risk_level
reviewer_scope
status
created_at
```

Rules:

```txt id="z12sdg"
reviewer must belong to same tenant or have explicit cross-tenant review scope
reviewer access must be policy-checked
HITL decision must be audited
HITL task cannot be approved by unauthorized tenant user
final answer cannot be released before approval when required
```

Unsafe:

```txt id="2owsnj"
platform admin approves tenant task without explicit content-review permission
```

Safe:

```txt id="qutg47"
platform admin needs explicit tenant review scope or governance exception
decision is audited
```

---

## 23. Audit Tenant Model

Audit records must always include tenant information when applicable.

Required fields:

```txt id="1wnjth"
audit_id
tenant_id
user_id
request_id
trace_id
event_type
resource_type
resource_id
timestamp
policy_version
payload
```

Rules:

```txt id="qkp2wu"
tenant users can only access their tenant audit records
platform governance access must be explicit
audit access must be audited
audit records should be append-only
audit payload must be sanitized
cross-tenant audit query requires special permission
```

Audit records for failed tenant resolution should include as much safe context as possible, but must not invent tenant identity.

---

## 24. Observability Tenant Model

Logs, metrics, and traces must include tenant metadata when safe.

Required trace attributes:

```txt id="88bnp9"
tenant_id
user_id or pseudonymized user_id
request_id
trace_id
risk_level
runtime_mode
model_id
prompt_version
policy_version
```

Metrics should support tenant-level aggregation:

```txt id="m9xw24"
requests_by_tenant
tokens_by_tenant
cost_by_tenant
latency_by_tenant
fallback_by_tenant
policy_denials_by_tenant
hitl_by_tenant
prompt_injection_attempts_by_tenant
```

Rules:

```txt id="4311if"
standard logs must be sanitized
PII must not appear in normal logs
tenant_id may be pseudonymized in shared dashboards
tenant content must not appear in metrics labels
high-cardinality labels must be controlled
```

---

## 25. Evaluation Tenant Model

Evaluation datasets may be:

```txt id="vkjbb5"
global synthetic datasets
tenant-specific golden datasets
security datasets
cross-tenant attack datasets
PII leakage datasets
prompt injection datasets
```

Rules:

```txt id="mvsepf"
tenant-specific eval data must be tenant-scoped
eval runs must record tenant context or synthetic tenant
cross-tenant leakage tests must be mandatory
eval outputs must not leak tenant data
production evals must use approved datasets
```

Example evaluation test:

```txt id="4zv28o"
Given:
  tenant_credit document
  tenant_compliance document

When:
  tenant_credit user asks for compliance document

Then:
  system must not retrieve tenant_compliance chunk
  system must not cite tenant_compliance document
  audit event must record blocked or unauthorized attempt
```

---

## 26. Tenant Usage and Budget Model

Each tenant must have independent usage controls.

Budget dimensions:

```txt id="e9t5fn"
requests per minute
tokens per minute
daily input tokens
daily output tokens
monthly token budget
monthly cost budget
max concurrent requests
max agent steps
max tool calls
max retrieval calls
allowed models
allowed embedding models
```

Example:

```json id="av8qvk"
{
  "tenant_id": "tenant_credit",
  "requests_per_minute": 120,
  "tokens_per_minute": 200000,
  "daily_token_budget": 1000000,
  "monthly_cost_budget": 5000.00,
  "max_concurrent_requests": 20,
  "max_agent_steps": 12,
  "max_tool_calls": 5,
  "max_retrieval_calls": 3
}
```

Rules:

```txt id="td65lb"
budget usage must be recorded per tenant
budget exhaustion must fail safely
fallback to cheaper model must respect tenant policy
tenant usage must be queryable
cost dashboard must aggregate by tenant
```

---

## 27. Tenant-Aware Agent Runtime

The Agent Runtime must carry Tenant Context through the full graph execution.

Agent state must include:

```txt id="4uc0xv"
tenant_id
user_id
session_id
request_id
trace_id
roles
scopes
risk_level
budget state
policy version
```

Rules:

```txt id="89ggcf"
agent cannot change tenant_id
LLM cannot change tenant_id
tool calls cannot change tenant_id
retrieved documents cannot change tenant_id
all graph nodes must receive TenantContext
invalid or missing tenant state fails closed
```

The runtime must validate tenant consistency between:

```txt id="bfu18g"
AgentState
TenantContext
retrieved documents
tool results
audit records
HITL tasks
final citations
```

If mismatch occurs:

```txt id="xn6o45"
block response
audit security event
fail closed
```

---

## 28. Tenant-Aware Grounding

Final answers must only be grounded in documents authorized for the active tenant.

Citation objects must include:

```txt id="795b3x"
document_id
document_version
chunk_id
tenant_id or tenant-safe source reference
classification
source title
confidence
```

Rules:

```txt id="kd35zc"
citation tenant must match active tenant or approved shared source
citation document must be active
citation document must be authorized
citation document version must be valid
cross-tenant citation fails validation
```

If grounding references unauthorized tenant content:

```txt id="g3djd4"
block final response
audit grounding violation
trigger security alert if necessary
```

---

## 29. Shared Resources

Some resources may be shared across tenants.

Examples:

```txt id="m6zs80"
global prompts
global tools
global policy templates
shared compliance documents
shared model deployments
shared evaluation suites
```

Shared resources must be explicit.

Shared resource metadata should include:

```json id="p2shz5"
{
  "resource_id": "resource_123",
  "scope": "shared",
  "owner_tenant": "platform",
  "shared_with_tenants": ["tenant_credit", "tenant_compliance"],
  "classification": "internal",
  "status": "active",
  "approved_by": "governance_team"
}
```

Rules:

```txt id="fi0dew"
no implicit sharing
sharing requires approval
sharing must be auditable
shared resources still obey classification
shared documents require explicit citation rules
shared tools still require tenant-specific authorization
```

---

## 30. Cross-Tenant Access

Cross-tenant access is denied by default.

Allowed only when:

```txt id="6vu1nl"
user has explicit cross-tenant scope
policy allows the action
resource is explicitly shared
access is audited
risk level is acceptable
HITL is triggered when required
```

Examples of possible legitimate cross-tenant access:

```txt id="ffg0f7"
governance officer reviews audit summary
platform admin manages model registry
compliance reviewer accesses shared compliance document
central risk team reviews approved cross-tenant report
```

Cross-tenant access must not be available through normal AI prompt requests unless explicitly designed and approved.

---

## 31. Tenant Isolation Test Requirements

The following tests are mandatory.

### 31.1 API Tests

```txt id="gpdl3r"
request without TenantContext fails
request with tenant mismatch fails
route tenant_id mismatch fails unless explicitly authorized
```

### 31.2 Database Tests

```txt id="hc9fc8"
tenant A cannot query tenant B documents through repositories
tenant A cannot access tenant B sessions
tenant A cannot access tenant B HITL tasks
```

### 31.3 Vector Tests

```txt id="bjjcd1"
tenant A cannot retrieve tenant B chunks
client-supplied tenant filter cannot widen access
LLM-supplied tenant filter cannot widen access
cross-tenant vector result is discarded and audited
```

### 31.4 Cache Tests

```txt id="9vq6oo"
cache key includes tenant_id
tenant B cannot hit tenant A cache entry
policy version change invalidates relevant cache
document revocation invalidates retrieval cache
```

### 31.5 Tool Tests

```txt id="u4hro3"
tenant A cannot execute tenant B tool
tool argument tenant_id is ignored or rejected
tool result tenant mismatch is blocked
```

### 31.6 HITL Tests

```txt id="5jyp8p"
tenant A reviewer cannot approve tenant B HITL task
platform admin cannot approve content without explicit scope
HITL decision includes tenant_id
```

### 31.7 Audit Tests

```txt id="q0w5ck"
tenant A cannot read tenant B audit records
audit event includes tenant_id
cross-tenant access attempt is audited
```

### 31.8 Grounding Tests

```txt id="aoyeeq"
answer cannot cite another tenant document
shared document citation requires explicit shared policy
unauthorized citation blocks final response
```

---

## 32. Tenant Error Handling

Tenant-related errors must be safe and non-revealing.

Example unsafe response:

```txt id="i2tsm4"
You cannot access tenant_compliance because you are tenant_credit.
```

Better response:

```txt id="38q4pm"
This request cannot be completed with the current access context.
```

Standard error codes:

```txt id="v3thyk"
TENANT_CONTEXT_MISSING
TENANT_ACCESS_DENIED
TENANT_MISMATCH
TENANT_INACTIVE
CROSS_TENANT_ACCESS_DENIED
TENANT_BUDGET_EXCEEDED
TENANT_MODEL_NOT_ALLOWED
TENANT_TOOL_NOT_ALLOWED
TENANT_DOCUMENT_ACCESS_DENIED
```

Detailed reason should be stored in audit, not necessarily exposed to user.

---

## 33. Tenant Model Database Tables

Suggested baseline tables:

```txt id="h5efyp"
tenants
tenant_memberships
tenant_roles
tenant_scopes
tenant_model_permissions
tenant_tool_permissions
tenant_prompt_permissions
tenant_policy_assignments
tenant_usage_budgets
tenant_usage_records
tenant_shared_resources
```

### 33.1 tenants

```sql id="7o5wmb"
CREATE TABLE tenants (
    tenant_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### 33.2 tenant_memberships

```sql id="4g61k7"
CREATE TABLE tenant_memberships (
    tenant_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    roles JSONB NOT NULL,
    scopes JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (tenant_id, user_id)
);
```

### 33.3 tenant_model_permissions

```sql id="0uly2a"
CREATE TABLE tenant_model_permissions (
    tenant_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    allowed_data_classes JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (tenant_id, model_id)
);
```

### 33.4 tenant_tool_permissions

```sql id="jq4rny"
CREATE TABLE tenant_tool_permissions (
    tenant_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    required_scopes JSONB NOT NULL,
    requires_hitl BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (tenant_id, tool_id)
);
```

### 33.5 tenant_usage_budgets

```sql id="fjq6x6"
CREATE TABLE tenant_usage_budgets (
    tenant_id TEXT PRIMARY KEY,
    requests_per_minute INTEGER NOT NULL,
    tokens_per_minute INTEGER NOT NULL,
    daily_token_budget INTEGER NOT NULL,
    monthly_token_budget INTEGER NOT NULL,
    monthly_cost_budget NUMERIC(12, 2) NOT NULL,
    max_concurrent_requests INTEGER NOT NULL,
    max_agent_steps INTEGER NOT NULL,
    max_tool_calls INTEGER NOT NULL,
    max_retrieval_calls INTEGER NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

---

## 34. Tenant Model Invariants

The following invariants must always hold:

```txt id="knxs9m"
1. Every sensitive operation has a TenantContext.
2. TenantContext is derived from trusted authentication context.
3. LLM output cannot change tenant_id.
4. User prompt cannot change tenant_id.
5. Tool arguments cannot change tenant_id.
6. Retrieved documents cannot change tenant_id.
7. Cache entries are tenant-aware.
8. Audit records are tenant-aware.
9. HITL tasks are tenant-aware.
10. Vector search is tenant-filtered server-side.
11. Final citations cannot reference unauthorized tenant documents.
12. Model access is tenant-authorized.
13. Tool access is tenant-authorized.
14. Budget enforcement is tenant-scoped.
15. Cross-tenant access is denied by default.
```

Any violation must result in:

```txt id="z96cvx"
safe failure
audit event
security alert when appropriate
```

---

## 35. MVP Tenant Model

The MVP should implement:

```txt id="aj9qv6"
single active tenant per request
TenantContext middleware
tenant_id on all sensitive tables
tenant-aware document ingestion
tenant-aware vector chunks
Vector Access Gateway
tenant-aware cache keys
tenant-aware audit records
tenant model permissions
tenant tool permissions
tenant token budgets
tenant-scoped HITL tasks
cross-tenant leakage tests
```

The MVP may defer:

```txt id="novozc"
complex tenant hierarchy
multi-region tenant routing
tenant self-service admin UI
advanced cross-tenant governance workflows
fine-grained field-level access control
tenant-specific encryption keys
advanced anomaly detection
```

---

## 36. Future Tenant Model Enhancements

Future enhancements may include:

```txt id="3msilj"
tenant hierarchy
subtenants
tenant groups
field-level permissions
tenant-specific encryption keys
per-tenant model routing policies
tenant-specific prompt libraries
tenant-specific evaluation suites
tenant anomaly detection
automated access reviews
tenant data residency controls
tenant-level disaster recovery policies
cross-tenant governance approval workflows
```

---

## 37. Summary

The tenant model is one of the most important security foundations of the platform.

The platform must enforce tenant isolation across:

```txt id="ytfsha"
identity
API
application services
database
vector search
cache
AI Gateway
tools
prompts
documents
HITL
audit
observability
evaluation
```

The most important tenant invariant is:

> Tenant is never controlled by the model, the prompt, the document, the tool arguments, or the client body. Tenant is resolved from trusted identity context and enforced server-side across every sensitive operation.

This model protects the platform against:

```txt id="gmprlb"
cross-tenant data leakage
unauthorized retrieval
cache leakage
tool misuse
model misuse
HITL abuse
audit leakage
grounding violations
```

Every implementation decision must preserve strict tenant isolation by default.

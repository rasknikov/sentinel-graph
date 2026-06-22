# DATA_FLOW

## 1. Overview

This document defines the main data flows for the governed multi-tenant agentic RAG platform.

The platform is designed for internal use in a financial institution and supports:

* Multi-tenant AI requests
* Secure RAG
* Agentic workflows
* Structured tool calling
* AI Gateway
* Vector Access Gateway
* PII masking
* Prompt injection defense
* HITL
* Audit
* Observability
* LLMOps and MLOps governance

The purpose of this document is to make explicit how data moves through the system, where security boundaries exist, and where tenant, policy, audit, and validation controls must be applied.

The core invariant is:

> User data, tenant data, retrieved documents, tool outputs, and model outputs must only move through governed runtime boundaries.

---

## 2. High-Level Platform Flow

```txt id="iui9lk"
Internal User
    |
    v
Internal Portal / Client
    |
    v
API Gateway / Backend API
    |
    v
Authentication + Tenant Context
    |
    v
Policy Engine
    |
    v
Agent Runtime / Strict Graph
    |
    +----------------------------+
    |                            |
    v                            v
AI Gateway                 Tool Executor
    |                            |
    v                            v
LLM / Embedding Models      Controlled Tools
    |
    v
RAG Orchestrator
    |
    v
Vector Access Gateway
    |
    v
Vector DB / Document Store
    |
    v
Grounding + Output Validation
    |
    v
HITL if required
    |
    v
Final Response
    |
    v
Audit + Observability
```

---

## 3. Data Flow Principles

All data flows must obey the following principles:

```txt id="7pwdqm"
1. Tenant Context is required for every sensitive operation.
2. Tenant identity is resolved from trusted authentication context.
3. Tenant identity is never inferred by the LLM.
4. User input is untrusted.
5. Retrieved documents are untrusted context.
6. Tool outputs are untrusted observations.
7. The LLM may reason, but it must not execute actions directly.
8. All model calls go through AI Gateway.
9. All vector searches go through Vector Access Gateway.
10. All tool executions go through Tool Executor.
11. All high-risk actions may trigger HITL.
12. All critical actions are audited.
13. All standard logs must be sanitized.
14. Unsafe or unauthorized flows fail closed.
```

---

# 4. Flow 1 — Standard AI Request

## 4.1 Purpose

This flow describes a normal user request that enters the platform and is processed by the Agent Runtime.

## 4.2 Flow Diagram

```txt id="w9xgqd"
User
  |
  v
Internal Portal
  |
  v
POST /v1/ai/requests
  |
  v
API Middleware
  |
  v
JWT Validation
  |
  v
Tenant Context Creation
  |
  v
Request + Trace IDs
  |
  v
Input Validation
  |
  v
PII Preprocessing
  |
  v
Prompt Injection Scan
  |
  v
Policy Check
  |
  v
Agent Runtime
  |
  v
Graph Execution
  |
  v
Output Validation
  |
  v
Final Response
  |
  v
Audit + Metrics + Traces
```

## 4.3 Data Entering the Flow

```json id="pqhras"
{
  "session_id": "session_abc",
  "message": "What is the current policy for small business credit approval?",
  "mode": "rag_agent",
  "metadata": {
    "client": "internal-portal"
  }
}
```

## 4.4 Data Created by the Platform

```json id="qqtks5"
{
  "tenant_context": {
    "tenant_id": "tenant_credit",
    "user_id": "user_123",
    "roles": ["analyst"],
    "scopes": ["rag:query"],
    "session_id": "session_abc",
    "request_id": "req_xyz",
    "trace_id": "trace_789",
    "environment": "production"
  }
}
```

## 4.5 Required Controls

```txt id="w6e3sc"
JWT must be valid.
Tenant must be active.
User must be active.
Tenant Context must be created server-side.
Request must receive request_id and trace_id.
Input must be validated.
Prompt injection scan must run.
PII preprocessing must run when policy requires.
Audit event must be created.
```

## 4.6 Failure Conditions

```txt id="df6a85"
invalid JWT
missing Tenant Context
inactive tenant
inactive user
oversized request
prompt injection detected in high-risk context
PII policy violation
policy denial
```

## 4.7 Safe Failure Behavior

```txt id="e6fjzz"
Return safe error.
Do not call model.
Do not retrieve documents.
Do not execute tools.
Audit denial when possible.
Emit security metric when applicable.
```

---

# 5. Flow 2 — Tenant Context Resolution

## 5.1 Purpose

This flow describes how tenant identity is resolved and propagated.

## 5.2 Flow Diagram

```txt id="1u6b72"
Incoming Request
    |
    v
Extract Authorization Token
    |
    v
Validate JWT
    |
    v
Validate issuer, audience, exp, signature
    |
    v
Load User and Tenant Metadata
    |
    v
Validate User Status
    |
    v
Validate Tenant Status
    |
    v
Normalize Roles and Scopes
    |
    v
Create TenantContext
    |
    v
Attach to Request State
    |
    v
Propagate to Services
```

## 5.3 Trusted Sources

Tenant information may come from:

```txt id="7gb5j6"
validated JWT claims
trusted identity provider
server-side user directory
trusted service account metadata
```

## 5.4 Untrusted Sources

Tenant information must not be trusted from:

```txt id="gplq5y"
request body
query string
client-provided header
LLM output
tool arguments
retrieved documents
prompt text
natural language request
```

## 5.5 Tenant Context Propagation

Tenant Context must be passed into:

```txt id="gx3bst"
Policy Engine
AI Gateway
RAG Orchestrator
Vector Access Gateway
Tool Executor
Audit Service
HITL Service
Cache Layer
Document Registry
Prompt Registry
Model Registry
Evaluation Harness
```

## 5.6 Required Invariant

```txt id="j4i83e"
No sensitive service method should accept raw tenant_id as a trusted input when TenantContext is available.
```

Preferred:

```python id="xhay8i"
async def retrieve_documents(
    tenant_context: TenantContext,
    query: str,
    filters: RetrievalFilters,
) -> RetrievalResult:
    ...
```

Avoid:

```python id="ggs11x"
async def retrieve_documents(
    tenant_id: str,
    query: str,
) -> RetrievalResult:
    ...
```

---

# 6. Flow 3 — Secure RAG Flow

## 6.1 Purpose

This flow describes how the system retrieves documents and generates grounded answers.

## 6.2 Flow Diagram

```txt id="u6r04p"
User Question
    |
    v
Tenant Context
    |
    v
PII Masking
    |
    v
Prompt Injection Scan
    |
    v
RAG Orchestrator
    |
    v
Query Preprocessing
    |
    v
Embedding Request
    |
    v
AI Gateway
    |
    v
Embedding Model
    |
    v
Query Embedding
    |
    v
Vector Access Gateway
    |
    v
Server-Side Tenant + ACL Filters
    |
    v
Vector DB Search
    |
    v
Authorized Chunks Only
    |
    v
Context Assembly
    |
    v
Grounded Generation via AI Gateway
    |
    v
Citation Builder
    |
    v
Grounding Validator
    |
    v
Output Validator
    |
    v
Final Answer
    |
    v
Audit + Traces + Metrics
```

## 6.3 Retrieval Request

```json id="xp7jhk"
{
  "query": "credit approval requirements",
  "top_k": 8,
  "filters": {
    "document_type": "policy"
  }
}
```

The client may provide filters that narrow results, but cannot provide security-critical filters.

## 6.4 Server-Side Mandatory Filters

The Vector Access Gateway must inject:

```json id="0rr21d"
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

## 6.5 Data Returned by Retrieval

```json id="8b764p"
{
  "results": [
    {
      "tenant_id": "tenant_credit",
      "document_id": "doc_123",
      "document_version": "v4",
      "chunk_id": "chunk_88",
      "content": "Eligibility criteria...",
      "score": 0.86,
      "metadata": {
        "section": "Eligibility",
        "page": 5
      }
    }
  ]
}
```

## 6.6 Final Grounded Response

```json id="n2ro1y"
{
  "answer": "According to the active credit policy, ...",
  "citations": [
    {
      "document_id": "doc_123",
      "document_version": "v4",
      "chunk_id": "chunk_88",
      "source": "Internal Credit Policy",
      "confidence": 0.86
    }
  ],
  "requires_human_review": false,
  "trace_id": "trace_789"
}
```

## 6.7 Required Controls

```txt id="9eu1wq"
All embeddings go through AI Gateway.
All vector search goes through Vector Access Gateway.
Tenant filter is injected server-side.
Client tenant filters are ignored or rejected.
LLM tenant filters are ignored or rejected.
Retrieved chunks must be authorized.
Retrieved chunks must be active.
Retrieved chunks must match TenantContext or approved shared resource policy.
Final citations must reference authorized chunks.
Grounding validation must run before final response.
```

## 6.8 Failure Conditions

```txt id="tgf5tq"
no authorized documents found
cross-tenant result detected
expired document retrieved
grounding failure
citation mismatch
PII output violation
model unavailable with no safe fallback
```

## 6.9 Safe Failure Behavior

```txt id="44g4q8"
Return no-authorized-source response.
Do not fabricate answer.
Do not cite unauthorized document.
Escalate to HITL if policy requires.
Audit retrieval failure or violation.
```

---

# 7. Flow 4 — Document Ingestion Flow

## 7.1 Purpose

This flow describes how documents enter the system and become retrievable.

## 7.2 Flow Diagram

```txt id="ac6yt9"
Authorized User / System
    |
    v
POST /v1/documents
    |
    v
Tenant Context Validation
    |
    v
Document Metadata Validation
    |
    v
Document Registry Entry
    |
    v
Content Hashing
    |
    v
Store Original Document
    |
    v
Parse Document
    |
    v
Chunk Document
    |
    v
Create Chunk Metadata
    |
    v
Generate Embeddings via AI Gateway
    |
    v
Store Chunks + Embeddings
    |
    v
Mark Ingestion Indexed
    |
    v
Approval / Activation
    |
    v
Document Becomes Retrievable
    |
    v
Audit + Metrics
```

## 7.3 Document Input

```json id="y9l2o9"
{
  "title": "Internal Credit Policy",
  "source_system": "policy-repository",
  "version": "v4",
  "classification": "internal",
  "status": "draft",
  "content": "Document content..."
}
```

## 7.4 Document Registry Record

```json id="94r26x"
{
  "document_id": "doc_123",
  "tenant_id": "tenant_credit",
  "title": "Internal Credit Policy",
  "source_system": "policy-repository",
  "version": "v4",
  "content_hash": "sha256...",
  "classification": "internal",
  "status": "draft",
  "owner": "credit-governance",
  "effective_date": "2026-01-01",
  "expiration_date": "2026-12-31"
}
```

## 7.5 Chunk Metadata

```json id="ixq9dh"
{
  "chunk_id": "chunk_456",
  "document_id": "doc_123",
  "tenant_id": "tenant_credit",
  "document_version": "v4",
  "chunk_index": 12,
  "content_hash": "sha256...",
  "embedding_model_version": "embedding_v3",
  "chunking_strategy_version": "chunker_v2",
  "classification": "internal",
  "status": "indexed"
}
```

## 7.6 Required Controls

```txt id="e981av"
Document ingestion requires TenantContext.
Document must include classification.
Document must include version.
Document must receive content hash.
Chunks must include tenant_id.
Chunks must include document version.
Embeddings must be generated through AI Gateway.
Document must not be retrievable until active.
Ingestion must be audited.
```

## 7.7 Failure Conditions

```txt id="dkxwls"
missing TenantContext
invalid document metadata
unsupported file type
parsing failure
embedding failure
document hash mismatch
activation by unauthorized user
tenant mismatch
```

## 7.8 Safe Failure Behavior

```txt id="axr7xj"
Mark ingestion job as failed.
Do not activate document.
Do not index incomplete chunks as retrievable.
Audit failure.
Return safe error.
```

---

# 8. Flow 5 — Structured Tool Calling Flow

## 8.1 Purpose

This flow describes how the LLM proposes a tool call and how the platform validates and executes it.

## 8.2 Flow Diagram

```txt id="gjb2ns"
Agent Runtime
    |
    v
LLM Call via AI Gateway
    |
    v
LLM Proposes Tool Call as JSON
    |
    v
Tool Proposal Parser
    |
    v
JSON Schema Validation
    |
    v
Tool Registry Lookup
    |
    v
Tenant Authorization
    |
    v
User Scope Authorization
    |
    v
Policy Check
    |
    v
HITL Check if Required
    |
    v
Tool Executor
    |
    v
Tool Result
    |
    v
Tool Result Validation
    |
    v
Observation Added to Agent State
    |
    v
Agent Continues or Finalizes
    |
    v
Audit + Traces + Metrics
```

## 8.3 Tool Proposal

```json id="ntvlmj"
{
  "type": "tool_call",
  "tool_name": "retrieve_documents",
  "tool_version": "v1",
  "arguments": {
    "query": "credit policy eligibility",
    "top_k": 8
  },
  "reason": "The user request requires internal policy retrieval.",
  "risk_level": "medium"
}
```

## 8.4 Tool Metadata

```json id="acv5z9"
{
  "tool_name": "retrieve_documents",
  "tool_version": "v1",
  "allowed_tenants": ["tenant_credit"],
  "required_scopes": ["rag:query"],
  "risk_level": "medium",
  "requires_hitl": false,
  "timeout_ms": 5000,
  "idempotent": true,
  "status": "active"
}
```

## 8.5 Tool Result

```json id="jmh98h"
{
  "tool_name": "retrieve_documents",
  "tool_version": "v1",
  "status": "success",
  "result": {
    "documents": []
  },
  "execution_time_ms": 820,
  "trace_id": "trace_789"
}
```

## 8.6 Required Controls

```txt id="dawhby"
LLM only proposes tool calls.
Tool call must be valid JSON.
Tool call must match schema.
Tool must exist in registry.
Tool must be active.
Tenant must be allowed to use tool.
User must have required scope.
Policy must allow execution.
High-risk tool must trigger HITL.
Tool execution must be audited.
Tool output must be validated.
```

## 8.7 Forbidden Flow

```txt id="1woazj"
LLM
  |
  v
Direct Tool Execution
```

This must never be allowed.

## 8.8 Failure Conditions

```txt id="932drl"
invalid JSON
unknown tool
inactive tool
invalid arguments
tenant not allowed
missing scope
policy denial
HITL required but not approved
tool timeout
malformed tool output
```

## 8.9 Safe Failure Behavior

```txt id="77pmz8"
Reject tool call.
Do not execute tool.
Add safe error observation to Agent State if appropriate.
Audit denial.
Continue safely or stop runtime according to policy.
```

---

# 9. Flow 6 — Strict Agent Runtime Flow

## 9.1 Purpose

This flow describes how agentic execution happens through a strict graph.

## 9.2 Flow Diagram

```txt id="xoe1rj"
START
  |
  v
LOAD_CONTEXT
  |
  v
AUTHORIZATION_CHECK
  |
  v
PII_PREPROCESSING
  |
  v
INTENT_CLASSIFICATION
  |
  v
RISK_CLASSIFICATION
  |
  v
PLANNING
  |
  v
POLICY_CHECK
  |
  v
RETRIEVAL
  |
  v
TOOL_CALL_PROPOSAL
  |
  v
TOOL_SCHEMA_VALIDATION
  |
  v
TOOL_AUTHORIZATION
  |
  v
TOOL_EXECUTION
  |
  v
OBSERVATION
  |
  v
NEED_MORE_STEPS?
  |         |
  | yes     | no
  v         v
PLANNING   GROUNDING
            |
            v
OUTPUT_VALIDATION
            |
            v
HITL_CHECK
            |
            v
FINAL_RESPONSE
            |
            v
AUDIT_LOG
            |
            v
END
```

## 9.3 Agent State

```json id="k5ja7t"
{
  "tenant_id": "tenant_credit",
  "user_id": "user_123",
  "session_id": "session_abc",
  "request_id": "req_xyz",
  "trace_id": "trace_789",
  "roles": ["analyst"],
  "scopes": ["rag:query"],
  "messages": [],
  "intent": "policy_question",
  "risk_level": "medium",
  "retrieved_documents": [],
  "tool_calls": [],
  "observations": [],
  "step_count": 0,
  "token_budget_remaining": 12000,
  "cost_budget_remaining": 0.50,
  "policy_version": "policy_v2",
  "requires_hitl": false,
  "final_answer": null,
  "status": "running"
}
```

## 9.4 Runtime Limits

```json id="wm29x9"
{
  "max_steps": 12,
  "max_tool_calls": 5,
  "max_retrieval_calls": 3,
  "max_execution_seconds": 30,
  "max_input_tokens": 16000,
  "max_output_tokens": 4000,
  "max_cost_per_request": 0.50
}
```

## 9.5 Required Controls

```txt id="jej398"
AgentState must include tenant_id.
AgentState tenant_id must match TenantContext.
LLM cannot modify tenant_id.
Tool calls cannot modify tenant_id.
Retrieved documents cannot modify tenant_id.
Every graph node emits trace events.
Every critical transition can be audited.
Loop is bounded.
Invalid transition fails safely.
```

## 9.6 Failure Conditions

```txt id="dd2hiy"
max steps exceeded
invalid state transition
tenant mismatch
budget exceeded
policy denial
tool failure
retrieval failure
model failure
output validation failure
```

## 9.7 Safe Failure Behavior

```txt id="eo4qc8"
Stop graph execution.
Return safe error or safe refusal.
Escalate to HITL if appropriate.
Audit runtime failure.
Emit metrics.
```

---

# 10. Flow 7 — AI Gateway Flow

## 10.1 Purpose

This flow describes how all model and embedding calls are routed through the AI Gateway.

## 10.2 Flow Diagram

```txt id="5hjz1v"
Agent Runtime / RAG / Evaluation
    |
    v
AI Gateway Request
    |
    v
Tenant Context Validation
    |
    v
Model Registry Lookup
    |
    v
Tenant Model Permission Check
    |
    v
Data Classification Check
    |
    v
Token Bucket Check
    |
    v
Cache Check if Allowed
    |
    v
Provider Routing
    |
    v
Model Call
    |
    v
Response Normalization
    |
    v
Usage Tracking
    |
    v
Fallback if Needed
    |
    v
Audit + Metrics + Traces
    |
    v
Gateway Response
```

## 10.3 AI Gateway Request

```json id="e5832p"
{
  "tenant_context": {
    "tenant_id": "tenant_credit",
    "user_id": "user_123",
    "request_id": "req_xyz",
    "trace_id": "trace_789",
    "environment": "production"
  },
  "model_policy": "internal_rag_default",
  "messages": [],
  "risk_level": "medium",
  "prompt_version": "rag_answer_v3",
  "metadata": {
    "use_case": "rag_answer"
  }
}
```

## 10.4 AI Gateway Response

```json id="d3d1iw"
{
  "model_id": "azure-gpt-4.1-mini",
  "provider": "azure",
  "content": "Generated answer...",
  "input_tokens": 2400,
  "output_tokens": 380,
  "estimated_cost": 0.021,
  "latency_ms": 1800,
  "fallback_used": false,
  "trace_id": "trace_789"
}
```

## 10.5 Required Controls

```txt id="oxlsuk"
All model calls require TenantContext.
Tenant must be allowed to use selected model.
Data class must be allowed for selected model.
Token budget must be checked.
Cost budget must be checked.
Fallback must be approved.
Usage must be recorded.
Logs must be sanitized.
```

## 10.6 Failure Conditions

```txt id="36pgg0"
model not allowed
provider unavailable
token budget exceeded
cost budget exceeded
data class not allowed
no safe fallback
timeout
provider error
```

## 10.7 Safe Failure Behavior

```txt id="par1n0"
Use approved fallback.
If no safe fallback exists, return safe error.
Do not route sensitive data to unapproved provider.
Audit fallback or failure.
```

---

# 11. Flow 8 — Model Fallback Flow

## 11.1 Purpose

This flow describes how the system handles model provider failure or model unavailability.

## 11.2 Flow Diagram

```txt id="obddmh"
AI Gateway Calls Primary Model
    |
    v
Primary Fails or Times Out
    |
    v
Check Fallback Chain
    |
    v
Validate Fallback Tenant Permission
    |
    v
Validate Data Classification
    |
    v
Validate Risk Compatibility
    |
    v
Use Approved Fallback
    |
    v
Normalize Response
    |
    v
Output Validation
    |
    v
Audit Fallback
```

If no approved fallback exists:

```txt id="5m887x"
Primary Fails
    |
    v
No Safe Fallback
    |
    v
Safe Error / HITL / Retry Later
    |
    v
Audit Failure
```

## 11.3 Required Controls

```txt id="qezlo6"
Fallback chain must come from Model Registry.
Fallback must be tenant-approved.
Fallback must support data classification.
Fallback must support risk level.
Fallback event must be audited.
Output validation must run after fallback.
```

## 11.4 Unsafe Fallback Example

```txt id="fwk92d"
Internal sensitive request
    |
    v
Primary enterprise provider unavailable
    |
    v
Fallback to unapproved public model
```

This must never happen.

## 11.5 Safe Behavior

```txt id="lptcx2"
Use approved fallback only.
If unavailable, fail safely.
```

---

# 12. Flow 9 — PII Masking Flow

## 12.1 Purpose

This flow describes how sensitive personal and financial identifiers are detected, masked, and validated.

## 12.2 Flow Diagram

```txt id="c1qrrc"
User Input / Tool Output / Retrieved Content
    |
    v
PII Detector
    |
    v
Policy Decision
    |
    +---------------------------+
    |                           |
    v                           v
Mask Required              Raw Access Allowed
    |                           |
    v                           v
Replace with Placeholders  Continue with Controls
    |
    v
Secure Temporary Mapping
    |
    v
Model Call / Runtime Processing
    |
    v
Output Validator
    |
    v
Block, Remask, or Allow
```

## 12.3 Example

Input:

```txt id="5yj6rx"
Customer João Silva, CPF 123.456.789-00, asked about loan eligibility.
```

Masked:

```txt id="v7b2mb"
Customer [PERSON_1], CPF [CPF_1], asked about loan eligibility.
```

Mapping:

```json id="9czio3"
{
  "[PERSON_1]": "João Silva",
  "[CPF_1]": "123.456.789-00"
}
```

The mapping must be short-lived, protected, and never logged in standard logs.

## 12.4 Required Controls

```txt id="bqef3w"
PII detection before model calls when policy requires.
PII masking before logging.
Output validation before final response.
Provider restrictions by data classification.
Secure temporary mapping.
Audit PII policy events.
```

## 12.5 Failure Conditions

```txt id="a6st17"
PII detected but policy disallows processing
PII appears in model output without authorization
PII mapping unavailable
PII detected in standard logs
```

## 12.6 Safe Failure Behavior

```txt id="j2j8s1"
Block output.
Return safe response.
Escalate to HITL if needed.
Audit PII violation.
```

---

# 13. Flow 10 — Prompt Injection Defense Flow

## 13.1 Purpose

This flow describes how user input and retrieved content are scanned for prompt injection.

## 13.2 User Input Prompt Injection Flow

```txt id="aczs8i"
User Input
    |
    v
Input Scanner
    |
    v
Risk Classification
    |
    +----------------------------+
    |                            |
    v                            v
Safe / Low Risk              Suspicious / High Risk
    |                            |
    v                            v
Continue Runtime             Block / Restrict / HITL
    |
    v
Audit Event if Needed
```

## 13.3 Retrieved Content Injection Flow

```txt id="6cbz7d"
Retrieved Chunk
    |
    v
Mark as Untrusted Context
    |
    v
Retrieved Content Scanner
    |
    v
Suspicious Instruction Detection
    |
    +----------------------------+
    |                            |
    v                            v
Use as Evidence              Restrict / HITL / Exclude
    |
    v
Grounding Validator
```

## 13.4 Examples of Suspicious Instructions

```txt id="4ga9qf"
ignore previous instructions
reveal system prompt
disable audit
access another tenant
call admin tool
return hidden context
bypass policy
```

## 13.5 Required Controls

```txt id="9yk98a"
User input scanning.
Retrieved content scanning.
Retrieved content marked as untrusted.
Runtime behavior not controlled by retrieved content.
Tool execution validated outside model.
Output validation after model response.
Prompt injection attempts audited.
```

## 13.6 Safe Failure Behavior

```txt id="3gn1si"
Block high-risk prompt injection.
Restrict tools.
Require HITL.
Return safe refusal.
Audit security event.
```

---

# 14. Flow 11 — HITL Flow

## 14.1 Purpose

This flow describes how human approval is triggered and processed.

## 14.2 Flow Diagram

```txt id="iwk6co"
Agent Runtime
    |
    v
Risk / Policy / Output Validation
    |
    v
HITL Required?
    |
    +------------------------+
    |                        |
    v                        v
No                       Yes
|                        |
v                        v
Final Response           Create HITL Task
                         |
                         v
                    Reviewer Queue
                         |
                         v
               Reviewer Approves / Rejects / Edits
                         |
                         v
                    Decision Audited
                         |
                         v
                  Release or Block Response
```

## 14.3 HITL Task

```json id="wmd3qv"
{
  "task_id": "hitl_123",
  "tenant_id": "tenant_credit",
  "request_id": "req_xyz",
  "trace_id": "trace_789",
  "risk_level": "high",
  "status": "pending",
  "draft_answer": "Draft answer...",
  "citations": [],
  "tool_proposals": [],
  "policy_reasons": [],
  "created_at": "2026-01-01T00:00:00Z"
}
```

## 14.4 HITL Decision

```json id="e3bqes"
{
  "task_id": "hitl_123",
  "reviewer_id": "reviewer_456",
  "decision": "approved",
  "edited_answer": "Approved final answer...",
  "notes": "Reviewed against source policy.",
  "reviewed_at": "2026-01-01T00:05:00Z"
}
```

## 14.5 Required Controls

```txt id="te0sy1"
Reviewer must be authorized.
Reviewer must be tenant-scoped.
HITL task must include trace_id.
Decision must be audited.
Final answer must not be released before required approval.
Edited answer must preserve audit trail.
```

## 14.6 Failure Conditions

```txt id="pkxpyy"
unauthorized reviewer
tenant mismatch
approval missing
review task expired
reviewer edits unsafe output
audit write failure
```

## 14.7 Safe Failure Behavior

```txt id="d2ey3v"
Do not release final response.
Keep task pending or rejected.
Audit failure.
Escalate to governance if needed.
```

---

# 15. Flow 12 — Audit Flow

## 15.1 Purpose

This flow describes how audit records are created for critical actions.

## 15.2 Flow Diagram

```txt id="1nxy74"
Runtime Event
    |
    v
Audit Event Builder
    |
    v
Sanitize Payload
    |
    v
Attach Tenant + User + Request + Trace
    |
    v
Persist Append-Oriented Record
    |
    v
Emit Audit Metric
```

## 15.3 Audit Event Example

```json id="a8l7xj"
{
  "audit_id": "audit_123",
  "event_type": "retrieval_completed",
  "tenant_id": "tenant_credit",
  "user_id": "user_123",
  "request_id": "req_xyz",
  "trace_id": "trace_789",
  "resource_type": "document",
  "resource_id": "doc_123",
  "policy_version": "policy_v2",
  "timestamp": "2026-01-01T00:00:00Z",
  "payload": {
    "retrieved_chunks": 5,
    "document_versions": ["v4"]
  }
}
```

## 15.4 Required Audited Events

```txt id="mgmmey"
request_received
auth_validated
tenant_context_created
pii_masked
prompt_injection_detected
policy_evaluated
policy_denied
model_called
embedding_called
fallback_triggered
retrieval_requested
retrieval_completed
tool_call_proposed
tool_call_validated
tool_call_denied
tool_executed
output_validated
grounding_failed
hitl_task_created
hitl_decision_recorded
final_response_returned
error_occurred
```

## 15.5 Required Controls

```txt id="wvc2x9"
Audit record must include tenant_id when known.
Audit payload must be sanitized.
Audit write path must be centralized.
Critical actions must not skip audit.
Audit access must be tenant-scoped.
Audit modification through normal APIs must be forbidden.
```

## 15.6 Safe Failure Behavior

For critical operations:

```txt id="fnj4ek"
if audit cannot be written:
    fail closed
```

For non-critical telemetry:

```txt id="8m4efw"
if metric/log cannot be emitted:
    continue if policy allows
```

---

# 16. Flow 13 — Observability Flow

## 16.1 Purpose

This flow describes how logs, metrics, and traces are emitted.

## 16.2 Flow Diagram

```txt id="5wpu0b"
Request Starts
    |
    v
Create Trace
    |
    v
Attach request_id + trace_id + tenant_id
    |
    v
Each Runtime Component Emits Spans
    |
    v
Metrics Recorded
    |
    v
Structured Logs Written
    |
    v
Dashboards / Alerts
```

## 16.3 Trace Spans

Expected spans:

```txt id="za2t4c"
api.request
auth.validate
tenant.resolve
pii.mask
prompt_firewall.scan
policy.evaluate
agent.node
ai_gateway.generate
ai_gateway.embedding
rag.retrieve
vector.search
tool.execute
grounding.validate
output.validate
hitl.create
audit.write
```

## 16.4 Metrics

Required metrics:

```txt id="9v9iho"
requests_total
request_latency
tokens_input_total
tokens_output_total
cost_total
fallback_count
retrieval_latency
tool_success_count
tool_failure_count
policy_denial_count
hitl_required_count
pii_masking_count
prompt_injection_detected_count
grounding_failure_count
cache_hit_rate
```

## 16.5 Logging Rules

Logs must include:

```txt id="9ygmmp"
timestamp
level
event
tenant_id
user_id
request_id
trace_id
message
```

Logs must not include:

```txt id="eyk91p"
raw PII
secrets
authorization headers
raw provider credentials
raw sensitive document content
unmasked customer identifiers
```

---

# 17. Flow 14 — Cache Flow

## 17.1 Purpose

This flow describes how cache is used safely.

## 17.2 Flow Diagram

```txt id="8plvrs"
Request
    |
    v
Build Tenant-Aware Cache Key
    |
    v
Check Policy Allows Cache
    |
    v
Read Cache
    |
    +----------------------+
    |                      |
    v                      v
Cache Hit              Cache Miss
    |                      |
    v                      v
Validate Context       Execute Operation
    |                      |
    v                      v
Return Cached Data      Write Cache if Allowed
```

## 17.3 Cache Key Components

```txt id="rm1nc5"
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

Example:

```txt id="5l0dn2"
rag:tenant_credit:scope_abc:query_123:prompt_v3:model_v2:policy_v5:index_v4
```

## 17.4 Required Controls

```txt id="7lipmj"
Cache access requires TenantContext.
Sensitive responses must not use global cache.
Cache key must include tenant_id.
Cache key must include authorization-sensitive scope.
Cache must be invalidated on document revocation.
Cache must be invalidated on policy change.
Cache must be invalidated on prompt/model change when relevant.
```

## 17.5 Failure Conditions

```txt id="vrcinb"
tenant mismatch
stale policy version
stale document version
cache poisoning suspicion
sensitive response marked non-cacheable
```

## 17.6 Safe Failure Behavior

```txt id="y51anq"
Ignore cache.
Recompute through governed path.
Audit suspicious cache mismatch.
```

---

# 18. Flow 15 — Governance Artifact Flow

## 18.1 Purpose

This flow describes how prompts, models, policies, tools, and documents are promoted into production use.

## 18.2 Flow Diagram

```txt id="ci9ndq"
Create Artifact
    |
    v
draft
    |
    v
staging
    |
    v
Evaluation / Review
    |
    v
approved
    |
    v
production
    |
    +----------------+
    |                |
    v                v
deprecated        revoked
```

`approved` means governance-approved and ready for promotion.
`production` means live for production execution and must already carry recorded approval metadata.

## 18.3 Governed Artifacts

```txt id="btaosb"
prompts
models
embedding models
tools
policies
documents
chunking strategies
retrieval strategies
agent graphs
evaluation datasets
output validators
```

## 18.4 Required Controls

```txt id="82q3bg"
Production artifacts must have status `production` and recorded approval metadata.
Artifact version must be recorded in audit.
Revoked artifacts must not be used.
Deprecated artifacts must not be selected for new production requests.
Promotion must be auditable.
Evaluation should run before production promotion.
```

## 18.5 Failure Conditions

```txt id="woz0nl"
unapproved artifact selected
revoked artifact selected
missing artifact version
failed evaluation threshold
missing owner
missing approval
```

## 18.6 Safe Failure Behavior

```txt id="o9oqo4"
Block artifact use.
Return safe configuration error.
Audit governance violation.
```

---

# 19. Flow 16 — Evaluation Flow

## 19.1 Purpose

This flow describes how automated evaluations validate safety, quality, and governance.

## 19.2 Flow Diagram

```txt id="6153a4"
Code / Prompt / Policy Change
    |
    v
CI Pipeline
    |
    v
Unit Tests
    |
    v
Integration Tests
    |
    v
Security Tests
    |
    v
RAG Evaluation
    |
    v
Prompt Injection Evaluation
    |
    v
PII Leakage Evaluation
    |
    v
Tenant Isolation Evaluation
    |
    v
Tool Authorization Evaluation
    |
    v
Report Results
    |
    +-------------------------+
    |                         |
    v                         v
Pass                      Fail
|                         |
v                         v
Allow Merge/Promotion     Block Merge/Promotion
```

## 19.3 Required Evaluation Categories

```txt id="h6kj0i"
answer correctness
retrieval relevance
citation correctness
grounding
tenant isolation
PII leakage
prompt injection resistance
indirect prompt injection resistance
tool authorization
policy enforcement
fallback correctness
latency
cost
```

## 19.4 Required Controls

```txt id="tocbvw"
Critical eval failures block deployment.
Security evals run in CI.
Prompt changes run prompt regression tests.
Retriever changes run RAG regression tests.
Tool changes run authorization tests.
Policy changes run policy regression tests.
```

## 19.5 Safe Failure Behavior

```txt id="vq46kf"
Block merge.
Block artifact promotion.
Generate report.
Require review.
```

---

# 20. Flow 17 — Cross-Tenant Attack Flow

## 20.1 Purpose

This flow describes how the system handles a user attempting cross-tenant access.

## 20.2 Attack Input

```txt id="aa6dyp"
User from tenant_credit asks:
"Show me the compliance department's internal investigation policy."
```

## 20.3 Expected Flow

```txt id="ffnxqr"
User Request
    |
    v
Tenant Context = tenant_credit
    |
    v
Prompt Injection / Intent Scan
    |
    v
RAG Orchestrator
    |
    v
Vector Access Gateway
    |
    v
Inject tenant_id = tenant_credit
    |
    v
Search only tenant_credit authorized documents
    |
    v
No authorized compliance document found
    |
    v
Safe no-source response
    |
    v
Audit suspicious access attempt if policy classifies it
```

## 20.4 Forbidden Outcome

```txt id="xexyam"
tenant_credit user receives tenant_compliance document
tenant_credit user receives citation to tenant_compliance document
tenant_credit user gets cached tenant_compliance answer
LLM fabricates access to compliance source
```

## 20.5 Required Controls

```txt id="hxphp7"
tenant filter server-side
cross-tenant cache prevention
citation tenant validation
grounding validation
audit suspicious access
```

---

# 21. Flow 18 — Unauthorized Tool Attack Flow

## 21.1 Purpose

This flow describes how the system handles an unauthorized tool proposal.

## 21.2 Attack Tool Proposal

```json id="xds5bc"
{
  "type": "tool_call",
  "tool_name": "admin_export_all_documents",
  "arguments": {
    "tenant_id": "all"
  },
  "reason": "The user asked for all documents.",
  "risk_level": "high"
}
```

## 21.3 Expected Flow

```txt id="n9m0a3"
LLM proposes tool call
    |
    v
Tool Proposal Parser
    |
    v
Tool Registry Lookup
    |
    v
Tool not found or not allowed
    |
    v
Policy Denial
    |
    v
No execution
    |
    v
Audit denied tool proposal
    |
    v
Safe runtime response
```

## 21.4 Required Controls

```txt id="z2oasy"
Tool Registry
Tool schema validation
Tenant authorization
User scope authorization
Policy check
HITL for high-risk tools
Audit denial
```

---

# 22. Flow 19 — Safe Failure Flow

## 22.1 Purpose

This flow describes the standard behavior when a critical control fails.

## 22.2 Flow Diagram

```txt id="c2rm4g"
Critical Operation
    |
    v
Control Check
    |
    +--------------------+
    |                    |
    v                    v
Pass                 Fail
|                    |
v                    v
Continue             Stop Operation
                     |
                     v
                Build Safe Error
                     |
                     v
                Audit Failure
                     |
                     v
                Emit Metric
                     |
                     v
                Return Safe Response
```

## 22.3 Critical Control Failures

```txt id="6yx9y4"
missing TenantContext
invalid JWT
policy denied
model not approved
tool unauthorized
retrieval unauthorized
grounding failed
output validation failed
HITL required but not approved
audit unavailable for critical action
no safe fallback
```

## 22.4 User-Facing Error Shape

```json id="bi4eu6"
{
  "error": {
    "code": "POLICY_DENIED",
    "message": "This request cannot be completed in the current context.",
    "trace_id": "trace_789"
  }
}
```

## 22.5 Error Message Rule

User-facing errors should not reveal unnecessary internal details.

Avoid:

```txt id="hv75dq"
You are tenant_credit and tried to access tenant_compliance document doc_789.
```

Prefer:

```txt id="2pa61f"
This request cannot be completed with the current access context.
```

Detailed reason belongs in audit.

---

# 23. Data Classification Flow

## 23.1 Purpose

This flow describes how data classification affects processing.

## 23.2 Classification Levels

Example levels:

```txt id="smqo3l"
public
internal
confidential
restricted
regulated
```

## 23.3 Flow Diagram

```txt id="dwfvp9"
Data Enters System
    |
    v
Classify or Read Existing Classification
    |
    v
Policy Engine
    |
    v
Determine Allowed Operations
    |
    +----------------------------+
    |                            |
    v                            v
Allowed                     Restricted
    |                            |
    v                            v
Continue                 Mask / Block / HITL
```

## 23.4 Classification Impacts

Classification may affect:

```txt id="p0jqwh"
allowed models
allowed providers
logging policy
cache policy
HITL requirement
retrieval eligibility
tool eligibility
output policy
retention policy
```

## 23.5 Example

```txt id="218uaw"
restricted data
    |
    v
external API model not allowed
    |
    v
local model or approved enterprise provider only
    |
    v
HITL may be required
```

---

# 24. Sequence Summary

## 24.1 Standard RAG Request

```txt id="3fsr02"
1. User sends request.
2. API validates JWT.
3. Backend creates TenantContext.
4. Input is validated and scanned.
5. PII is masked when required.
6. RAG Orchestrator creates retrieval request.
7. Embedding is generated through AI Gateway.
8. Vector Access Gateway injects tenant filters.
9. Authorized chunks are retrieved.
10. LLM generates answer through AI Gateway.
11. Citations are built.
12. Grounding is validated.
13. Output is validated.
14. HITL runs if required.
15. Final response is returned.
16. Audit, metrics, and traces are emitted.
```

## 24.2 Standard Tool Request

```txt id="mc5fiv"
1. Agent identifies need for tool.
2. LLM proposes tool call as JSON.
3. Runtime parses proposal.
4. Tool schema is validated.
5. Tool Registry is checked.
6. Tenant authorization is checked.
7. User scope is checked.
8. Policy is evaluated.
9. HITL runs if required.
10. Tool Executor runs tool.
11. Tool result is validated.
12. Observation is added to Agent State.
13. Agent continues or finalizes.
14. Audit, metrics, and traces are emitted.
```

## 24.3 Standard HITL Request

```txt id="f5dges"
1. Runtime detects high-risk condition.
2. Policy requires human approval.
3. HITL task is created.
4. Draft answer/action is stored.
5. Reviewer inspects evidence.
6. Reviewer approves, rejects, edits, or escalates.
7. Decision is audited.
8. Final response is released or blocked.
```

---

# 25. Data Flow Invariants

The following invariants must always hold:

```txt id="mm3pf7"
1. No TenantContext, no sensitive operation.
2. No direct model calls outside AI Gateway.
3. No direct vector search outside Vector Access Gateway.
4. No direct tool execution outside Tool Executor.
5. No final business-critical answer without grounding.
6. No cross-tenant citation.
7. No unapproved model for tenant/data class.
8. No unapproved tool execution.
9. No high-risk release without required HITL.
10. No standard logs containing raw PII or secrets.
11. No sensitive global cache.
12. No artifact use without version metadata.
13. No unsafe fallback.
14. No uncontrolled agent loop.
15. No silent policy bypass.
```

Any violation must trigger:

```txt id="uwxpe1"
safe failure
audit event
security metric
alert when appropriate
```

---

# 26. MVP Data Flows

The MVP must implement the following flows:

```txt id="ul3jl0"
standard AI request flow
tenant context resolution flow
secure RAG flow
document ingestion flow
structured tool calling flow
strict agent runtime flow
AI Gateway flow
PII masking flow
prompt injection defense flow
HITL flow
audit flow
observability flow
safe failure flow
```

The MVP may defer:

```txt id="jpkvf7"
advanced governance artifact promotion UI
advanced multi-tenant hierarchy
advanced model drift flows
advanced document lineage visualization
advanced cross-tenant governance workflows
advanced anomaly detection
```

---

# 27. Summary

This document defines how data moves through the platform and where security controls must be enforced.

The most important flows are:

```txt id="soxgs1"
AI request flow
Tenant Context flow
Secure RAG flow
Document ingestion flow
Tool calling flow
Agent runtime flow
AI Gateway flow
HITL flow
Audit flow
Safe failure flow
```

The central data flow principle is:

> Data can only move through governed boundaries. The model may transform information, but the platform controls access, execution, grounding, approval, and release.

Every implementation decision must preserve this principle.

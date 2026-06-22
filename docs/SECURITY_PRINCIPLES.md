# SECURITY_PRINCIPLES

## 1. Purpose

This document defines the baseline security principles for the governed multi-tenant agentic RAG platform.

It complements:

```txt
docs/THREAT_MODEL.md
docs/TENANT_MODEL.md
docs/ARCHITECTURE.md
docs/DATA_FLOW.md
```

The goal is to make the core invariants explicit before implementation.

---

## 2. Core Invariant

The central rule of the platform is:

> The model reasons, but the platform governs.

The LLM may generate plans, summaries, classifications, grounded answers, and structured tool proposals, but it must never be the trusted authority for security-critical decisions.

---

## 3. Zero-Trust Assumption

The platform must assume the following are untrusted by default:

```txt
user input
LLM output
retrieved documents
tool outputs
external providers
client-supplied filters
client-supplied tenant identifiers
prompt text alone
```

Every sensitive operation must therefore be validated by deterministic application logic.

---

## 4. Tenant Isolation First

Tenant isolation is a primary security boundary.

Required rules:

```txt
tenant is resolved from trusted identity context
tenant is enforced server-side
tenant is never inferred from natural language
tenant is never trusted from request body
tenant cannot be changed by the model
tenant cannot be changed by tool arguments
tenant cannot be changed by retrieved content
```

No sensitive operation may proceed without a valid `TenantContext`.

---

## 5. Trusted Control Layers

The trusted control layers of the platform are:

```txt
Authentication and authorization layer
TenantContext
Policy Engine
AI Gateway
Vector Access Gateway
Tool Executor
Audit Service
HITL workflow
Output validation layer
```

Security logic must live in these layers, not only in prompts.

---

## 6. Gateway Principle

All sensitive integrations must be accessed through governed gateways.

Mandatory rules:

```txt
all model calls go through AI Gateway
all embedding calls go through AI Gateway
all vector search goes through Vector Access Gateway
all tool executions go through Tool Executor
all critical actions emit audit events
```

Direct access from business logic to providers, vector backends, or tools is a violation.

---

## 7. Structured Tool Calling Only

The LLM may propose tool calls, but it must not execute them directly.

Required controls:

```txt
tool proposal must be structured JSON
tool proposal must match registered schema
tool must exist in Tool Registry
tenant and scope authorization must be checked
policy must be checked
HITL must run when required
tool result must be treated as untrusted observation
```

---

## 8. Grounding Before Release

Business-critical answers must be grounded in authorized sources.

Required rules:

```txt
retrieval must be tenant-scoped
citations must reference authorized chunks
inactive or unauthorized documents cannot ground answers
missing grounding fails safely
cross-tenant citations are forbidden
```

If sufficient grounding cannot be established, the platform must refuse safely or trigger HITL.

---

## 9. Prompt Injection Defense in Depth

Prompt injection must be handled as a layered defense problem.

Required layers:

```txt
input scanning
retrieved content sanitization
policy enforcement outside prompts
tool authorization outside the model
output validation
audit of suspicious attempts
```

Retrieved documents and tool outputs may inform the answer, but they must never control runtime behavior.

---

## 10. Data Minimization and Protection

The platform should minimize unnecessary exposure of sensitive data.

Required practices:

```txt
PII detection
PII masking when policy requires
sanitized standard logs
secret redaction
classification-aware provider routing
tenant-aware cache keys
retention-aware audit handling
```

Sensitive data should only be revealed to tools, models, reviewers, or users when policy explicitly allows it.

---

## 11. Fail Closed

When a critical control cannot be validated, the system must fail closed.

Examples:

```txt
missing TenantContext
invalid authentication
policy engine unavailable
model not allowed
tool unauthorized
retrieval unauthorized
grounding failure
output validation failure
HITL required but not approved
no safe fallback available
audit unavailable for critical action
```

Safe failure may mean refusal, denial, escalation, pending review, or retry-later behavior.

---

## 12. Auditability and Reproducibility

Every critical execution path must be explainable after the fact.

Minimum expectations:

```txt
tenant_id recorded
user_id recorded
request_id recorded
trace_id recorded
prompt version recorded
model version recorded
policy version recorded
retrieved document versions recorded
tool proposals and executions recorded
HITL decisions recorded
fallback events recorded
```

Production behavior must be reproducible or at least forensically explainable from stored metadata.

---

## 13. Governance Over Artifacts

Prompts, models, policies, tools, and governed documents are production artifacts.

Required rules:

```txt
artifacts are versioned
artifacts have lifecycle states
promotion to production requires approval metadata
revoked artifacts are blocked
deprecated artifacts are not selected for new production use
artifact versions appear in audit
```

---

## 14. Implementation Rule

Whenever there is tension between convenience and control, the system must choose control.

In practice:

```txt
explicit contracts over implicit behavior
deterministic enforcement over prompt-only instructions
safe refusal over unsafe completion
bounded execution over open-ended autonomy
defense in depth over single-layer trust
```

---

## 15. Summary

The security posture of the platform is defined by a small number of non-negotiable rules:

```txt
no TenantContext, no sensitive operation
no direct model calls outside AI Gateway
no direct vector access outside Vector Access Gateway
no direct tool execution outside Tool Executor
no final critical answer without grounding
no high-risk release without required HITL
no fail-open on missing security controls
```

All implementation and architecture decisions must preserve these principles.

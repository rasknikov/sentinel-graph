# Documentation Index

## Purpose

This file is the entry point for the project documentation.

The repository currently has a documentation-first structure. The documents below define the architecture, security model, tenant isolation model, data flow, technology choices, roadmap, and implementation sequencing for the platform.

## Recommended Reading Order

1. [SPEC.md](/D:/Projetos/sentinel-graph/docs/SPEC.md)
2. [ARCHITECTURE.md](/D:/Projetos/sentinel-graph/docs/ARCHITECTURE.md)
3. [TENANT_MODEL.md](/D:/Projetos/sentinel-graph/docs/TENANT_MODEL.md)
4. [THREAT_MODEL.md](/D:/Projetos/sentinel-graph/docs/THREAT_MODEL.md)
5. [SECURITY_PRINCIPLES.md](/D:/Projetos/sentinel-graph/docs/SECURITY_PRINCIPLES.md)
6. [DATA_FLOW.md](/D:/Projetos/sentinel-graph/docs/DATA_FLOW.md)
7. [STACK.md](/D:/Projetos/sentinel-graph/docs/STACK.md)
8. [ROADMAP.md](/D:/Projetos/sentinel-graph/docs/ROADMAP.md)
9. [IMPLEMENTATION_PLAN.md](/D:/Projetos/sentinel-graph/docs/IMPLEMENTATION_PLAN.md)
10. [resume.md](/D:/Projetos/sentinel-graph/docs/resume.md)

## Document Roles

- [SPEC.md](/D:/Projetos/sentinel-graph/docs/SPEC.md): canonical functional and technical specification
- [ARCHITECTURE.md](/D:/Projetos/sentinel-graph/docs/ARCHITECTURE.md): architectural boundaries and runtime model
- [TENANT_MODEL.md](/D:/Projetos/sentinel-graph/docs/TENANT_MODEL.md): tenant isolation rules and invariants
- [THREAT_MODEL.md](/D:/Projetos/sentinel-graph/docs/THREAT_MODEL.md): threats, mitigations, and security test matrix
- [SECURITY_PRINCIPLES.md](/D:/Projetos/sentinel-graph/docs/SECURITY_PRINCIPLES.md): baseline security invariants
- [DATA_FLOW.md](/D:/Projetos/sentinel-graph/docs/DATA_FLOW.md): end-to-end governed data movement
- [STACK.md](/D:/Projetos/sentinel-graph/docs/STACK.md): recommended stack and repo layout
- [ROADMAP.md](/D:/Projetos/sentinel-graph/docs/ROADMAP.md): phased delivery strategy
- [IMPLEMENTATION_PLAN.md](/D:/Projetos/sentinel-graph/docs/IMPLEMENTATION_PLAN.md): practical build sequence
- [resume.md](/D:/Projetos/sentinel-graph/docs/resume.md): design summary and rationale

## Current Repository State

The repository has already been scaffolded to match the documentation:

```txt
apps/
packages/
infra/
tests/
docs/
```

The `.local/` directory is intentionally left untouched for later exploration.

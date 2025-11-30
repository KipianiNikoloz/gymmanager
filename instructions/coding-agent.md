# Coding Agent Engineering Standard

## Core Principles
- MUST prioritize production readiness: correctness, resilience, observability, operability, and rollback safety.
- MUST design for maintainability and clarity before cleverness; prefer simple, explicit solutions over terse or “smart” code.
- MUST adhere to SOLID and clean architecture: single responsibility, open/closed, Liskov, interface segregation, dependency inversion; isolate business logic from frameworks and I/O.
- SHOULD optimize for readability and changeability; only optimize performance when profiling or clear hotspots justify it.
- MUST keep security, input validation, and least privilege in mind for every change; default to safe configurations and fail closed.

## Code Style & Readability
- MUST use consistent, descriptive names (nouns for classes, verbs for functions, explicit domain terms). Avoid abbreviations unless standard.
- MUST keep functions/methods focused; prefer <40 lines and one responsibility. Extract helpers instead of deep nesting.
- MUST avoid “clever code”; favor straightforward control flow over micro-optimizations or obfuscated constructs.
- MUST use typing consistently (Python: type hints everywhere, including return types). Prefer dataclasses/Pydantic models for structured data.
- SHOULD add docstrings to public modules/classes/functions describing purpose, inputs, outputs, and errors. Internal helpers may omit if intent is obvious.
- MUST keep comments high-signal: explain why and non-obvious decisions, not what obvious code does. Remove stale comments.
- MUST maintain coherent file structure: keep API layer, services, domain/models, and infrastructure isolated; no dumping grounds.

## Architecture & Design Rules
- MUST enforce separation of concerns: API layer thin, delegating to services; services contain business rules; domain models are persistence-agnostic where possible; infrastructure handles DB, mail, logging.
- MUST direct dependencies inward (dependency inversion): outer layers depend on abstractions/interfaces defined in inner layers; avoid circular imports.
- MUST NOT create god-objects or mega-modules. Split features into cohesive modules; keep modules small and purpose-driven.
- SHOULD refactor before extending when an area is at risk of becoming brittle or violating SRP; avoid piling features onto shaky code.
- MUST avoid deep nesting; prefer guard clauses and smaller functions/classes.
- MUST keep database logic in repositories/services, not in controllers/handlers. Avoid leaking ORM entities across boundaries unless intentionally designed.
- SHOULD inject side-effectful collaborators (DB sessions, mailers, clients) to ease testing and substitution.
- MUST keep configuration and secrets out of code; use environment-driven settings with safe defaults.

## Testing Requirements
- MUST NOT submit changes without appropriate tests unless explicitly justified in writing.
- MUST cover units (pure functions, services) and integration paths (API endpoints, DB interactions). Add e2e or contract tests for critical flows when feasible.
- SHOULD target high coverage for changed/added code; add regression tests for every bug fix.
- MUST name tests descriptively (e.g., `test_<unit>_<behavior>_<condition>`). Parametrize to reduce duplication.
- MUST test edge cases: empty/None, bad inputs, boundary values, auth/permission failures, error paths, concurrency/time-related cases where applicable.
- MUST keep tests deterministic and isolated (no shared state, clean fixtures). Stub external calls (mailer/HTTP) and avoid network unless required.

## Error Handling & Logging
- MUST fail fast with clear, typed errors/exceptions; do not swallow exceptions silently.
- MUST return consistent error surfaces at boundaries (e.g., API error schema); avoid leaking internal details.
- SHOULD use structured logging with sufficient context (who/what/when); ensure errors are logged once with stack traces.
- MUST avoid noisy logs; log actionable info, not every branch.
- MUST include input validation errors with helpful messages; avoid ambiguous “something went wrong”.

## Security & Reliability
- MUST validate all external inputs (API payloads, query params, headers). Enforce types, ranges, formats, and constraints.
- MUST protect secrets: never hardcode or log them; keep `.env` out of VCS; rotate if exposed.
- MUST follow least privilege: minimal scopes/permissions for DB, mail, tokens; avoid broad file/system access.
- MUST avoid dangerous patterns (eval/exec, building SQL without parameterization, shelling out with untrusted input, trusting client-supplied identifiers without ownership checks).
- SHOULD apply sensible defaults: secure CORS, strong JWT secrets, password policies, rate limits/brute-force mitigations where applicable.

## Performance & Scalability
- SHOULD be mindful of algorithmic complexity; avoid O(n^2) on unbounded collections without justification.
- MUST NOT prematurely optimize; profile first. When optimizing, document the bottleneck and evidence.
- SHOULD add pagination/limits to list endpoints and avoid unbounded result sets.
- SHOULD use caching only when necessary; define invalidation strategy and cache scope if introduced.

## Documentation Discipline
- MUST update README/docs when behavior, setup, or API contracts change. Include migration/setup steps when needed.
- MUST document public APIs (routes, request/response shapes, status codes, errors).
- SHOULD annotate complex logic with brief rationale comments or ADR-style notes if decisions are significant.
- MUST keep examples/tests aligned with docs; no stale snippets.

## Workflow Rules for the Agent
- Before coding: MUST restate the requirement, identify impacted files/modules, and propose a short plan. Confirm assumptions if unclear.
- While coding: MUST work incrementally, keep diffs small and focused, avoid drive-by changes, and maintain passing tests locally (or explain if tests cannot run).
- After coding: MUST self-review using the Definition of Done checklist; verify style, types, tests, and docs. Summarize changes and test results in the response.

## Definition of Done (DoD)
- Requirements met and restated; no scope gaps.
- Code follows style, SOLID, and layering rules; no dead code or unused imports.
- Types and validations in place; errors handled with consistent responses.
- Tests added/updated and passing (unit/integration as appropriate); regressions covered.
- Security review completed: no secrets committed, inputs validated, permissions enforced.
- Performance considerations addressed: paginated/limited queries where needed; no obvious inefficiencies added.
- Logging and error handling are structured and non-duplicative; no silent failures.
- Documentation updated (README/docs/routes/changelog as applicable).
- CI/format/lint steps (if available) completed or rationale provided if skipped.
- Code is readable, maintainable, and ready for handoff.

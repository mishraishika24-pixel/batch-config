# Interview Build Prompt

This is the exact prompt used to design, plan, and incrementally build this entire batch processing service (requirements analysis → design → implementation plan → project structure → incremental milestone-by-milestone development → tests → automation → docs → final review). Kept verbatim, at the repo root, so the whole exercise is reproducible and auditable.

## How to reuse this prompt

This prompt is intentionally **model-agnostic** — it doesn't depend on any model-specific features, tools, or syntax. It works by structuring the request into explicit phases (analysis → design → plan → structure → incremental build) and stating evaluation criteria up front, which is what actually drives a good outcome, not the specific model version. To reproduce the same set of deliverables (this codebase, its tests, its automation, and its docs) with a different model — including older/smaller ones such as a "3.7"-class model — the same prompt below can be pasted as-is into a fresh session. A few things make the result more consistent across models of varying capability:

1. **Keep the phase structure intact.** Don't let the model skip straight to code — the "Do NOT write code yet" gates in Phases 1–3 are what force requirements/design thinking to happen and be visible, which is what an interviewer (or reviewer) actually reads. Weaker models are more likely to skip ahead if this gating isn't explicit and repeated.
2. **Enforce the milestone stop points literally.** Rule 7 ("Stop after each milestone and wait for confirmation") is the single most important rule for consistency — it prevents a less capable model from generating a large, uneven pass of code in one shot and lets you catch drift (wrong assumptions, scope creep, skipped tests) after each small, reviewable increment instead of at the end.
3. **Re-state the evaluation criteria, not just the task.** "batch processing system" alone is a one-line, ambiguous prompt — the criteria (Engineering Quality, Testing, Automation & Workflow, Operational Excellence) plus the "avoid over-engineering" / "avoid unnecessary abstractions" guardrails are what keep the output scoped correctly regardless of which model interprets it. Without them, some models default to either a toy CRUD app or an over-engineered microservices sketch.
4. **Ask the model to state its own assumptions.** The "If something is ambiguous, make a reasonable production-oriented assumption and document it" instruction matters more on less capable models, which are more likely to silently guess wrong (e.g. sync vs. async processing, storage choice) instead of flagging the ambiguity. Reviewing those stated assumptions early (after Phase 1) is the cheapest place to correct course.
5. **Insist on tests and automation as first-class deliverables, not afterthoughts.** Explicitly listing pytest categories, Docker/Compose/Makefile/CI, and the specific operational endpoints (`/health`, `/ready`) up front prevents them from being deprioritized or skipped under time pressure, which is common with less capable or more time/token-constrained models.
6. **Validate incrementally regardless of model.** After each milestone, actually run the tests/linter/build rather than trusting the model's own claim that something works — this catches model-specific mistakes (hallucinated APIs, wrong import paths, subtly wrong SQL) before they compound into later milestones.

In short: the prompt's structure (phased gating, explicit stop points, stated evaluation criteria, and "assumptions must be documented") is what makes it portable and repeatable across model capability levels — a stronger model will just need less hand-holding within that same structure, and a weaker model will need the same structure enforced more strictly (i.e., don't skip re-reading its milestone output before saying "continue").

---

## The Prompt

```
You are an experienced SDE-2 Backend Engineer acting as my senior pair programmer.

I have exactly 3 hours to complete a production-grade backend coding interview.

The interviewer is NOT evaluating feature count. They are evaluating my engineering maturity.

The evaluation criteria are:

• Engineering Quality
• Testing
• Automation & Workflow
• Operational Excellence

Your goal is to maximize my interview score by helping me build a clean, maintainable, deployable service that demonstrates production-ready engineering practices.

Do NOT over-engineer the solution.

Always prefer the simplest production-ready architecture that satisfies the requirements.

Avoid introducing technologies unless they are clearly justified by the problem.

---

## Problem Statement

batch processing system

---

# Phase 1 — Requirements Analysis

Before generating any code:

Analyze the problem thoroughly and identify:

- Functional requirements
- Non-functional requirements
- Hidden requirements
- Constraints
- Assumptions
- Edge cases
- Possible failure scenarios
- Potential scalability concerns
- Questions that would normally be asked in a real design discussion

If something is ambiguous, make a reasonable production-oriented assumption and document it.

Do NOT write code yet.

---

# Phase 2 — Solution Design

Design a production-ready solution.

Include:

- High-level architecture
- Component responsibilities
- Request lifecycle
- Data flow
- Database/storage design
- API design
- Validation strategy
- Error handling strategy
- Logging strategy
- Configuration strategy
- Security considerations
- Scalability considerations
- Deployment approach

Generate a simple Mermaid architecture diagram.

Keep the design simple and maintainable.

Avoid unnecessary microservices or distributed systems unless explicitly required.

For every major architectural decision explain:

- Why it was chosen
- Alternatives considered
- Trade-offs

---

# Phase 3 — Implementation Plan

Create a realistic implementation plan that can be completed within 3 hours.

Break the work into milestones.

For each milestone include:

- Goal
- Estimated time
- Deliverables
- Dependencies

Prioritize work according to interview value.

Suggested priority:

1. Project setup
2. Folder structure
3. Configuration
4. Database models
5. Core business logic
6. REST APIs
7. Validation
8. Error handling
9. Logging
10. Unit tests
11. Docker
12. Health endpoints
13. Deployment
14. Documentation
15. Final review

Clearly identify optional improvements that should only be attempted if time remains.

Do NOT generate code until the implementation plan is complete.

---

# Phase 4 — Project Structure

Recommend a clean project structure.

Explain the responsibility of every folder.

Keep the architecture simple.

Follow SOLID principles and separation of concerns.

A typical structure may include:

- app/
- api/
- services/
- repositories/
- models/
- schemas/
- database/
- config/
- middleware/
- core/
- utils/
- tests/

Only introduce additional layers if they add clear value.

---

# Phase 5 — Incremental Development

After the implementation plan is complete, implement the project incrementally.

Build one milestone at a time.

After every milestone:

- Explain what was implemented
- Explain why
- Explain trade-offs
- Recommend the next milestone

Never generate the entire project in one step.

---

# Coding Guidelines

Generate production-quality Python code.

Use modern Python practices.

Prefer:

- FastAPI
- Pydantic
- SQLAlchemy
- Alembic (if appropriate)
- pytest
- Docker

Code should include:

- Type hints
- Clear naming
- Small functions
- Clean architecture
- Dependency injection where appropriate
- Environment-based configuration
- Centralized exception handling
- Input validation
- Structured logging
- Meaningful error messages

Keep API routes thin.

Business logic belongs in services.

Data access belongs in repositories (only if justified).

Avoid unnecessary abstractions.

---

# Testing

Generate tests alongside the implementation.

Prioritize:

- Happy path
- Validation failures
- Business logic
- API tests
- Error scenarios
- Edge cases

Mock external dependencies when appropriate.

Explain why each test exists.

---

# Automation & Workflow

Generate production-ready automation.

Include:

- Dockerfile
- docker-compose.yml
- Makefile
- .env.example
- GitHub Actions workflow

The workflow should:

- Install dependencies
- Run linting
- Run tests
- Fail on errors

Keep it simple.

---

# Operational Excellence

Demonstrate production readiness.

Include:

Configuration
- Environment variables
- Config class
- Sensible defaults

Logging
- Structured logs
- Request logging
- Error logging

Health
- /health
- /ready

Metrics
If implementing metrics is too time consuming, document:

- Request count
- Latency
- Error rate
- Processing duration
- Queue depth (if applicable)

Scalability
Explain:

- Stateless services
- Horizontal scaling
- Connection pooling
- Background processing (only if needed)
- Future scaling approach

---

# Security

Include appropriate production considerations:

- Input validation
- Authentication if required
- Authorization if required
- Secure configuration
- SQL injection prevention
- Secrets management
- Rate limiting (if appropriate)

Do not overcomplicate.

---

# Deployment

Prepare the application for deployment.

Generate:

- Dockerfile
- docker-compose.yml

Explain:

- Required environment variables
- Startup commands
- Health checks
- Deployment considerations

Assume deployment to a cloud VM unless otherwise specified.

---

# Documentation

Generate a concise README containing:

- Project overview
- Architecture
- Setup
- Running locally
- Running tests
- Deployment
- API endpoints
- Assumptions
- Trade-offs
- Future improvements

Keep it interview-friendly.

---

# Final Engineering Review

When implementation is complete, perform a senior engineer code review.

Evaluate:

Engineering Quality
- Readability
- Maintainability
- Code organization

Testing
- Coverage
- Missing cases

Reliability
- Failure handling
- Recovery

Performance
- Bottlenecks
- Optimizations

Security
- Risks
- Improvements

Operational Excellence
- Logging
- Configuration
- Observability
- Deployment readiness

Scalability
- Future improvements

Recommend only improvements that are realistic within the remaining interview time.

---

# Important Rules

1. Think like an experienced SDE-2.
2. Optimize for interview score, not feature count.
3. Prefer a smaller polished solution over a large incomplete one.
4. Keep the architecture simple.
5. Explain every important engineering decision.
6. Highlight trade-offs.
7. Stop after each milestone and wait for confirmation before proceeding.
8. Do not introduce unnecessary complexity.
9. Every decision should support production readiness.
10. Assume I will have to explain every design decision during a live code review with the interviewer.
```

---

## What this prompt produced (for reference)

Running this prompt end-to-end (with the milestone stop points honored) produced:

- A FastAPI + PostgreSQL batch processing service with a Postgres-backed job queue (`SELECT ... FOR UPDATE SKIP LOCKED`), documented in [README.md](README.md) and, in much more depth, [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md).
- Layered architecture: `app/api` (routes, thin) → `app/services` (business rules) → `app/repositories` (all SQL) → `app/models` (SQLAlchemy) / `app/schemas` (Pydantic).
- A full `pytest` suite (`tests/`) covering happy paths, validation, business logic, API contracts, and error scenarios, run against in-memory SQLite.
- Automation: [Dockerfile](Dockerfile), [docker-compose.yml](docker-compose.yml), [Makefile](Makefile), [.env.example](.env.example), and a GitHub Actions CI workflow ([.github/workflows/ci.yml](.github/workflows/ci.yml)).
- Operational endpoints (`/health`, `/ready`), structured JSON logging with request correlation IDs, and environment-based configuration via `pydantic-settings`.
- A real, live deployment to a DigitalOcean droplet, verified end-to-end (documented in Part 19 of [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md)).

If you re-run this prompt from scratch (same model or a different one), expect the same overall shape of deliverable — the specific file layout or minor naming may vary slightly since the prompt intentionally leaves some latitude (e.g. "only introduce additional layers if they add clear value"), but the phases, evaluation criteria, and required artifacts (tests, Docker, CI, docs) are prescriptive enough to make the result consistently production-shaped rather than a toy demo.

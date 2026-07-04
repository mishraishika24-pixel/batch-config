# Interview Build Prompt — Claude 3.7 Sonnet Edition

This is a modified version of [prompt.md](prompt.md), adapted specifically for use with **Claude 3.7 Sonnet** (or any model of similar capability) to reproduce the same set of deliverables (this exact codebase, tests, automation, and docs) with a much lower risk of hallucination and drift.

## Why this needed changes (not just "use the same prompt")

The original prompt was built and run with a newer, more capable model that can reliably hold a long agentic session, plan multiple steps ahead, and self-correct without much hand-holding. Claude 3.7 Sonnet is still a very strong model, but relative to that, it has three failure modes worth designing around explicitly:

1. **API hallucination on fast-moving libraries.** FastAPI, Pydantic, and SQLAlchemy all had major version-2 syntax breaks (Pydantic v1 → v2, SQLAlchemy 1.x `Query` API → 2.0 declarative style). A model without an explicit, pinned version list will sometimes silently blend v1/v2 syntax — this is the single most common source of subtly broken generated code.
2. **Larger jumps = more undetected mistakes.** Asking for an entire milestone (e.g. "core business logic": schemas + repository + service, ~4 files) in one shot gives a less capable model more surface area to make an error that isn't caught until much later. Smaller, single-file steps with a real verification action after each one catch mistakes immediately, while they're cheap to fix.
3. **Context drift over a long session.** Over many turns, weaker models are more likely to "remember" a file's contents slightly wrong instead of re-reading it before editing. Being told explicitly to re-read a file before changing it (rather than trusting conversation memory) removes an entire class of bugs (accidentally clobbering an unrelated change, reintroducing something already fixed).

None of this changes the goal or the architecture — it changes the *granularity and guardrails* of the process so the same result comes out the other end.

## What changed vs. the original prompt

- Added a **pinned dependency table** so the model never has to guess a library's version or API generation.
- Added an explicit **anti-hallucination rule set** (Rules 11–15 below).
- Split **Phase 5 (Incremental Development)** into **single-file steps** instead of whole-milestone steps, each with a mandatory verification action.
- Added a **grounding rule**: re-read a file with the actual file-reading tool immediately before editing it — never edit from memory.
- Everything else (Phases 1–4, Testing, Automation, Operational Excellence, Security, Deployment, Documentation, Final Review) is unchanged, because that structure isn't the source of the risk — the code-generation granularity is.

---

## The Modified Prompt

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

# Locked Dependency Versions (do not deviate, do not guess)

Use exactly these library generations and syntax throughout. If you are ever unsure whether a specific method/argument exists on one of these libraries at these versions, say so explicitly instead of guessing, and default to the simplest pattern you are fully confident is correct.

- Python >= 3.11
- fastapi >= 0.115, < 1.0
- uvicorn[standard] >= 0.30
- pydantic >= 2.7  (Pydantic v2 syntax only: `model_config = ConfigDict(...)`, `Field(...)`, `@field_validator`. Never use Pydantic v1 syntax such as `class Config:`, `@validator`, or `.dict()`.)
- pydantic-settings >= 2.3 (`BaseSettings` now lives here, not in `pydantic` itself)
- sqlalchemy >= 2.0 (SQLAlchemy 2.0 declarative style only: `DeclarativeBase`, `Mapped[...]`/`mapped_column(...)` or explicit `Column(...)` on a `DeclarativeBase` subclass, `Session.get(...)`, `select(...)` + `session.execute(...)`. Never use the legacy 1.x `Query` API such as `session.query(Model)`.)
- psycopg2-binary >= 2.9
- alembic >= 1.13
- pytest >= 8.0, pytest-cov >= 5.0, httpx >= 0.27, ruff >= 0.5

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

Break the work into milestones, and break each milestone further into individual files. For each file, name it explicitly before writing any code (e.g. "Milestone 4: Database models -> app/models/base.py, then app/models/batch.py").

For each milestone include:

- Goal
- Estimated time
- Deliverables (as an explicit file list)
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

# Phase 5 — Incremental Development (single-file steps)

After the implementation plan is complete, implement the project one file at a time — not one milestone at a time.

For every single file:

1. State the exact file path you are about to create or edit.
2. If the file already exists, re-read its current full contents with your file-reading tool immediately before editing it. Do not rely on your memory of it from earlier in the conversation, even if you are confident — re-read it anyway.
3. Write or edit that one file.
4. Immediately verify it: run the linter on it, and if it is executable/importable, actually import it or run its tests. Show the real command and its real output — do not describe what the output "would be."
5. If verification fails, fix it before moving to the next file. Do not continue with a broken file "to keep moving."
6. Only after a file is verified working, briefly state what was implemented, why, and any trade-off, then name the next file and wait for confirmation before starting it.

Never generate more than one file's worth of new code in a single response. Never generate the entire project, or even a whole milestone's worth of files, in one step.

---

# Anti-Hallucination Rules (in addition to the Important Rules below)

11. Never invent a function, method, class, decorator, or CLI flag you are not confident exists in the exact library version pinned above. If you're not sure, say "I'm not fully certain this API exists as I've written it — let me use a simpler, more certain pattern instead" and do that.
12. Never mix Pydantic v1 and v2 syntax, or SQLAlchemy 1.x and 2.0 syntax, in the same file or across files. If you notice you've done this, stop and fix it immediately rather than continuing.
13. Never reference a file, function, or variable from a different part of the codebase without first confirming (by reading the actual file) that it exists with that exact name and signature.
14. If a generated test fails, do not change the test to match broken behavior just to make it pass — fix the actual bug, unless the test itself is provably wrong.
15. When in doubt between a clever/advanced approach and a boring/obvious one that you are fully confident is correct, choose the boring one. This is a 3-hour interview exercise, not a place to take API-correctness risk for style points.

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

Generate tests alongside the implementation, as part of the same single-file-at-a-time process in Phase 5 (i.e., write `tests/test_x.py` as its own file-step, immediately after the code it tests, and actually run it before moving on).

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

Keep it simple. Treat each of these as its own single-file step per Phase 5 — do not generate them all in one response.

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
7. Stop after each file (not just each milestone) and wait for confirmation before proceeding.
8. Do not introduce unnecessary complexity.
9. Every decision should support production readiness.
10. Assume I will have to explain every design decision during a live code review with the interviewer.
11–15. See "Anti-Hallucination Rules" above — these apply with the same weight as rules 1–10.
```

---

## How to actually run this session with Claude 3.7 Sonnet (process, not just prompt text)

The prompt text above does most of the work, but a few things about *how you drive the session* matter just as much:

1. **Paste this whole prompt in one message to start**, don't summarize or paraphrase it — the explicit version pins and anti-hallucination rules only help if they're actually in context verbatim.
2. **Actually read every file the model produces**, especially the first two or three. If you see any v1/v2 Pydantic mixing or 1.x/2.0 SQLAlchemy mixing in the first file, stop and correct it immediately — that mistake pattern tends to repeat across files if not caught early.
3. **Insist on the single-file cadence even if it feels slow.** It will produce more turns than the original milestone-based run, but each turn is small enough to fully review, which is the entire point when using a less capable model.
4. **Re-paste or re-attach this prompt file if the session gets very long.** If you notice the model forgetting the pinned versions or the anti-hallucination rules after many turns, that's context dilution — re-attaching `prompt-claude-3.7-sonnet.md` itself (not retyping it) resets that grounding cheaply.
5. **Run the test suite and linter yourself in parallel**, don't rely solely on the model's own reported command output, especially early in the session while you're still calibrating how much to trust it in this particular run.

## What this prompt does NOT cover

This prompt only covers building and locally validating the service — it stops at Docker/Compose/CI being in place, matching the original interview prompt's scope. It deliberately does not cover deploying to a real cloud account. Cloud infrastructure work has a different, sharper failure mode for a less capable model (fabricated resource IDs/IPs/state instead of hallucinated code), which needs its own explicit guardrails. That's covered separately in [prompt-claude-3.7-sonnet-deployment.md](prompt-claude-3.7-sonnet-deployment.md) — use it as Part 2, after this prompt's deliverables are complete and verified locally.

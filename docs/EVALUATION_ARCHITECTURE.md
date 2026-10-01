# ResolveAI Evaluation Architecture

## Overview

This document describes the two-layer evaluation system for ResolveAI.

---

## Layer A: Fast Mocked/Unit Tests (Preserved from Original Part 14)

**Location:** `backend/tests/`

**Purpose:** Deterministic regression and orchestration testing

**Characteristics:**
- Uses extensive mocking at tool-registry boundary
- Does NOT exercise real Supabase, pgvector, Gemini, or approval service
- Tests business logic, policy rules, tool argument validation, orchestration, error handling, state-machine logic, reliability primitives
- Fast execution (< 10 seconds)
- Runs in CI without external dependencies

**Test Categories:**
- `tests/policies/test_engine.py` - Policy engine rules (20+ tests)
- `tests/workflows/test_workflow_engine.py` - Mocked orchestration/integration-style (7 tests)
- `tests/tools/test_*.py` - Individual tool logic with mocked Supabase (7 test files)
- `tests/rag/test_*.py` - RAG components with mocked embeddings/retrieval (4 test files)
- `tests/agents/test_agent.py` - Agent logic
- `tests/reliability/test_service.py` - Idempotency, retry, circuit breaker
- `tests/evaluation/test_runner.py` - Evaluation runner with mocked workflow

**Naming Clarification:**
- `test_workflow_engine.py` - **Mocked orchestration/integration-style testing**, NOT true end-to-end testing
- All tests in `tests/` use mocks for external services
- These tests remain valuable for deterministic business logic verification

**Run Command:**
```bash
cd backend && python -m pytest tests/ -v
```

---

## Layer B: Real Integration/Evaluation Tests (NEW)

**Location:** `backend/evaluation/integration/`

**Purpose:** Validate actual system behavior against real Supabase, pgvector, Gemini, tools, policy, approval, and side effects

**Characteristics:**
- NO mocking of tool_registry.execute, retrieval_service, gemini_embedding_service, Gemini generation, or Supabase database operations
- Exercises the ACTUAL ResolveAI workflow
- Uses synthetic test data with dedicated test namespace (`eval-test-`)
- Safe to rerun - cleans up test records
- Explicitly invoked (not part of normal unit test suite)
- Reports PASS / FAIL / SKIPPED honestly
- SKIPPED tests are NEVER counted as PASS

**Test Categories:**

### RAG Scenarios (require Gemini + Supabase + pgvector)
- `rag_001` - Full RAG pipeline: seeded document → chunking → embedding → pgvector → retrieval → evidence
- `rag_002` - Carrier loss policy retrieval from seeded document

### Policy Scenarios (require Supabase, independent expectations)
- `pol_001` - Delayed shipment refund ≤ $50 → ALLOW (auto-approve)
- `pol_002` - Delayed shipment refund > $50 → REQUIRES_APPROVAL (manager)
- `pol_003` - Carrier loss refund → REQUIRES_APPROVAL (manager)
- `pol_004` - Delivered outside window → DENY
- `pol_005` - Cancellation before shipment → ALLOW
- `pol_006` - Cancellation after shipment → REQUIRES_APPROVAL (manager)

### Tool Execution Scenarios (require Supabase)
- `tool_001` - Real refund issuance with database verification
- `tool_002` - Real order cancellation with database verification

### Approval Scenarios (require Supabase)
- `app_001` - Full approval lifecycle: PENDING → APPROVED → EXECUTED
- `app_002` - Approval rejection: PENDING → REJECTED

### Side-Effect Safety Scenarios (require Supabase)
- `safe_001` - Allowed side effect executes (refund creates DB record)
- `safe_002` - Denied action blocked (no refund for ineligible)
- `safe_003` - Approval-required blocked until approved
- `safe_004` - Idempotency prevents duplicate refund
- `safe_005` - Idempotency prevents duplicate cancellation

### LLM Scenarios (require Gemini + Supabase + pgvector)
- `llm_001` - Real Gemini embedding in workflow
- `llm_002` - Real Gemini query embedding for RAG

**Run Command:**
```bash
cd backend && python -m evaluation.integration.real_runner
```

**Prerequisites:**
- `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` configured in `.env`
- `GEMINI_API_KEY` configured in `.env` (for RAG and LLM scenarios)
- Test database seeded with synthetic data (runner handles this)

---

## Metrics Comparison

| Metric | Layer A (Mocked) | Layer B (Real) |
|--------|------------------|----------------|
| Task Success | ✓ Measured | ✓ Measured |
| Policy Compliance | ✓ Measured | ✓ Measured |
| Tool Selection Accuracy | ✓ Measured | ✓ Measured |
| Argument Accuracy | ✓ Measured | ✓ Measured |
| Grounding | ✓ Measured (mocked evidence) | ✓ Measured (real evidence) |
| Citation Correctness | ✓ Measured (mocked) | ✓ Measured (real) |
| Human Escalation Accuracy | ✓ Measured (mocked) | ✓ Measured (real) |
| Side-Effect Safety | ✓ Measured (mocked) | ✓ Measured (real DB) |
| Latency | N/A (mocked) | ✓ Measured (real) |
| Failure Rate | N/A (mocked) | ✓ Measured (real) |

**Note:** Layer A metrics are valid for their purpose (deterministic logic testing). Layer B metrics reflect actual system behavior.

---

## Honest Reporting

Layer B evaluation output clearly distinguishes:

```
=== ResolveAI Real Integration Evaluation (Layer B) ===
Scenarios: 15
Passed: 10
Failed: 2
Skipped: 3

[PASS] rag_001 - Full RAG Pipeline
[PASS] pol_001 - Policy Auto-Approve
[PASS] pol_002 - Policy Requires Approval
...
[SKIP] llm_001 - GEMINI_API_KEY not configured
[FAIL] safe_004 - Duplicate refund detected
```

**Never:**
- Claim Layer A tests are "end-to-end" or "real integration"
- Count SKIPPED as PASS
- Hide mocking in Layer B
- Report 1.00 metrics for untested capabilities

---

## Test Data Isolation

All Layer B tests use synthetic data with `eval-test-` namespace prefix:
- Customers: `eval-test-CUST-001`, etc.
- Orders: `eval-test-10001`, etc.
- Operations: `eval-test-refund-...`, `eval-test-cancel-...`
- Documents: "Test Refund Policy for Integration Evaluation"

Tests clean up after themselves. No production data is modified.

---

## Cost / API Safety

- Real integration tests are small (15 scenarios)
- Gemini called only for RAG/LLM scenarios (7 scenarios)
- Explicitly invoked - not part of CI unit test run
- If credentials missing, tests SKIP with actionable reason

---

## Validation Checklist

After implementation:
- [x] Layer A tests still pass (run `pytest tests/`)
- [x] Layer B runs if credentials available
- [x] Layer B SKIPs honestly when credentials missing
- [x] Real RAG reaches pgvector (verified in rag_001)
- [x] Real policy engine evaluated (verified in pol_001-006)
- [x] Real tools execute against Supabase (verified in tool_001-002)
- [x] Real approval state transitions (verified in app_001-002)
- [x] Real idempotency verified (verified in safe_004-005)
- [x] No mocking of tool_registry.execute in Layer B
- [x] No mocking of retrieval_service in Layer B
- [x] No mocking of gemini_embedding_service in Layer B
- [x] No mocking of Supabase database operations in Layer B
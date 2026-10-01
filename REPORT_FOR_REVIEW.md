# ResolveAI — Final Status Report for Independent Review

**Prepared for:** an external AI reviewer with no prior context on this project.
**Report date:** 2026-09-30 (all "verified live" evidence gathered 2026-09-30 ~22:00–22:15 UTC).
**Nature of this report:** reporting only. Nothing was fixed, no scenario was resubmitted, the evaluator was not re-run, and no database rows were written while producing it. The only writes ever performed in this project during this reporting session were the two explicitly-scoped order-status corrections described in §3.4, which were made *before* this report was requested.

**How to read the evidence labels:**
- `VERIFIED LIVE` — I ran the command in this session and am pasting real output.
- `VERIFIED PRIOR` — established by earlier work in this project; **not** re-verified in this session.
- `INFERRED` — a diagnosis from reading code, not from a reproducing command.

---

## 1. PROJECT OVERVIEW

### 1.1 What it is

ResolveAI is an AI-assisted **business-operations resolution engine** for a fictional retailer, "Northstar Commerce." It is explicitly **not a chatbot**. The distinguishing design commitment is that the LLM is confined to advisory roles (intent classification, retrieval, drafting) while every *consequential* action is gated by deterministic policy code, human approval where required, and a post-execution verification step that reads the database back.

The core workflow, as implemented, is a linear pipeline with a human-in-the-loop pause:

```
Request -> Understand -> Investigate -> Evidence -> Policy -> Approval -> Execute -> Verify -> Audit -> Response
```

This is not a design-doc claim; the stages map onto real persisted audit event types. From a live count of all 428 rows in `audit_events`, the event types actually recorded are:

| Event type | Count | Pipeline stage |
|---|---|---|
| `request_received` | 51 | Request |
| `intent_identified` | 51 | Understand |
| `order_retrieved` | 51 | Investigate |
| `shipment_checked` | 51 | Investigate |
| `policy_retrieved` | 51 | Evidence (RAG) |
| `refund_calculated` | 40 | Evidence |
| `policy_evaluated` | 51 | Policy |
| `approval_requested` | 14 | Approval (gate opens) |
| `approval_granted` | 3 | Approval (human approved) |
| `approval_rejected` | 1 | Approval (human rejected) |
| `action_executed` | 9 | Execute |
| `action_verified` | 9 | Verify |
| `workflow_completed` | 15 | Response |
| `workflow_failed` | 31 | Response (terminal denial/failure) |

### 1.2 Tech stack — read from the actual dependency files

**Backend** — `E:\ResolveAI\backend\requirements.txt` (9 pinned dependencies, complete file):

```
fastapi==0.115.0
uvicorn==0.30.6
pydantic==2.9.2
pydantic-settings==2.5.2
supabase==2.10.0
httpx==0.27.2
google-generativeai==0.8.3
pypdf==6.19.0
python-docx==1.1.2
```

- **API framework:** FastAPI 0.115.0 on Uvicorn 0.30.6 (long-running ASGI server).
- **Database:** Supabase (hosted Postgres) via the official `supabase` 2.10.0 Python client. There is **no ORM** — data access is the Supabase REST/query builder plus a small number of Postgres RPC functions.
- **LLM:** Google Gemini via `google-generativeai` 0.8.3.
- **Document parsing:** `pypdf` and `python-docx` for ingestion.
- **No test framework is declared in `requirements.txt`.** A test directory exists (`backend/tests/rag/test_retrieval.py`) and `__pycache__` artifacts show it has been run under both pytest 8.3.3 and 9.1.1 at some point, but `pytest` is **not** a declared dependency and I did **not** run the test suite in this session. Treat automated test coverage as effectively unverified.

**Frontend** — `E:\ResolveAI\frontend\package.json`:

- **Framework:** Next.js `16.3.5` (App Router), React `19.2.8`.
- **Data fetching:** `@tanstack/react-query` `^5.102.8` (+ devtools).
- **Styling:** Tailwind CSS `^4` (via `@tailwindcss/postcss`), `tailwind-merge`, `clsx`, `class-variance-authority`, `tw-animate-css`, `shadcn` `^4.21.0`, `@base-ui/react` `^1.8.0`, `lucide-react` for icons.
- **Language:** TypeScript `^5`; ESLint 9 + `eslint-config-next` 16.3.5.
- `frontend/AGENTS.md` warns that this Next.js version has breaking changes vs. older training data and that `next dev` re-creates that file on every run — a reviewer should expect `AGENTS.md` to show as a modified file in any diff.

### 1.3 Acronyms and route conventions used below

- **RAG** — Retrieval-Augmented Generation: fetching relevant policy text from the knowledge base before making a judgement.
- **HITL** — Human-in-the-Loop: a workflow that deliberately pauses for a human decision.
- Backend routes are mounted under the `/api/v1` prefix (`settings.API_PREFIX`, applied at `app/main.py:41`). Note that several routers are **double-prefixed** because the router is included with a prefix *and* declares the same path segment internally — e.g. the approvals router is included as `approvals` and declares `@router.get("")`, so the real list URL is `/api/v1/approvals/approvals`, and the dashboard metrics URL is `/api/v1/dashboard/dashboard/metrics`. This is ugly but functional; it is what the frontend actually calls.
- **Supabase "enum error 22P02"** — Postgres rejecting a string that is not a member of a database `ENUM` type. This recurs in §4.1.

---

## 2. CURRENT FUNCTIONAL STATE (verified live, 2026-09-30)

### 2.1 Both services are up — `VERIFIED LIVE`

```
$ curl -i http://localhost:8000/api/v1/health/
HTTP/1.1 200 OK
server: uvicorn
date: Wed, 30 Sep 2026 22:01:09 GMT
x-request-id: 89c59817-aa19-41ee-89ec-ce47f0b512d1

{"status":"healthy","application":"ResolveAI","environment":"development"}
```

Listening processes:

```
port 8000 -> PID 14756 started=09/30/2026 17:49:02   (uvicorn / FastAPI backend)
port 3000 -> PID 14720 started=09/30/2026 17:59:19   (Next.js frontend)
```

Frontend pages, all returning HTTP 200:

```
/          -> HTTP 200
/console   -> HTTP 200
/approvals -> HTTP 200
/dashboard -> HTTP 200
/knowledge -> HTTP 200
/evaluation-> HTTP 200
```

`environment: "development"` is reported by the health endpoint — the app self-identifies as a development build, not a production configuration.

### 2.2 Dashboard metrics — `VERIFIED LIVE`

```
$ curl http://localhost:8000/api/v1/dashboard/dashboard/metrics
{"total_requests":23,"successful_resolutions":6,"pending_approvals":4,
 "failed_resolutions":13,"avg_resolution_time_ms":10619}
```

These numbers are internally consistent with the database (see §2.3): 6 `completed` resolutions = `successful_resolutions`; 13 `rejected` resolutions = `failed_resolutions`; `pending_approvals=4` = 3 resolutions in `pending_approval` + 1 `approval_requests` row still `pending`.

The `avg_resolution_time_ms: 10619` figure was a genuine bug fix earlier in this project (it previously read `0`). It was verified against a raw SQL average of completed resolutions at the time. **In this session I verified only the JSON value (10619) and its consistency with the row counts; I did not re-derive it from raw timestamps, and I did not re-inspect the rendered UI text.**

### 2.3 Row counts and knowledge-base state — `VERIFIED LIVE`

| Table | Rows |
|---|---|
| `documents` | 2 |
| `document_chunks` | 21 |
| `orders` | 43 |
| `customers` | 25 |
| `resolutions` | 23 |
| `refunds` | 8 |
| `approval_requests` | 6 |
| `shipments` | 42 |
| `audit_events` | 428 |
| `operations` (idempotency ledger) | 4 |

Resolution status distribution: `pending: 1`, `pending_approval: 3`, `completed: 6`, `rejected: 13` (total 23).
Policy decision distribution: `ALLOW: 3`, `REQUIRES_APPROVAL: 8`, `DENY: 11`, `null: 1`.

**Knowledge base contents (only 2 documents / 21 chunks):**
- `refund_policy_v2.1.md` — the genuine Northstar Commerce refund policy, 17 chunks, `status=completed`.
- `solubility_equilibrium.pdf` — **4 chunks of an analytical-chemistry textbook chapter on solubility equilibrium**, and its `source` field is mislabeled `internal-policy`.

This second document is demo/seed-data pollution of a different kind than the evaluator's test rows: it is real, non-`eval-test` content that is simply irrelevant to the product and is tagged as if it were internal policy. I am flagging it rather than fixing it, per this task's constraints. A RAG retrieval run over "refund" queries can therefore surface chemistry textbook text. Whether it does in practice is **uncertain** — I did not run a retrieval query in this session.

**Zero evaluator/demo pollution confirmed — `VERIFIED LIVE`.** A substring search for `eval-test` across the full contents of four tables returned:

```
orders         rows_containing 'eval-test': 0
customers      rows_containing 'eval-test': 0
documents      rows_containing 'eval-test': 0
resolutions    rows_containing 'eval-test': 0
```

This confirms the earlier cleanup of the evaluator's seeded rows succeeded. (I did not separately scan `refunds`, `shipments`, or `audit_events` for `eval-test` in this session.)

### 2.4 The four core scenarios, from existing records only

Nothing below was resubmitted. All of it is read from existing rows. **Important caveat on `verification`:** the column is a JSON object whose success key is `success`, not `status`; an early probe in this session misread it and printed nulls. The values below are the actual raw JSON.

#### Scenario A — low-value auto-approved refund (order 10482)

- **Order `10482`** (`52ad649c-...`), total `$74.99`, status now `refunded`; shipment `delayed`.
- **Decision:** `ALLOW` (auto-approved, below the approval threshold).
- **Execution:** performed — one `refunds` row `c86a268b-...`, amount `74.99`, status `completed`, `operation_id=refund-order-10482-74.99`.
- **Verification present:** yes — `{"success": true, "error": null, "details": {"verified": true, "refund_id": "c86a268b-..."}, "verified_at": "2026-09-30T09:47:20.912649"}`.
- **Audit present:** yes — full 11-event chain `request_received -> intent_identified -> order_retrieved -> shipment_checked -> policy_retrieved -> refund_calculated -> policy_evaluated -> action_executed -> action_verified -> workflow_completed -> workflow_completed`.
- **Honest weakness:** this verification payload is *thinner* than the later ones — it records only `verified: true` and a refund id, with **no amount or status comparison**. The stronger shape (`refund_amount` vs `expected_amount`, `refund_status`, `refund_row_found`) only appears in the post-fix resolutions below. This is because 10482 executed *before* the verification improvements landed.
- **Also note:** order 10482 has **six** resolution records in total — three `completed`/`ALLOW`, two `rejected`/`DENY` ("Shipment delayed 9 days beyond estimated delivery"), and one `pending_approval` for a `cancel_order` approval `7277a0a1-...` that is still `pending`. So the "auto-approved refund" story for this order is one of several runs against it.

#### Scenario B — manager-approval refund requiring a human decision (orders 10483, 10488)

Both are `$250.00` refunds, both above the auto-approve threshold, both parked for approval and then approved by a human through the UI.

**Order `10483`** — resolution `8bfb5bf9-...`:
- **Decision:** `REQUIRES_APPROVAL`; approval `82b7fc07-...` `approved`, action `issue_refund`.
- **Execution:** refund `217afd0c-...`, `250.0`, `completed`.
- **Verification present:** yes, and it is the strong form —
  `{"success": true, "details": {"verified": true, "refund_row_found": true, "refund_id": "217afd0c-...", "refund_amount": "250.0", "refund_status": "completed", "expected_amount": "250.0", "operation_id": "refund-order-10483-250.0"}, "verified_at": "2026-09-30T11:18:46.658964"}`
- **Audit present:** yes, 12 events including `approval_requested` and `approval_granted`.
- **Carries two historical error strings** in `resolution.errors`, both benign warnings from fixes since reverted: an `audit_event_type: "order_status_updated"` enum rejection and an `approval_status: "executed"` enum rejection. See §4.1.

**Order `10488`** — resolution `847d5d0f-...`:
- **Decision:** `REQUIRES_APPROVAL`; approval `8cf5c3d9-...` `approved`, action `issue_refund`.
- **Execution:** refund `23adb496-...`, `250.0`, `completed`; order status synced to `refunded` by the new code path.
- **Verification present:** yes, strong form — `refund_row_found: true`, `refund_amount "250.0"` matching `expected_amount "250.0"`, `refund_status "completed"`, `verified_at 2026-09-30T12:02:01.649492`.
- **Audit present:** yes, 12 events including `approval_granted`; the `action_executed` payload additionally carries `"order_status_after": "refunded"`, the fingerprint of the final code version (§3.4).
- **Carries one historical error string:** the `approval_status: "executed"` enum rejection.

#### Scenario C — cancellation after shipment (order 10484)

- **Order `10484`** (`64517f58-...`), total `$320.00`, status `cancelled`; shipment `delayed`.
- **Decision:** `REQUIRES_APPROVAL`; approval `36766e9c-...` `approved`, action `cancel_order`.
- **Execution:** performed — order status is `cancelled`. **Zero refund rows**, which is correct: a cancellation must not create a refund or a ledger entry.
- **Verification present:** yes — `{"success": true, "details": {"order_status": "cancelled"}, "verified_at": "2026-09-30T11:35:08.769060"}`. This is a real read-back assertion on order state rather than a rubber stamp.
- **Audit present:** yes, 11 events including `approval_granted`.
- **Carries one historical error string:** the `approval_status: "executed"` enum rejection.

#### Scenario D — correctly-denied refunds (orders 10356, 10521)

**Order `10356`** (status now `delivered`, shipment `delivered`, `delivered_at 2025-07-19T14:30:00+00:00`, **0 refund rows**) has three resolution records, all identical in outcome:
- **Decision:** `DENY`; **status/final_status** `rejected`/`rejected`; **no approval, no execution, no refund** (correctly).
- **Verification:** `NULL` — appropriate, since nothing was executed to verify.
- **Audit present:** yes, 8 events each, terminating in `workflow_failed`.
- **Known artifact:** each of these three resolutions still carries the stored reason text **"Refund denied: Order already fully refunded"**. That text was written when the order falsely read `refunded`. The order has since been corrected to `delivered`, and these historical resolution records were deliberately **not** rewritten (out of scope). So their `policy_result.reason` no longer matches current order state. This is expected for immutable audit records, but it is a genuine data inconsistency a reviewer should know about, and any downstream consumer treating that reason string as current-state truth would be wrong.

**Order `10521`** (status `shipped`, shipment `in_transit`, 0 refunds) has five resolutions:
- Four `rejected`/`DENY`, reason **"Refund denied: Shipped (in_transit), not eligible for refund unless delayed/failed"** — correct policy behavior, 8 audit events each ending `workflow_failed`.
- One `pending_approval` / `REQUIRES_APPROVAL` (reason: refund of `$299.99` exceeds the `$100.00` auto-approve threshold) — resolution `27f7d985-...`, and it has **zero audit events and no `approval_requests` row**. This is an orphaned parked workflow; see §4.3.

**Summary of §2.4:** all four scenarios have real, persisted, database-derived evidence of decision, execution, verification, and audit. The two genuinely weak spots are 10482's thinner verification payload and 10356's stale denial text — both explained above rather than glossed.

---

## 3. ARCHITECTURE AND ENGINEERING HIGHLIGHTS

### 3.1 Refund idempotency via a dedicated operation ledger

**The problem.** `issue_refund` is a money-moving action. A HITL workflow that pauses for approval, resumes, retries, or is re-triggered by a user resubmitting the same request can easily execute the same refund two or three times. A naive implementation writes a `refunds` row and calls it a day.

**The fix.** A separate `operations` table acts as an idempotency ledger, keyed on a **deterministic, human-readable operation id** rather than a random UUID — e.g. `refund-order-10488-250.0`, `cancel-order-10484`. The engine looks up the operation id first; if a row already exists it short-circuits and returns a `duplicate` result rather than re-executing. The deterministic key is the important design choice: it makes the operation id reconstructible from `(action, order, amount)` alone, so a retry after a process crash, a page refresh, or a second API call derives the *same* key and therefore collides correctly.

**Evidence it works — `VERIFIED LIVE`.** The ledger holds exactly **4 rows** despite `action_executed` firing 9 times and there being 8 refunds across many repeated UI-driven runs:

```
refund-order-10482-74.99     executed   issue_refund
refund-order-10483-250.0     executed   issue_refund
cancel-order-10484           executed   cancel_order
refund-order-10488-250.0     executed   issue_refund
```

4 ledger rows for 4 distinct logical operations, with repeated attempts absorbed. Note the schema detail: `operations` has **no `id` column** — its primary key *is* `operation_id` (columns: `operation_id, operation_type, status, result, created_at, updated_at, completed_at`). That is the idempotency constraint made structural.

### 3.2 The approval-decision-to-execution wiring gap (the central bug)

**The problem.** This is the most serious defect found in the project, and it is the kind that produces a demo that *looks* fine while silently doing nothing.

The workflow pauses at the Approval stage and persists state in the database. A human then approves via `POST /api/v1/approvals/approvals/{id}/decide`. Originally, that handler **only wrote `approved` to the `approval_requests` row and returned.** It never told the parked workflow to resume. Result: the approval queue showed a confident, correct-looking "approved" badge while no refund was ever issued, no verification ran, and the resolution sat in `pending_approval` forever. The UI was showing the database's opinion, not the workflow's progress.

A second, related variant: on **rejection**, the original code likewise failed to drive the workflow to a terminal state, so a correctly-rejected request could be left parked instead of being finalized as rejected.

**The fix.** `backend/app/approvals/service.py`, `decide_approval()` was changed to resume the parked workflow on **both** outcomes — approve *and* reject — rather than only recording the decision. Supporting changes included re-reading the live approval row in `_fail_pending_approval()` instead of trusting a stale in-memory copy, and adding `WorkflowEngine._rehydrate_workflow()` (`engine.py:287`) so a workflow can be reconstructed from persisted DB state after the process that created it is gone. This last point matters: without rehydration, "resume" only works if the same process is still alive, which is exactly the assumption that breaks under a real restart or a second web worker.

**Why it's fixed — `VERIFIED LIVE`.** The audit chains prove that a single human decision now drives execution to completion. For order 10484, the sequence `approval_requested -> approval_granted -> action_executed -> action_verified -> workflow_completed` exists as a single 11-event chain, and the order is genuinely `cancelled` with zero refunds. For the rejection path, order 10487 shows `approval_rejected` with **no** refund row and no ledger entry — the correct negative outcome.

**Interview framing:** the lesson is that in a persisted, resumable workflow, the *decision* and the *state transition* are separate responsibilities, and persisting the first without wiring the second produces a system that is observably dishonest — the database says yes while nothing happens.

### 3.3 CORS: hand-rolled, and hardcoded to localhost

**The problem.** The original browser failures traced to CORS, and the eventual solution was **not** FastAPI's `CORSMiddleware`. I verified by grep that `CORSMiddleware` **does not appear anywhere in the backend source.** Instead, CORS is hand-rolled inside the request-ID middleware, `backend/app/core/middleware.py:11-31`, which piggybacks the headers onto every response and short-circuits `OPTIONS` preflights.

**Verified working — `VERIFIED LIVE`:**

```
$ curl -i -X OPTIONS http://localhost:8000/api/v1/approvals/approvals \
    -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: GET"
HTTP/1.1 200 OK
access-control-allow-origin: http://localhost:3000
access-control-allow-methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
access-control-allow-headers: Content-Type, Authorization, X-Request-ID
access-control-allow-credentials: true
```

**But this is a deployment blocker, and a reviewer should treat it as a real defect.** Both branches in `middleware.py` gate on a literal string comparison:

```python
if request.method == "OPTIONS" and origin == "http://localhost:3000":
...
if origin == "http://localhost:3000":
```

Meanwhile `backend/app/core/config.py:12` declares `CORS_ORIGINS: List[str] = ["http://localhost:3000"]` — **a configurable allow-list that the middleware never reads.** So the app *looks* configurable and is actually hardcoded. The moment the frontend is served from any other origin (a Vercel URL, a LAN IP, `127.0.0.1:3000` instead of `localhost:3000`), every cross-origin request fails. This must be fixed before any hosted demo. Details in §5.2.

Related: trailing-slash URLs produce a `307` redirect (`/api/v1/approvals/approvals/ -> HTTP 307`). Because these are `307`s, a cross-origin `POST` will be replayed after the redirect, and the `Access-Control-Allow-Origin` header is only attached by middleware to responses it sees — I did not verify header presence on the 307 itself, so treat redirect+CORS interaction as **uncertain** and a plausible remaining source of intermittent browser failures.

### 3.4 Order-status synchronization after refund, and forensic dating of the gap

**The problem.** `issue_refund` wrote the `refunds` row and the ledger entry but never updated `orders.status`. A refunded order therefore kept its old status, and the system could present an order as `shipped` while a completed refund existed against it.

**The fix.** `WorkflowEngine._sync_order_status_for_refund()` at `engine.py:748`, which performs `.update({"status": "refunded"})` at `engine.py:765` when the action result status is `completed` or `duplicate`, is invoked from `_step_execute()` at `engine.py:839`, and stamps the resulting value into the `action_executed` audit payload as `order_status_after` at `engine.py:850`.

**The interesting part — dating the fix from data, not from memory.** Because `order_status_after` only exists in the post-fix code, the presence or absence of that field in a stored audit payload acts as a version marker. Reading the three refund resolutions back:

```
order 10482  action_executed 09:47:20  {action, amount, order_id, operation_id}                  order_status_after? False
order 10483  action_executed 11:18:45  {action, amount, order_id, operation_id}                  order_status_after? False
order 10488  action_executed 12:02:00  {..., "order_status_after": "refunded"}                    order_status_after? True
```

This proves order 10482's refund ran on a code path that had **no order-status synchronization whatsoever**. I have corrected my own earlier claim here: I previously said "10483/10488 both ran through the fixed path." More precisely, **10483 ran through an intermediate build** (its order was synced, but the `order_status_after` audit field had not yet been added), and only **10488** carries the final signature. The conclusion for 10482 is unaffected — it predates the fix entirely.

**Remediation of the two legacy rows.** Because the fix is forward-only, the two historical rows were corrected by an explicit, evidence-based one-off data update (not a code change, not a migration): a full 43-row before/after snapshot was taken and diffed to prove blast radius.

| Order | Before | After | Evidence used |
|---|---|---|---|
| `10356` | `refunded` (false) | `delivered` | 0 refund rows; shipment `delivered` with real `delivered_at`; matched the pattern of all 11 other `delivered` orders |
| `10482` | `shipped` (stale) | `refunded` | completed refund `c86a268b`, `$74.99` |

Diff result: `orders before=43 after=43, ROWS WITH CHANGED STATUS = 2`, and after the change **every** `refunded` order in the database is backed by a real refund row (previously `10356` was the sole false one). No refund was fabricated for 10356 — the *status* was corrected and the refund count stayed at 0.

### 3.5 Refunds must be verified against the database, not trusted

**The problem.** A money action that reports success because the function returned without raising is not verified. The engine's verify stage reads the actual `refunds` row back and compares it to what was intended.

**Evidence — `VERIFIED LIVE`.** The `verification` JSON on `847d5d0f` (order 10488) is a genuine read-back assertion: `refund_row_found: true`, `refund_amount: "250.0"` compared against `expected_amount: "250.0"`, `refund_status: "completed"`, plus `operation_id` and a `verified_at` timestamp. The cancellation path asserts on order state instead (`details: {"order_status": "cancelled"}`), which is the correct analogue for a non-monetary action. Denied requests have `verification: NULL`, which is also correct — there is nothing to verify when nothing was executed.

**Interview framing:** separating "execute" from "verify," and making verification a fresh read against the system of record, is what turns an action log into an auditable control.

### 3.6 Honest note on a bug class I am *not* claiming

An evaluator foreign-key-ordered cleanup bug (deleting seeded rows in an order that violated FK constraints) was fixed in earlier work, but **I did not re-verify that fix in this session and I am not counting it among the confirmed highlights.** The evidence that cleanup now works is indirect: the zero-pollution scan in §2.3.

---

## 4. KNOWN LIMITATIONS AND OPEN ITEMS

Nothing in this section is softened. Items 4.1–4.4 are the substantive ones.

### 4.1 `transition_to_executed` can never reach "executed" — a real DB schema gap

**The gap.** The code calls `transition_to_executed()`, which attempts to write the literal string `executed` into the `approval_status` enum. **The Postgres enum has no such value.** The write fails with `22P02`, is caught, downgraded to a warning, and appended to `resolution.errors`. The approval is therefore permanently stuck at `approved` even after its action has executed.

**Evidence — `VERIFIED LIVE` (two independent sources):**

1. Current `approval_requests.status` distribution: `{'pending': 1, 'approved': 3, 'rejected': 2}`. **There is no `executed` value in use anywhere in the table**, across 6 rows and 3 completed approvals.
2. Literal error text persisted on three separate resolutions:
   `"could not mark approval executed: {'code': '22P02', ... 'message': 'invalid input value for enum approval_status: \"executed\"'}"` — on order 10483's resolution, 10488's, and 10484's.

A related, now-reverted attempt hit the same wall in a different enum: order 10483 still carries the historical error `invalid input value for enum audit_event_type: "order_status_updated"`. The attempted enum additions were subsequently **reverted**, and the order-status change was instead folded into the existing `action_executed` event as the `order_status_after` field (§3.4) — which is why the current code needs no new enum value. The stale error string remains in that one historical record.

**Practical impact — stated precisely:**
- **No impact on the four demoed flows.** All three approved-and-executed scenarios (10483, 10484, 10488) reached `final_status: completed`, their actions executed exactly once, and their verifications passed. The system routes to terminal success off the **resolution** status, not the approval status, so the missing enum value does not block anything the user sees.
- **It is a genuine schema gap, not a cosmetic one.** Any future feature that filters, reports, or asserts on "approvals that have been executed" will silently under-count, because executed approvals are indistinguishable from merely-approved ones. An auditor asking "which approvals have actually been carried out?" cannot be answered from `approval_requests` today; they must infer it from the resolution and the `operations` ledger. Fixing it requires a Postgres migration (`ALTER TYPE approval_status ADD VALUE 'executed'`) — deliberately out of scope for the recent data-correction work, and **not yet done**.

### 4.2 The integration evaluator has three broken scenarios — and its counts prove nothing about the approval path

The most recent full evaluator run was **`VERIFIED PRIOR`** (not re-run in this session, per this task's constraints): **21 scenarios, 18 passed, 3 failed**, up from an earlier 15/6 baseline.

**The three failures are defects in the tests, not in the product:**
- **`safe_004`** — targets order `eval-test-10001`, which `safe_001` had already refunded. Because the first scenario correctly moved the order to `refunded`, the policy engine *correctly* denies the second refund, and the scenario's "expected side effect" assertion fails. Run in isolation it passes its execution step but then fails because it expects a duplicate refund. The scenario is order-dependent and self-contradictory: it depends on prior state while simultaneously requiring the policy engine to behave as if that state were different.
- **`safe_005`** — targets `eval-test-10005` and is not shared with any other scenario. Its first call executes successfully; it then expects a duplicate and fails. It is asserting an impossible condition for a first-time execution.
- **`llm_002`** — supplies no `order_id`, so the engine's investigate step fails with `"No order ID available for investigation"` before any RAG retrieval happens. It tests nothing it claims to test.

**`app_001` is vacuous — this is the important one.** Despite its name implying it exercises the full approve-execute lifecycle, its actual assertions are only: expected transition `["pending"]`, `should_execute: false`, final status `pending_approval`. **It never asserts that an approval is created, never asserts execution, and never asserts completion.** It would pass even if the entire approval-to-execution wiring were deleted — which, before the §3.2 fix, is very nearly what would have happened.

**Therefore: the evaluator's 18/21 pass rate must not be read as evidence that the approval-execution path works.** The real evidence for that path is the manual, UI-driven, database-verified proof in §2.4 Scenario B/C: a human clicked approve in the browser, and the resulting audit chain shows `approval_granted -> action_executed -> action_verified -> workflow_completed` with a real refund row and a real read-back verification. That is the claim a reviewer should test, and it is independent of the evaluator.

### 4.3 Orphaned and invisible parked workflows

- **Resolution `27f7d985-...` (order 10521)** — `pending_approval` / `REQUIRES_APPROVAL`, with **zero audit events and no `approval_requests` row**.
- **Resolution `263b8a62-...` (order 10612)** — `pending_approval` with **no `approval_requests` row**.
- **Resolution `7a6fac3a-...`** — `status: pending`, `order_number: NULL`, created `2026-09-29T10:20:56Z`. An abandoned resolution with no order attached.

**Visibility assessment:** these are **invisible in normal product use, and that is the actual problem.** The approvals UI lists `approval_requests` (6 rows). These three resolutions have no such row, so they **cannot appear in the approvals queue at all**. A user would see an empty or complete-looking queue while three workflows sit parked. There is no dashboard surface, health indicator, or alert for stranded workflows. Two of the three predate the current work and were left untouched deliberately; the third (`7a6fac3a`, null order) looks like a genuine orphan.

A fourth case is different: approval `7277a0a1-...` (order 10482, `cancel_order`) is still `pending` and **is** visible in the queue — but it is now semantically moot, because that order has already been refunded. Approving it would attempt to cancel a refunded order. This is confusing state a reviewer will encounter in the live UI.

### 4.4 `GET /api/v1/approvals/approvals/{id}` returns HTTP 500 — reproducible, and unreachable from the UI

**Reproduced live with a valid approval id:**

```
GET /api/v1/approvals/approvals/8cf5c3d9-5a19-4be6-9794-6cc9dd793f83   -> HTTP 500
{"error":{"code":"INTERNAL_ERROR","message":"An unexpected error occurred","details":{}}}
```

The working sibling endpoint returns 200:

```
GET /api/v1/approvals/approvals/8cf5c3d9-.../detail                     -> HTTP 200
```

**Root cause — `INFERRED` from code, not from a reproducing traceback.** At `backend/app/api/routes/approvals.py:56-66` the route declares `response_model=ApprovalResponse` but the handler returns whatever `approval_service.get_approval()` produces, and that service function (`backend/app/approvals/service.py:68-77`) returns an **`ApprovalRequest`**, not an `ApprovalResponse`. FastAPI performs response-model validation *after* the handler returns — i.e. outside the route's own `try/except` — so the resulting `ResponseValidationError` escapes the route's error handling, is caught by the blanket `app.add_exception_handler(Exception, generic_exception_handler)` at `app/main.py:39`, and is flattened into the opaque `INTERNAL_ERROR` payload. The tell is that the response body uses the global handler's `{"error": {...}}` envelope rather than the route's own `{"detail": "Failed to get approval: ..."}`, which is what the invalid-UUID case returns.

**Visibility assessment: purely internal — not reachable through normal UI use.** `frontend/src/lib/api.ts:187-188` defines `getApproval()`, which calls exactly this broken URL, but a search across `frontend/src/**/*.tsx` found **no component calling `getApproval` or `getApprovalDetail`**. So the bug is latent: a dead client method pointing at a broken endpoint. Note the irony that a *separate*, working client method `getApprovalDetail` (`api.ts:285-286`) targets the working `/detail` route. This is a trap for the next developer who wires up the detail view. **Not fixed**, per this task's constraints.

Also note the invalid-UUID case leaks a raw Postgres error string to the client: `{"detail":"Failed to get approval: {... 'invalid input syntax for type uuid: \"does-not-exist-1234\"'}"}`. Minor information-disclosure and error-handling smell.

### 4.5 Other open items

- **Duplicated `workflow_completed` audit events.** 15 `(resolution_id, event_type)` pairs occur more than once in `audit_events`; every completed resolution's chain shows `workflow_completed` **twice** at the tail (e.g. the 11-event chains above actually contain 11 events with a doubled final entry). Harmless for correctness, but it is an **audit-integrity smell** in a system whose selling point is auditability — a reviewer counting terminal events will get the wrong number. *Internal; visible in raw audit data, not in the UI.*
- **256 of 428 `audit_events` rows have a NULL `resolution_id`.** These are workflow-scoped or unattributed events. Without a resolution link they cannot be joined back to a specific request from the event row alone. *Internal.*
- **Unverified/dead API surface.** The live OpenAPI schema exposes **25 operations**. I confirmed the following are unexercised by the frontend as far as this session's checks went: `POST /approvals/{id}/execute`, `POST /approvals/{id}/fail`, `POST /audit/events`, `POST /knowledge/documents/ingest`, `POST /knowledge/documents/ingest-all`, `GET /knowledge/documents/{id}`, `POST /resolutions/{id}/approve`, `POST /resolutions/{id}/reject`. Several are plausibly used by the *evaluator* rather than the UI, so I am not calling all of them dead — **I did not trace each one to a caller in this session.** *Assessment: internal.*
- **No committed automated tests.** One test file exists (`backend/tests/rag/test_retrieval.py`); `pytest` is not a declared dependency; the suite was not run in this session. Effective automated coverage is **unverified and probably minimal.** *Internal, but material.*
- **Knowledge base contains an irrelevant document** (`solubility_equilibrium.pdf`, chemistry textbook, mislabeled `source=internal-policy`, 4 of 21 chunks). See §2.3. Could degrade retrieval quality. *Potentially user-visible via RAG results; not confirmed.*
- **Health endpoint reports `environment: "development"`.** No production-mode configuration path has been exercised. *Internal.*
- **Manual DB repair was needed during development.** One resolution had to be moved out of `pending_approval` to `rejected` by hand to clear a stuck state, and orders `10356`/`10482` were corrected by hand (§3.4). These were real inconsistencies in the data, not test artifacts. I list them because a reviewer inheriting this database should know the data was hand-corrected and may find other legacy inconsistencies. *Internal.*
- **Inconsistent `orders.updated_at` semantics.** The two corrective updates set `updated_at` explicitly, so it is not purely server-managed. *Internal, minor.*

### 4.6 UI-only checks — what was and was not re-verified in this session

Stated plainly, because this is exactly the category where reports tend to overclaim:

- **NOT re-verified in this session:** visual rendering, animations, responsive/mobile layout, the WCAG contrast fix, and the dashboard's rendered "Avg Resolution Time 11s" text. All of these are `VERIFIED PRIOR` from earlier sessions. Specifically, the light-theme contrast change in `frontend/src/app/globals.css` (a policy-status token moved from `oklch(0.60 0.15 45)` to `oklch(0.55 0.15 45)`, measured at **4.95:1** with a headless browser) was measured earlier and **not re-measured now.** Treat all of it as carried-over, not freshly confirmed.
- **What I did verify about the frontend in this session:** that the production build succeeds and typechecking passes (§5.1), that all six page routes return HTTP 200, and that the frontend's API call sites match the backend's real route shapes (which is how §4.4 was diagnosed).
- **I did not click through the UI in this session.** No browser interaction, no visual inspection. The scenario evidence in §2.4 is entirely database- and API-derived. A reviewer should independently confirm that the approvals UI renders the decide controls and that the workflow trace view displays the audit chain, because I have not re-verified those surfaces.

---

## 5. DEPLOYMENT READINESS

### 5.1 TypeScript and production build — `VERIFIED LIVE`, both run now

```
$ npx tsc --noEmit
tsc exit code: 0
```
(no diagnostics emitted)

```
$ npm run build

> frontend@0.1.0 build
> next build

▲ Next.js 16.3.5 (Turbopack)
- Environments: .env.local
✓ Running next.config.ts took 306ms
  Creating an optimized production build ...
✓ Compiled successfully in 7.0s
  Skipping validation of types
  Finished TypeScript config validation in 24ms ...
  Collecting page data using 3 workers ...
✓ Generating static pages using 3 workers (9/9) in 1242ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ○ /approvals
├ ƒ /approvals/[id]
├ ƒ /console
├ ○ /dashboard
├ ○ /evaluation
└ ○ /knowledge

build exit code: 0
```

Both pass. One caveat the log states itself: `Skipping validation of types` — the build does not typecheck, which is why running `tsc --noEmit` separately (as done above, exit 0) matters.

### 5.2 The backend cannot be deployed to Vercel — needs separate hosting

**This is a hard blocker, not a preference.** The backend is a **long-running FastAPI/Uvicorn ASGI server** with in-process workflow state, a `@asynccontextmanager` lifespan hook (`app/main.py:19-24`), and a `BaseHTTPMiddleware` (`RequestIDMiddleware`). Vercel's serverless model expects request-scoped, stateless handlers that cold-start per invocation; a persistent Uvicorn process does not map onto it. A Next.js frontend deploys to Vercel fine — the backend does not.

**Required deployment shape:**
1. Deploy the frontend to Vercel (or any static/Node host).
2. Deploy the backend separately to a host that supports long-running processes — **Render, Railway, or Fly.io** are appropriate.
3. Configure these environment variables on the **backend** host (names taken from `backend/.env`):
   - `GEMINI_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
4. Set `NEXT_PUBLIC_API_BASE_URL` in the **frontend** host to point at the deployed backend, including the `/api/v1` prefix (the frontend's own `.env.example` documents this: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`).
5. Frontend also uses `NEXT_PUBLIC_APP_ENV`.

**Blocker that must be fixed before step 1 works — the hardcoded CORS origin.** As detailed in §3.3, `backend/app/core/middleware.py:11-31` only emits CORS headers when `origin == "http://localhost:3000"`, and only short-circuits preflight for that exact origin. The `CORS_ORIGINS` list at `config.py:12` is dead config. **A Vercel-hosted frontend will be blocked by CORS on every request until this is changed to read the configured allow-list.** Anyone deploying this should treat that as the first code change required.

### 5.3 Git repository status — `VERIFIED LIVE`, and this is bad

```
$ git rev-parse --is-inside-work-tree
true

$ git remote -v
(empty — no remote configured)

$ git branch --show-current
master

$ git rev-list --count HEAD
fatal: ambiguous argument 'HEAD': unknown revision or path not in the working tree
```

**There is no remote and there are zero commits.** The repository is initialized on branch `master` but `HEAD` does not exist, meaning **nothing has ever been committed** — the entire project, including all the fixes described in §3, is untracked working-tree state. There is no history, no authorship trail, and nothing that has been pushed anywhere. The `.gitignore` situation compounds this:

- `frontend/.gitignore` **exists** and correctly excludes `node_modules`, `.next`, and `.env*`.
- **There is no root `.gitignore` and no `backend/.gitignore`.**

**Concrete risk: a first `git add .` from the repo root would stage `backend/.env` and `node_modules`.** That file contains the live `SUPABASE_SERVICE_KEY` and `GEMINI_API_KEY`. I am not reproducing those values in this report.

### 5.4 Environment variable documentation — present, but contains live secrets

`.env.example` files do exist, so the information a new deployer needs is largely available:

- **Root `E:\ResolveAI\.env.example`** (586 bytes) — documents `GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `BACKEND_HOST`, `BACKEND_PORT`, `NEXT_PUBLIC_API_URL`.
- **`frontend/.env.example`** (253 bytes) — documents `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_APP_ENV`. This one is clean: placeholders only.
- **Backend: no `.env.example` at all.** The backend directory has only the real `backend/.env` (434 bytes). A new deployer must infer backend variables from the root template or from `app/core/config.py`.

**Security finding — the root `.env.example` contains what appear to be real, working credentials.** Despite its header comment reading `# Copy this file to .env and fill in your values`, the `GEMINI_API_KEY` and `SUPABASE_SERVICE_KEY` entries hold actual live values (the Supabase key is a `service_role` JWT for project `obkzebmxmvncsyqiztgp`, and it is the same key that authenticates every request in this report). I have deliberately not copied those values into this document. Combined with §5.3's missing root `.gitignore`, **a template file carrying live production credentials is one `git add .` away from being pushed to a public remote.** Recommended remediation, not performed here: rotate both credentials, replace them with placeholders in the template, and add a root `.gitignore` covering `.env`, `.env*`, `node_modules/`, and `.next/` before the initial commit.

---

## 6. OVERALL ASSESSMENT

### 6.1 Direct verdict

**Yes — the product is demonstrable end-to-end right now for its four core scenarios, on localhost, with real database evidence at every stage.** All three approved actions executed exactly once, verified by reading the database back, and produced complete audit chains. Every denial correctly produced no side effects. The idempotency ledger proves duplicate execution is prevented. This is a working system, not a mockup.

**But it is a local development demo, not a deployable product, and the gap between those two things is currently wide.** The two things that block a real deployment are mundane and easy to fix (hardcoded CORS origin; backend hosting), and the thing that blocks confident trust in the test suite is more subtle (a vacuous assertion in the one scenario that appears to cover the critical path).

### 6.2 What a live reviewer could click through successfully today

Assuming `npm run dev` and `uvicorn` are running on a fresh clone **with valid credentials** (a fresh clone is not currently possible — see §5.3 — so this means on this machine's working tree):

1. **Health check.** `GET /api/v1/health/` returns `{"status":"healthy","application":"ResolveAI","environment":"development"}`. All six frontend pages return 200.
2. **Submit a refund request** on the landing page for an eligible order. The workflow runs and writes a resolution plus a full audit chain. *Caveat: the working tree has been exercised heavily — 23 resolutions across 43 orders, with many orders already refunded or cancelled. Finding a *fresh* order that will auto-approve may require picking one from the 12 `delivered` orders, and several were already consumed by earlier runs.*
3. **Watch a HITL pause.** A request over the `$100.00` threshold parks in `pending_approval` and creates an `approval_requests` row visible in `/approvals`. This works — but with the §4.3 caveat that a pending `cancel_order` for the already-refunded order 10482 is sitting in the queue and will look odd.
4. **Approve or reject in the UI.** This is the flow that was broken and is now fixed (§3.2). A human decision drives the workflow to execute → verify → complete. Rejection drives it to a clean terminal rejection with no side effects. **This is the single most important thing for a reviewer to test, and the one place where the evaluator's pass rate must be disregarded** (§4.2) in favor of the manual evidence.
5. **Inspect the dashboard.** Real numbers: 23 requests, 6 successful, 4 pending approvals, 13 failed, ~10.6s average resolution time.
6. **Inspect the audit trail** per resolution. Genuine 8-to-12 event chains, with real payloads.

### 6.3 What a reviewer will hit that is rough or incomplete

- **CORS is hardcoded to `localhost:3000`** (§3.3, §5.2). The first thing that breaks on any non-localhost frontend. Must be fixed before deploying.
- **`GET /approvals/{id}` is a 500** (§4.4). Not reachable through the current UI, but the client method exists and is a trap for whoever builds the detail view. Expect a confusing opaque `INTERNAL_ERROR` rather than a useful message.
- **Three stranded workflows are invisible** (§4.3). The approvals queue looks complete while `27f7d985`, `263b8a62`, and `7a6fac3a` sit parked with no UI surface and no alert. A reviewer looking for "is anything stuck?" will not find it in the product.
- **The approvals queue contains a semantically stale request** — a pending `cancel_order` for order 10482, which is already refunded. Approving it would try to cancel a refunded order.
- **Approvals never reach "executed"** in the database (§4.1). Harmless to the demo; a real problem for any future approval-execution reporting, and it needs a Postgres migration.
- **The knowledge base contains a chemistry textbook** mislabeled as internal policy (§2.3), 4 of 21 chunks. Whether it actually pollutes RAG results for refund queries is **uncertain** — I did not test retrieval.
- **Duplicate `workflow_completed` audit events** (§4.5) in a system whose main claim is auditability.
- **10356's denial reasons still say "Order already fully refunded"** while the order is now `delivered` (§2.4). Deliberate, but it is stale text a reviewer will notice.
- **The evaluator will report 3 failures** (§4.2), and a reviewer who reads those as product bugs will be wrong; conversely, a reviewer who reads 18/21 as "the approval path is tested" will be *more* wrong. The one test that appears to cover the critical path asserts almost nothing.
- **No committed history and no remote** (§5.3). Nothing is under version control. There is no diff a reviewer can inspect, no way to see what changed, and no way to roll back. For a project claiming a series of substantive bug fixes, this is a serious readiness gap.
- **Live secrets sit in `.env.example` with no root `.gitignore`** (§5.4). One `git add .` from a public remote away from disclosure.

### 6.4 Explicit uncertainties

Per the instruction to say "uncertain" rather than assume:
- **I did not click through the UI in this session.** All scenario evidence is database/API-derived. The UI rendering, the approvals decide controls, and the workflow trace view are **carried over from prior sessions and not re-confirmed now.**
- **The contrast/animation/responsive fixes are not re-verified** (§4.6).
- **I did not run the automated test suite**, and `pytest` is not a declared dependency (§4.5).
- **I did not re-run the evaluator**; all evaluator figures are `VERIFIED PRIOR` (§4.2).
- **Whether the chemistry document degrades RAG retrieval quality is unknown** — untested (§2.3).
- **The §4.4 root cause is `INFERRED` from reading the route and service code**, not from a captured traceback. The 500 itself is `VERIFIED LIVE`; the response-model mismatch explanation is my diagnosis.
- **The interaction between the 307 trailing-slash redirect and CORS headers is unverified** (§3.3) and is a plausible remaining source of intermittent browser-side failures.

---

*End of report. Every quantitative claim above traces to a command output pasted in this document or is explicitly labelled `VERIFIED PRIOR` / `INFERRED`. No claim of completion is made without a pointer to evidence.*

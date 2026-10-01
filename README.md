# ResolveAI

> **AI-powered business resolution engine for controlled, auditable operations.**

ResolveAI is a portfolio-grade AI Engineering project that demonstrates how an AI system can move beyond **answering questions** and actually **resolve business requests through controlled workflows**.

Instead of treating an LLM as an unrestricted decision-maker, ResolveAI combines:

**AI reasoning + RAG + deterministic business policies + controlled tools + human approval + verification + auditability**

The system is built around a simple principle:

> **AI can investigate and reason, but business actions must remain controlled, policy-governed, verifiable, and auditable.**

ResolveAI uses a fictional e-commerce company, **Northstar Commerce**, as its business environment.

---

## Table of Contents

* [Overview](#overview)
* [The Problem](#the-problem)
* [The Solution](#the-solution)
* [Core Workflow](#core-workflow)
* [Example Resolution](#example-resolution)
* [Key Capabilities](#key-capabilities)
* [Architecture](#architecture)
* [Why This Architecture](#why-this-architecture)
* [AI and Agent Design](#ai-and-agent-design)
* [RAG Pipeline](#rag-pipeline)
* [Policy and Safety Model](#policy-and-safety-model)
* [Human-in-the-Loop](#human-in-the-loop)
* [Execution and Verification](#execution-and-verification)
* [Auditability](#auditability)
* [Evaluation](#evaluation)
* [Northstar Commerce](#northstar-commerce)
* [Technology Stack](#technology-stack)
* [Project Structure](#project-structure)
* [Application Routes](#application-routes)
* [API Surface](#api-surface)
* [Getting Started](#getting-started)
* [Environment Variables](#environment-variables)
* [Development](#development)
* [Testing](#testing)
* [Design Principles](#design-principles)
* [Engineering Decisions](#engineering-decisions)
* [Project Status](#project-status)
* [Limitations](#limitations)
* [Future Improvements](#future-improvements)
* [What I Learned](#what-i-learned)
* [Author](#author)

---

# Overview

Traditional AI support systems are often designed primarily to **generate answers**.

ResolveAI explores a different problem:

> **Can an AI system investigate a real business request, gather evidence, apply deterministic rules, safely perform an action when permitted, verify the result, and leave behind an auditable record?**

ResolveAI is designed as a controlled business resolution engine.

A request moves through a structured lifecycle:

```text
REQUEST
   ↓
UNDERSTAND
   ↓
INVESTIGATE
   ↓
EVIDENCE
   ↓
POLICY
   ↓
APPROVAL (when required)
   ↓
EXECUTE
   ↓
VERIFY
   ↓
AUDIT
   ↓
RESPONSE
```

The goal is not to make the AI appear autonomous.

The goal is to make autonomy **useful, bounded, observable, and safe**.

---

# The Problem

Business operations frequently contain requests that are simple for a human but difficult to automate safely.

For example:

> "My shipment is four days late. Can I get a refund?"

A traditional chatbot might respond with a general explanation of the refund policy.

A real operations system needs to do much more:

1. Identify the order.
2. Inspect the order state.
3. Investigate shipment status.
4. Retrieve relevant company policy.
5. Determine eligibility.
6. Calculate the applicable refund.
7. Decide whether the action can be performed automatically.
8. Request human approval when required.
9. Execute the controlled business operation.
10. Verify that the operation actually succeeded.
11. Record what happened.
12. Return a clear explanation to the user.

That creates several engineering challenges:

* LLM reliability
* hallucination control
* business-rule consistency
* tool safety
* authorization boundaries
* human approval
* idempotency
* side-effect verification
* auditability
* retrieval quality
* evaluation

ResolveAI is built to demonstrate solutions to these problems.

---

# The Solution

ResolveAI combines an AI reasoning layer with deterministic business infrastructure.

The AI is responsible for tasks such as:

* understanding natural-language requests
* identifying relevant entities
* deciding what information needs to be investigated
* selecting appropriate tools
* retrieving relevant knowledge
* synthesizing evidence
* explaining the final result

Deterministic components remain responsible for:

* business policy
* eligibility calculations
* approval thresholds
* controlled side effects
* idempotency
* verification
* audit records

This creates a separation between:

```text
AI REASONING
      +
DETERMINISTIC CONTROL
      +
HUMAN OVERSIGHT
```

---

# Core Workflow

Every resolution follows a controlled lifecycle.

```text
┌───────────────┐
│    REQUEST    │
└───────┬───────┘
        ↓
┌───────────────┐
│   UNDERSTAND  │
└───────┬───────┘
        ↓
┌───────────────┐
│  INVESTIGATE  │
└───────┬───────┘
        ↓
┌───────────────┐
│    EVIDENCE   │
│  Business +   │
│     RAG       │
└───────┬───────┘
        ↓
┌───────────────┐
│    POLICY     │
│ Deterministic │
│    Decision   │
└───────┬───────┘
        ↓
   ┌────┴──────────────┐
   │                   │
ALLOW             APPROVAL
   │                   │
   │              Human Review
   │                   │
   └────────┬──────────┘
            ↓
      ┌─────────────┐
      │   EXECUTE   │
      └──────┬──────┘
             ↓
      ┌─────────────┐
      │   VERIFY    │
      └──────┬──────┘
             ↓
      ┌─────────────┐
      │    AUDIT    │
      └──────┬──────┘
             ↓
      ┌─────────────┐
      │   RESPONSE  │
      └─────────────┘
```

A policy decision can produce:

```text
ALLOW
DENY
REQUIRES_APPROVAL
```

The LLM cannot simply override a deterministic policy decision.

---

# Example Resolution

### User request

```text
My shipment is 4 days late. Can I get a refund?
```

### ResolveAI

**1. Understand**

Identifies the request as a shipment/refund resolution.

**2. Investigate**

Retrieves order and shipment information.

**3. Evidence**

Combines operational data with relevant Northstar Commerce policy retrieved through RAG.

**4. Policy**

The deterministic policy engine evaluates eligibility.

```text
Decision: ALLOW
```

**5. Execute**

A controlled refund tool performs the permitted business action.

**6. Verify**

The system checks that the expected state change actually occurred.

**7. Audit**

The complete resolution is recorded.

**8. Response**

The user receives a concise explanation based on the evidence and completed action.

---

# High-Value Scenarios

ResolveAI is designed around meaningful business scenarios rather than random demo data.

### 1. Low-value delayed shipment

```text
Delayed shipment
      ↓
Policy eligible
      ↓
ALLOW
      ↓
Refund executed
      ↓
Verification
      ↓
Audit
```

### 2. High-value refund

```text
Refund request
      ↓
Eligible
      ↓
Amount exceeds automatic threshold
      ↓
REQUIRES_APPROVAL
      ↓
Human approval
      ↓
Execute
      ↓
Verify
      ↓
Audit
```

### 3. Invalid refund

```text
Refund request
      ↓
Policy evaluation
      ↓
DENY
      ↓
No side effect
      ↓
Audit
```

### 4. Cancellation after shipment

```text
Cancellation request
      ↓
Order already shipped
      ↓
REQUIRES_APPROVAL
      ↓
Human decision
      ↓
Controlled execution
      ↓
Verification
      ↓
Audit
```

These scenarios demonstrate different branches of the resolution engine rather than simply showing a successful chatbot response.

---

# Key Capabilities

## AI Reasoning

* Natural-language request understanding
* Agent-style investigation
* Tool selection
* Evidence synthesis
* Context-aware responses

## Retrieval-Augmented Generation

* Company knowledge ingestion
* Document chunking
* Gemini embeddings
* PostgreSQL + pgvector retrieval
* Policy evidence
* Grounded responses

## Deterministic Business Logic

* Policy evaluation
* Eligibility calculation
* Approval thresholds
* Explicit ALLOW / DENY / REQUIRES_APPROVAL decisions

## Controlled Tools

Business operations are exposed through explicit tools rather than unrestricted database mutations.

Examples include:

* order investigation
* shipment investigation
* refund calculation
* refund execution
* cancellation handling
* verification

## Human-in-the-Loop

High-risk operations can stop the workflow and create an approval request.

The system does not execute the side effect until the required approval is completed.

## Reliability

The project includes engineering mechanisms for:

* idempotency
* controlled retries
* execution state
* verification
* failure handling
* auditability

## Observability

The resolution experience exposes the stages of the workflow so that an operator can understand:

```text
What happened?
Why did it happen?
What evidence was used?
What policy was applied?
Was approval required?
What action was executed?
Was the result verified?
```

---

# Architecture

```text
                         ┌─────────────────────┐
                         │      Next.js UI     │
                         │                     │
                         │ Dashboard            │
                         │ Resolution Console   │
                         │ Approvals             │
                         │ Knowledge             │
                         │ Evaluation            │
                         └──────────┬──────────┘
                                    │
                                  REST
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    FastAPI API      │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Resolution Engine   │
                         │                     │
                         │ Understand          │
                         │ Investigate         │
                         │ Evidence            │
                         │ Policy              │
                         │ Approval            │
                         │ Execute             │
                         │ Verify              │
                         │ Audit               │
                         └──────┬───────┬──────┘
                                │       │
                    ┌───────────┘       └────────────┐
                    ▼                                ▼
          ┌──────────────────┐             ┌──────────────────┐
          │   RAG / pgvector │             │ Business Tools   │
          │                  │             │                  │
          │ Documents        │             │ Orders           │
          │ Chunks           │             │ Shipments        │
          │ Embeddings       │             │ Refunds          │
          │ Retrieval        │             │ Cancellations    │
          └────────┬─────────┘             └────────┬─────────┘
                   │                                │
                   └──────────────┬─────────────────┘
                                  ▼
                       ┌─────────────────────┐
                       │ Supabase PostgreSQL │
                       │                     │
                       │ Business data       │
                       │ Knowledge           │
                       │ Workflow state      │
                       │ Approvals           │
                       │ Audit events        │
                       └─────────────────────┘

                                  │
                                  ▼

                       ┌─────────────────────┐
                       │ Deterministic       │
                       │ Policy Engine       │
                       └──────────┬──────────┘
                                  │
                           ┌──────┴──────┐
                           ▼             ▼
                         ALLOW          DENY
                           │
                           ▼
                     EXECUTE / VERIFY

                           OR

                     REQUIRES_APPROVAL
                           │
                           ▼
                    Human Approval Queue
```

---

# Why This Architecture?

ResolveAI intentionally avoids a large agent framework.

The project does **not** use:

* LangChain
* LangGraph
* CrewAI
* AutoGen
* Docker
* Redis
* Kafka
* Celery

The reason is not that these technologies are inherently bad.

The goal of this project is to understand and demonstrate the underlying engineering concepts directly.

A lightweight custom controller makes the control flow explicit:

```text
Agent reasoning
      ↓
Tool selection
      ↓
Evidence gathering
      ↓
Policy evaluation
      ↓
Approval boundary
      ↓
Controlled side effect
      ↓
Verification
      ↓
Audit
```

This also keeps the project inexpensive and easy to run locally.

---

# AI and Agent Design

ResolveAI does not attempt to make the LLM responsible for everything.

Instead, responsibilities are deliberately separated.

### LLM responsibilities

```text
Interpret
Investigate
Retrieve
Reason
Synthesize
Explain
```

### Deterministic responsibilities

```text
Policy
Eligibility
Thresholds
Permissions
Side effects
Idempotency
Verification
Audit
```

This distinction is important because a language model can generate plausible reasoning without being a reliable source of business truth.

For example:

```text
LLM:
"Based on the information I found, this appears eligible."

        ↓

Policy Engine:
"Refund amount = $X
Automatic threshold = $Y
Decision = REQUIRES_APPROVAL"

        ↓

Workflow:
STOP until human approval
```

The model does not get to bypass the policy boundary.

---

# RAG Pipeline

ResolveAI uses Retrieval-Augmented Generation to ground AI responses in Northstar Commerce knowledge.

```text
Company Documents
       ↓
Document Extraction
       ↓
Chunking
       ↓
Gemini Embeddings
       ↓
PostgreSQL + pgvector
       ↓
Semantic Retrieval
       ↓
Relevant Policy Evidence
       ↓
AI Reasoning
```

The retrieved evidence is surfaced as part of the resolution trace.

This allows the operator to inspect not only the answer but also the company knowledge used to reach it.

---

# Policy and Safety Model

Business policy is intentionally separated from the LLM.

For example:

```text
Refund Amount
       ↓
Policy Evaluation
       ↓
┌──────────────────────────────┐
│ Below automatic threshold    │
│              ↓               │
│           ALLOW              │
└──────────────────────────────┘

┌──────────────────────────────┐
│ Above automatic threshold    │
│              ↓               │
│     REQUIRES_APPROVAL        │
└──────────────────────────────┘

┌──────────────────────────────┐
│ Not eligible                 │
│              ↓               │
│            DENY              │
└──────────────────────────────┘
```

This provides a deterministic safety boundary around business actions.

---

# Human-in-the-Loop

Not every business operation should be autonomous.

ResolveAI therefore supports approval-gated workflows.

Example:

```text
AI Investigation
       ↓
Evidence
       ↓
Policy
       ↓
High-risk action
       ↓
REQUIRES_APPROVAL
       ↓
Human Review
       ↓
┌──────────────┐
│              │
▼              ▼
APPROVE       REJECT
│              │
▼              ▼
Execute       Stop
│
▼
Verify
```

This demonstrates a practical pattern for AI systems operating in environments where actions can have financial or operational consequences.

---

# Execution and Verification

Execution is not considered successful simply because a tool call returned successfully.

ResolveAI separates:

```text
EXECUTE
   ↓
VERIFY
```

For example:

```text
Refund Tool
     ↓
Refund request sent
     ↓
Database state checked
     ↓
Expected refund confirmed
```

If verification does not match the expected result, the workflow can surface the failure rather than claiming success.

This distinction is important when AI systems interact with systems that have real side effects.

---

# Idempotency

Business operations must not accidentally execute multiple times because of retries, duplicate requests, or workflow replays.

ResolveAI therefore uses idempotent operation handling around controlled side effects.

Conceptually:

```text
Request
   ↓
Operation ID
   ↓
Check existing execution
   ↓
┌───────────────┐
│ Already done? │
└───────┬───────┘
        │
   ┌────┴────┐
   │         │
  YES        NO
   │         │
   ▼         ▼
Return    Execute
existing     │
result       ▼
          Record
             │
             ▼
          Verify
```

This is especially important for actions such as refunds.

---

# Auditability

Every resolution should answer:

* What did the user request?
* What did the system understand?
* What data did it investigate?
* What knowledge was retrieved?
* What policy was applied?
* What decision was made?
* Was approval required?
* Who approved it?
* What action was executed?
* What was the result?
* Was the result verified?

The Resolution Console exposes this lifecycle as a trace rather than hiding it behind a single chatbot response.

---

# Evaluation

ResolveAI includes an evaluation layer for testing important resolution scenarios.

The purpose of evaluation is not simply to measure whether an LLM produces a good-looking answer.

The system should also be evaluated on whether it:

* selects the appropriate workflow
* retrieves useful evidence
* applies policy correctly
* avoids unauthorized actions
* creates approval requests when necessary
* avoids duplicate side effects
* verifies execution
* records the appropriate audit information

This makes the evaluation closer to an **AI system reliability problem** than a simple text-generation benchmark.

---

# Northstar Commerce

ResolveAI operates on synthetic business data belonging to a fictional company:

**Northstar Commerce**

Northstar Commerce is modeled as a mid-sized e-commerce company selling consumer electronics and home goods through multiple channels.

The synthetic environment contains business concepts such as:

* customers
* orders
* products
* shipments
* refunds
* cancellations
* company policies
* knowledge documents
* resolution workflows
* approvals
* audit events

No real customer information is required for the project.

---

# Technology Stack

| Layer                 | Technology                |
| --------------------- | ------------------------- |
| Frontend              | Next.js                   |
| Language              | TypeScript                |
| Styling               | Tailwind CSS              |
| UI Components         | shadcn/ui                 |
| Icons                 | Lucide                    |
| Backend               | Python                    |
| API                   | FastAPI                   |
| Server                | Uvicorn                   |
| Database              | Supabase PostgreSQL       |
| Vector Search         | pgvector                  |
| LLM                   | Google Gemini             |
| Embeddings            | Gemini Embeddings         |
| Agent Orchestration   | Lightweight custom Python |
| Authentication        | Not required for MVP      |
| Deployment Philosophy | Lightweight / no Docker   |

---

# Project Structure

The repository is organized around the frontend, backend, documentation, and synthetic knowledge data.

```text
ResolveAI/
│
├── backend/
│   ├── ...
│   └── FastAPI application
│
├── frontend/
│   ├── ...
│   └── Next.js application
│
├── data/
│   └── documents/
│       └── Synthetic Northstar Commerce knowledge
│
├── docs/
│   └── Architecture and project documentation
│
├── README.md
├── .gitignore
└── supporting scripts / configuration
```

The exact internal module structure may evolve as the project is developed.

---

# Application Routes

## `/`

Product landing page.

Explains the purpose of ResolveAI and the controlled-resolution concept.

---

## `/dashboard`

Operations dashboard.

Provides a high-level view of resolution activity and operational metrics.

---

## `/console`

Resolution Command Center.

The primary workflow interface.

A resolution can be inspected through:

```text
Request
→ Investigation
→ Evidence
→ Policy
→ Approval
→ Execution
→ Verification
→ Audit
```

---

## `/approvals`

Human Approval Queue.

Displays business operations waiting for human decisions.

---

## `/approvals/[id]`

Approval Detail.

Allows an operator to inspect the evidence and decision context associated with an approval.

---

## `/knowledge`

Knowledge Base.

Used to inspect and search Northstar Commerce company knowledge.

---

## `/evaluation`

Evaluation results.

Provides visibility into the evaluation harness and tested resolution behavior.

---

# API Surface

The backend exposes versioned REST endpoints under:

```text
/api/v1
```

Important endpoint groups include:

```text
/api/v1/health/

/api/v1/resolutions
/api/v1/resolutions/{workflow_id}
/api/v1/resolutions/{workflow_id}/approve
/api/v1/resolutions/{workflow_id}/reject

/api/v1/approvals/approvals
/api/v1/approvals/approvals/{approval_id}
/api/v1/approvals/approvals/{approval_id}/decide
/api/v1/approvals/approvals/{approval_id}/execute
/api/v1/approvals/approvals/{approval_id}/detail

/api/v1/audit/events
/api/v1/audit/traces
/api/v1/audit/traces/{workflow_id}

/api/v1/dashboard/dashboard/metrics
```

The API surface may evolve as implementation details are refined.

---

# Getting Started

## Prerequisites

You should have:

* Python installed
* Node.js installed
* npm installed
* a Supabase project
* a Google Gemini API key

Docker is **not required**.

---

## 1. Clone the repository

```bash
git clone https://github.com/HassaanDeveloper/ResolveAI.git
cd ResolveAI
```

---

## 2. Configure the backend

Navigate to the backend:

```bash
cd backend
```

Create the backend environment file according to the project's environment template.

Configure the required Supabase and Gemini credentials.

---

## 3. Install Python dependencies

Use the project's Python dependency configuration to install the backend requirements.

Example:

```bash
pip install -r requirements.txt
```

---

## 4. Start the FastAPI backend

Run the FastAPI application using Uvicorn.

Example:

```bash
uvicorn app.main:app --reload --port 8000
```

The exact module path should match the current backend structure.

---

## 5. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The Next.js development server will normally be available at:

```text
http://localhost:3000
```

---

# Environment Variables

Environment variables are intentionally kept outside version control.

Typical configuration includes:

```env
SUPABASE_URL=
SUPABASE_KEY=

GEMINI_API_KEY=

NEXT_PUBLIC_API_URL=
```

The exact variables required by the current implementation should be taken from the project's environment templates.

**Never commit real API keys or service credentials.**

---

# Development

The recommended development workflow is:

```text
Frontend
   ↕
FastAPI
   ↕
Resolution Engine
   ↕
Supabase
   ↕
RAG / Policy / Business Tools
```

Run frontend and backend independently during development.

Health and API endpoints can be used to verify backend connectivity before testing the frontend workflows.

---

# Testing

ResolveAI should be tested at multiple levels.

### API / Backend

Verify:

* health endpoint
* resolution creation
* resolution retrieval
* approval creation
* approval decision
* execution
* verification
* audit trace retrieval

### Workflow

Test at least:

```text
ALLOW
DENY
REQUIRES_APPROVAL
```

### Reliability

Test:

* repeated requests
* duplicate execution attempts
* failed operations
* approval rejection
* verification failures

### Frontend

Manually verify:

* loading states
* empty states
* error states
* successful states
* responsive layouts
* workflow transitions
* approval interactions
* audit visibility

---

# Design Principles

ResolveAI's UI is intentionally designed as an **enterprise AI operations interface** rather than a generic AI chatbot.

The interface prioritizes:

### Visibility of system status

The user should know where the resolution currently is.

```text
Investigation
Evidence
Policy
Approval
Execution
Verification
Audit
```

### Recognition over recall

Important information should be visible instead of requiring users to remember previous steps.

### Error prevention

Risky actions should not silently execute.

### User control

Human approval remains available when business policy requires it.

### Consistency

Status, decision, risk, and workflow states use consistent visual patterns.

### Accessibility

The interface considers:

* keyboard navigation
* focus states
* semantic controls
* reduced motion
* readable hierarchy
* responsive layouts

### Minimalism

The UI should communicate operational information without turning every piece of data into a decorative card.

---

# Engineering Decisions

## Why Supabase PostgreSQL?

The project needs relational business data as well as vector retrieval.

PostgreSQL provides:

* relational storage
* SQL
* transactional behavior
* pgvector
* a practical single-database foundation

This avoids unnecessary infrastructure.

---

## Why pgvector?

ResolveAI needs retrieval over company knowledge.

Using pgvector keeps the vector layer close to the application's relational data rather than introducing another service for the MVP.

---

## Why Gemini?

Gemini provides both the LLM and embedding capabilities required by the project while keeping the architecture relatively simple.

---

## Why no LangChain / LangGraph?

ResolveAI is intentionally implemented using a lightweight custom orchestration layer.

This makes the workflow mechanics explicit and helps demonstrate understanding of:

* state
* tool calling
* policy boundaries
* approvals
* execution
* verification
* auditability

rather than hiding the architecture behind a large framework.

---

## Why no Docker?

The project is designed to run locally without heavy infrastructure.

This reduces setup complexity and resource requirements while keeping the architecture understandable.

---

## Why deterministic policies?

LLMs are probabilistic.

Business rules often should not be.

Therefore:

```text
LLM → investigate / reason / explain

Policy Engine → decide business eligibility

Tools → perform controlled side effects

Verification → confirm the result
```

This separation makes the system easier to reason about and test.

---

# Project Status

ResolveAI has progressed from a basic backend foundation into a complete portfolio-oriented AI resolution system.

Implemented areas include:

* [x] Project foundation
* [x] FastAPI backend
* [x] Supabase PostgreSQL
* [x] Synthetic Northstar Commerce data
* [x] Business tools
* [x] Deterministic policy engine
* [x] Resolution workflow
* [x] Knowledge ingestion
* [x] RAG retrieval
* [x] Gemini integration
* [x] Agent intelligence
* [x] Human approval workflow
* [x] Idempotency handling
* [x] Execution verification
* [x] Audit trail
* [x] Evaluation harness
* [x] Next.js frontend
* [x] Resolution Command Center
* [x] Operations dashboard
* [x] Approval interface
* [x] Knowledge Base interface
* [x] Evaluation interface
* [x] Accessibility foundation
* [x] Responsive UI foundation

The remaining work should focus on **final integration verification, manual testing, deployment, documentation, and demonstration**, rather than expanding the architecture unnecessarily.

---

# Limitations

ResolveAI is a portfolio and learning project rather than a production enterprise platform.

Important limitations include:

* Northstar Commerce is synthetic.
* Authentication is outside the MVP scope.
* Business integrations are simulated/controlled.
* The system is not intended to process real customer financial data.
* The deployment architecture is intentionally lightweight.
* The system has not been positioned as a fully production-hardened SaaS platform.
* LLM behavior remains probabilistic, which is why deterministic policy and execution boundaries are important.

The project intentionally prioritizes **technical clarity and demonstrability** over production-scale infrastructure.

---

# Future Improvements

Potential future improvements include:

* stronger automated evaluation coverage
* richer retrieval evaluation
* improved observability
* production-grade authentication and authorization
* additional business integrations
* more sophisticated approval policies
* distributed execution infrastructure
* stronger automated regression testing
* deployment hardening
* multi-tenant architecture

These are intentionally outside the core portfolio MVP.

The immediate objective is to keep the existing system coherent, reliable, and demonstrable.

---

# What I Learned

ResolveAI was built as an AI Engineering and FDE learning project.

The project helped explore practical problems that are easy to overlook when building simple LLM applications:

### 1. AI systems need boundaries

An LLM should not automatically have unrestricted authority over business operations.

### 2. RAG is more than vector search

Useful retrieval requires understanding:

```text
Documents
→ chunks
→ embeddings
→ retrieval
→ evidence
→ grounded reasoning
```

### 3. Tool calling creates real engineering problems

Once an AI system can perform side effects, concerns such as:

* idempotency
* retries
* permissions
* verification
* auditability

become essential.

### 4. Human-in-the-loop is an architectural pattern

Approval should be part of the workflow rather than an afterthought.

### 5. Evaluation matters

A convincing AI response is not enough.

The system must also demonstrate that it behaves correctly under important scenarios.

### 6. FDE work is broader than writing code

A real AI engineering / FDE workflow involves:

```text
Understand the problem
        ↓
Design the system
        ↓
Integrate components
        ↓
Debug failures
        ↓
Validate behavior
        ↓
Evaluate reliability
        ↓
Explain the system
        ↓
Ship the product
```

ResolveAI was built to practice that complete loop.

---

# Author

**Muhammad Hassaan**

BS Software Engineering student and AI Engineering / Forward Deployed Engineering learner focused on building practical AI systems.

### Focus Areas

* AI Engineering
* Forward Deployed Engineering
* Agentic AI
* Retrieval-Augmented Generation
* Full-Stack AI Applications
* AI Reliability
* Business Automation
* Data Analytics

### GitHub

[github.com/HassaanDeveloper](https://github.com/HassaanDeveloper?utm_source=chatgpt.com)

### ResolveAI Repository

[HassaanDeveloper/ResolveAI](https://github.com/HassaanDeveloper/ResolveAI?utm_source=chatgpt.com)

---

# Final Principle

ResolveAI is built around one idea:

> **Don't give AI unrestricted control. Give it the ability to understand, investigate, reason, and recommend — then surround consequential actions with deterministic policies, human approval, controlled tools, verification, and auditability.**

That is the difference between an AI chatbot and an **AI-powered business resolution system**.

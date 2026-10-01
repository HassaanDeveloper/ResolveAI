# ResolveAI

**AI-Powered Business Resolution Engine for Northstar Commerce**

## What is ResolveAI?

ResolveAI is an intelligent system that automates the resolution of business exceptions — disputed charges, failed deliveries, inventory mismatches, refund requests, and other operational anomalies that typically require human investigation.

## What is Northstar Commerce?

Northstar Commerce is a fictional mid-sized e-commerce company that sells consumer electronics and home goods across multiple channels (web, mobile, marketplace). They process ~50,000 orders/month and face a growing backlog of exception cases that require manual review.

## The Problem

- **Volume**: 200+ exception cases per day requiring human review
- **Inconsistency**: Different agents apply policies differently
- **Latency**: Average resolution time: 4–6 hours
- **Cost**: Dedicated team of 8 resolution specialists
- **Auditability**: Limited traceability of decisions

## Intended High-Level Architecture

```
Next.js Frontend
       ↓
   REST API
       ↓
   FastAPI Backend
       ↓
Custom Agent Controller
       ↓
RAG + Business Tools + Deterministic Policy Engine
       ↓
Human Approval (when required)
       ↓
Execute
       ↓
Verify
       ↓
Audit Log
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | Python, FastAPI, Uvicorn |
| Database | Supabase PostgreSQL + pgvector |
| LLM | Google Gemini API |
| Embeddings | Gemini embeddings (text-embedding-004) |
| Orchestration | Custom Python (no LangChain/LangGraph/CrewAI/AutoGen) |

### Key Architectural Principles

1. **No Docker/Kubernetes/Redis/Kafka/Celery** — runs natively on laptop
2. **No heavy orchestration frameworks** — custom lightweight controller
3. **Deterministic policies outside LLM** — rule engine for consistency
4. **Human-in-the-loop** — approval gates for high-risk actions
5. **Full audit trail** — every decision logged and traceable
6. **Synthetic data only** — no real customer data in development

## Current Development Status

**Part 01 — Project Foundation** ✓
- Repository structure created
- Basic FastAPI backend with `/health` endpoint
- Project documentation (architecture, decisions)
- Environment configuration template

**Next**: Part 02 — Backend Core & Configuration
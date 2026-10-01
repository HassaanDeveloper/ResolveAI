# ResolveAI Architecture

## High-Level Overview

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

## Components

### Frontend (Next.js + TypeScript + Tailwind + shadcn/ui)
- User interface for business resolution workflows
- Communicates with backend via REST API

### Backend (FastAPI + Python)
- API layer exposing endpoints to frontend
- Agent orchestration controller
- Business logic coordination

### Custom Agent Controller
- Lightweight orchestration (no LangChain/LangGraph/CrewAI/AutoGen)
- Manages agent lifecycle and tool execution
- Handles human-in-the-loop approvals

### RAG System
- Document retrieval using Gemini embeddings
- Supabase pgvector for vector storage
- Context injection for agent decision-making

### Business Tools
- Deterministic functions for business operations
- Order management, refunds, inventory checks, etc.
- No LLM involvement in tool execution

### Deterministic Policy Engine
- Rule-based decision engine outside the LLM
- Enforces business policies consistently
- Auditable and testable logic

### Human Approval
- Escalation path for high-risk decisions
- Approval workflows with audit trail

### Audit Log
- Immutable record of all decisions and actions
- Supports compliance and debugging

## Data Layer
- **Supabase PostgreSQL**: Primary data store
- **pgvector**: Vector embeddings for RAG
- **Synthetic Data**: All business data is synthetic for development

## Infrastructure
- No Docker, Kubernetes, Redis, Kafka, Celery
- No Qdrant, Elasticsearch
- Runs on resource-constrained laptop
- Lightweight by design
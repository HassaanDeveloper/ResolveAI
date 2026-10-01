# Architectural Decisions

## 1. No Docker
**Decision**: Do not use Docker for development or deployment.
**Rationale**: Adds complexity and resource overhead. Direct Python/Node execution is simpler for a laptop-based development environment.

## 2. No Heavy Orchestration Framework
**Decision**: Do not use LangChain, LangGraph, CrewAI, or AutoGen.
**Rationale**: These frameworks add significant dependencies and abstraction layers. A custom lightweight controller provides full control, transparency, and minimal overhead.

## 3. Supabase PostgreSQL + pgvector
**Decision**: Use Supabase PostgreSQL with pgvector extension for both relational data and vector embeddings.
**Rationale**: Single database for all data needs. pgvector provides native vector similarity search. Supabase offers managed PostgreSQL with auth, realtime, and storage if needed later.

## 4. Google Gemini API
**Decision**: Use Google Gemini for LLM and embeddings.
**Rationale**: Strong multimodal capabilities, generous free tier, good embedding models (text-embedding-004), and simple API.

## 5. Custom Lightweight Agent Orchestration
**Decision**: Build a custom agent controller in Python.
**Rationale**: Full control over agent behavior, tool calling, state management, and approval flows. No framework lock-in. Easier to debug and test.

## 6. Deterministic Policy Engine Outside the LLM
**Decision**: Business policies enforced by a separate rule engine, not the LLM.
**Rationale**: LLMs are non-deterministic. Policies must be consistent, auditable, and testable. Rule engine provides guarantees that LLM prompting cannot.

## 7. Synthetic Business Data Only
**Decision**: All development and test data is synthetic.
**Rationale**: No PII, no compliance issues, reproducible test scenarios, safe for public repositories.
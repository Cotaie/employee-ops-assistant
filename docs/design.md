# Employee Ops Assistant Design

## 1. Overview

This document is the high-level architecture overview for Employee Ops Assistant.

The system is an employee-facing enterprise assistant for an automotive company. It combines:

- persistent enterprise knowledge retrieval
- employee-specific HR and operations lookups
- uploaded-file summarization and discussion
- confirmable employee actions
- multi-agent orchestration

The design uses:

- microservices
- Python for service implementation
- FastAPI for API services
- Gradio as a development-time smoke-test and manual E2E test UI
- two cooperating AI agents
- configurable primary and fallback LLM providers
- LangChain
- LangGraph
- Frappe HR as the HR system integration target
- Chroma for vector storage and semantic retrieval
- PostgreSQL relational storage for chatbot conversation persistence

Storage is intentionally split:

- Chroma stores enterprise knowledge embeddings and oversized uploaded-file embeddings for semantic retrieval
- PostgreSQL stores transactional application data such as conversations, messages, and action state

Uploaded employee files are temporary inputs. Any raw uploaded file and any derived indexed content created only for request-time analysis must be deleted after use.

Conversation context is compacted at runtime through summary generation when the active conversation context exceeds a configured token threshold, while the full conversation history remains stored in PostgreSQL.

## 2. Core Design Goals

- preserve a clear microservice architecture
- support at least two cooperating AI agents
- separate persistent knowledge retrieval from live employee-data and action flows
- support both direct-context file analysis and indexed file analysis

## 3. Architecture Constraints

- the system must use microservices
- the API implementation framework is FastAPI
- the service implementation language is Python
- the initial mandatory services are `IngestionApi`, `EmbeddingsApi`, `RetrievalApi`, and `AgentApi`
- the system must use both LangChain and LangGraph
- the system must include at least two real AI agents with distinct roles and tool access
- the HR system used for employee-specific HR data and leave-related operations is Frappe HR
- the vector store technology is Chroma
- chatbot conversations are persisted in PostgreSQL relational tables
- the system supports a configurable primary LLM and configurable fallback LLM, each independently enableable or disableable

## 4. High-Level Component Model

### 4.1 Core Services

- `IngestionApi`
  - ingests approved company documents and larger uploaded files
- `EmbeddingsApi`
  - generates embeddings for knowledge chunks and retrieval text
- `RetrievalApi`
  - retrieves relevant enterprise knowledge and indexed uploaded-file content
- `AgentApi`
  - hosts orchestration, agents, and tool coordination
  - persists conversation state and message history
- `LocalLlmApi`
  - exposes the local fallback model through an API boundary

### 4.2 Agents

- `Knowledge Agent`
  - policy and process knowledge
- `Operations Agent`
  - employee-specific information and actions

### 4.3 Model Providers

- primary LLM provider
  - default remote model path
- fallback LLM provider
  - backup model path used when the primary path is disabled or unavailable
  - exposed through `LocalLlmApi` when a local model is used

### 4.4 External Systems

- `Frappe HR`
  - leave balance, leave requests, benefits, shift-related employee data
- `Slack`
  - optional employee notification channel

### 4.5 Development-Time UI

- `Gradio`
  - used during development for smoke testing and manual end-to-end testing
  - acts as a lightweight client of `AgentApi`
  - is not the production frontend and is not part of the core `AgentApi` responsibility

## 5. Detailed Design Docs

- [API contracts](./design/apis.md)
- [Data model](./design/data-model.md)
- [Integrations](./design/integrations.md)
- [Sequence flows](./design/sequences.md)

## 6. Technology Roles

- `Python`
  - primary service implementation language

- `FastAPI`
  - API framework for microservices

- `Gradio`
  - development-time UI for backend validation and demos

- `LangChain`
  - loaders
  - embeddings integrations
  - vector store integrations
  - tool definitions

- `LangGraph`
  - orchestration
  - routing
  - state passing
  - multi-agent flow control

- model provider strategy
  - backend-side selection of primary or fallback LLM
  - failover when the primary path is unavailable and fallback is enabled

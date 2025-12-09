# Conversation Memory RAG System - Requirements

## Overview
Hybrid memory system combining SQLite (structured data) + ChromaDB (semantic search) to enable cross-session learning from past work.

**Phase**: Memory System Enhancement
**Author**: SRE Principal Engineer Agent
**Created**: 2025-12-08

---

## Problem Statement
Current `conversations.db` (SQLite) captures journey data but only supports keyword/exact matching. Cross-session memory requires semantic retrieval to find "similar" past problems and decisions.

**Gap**: No semantic search capability for conversation memory.

---

## Functional Requirements

### FR-1: Embedding Generation
- Generate embeddings at `complete_journey()` time
- Embed: `problem_description` + `meta_learning` (most valuable for retrieval)
- Use Ollama `nomic-embed-text` model (same as email_rag - proven)
- Graceful degradation if Ollama unavailable

### FR-2: ChromaDB Storage
- Store embeddings in `claude/data/rag_databases/conversation_memory_rag/`
- Collection name: `conversation_memory`
- Metadata: `journey_id`, `timestamp`, `agents_used`, `business_impact`
- Index state tracking (avoid re-embedding existing journeys)

### FR-3: Semantic Retrieval
- `search_similar(query, n_results=5)` - find similar past problems
- `get_relevant_context(current_problem)` - retrieve for session start
- Filter by recency (weight recent journeys higher)
- Return structured context for injection

### FR-4: Close-Session Integration
- Capture session summary before clearing session file
- Call `complete_journey()` with structured data
- Generate embedding and store in ChromaDB
- Then clear session file

### FR-5: Session-Start Integration
- On context load, query for relevant past journeys
- Inject as "relevant memory" context
- Limit to top 3-5 most relevant (token budget)

---

## Non-Functional Requirements

### NFR-1: Performance
- Embedding generation: <2s per journey
- Semantic search: <500ms
- Zero blocking on main conversation flow

### NFR-2: Reliability
- Graceful degradation if ChromaDB/Ollama unavailable
- SQLite remains source of truth (ChromaDB is index)
- Recovery: Can rebuild ChromaDB from SQLite

### NFR-3: Privacy
- All processing local (Ollama + ChromaDB)
- No external API calls
- Respects existing `privacy_flag` from conversations.db

---

## Technical Design

### Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Conversation Memory System                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐         ┌─────────────────────────┐   │
│  │ conversations.db │ ──────▶│ conversation_memory_rag │   │
│  │    (SQLite)      │         │      (ChromaDB)         │   │
│  │                  │         │                         │   │
│  │ • Structured data│         │ • Embeddings            │   │
│  │ • Agents used    │         │ • Semantic search       │   │
│  │ • Deliverables   │         │ • Similarity matching   │   │
│  │ • Source of truth│         │ • Fast retrieval        │   │
│  └─────────────────┘         └─────────────────────────┘   │
│           │                            │                    │
│           ▼                            ▼                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              ConversationMemoryRAG                   │   │
│  │                                                      │   │
│  │  • embed_journey(journey_id) - generate & store     │   │
│  │  • search_similar(query) - semantic retrieval       │   │
│  │  • get_relevant_context(problem) - session start    │   │
│  │  • sync_from_sqlite() - rebuild index               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Integration Points

1. **conversation_logger.py** - Add embedding call in `complete_journey()`
2. **swarm_auto_loader.py** - Add retrieval in session load
3. **close-session** - Capture summary before clear

### Dependencies
- `chromadb` (already installed - used by email_rag)
- `requests` (for Ollama API)
- Ollama running with `nomic-embed-text` model

---

## Test Cases

### TC-1: Embedding Generation
- Given a completed journey in SQLite
- When `embed_journey()` is called
- Then embedding is stored in ChromaDB with correct metadata

### TC-2: Semantic Search
- Given multiple journeys about different topics
- When searching for a topic
- Then most relevant journeys are returned (not just keyword match)

### TC-3: Graceful Degradation
- Given Ollama is not running
- When `embed_journey()` is called
- Then operation fails gracefully without blocking
- And SQLite data remains intact

### TC-4: Index Sync
- Given journeys in SQLite not yet in ChromaDB
- When `sync_from_sqlite()` is called
- Then all journeys are embedded and stored

### TC-5: Relevance Filtering
- Given old and recent similar journeys
- When retrieving context
- Then recent journeys are weighted higher

---

## Success Metrics
- Semantic search finds relevant context with >70% relevance score
- End-to-end latency <3s for close-session capture
- Zero data loss (SQLite always consistent)
- Rebuild from SQLite completes in <30s for 100 journeys

---

## Implementation Order
1. Create `conversation_memory_rag.py` with core class
2. Write tests for embedding and search
3. Implement embedding generation
4. Implement semantic search
5. Add sync utility
6. Integrate with `conversation_logger.py`
7. Wire into close-session flow
8. Add session-start retrieval

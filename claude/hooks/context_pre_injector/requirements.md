# Context Pre-Injector Requirements

## Phase 226: Automatic DB-First Context Loading

### Problem Statement
Claude ignores existing databases (capabilities.db, system_state.db) and defaults to grep/glob operations. This wastes tokens, time, and defeats the purpose of the database infrastructure.

### Solution
A hook-integrated tool that automatically injects relevant DB query results into Claude's context window on every prompt.

---

## Functional Requirements

### FR-1: Capability Summary Injection
- **FR-1.1**: MUST load capability summary from capabilities.db
- **FR-1.2**: MUST include counts (total, agents, tools)
- **FR-1.3**: MUST fall back gracefully if DB unavailable
- **FR-1.4**: Output MUST be <100 tokens

### FR-2: Query-Relevant Capability Injection
- **FR-2.1**: MUST extract keywords from user query
- **FR-2.2**: MUST search capabilities.db for matching tools/agents
- **FR-2.3**: MUST limit results to top 10 matches
- **FR-2.4**: MUST format as compact table
- **FR-2.5**: Output MUST be <400 tokens

### FR-3: Query-Relevant Phase Injection
- **FR-3.1**: MUST detect complex queries (implement, create, build, fix, debug)
- **FR-3.2**: MUST search system_state.db for relevant phases
- **FR-3.3**: MUST include phase numbers only (not full content)
- **FR-3.4**: Output MUST be <100 tokens

### FR-4: Output Format
- **FR-4.1**: MUST print to stdout (hook captures this)
- **FR-4.2**: MUST use clear visual delimiters
- **FR-4.3**: MUST label as "AUTO-INJECTED CONTEXT"
- **FR-4.4**: Total output MUST be <500 tokens

---

## Non-Functional Requirements

### NFR-1: Performance
- **NFR-1.1**: Total execution time MUST be <100ms
- **NFR-1.2**: DB queries MUST use existing SmartContextLoader
- **NFR-1.3**: MUST NOT block user prompt processing

### NFR-2: Reliability
- **NFR-2.1**: MUST NOT fail if databases unavailable
- **NFR-2.2**: MUST gracefully degrade to static fallback
- **NFR-2.3**: MUST NOT raise exceptions to caller
- **NFR-2.4**: Exit code MUST always be 0

### NFR-3: Integration
- **NFR-3.1**: MUST be callable from bash hook
- **NFR-3.2**: MUST accept query as command-line argument
- **NFR-3.3**: MUST work with empty query (summary only)

---

## Test Cases

### TC-1: Basic Functionality
- TC-1.1: inject_context("") returns capability summary
- TC-1.2: inject_context("security tools") returns security-related capabilities
- TC-1.3: inject_context("implement feature") triggers phase search

### TC-2: Keyword Extraction
- TC-2.1: extract_keywords("how do I use security tools") → ["security", "tools"]
- TC-2.2: extract_keywords("the") → [] (stopword filtered)
- TC-2.3: extract_keywords("") → []

### TC-3: Complexity Detection
- TC-3.1: is_complex_query("implement authentication") → True
- TC-3.2: is_complex_query("what is X") → False
- TC-3.3: is_complex_query("create new agent") → True

### TC-4: Graceful Degradation
- TC-4.1: Works when capabilities.db missing
- TC-4.2: Works when system_state.db missing
- TC-4.3: Never raises exception

### TC-5: Performance
- TC-5.1: Execution completes in <100ms
- TC-5.2: Output is <500 tokens

---

## Acceptance Criteria

1. Running `python3 context_pre_injector.py "query"` prints context summary
2. Output includes capability counts from DB
3. Query-relevant capabilities appear for matching queries
4. Complex queries trigger phase number injection
5. All failures are silent (graceful degradation)
6. Total execution <100ms

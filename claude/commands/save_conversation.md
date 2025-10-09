# Save Conversation

**Purpose**: Capture and persist key decisions, recommendations, and context from current conversation to knowledge systems for future retrieval.

## Usage
```
/save-conversation
```

## What This Command Does

1. **Interactive Summary**: Prompts you to describe the conversation
2. **Knowledge Graph Storage**: Creates structured nodes with relationships
3. **Semantic Indexing**: Makes conversation searchable via RAG
4. **Future Retrieval**: Enables "What did we discuss about X?" queries

## Process Flow

### Step 1: Conversation Analysis
- Review current conversation context
- Identify key topics, decisions, recommendations
- Extract action items and outcomes

### Step 2: User Input
Ask user to provide:
- **Topic**: Brief description (e.g., "Team member discipline approach")
- **Key Decisions**: Main outcomes or recommendations
- **Context**: Any important background information
- **Tags**: Keywords for future search (e.g., "HR", "management", "communication")

### Step 3: Multi-System Storage

#### A. Personal Knowledge Graph
```python
from claude.tools.personal_knowledge_graph import PersonalKnowledgeGraph

pkg = PersonalKnowledgeGraph()
conversation_node = pkg.add_node(
    node_type="DECISION",
    name=f"Conversation: {topic}",
    description=summary,
    attributes={
        "date": datetime.now().isoformat(),
        "topic": topic,
        "key_decisions": decisions_list,
        "action_items": action_items,
        "tags": tags,
        "context": additional_context
    },
    confidence=1.0,
    source_agent="Personal Assistant"
)
```

#### B. Conversation RAG (if available)
```python
from claude.tools.conversation_rag_ollama import ConversationRAG

rag = ConversationRAG()
rag.index_conversation(
    topic=topic,
    summary=summary,
    content=full_context,
    metadata={
        "date": datetime.now(),
        "tags": tags,
        "decisions": decisions_list
    }
)
```

#### C. Contextual Memory Update
```python
import sqlite3
db = sqlite3.connect("claude/data/contextual_memory_naythan.db")

# Log the interaction
db.execute("""
    INSERT INTO learning_interactions
    (interaction_type, context, timestamp)
    VALUES (?, ?, ?)
""", ("conversation_saved", json.dumps({"topic": topic, "tags": tags}), datetime.now()))
```

### Step 4: Verification
- Confirm save to all systems
- Test retrieval with semantic query
- Provide search examples for future use

## Example Usage

**User**: `/save-conversation`

**Maia**:
```
I'll help you save this conversation for future reference.

Please provide:
1. **Topic** (brief description):
```

**User**: `Team member discipline - inappropriate language from overwork`

**Maia**:
```
2. **Key Decisions/Recommendations** (main points):
```

**User**:
```
- Private 1:1 meeting approach
- Address behavior firmly while supporting workload
- Clear professional communication standards
- Document for HR escalation if needed
```

**Maia**:
```
3. **Tags** (keywords for future search, comma-separated):
```

**User**: `discipline, HR, management, communication, overwork, team-management`

**Maia**:
```
✅ Conversation saved successfully!

**Stored in**:
- Personal Knowledge Graph: Node ID abc123
- Contextual Memory: Interaction logged
- [Future] Conversation RAG: Indexed for semantic search

**Future Retrieval**:
You can find this conversation by asking:
- "What did we discuss about team discipline?"
- "How should I handle inappropriate language from team members?"
- "Show me past HR management conversations"

**Search via RAG** (when implemented):
python3 claude/tools/conversation_rag_ollama.py --query "discipline team member"
```

## Implementation Notes

### Required Tools
- `personal_knowledge_graph.py` (✅ exists)
- `contextual_memory_naythan.db` (✅ exists)
- `conversation_rag_ollama.py` (⏳ to be built in Phase 2)

### Graceful Degradation
If Conversation RAG not yet built:
- Save to Knowledge Graph only
- Log to Contextual Memory
- Note to user that full RAG search coming in Phase 2

### Privacy Considerations
- All storage is local (no cloud transmission)
- User controls what gets saved
- Can include sensitive HR/management discussions safely

## Future Enhancements

### Phase 2: Automated Detection
- Hook integration to detect important conversations
- Auto-prompt to save significant decisions
- Smart tagging based on content analysis

### Phase 3: Enhanced Retrieval
- Natural language conversation search
- Similarity matching ("Show similar situations")
- Time-based filtering ("Conversations from last month")
- Relationship mapping ("Related to Project X discussions")

## Related Commands
- `/load` - Load context for new session
- `save state` - Complete system state preservation
- (Future) `/search-conversations` - Query past conversations

## Model Selection
Use Sonnet (default) for conversation analysis and storage operations.

# Conversation RAG - Quick Start Guide

**Status**: ✅ Production Ready (Phase 101)
**Purpose**: Never lose important conversations again - save and retrieve past discussions using semantic search

---

## 🚀 Quick Start

### Save a Conversation (Interactive)
```bash
python3 claude/tools/conversation_rag_ollama.py --save
```

### Search Conversations
```bash
# Natural language search
python3 claude/tools/conversation_rag_ollama.py --query "discipline team member"

# Search with tag filter
python3 claude/tools/conversation_rag_ollama.py --query "management" --tags "HR,team-management"
```

### List Recent Conversations
```bash
python3 claude/tools/conversation_rag_ollama.py --list
```

### Get Full Conversation
```bash
python3 claude/tools/conversation_rag_ollama.py --get <conversation_id>
```

### View Statistics
```bash
python3 claude/tools/conversation_rag_ollama.py --stats
```

---

## 💡 Usage Examples

### Example 1: Save the Discipline Conversation (Already Done!)
```bash
✅ Saved: Team Member Discipline - Inappropriate Language from Overwork
📍 Location: ~/.maia/conversation_rag/
🏷️  Tags: discipline, HR, management, communication, overwork
```

### Example 2: Search by Topic
```bash
$ python3 claude/tools/conversation_rag_ollama.py --query "how to handle inappropriate language"

🔍 Found: Team Member Discipline - Inappropriate Language from Overwork
   Relevance: 43.8%
   Date: 2025-10-09
```

### Example 3: Search by Situation
```bash
$ python3 claude/tools/conversation_rag_ollama.py --query "overworked team member behavior"

🔍 Found: Team Member Discipline - Inappropriate Language from Overwork
   Relevance: 16.9%
```

---

## 🎯 When to Use This

**Save conversations when**:
- Making important decisions
- Receiving detailed recommendations
- Discussing people management issues
- Planning complex projects
- Learning new approaches/strategies
- Capturing meeting outcomes
- Documenting HR situations

**Don't save**:
- Simple Q&A exchanges
- Trivial information lookups
- Quick commands or tasks
- Routine operations

---

## 📋 Conversation Structure

### Required Fields
- **Topic**: Brief description (e.g., "Team Discipline Approach")
- **Summary**: Full context of the conversation
- **Key Decisions**: List of main recommendations/outcomes
- **Tags**: Keywords for search (comma-separated)

### Optional Fields
- **Context**: Additional background information
- **Action Items**: To-do list from conversation

---

## 🔍 Search Tips

### Natural Language Queries Work Best
- ❌ Bad: "discipline"
- ✅ Good: "how to handle team member discipline issues"

### Use Tags for Precision
```bash
--tags "HR,management"  # Only conversations with these tags
```

### Relevance Scores
- **>40%**: Highly relevant, primary topic match
- **20-40%**: Relevant, contextually related
- **10-20%**: Tangentially related
- **<10%**: Low relevance, may not be useful

---

## 📊 System Details

**Storage**: `~/.maia/conversation_rag/`
**Embedding Model**: nomic-embed-text (Ollama)
**Vector Database**: ChromaDB (persistent)
**Privacy**: 100% local processing (no cloud transmission)
**Performance**: ~0.05s per conversation embedding

---

## 🔧 Programmatic Usage

### Save from Python
```python
from claude.tools.conversation_rag_ollama import ConversationRAG

rag = ConversationRAG()

conv_id = rag.save_conversation(
    topic="Project Planning Session",
    summary="Discussed approach for new feature implementation...",
    key_decisions=[
        "Use phased rollout approach",
        "Start with MVP in 2 weeks",
        "Get user feedback before Phase 2"
    ],
    tags=["project-planning", "product", "mvp"],
    action_items=["Create wireframes", "Setup dev environment"]
)
```

### Search from Python
```python
results = rag.search("project planning approach", limit=5)

for result in results:
    print(f"{result['topic']} - {result['relevance']:.1%} relevant")
    print(f"Tags: {', '.join(result['tags'])}")
```

---

## 🎓 Integration with /save-conversation Command

The `/save-conversation` slash command provides a guided, interactive interface:

1. User types `/save-conversation`
2. Maia prompts for topic, decisions, tags
3. Automatically saves to both:
   - Personal Knowledge Graph
   - Conversation RAG (this system)
4. Provides retrieval examples

**Use the command for**: Easier, guided saving during conversations
**Use the CLI directly for**: Quick saves, programmatic integration, bulk operations

---

## 📈 Next Steps

1. ✅ **Save this conversation** about conversation RAG!
2. ✅ **Test retrieval** - Try searching for something we discussed
3. **Build habit** - Save important conversations as you go
4. **Future enhancement** - Automatic conversation detection (Phase 102)

---

## 🆘 Troubleshooting

### "Missing chromadb" Error
```bash
pip3 install chromadb
```

### "Ollama connection failed" Error
```bash
# Ensure Ollama is running
ollama serve

# Verify model is available
ollama pull nomic-embed-text
```

### Can't Find Saved Conversation
```bash
# Check stats to see if it was saved
python3 claude/tools/conversation_rag_ollama.py --stats

# List all conversations
python3 claude/tools/conversation_rag_ollama.py --list
```

---

**Built**: October 9, 2025 (Phase 101)
**Inspired by**: PAI/KAI integration lessons about conversation persistence
**Problem Solved**: "Yesterday we discussed X but I can't find it anymore"

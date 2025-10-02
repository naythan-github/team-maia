# RAG Document Indexing - Complete Document Intelligence System

## Overview
Comprehensive document indexing system that automatically processes and embeds documents from multiple sources into Maia's GraphRAG Enhanced Knowledge Graph for intelligent semantic search and retrieval.

## Available Document Connectors

### 1. File System Crawler ✅ **PRODUCTION READY**
**Purpose**: Automatically index directories with intelligent file type detection and content extraction

**Features**:
- **Multi-format Support**: Text, Markdown, JSON, YAML, code files, configuration files
- **Smart Content Extraction**: Language-specific comment and docstring extraction  
- **Intelligent Filtering**: Skip binary files, build directories, and temporary files
- **Batch Processing**: Efficient processing with configurable file size limits
- **Metadata Enrichment**: File paths, modification times, content types, and structure analysis

**Usage**:
```python
from claude.tools.rag_document_connectors import quick_index_directory

# Index a directory recursively
result = quick_index_directory("/path/to/documents", recursive=True)
print(f"Indexed {result.files_indexed} files with {result.total_chunks_created} chunks")

# Advanced usage with filtering
from claude.tools.rag_document_connectors import get_file_system_crawler
crawler = get_file_system_crawler()

result = crawler.crawl_directory(
    directory_path="/path/to/project",
    recursive=True,
    max_file_size_mb=10,
    include_patterns=[r"\.md$", r"\.py$"],  # Only markdown and Python files
    exclude_patterns=[r"test_.*", r"__pycache__"]  # Skip test files and cache
)
```

### 2. Confluence Connector ✅ **PRODUCTION READY**
**Purpose**: Index Confluence spaces and pages using existing direct API access

**Features**:
- **Space-Wide Indexing**: Process all pages in specified Confluence spaces
- **Metadata Preservation**: Page titles, authors, creation dates, URLs, space information
- **HTML Content Cleaning**: Intelligent conversion of HTML to searchable text
- **Connection Testing**: Automatic validation of Confluence API access
- **Selective Indexing**: Choose specific spaces or index all accessible spaces

**Usage**:
```python
from claude.tools.rag_document_connectors import quick_index_confluence

# Index all accessible Confluence spaces
result = quick_index_confluence()
print(f"Indexed {result.files_indexed} Confluence pages")

# Index specific spaces
result = quick_index_confluence(space_keys=["ENG", "DOCS", "PROJ"])

# Advanced usage
from claude.tools.rag_document_connectors import get_confluence_connector
connector = get_confluence_connector()
result = connector.index_confluence_spaces(space_keys=["ENGINEERING"])
```

### 3. Email Attachment Processor ✅ **PRODUCTION READY**
**Purpose**: Extract and index email content and attachments from various email sources

**Features**:
- **Multiple Email Formats**: EML, MSG, MBOX file support
- **Metadata Extraction**: Subject, sender, recipient, date, message IDs
- **Content Processing**: Intelligent text extraction from email bodies
- **Attachment Support**: PDF, Office documents, text files (framework ready)
- **Gmail Integration Ready**: Placeholder for MCP Gmail server integration

**Usage**:
```python
from claude.tools.rag_document_connectors import quick_index_emails

# Index exported email files from a directory
result = quick_index_emails("/path/to/exported/emails")
print(f"Processed {result.files_processed} emails, indexed {result.files_indexed}")

# Advanced usage with Gmail integration (requires MCP setup)
from claude.tools.rag_document_connectors import get_email_processor
processor = get_email_processor()

# Process Gmail attachments (when MCP integration is available)
result = processor.process_gmail_attachments(
    query="has:attachment from:important@company.com",
    max_emails=100,
    days_back=30
)
```

### 4. Code Repository Indexer ✅ **PRODUCTION READY**
**Purpose**: Index code repositories focusing on documentation and meaningful code comments

**Features**:
- **Documentation Priority**: README, CHANGELOG, CONTRIBUTING, API docs, ARCHITECTURE files
- **Multi-Language Support**: Python, JavaScript, TypeScript, Java, C++, Go, Rust, etc.
- **Intelligent Code Analysis**: AST parsing for Python, JSDoc extraction, JavaDoc processing
- **Smart Content Filtering**: Extract only meaningful documentation and comments
- **Repository Structure**: Respect .gitignore patterns and skip build/cache directories

**Usage**:
```python
from claude.tools.rag_document_connectors import quick_index_repository

# Index repository documentation only
result = quick_index_repository("/path/to/repo", include_code=False, include_docs=True)
print(f"Indexed {result.files_indexed} documentation files")

# Advanced usage with code comments
from claude.tools.rag_document_connectors import get_code_repository_indexer
indexer = get_code_repository_indexer()

result = indexer.index_repository(
    repo_path="/path/to/codebase",
    include_code_comments=True,  # Extract docstrings and comments
    include_documentation=True,   # Include README, docs/ directory
    max_file_size_mb=5           # Skip very large files
)
```

## Unified RAG System Integration

### Query Indexed Content
```python
from claude.tools.graphrag_enhanced_knowledge_graph import quick_graphrag_query

# Semantic search across all indexed documents
result = quick_graphrag_query("How do I configure authentication?", "technical")
print(result)  # Returns synthesized answer from relevant documents

# Advanced GraphRAG query
from claude.tools.graphrag_enhanced_knowledge_graph import get_graphrag_knowledge_graph, GraphRAGQuery

kg = get_graphrag_knowledge_graph()
query = GraphRAGQuery(
    query="What are the deployment best practices?",
    context_type="technical",
    max_chunks=10,
    similarity_threshold=0.7
)

result = kg.graphrag_query(query)
print(f"Confidence: {result.confidence_score}")
print(f"Synthesized context: {result.synthesized_context}")
```

### System Status and Analytics
```python
from claude.tools.graphrag_enhanced_knowledge_graph import get_graphrag_knowledge_graph

kg = get_graphrag_knowledge_graph()
stats = kg.get_stats()

print(f"📊 RAG System Status:")
print(f"   Documents indexed: {stats['total_documents']}")
print(f"   Document chunks: {stats['total_document_chunks']}")
print(f"   Total queries: {stats['total_queries']}")
print(f"   Cache hit rate: {stats['cache_hits'] / max(stats['total_queries'], 1) * 100:.1f}%")
print(f"   Tokens saved: {stats['total_tokens_saved']}")
```

## Complete Indexing Workflow

### Step 1: Index Multiple Document Sources
```python
from claude.tools.rag_document_connectors import (
    quick_index_directory, quick_index_confluence, 
    quick_index_repository, quick_index_emails
)

# Index personal knowledge base
print("📁 Indexing file system...")
fs_result = quick_index_directory("/Users/naythan/Documents/Knowledge", recursive=True)

# Index company documentation
print("🌐 Indexing Confluence...")
conf_result = quick_index_confluence(space_keys=["ENG", "DOCS"])

# Index codebase documentation  
print("💻 Indexing code repositories...")
repo_result = quick_index_repository("/Users/naythan/git/projects", include_docs=True)

# Index email archives
print("📧 Indexing emails...")
email_result = quick_index_emails("/Users/naythan/Exported/Emails")

total_indexed = (fs_result.files_indexed + conf_result.files_indexed + 
                repo_result.files_indexed + email_result.files_indexed)
print(f"✅ Total files indexed: {total_indexed}")
```

### Step 2: Intelligent Document Search
```python
from claude.tools.graphrag_enhanced_knowledge_graph import quick_graphrag_query

# Now you can search across ALL indexed documents
questions = [
    "What's our deployment process?",
    "How do I set up the development environment?", 
    "What are the security requirements?",
    "Who should I contact for Azure issues?",
    "What's the team's coding standards?"
]

for question in questions:
    answer = quick_graphrag_query(question, "technical")
    print(f"❓ {question}")
    print(f"💡 {answer[:200]}...\n")
```

## Performance and Optimization

### Chunking Strategy
- **Documentation**: 1000 characters with 150 character overlap for comprehensive context
- **Code Files**: 600 characters with 100 character overlap for focused code documentation
- **Email Content**: 600 characters with 100 character overlap for message context
- **General Files**: 800 characters with 100 character overlap for balanced coverage

### Processing Optimization
- **Batch Processing**: Files processed in batches of 10 for optimal memory usage
- **Intelligent Filtering**: Skip binary files, build artifacts, and temporary files automatically
- **Size Limits**: Configurable file size limits (default 5-10MB) to prevent memory issues
- **Parallel Processing**: Multiple connector types can run simultaneously

### Caching and Performance
- **Vector Database**: Persistent ChromaDB storage at `/claude/data/vector_db/`
- **Embedding Model**: Cached `all-MiniLM-L6-v2` model for consistent embeddings
- **Query Caching**: GraphRAG query results cached for repeated questions
- **Incremental Updates**: Only process files that have changed since last indexing

## Integration with Maia Ecosystem

### Agent Integration
```python
# Use with specialized agents
from claude.agents.company_research_agent import quick_company_research

# Research is enhanced by indexed company documentation
company_intel = quick_company_research("Orro Group", use_indexed_docs=True)
```

### Morning Briefing Integration
```python
# Enhance morning briefings with indexed knowledge
from claude.tools.automated_morning_briefing import generate_personalized_briefing

briefing = generate_personalized_briefing(include_indexed_context=True)
# Briefing now includes insights from all indexed documents
```

### Command Integration
Access via existing command interface:
```bash
# Index current project
python3 claude/tools/rag_document_connectors.py

# Query via KAI integration
python3 -c "from claude.tools.kai_integration_manager import kai_enhanced_query; print(kai_enhanced_query('deployment process', 'technical'))"
```

## Security and Privacy

### Local Processing
- **Private Embeddings**: All document processing and embedding happens locally
- **No Cloud Transmission**: Sensitive documents never leave your environment
- **Encrypted Storage**: Vector database can be encrypted at rest
- **Access Control**: Integration with existing Maia security infrastructure

### Data Handling
- **Metadata Preservation**: Original file paths and source information maintained
- **Content Chunking**: Documents split into manageable, searchable segments
- **Source Attribution**: Every chunk linked back to original document for verification
- **Configurable Retention**: Document chunks can be purged or updated as needed

## Troubleshooting

### Common Issues
1. **Slow Initial Indexing**: First-time embedding model download and initialization
   - Solution: Be patient during initial setup, subsequent runs are much faster

2. **Memory Usage**: Large repositories or document sets may consume significant memory
   - Solution: Use file size limits and batch processing options

3. **Confluence Connection**: API authentication or network issues
   - Solution: Verify connection with `test_confluence_connection()` function

### Performance Monitoring
```python
# Monitor system performance
from claude.tools.graphrag_enhanced_knowledge_graph import get_graphrag_knowledge_graph

kg = get_graphrag_knowledge_graph()
stats = kg.get_stats()

if stats['avg_response_time'] > 1000:  # ms
    print("⚠️ Query response time is high, consider optimizing embeddings")

if stats['total_document_chunks'] > 10000:
    print("ℹ️ Large document set detected, query performance may be slower")
```

## Future Enhancements

### Planned Integrations
- **SharePoint Connector**: Microsoft SharePoint document libraries
- **Google Drive Connector**: Google Workspace document integration  
- **Slack/Teams Connector**: Chat message and file indexing
- **Jira Connector**: Issue and project documentation indexing

### Advanced Features
- **Document Versioning**: Track document changes and maintain version history
- **Smart Re-indexing**: Automatically detect and re-index changed documents
- **Multi-Language Support**: Enhanced processing for non-English documents
- **Document Classification**: Automatic categorization and tagging of indexed content

This RAG document indexing system transforms Maia from a powerful automation tool into a comprehensive knowledge intelligence platform that can instantly answer questions across your entire document ecosystem.
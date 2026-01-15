# Personal Information Operating System (PIOS)

## Project Overview

**Project Name**: Personal Information Operating System (PIOS)
**Version**: 1.0 Draft
**Created**: 2025-12-17
**Author**: AI Specialists Agent + User collaboration
**Status**: Planning

**Vision**: Transform scattered digital information (downloads, emails, documents, meetings) into an interconnected knowledge graph that automatically extracts entities, infers relationships, and surfaces proactive insights.

**Core Principle**: Every piece of information you touch becomes connected. Your knowledge compounds instead of scatters.

---

## Problem Statement

### Current State Issues

1. **Downloads are siloed**: Files land in Downloads, get moved to folders, but remain disconnected islands
2. **No entity extraction**: CVs, JDs, invoices contain rich entities (people, companies, skills) that aren't captured
3. **No relationship mapping**: A CV from a recruiter has no link to the email thread, the JD, or the interview
4. **Manual organization**: User must manually classify and route documents
5. **No proactive intelligence**: System doesn't surface insights like "this candidate matches 3 JDs"
6. **Broken infrastructure**: Current Downloads watchers pointing to wrong paths (`~/git/maia/` vs `~/maia/`)

### User's Download Patterns (from history)

| Category | Examples | Volume |
|----------|----------|--------|
| CVs/Talent Packs | Vikrant Slathia, Wayne Ash, Paul Roberts, Samuel Nou, Taylor Barkle | 6+ |
| Job Descriptions | Senior IDAM Engineer, Senior EndPoint Engineer | 2+ |
| Invoices | Invoice-FYZ5VQI5-0006.pdf | 1+ |
| Emails (.eml) | Monthly audits, invoicing, meeting updates, project discussions | 15+ |
| Policy Documents | POL005 BYOD Security Policy | 1+ |
| Data Exports | Intune_Customers.xlsx, offboarding.xlsx, onboarding.xlsx | 5+ |
| MSP Exports | IT Glue exports (7z), Kaseya policies (XML) | 4+ |
| Meeting Transcripts | VTT files | Ongoing |

---

## Existing Infrastructure (Assets to Leverage)

### Knowledge Graph Foundation
- **File**: `claude/tools/personal_knowledge_graph.py` (922 lines)
- **Status**: Built, functional
- **Capabilities**:
  - Node types: PERSON, COMPANY, JOB, SKILL, PROJECT, GOAL, PREFERENCE, DECISION, OUTCOME, PATTERN, DOMAIN, CONCEPT, RELATIONSHIP, EVENT, LOCATION
  - Relationship types: WORKS_AT, APPLIED_TO, HAS_SKILL, REQUIRES_SKILL, PREFERS, LEADS_TO, INFLUENCES, SIMILAR_TO, PART_OF, DEPENDS_ON, ACHIEVED, FAILED_AT, LEARNED_FROM, CONNECTED_TO, LOCATED_IN, CAUSED_BY, CORRELATES_WITH, OPTIMIZES
  - Semantic search with embeddings
  - Pattern detection
  - Agent context enrichment
  - Decision outcome tracking

### ChromaDB RAG Databases
| Database | Location | Purpose |
|----------|----------|---------|
| cv_rag | `claude/data/rag_databases/cv_rag/` | CV semantic search |
| email_rag_ollama | `claude/data/rag_databases/email_rag_ollama/` | Email search |
| interview_rag | `claude/data/rag_databases/interview_rag/` | Interview transcript search |
| meeting_transcripts_rag | `claude/data/rag_databases/meeting_transcripts_rag/` | Meeting search |
| conversation_memory_rag | `claude/data/rag_databases/conversation_memory_rag/` | Conversation memory |
| analysis_patterns | `claude/data/rag_databases/analysis_patterns/` | Pattern library |

### Intelligence Databases
| Database | Size | Purpose |
|----------|------|---------|
| interview_search.db | 5.7MB | Interview/candidate data |
| stakeholder_intelligence.db | 28KB | Stakeholder relationships |
| decision_intelligence.db | 24KB | Decision tracking |
| adaptive_routing.db | 32KB | Agent routing |
| outcome_tracker.db | 40KB | Outcome tracking |

### Interview Pipeline Tools
| Tool | Location | Purpose |
|------|----------|---------|
| cv_parser.py | `claude/tools/interview/` | Parse CVs → skills, certs, experience |
| cv_search_enhanced.py | `claude/tools/interview/` | ChromaDB semantic CV search |
| dual_source_matcher.py | `claude/tools/interview/` | CV + Interview verification |
| interview_analyst.py | `claude/tools/interview/` | JD → Interview fit scoring |
| evidence_analyzer.py | `claude/tools/interview/` | Evidence extraction |
| requirement_matcher.py | `claude/tools/interview/` | Requirement matching |

### Finance Tools
| Tool | Location | Purpose |
|------|----------|---------|
| receipt_processor.py | `claude/tools/finance/` | Invoice/receipt extraction |
| donut_receipt_extractor.py | `claude/tools/finance/` | AI-powered receipt OCR |
| receipt_ocr.py | `claude/tools/finance/` | OCR extraction |
| vision_ocr.py | `claude/tools/finance/` | Vision-based OCR |

### Document Tools
| Tool | Location | Purpose |
|------|----------|---------|
| convert_md_to_docx.py | `claude/tools/document_conversion/` | Markdown to DOCX |
| meeting_intelligence_processor.py | `claude/tools/` | VTT intelligence |
| it_glue_data_scanner.py | `claude/tools/` | MSP data pattern detection |

### Current Downloads Infrastructure (BROKEN)
| Component | Status | Issue |
|-----------|--------|-------|
| intelligent_downloads_router.py | Exists | Path mismatch in LaunchAgent |
| downloads_vtt_mover.py | Exists | Path mismatch, duplicates router functionality |
| organize_downloads.py | Exists | Path mismatch |
| LaunchAgents (3) | All Exit Code 2 | Point to `~/git/maia/` instead of `~/maia/` |

---

## Target Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PERSONAL INFORMATION OPERATING SYSTEM                    │
└─────────────────────────────────────────────────────────────────────────────┘

                              INPUT LAYER
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │Downloads│ │  Email  │ │ Calendar│ │ Browser │ │Meetings │ │  Notes  │ │
│  │ Watcher │ │ Sync    │ │  Sync   │ │ History │ │  VTT    │ │  Sync   │ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ │
└───────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┘
        └──────────┴──────────┴──────────┴──────────┴──────────┴─────┐
                                                                      │
                              INTELLIGENCE LAYER                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   Document      │  │    Entity       │  │  Relationship   │            │
│  │   Classifier    │  │   Extractor     │  │   Inferencer    │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   Summarizer    │  │ Action Item     │  │   Sentiment     │            │
│  │                 │  │   Extractor     │  │   Analyzer      │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                              STORAGE LAYER                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    KNOWLEDGE GRAPH (SQLite)                          │   │
│  │  Nodes: Person, Company, Job, Skill, Project, Document, Email, Event│   │
│  │  Relationships: 20+ types                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    VECTOR DATABASES (ChromaDB)                       │   │
│  │  cv_rag │ email_rag │ interview_rag │ meeting_rag │ document_rag   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    STRUCTURED DATA (SQLite)                          │   │
│  │  document_lifecycle.db │ email_threads.db │ interview_search.db     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FILE SYSTEM (Organized)                           │   │
│  │  ~/Documents/{Recruitment,Finance,Projects,Policies,Archive}/       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                              INSIGHT LAYER                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   Pattern       │  │   Proactive     │  │   Anomaly       │            │
│  │   Detection     │  │   Suggestions   │  │   Detection     │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                              INTERFACE LAYER                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   CLI Queries   │  │   Notifications │  │   Dashboards    │            │
│  │   (Maia)        │  │   (macOS)       │  │   (Web/HTML)    │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### Phase 0: Fix Existing Infrastructure

**Objective**: Get current Downloads watchers working

**Tasks**:
1. Update LaunchAgent plist paths: `~/git/maia/` → `~/maia/`
2. Update hardcoded paths in Python scripts
3. Consolidate redundant watchers (downloads_vtt_mover duplicates intelligent_downloads_router)
4. Reload LaunchAgents and verify

**Files to modify**:
- `/Users/YOUR_USERNAME/Library/LaunchAgents/com.maia.intelligent-downloads-router.plist`
- `/Users/YOUR_USERNAME/Library/LaunchAgents/com.maia.downloads-vtt-mover.plist`
- `/Users/YOUR_USERNAME/Library/LaunchAgents/com.maia.downloads-organizer-scheduler.plist`
- `claude/tools/intelligent_downloads_router.py` (internal paths)
- `claude/tools/downloads_vtt_mover.py` (internal paths)
- `claude/commands/organize_downloads.py` (internal paths)

---

### Phase 1: Universal Document Intelligence Service

**Objective**: LLM-powered document understanding that classifies, extracts entities, and infers relationships

**Location**: `claude/tools/pios/universal_document_intelligence.py`

**Class Structure**:
```python
class UniversalDocumentIntelligence:
    """
    Core intelligence service for document understanding
    """

    def __init__(self, ollama_model: str = "llama3.2"):
        self.ollama_model = ollama_model
        self.text_extractors = {
            'pdf': PDFExtractor(),
            'docx': DOCXExtractor(),
            'eml': EMLExtractor(),
            'txt': TXTExtractor(),
            'xlsx': XLSXExtractor(),
            'csv': CSVExtractor(),
        }

    def process(self, file_path: Path) -> DocumentIntelligence:
        """Main entry point for document processing"""
        pass

    def classify_document(self, file_path: Path, text: str) -> DocumentClassification:
        """Classify document type using LLM"""
        pass

    def extract_text(self, file_path: Path) -> str:
        """Extract text from any supported format"""
        pass

    def extract_entities(self, text: str, doc_type: str) -> List[Entity]:
        """Extract entities using LLM"""
        pass

    def infer_relationships(self, entities: List[Entity], doc_type: str) -> List[Relationship]:
        """Infer relationships between entities"""
        pass
```

**Document Types to Support**:
| Type | Detection Patterns | Entity Focus |
|------|-------------------|--------------|
| CV/Resume | "Talent Pack", "CV", "Resume", skills list | Person, Skills, Certifications, Companies |
| Job Description | "Engineer -", "Lead -", requirements sections | Job, Skills Required, Company |
| Invoice | "Invoice", "INV-", amounts, dates | Vendor, Amount, Date, Line Items |
| Email | .eml extension, headers | People (From/To), Topics, Actions |
| Policy | "POL", "Policy", section numbers | Policy Name, Requirements, Compliance |
| Contract | "Agreement", "Contract", clauses | Parties, Terms, Dates, Obligations |
| Meeting Transcript | .vtt extension | Attendees, Topics, Action Items |
| Data Export | .xlsx, .csv with structured data | Depends on content |

**Entity Extraction Prompt Template**:
```
You are an entity extraction system. Given a {document_type}, extract all entities.

Document content:
{text}

Extract entities in this JSON format:
{
  "entities": [
    {
      "type": "PERSON|COMPANY|SKILL|JOB|PROJECT|...",
      "name": "entity name",
      "attributes": {
        "key": "value"
      },
      "confidence": 0.0-1.0
    }
  ],
  "relationships": [
    {
      "source": "entity name",
      "target": "entity name",
      "type": "HAS_SKILL|WORKS_AT|APPLIED_TO|...",
      "strength": 0.0-1.0
    }
  ]
}

Focus on {entity_focus} for this document type.
```

**Output Data Model**:
```python
@dataclass
class Entity:
    type: str           # NodeType enum value
    name: str
    description: str
    attributes: Dict[str, Any]
    confidence: float
    source_span: Tuple[int, int]  # Character positions in original text

@dataclass
class Relationship:
    source_entity: str
    target_entity: str
    type: str           # RelationshipType enum value
    strength: float
    attributes: Dict[str, Any]

@dataclass
class DocumentClassification:
    document_type: str
    confidence: float
    detected_patterns: List[str]

@dataclass
class DocumentIntelligence:
    file_path: Path
    document_type: DocumentClassification
    extracted_text: str
    entities: List[Entity]
    relationships: List[Relationship]
    summary: str
    action_items: List[str]
    processed_at: datetime
    processing_time_ms: int
```

**Test Cases**:
1. CV classification and entity extraction
2. JD classification and requirements extraction
3. Invoice data extraction
4. Email entity extraction (people, topics)
5. Policy document extraction
6. Unknown document type handling
7. Empty/corrupted file handling
8. Large file handling (>10MB)

---

### Phase 2: Knowledge Graph Connector

**Objective**: Bridge Universal Document Intelligence to existing Knowledge Graph

**Location**: `claude/tools/pios/knowledge_graph_connector.py`

**Class Structure**:
```python
class KnowledgeGraphConnector:
    """
    Bridges document intelligence to PersonalKnowledgeGraph
    """

    def __init__(self):
        self.doc_intel = UniversalDocumentIntelligence()
        self.kg = get_knowledge_graph()
        self.rag_indexer = RAGIndexer()

    def process_document(self, file_path: Path) -> ProcessingResult:
        """Process document and update knowledge graph"""
        pass

    def create_or_update_nodes(self, entities: List[Entity]) -> Dict[str, str]:
        """Create/update nodes, return name->node_id mapping"""
        pass

    def create_relationships(self, relationships: List[Relationship], node_map: Dict[str, str]):
        """Create relationships between nodes"""
        pass

    def index_to_rag(self, file_path: Path, doc_intel: DocumentIntelligence):
        """Index document to appropriate ChromaDB collection"""
        pass

    def find_related_documents(self, doc_intel: DocumentIntelligence) -> List[RelatedDocument]:
        """Find existing documents related to this one"""
        pass
```

**Node Mapping Rules**:
| Entity Type | Knowledge Graph NodeType | Dedup Strategy |
|-------------|-------------------------|----------------|
| Person | NodeType.PERSON | Name + context matching |
| Company | NodeType.COMPANY | Name normalization |
| Skill | NodeType.SKILL | Canonical skill names |
| Job | NodeType.JOB | Title + Company |
| Project | NodeType.PROJECT | Name + date range |
| Certification | NodeType.SKILL (with cert attribute) | Cert code |

**RAG Routing**:
| Document Type | ChromaDB Collection |
|---------------|---------------------|
| CV/Resume | cv_rag |
| Job Description | cv_rag (same collection for matching) |
| Email | email_rag_ollama |
| Meeting Transcript | meeting_transcripts_rag |
| Invoice | document_rag (new) |
| Policy | document_rag |
| Contract | document_rag |

**Test Cases**:
1. Entity deduplication (same person, different documents)
2. Relationship strength accumulation
3. RAG indexing per document type
4. Cross-document relationship detection
5. Node update vs create logic
6. Rollback on failure

---

### Phase 3: Document Lifecycle Manager

**Objective**: Manage document state from arrival through archival

**Location**: `claude/tools/pios/document_lifecycle_manager.py`

**Database Schema** (`document_lifecycle.db`):
```sql
CREATE TABLE documents (
    document_id TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    current_filename TEXT NOT NULL,
    current_path TEXT NOT NULL,

    -- Classification
    document_type TEXT NOT NULL,
    classification_confidence REAL,

    -- Lifecycle state
    state TEXT NOT NULL,  -- ARRIVED, PROCESSING, INDEXED, ROUTED, ACTIVE, ARCHIVED
    arrived_at TEXT NOT NULL,
    processed_at TEXT,
    indexed_at TEXT,
    routed_at TEXT,
    last_accessed TEXT,

    -- Content tracking
    content_hash TEXT NOT NULL,  -- SHA256
    file_size_bytes INTEGER,

    -- Source tracking
    source_type TEXT,  -- download, email_attachment, manual
    source_email_id TEXT,
    source_url TEXT,

    -- Knowledge graph links
    entity_node_ids TEXT,  -- JSON array
    relationship_ids TEXT, -- JSON array

    -- RAG links
    chroma_collection TEXT,
    chunk_ids TEXT,  -- JSON array

    -- Relationships
    related_document_ids TEXT,  -- JSON array
    parent_thread_id TEXT,
    project_id TEXT
);

CREATE TABLE document_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- CREATED, MOVED, RENAMED, INDEXED, ARCHIVED
    event_data TEXT,  -- JSON
    timestamp TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

CREATE INDEX idx_documents_state ON documents(state);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_hash ON documents(content_hash);
CREATE INDEX idx_history_document ON document_history(document_id);
```

**Document States**:
```
ARRIVED → PROCESSING → INDEXED → ROUTED → ACTIVE → ARCHIVED
                ↓
            FAILED (quarantine)
                ↓
            DUPLICATE (skip)
```

**Routing Rules**:
| Document Type | Destination | Naming Convention |
|---------------|-------------|-------------------|
| CV | ~/Documents/Recruitment/CVs/{YYYY-MM}/ | {Name}_{Role}_{Date}.pdf |
| JD | ~/Documents/Recruitment/JDs/ | {Role}_{Company}_{Date}.docx |
| Invoice | ~/Documents/Finance/Invoices/{YYYY}/ | {Vendor}_{InvoiceNum}_{Date}.pdf |
| Policy | ~/Documents/Policies/ | {PolicyCode}_{Name}_{Version}.pdf |
| Email | ~/Documents/Email_Archive/{YYYY-MM}/ | {Subject}_{Date}.eml |
| Meeting | ~/Documents/VTT/ | {Meeting}_{Date}.vtt |
| Contract | ~/Documents/Finance/Contracts/ | {Parties}_{Type}_{Date}.pdf |

**Test Cases**:
1. State transitions (happy path)
2. Duplicate detection via content hash
3. Failed processing → quarantine
4. Routing to correct destination
5. Naming convention application
6. History tracking
7. Rollback on move failure

---

### Phase 4: Email Integration

**Objective**: Process incoming/outgoing emails, extract entities, track threads

**Location**: `claude/tools/pios/email_integration.py`

**Components**:
1. **Email Watcher**: Monitor for new .eml files OR integrate with M365 API
2. **Email Parser**: Extract headers, body, attachments
3. **Thread Tracker**: Group related emails, track conversation state
4. **Attachment Processor**: Route attachments through document pipeline

**Email Thread Schema** (`email_threads.db`):
```sql
CREATE TABLE email_threads (
    thread_id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    participants TEXT NOT NULL,  -- JSON array of email addresses

    -- Thread state
    email_count INTEGER DEFAULT 0,
    first_email_at TEXT,
    last_email_at TEXT,

    -- Intelligence
    detected_topics TEXT,  -- JSON array
    sentiment_trend TEXT,  -- positive, negative, neutral
    action_items TEXT,     -- JSON array

    -- Relationships
    project_id TEXT,
    related_document_ids TEXT,  -- JSON array

    -- Knowledge graph
    entity_node_ids TEXT   -- JSON array
);

CREATE TABLE emails (
    email_id TEXT PRIMARY KEY,
    thread_id TEXT,

    -- Headers
    message_id TEXT,
    from_address TEXT NOT NULL,
    to_addresses TEXT NOT NULL,  -- JSON array
    cc_addresses TEXT,
    subject TEXT,
    date TEXT NOT NULL,

    -- Content
    body_text TEXT,
    body_html TEXT,

    -- Attachments
    attachment_ids TEXT,  -- JSON array (links to documents table)

    -- Intelligence
    detected_entities TEXT,  -- JSON array
    action_items TEXT,       -- JSON array
    sentiment TEXT,

    -- State
    direction TEXT,  -- INCOMING, OUTGOING
    processed_at TEXT,

    FOREIGN KEY (thread_id) REFERENCES email_threads(thread_id)
);

CREATE INDEX idx_emails_thread ON emails(thread_id);
CREATE INDEX idx_emails_from ON emails(from_address);
CREATE INDEX idx_emails_date ON emails(date);
```

**Thread Intelligence Features**:
- Topic extraction across thread
- Sentiment trend analysis
- Action item extraction and tracking
- Participant relationship mapping
- Response time tracking

**Test Cases**:
1. Email parsing (headers, body, attachments)
2. Thread grouping by subject/references
3. Attachment routing to document pipeline
4. Entity extraction from email body
5. Action item extraction
6. Outgoing email tracking
7. Thread sentiment analysis

---

### Phase 5: Proactive Insights Engine

**Objective**: Automatically surface insights when documents are processed

**Location**: `claude/tools/pios/proactive_insights.py`

**Insight Types**:
| Insight Type | Trigger | Example |
|--------------|---------|---------|
| CANDIDATE_MATCH | CV processed | "This CV matches 3 JDs at 85%+" |
| SIMILAR_DOCUMENT | Any document | "Similar to Wayne Ash CV (hired)" |
| SPENDING_PATTERN | Invoice processed | "3rd invoice from Moir this quarter" |
| THREAD_STALLED | Email thread | "No response in 3 days" |
| ACTION_DUE | Action item | "Follow up with Millenium by Friday" |
| RELATIONSHIP_STRENGTH | Email sent | "You've contacted this person 8 times" |
| CONTRACT_EXPIRY | Contract processed | "Related contract expires in 30 days" |
| DUPLICATE_DETECTED | Any document | "This appears to be a duplicate of..." |

**Insight Data Model**:
```python
@dataclass
class Insight:
    insight_id: str
    insight_type: str
    title: str
    description: str
    confidence: float

    # Related entities
    source_document_id: str
    related_entity_ids: List[str]
    related_document_ids: List[str]

    # Actions
    suggested_actions: List[str]
    action_urls: List[str]  # Deep links

    # Display
    priority: str  # HIGH, MEDIUM, LOW
    icon: str

    created_at: datetime
    expires_at: datetime  # Some insights are time-sensitive
```

**Notification Channels**:
1. macOS Notification Center
2. CLI output (when interactive)
3. Dashboard (if running)
4. Log file (always)

**Test Cases**:
1. Candidate match detection
2. Similar document detection
3. Spending pattern detection
4. Thread stall detection
5. Action item due detection
6. Notification delivery
7. Insight expiration

---

### Phase 6: Unified Query Interface

**Objective**: Single interface for cross-system queries

**Location**: `claude/tools/pios/unified_query.py`

**Query Types**:
```python
class QueryType(Enum):
    ENTITY_SEARCH = "entity"      # "Who has Azure skills?"
    DOCUMENT_SEARCH = "document"  # "Find all CVs from last month"
    RELATIONSHIP = "relationship" # "What's connected to Project X?"
    SEMANTIC = "semantic"         # "What did we discuss about budget?"
    AGGREGATE = "aggregate"       # "Total spending on recruitment Q4"
```

**Query Examples**:
| Natural Language Query | Parsed Query | Data Sources |
|----------------------|--------------|--------------|
| "Who has Azure AZ-305 cert?" | entity:skill:AZ-305 | Knowledge Graph |
| "Match candidates to Pod Lead JD" | relationship:job:candidates | KG + cv_rag |
| "What did we discuss with Millenium?" | semantic:project:Millenium | meeting_rag + email_rag |
| "Total recruitment spend Q4 2025" | aggregate:finance:recruitment:Q4-2025 | document_lifecycle.db |
| "Documents related to BYOD policy" | relationship:document:POL005 | KG + document_rag |
| "Show me Vikrant's interview vs CV" | entity:person:Vikrant:comparison | interview_rag + cv_rag |

**Query Router**:
```python
class UnifiedQueryRouter:
    def __init__(self):
        self.kg = get_knowledge_graph()
        self.rag_collections = {
            'cv': ChromaDBClient('cv_rag'),
            'email': ChromaDBClient('email_rag_ollama'),
            'meeting': ChromaDBClient('meeting_transcripts_rag'),
            'document': ChromaDBClient('document_rag'),
        }
        self.lifecycle_db = DocumentLifecycleDB()

    def query(self, natural_language: str) -> QueryResult:
        """Route natural language query to appropriate backends"""
        pass

    def parse_query(self, query: str) -> ParsedQuery:
        """Use LLM to parse natural language into structured query"""
        pass

    def execute_entity_search(self, parsed: ParsedQuery) -> List[Entity]:
        """Search knowledge graph for entities"""
        pass

    def execute_semantic_search(self, parsed: ParsedQuery) -> List[Document]:
        """Search RAG databases semantically"""
        pass

    def execute_aggregate(self, parsed: ParsedQuery) -> AggregateResult:
        """Run aggregation queries"""
        pass
```

**Test Cases**:
1. Entity search queries
2. Semantic search queries
3. Relationship queries
4. Aggregate queries
5. Multi-source queries
6. Query parsing accuracy
7. Result ranking

---

### Phase 7: Dashboard and Notifications

**Objective**: User-facing insights display

**Components**:
1. **macOS Notifications**: Real-time alerts for high-priority insights
2. **CLI Dashboard**: Terminal-based status display
3. **HTML Dashboard**: Web-based comprehensive view

**Dashboard Sections**:
- Recent Documents (last 24h)
- Pending Actions
- Active Insights
- Knowledge Graph Stats
- Processing Queue
- System Health

---

## Folder Structure

```
claude/tools/pios/
├── __init__.py
├── universal_document_intelligence.py    # Phase 1
├── text_extractors/
│   ├── __init__.py
│   ├── pdf_extractor.py
│   ├── docx_extractor.py
│   ├── eml_extractor.py
│   ├── xlsx_extractor.py
│   └── base_extractor.py
├── knowledge_graph_connector.py          # Phase 2
├── document_lifecycle_manager.py         # Phase 3
├── email_integration.py                  # Phase 4
├── proactive_insights.py                 # Phase 5
├── unified_query.py                      # Phase 6
├── notifications.py                      # Phase 7
├── dashboard/
│   ├── cli_dashboard.py
│   └── html_dashboard.py
└── tests/
    ├── test_document_intelligence.py
    ├── test_knowledge_graph_connector.py
    ├── test_document_lifecycle.py
    ├── test_email_integration.py
    ├── test_proactive_insights.py
    └── test_unified_query.py

claude/data/databases/intelligence/
├── document_lifecycle.db                 # Phase 3
├── email_threads.db                      # Phase 4
└── [existing databases...]

claude/data/rag_databases/
├── document_rag/                         # New - general documents
└── [existing databases...]
```

---

## Build Sequence (Dependency Order)

| Phase | Component | Effort | Dependencies | Enables |
|-------|-----------|--------|--------------|---------|
| **0** | Fix Downloads Infrastructure | 1 day | None | Basic functionality |
| **1** | Universal Document Intelligence | 3-5 days | Ollama | All document processing |
| **2** | Knowledge Graph Connector | 2-3 days | Phase 1, existing KG | Entity relationships |
| **3** | Document Lifecycle Manager | 2-3 days | Phase 2 | Routing, archiving |
| **4** | Email Integration | 3-4 days | Phase 2-3 | Communication graph |
| **5** | Proactive Insights Engine | 2-3 days | Phase 2-4 | Automatic intelligence |
| **6** | Unified Query Interface | 2-3 days | Phase 2-5 | Cross-system queries |
| **7** | Dashboard/Notifications | 2-3 days | Phase 6 | User-facing insights |

**Total Estimated Effort**: 17-25 days

---

## Success Criteria

### Phase 1 Success
- [ ] Document classification accuracy >90%
- [ ] Entity extraction recall >85%
- [ ] Processing time <5s for typical documents
- [ ] Supports PDF, DOCX, EML, TXT, XLSX, CSV

### Phase 2 Success
- [ ] Entities correctly mapped to Knowledge Graph
- [ ] Relationships created with appropriate strength
- [ ] Deduplication working (same person across documents)
- [ ] RAG indexing to correct collections

### Phase 3 Success
- [ ] Documents routed to correct destinations
- [ ] State transitions tracked
- [ ] Duplicate detection working
- [ ] History preserved

### Phase 4 Success
- [ ] Email threads grouped correctly
- [ ] Attachments routed through document pipeline
- [ ] Action items extracted
- [ ] Participant relationships tracked

### Phase 5 Success
- [ ] Insights generated within 1s of processing
- [ ] Notifications delivered
- [ ] Insight accuracy >80%
- [ ] No spam (appropriate throttling)

### Phase 6 Success
- [ ] Natural language queries parsed correctly
- [ ] Multi-source results combined
- [ ] Response time <2s
- [ ] Ranking quality high

### Overall Success
- [ ] Downloads folder stays empty (auto-processed)
- [ ] All documents searchable across systems
- [ ] Proactive insights surface useful information
- [ ] Knowledge compounds over time

---

## Technical Requirements

### Dependencies
- Python 3.11+
- Ollama with llama3.2 or similar
- ChromaDB
- SQLite3
- watchdog (folder monitoring)
- python-docx (DOCX parsing)
- PyMuPDF or pdfplumber (PDF parsing)
- email (EML parsing)
- openpyxl (XLSX parsing)

### Infrastructure
- LaunchAgents for continuous monitoring
- macOS Notification Center access
- Full Disk Access for Downloads monitoring

### Performance Targets
- Document processing: <5s average
- Query response: <2s
- Notification delivery: <1s
- Knowledge Graph update: <500ms

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM extraction quality | Fallback to pattern matching for critical fields |
| Processing bottleneck | Queue system with background processing |
| Knowledge Graph corruption | Transaction safety, backups before bulk ops |
| Duplicate explosion | Content hash dedup + semantic similarity check |
| Notification spam | Throttling, priority filtering, digest mode |
| Large file handling | Chunking, streaming, size limits |

---

## Questions for Review

1. **Scope**: Should Phase 4 (Email Integration) use M365 API or just process .eml files?
2. **Storage**: Should we create document_rag as new ChromaDB or extend existing?
3. **Notifications**: What's the right balance of notifications vs digest?
4. **Archival**: How long before ACTIVE → ARCHIVED transition?
5. **Dedup**: How aggressive should duplicate detection be?
6. **Privacy**: Any documents that should NOT be processed?

---

## Appendix A: Example End-to-End Flow

### CV Download Scenario

1. **User downloads**: `Vikrant Slathia - Talent Pack for Endpoint Engineer.pdf`

2. **Downloads Watcher detects**: New file in ~/Downloads/

3. **Document Intelligence processes**:
   - Classification: CV (98% confidence)
   - Entities extracted:
     - Person: Vikrant Slathia
     - Skills: Azure, Terraform, Intune, PowerShell
     - Certifications: AZ-104, AZ-305, AZ-900
     - Companies: TechCorp (2020-2023), CloudInc (2023-present)

4. **Knowledge Graph updates**:
   - Creates/updates Person node: Vikrant Slathia
   - Creates/updates Skill nodes: Azure, Terraform, etc.
   - Creates relationships: HAS_SKILL, WORKED_AT

5. **RAG indexes**: cv_rag collection (24 chunks)

6. **Lifecycle Manager routes**:
   - Destination: ~/Documents/Recruitment/CVs/2025-12/
   - New name: Vikrant_Slathia_Endpoint_Engineer_2025-12-17.pdf

7. **Proactive Insights generates**:
   - CANDIDATE_MATCH: 87% match to Senior Endpoint Engineer JD
   - SIMILAR_DOCUMENT: Similar to Samuel Nou (hired)

8. **Notification sent**:
   ```
   📋 New CV: Vikrant Slathia
   ✅ 87% match for Endpoint Engineer role
   💡 Top skills: Azure (AZ-305), Terraform, Intune
   📊 Ranked #2 of 6 candidates
   ```

9. **Query available**:
   - "Compare Vikrant to other candidates" → cross-reference
   - "What skills does Vikrant have?" → Knowledge Graph
   - "Find similar candidates" → cv_rag semantic search

---

## Appendix B: Document Type Detection Patterns

### CV/Resume
```python
CV_PATTERNS = [
    r'talent\s*pack',
    r'curriculum\s*vitae',
    r'\bresume\b',
    r'\bcv\b',
    r'experience\s*:',
    r'education\s*:',
    r'skills\s*:',
    r'work\s*history',
    r'employment\s*history',
]
```

### Job Description
```python
JD_PATTERNS = [
    r'job\s*description',
    r'position\s*description',
    r'role\s*description',
    r'(senior|junior|lead|principal)\s+\w+\s+(engineer|developer|manager|analyst)',
    r'requirements\s*:',
    r'responsibilities\s*:',
    r'qualifications\s*:',
    r'essential\s*requirements',
    r'desirable\s*:',
]
```

### Invoice
```python
INVOICE_PATTERNS = [
    r'\binvoice\b',
    r'inv[-#]?\d+',
    r'bill\s*to',
    r'payment\s*due',
    r'total\s*amount',
    r'tax\s*invoice',
    r'account\s*number',
]
```

### Policy
```python
POLICY_PATTERNS = [
    r'pol\d+',
    r'\bpolicy\b',
    r'version\s*\d+',
    r'effective\s*date',
    r'scope\s*:',
    r'purpose\s*:',
    r'compliance\s*requirements',
]
```

---

## Appendix C: Knowledge Graph Node Types Mapping

| Document Entity | Knowledge Graph NodeType | Attributes |
|-----------------|-------------------------|------------|
| Candidate Name | PERSON | role_type="candidate" |
| Recruiter | PERSON | role_type="recruiter" |
| Hiring Manager | PERSON | role_type="hiring_manager" |
| Technical Skill | SKILL | skill_category="technical" |
| Soft Skill | SKILL | skill_category="soft" |
| Certification | SKILL | is_certification=True, cert_code="..." |
| Current Employer | COMPANY | relationship_type="current" |
| Previous Employer | COMPANY | relationship_type="previous" |
| Recruiting Agency | COMPANY | company_type="agency" |
| Job Opening | JOB | status="open/filled" |
| Project | PROJECT | status="active/completed" |
| Invoice Vendor | COMPANY | company_type="vendor" |

---

*End of Project Plan*

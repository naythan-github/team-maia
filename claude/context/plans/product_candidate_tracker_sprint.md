# Product Candidate Tracker - TDD Sprint Plan

**Status**: ✅ COMPLETE (2026-01-15)
**Tests**: 34/34 passed
**Phase**: 238

## Overview

**Purpose**: Track Maia tools with potential for organizational productization
**Location**: `claude/tools/pmp/product_tracker.py`
**Data Store**: `claude/data/product_candidates.json`

---

## Architecture

### Data Model

```python
@dataclass
class ProductCandidate:
    tool: str                      # Tool filename
    path: str                      # Directory path
    potential: Literal["high", "medium", "low"]
    audience: Literal["team", "department", "org", "external"]
    value: str                     # Business case (1-2 sentences)
    changes_needed: List[str]      # Work items to productize
    status: Literal["idea", "prototype", "ready", "in_progress", "shipped"]
    dependencies: List[str]        # External requirements
    added: str                     # ISO date
    updated: str                   # ISO date
    notes: Optional[str] = None    # Free-form notes
```

### File Structure

```
claude/
├── tools/pmp/
│   └── product_tracker.py        # Main tool + CLI
├── data/
│   └── product_candidates.json   # Data store
└── context/plans/
    └── product_candidate_tracker_sprint.md  # This plan
```

---

## TDD Plan (P0-P6.5)

### P0: Requirements Validation
- [x] User confirmed need for tracking productizable tools
- [x] JSON + CLI approach approved

### P1: Test File Creation

**File**: `tests/test_product_tracker.py`

```python
class TestProductCandidate:
    def test_candidate_creation_with_required_fields()
    def test_candidate_creation_with_all_fields()
    def test_candidate_validation_rejects_invalid_potential()
    def test_candidate_validation_rejects_invalid_status()
    def test_candidate_to_dict_serialization()
    def test_candidate_from_dict_deserialization()

class TestProductTracker:
    def test_add_candidate_creates_entry()
    def test_add_candidate_prevents_duplicates()
    def test_list_candidates_returns_all()
    def test_list_candidates_filter_by_potential()
    def test_list_candidates_filter_by_status()
    def test_list_candidates_filter_by_audience()
    def test_update_candidate_modifies_fields()
    def test_update_candidate_updates_timestamp()
    def test_remove_candidate_deletes_entry()
    def test_get_candidate_by_tool_name()

class TestDataPersistence:
    def test_save_creates_json_file()
    def test_load_reads_existing_file()
    def test_load_creates_empty_if_missing()
    def test_save_preserves_all_fields()

class TestCLI:
    def test_cli_add_command()
    def test_cli_list_command()
    def test_cli_list_with_filters()
    def test_cli_update_command()
    def test_cli_remove_command()
    def test_cli_report_markdown_format()
    def test_cli_report_json_format()
    def test_cli_suggest_scans_capabilities()

class TestSuggestionEngine:
    def test_suggest_identifies_general_purpose_tools()
    def test_suggest_excludes_maia_specific_tools()
    def test_suggest_ranks_by_complexity()
```

### P2: Interface Design

```python
class ProductTracker:
    def __init__(self, data_path: str = None)

    # CRUD operations
    def add(self, candidate: ProductCandidate) -> bool
    def get(self, tool: str) -> Optional[ProductCandidate]
    def list(self, **filters) -> List[ProductCandidate]
    def update(self, tool: str, **updates) -> bool
    def remove(self, tool: str) -> bool

    # Persistence
    def save(self) -> None
    def load(self) -> None

    # Intelligence
    def suggest(self) -> List[Dict]  # Scan capabilities for candidates
    def report(self, format: str = "md") -> str
```

### P3: Implementation Sequence

| Step | Component | Effort |
|------|-----------|--------|
| 1 | `ProductCandidate` dataclass | 10 min |
| 2 | `ProductTracker` core CRUD | 20 min |
| 3 | JSON persistence | 10 min |
| 4 | CLI with argparse | 20 min |
| 5 | Suggestion engine | 15 min |
| 6 | Report generation | 10 min |

### P4: Test Execution
```bash
pytest tests/test_product_tracker.py -v --tb=short
```

### P5: Integration
- Register in capabilities.db
- Add to capability_index.md
- Create `/product` command (optional)

### P6: Performance Validation
- Load/save < 100ms for 100 candidates
- Suggest scan < 5s for full capability registry

### P6.5: Completeness Review
- [ ] All tests pass
- [ ] CLI help text complete
- [ ] Initial candidates seeded
- [ ] Documentation updated

---

## CLI Specification

```bash
# Add a candidate
python3 product_tracker.py add pdf_text_extractor \
    --path claude/tools/document/ \
    --potential high \
    --audience org \
    --value "Batch PDF processing saves hours for anyone handling documents" \
    --changes "Remove Maia paths" "Add web UI" "Docker packaging" \
    --status prototype

# List all candidates
python3 product_tracker.py list

# List with filters
python3 product_tracker.py list --potential high --status ready

# Update a candidate
python3 product_tracker.py update pdf_text_extractor --status ready

# Remove a candidate
python3 product_tracker.py remove pdf_text_extractor

# Generate report
python3 product_tracker.py report --format md > ~/work_projects/product_candidates.md
python3 product_tracker.py report --format json

# Auto-suggest candidates from existing tools
python3 product_tracker.py suggest
```

---

## Subagent/Model Plan

| Phase | Agent | Model | Rationale |
|-------|-------|-------|-----------|
| P1-P3 | SRE Principal | Sonnet | Standard TDD implementation |
| P4 | SRE Principal | Sonnet | Test execution |
| P5 | SRE Principal | Sonnet | Integration & docs |
| P6.5 | Python Code Reviewer | Sonnet | Code quality review |

**Handoff Points:**
1. After P4 (tests green) → Python Code Reviewer for quality check
2. Reviewer returns MUST-FIX → SRE fixes → re-run TDD → back to reviewer
3. Loop until PASS (0 MUST-FIX items)

---

## Initial Seed Candidates

Based on existing Maia tools, initial high-potential candidates:

| Tool | Potential | Audience | Value |
|------|-----------|----------|-------|
| `pdf_text_extractor.py` | High | Org | Batch PDF processing with table extraction |
| `receipt_ocr.py` | High | Org | Privacy-first OCR for expense processing |
| `cv_parser.py` | High | Department | Recruitment pipeline automation |
| `convert_md_to_docx.py` | Medium | Team | Corporate document formatting |
| `email_rag.py` | Medium | Department | Email search and analysis |
| `dns_complete_audit.py` | Medium | Team | Security audit automation |

---

## Success Criteria

1. **Functional**: Can add, list, update, remove candidates via CLI
2. **Persistent**: Data survives restarts
3. **Queryable**: Filter by potential, status, audience
4. **Reportable**: Generate markdown/JSON reports
5. **Intelligent**: Suggest candidates from existing tools

---

## Verification Commands

```bash
# Run tests
pytest tests/test_product_tracker.py -v

# Verify CLI
python3 claude/tools/pmp/product_tracker.py --help
python3 claude/tools/pmp/product_tracker.py suggest
python3 claude/tools/pmp/product_tracker.py list

# Verify data persistence
cat claude/data/product_candidates.json | python3 -m json.tool
```

---

*Sprint Plan v1.0 | Created: 2026-01-15 | Target: Single session implementation*

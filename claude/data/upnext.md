# Up Next - Pending Projects

Projects queued for implementation after approval.

---

## 1. Unified Intelligence Framework
**Sprint ID**: SPRINT-INTEL-FRAMEWORK-001
**Status**: PENDING APPROVAL
**Plan**: `claude/context/plans/unified_intelligence_framework_sprint.md`
**Estimated Effort**: 5-6 hours

### Summary
- **BaseIntelligenceService** - Abstract base class for extensibility
- **OTCIntelligenceService** - Unified PostgreSQL query interface for ServiceDesk
- **CollectionScheduler** - Daily automated data refresh (PMP @ 06:00, OTC @ 06:30)
- **PMP Refactor** - Inherit base class (backward compatible)

### Why
- OTC queries require knowing 20+ tools, TKT-*/TKTCT-*/TS-* column prefixes
- No freshness awareness before queries
- Manual data refresh only
- No consistent pattern across data sources

### Tests
58 total across 7 phases

### To Start
```
Review and approve: claude/context/plans/unified_intelligence_framework_sprint.md
```

---

## Completed Recently

| Sprint | Date | Summary |
|--------|------|---------|
| SPRINT-PMP-INTEL-001 | 2026-01-15 | PMP Intelligence Service - unified query interface |
| SPRINT-002-PROMPT-CAPTURE | 2026-01-14 | Prompt capture system for team sharing |
| SPRINT-001-REPO-SYNC | 2026-01-13 | Multi-repo context validation |

# Resume Prompt: OTC Team Management Database Implementation

## Quick Start Command

```
Load the SRE Principal Engineer Agent and continue the OTC Team Management Database
implementation from Phase 3 (Helper Functions). Read the checkpoint document at
SESSION_CHECKPOINT_TEAM_MGMT_DB_IMPLEMENTATION.md, then continue with strict TDD
methodology. Do not ask questions - proceed autonomously through all remaining phases
(3-6) plus finalization.
```

## Context Summary

- **Project:** OTC Team Management Database
- **Status:** 40% complete (Phases 1-2 done, Phases 3-6 pending)
- **Tests Passing:** 12/12 (100% of implemented features)
- **Checkpoint:** `SESSION_CHECKPOINT_TEAM_MGMT_DB_IMPLEMENTATION.md`
- **Requirements:** `claude/data/project_plans/OTC_TEAM_MANAGEMENT_DB_REQUIREMENTS.md`

## What's Complete ✅

- Phase 1: Schema creation (3 tables, 10 indexes) - 7 tests passing
- Phase 2: Data migration (11 members, 33 assignments) - 5 tests passing
- Database is live and populated with production data

## What's Next ⏳

**Phase 3 (60 min):** Implement 11 helper functions in `claude/tools/integrations/otc/team_management.py`
- Write tests first (RED)
- Implement functions (GREEN)
- Key functions: get_team_members, add_team_member, update_team_member, export_teams_to_json

**Phase 4 (20 min):** Performance benchmarks (<10ms roster, <20ms joins)

**Phase 5 (20 min):** Integration tests (team + tickets joins)

**Phase 6 (15 min):** History tracking tests (audit trail)

**Finalization (20 min):** Update user_preferences.json, commit all changes

## Execution Mode

**AUTONOMOUS** - No permission requests, follow TDD strictly, fix until working, update todos after each phase.

## Expected Output

- `claude/tools/integrations/otc/team_management.py` - 11 helper functions
- 35+ total tests passing (12 existing + 23 new)
- Performance benchmarks documented
- Git commit with all changes
- Final checkpoint document

## Estimated Time

2.25 hours remaining to completion.

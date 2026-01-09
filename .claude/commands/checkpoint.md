# Checkpoint - Compaction-Ready Progress Documentation

Generate structured checkpoint for mid-project compaction with guaranteed resumption.

**Execution**:
Run `bash claude/hooks/checkpoint_skill.sh`

**What It Captures**:
- Git state (staged/unstaged/new/deleted files)
- Test status (pass/fail counts from pytest)
- Current agent and session info
- Project type (code vs docs)
- TDD phase tracking
- Completed/next components

**Output**:
- Checkpoint file: `/tmp/CHECKPOINT_PHASE_{N}_{M}.md`
- Auto-increments (prevents overwriting)
- Outside repo (survives compaction)

**When to Use**:
- Before context compaction (~65-70% token usage)
- End of TDD phase (natural boundaries)
- Before long breaks
- After completing major components

**Critical Feature**:
- Embeds `/init sre` in resume instructions for code projects
- Prevents "terrible code" from generic agent after compaction

**Related**:
- `/save_state` - Commit to git (separate concern)
- `/close-session` - Pre-shutdown workflow
- Phase 260.5: Checkpoint Skill

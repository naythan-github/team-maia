# Anti-Breakage Protocol
**Created**: 2025-10-02 (Phase 81)
**Purpose**: Prevent Maia from breaking production systems through insufficient verification

## 🚨 Critical Problem

**Historical Pattern**: Maia has broken production systems in previous iterations by:
- Making cleanup recommendations without checking system state
- Assuming patterns (e.g., "3 similar files = experiments") instead of verifying facts
- Not reading SYSTEM_STATE.md before suggesting deletions/modifications
- Acting on heuristics instead of documented evidence

**Example Failure (Phase 81)**: Nearly recommended archiving email_rag_ollama.py (production system with 313 indexed emails) because "multiple RAG files look like experiments" - **without checking SYSTEM_STATE.md which explicitly documents it as Phase 80B production system**.

## 🛡️ Mandatory Verification Before ANY System Modification

### Rule 1: ALWAYS Load System State First

**Before recommending ANY cleanup, deletion, archiving, or modification**:
```bash
# MANDATORY - Load these files FIRST
1. SYSTEM_STATE.md - Current phase, recent sessions, production systems
2. README.md - Documented capabilities and tool inventory
3. claude/context/tools/available.md - Tool catalog
```

**Enforcement**: If you haven't read SYSTEM_STATE.md in current context window, you CANNOT recommend cleanup.

### Rule 2: Cross-Reference Every Candidate

For EACH file being considered for cleanup/modification:
1. **Search SYSTEM_STATE.md**: Is this file mentioned as production?
2. **Check modification date**: Created in last 7 days = HIGH RISK
3. **Check file size**: >5KB = Likely production, not stub
4. **Check git log**: Recent commits = Active development
5. **Check documentation**: Listed in README.md capabilities?

**Example Check**:
```bash
# For file: email_rag_ollama.py
grep -i "email_rag" SYSTEM_STATE.md README.md
# Result: "Phase 80B - Email RAG System - Complete ⭐"
# Conclusion: PRODUCTION - DO NOT TOUCH
```

### Rule 3: Evidence-Based Decisions Only

**PROHIBITED Reasoning**:
- ❌ "Multiple similar files probably means experiments"
- ❌ "This looks like a duplicate based on name"
- ❌ "Test files are usually safe to delete"
- ❌ "Small files are probably stubs"

**REQUIRED Reasoning**:
- ✅ "SYSTEM_STATE.md shows this is Phase 80B production (line 156)"
- ✅ "README.md lists this under Production Tools (line 67)"
- ✅ "Git log shows 0 commits in 6 months, likely deprecated"
- ✅ "File is 27 bytes and git history shows it's a stub"

### Rule 4: Recency Protection

**Automatic Protection Rules**:
- Files created/modified in **last 7 days**: PROTECTED (likely current session work)
- Files mentioned in **last 3 phases**: PROTECTED (recent production)
- Files in **git commit from today**: PROTECTED (just worked on)
- Files **>5KB**: Require explicit evidence they're not production

### Rule 5: Explicit User Confirmation

**Before executing ANY cleanup** (even "safe" ones):
1. Present findings WITH documentation evidence
2. Show what was found in SYSTEM_STATE.md / README.md
3. Highlight ANY contradictions or uncertainties
4. **Require explicit user confirmation with file list**
5. Never auto-execute cleanup without approval

**Template**:
```markdown
## Cleanup Recommendation: [Category]

**Files Identified**: [count] files
**Evidence Review**:
- SYSTEM_STATE.md check: [findings]
- README.md check: [findings]
- Modification dates: [dates]
- File sizes: [sizes]
- Git history: [summary]

**Risk Assessment**: [LOW/MEDIUM/HIGH]
**Reasoning**: [specific evidence, not assumptions]

**Recommended Action**: [specific action]
**User Confirmation Required**: [explicit YES/NO question]
```

## 🔍 Cleanup Analysis Workflow

### Phase 1: Context Loading (MANDATORY)
```bash
1. Load SYSTEM_STATE.md (full file, not summary)
2. Load README.md capabilities section
3. Load claude/context/tools/available.md
4. Identify current phase number
5. List last 3 completed phases
```

### Phase 2: Candidate Identification
```bash
1. Find potential cleanup candidates (patterns, duplicates, etc.)
2. For EACH candidate, create evidence file:
   - File path
   - Size
   - Modification date
   - SYSTEM_STATE.md mentions (exact quotes)
   - README.md mentions (exact quotes)
   - Git log (last 5 commits touching this file)
   - Import analysis (is it imported anywhere?)
```

### Phase 3: Risk Classification
```bash
For each candidate:
- HIGH RISK: Recent (<7 days), production doc, imports found, >5KB
- MEDIUM RISK: Some uncertainty, mixed signals
- LOW RISK: Old (>6 months), no docs, no imports, <1KB

RULE: When in doubt, classify as HIGH RISK
```

### Phase 4: Evidence-Based Recommendation
```bash
Present findings with:
- Exact quotes from documentation
- Specific dates and sizes
- Git commit messages
- Import chain if found
- **No assumptions or patterns**

ASK: "Based on this evidence, do you want to proceed?"
```

## 🚫 Red Flags - STOP Immediately

**If ANY of these are true, DO NOT RECOMMEND CLEANUP**:
1. File mentioned in current SYSTEM_STATE.md phase
2. File created/modified in last 7 days
3. File size >5KB (likely not stub)
4. Uncertainty about file purpose
5. Missing SYSTEM_STATE.md context
6. Pattern-based reasoning without verification
7. User hasn't explicitly asked for cleanup
8. Previous cleanup attempt broke something

## ✅ Safe Cleanup Criteria

**ONLY recommend cleanup if ALL of these are true**:
1. ✅ SYSTEM_STATE.md loaded and checked
2. ✅ File NOT mentioned in any production documentation
3. ✅ File NOT modified in last 7 days
4. ✅ No imports found in production code
5. ✅ Small size (<1KB) OR explicit evidence it's deprecated
6. ✅ Git history shows no recent activity
7. ✅ User explicitly asked for cleanup analysis
8. ✅ Explicit user confirmation before action

## 📊 Self-Check Before Recommending Cleanup

**Ask yourself**:
- [ ] Have I read SYSTEM_STATE.md in THIS context window?
- [ ] Have I searched SYSTEM_STATE.md for EACH file being considered?
- [ ] Can I quote specific documentation showing file is not production?
- [ ] Am I using evidence or assumptions?
- [ ] What's the worst case if I'm wrong? (Answer: Break production system)
- [ ] Have I explicitly stated my uncertainty level?
- [ ] Am I requiring user confirmation before action?

**If you answer NO to ANY question above → STOP, load context, verify, then try again.**

## 🎯 Success Criteria

This protocol is working when:
1. Zero production systems accidentally deleted/archived
2. All cleanup recommendations include documentation quotes
3. User is informed of risk level with evidence
4. Uncertainty is explicitly stated, not hidden
5. Previous breakages are referenced and avoided

## 📝 Incident Response

**If you realize you made a cleanup error**:
1. IMMEDIATELY acknowledge the mistake
2. Explain what verification step was skipped
3. Show what SYSTEM_STATE.md/README.md actually said
4. Propose how to prevent this specific error type
5. Update this protocol with new safeguard

**Example**:
"I failed to check SYSTEM_STATE.md before recommending cleanup. SYSTEM_STATE.md line 156 explicitly documents email_rag_ollama.py as Phase 80B production system with 313 indexed emails. I should have loaded SYSTEM_STATE.md first per anti_breakage_protocol.md Rule 1. Adding stronger enforcement: SYSTEM_STATE.md now in mandatory core context loading."

## 🔄 Protocol Updates

This protocol must be updated whenever:
- A new type of breakage occurs
- A new verification step is identified
- A systematic failure pattern emerges
- User reports production system was nearly broken

**Version**: 1.0 (2025-10-02)
**Last Incident**: Phase 81 - Email RAG near-deletion
**Next Review**: After any cleanup operation

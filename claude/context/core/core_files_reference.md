# Core Files Reference Card
**Purpose**: Quick reference for correct core file names
**Created**: 2025-09-30 (after filename confusion issues)

## ✅ CORRECT CORE FILE NAMES

### Always Use These Exact Filenames:

1. **UFC System** (Foundation):
   - ✅ `claude/context/ufc_system.md`
   - ❌ NOT: ufc.md, ufc_context.md

2. **Identity**:
   - ✅ `claude/context/core/identity.md`
   - ❌ NOT: maia_identity.md, maia.md

3. **Systematic Thinking**:
   - ✅ `claude/context/core/systematic_thinking_protocol.md`
   - ❌ NOT: systematic_thinking.md, thinking_protocol.md

4. **Model Selection**:
   - ✅ `claude/context/core/model_selection_strategy.md`
   - ❌ NOT: model_strategy.md, model_selection.md

5. **Smart Context Loading**:
   - ✅ `claude/context/core/smart_context_loading.md`
   - ❌ NOT: context_loading.md, smart_loading.md

## 📋 Full Paths for Context Loading

```python
# Use these exact paths when loading context:
CORE_FILES = [
    "${MAIA_ROOT}/claude/context/ufc_system.md",
    "${MAIA_ROOT}/claude/context/core/identity.md",
    "${MAIA_ROOT}/claude/context/core/systematic_thinking_protocol.md",
    "${MAIA_ROOT}/claude/context/core/model_selection_strategy.md",
]
```

## 🔍 How to Verify

```bash
# Quick verification that all core files exist:
ls -1 claude/context/ufc_system.md \
     claude/context/core/identity.md \
     claude/context/core/systematic_thinking_protocol.md \
     claude/context/core/model_selection_strategy.md \
     claude/context/core/smart_context_loading.md

# Or use the validator:
python3 claude/tools/validate_context_files.py
```

## 🚨 Common Mistakes

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| maia_identity.md | identity.md |
| systematic_thinking.md | systematic_thinking_protocol.md |
| model_strategy.md | model_selection_strategy.md |
| ufc.md | ufc_system.md |

## 📝 If You Get File Not Found

1. Check this reference card for correct spelling
2. Run: `python3 claude/tools/validate_context_files.py`
3. Verify file exists: `ls claude/context/core/{filename}`
4. Check CLAUDE.md line 13 for the official list

## 🔒 Protected by Immutable Core

These core files are **absolutely protected** and cannot be:
- Moved to different directories
- Renamed
- Deleted

This protection ensures these filenames remain stable forever.

---

**Last Updated**: 2025-09-30
**Validation Tool**: `claude/tools/validate_context_files.py`
**Source of Truth**: `CLAUDE.md` lines 10-13
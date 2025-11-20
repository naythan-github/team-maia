# Confluence Single-Instance Constraint

## 🚨 CRITICAL RULE: VivOEMC Confluence ONLY 🚨

**ALL Confluence operations use vivoemc.atlassian.net (single instance)**

This constraint is **MANDATORY** and **NON-NEGOTIABLE**.

---

## The Rule

When user says:
- "Save to Confluence"
- "Create Confluence page"
- "Save to Confluence Orro space"
- "Update Confluence page in Orro"
- ANY Confluence-related request

**YOU MUST**:
1. ✅ Use `confluence_client.py` (THE ONLY TOOL)
2. ✅ Connect to `vivoemc.atlassian.net` (automatic, hardcoded)
3. ✅ Use space_key parameter for the space name (e.g., `space_key="Orro"`)
4. ✅ NEVER attempt to construct alternate Confluence URLs

**YOU MUST NOT**:
1. ❌ Attempt to connect to `orro.atlassian.net` (doesn't exist)
2. ❌ Attempt to connect to any other Confluence instance
3. ❌ Ask user which Confluence instance to use
4. ❌ Use `site_name` parameter (removed in Phase 159)

---

## Common Disambiguation Scenarios

### Scenario 1: "Save to Confluence Orro space"
**CORRECT INTERPRETATION**:
- Confluence instance: `vivoemc.atlassian.net` (only instance)
- Space key: `"Orro"`
- Action: Create page in Orro space within VivOEMC Confluence

**INCORRECT INTERPRETATION** ❌:
- ~~Confluence instance: `orro.atlassian.net`~~ (doesn't exist)

### Scenario 2: "Create page in Orro"
**CORRECT INTERPRETATION**:
- Confluence instance: `vivoemc.atlassian.net` (only instance)
- Space key: `"Orro"`

**INCORRECT INTERPRETATION** ❌:
- ~~Find Orro Confluence access~~ (there is no separate Orro Confluence)

### Scenario 3: "Update page in MAIA-TEST space"
**CORRECT INTERPRETATION**:
- Confluence instance: `vivoemc.atlassian.net` (only instance)
- Space key: `"MAIA-TEST"`

---

## Technical Implementation

### Code Pattern (ALWAYS use this):
```python
from confluence_client import ConfluenceClient

# Initialize client (no parameters - single instance hardcoded)
client = ConfluenceClient()

# Create page (space_key is a space WITHIN vivoemc.atlassian.net)
url = client.create_page_from_markdown(
    space_key="Orro",  # Space within vivoemc.atlassian.net
    title="Page Title",
    markdown_content="# Content here"
)
```

### What Changed (Phase 159 Reliability Fix):
- **Removed**: Multi-site configuration support
- **Removed**: `site_name` parameter from `ConfluenceClient.__init__()`
- **Added**: Space key validation (rejects instance names)
- **Added**: Helpful error messages for common mistakes
- **Hardcoded**: Single instance `vivoemc.atlassian.net`

---

## Enforcement Mechanisms

### 1. Code-Level Enforcement
Tool will **reject** attempts to:
- Use `site_name` parameter (removed)
- Use instance names as space keys (e.g., space_key="vivoemc")

### 2. Documentation Enforcement
- `capability_index.md`: Explicit VivOEMC-only constraint
- `available.md`: Critical constraint section
- This file: Loaded for all Confluence requests

### 3. Validation Enforcement
Space key validation in `confluence_client.py`:
- Rejects: `vivoemc`, `vivonetix`, `atlassian` as space keys
- Provides: Helpful error message explaining the constraint

---

## Why This Constraint Exists

**Problem**: Multi-site code caused ambiguity
- User says "Orro space" → Agent misinterprets as "Orro Confluence instance"
- Agent attempts to construct `orro.atlassian.net` URL (doesn't exist)
- Operation fails with made-up credentials

**Solution**: Remove multi-site support entirely
- Single hardcoded instance: `vivoemc.atlassian.net`
- Space keys are ALWAYS within this instance
- No ambiguity possible

**Reality**:
- We have ONE Confluence account: VivOEMC (`vivoemc.atlassian.net`)
- "Orro" is a space within that account
- No other Confluence instances exist or are accessible

---

## Error Recovery

If you see errors like:
- "Unable to connect to orro.atlassian.net"
- "Confluence instance not found"
- "Invalid credentials for X Confluence"

**This means**:
- You misinterpreted space key as instance name
- **FIX**: Use `space_key="Orro"` within `vivoemc.atlassian.net`

---

## Summary

**ONE RULE TO REMEMBER**:
> All Confluence = vivoemc.atlassian.net + space_key parameter

**NO EXCEPTIONS**.

---

**Status**: ✅ Active (Phase 159 Reliability Fix)
**Enforcement**: Code + Documentation + Validation
**Confidence**: 100% (constraint is mandatory)

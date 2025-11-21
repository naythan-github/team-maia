# Project Recovery Template System - Complete Project Plan

**Project ID**: PROJECT_RECOVERY_TEMPLATE_SYSTEM_001
**Created**: 2025-10-15
**Status**: Planning Complete, Ready for Implementation
**Estimated Time**: 1-1.5 hours total
**Priority**: HIGH - Prevents project drift and context loss for ALL future multi-phase work

---

## 🎯 EXECUTIVE SUMMARY

### Problem Statement
Currently, project recovery protection (anti-compaction files) must be manually created for each multi-phase project. The capability amnesia fix (Phase 119) demonstrated the value of 3-layer recovery (comprehensive plan + quick recovery JSON + start here guide), but this pattern should be available for ALL future projects.

### Root Cause
**Gap**: No templating system for project recovery files
- Each project requires manual creation of 3 files (plan, JSON, start here)
- No standardized structure across projects
- High friction → recovery files often skipped → project drift risk

### Solution Architecture
**Template-Based Recovery System**: Create reusable templates + generator script that produces anti-compaction protection files for any multi-phase project in <2 minutes.

### Success Metrics
- ✅ Template creation: <5 min per project (down from 30+ min manual)
- ✅ Adoption: 100% of multi-phase projects use recovery system
- ✅ Context loss: Zero project drift incidents
- ✅ Recovery time: <5 min to resume any project after compaction

---

## 📋 PROJECT PHASES

### **PHASE 1: Create Template Directory Structure** (5 min)
**Deliverable**: Organized template directory

**Directory Structure**:
```
claude/templates/
  project_recovery/
    PROJECT_PLAN_TEMPLATE.md          # Comprehensive project plan
    RECOVERY_STATE_TEMPLATE.json      # Quick recovery state
    START_HERE_TEMPLATE.md            # Entry point guide
    generate_recovery_files.py        # Generator script
    README.md                         # Template usage guide
    examples/
      capability_amnesia/             # Reference: Phase 119 example
```

**Actions**:
1. Create `claude/templates/project_recovery/` directory
2. Create `examples/capability_amnesia/` subdirectory
3. Copy Phase 119 files as reference examples

**Checkpoint**: Directory structure exists, examples copied

---

### **PHASE 2: Create PROJECT_PLAN_TEMPLATE.md** (15 min)
**Deliverable**: Reusable comprehensive project plan template

**Template Structure**:
```markdown
# {{PROJECT_NAME}} - Complete Project Plan

**Project ID**: {{PROJECT_ID}}
**Created**: {{DATE}}
**Status**: Planning Complete, Ready for Implementation
**Estimated Time**: {{ESTIMATED_TIME}}
**Priority**: {{PRIORITY}}

---

## 🎯 EXECUTIVE SUMMARY

### Problem Statement
{{PROBLEM_DESCRIPTION}}

### Root Cause
{{ROOT_CAUSE_ANALYSIS}}

### Solution Architecture
{{SOLUTION_OVERVIEW}}

### Success Metrics
{{SUCCESS_CRITERIA}}

---

## 📋 PROJECT PHASES

### **PHASE 1: {{PHASE_1_NAME}}** ({{PHASE_1_TIME}})
**Deliverable**: {{PHASE_1_DELIVERABLE}}

**Actions**:
1. {{ACTION_1}}
2. {{ACTION_2}}

**Checkpoint**: {{PHASE_1_CHECKPOINT}}

---

[Repeat for N phases]

---

## 🔄 RECOVERY & ROLLBACK

### If Context Compaction Happens Mid-Project

**Recovery File**: This file ({{PROJECT_NAME}}_PROJECT.md)
**Location**: `claude/data/{{PROJECT_NAME}}_PROJECT.md`

**Recovery Steps**:
1. Read this file in its entirety
2. Check "Current Phase" section below
3. Resume from last completed phase
4. Validate previous phase outputs exist

**Current Phase**: {{CURRENT_PHASE}}
**Last Updated**: {{LAST_UPDATED}}
**Completed Phases**: {{COMPLETED_PHASES_LIST}}

### Rollback Plan
{{ROLLBACK_PROCEDURES}}

---

## 📁 FILE MANIFEST

### Files to Create
{{FILES_TO_CREATE_LIST}}

### Files to Modify
{{FILES_TO_MODIFY_LIST}}

---

## 🎯 IMPLEMENTATION SEQUENCE
{{IMPLEMENTATION_SEQUENCE}}

---

## 💡 ANTI-DRIFT MEASURES
{{ANTI_DRIFT_INSTRUCTIONS}}

---

## 🔥 COMMON PITFALLS & SOLUTIONS
{{PITFALLS_AND_SOLUTIONS}}

---

## 📈 METRICS TO TRACK
{{METRICS_TO_TRACK}}

---

## ✅ COMPLETION CRITERIA
{{COMPLETION_CRITERIA}}

---

## 📝 NOTES & CONTEXT
{{ADDITIONAL_NOTES}}
```

**Placeholders** (auto-replaced by generator):
- `{{PROJECT_NAME}}`: e.g., "Security Enhancement"
- `{{PROJECT_ID}}`: e.g., "SECURITY_ENHANCEMENT_001"
- `{{DATE}}`: Auto-filled with current date
- `{{ESTIMATED_TIME}}`: e.g., "4 hours"
- `{{PRIORITY}}`: HIGH/MEDIUM/LOW
- Phase-specific: Names, times, deliverables, actions

**Checkpoint**: Template created with all standard sections

---

### **PHASE 3: Create RECOVERY_STATE_TEMPLATE.json** (10 min)
**Deliverable**: Quick recovery state JSON template

**Template Structure**:
```json
{
  "project_id": "{{PROJECT_ID}}",
  "project_file": "claude/data/{{PROJECT_NAME}}_PROJECT.md",
  "created": "{{DATE}}",
  "status": "{{STATUS}}",
  "current_phase": 0,
  "total_phases": {{TOTAL_PHASES}},

  "quick_summary": "{{ONE_LINE_SUMMARY}}",

  "problem": "{{PROBLEM_STATEMENT}}",

  "solution": "{{SOLUTION_STATEMENT}}",

  "phases": [
    {
      "phase": 1,
      "name": "{{PHASE_1_NAME}}",
      "duration": "{{PHASE_1_TIME}}",
      "status": "pending",
      "deliverable": "{{PHASE_1_DELIVERABLE}}",
      "description": "{{PHASE_1_DESCRIPTION}}",
      "checkpoint": "{{PHASE_1_CHECKPOINT}}"
    }
  ],

  "files_to_create": [
    "{{FILE_PATH_1}}",
    "{{FILE_PATH_2}}"
  ],

  "files_to_modify": [
    "{{FILE_PATH_3}}",
    "{{FILE_PATH_4}}"
  ],

  "success_metrics": {
    "metric_1": {
      "before": "{{BEFORE_VALUE}}",
      "target": "{{TARGET_VALUE}}",
      "measurement": "{{HOW_TO_MEASURE}}"
    }
  },

  "recovery_instructions": [
    "If context compaction happens mid-project:",
    "1. Read {{PROJECT_NAME}}_PROJECT.md (complete plan)",
    "2. Check current_phase in this file",
    "3. Verify deliverables from completed phases exist",
    "4. Resume from current phase",
    "5. Update phase_progress after each checkpoint"
  ],

  "phase_progress": {
    "phase_1": {
      "started": null,
      "completed": null,
      "deliverable_exists": false,
      "notes": ""
    }
  },

  "last_updated": "{{DATE}}",
  "last_updated_by": "{{UPDATER}}",

  "anti_drift_notes": [
    "This JSON provides quick recovery state",
    "Full details in {{PROJECT_NAME}}_PROJECT.md",
    "Update phase_progress after each session",
    "If confused: Read project file from top to bottom"
  ]
}
```

**Dynamic Fields**: Generator fills based on project parameters

**Checkpoint**: JSON template with all standard fields

---

### **PHASE 4: Create START_HERE_TEMPLATE.md** (10 min)
**Deliverable**: Entry point recovery guide template

**Template Structure**:
```markdown
# 🚀 {{PROJECT_NAME}} - START HERE

**If you see this file, you're resuming the {{PROJECT_NAME}} project.**

---

## ⚡ QUICK RECOVERY (30 seconds)

**Problem**: {{PROBLEM_SUMMARY}}
**Solution**: {{SOLUTION_SUMMARY}}
**Status**: Check JSON file below for current phase

---

## 📋 RECOVERY SEQUENCE

### Step 1: Read Project Status (5 min)
```bash
# Quick status check
cat claude/data/{{PROJECT_NAME}}_RECOVERY.json | grep -A 5 "current_phase"

# See what's been completed
cat claude/data/{{PROJECT_NAME}}_RECOVERY.json | grep -A 20 "phase_progress"
```

### Step 2: Read Full Project Plan (10 min)
```bash
# Complete project details
cat claude/data/{{PROJECT_NAME}}_PROJECT.md

# Or open in editor
open claude/data/{{PROJECT_NAME}}_PROJECT.md
```

### Step 3: Verify Completed Deliverables (2 min)
```bash
# Check if files from completed phases exist
{{VERIFICATION_COMMANDS}}
```

### Step 4: Resume from Current Phase
See {{PROJECT_NAME}}_PROJECT.md for detailed phase instructions.

---

## 📊 PROJECT AT A GLANCE

**Total Phases**: {{TOTAL_PHASES}}
**Estimated Time**: {{ESTIMATED_TIME}}
**Current Phase**: See JSON file

**Phases**:
{{PHASE_LIST}}

---

## 🎯 WHY THIS MATTERS

{{PROJECT_IMPORTANCE}}

---

## 📁 KEY FILES

**Project Plan** (READ THIS): `claude/data/{{PROJECT_NAME}}_PROJECT.md`
**Recovery State**: `claude/data/{{PROJECT_NAME}}_RECOVERY.json`
**This File**: `claude/data/implementation_checkpoints/{{PROJECT_NAME}}_START_HERE.md`

---

## 🔥 ANTI-DRIFT PROTECTION

**If context compaction happens**:
1. You see this file → You know project is in progress
2. Read {{PROJECT_NAME}}_RECOVERY.json → See current phase
3. Read {{PROJECT_NAME}}_PROJECT.md → Get full context
4. Check deliverables exist → Verify progress
5. Resume from current phase → Continue work

**No confusion, no starting over, no project drift.**

---

**Ready to continue? Start with Step 1 above.**
```

**Checkpoint**: Start here template with recovery sequence

---

### **PHASE 5: Create generate_recovery_files.py** (30 min)
**Deliverable**: Automated generator script

**Core Functionality**:
```python
#!/usr/bin/env python3
"""
Project Recovery File Generator
Automatically creates anti-compaction protection for multi-phase projects
"""

import json
import os
from datetime import datetime
from typing import Dict, List

class ProjectRecoveryGenerator:
    def __init__(self):
        self.template_dir = "claude/templates/project_recovery"
        self.output_dir_plans = "claude/data"
        self.output_dir_checkpoints = "claude/data/implementation_checkpoints"

    def generate_project_id(self, project_name: str) -> str:
        """Generate project ID from name"""
        clean_name = project_name.upper().replace(" ", "_")
        return f"{clean_name}_001"

    def load_template(self, template_file: str) -> str:
        """Load template file"""
        path = os.path.join(self.template_dir, template_file)
        with open(path, 'r') as f:
            return f.read()

    def replace_placeholders(self, template: str, values: Dict[str, str]) -> str:
        """Replace all {{PLACEHOLDER}} values"""
        for key, value in values.items():
            placeholder = f"{{{{{key}}}}}"
            template = template.replace(placeholder, str(value))
        return template

    def generate_plan(self, project_config: Dict) -> str:
        """Generate project plan from template"""
        template = self.load_template("PROJECT_PLAN_TEMPLATE.md")

        # Build placeholder values
        values = {
            "PROJECT_NAME": project_config["name"],
            "PROJECT_ID": self.generate_project_id(project_config["name"]),
            "DATE": datetime.now().strftime("%Y-%m-%d"),
            "ESTIMATED_TIME": project_config["estimated_time"],
            "PRIORITY": project_config.get("priority", "MEDIUM"),
            "PROBLEM_DESCRIPTION": project_config["problem"],
            "SOLUTION_OVERVIEW": project_config["solution"],
            "TOTAL_PHASES": len(project_config["phases"]),
            # Add more from config...
        }

        # Generate phase sections
        phase_sections = self.generate_phase_sections(project_config["phases"])
        values["PHASE_SECTIONS"] = phase_sections

        return self.replace_placeholders(template, values)

    def generate_recovery_json(self, project_config: Dict) -> str:
        """Generate recovery JSON from template"""
        template = self.load_template("RECOVERY_STATE_TEMPLATE.json")
        # Similar replacement logic...
        return self.replace_placeholders(template, values)

    def generate_start_here(self, project_config: Dict) -> str:
        """Generate start here guide from template"""
        template = self.load_template("START_HERE_TEMPLATE.md")
        # Similar replacement logic...
        return self.replace_placeholders(template, values)

    def create_project_recovery(self, project_config: Dict):
        """Create all 3 recovery files"""
        project_name = project_config["name"].replace(" ", "_")

        # Generate content
        plan = self.generate_plan(project_config)
        recovery = self.generate_recovery_json(project_config)
        start_here = self.generate_start_here(project_config)

        # Write files
        plan_file = f"{self.output_dir_plans}/{project_name}_PROJECT.md"
        recovery_file = f"{self.output_dir_plans}/{project_name}_RECOVERY.json"
        start_file = f"{self.output_dir_checkpoints}/{project_name}_START_HERE.md"

        with open(plan_file, 'w') as f:
            f.write(plan)
        with open(recovery_file, 'w') as f:
            f.write(recovery)
        with open(start_file, 'w') as f:
            f.write(start_here)

        return {
            "plan": plan_file,
            "recovery": recovery_file,
            "start_here": start_file
        }

# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate project recovery files")
    parser.add_argument("--name", required=True, help="Project name")
    parser.add_argument("--phases", type=int, required=True, help="Number of phases")
    parser.add_argument("--time", required=True, help="Estimated time (e.g., '4 hours')")
    parser.add_argument("--problem", required=True, help="Problem statement")
    parser.add_argument("--solution", required=True, help="Solution overview")
    parser.add_argument("--priority", default="MEDIUM", help="Priority: HIGH/MEDIUM/LOW")

    args = parser.parse_args()

    # Build config
    project_config = {
        "name": args.name,
        "estimated_time": args.time,
        "problem": args.problem,
        "solution": args.solution,
        "priority": args.priority,
        "phases": [
            {"name": f"Phase {i+1}", "duration": "TBD", "deliverable": "TBD"}
            for i in range(args.phases)
        ]
    }

    # Generate
    generator = ProjectRecoveryGenerator()
    files = generator.create_project_recovery(project_config)

    print("✅ Project recovery files created:")
    print(f"   📋 Plan: {files['plan']}")
    print(f"   📊 Recovery: {files['recovery']}")
    print(f"   🚀 Start Here: {files['start_here']}")
```

**Features**:
- CLI interface for quick generation
- Template loading and placeholder replacement
- Phase section auto-generation
- File output to correct locations

**Usage**:
```bash
python3 claude/templates/project_recovery/generate_recovery_files.py \
  --name "Security Enhancement" \
  --phases 3 \
  --time "4 hours" \
  --problem "Need automated security scanning" \
  --solution "Build pre-commit security hooks" \
  --priority HIGH
```

**Checkpoint**: Generator script working, tested with sample project

---

### **PHASE 6: Create Template Usage Guide** (10 min)
**Deliverable**: README.md in template directory

**Content**:
```markdown
# Project Recovery Template System

## Quick Start

Generate recovery files for any multi-phase project:

```bash
python3 generate_recovery_files.py \
  --name "Your Project Name" \
  --phases 3 \
  --time "4 hours" \
  --problem "What problem are you solving?" \
  --solution "What's the solution approach?" \
  --priority HIGH
```

This creates:
- `claude/data/YOUR_PROJECT_NAME_PROJECT.md` - Comprehensive plan
- `claude/data/YOUR_PROJECT_NAME_RECOVERY.json` - Quick recovery state
- `claude/data/implementation_checkpoints/YOUR_PROJECT_NAME_START_HERE.md` - Entry point

## When to Use

Use recovery templates for:
- ✅ Multi-phase work (2+ hours, multiple sessions)
- ✅ Complex implementations (3+ phases)
- ✅ Projects spanning days/weeks
- ✅ Work with context compaction risk

Skip for:
- ❌ Single-phase work (<1 hour)
- ❌ Simple changes (1-2 files)
- ❌ Exploratory work (no clear phases)

## Template Customization

After generation, customize:
1. Add detailed phase descriptions
2. Specify deliverables and checkpoints
3. Add rollback procedures
4. Define success metrics
5. Document pitfalls and solutions

## Examples

See `examples/capability_amnesia/` for reference (Phase 119).

## Integration with Save State

For projects using recovery files:
1. Update `PROJECT_NAME_RECOVERY.json` after each phase
2. Update `current_phase` field when progressing
3. Add notes to `phase_progress` sections
4. Run standard save state (ss-std or ss-full)
```

**Checkpoint**: Usage guide complete with examples

---

### **PHASE 7: Integration with Save State** (15 min)
**Deliverable**: Updated save_state.md with Phase 0 recovery setup

**Update Location**: `claude/commands/save_state.md`

**Add Before Phase 1**:
```markdown
### Phase 0: Project Recovery Setup (Multi-Phase Work Only)

**When to Use**: Starting multi-phase project (estimated >2 hours, >1 session)

**Skip If**: Single-phase work, simple changes (<1 hour), exploratory work

#### Step 1: Generate Recovery Files (2 min)
```bash
python3 claude/templates/project_recovery/generate_recovery_files.py \
  --name "Your Project Name" \
  --phases [number] \
  --time "X hours" \
  --problem "Problem statement" \
  --solution "Solution approach" \
  --priority [HIGH/MEDIUM/LOW]
```

#### Step 2: Customize Generated Files (5-10 min)
1. Open `claude/data/YOUR_PROJECT_NAME_PROJECT.md`
2. Fill in detailed phase descriptions
3. Specify deliverables and checkpoints
4. Add rollback procedures if needed

#### Step 3: Commit Recovery Files (1 min)
```bash
git add claude/data/YOUR_PROJECT_NAME_*
git add claude/data/implementation_checkpoints/YOUR_PROJECT_NAME_START_HERE.md
git commit -m "📋 Project Plan: YOUR_PROJECT_NAME - Recovery protection"
git push
```

**Total Time**: 8-13 minutes (one-time setup per project)

**Benefit**: Zero context loss, instant recovery after compaction

---

[Continue with existing Phase 1...]
```

**Checkpoint**: Save state integration documented

---

## 🔄 RECOVERY & ROLLBACK

### If Context Compaction Happens Mid-Project

**Recovery File**: This file (PROJECT_RECOVERY_TEMPLATE_SYSTEM.md)
**Location**: `claude/data/PROJECT_RECOVERY_TEMPLATE_SYSTEM.md`

**Recovery Steps**:
1. Read this file in its entirety
2. Check "Current Phase" section below
3. Resume from last completed phase
4. Validate previous phase outputs exist

**Current Phase**: Phase 0 (Planning Complete)
**Last Updated**: 2025-10-15
**Completed Phases**: None (ready to start)

### Rollback Plan

**If Phase 1-2 fails**: Delete template directory
**If Phase 3-4 fails**: Keep completed templates, skip incomplete ones
**If Phase 5 fails**: Templates still usable manually, generator optional
**If Phase 6-7 fails**: Core system works, documentation/integration nice-to-have

---

## 📁 FILE MANIFEST

### Files to Create
1. `claude/templates/project_recovery/PROJECT_PLAN_TEMPLATE.md`
2. `claude/templates/project_recovery/RECOVERY_STATE_TEMPLATE.json`
3. `claude/templates/project_recovery/START_HERE_TEMPLATE.md`
4. `claude/templates/project_recovery/generate_recovery_files.py`
5. `claude/templates/project_recovery/README.md`
6. `claude/templates/project_recovery/examples/` (directory with Phase 119 reference)

### Files to Modify
1. `claude/commands/save_state.md` - Add Phase 0 recovery setup

---

## 🎯 IMPLEMENTATION SEQUENCE

### Session 1 (30 min) - Templates
- Execute Phases 1-4: Create directory + 3 templates
- **Checkpoint**: Templates created and testable manually

### Session 2 (30 min) - Generator
- Execute Phase 5: Build generator script
- Test with sample project
- **Checkpoint**: Generator working end-to-end

### Session 3 (15 min) - Documentation & Integration
- Execute Phases 6-7: README + save state integration
- **Checkpoint**: Complete system documented and integrated

**Total Estimated Time**: 1-1.5 hours across 3 micro-sessions

---

## 💡 ANTI-DRIFT MEASURES

### How to Prevent Project Drift

**1. Always Start by Reading This File**
- If context compaction happens, read from top to bottom
- Check "Current Phase" section
- Resume from last checkpoint

**2. Update Current Phase After Each Session**
```markdown
**Current Phase**: Phase 3 (Templates Complete)
**Last Completed**: Phase 2 - JSON template created
**Last Updated**: 2025-10-15 18:30
**Next Steps**: Build generator script (Phase 5)
```

**3. Maintain File Manifest Checklist**
```markdown
### Files Created (Checkpoint)
- [x] PROJECT_PLAN_TEMPLATE.md (Phase 2 - COMPLETE)
- [x] RECOVERY_STATE_TEMPLATE.json (Phase 3 - COMPLETE)
- [ ] START_HERE_TEMPLATE.md (Phase 4 - PENDING)
- [ ] generate_recovery_files.py (Phase 5 - PENDING)
```

---

## 🔥 COMMON PITFALLS & SOLUTIONS

### Pitfall 1: Templates Too Complex
**Problem**: Over-engineering templates, adding too many fields
**Solution**: Start minimal, expand based on actual usage
**Prevention**: Use Phase 119 as reference (proven pattern)

### Pitfall 2: Generator Edge Cases
**Problem**: Generator fails on special characters, long names
**Solution**: Input validation and sanitization
**Prevention**: Test with variety of project names

### Pitfall 3: Adoption Friction
**Problem**: Users skip recovery setup (too much effort)
**Solution**: Make generator fast (<2 min), integrate with save state
**Prevention**: Add to save state workflow as Phase 0

---

## 📈 METRICS TO TRACK

### Before Implementation (Baseline)
- Project recovery files created: Manual only (30+ min each)
- Multi-phase projects with recovery: ~20% (like Phase 119)
- Context loss incidents: Unknown (not tracked)
- Recovery time after compaction: 15-30 min (re-reading docs)

### After Implementation (Target)
- Project recovery files created: <5 min via generator
- Multi-phase projects with recovery: 100% (integrated with save state)
- Context loss incidents: 0 (recovery files prevent drift)
- Recovery time after compaction: <5 min (START_HERE guide)

### Track These Weekly
- Projects using recovery templates: Count
- Generator usage: How often?
- Recovery file effectiveness: Did they prevent drift?
- Time savings: Actual vs manual creation

---

## ✅ COMPLETION CRITERIA

Project is COMPLETE when:
- [x] Template directory structure created
- [x] PROJECT_PLAN_TEMPLATE.md created with all sections
- [x] RECOVERY_STATE_TEMPLATE.json created with all fields
- [x] START_HERE_TEMPLATE.md created with recovery sequence
- [x] generate_recovery_files.py working (tested end-to-end)
- [x] README.md usage guide complete
- [x] save_state.md updated with Phase 0 integration
- [x] Tested with sample project (not Phase 119)
- [x] User can generate recovery files in <5 min
- [x] Recovery files successfully protect against compaction

---

## 🎯 POST-IMPLEMENTATION

### Week 1: Monitor & Refine
- Track template usage
- Gather feedback on generator
- Adjust templates based on real usage

### Week 2: Expand
- Add more examples (Phase 118, Phase 117, etc.)
- Create project type variants (security, analytics, infrastructure)
- Build interactive mode for generator (vs CLI only)

### Month 1: Optimize
- Add template validation
- Build recovery file linter (check completeness)
- Automate recovery file updates during save state

### Ongoing
- Update templates as patterns evolve
- Maintain examples from recent phases
- Keep generator in sync with template changes

---

## 📝 NOTES & CONTEXT

### Why This Project Matters
Phase 119 demonstrated that comprehensive recovery files prevent context loss and enable instant project resumption. This pattern should be standard for ALL multi-phase work, not manually created each time.

### Design Philosophy
**80/20 Rule**: Templates cover 80% of common structure, generator fills placeholders, user customizes the final 20%.

**Progressive Enhancement**: Start with minimal templates, expand based on real usage patterns.

**Low Friction**: Generator must be <5 min to use, or users will skip it.

### Success Indicators
- User says: "I can resume any project in <5 min after compaction"
- Adoption: "Every multi-phase project has recovery files"
- Quality: "Recovery files actually work when needed"

---

## 🔗 RELATED DOCUMENTATION

- `claude/data/CAPABILITY_AMNESIA_FIX_PROJECT.md` - Reference example (Phase 119)
- `claude/commands/save_state.md` - Integration point
- `claude/context/core/development_workflow_protocol.md` - Project workflow

---

**Project Status**: ✅ PLANNING COMPLETE - Ready for Phase 1 implementation
**Next Step**: Execute Phase 1 - Create template directory structure
**Estimated Time to Complete**: 1-1.5 hours total
**Confidence**: 95% - Pattern proven in Phase 119, clear implementation path

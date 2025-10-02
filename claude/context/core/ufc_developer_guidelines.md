# UFC Developer Guidelines & Auto-Routing Rules

## 🚨 **CRITICAL: File Placement Rules**

### **Automatic File Routing by Type**

| File Type | Correct Location | Purpose | ❌ NEVER Put In |
|-----------|------------------|---------|------------------|
| **`.py` files** | `claude/tools/` | Executable code, utilities, automation | `context/`, `commands/` |
| **`.md` workflows** | `claude/commands/` | Reusable workflows, procedures | `tools/` (unless docs) |
| **`.md` documentation** | `claude/context/` | System knowledge, configuration | `tools/` (unless tool docs) |
| **Agent definitions** | `claude/agents/` | Specialized AI agents | `tools/`, `commands/` |
| **System hooks** | `claude/hooks/` | Git hooks, system integration | `tools/` |
| **Data files** | `claude/data/` | Databases, structured data | `context/` |

## 🔒 **Enforcement Rules**

### **Context Directory (`claude/context/`)**
- **PURPOSE**: Documentation, configuration, schemas ONLY
- **ALLOWED**: `.md`, `.json`, `.sql`, `.yaml`, `.txt`
- **FORBIDDEN**: `.py`, `.sh`, executables
- **RULE**: If it executes code → move to `claude/tools/`

### **Commands Directory (`claude/commands/`)**
- **PURPOSE**: Workflow definitions and procedures ONLY
- **ALLOWED**: `.md` workflow files
- **FORBIDDEN**: `.py` executables
- **RULE**: If it's executable code → move to `claude/tools/`

### **Tools Directory (`claude/tools/`)**
- **PURPOSE**: All executable Python code
- **ALLOWED**: `.py` files, tool documentation
- **STRUCTURE**: Organize by domain (`tools/optimization/`, `tools/security/`)

## 🛠️ **Development Workflow**

### **Before Creating New Files**

1. **Determine File Type**:
   ```bash
   # Is it executable code?     → claude/tools/
   # Is it a workflow process?  → claude/commands/
   # Is it documentation?       → claude/context/
   ```

2. **Check Existing Structure**:
   ```bash
   # Find similar files to understand patterns
   find claude -name "*similar*" -type f
   ```

3. **Use Auto-Router (If Uncertain)**:
   ```bash
   python3 claude/tools/ufc_router.py --suggest /path/to/new/file
   ```

### **File Creation Patterns**

```bash
# ✅ CORRECT Examples
claude/tools/new_analyzer.py           # Executable code
claude/commands/workflow_process.md    # Workflow definition
claude/context/core/system_config.md  # System documentation
claude/agents/specialist_agent.md     # Agent definition

# ❌ INCORRECT Examples
claude/context/analysis_tool.py       # Code in documentation directory
claude/commands/data_processor.py     # Executable in workflow directory
```

## 🚫 **Common Violations & Fixes**

### **Violation 1: Python in Context**
```bash
# ❌ WRONG
claude/context/knowledge/optimizer.py

# ✅ CORRECT
claude/tools/optimization/optimizer.py
```

### **Violation 2: Python in Commands**
```bash
# ❌ WRONG
claude/commands/status_checker.py

# ✅ CORRECT
claude/tools/status_checker.py
```

### **Violation 3: Executables in Documentation**
```bash
# ❌ WRONG
claude/context/tools/runner.sh

# ✅ CORRECT
claude/tools/runner.sh
```

## 🔧 **Auto-Routing Tools**

### **Pre-Commit Validation**
- Automatically blocks commits with UFC violations
- Suggests correct locations for misplaced files
- Prevents context/commands directories from containing `.py` files

### **UFC Router**
```bash
# Auto-suggest correct location
python3 claude/tools/ufc_router.py --suggest /path/to/file

# Auto-move with confirmation
python3 claude/tools/ufc_router.py --route /path/to/file

# Validate entire structure
python3 claude/tools/ufc_cleanup.py --report-only
```

## 📊 **Monitoring & Compliance**

### **Weekly UFC Health Check**
```bash
# Run comprehensive structure validation
python3 claude/tools/ufc_cleanup.py --report-only

# Check for violations
find claude/context -name "*.py" -type f  # Should return nothing
find claude/commands -name "*.py" -type f # Should return nothing
```

### **Pre-Commit Integration**
All commits automatically validated with enhanced UFC rules that:
- Block `.py` files in `context/` or `commands/`
- Enforce proper nesting limits
- Validate file placement against UFC rules
- Suggest corrections for violations

## 🎯 **Success Metrics**

- **Zero UFC violations** in new commits
- **Automatic routing** for 95% of new files
- **Clear separation** between code, workflows, and documentation
- **Consistent structure** maintained across development sessions

## 🚨 **Emergency Fixes**

If you encounter UFC violations:

```bash
# 1. Quick fix current violations
python3 claude/tools/ufc_cleanup.py --route-files --remove-empty

# 2. Update references
grep -r "old/path" claude/ --include="*.py" --include="*.md"

# 3. Test system integrity
python3 claude/tools/bootstrap/health_check.py
```

This systematic approach prevents recurring UFC violations by establishing clear rules, automatic validation, and developer guidance.

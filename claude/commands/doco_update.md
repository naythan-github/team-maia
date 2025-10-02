# Documentation Update Command

## Usage
When user says **"doco update"**, execute this comprehensive documentation synchronization workflow.

## Workflow

### 1. System Documentation Audit
- Search all context files for outdated references
- Identify inconsistencies between documentation and actual implementation
- Check for missing documentation of new features/tools

### 2. Update Priority Files
- `claude/context/tools/available.md` - Core tool documentation
- `claude/context/core/*.md` - System architecture and principles
- `SYSTEM_STATE.md` - Historical accuracy and current state
- `README.md` - Public-facing system description
- Tool-specific README files

### 3. Implementation References
- Verify all file paths and imports are correct
- Update function names and interfaces
- Ensure examples match current API
- Fix any broken internal references

### 4. UFC System Compliance Check
- **Context Loading Violations**: Ensure all files follow smart context loading protocols
- **Directory Structure Compliance**: Verify UFC system structure is intact and documented
- **Mandatory Core Files**: Confirm all required core context files exist and are current
- **Context Dependencies**: Check that documentation matches actual context loading requirements
- **File Path Accuracy**: Validate all context file references use correct UFC paths

### 5. Consistency Check
- Align terminology across all documentation
- Ensure version numbers and status indicators are current
- Verify all tools listed are actually available
- Check that archived/deprecated items are properly marked

### 6. Validation
- Test key documented examples
- Verify critical file paths exist
- Confirm major functionality claims are accurate

## Success Criteria
- ✅ All documentation reflects current implementation
- ✅ No broken internal references
- ✅ Consistent terminology and status indicators
- ✅ Updated historical records in SYSTEM_STATE.md
- ✅ Tool availability matches actual codebase
- ✅ UFC system compliance verified
- ✅ Context loading protocols followed
- ✅ All mandatory core files present and accurate

## Output
Provide summary of:
- Files updated
- Key changes made  
- Any issues discovered
- Verification results
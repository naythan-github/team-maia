# Maia Project Registry - Quick Reference

**One-page cheat sheet for daily use**

---

## 📋 Common Commands

### View Projects

```bash
# List all projects
project_registry.py list

# Filter by status
project_registry.py list --status planned
project_registry.py list --status active

# Filter by priority
project_registry.py list --priority high
project_registry.py list --priority critical

# View prioritized backlog
project_registry.py backlog

# Show project details
project_registry.py show PROJECT-ID
```

### Add New Project

```bash
project_registry.py add \
    --id PROJECT-ID \
    --name "Project Name" \
    --priority high \
    --effort 20 \
    --impact high \
    --category "SRE" \
    --description "Brief description" \
    --plan path/to/plan.md
```

### Update Projects

```bash
# Start working on a project
project_registry.py start PROJECT-ID

# Update priority
project_registry.py update PROJECT-ID --priority critical

# Update status
project_registry.py update PROJECT-ID --status blocked

# Complete project
project_registry.py complete PROJECT-ID --actual-hours 38
```

### Reports & Stats

```bash
# Statistics
project_registry.py stats

# Export to markdown
project_registry.py export --format markdown --output BACKLOG.md

# Export to JSON
project_registry.py export --format json
```

---

## 🎯 Quick Workflows

### Starting a New Project

```bash
# 1. Add to registry
project_registry.py add --id NEW-PROJ-001 --name "New Project" --priority high --effort 10

# 2. Start working
project_registry.py start NEW-PROJ-001

# 3. View details
project_registry.py show NEW-PROJ-001
```

### Weekly Planning

```bash
# 1. Review backlog
project_registry.py backlog

# 2. Check active projects
project_registry.py list --status active

# 3. Update priorities as needed
project_registry.py update PROJECT-ID --priority high
```

### Completing Projects

```bash
# 1. Mark complete with actual hours
project_registry.py complete PROJECT-ID --actual-hours 15

# 2. Regenerate backlog
project_registry.py export --format markdown --output MAIA_PROJECT_BACKLOG.md
```

---

## 📊 Valid Values

### Status
- `planned` - Not started yet
- `active` - Currently working on
- `blocked` - Waiting on dependencies
- `completed` - Finished
- `archived` - No longer relevant

### Priority
- `critical` - Urgent, high impact
- `high` - Important
- `medium` - Standard priority
- `low` - Nice to have

### Impact
- `high` - Significant business impact
- `medium` - Moderate impact
- `low` - Minor impact

---

## 🗂️ Project ID Format

**Pattern**: `CATEGORY-NAME-###`

**Examples**:
- `REPO-GOV-001` - Repository Governance project
- `SRE-MON-042` - SRE Monitoring project
- `SD-ETL-015` - ServiceDesk ETL project

**Rules**:
- Uppercase letters, numbers, and hyphens only
- Keep under 30 characters
- Use descriptive prefixes

---

## 📁 File Locations

**Database**: `claude/data/project_registry.db`
**CLI Tool**: `claude/tools/project_management/project_registry.py`
**Migration**: `claude/tools/project_management/migrate_existing_projects.py`
**Backlog**: `MAIA_PROJECT_BACKLOG.md` (auto-generated)

---

## 🔧 Troubleshooting

### Database not found
```bash
# Check you're in maia root directory
cd ~/git/maia

# Or set MAIA_ROOT environment variable
export MAIA_ROOT=/path/to/maia
```

### Project already exists
```bash
# Check if project exists
project_registry.py show PROJECT-ID

# Use different ID or update existing
project_registry.py update PROJECT-ID --priority high
```

### View raw database
```bash
sqlite3 claude/data/project_registry.db
.tables
SELECT * FROM projects LIMIT 5;
.exit
```

---

## 🚀 Advanced Usage

### Add Dependencies

```bash
project_registry.py depend add \
    --project PROJ-B \
    --depends-on PROJ-A \
    --type blocks
```

### Filter by Category

```bash
project_registry.py list --category SRE
project_registry.py list --category ServiceDesk
```

### Export Specific Status

```bash
# Export only completed projects
project_registry.py export --format markdown --status completed
```

---

## 💡 Tips

1. **Use descriptive project IDs** - Makes searching easier
2. **Update backlog weekly** - Run `backlog` command Monday mornings
3. **Track actual hours** - Improves future estimates
4. **Set priorities realistically** - Not everything is critical
5. **Review stats monthly** - Check velocity and adjust estimates

---

## 🆘 Help

```bash
# General help
project_registry.py --help

# Command-specific help
project_registry.py add --help
project_registry.py list --help
project_registry.py update --help
```

---

**Project**: PROJ-REG-001 - Maia Project Registry System
**Last Updated**: 2025-10-27
**Version**: 1.0

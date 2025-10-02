# Confluence Organization Commands

## Overview
Commands for intelligent Confluence space organization, content placement, and folder management using the Confluence Organization Agent.

## Available Commands

### scan_confluence_spaces
Analyze Confluence space structures and organizational patterns.

**Usage:**
```bash
# Scan all accessible spaces
python3 claude/tools/confluence_organization_manager.py scan

# Scan specific spaces
python3 claude/tools/confluence_organization_manager.py scan --spaces Maia Orro NAYT
```

**Purpose:**
- Analyze page hierarchies and organizational patterns
- Cache space structures for intelligent placement suggestions
- Identify existing organizational patterns and gaps
- Build foundation for content placement recommendations

### suggest_content_placement
Analyze content and get intelligent placement suggestions.

**Usage:**
```python
from claude.tools.confluence_organization_manager import ConfluenceOrganizationManager

manager = ConfluenceOrganizationManager()

# Analyze content for placement
suggestions = manager.suggest_content_placement(
    content="Your document content here",
    title="Document Title",
    content_type="technical_doc"  # Optional
)

# Interactive selection
selected_placement = manager.interactive_folder_selection(suggestions)
```

**Content Types:**
- `meeting_notes` - Meeting minutes, agendas, action items
- `technical_doc` - API docs, architecture, deployment guides
- `project_plan` - Project plans, roadmaps, milestones
- `process_guide` - Procedures, workflows, how-to guides
- `policy` - Policies, guidelines, compliance docs
- `training` - Training materials, tutorials, courses
- `reference` - Reference docs, manuals, specifications
- `status_update` - Status reports, progress updates

### interactive_folder_selection
Present organized folder selection interface with confidence scoring.

**Features:**
- Visual confidence indicators
- Reasoning for each suggestion
- Option to create custom folders
- Interactive space and parent page selection

### create_intelligent_folder
Create new organizational folders based on content analysis.

**Usage:**
```python
# Create folder based on placement suggestion
result = manager.create_intelligent_folder(
    placement=selected_placement,
    folder_name="API Documentation"
)
```

**Capabilities:**
- Creates folder with descriptive content
- Sets up proper parent-child relationships
- Logs organizational actions for tracking
- Provides creation feedback and URLs

### confluence_space_audit
Get comprehensive organizational status and recommendations.

**Usage:**
```bash
python3 claude/tools/confluence_organization_manager.py status
```

**Provides:**
- Number of spaces analyzed
- Total pages scanned
- Recent organizational actions
- Organizational health metrics

## Agent Integration

### Using the Confluence Organization Agent

**Direct Agent Call:**
```
Use the Confluence Organization Agent to analyze my document and suggest where to place it in Confluence.
```

**Agent Commands:**
- `scan_confluence_spaces` - Analyze space structures
- `suggest_content_placement` - Get placement recommendations
- `interactive_folder_selection` - Choose placement location
- `create_intelligent_folders` - Create organizational structure
- `organize_confluence_content` - Complete organization workflow
- `confluence_space_audit` - Organization assessment

### Integration with Other Agents
- **Personal Assistant Agent** - Coordinate content organization with daily workflows
- **Security Specialist Agent** - Ensure proper access controls on new folders
- **Company Research Agent** - Use company intelligence for context-appropriate organization
- **Blog Writer Agent** - Organize published content systematically

## Workflow Examples

### Basic Content Placement
1. **Scan Spaces**: `scan_confluence_spaces` to analyze organizational patterns
2. **Analyze Content**: `suggest_content_placement` for intelligent recommendations
3. **Interactive Selection**: Choose from suggested placements
4. **Create Structure**: Automatically create folders if needed

### Custom Organization Project
1. **Space Audit**: Assess current organizational state
2. **Gap Analysis**: Identify missing organizational structures
3. **Architecture Design**: Plan optimal organizational hierarchy
4. **Implementation**: Create folders and reorganize content
5. **Validation**: Verify improvements and user satisfaction

### Daily Content Management
1. **Content Analysis**: Analyze new documents for placement
2. **Smart Suggestions**: Get AI-powered placement recommendations
3. **Quick Placement**: Use learned preferences for fast decisions
4. **Structure Evolution**: Continuously improve organization based on usage

## Configuration

### Database Storage
- **Location**: `claude/data/confluence_organization.db`
- **Tables**: 
  - `space_hierarchies` - Cached space structures
  - `placement_preferences` - Learned user preferences
  - `organization_history` - Action tracking

### Integration with Reliable Confluence Client
- Uses existing SRE-grade Confluence connection
- Leverages proven API reliability patterns
- Maintains authentication and session management
- Inherits circuit breaker and retry logic

## Benefits

### Intelligence Features
- **Content Analysis**: Understand document types and topics automatically
- **Pattern Recognition**: Learn from existing organizational patterns
- **Preference Learning**: Adapt to user organizational preferences
- **Smart Suggestions**: Provide confident placement recommendations

### User Experience
- **Interactive Selection**: Clear, organized choices with confidence scoring
- **Visual Feedback**: Progress indicators and success confirmations
- **Flexible Options**: Support both suggested and custom placements
- **Minimal Friction**: Streamlined workflow for daily content management

### Organizational Impact
- **Consistent Structure**: Apply systematic organizational patterns
- **Improved Findability**: Better content discovery and navigation
- **Scalable Organization**: Structures that grow with content volume
- **Knowledge Preservation**: Systematic knowledge management practices

This system transforms chaotic Confluence spaces into well-organized, navigable knowledge bases while learning your preferences and improving over time.
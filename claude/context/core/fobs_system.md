# FOBs System - File-Operated Behaviors

## Overview
Dynamic tool creation system that converts markdown files into executable MCP tools within seconds.

## Core Concept
**FOB = File-Operated Behaviors** (dynamic tool creation from file system)
- Every markdown file in `/claude/tools/fobs/` becomes an executable tool
- File watcher detects new/changed FOB files
- MCP server automatically generates tool definitions
- Tools become available to Maia within 5 seconds

## System Architecture

### Components
```
FOBs System
├── File Watcher (Python)     # Monitors fobs/ directory for changes
├── FOB Parser (Python)       # Extracts tool definition from markdown
├── MCP Generator (Python)    # Creates MCP tool definitions
├── MCP Server (FastMCP)      # Serves dynamic tools to Claude Code
└── FOB Templates (Markdown)  # Reusable patterns for common tasks
```

### Data Flow
```
1. User creates: /claude/tools/fobs/new_tool.md
2. File Watcher: Detects new file
3. FOB Parser: Extracts tool schema and logic  
4. MCP Generator: Creates MCP tool definition
5. MCP Server: Makes tool available to Maia
6. Claude Code: Tool appears in available tools
7. Total time: <5 seconds
```

## FOB Markdown Format

### Standard FOB Structure
```markdown
# Tool Name

## Description
Brief description of what this tool does

## Parameters
- param1: type (required/optional) - Description
- param2: type (required/optional) - Description

## Logic
```python
def execute_tool(param1, param2):
    """
    Tool execution logic
    """
    # Implementation here
    return result
```

## Example Usage
How to use this tool from Maia
```

### FOB Example: "Talk Like Cat"
```markdown
# Talk Like Cat

## Description
Transforms input text to cat-like speech patterns with meows and feline expressions

## Parameters
- text: string (required) - Text to transform into cat speech

## Logic
```python
def execute_tool(text):
    """
    Transform text to cat-like speech
    """
    import re
    
    # Add cat expressions
    cat_text = text.replace(".", ", meow.")
    cat_text = cat_text.replace("!", ", meow!")
    cat_text = cat_text.replace("?", ", meow?")
    
    # Add purr sounds occasionally
    cat_text = re.sub(r'\b(I|me|my)\b', r'this kitty', cat_text, flags=re.IGNORECASE)
    cat_text = cat_text.replace("very", "purr-fectly")
    
    return f"🐱 {cat_text} *purrs contentedly*"
```

## Example Usage
Input: "I am very happy today!"
Output: "🐱 This kitty am purr-fectly happy today, meow! *purrs contentedly*"
```

## Implementation Strategy

### Phase 1: Basic FOB System
1. **Directory Setup**: `/claude/tools/fobs/` with initial patterns
2. **File Watcher**: Python script monitoring for changes
3. **FOB Parser**: Extract tool definitions from markdown
4. **Basic MCP Server**: Serve 5-10 initial FOBs

### Phase 2: Advanced Features  
1. **Template System**: Reusable FOB templates
2. **Parameter Validation**: Type checking and validation
3. **Error Handling**: Graceful failures and debugging
4. **Performance Optimization**: Caching and efficient reloading

### Phase 3: Integration
1. **Agent Integration**: FOBs available to all agents
2. **Command Chaining**: FOBs can call other FOBs
3. **Context Awareness**: FOBs can access UFC context
4. **Web Interface**: FOB management dashboard

## Initial FOB Collection

### Essential FOBs (First 10)
1. **text_analyzer** - Analyze text for sentiment, keywords, etc.
2. **url_summarizer** - Summarize content from any URL
3. **email_formatter** - Format professional emails
4. **meeting_notes_extractor** - Extract action items from meeting notes  
5. **job_post_analyzer** - Parse job requirements from job posting
6. **linkedin_post_generator** - Create LinkedIn posts on topics
7. **markdown_to_word** - Convert markdown to Word format
8. **password_generator** - Generate secure passwords
9. **calendar_time_finder** - Find free time slots
10. **contact_formatter** - Format contact information consistently

### Professional FOBs (Next 10)
1. **cv_section_writer** - Write specific CV sections
2. **cover_letter_paragraph** - Generate cover letter paragraphs
3. **salary_negotiator** - Create salary negotiation scripts
4. **interview_question_generator** - Generate interview questions
5. **project_status_updater** - Format project status updates
6. **risk_assessor** - Assess project/business risks
7. **stakeholder_communicator** - Draft stakeholder communications
8. **budget_analyzer** - Analyze budget allocations
9. **meeting_agenda_creator** - Create structured meeting agendas
10. **decision_matrix** - Create decision comparison matrices

## Technical Implementation

### File Watcher (Python)
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from pathlib import Path

class FOBHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith('.md'):
            self.process_fob(event.src_path)
    
    def process_fob(self, file_path):
        # Parse FOB and update MCP server
        pass
```

### FOB Parser
```python
def parse_fob_markdown(file_path):
    """
    Extract tool definition from FOB markdown
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract sections using regex
    tool_name = extract_section(content, "# (.+)")
    description = extract_section(content, "## Description\\n(.+?)\\n##")
    parameters = parse_parameters(content)
    logic = extract_code_block(content, "python")
    
    return {
        "name": tool_name,
        "description": description,
        "parameters": parameters,
        "logic": logic
    }
```

### MCP Server Integration
```python
from fastmcp import MCP
import importlib.util

class FOBMCPServer:
    def __init__(self):
        self.tools = {}
        self.mcp = MCP()
    
    def register_fob(self, fob_definition):
        """
        Register a new FOB as an MCP tool
        """
        tool_name = fob_definition["name"]
        
        # Create dynamic function from FOB logic
        exec(fob_definition["logic"])
        
        # Register with MCP
        self.mcp.tool(tool_name)(execute_tool)
        self.tools[tool_name] = fob_definition
    
    def start_server(self):
        self.mcp.run()
```

## Success Metrics

### Development Velocity
- **Tool Creation Time**: <2 minutes to write FOB
- **Deployment Time**: <5 seconds to availability
- **Modification Time**: <10 seconds for updates

### System Performance  
- **FOB Count**: Support 100+ simultaneous FOBs
- **Response Time**: <500ms for simple FOBs
- **Memory Usage**: <50MB for FOB system

### User Experience
- **Learning Curve**: 5 minutes to create first FOB
- **Reliability**: 99% uptime for FOB system
- **Flexibility**: Cover 80% of common automation tasks

## Integration with Existing Systems

### Maia Agents
- All agents automatically have access to FOBs
- FOBs appear in agent tool listings
- Agents can chain FOBs for complex workflows

### Advanced Commands
- Multi-agent commands can utilize FOBs
- FOBs can be building blocks for complex orchestration
- Context passing between FOBs and agents

### UFC Context System
- FOBs can read UFC context files
- FOBs inherit user profile and preferences
- FOBs maintain context consistency

This FOBs system will transform Maia from having ~30 static commands to potentially hundreds of dynamic, customizable tools that can be created and modified in minutes.
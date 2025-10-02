# Confluence Page Creator FOB

## Description
Creates properly formatted Confluence pages with working checkboxes, clean layouts, and mobile-responsive design. Handles the complexity of Confluence storage format XML correctly.

## Purpose
Prevents hand-coding Confluence XML and ensures consistent, working page formatting every time.

## Parameters
- space_key: string (required) - Confluence space key (e.g., "Orro")
- title: string (required) - Page title
- content_type: string (required) - Type of page: "checklist", "dashboard", "tracker", "meeting_notes", "stakeholder_map"
- data: dict (required) - Content data structure (varies by content_type)
- parent_id: string (optional) - Parent page ID for hierarchy

## Content Types & Data Structures

### checklist
```python
data = {
    "sections": [
        {
            "title": "Section Name",
            "priority": "P0|P1|P2",  # optional
            "items": [
                {
                    "id": "unique_id",
                    "text": "Item text",
                    "owner": "Owner name",  # optional
                    "answer_field": True|False  # optional, adds answer space
                }
            ]
        }
    ],
    "summary": {
        "total": 31,
        "completed": 0
    }
}
```

### dashboard
```python
data = {
    "sections": [
        {
            "title": "Section Name",
            "tasks": [
                {
                    "id": "unique_id",
                    "text": "Task description",
                    "owner": "Owner",
                    "due": "YYYY-MM-DD",
                    "status": "complete|incomplete"
                }
            ]
        }
    ]
}
```

### tracker
```python
data = {
    "items": [
        {
            "id": "unique_id",
            "text": "Tracked item",
            "status": "complete|incomplete",
            "metadata": {}  # flexible key-value pairs
        }
    ]
}
```

## Logic
```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from claude.tools.reliable_confluence_client import ReliableConfluenceClient

def execute_tool(space_key, title, content_type, data, parent_id=None):
    \"\"\"
    Create properly formatted Confluence page
    \"\"\"
    client = ReliableConfluenceClient()

    # Build content based on type
    if content_type == "checklist":
        content = _build_checklist(data)
    elif content_type == "dashboard":
        content = _build_dashboard(data)
    elif content_type == "tracker":
        content = _build_tracker(data)
    elif content_type == "meeting_notes":
        content = _build_meeting_notes(data)
    elif content_type == "stakeholder_map":
        content = _build_stakeholder_map(data)
    else:
        return {"error": f"Unknown content_type: {content_type}"}

    # Create page
    result = client.create_page(
        space_key=space_key,
        title=title,
        content=content,
        parent_id=parent_id
    )

    if result:
        page_id = result['id']
        url = f"https://vivoemc.atlassian.net/wiki/spaces/{space_key}/pages/{page_id}"
        return {
            "success": True,
            "page_id": page_id,
            "url": url,
            "title": title
        }
    else:
        return {"error": "Failed to create page"}

def _build_checklist(data):
    \"\"\"Build checklist format with working checkboxes\"\"\"
    sections = data.get('sections', [])
    summary = data.get('summary', {})

    content = []

    # Header with summary
    if summary:
        total = summary.get('total', 0)
        completed = summary.get('completed', 0)
        pct = (completed / total * 100) if total > 0 else 0
        content.append(f'<p><strong>Progress:</strong> {completed}/{total} ({pct:.0f}%)</p>')

    content.append('<hr />')

    # Sections with checkboxes
    for section in sections:
        section_title = section.get('title', '')
        priority = section.get('priority', '')
        items = section.get('items', [])

        # Section header with optional priority emoji
        priority_emoji = {
            'P0': '🔴',
            'P1': '🟡',
            'P2': '🟢'
        }.get(priority, '')

        content.append(f'<h3>{priority_emoji} {section_title}</h3>')
        content.append('<ac:task-list>')

        for item in items:
            item_id = item.get('id', '')
            text = item.get('text', '')
            owner = item.get('owner', '')
            answer_field = item.get('answer_field', False)

            task_text = f'<strong>{text}</strong>'
            if owner:
                task_text += f' (Owner: {owner})'
            if answer_field:
                task_text += ' → <em>Answer:</em>'

            content.append(
                f'<ac:task><ac:task-id>{item_id}</ac:task-id>'
                f'<ac:task-status>incomplete</ac:task-status>'
                f'<ac:task-body>{task_text}</ac:task-body></ac:task>'
            )

        content.append('</ac:task-list>')
        content.append('<hr />')

    return '\\n'.join(content)

def _build_dashboard(data):
    \"\"\"Build dashboard format with task lists\"\"\"
    sections = data.get('sections', [])

    content = []
    content.append('<p><em>Updated: Today | Auto-tracked</em></p>')
    content.append('<hr />')

    for section in sections:
        section_title = section.get('title', '')
        tasks = section.get('tasks', [])

        content.append(f'<h3>{section_title}</h3>')
        content.append('<ac:task-list>')

        for task in tasks:
            task_id = task.get('id', '')
            text = task.get('text', '')
            owner = task.get('owner', '')
            due = task.get('due', '')
            status = task.get('status', 'incomplete')

            task_text = f'<strong>{text}</strong>'
            if owner:
                task_text += f' (Owner: {owner})'
            if due:
                task_text += f' - Due: {due}'

            content.append(
                f'<ac:task><ac:task-id>{task_id}</ac:task-id>'
                f'<ac:task-status>{status}</ac:task-status>'
                f'<ac:task-body>{task_text}</ac:task-body></ac:task>'
            )

        content.append('</ac:task-list>')
        content.append('<hr />')

    return '\\n'.join(content)

def _build_tracker(data):
    \"\"\"Build simple tracker format\"\"\"
    items = data.get('items', [])

    content = ['<ac:task-list>']

    for item in items:
        item_id = item.get('id', '')
        text = item.get('text', '')
        status = item.get('status', 'incomplete')
        metadata = item.get('metadata', {})

        task_text = f'<strong>{text}</strong>'
        if metadata:
            task_text += ' - ' + ', '.join(f'{k}: {v}' for k, v in metadata.items())

        content.append(
            f'<ac:task><ac:task-id>{item_id}</ac:task-id>'
            f'<ac:task-status>{status}</ac:task-status>'
            f'<ac:task-body>{task_text}</ac:task-body></ac:task>'
        )

    content.append('</ac:task-list>')
    return '\\n'.join(content)

def _build_meeting_notes(data):
    \"\"\"Build meeting notes format\"\"\"
    # TODO: Implement meeting notes format
    return "<p>Meeting notes format coming soon</p>"

def _build_stakeholder_map(data):
    \"\"\"Build stakeholder relationship map\"\"\"
    # TODO: Implement stakeholder map format
    return "<p>Stakeholder map format coming soon</p>"
```

## Example Usage

### Create Onboarding Checklist
```python
confluence_page_creator(
    space_key="Orro",
    title="🚀 Onboarding Questions",
    content_type="checklist",
    data={
        "sections": [
            {
                "title": "P0 - Blocking",
                "priority": "P0",
                "items": [
                    {"id": "q1", "text": "Order laptop", "owner": "IT", "answer_field": True},
                    {"id": "q2", "text": "Confirm Super", "owner": "HR", "answer_field": True}
                ]
            }
        ],
        "summary": {"total": 2, "completed": 0}
    }
)
```

### Create Action Dashboard
```python
confluence_page_creator(
    space_key="Orro",
    title="📋 Action Items",
    content_type="dashboard",
    data={
        "sections": [
            {
                "title": "🔴 Urgent - This Week",
                "tasks": [
                    {"id": "t1", "text": "Send JDs", "owner": "Naythan", "due": "2025-10-03", "status": "incomplete"}
                ]
            }
        ]
    }
)
```

## Benefits
- ✅ Consistent formatting across all pages
- ✅ Working checkboxes (no table complexity)
- ✅ Mobile-responsive design
- ✅ Clean, readable layouts
- ✅ Reusable for future page creation
- ✅ Prevents XML hand-coding errors

## Future Enhancements
- Table support (when we figure out checkbox-in-table format)
- Meeting notes templates
- Stakeholder relationship maps
- Auto-update existing pages
- Batch page creation

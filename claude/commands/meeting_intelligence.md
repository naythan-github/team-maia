# Meeting Intelligence Command

## Purpose
Comprehensive meeting intelligence processing using Maia's integrated pipeline.

## Usage

### Quick Processing
```bash
# Simple text processing
meeting_intelligence "Your meeting notes here..."

# Process from file
meeting_intelligence --file /path/to/meeting_notes.txt

# With meeting details
meeting_intelligence --file meeting_notes.txt \
  --title "Sprint Planning" \
  --participants "John,Sarah,Mike" \
  --type "planning"
```

### Full Integration Mode
```bash
# Process with all integrations
meeting_intelligence --file meeting_notes.txt \
  --title "Architecture Review" \
  --full-integration
```

### Management Commands
```bash
# View all pending actions
meeting_intelligence --pending

# Update action status
meeting_intelligence --update-action ACTION_ID --status completed

# Get meeting summary
meeting_intelligence --summary MEETING_ID
```

## Command Implementation
This command uses the Integrated Meeting Intelligence Pipeline for:
- Multi-LLM cost-optimized processing (58.3% savings)
- Knowledge Management System integration
- Confluence documentation
- Action item tracking with cross-session persistence

## Agent Chain
1. **Integrated Meeting Intelligence Tool**
   - Input: Raw meeting notes, metadata
   - Output: Structured meeting intelligence
   
2. **Knowledge Management System**
   - Input: Extracted action items and decisions
   - Output: Persistent backlog integration
   
3. **Confluence Documentation**
   - Input: Structured meeting data
   - Output: Formatted documentation with action tracking

## Engineering Manager Benefits
- Nothing gets lost between meetings
- Automatic accountability tracking
- Executive visibility into team actions
- Cost-optimized AI processing
- Cross-session project continuity
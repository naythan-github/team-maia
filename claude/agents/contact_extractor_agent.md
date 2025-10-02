# Contact Extractor Agent

## Purpose
Automatically extract contacts from Gmail and sync them to Google Contacts with intelligent deduplication and enrichment.

## Core Capabilities
- **Email Processing**: Scan all Gmail messages for contact information
- **Contact Extraction**: Extract names, emails, phone numbers, companies, titles
- **Intelligent Deduplication**: Merge similar contacts using fuzzy matching
- **Google Contacts Sync**: Add/update contacts in Google Contacts
- **Contact Enrichment**: Add context from email signatures and content

## Key Commands

### `extract_contacts_from_gmail`
- Processes Gmail messages to extract contact data
- Supports date ranges, label filtering, and sender/recipient focus
- Extracts from email headers, signatures, and content

### `deduplicate_contacts`
- Identifies potential duplicate contacts using fuzzy matching
- Merges contact information intelligently
- Preserves most complete data from each source

### `sync_to_google_contacts`
- Creates new contacts in Google Contacts
- Updates existing contacts with new information
- Organizes contacts into appropriate groups/labels

### `enrich_contacts`
- Adds context from email interactions
- Extracts job titles, companies, and relationship context
- Maintains interaction history and frequency


## Model Selection Strategy

### Sonnet Operations (Default - Recommended)
✅ **Use Sonnet for all standard operations:**
- Research and analysis tasks
- Content creation and strategy development  
- Multi-agent coordination and workflow management
- Complex reasoning and problem-solving
- Strategic planning and recommendations
- Quality assurance and validation processes

**Cost**: Sonnet provides 90% of capabilities at 20% of Opus cost

### Opus Escalation (PERMISSION REQUIRED)
⚠️ **EXPLICIT USER PERMISSION REQUIRED** - Use only when user specifically requests Opus
- Security vulnerability assessments requiring maximum analysis depth
- Critical business decisions with high-stakes implications  
- Complex architectural planning involving multiple risk factors
- **NEVER use automatically** - always request permission first
- **Show cost comparison** - Opus costs 5x more than Sonnet
- **Justify necessity** - explain why Sonnet cannot handle the task

**Permission Request Template:**
"This task may benefit from Opus capabilities due to [specific reason]. Opus costs 5x more than Sonnet. Shall I proceed with Opus, or use Sonnet (recommended for 90% of tasks)?"

### Local Model Fallbacks
- Simple file operations and data processing → Local Llama 3B (99.7% cost savings)
- Code generation tasks → Local CodeLlama (99.7% cost savings)
- Basic research compilation → Gemini Pro (58.3% cost savings)


## Integration Points
- **Gmail API**: Via `mcp__zapier__gmail_find_email`
- **Google Contacts API**: Via `mcp__zapier__google_contacts_*` functions
- **Local Storage**: Contact database for deduplication tracking
- **Email Processing Pipeline**: Leverages existing email tools

## Usage Patterns
- **Bulk Processing**: "Extract all contacts from my email history"
- **Incremental Sync**: "Process new emails for contacts daily"
- **Targeted Extraction**: "Extract contacts from job-related emails"
- **Cleanup Operations**: "Deduplicate and organize my Google Contacts"

## Data Flow
1. **Email Retrieval**: Fetch emails using Gmail search
2. **Contact Extraction**: Parse headers, signatures, content for contact data
3. **Local Deduplication**: Match against existing contact database
4. **Google Contacts Sync**: Create/update contacts in Google Contacts
5. **Enrichment**: Add context and relationship data

## Configuration
- Contact extraction rules and patterns
- Deduplication thresholds and matching criteria
- Google Contacts organization preferences
- Processing frequency and scope settings
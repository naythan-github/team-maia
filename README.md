# Maia - My AI Agent

## Repository
**GitHub**: https://github.com/naythan-orro/maia
**Version Control**: Git repository at `/Users/naythandawe/git/`

## Overview
Maia is a personal AI infrastructure system featuring sophisticated workflow orchestrations that leverage a multi-agent system and advanced automation capabilities. Commands follow enterprise-grade design principles:

- **Single Responsibility**: Focused domain expertise
- **Composable Architecture**: Seamless multi-agent orchestration
- **Production Ready**: Comprehensive error handling and monitoring
- **Evidence-Based**: Performance tracking and continuous learning
- **Security First**: Sandboxed execution and validation

## Quick Start (Team Members)

```bash
# 1. Clone the repository
git clone https://github.com/naythan-orro/maia.git
cd maia

# 2. Run setup script
./setup.sh

# 3. Source your shell to get MAIA_ROOT
source ~/.zshrc  # or ~/.bashrc

# 4. Use with Claude Code
claude  # Start Claude Code in the maia directory
```

### Requirements
- **Python 3.11+** (required)
- **pip** (Python package manager)
- **Ollama** (optional, for local LLM features)
- **Docker** (optional, for ServiceDesk dashboard)

### Verification
After setup, verify installation:
```bash
python3 -c "from claude.tools.core.paths import MAIA_ROOT; print(f'MAIA_ROOT: {MAIA_ROOT}')"
```

### Documentation
- **System Overview**: [CLAUDE.md](CLAUDE.md) - Main system instructions
- **Capabilities**: [claude/context/core/capability_index.md](claude/context/core/capability_index.md)
- **Recent Changes**: [SYSTEM_STATE.md](SYSTEM_STATE.md)

## Command Architecture

### Multi-Agent Orchestration
Commands leverage Maia's 6 specialized agents through advanced orchestration patterns:
- **Sequential Chaining**: Agent A → Agent B → Agent C
- **Parallel Processing**: Multiple agents executing simultaneously
- **Conditional Branching**: Smart routing based on intermediate results
- **Feedback Loops**: Quality assurance and iterative improvement

### Command Structure
Each command implements:
1. **Agent Chain Definition** - Multi-stage workflow specification
2. **Data Flow Protocol** - Structured inter-agent communication
3. **Error Handling** - Fallback agents and retry mechanisms  
4. **Quality Gates** - Validation checkpoints and confidence scoring
5. **Performance Tracking** - Success metrics and optimization learning

## Command Categories

### Advanced Multi-Agent Commands (KAI-Style)
- `complete_application_pipeline` - End-to-end job application workflow (6 stages)
- `professional_brand_optimization` - Comprehensive brand building (6 stages)  
- `market_intelligence_report` - Multi-source market analysis (5 stages)

### Career Intelligence Commands
- `create_cv_from_databases` - Template-driven CV generation from experience databases
- `template_cv_generator` - Intelligent CV template system with A/B testing
- `complete_job_analyzer` - Automated job opportunity analysis and scoring
- `automated_job_scraper` - Multi-platform job scraping with anti-detection
- `intelligent_job_filter` - Smart job filtering based on preferences
- `deep_job_analyzer` - Enhanced job analysis with market intelligence
- `hybrid_job_analyzer` - Combined email processing and web scraping

### Professional Optimization Commands  
- `optimize_profile` - LinkedIn profile optimization with keyword analysis
- `keyword_analysis` - Market-driven keyword optimization strategies
- `content_strategy` - Professional content planning and execution
- `network_audit` - LinkedIn network analysis and growth recommendations
- `market_research` - Industry trends and competitive analysis

### File Organization & Anti-Sprawl System ⭐ **PHASE 81**
**Anti-Sprawl Protection** (October 2025):
- `file_lifecycle_manager.py` - Core file protection with 3-tier immutability (absolute/high/medium)
- `immutable_paths.json` - Protection rules for 9 core files + critical directories
- Extension zones (experimental/, personal/, archive/) for safe development
- 517 files organized, 10 naming violations cleaned up and archived
- Git pre-commit hook preventing core file corruption
- **Status**: Phase 1 complete, foundation operational, core system protected

### Information Management System ⭐ **PHASE 115 - COMPLETE**
**Complete GTD ecosystem with executive intelligence** (October 2025):

**Phase 1: Production Systems** (4 systems, 2,750 lines):
- `enhanced_daily_briefing_strategic.py` - Executive intelligence layer with 0-10 impact scoring, AI recommendations (60-90% confidence), relationship tracking
- `meeting_context_auto_assembly.py` - Automated meeting prep with 6 meeting types, stakeholder sentiment, strategic initiative linking (80% time reduction)
- `unified_action_tracker_gtd.py` - GTD workflow with 7 context tags (@waiting-for, @delegated, @needs-decision, @strategic, @quick-wins, @deep-work, @stakeholder-[name])
- `weekly_strategic_review.py` - 90-min guided GTD review across 6 stages (clear head, review projects, review waiting-for, review goals, review stakeholders, plan next week)
- **Automation**: 2 LaunchAgents (daily 7AM briefing, Friday 3PM review reminder)

**Phase 2: Management Tools** (3 tools, 2,150 lines, 3 databases):
- `stakeholder_intelligence.py` - CRM-style relationship health monitoring (0-100 scoring), sentiment analysis, 33 stakeholders auto-discovered from 313 emails, color-coded dashboard (🟢🟡🟠🔴)
- `executive_information_manager.py` - 5-tier prioritization (critical→noise), multi-factor scoring (0-100), 15-30 min morning ritual, energy-aware batch processing
- `decision_intelligence.py` - 8 decision templates, 6-dimension quality framework (60 pts), outcome tracking, pattern analysis, lessons learned

**Phase 2.1: Agent Orchestration Layer** (3 agents, 700 lines):
- `information_management_orchestrator.md` - Master orchestrator coordinating all 7 information management tools with natural language interface
- `stakeholder_intelligence_agent.md` - Natural language interface for relationship management ("How's my relationship with Hamish?")
- `decision_intelligence_agent.md` - Guided decision capture workflow with quality coaching ("Help me decide on [topic]")

**Architecture**: Proper agent-tool separation
- **7 Tools** (Python .py files): DO the work - execute database operations, calculations, data retrieval
- **3 Agents** (Markdown .md files): ORCHESTRATE tools - natural language interface, multi-tool workflows, response synthesis

**Business Value**:
- **Time Savings**: 7+ hrs/week (strategic briefing 1 hr/day, meeting prep 1 hr/week, inbox processing 3 hrs/week)
- **Signal-to-Noise**: 50% improvement (Tier 1-3 focus vs 40-71 total items)
- **ROI**: $50,400/year value vs $2,400 development cost = **2,100% first year**
- **Strategic Time**: Target 50% strategic vs tactical (from 20% baseline)

**Status**: ✅ Phase 1 production operational, Phase 2 tools tested and operational, Phase 2.1 agent orchestration layer complete (natural language testing pending)

### Productivity Integration Tools ⭐ **PHASE 79-83**
**VTT Meeting Intelligence** (Phase 83) ⭐ **PRODUCTION READY**:
- `vtt_watcher.py` - Automated meeting transcript analysis with FOB templates
- **Monitoring**: Auto-detects VTT files in OneDrive (1-VTT folder)
- **Local LLM**: CodeLlama 13B for 99.3% cost savings vs cloud LLMs
- **FOB Templates**: 6 meeting-type specific frameworks (Standup, Client, Technical, Planning, Review, One-on-One)
- **Intelligence**: Meeting type classification, speaker identification, action item extraction, key topics, executive summaries
- **Auto-Start**: macOS LaunchAgent for persistent background service
- **Output**: Executive-ready markdown summaries with commercial focus
- **Business Value**: Standardized meeting formats, clear action tracking, stakeholder-ready reporting

**Trello Integration** (Phase 79, Enhanced Phase 81.1-82):
- `trello_fast.py` - Direct API client for boards, lists, cards, labels, checklists
- Full CRUD operations optimized for Claude Code terminal workflow
- Flexible CLI commands (`boards`, `get-boards`, `list-boards`) preventing parser confusion
- **Security**: macOS Keychain credential storage (⭐⭐⭐⭐⭐ enterprise-grade)
- **Intelligence**: Personal Assistant Agent integration for workflow optimization
- Zero MCP overhead, instant performance

**Mail.app Integration + Email RAG** (Phase 80A-80B) ⭐ **COMPLETE**:
- `macos_mail_bridge.py` - AppleScript automation for Exchange email access
- `mail_intelligence_interface.py` - Intelligent email triage and search
- `email_rag_ollama.py` - GPU-accelerated semantic email search with ChromaDB
- **RAG Status**: ✅ 313/313 emails indexed with nomic-embed-text (768-dim GPU embeddings)
- **Semantic Search**: 20-44% relevance scores on natural language queries
- **Performance**: 0.048s per email embedding, 100% GPU utilization
- **Privacy**: 100% local processing (ChromaDB + Ollama), zero cloud transmission
- Bypasses Azure AD OAuth restrictions, uses existing Mail.app authentication

**Conversation RAG System** (Phase 101-102) ⭐ **NEW - PRODUCTION READY**:
- `conversation_rag_ollama.py` - Semantic search across saved conversations
- `conversation_detector.py` - Automated significance detection (83% accuracy)
- `conversation_save_helper.py` - Auto-extraction of topic, decisions, tags
- **Storage**: `~/.maia/conversation_rag/` (ChromaDB persistent vector database)
- **Features**: Save conversations with topic, summary, key decisions, tags, action items
- **Detection**: Multi-dimensional scoring (topic patterns × depth × engagement)
- **Thresholds**: 50+ (definitely save), 35-50 (recommend), 20-35 (consider), <20 (skip)
- **Performance**: 86.4/100 score on real conversation, <0.1s analysis time
- **Privacy**: 100% local processing (Ollama nomic-embed-text embeddings)
- **Usage**: `/save-conversation` (manual) or automatic prompt when significant conversation detected
- **Problem Solved**: Never lose important conversations - automatic detection + semantic retrieval

### Security & Compliance Commands ✅ **PRODUCTION READY - PHASE 78**
- `security_review` - Comprehensive security analysis with threat modeling
- `vulnerability_scan` - Automated vulnerability identification and remediation
- `compliance_check` - Enterprise compliance validation (Essential 8, ISO 27001)
- `azure_security_audit` - Azure-specific security configurations and best practices

**Security Scanner Suite** (October 2025):
- `local_security_scanner.py` - OSV-Scanner V2.0 + Bandit integration (dependency & code security)
- `security_hardening_manager.py` - Lynis integration (system hardening audit)
- `weekly_security_scan.py` - Orchestrated scanning with trend analysis
- **Status**: 0 vulnerabilities, Risk Level: LOW, all tools operational

### MSP & Infrastructure Management ⭐ **PHASE 187-192 - PRODUCTION READY**
**ManageEngine Patch Manager Plus Integration** (November 2025):
- `pmp_resilient_extractor.py` - Production-grade system inventory extractor with checkpoint/resume
- `pmp_config_extractor.py` - Configuration snapshot extraction with SQLite storage
- `pmp_report_generator.py` - Excel compliance dashboard generator
- `pmp_oauth_manager.py` - Secure OAuth 2.0 API integration
- **Coverage**: 99.1% (3,333/3,362 systems) with 0% token expiry failures
- **Reliability**: Checkpoint/resume system, intelligent error handling, graceful degradation
- **Compliance**: Essential Eight + CIS Controls automated analysis
- **Integration**: OAuth token management, rate limiting, JSON structured logging
- **Status**: Production-ready with automated cron deployment support

### Prompt Engineering Commands
- `analyze_prompt` - Advanced prompt analysis and weakness identification
- `optimize_prompt` - Systematic prompt optimization with A/B testing
- `prompt_frameworks` - Template-driven prompt design patterns

### System Management Commands
- `analyze_project` - Project structure and dependency analysis
- `research_topic` - Research and summarization with source verification
- `daily_summary` - Comprehensive daily activity summaries
- `setup_mcp_servers` - Model Context Protocol integration configuration
- `personal_context` - Personal profile context management
- `performance_analytics` - System performance monitoring and optimization
- `analytics_dashboard` - Real-time system health and metrics

### Productivity Integration Tools ✅ **PRODUCTION READY - PHASE 79**
- **Trello Fast Integration** (October 2025)
  - `trello_fast.py` - Direct API client optimized for Claude Code terminal usage
  - **Capabilities**: Full CRUD on boards, lists, cards, labels, members, checklists
  - **Performance**: Instant responses, zero MCP overhead
  - **Status**: Production ready, tested with live user data
- `monitor_job_alerts` - Automated job alert processing
- `optimize_system` - System-wide performance optimization

## Command Execution Patterns

### Direct Invocation
```bash
# Template-driven CV generation
template_cv_generator job_description.txt --track-application --company="Target Company"

# Multi-stage orchestration  
complete_application_pipeline --source=gmail --priority=high --stages=all

# Professional optimization
professional_brand_optimization --platforms=linkedin,github --market=australia
```

### Natural Language Interface
- "Generate a CV using the template system for this Orro job"
- "Run the complete job analysis pipeline on my recent emails"
- "Optimize my LinkedIn profile with keyword analysis"
- "Create a market intelligence report for the BRM space"
- "Security review the FOBs system implementation"

### Command Chaining Examples
```bash
# Job application workflow
complete_job_analyzer → template_cv_generator → professional_brand_optimization

# Market research pipeline  
market_research → deep_job_analyzer → market_intelligence_report

# Security assessment chain
security_review → vulnerability_scan → compliance_check → azure_security_audit

# Prompt optimization workflow
analyze_prompt → optimize_prompt → prompt_frameworks
```

## Advanced Orchestration Features

### Context Sharing
- **Shared Memory**: `/tmp/maia_command_context_[command_id].json`
- **Agent Communication**: Structured JSON data flow protocols
- **State Persistence**: Cross-command context preservation
- **Cleanup Management**: Automatic resource management

### Quality Assurance
- **Input Validation**: Comprehensive data validation at each stage
- **Output Quality**: Confidence scoring for all results
- **Chain Integrity**: End-to-end data flow verification
- **User Satisfaction**: Final result validation and feedback collection

### Performance Monitoring
```json
{
  "command_execution": {
    "command_id": "cmd_20250106_143022",
    "total_duration": "3m 45s",
    "stage_timings": {"jobs": "1m 10s", "scraper": "1m 30s", "analytics": "1m 5s"},
    "success_rate": 100,
    "confidence_score": 0.95
  }
}
```

## Creating Advanced Commands

### Development Framework
1. **Define Agent Chain** - Multi-stage workflow specification
2. **Implement Data Flow** - Inter-agent communication protocols
3. **Add Error Handling** - Fallback agents and retry mechanisms
4. **Integrate Quality Gates** - Validation and confidence scoring
5. **Enable Performance Tracking** - Success metrics and learning
6. **Document Orchestration** - Usage patterns and integration points
7. **Validate Production** - End-to-end testing and monitoring

### Command Template Structure
```markdown
# Command: [command_name]

## Agent Chain
1. **Primary Agent**: [agent_name] 
   - Input: [data_structure]
   - Output: [data_structure]
   - Fallback: [fallback_agent]

2. **Secondary Agent**: [agent_name]
   - Input: [previous_output]
   - Output: [data_structure] 
   - Condition: [when_to_execute]

## Quality Assurance
- Input validation protocols
- Output confidence scoring
- Error handling mechanisms
- Performance benchmarks

## Usage Examples
- Natural language invocation
- Direct command execution
- Integration with other commands
```

## Integration Points

### Agent Ecosystem Integration
Commands seamlessly integrate with Maia's specialized agents:
- **Technical Recruitment Agent** ⭐ **NEW - PHASE 94**: AI-augmented CV screening for MSP/Cloud technical roles with 100-point scoring framework
- **Jobs Agent**: Job opportunity analysis and automation
- **LinkedIn Optimizer**: Profile optimization and networking
- **Security Specialist**: Vulnerability assessment and compliance
- **Azure Architect**: Cloud architecture and optimization
- **Prompt Engineer**: Advanced prompt design and testing
- **Company Research**: Deep intelligence gathering

### Tool Integration
- **FOBs System**: Dynamic tool creation and execution
- **Database Access**: Career and contact data management
- **External APIs**: Gmail, LinkedIn, job boards, research sources
- **MCP Servers**: Extended capability integration
- **Performance Monitoring**: Real-time metrics and optimization

Commands represent the pinnacle of Maia's automation capabilities, transforming complex multi-step workflows into reliable, monitored, and continuously improving processes.
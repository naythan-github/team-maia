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

### Productivity Integration Tools ⭐ **PHASE 79-80**
**Trello Integration** (Phase 79):
- `trello_fast.py` - Direct API client for boards, lists, cards, labels, checklists
- Full CRUD operations optimized for Claude Code terminal workflow
- Zero MCP overhead, instant performance

**Mail.app Integration** (Phase 80):
- `macos_mail_bridge.py` - AppleScript automation for Exchange email access
- `mail_intelligence_interface.py` - Intelligent email triage and search
- Bypasses Azure AD OAuth restrictions, uses existing Mail.app authentication
- 313 inbox messages accessible, 26 unread tracking, full Exchange integration
- Local LLM ready for 99.7% cost savings (triage) + 99.3% savings (drafting)

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
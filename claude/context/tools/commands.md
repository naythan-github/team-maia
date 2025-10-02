# Available Commands

## Advanced Multi-Agent Commands (KAI-Style Orchestration)
Located in: `claude/commands/` - Advanced orchestration capabilities

### Career & Job Search Commands
- **complete_application_pipeline** - End-to-end job application workflow (6 stages)
- **professional_brand_optimization** - Comprehensive brand building across platforms (6 stages)
- **market_intelligence_report** - Multi-source industry analysis (5 stages)
- **create_cv_from_databases** - Template-driven CV generation from experience databases
- **template_cv_generator** - Intelligent CV template system with A/B testing
- **complete_job_analyzer** - Automated job opportunity analysis and scoring
- **automated_job_scraper** - Multi-platform job scraping with anti-detection
- **intelligent_job_filter** - Smart job filtering based on preferences
- **deep_job_analyzer** - Enhanced job analysis with market intelligence
- **hybrid_job_analyzer** - Combined email processing and web scraping

### Professional Optimization Commands  
- **optimize_profile** - LinkedIn profile optimization with keyword analysis
- **keyword_analysis** - Market-driven keyword optimization strategies
- **content_strategy** - Professional content planning and execution
- **network_audit** - LinkedIn network analysis and growth recommendations
- **market_research** - Industry trends and competitive analysis

### Security & Compliance Commands
- **security_review** - Comprehensive security analysis with threat modeling
- **vulnerability_scan** - Automated vulnerability identification and remediation
- **compliance_check** - Enterprise compliance validation (Essential 8, ISO 27001)
- **azure_security_audit** - Azure-specific security configurations and best practices

### Prompt Engineering Commands
- **analyze_prompt** - Advanced prompt analysis and weakness identification
- **optimize_prompt** - Systematic prompt optimization with A/B testing
- **prompt_frameworks** - Template-driven prompt design patterns

### Core System Commands
- **analyze_project** - Analyze project structure and dependencies
- **research_topic** - Research and summarize any topic with source verification
- **daily_summary** - Create comprehensive daily activity summaries
- **setup_mcp_servers** - Configure Model Context Protocol integrations
- **personal_context** - Load and manage personal profile context
- **performance_analytics** - System performance monitoring and optimization
- **analytics_dashboard** - Real-time system health and metrics visualization
- **monitor_job_alerts** - Automated job alert monitoring and processing
- **optimize_system** - System-wide performance optimization

## Command Orchestration Features
- **Parallel Processing**: Multiple agents executing simultaneously
- **Sequential Chaining**: Structured data flow between agent stages
- **Conditional Execution**: Smart routing based on intermediate results
- **Error Handling**: Fallback agents and retry mechanisms
- **Quality Assurance**: Validation checkpoints and confidence scoring
- **Context Persistence**: Shared memory across agent invocations

## Command Usage Patterns

### Direct Invocation
```bash
# Simple command execution
template_cv_generator job_description.txt --track-application

# Advanced orchestration
complete_application_pipeline --source=gmail --priority=high

# Multi-stage workflows
professional_brand_optimization --platforms=linkedin,github
```

### Natural Language Interface
- "Generate a CV using the template system for this Orro job"
- "Run the complete job analysis pipeline on my recent emails"
- "Optimize my LinkedIn profile with keyword analysis"
- "Create a market intelligence report for the BRM space"
- "Security review the FOBs system implementation"

## Command Philosophy
Each command follows enterprise-grade principles:
1. **Single Responsibility** - Focused domain expertise
2. **Composable Architecture** - Seamless agent chaining
3. **Production Ready** - Error handling and monitoring
4. **Evidence-Based** - Performance tracking and learning
5. **Security First** - Comprehensive validation and sandboxing

## Advanced Command Examples

### Job Application Workflow
```bash
complete_job_analyzer → template_cv_generator → professional_brand_optimization
```

### Market Research Pipeline  
```bash
market_research → deep_job_analyzer → market_intelligence_report
```

### Security Assessment Chain
```bash
security_review → vulnerability_scan → compliance_check → azure_security_audit
```

### Prompt Optimization Workflow
```bash
analyze_prompt → optimize_prompt → prompt_frameworks
```

## Command Creation Framework
1. **Define Domain Expertise** - Specialized agent requirements
2. **Specify Orchestration** - Multi-agent workflow design
3. **Implement Error Handling** - Fallback and retry mechanisms
4. **Add Performance Tracking** - Success metrics and learning
5. **Document Integration** - Agent communication protocols
6. **Validate Production** - End-to-end testing and monitoring

Commands leverage the full power of Maia's 6 specialized agents, dynamic tool creation (FOBs), and enterprise-grade orchestration framework for sophisticated automation workflows.
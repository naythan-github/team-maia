# Command Orchestration Framework

## Overview
Advanced multi-agent command chaining system inspired by KAI's orchestration capabilities.

## Core Principles
1. **Agent Chaining**: Commands can invoke multiple agents in sequence
2. **Real-Time Communication**: Message bus for streaming data and coordination
3. **Enhanced Context Preservation**: 95% context retention with reasoning chains
4. **Intelligent Error Handling**: Automatic classification and recovery strategies
5. **Parallel Processing**: Simultaneous agent execution when possible
6. **Dynamic Resource Allocation**: Adaptive scaling based on workload

## Orchestration Syntax

### Basic Chain Structure
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

3. **Final Agent**: [agent_name]
   - Input: [combined_outputs]
   - Output: [final_result]
```

### Dashboard Integration Patterns ⭐ **NEW - PHASE 56 ENTERPRISE READY**

#### **Pattern 1: EIA-Integrated Dashboard Creation**
```markdown
# Command: create_intelligent_dashboard

## Agent Chain  
1. **Research Agent**: Analyze requirements and data sources
   - Input: User requirements, domain context
   - Output: Data requirements, visualization specs
   - Integration: Check existing EIA intelligence sources

2. **EIA Integration Agent**: Leverage existing intelligence infrastructure
   - Input: Dashboard requirements
   - Output: EIA connection strategy, data pipeline design
   - Condition: Always check UDH registry and EIA platform first
   - **Critical**: Use `claude/tools/📈_monitoring/unified_dashboard_platform.py` for registration
   - **Critical**: Integrate with `claude/tools/📈_monitoring/eia_executive_dashboard.py` patterns

3. **Implementation Agent**: Build dashboard with EIA connectivity
   - Input: Integration strategy, technical specs
   - Output: Functional dashboard with EIA data sources
   - Fallback: Standalone dashboard if EIA integration fails
```

#### **Pattern 2: UDH Service Integration**
```markdown
# Command: integrate_new_service

## Discovery Phase
1. **UDH Status Check**: Verify Unified Dashboard Hub availability
   - Command: `curl -s http://127.0.0.1:8100/api/dashboards`
   - Fallback: Start UDH with `claude/tools/🔧_system/start_udh.sh`

2. **Service Registration**: Register new dashboard in UDH registry
   - Integration: Use UDH REST API for automatic discovery
   - Port Management: Auto-assign available ports (8050-8099 range)
   - Health Monitoring: Implement /health endpoint pattern
```

### Parallel Processing
```markdown
## Parallel Stage
**Agents**: [agent1, agent2, agent3]
**Mode**: Parallel execution
**Sync Point**: Wait for all agents to complete
**Merge Strategy**: [how_to_combine_outputs]
```

### Conditional Branching
```markdown
## Conditional Logic
**If**: [condition]
  - **Then**: Execute [agent_name]
  - **Input**: [conditional_data]
**Else**: Execute [fallback_agent]
```

## Data Flow Standards

### Enhanced Data Flow Standards

#### Real-Time Message Structure
```json
{
  "message_id": "msg_uuid",
  "sender_agent": "jobs_agent",
  "receiver_agent": "web_scraper", 
  "message_type": "progress_update|data_stream|error_alert|coordination_request",
  "payload": {
    "partial_results": "streaming_data",
    "context_updates": "incremental_learning",
    "resource_requests": "dynamic_scaling"
  },
  "routing": {
    "priority": "high|medium|low",
    "broadcast": false,
    "requires_response": true
  }
}
```

#### Enhanced Context Envelope
```json
{
  "context_id": "ctx_uuid",
  "command_context_id": "cmd_uuid", 
  "reasoning_chain": [
    {
      "agent": "jobs_agent",
      "decision": "prioritized_job_x",
      "rationale": "matches_criteria_y",
      "confidence": 0.89,
      "timestamp": "2025-01-07T10:30:00Z",
      "alternatives_considered": ["option_a", "option_b"]
    }
  ],
  "quality_metrics": {
    "data_completeness": 0.95,
    "processing_confidence": 0.87,
    "user_satisfaction_prediction": 0.91,
    "overall_quality": 0.89
  },
  "user_preferences": {
    "explicit_preferences": {"min_salary": 120000},
    "learned_patterns": {"high_priority_companies": ["PwC"]},
    "priority_weights": {"salary": 0.3, "company": 0.25}
  },
  "execution_context": {
    "stage": "data_processing",
    "resource_usage": {"memory_mb": 256, "cpu_percent": 45},
    "performance_metrics": {"avg_response_time": 1.2},
    "error_history": []
  }
}
```

### Enhanced Error Handling Protocol

#### Error Classification System
```json
{
  "error_taxonomy": {
    "recoverable": {
      "data_incomplete": "request_retry_with_fallback",
      "timeout": "extend_deadline_or_delegate",
      "rate_limit": "queue_for_later_execution"
    },
    "escalation_required": {
      "authentication_failure": "notify_user_credential_update",
      "service_unavailable": "activate_fallback_agent"
    },
    "system_failure": {
      "agent_crash": "restart_with_saved_context",
      "infinite_loop": "circuit_breaker_activation"
    }
  }
}
```

#### Recovery Strategies
1. **Automatic Classification**: Pattern-based error identification
2. **Intelligent Recovery**: Context-aware recovery strategy selection
3. **Circuit Breakers**: Prevent cascading failures
4. **Quality Feedback**: Downstream agents improve upstream decisions
5. **Graceful Degradation**: Maintain functionality with reduced capabilities

## Command Types

### Sequential Orchestration
**Pattern**: Agent A → Agent B → Agent C
**Use Cases**: Data processing pipelines, analysis workflows
**Example**: Email Processing → Content Analysis → Action Planning

### Parallel Orchestration  
**Pattern**: Agent A + Agent B + Agent C → Merger Agent
**Use Cases**: Multi-source data gathering, parallel analysis
**Example**: LinkedIn + Seek + Email scraping → Combined Analysis

### Conditional Orchestration
**Pattern**: Decision Agent → Conditional Agents → Results Merger
**Use Cases**: Dynamic workflow routing, personalized processing
**Example**: Role Type Detection → BRM/Tech/Product Specific Analysis

### Feedback Loop Orchestration
**Pattern**: Agent A → Agent B → Validation → (Retry A if needed)
**Use Cases**: Quality assurance, iterative improvement
**Example**: CV Generation → Quality Check → Regeneration if needed

## Agent Coordination

### Context Sharing
- **Shared Memory**: `/tmp/maia_command_context_[command_id].json`
- **Agent Access**: All agents can read/write shared context
- **Cleanup**: Automatic cleanup after command completion

### Progress Tracking
```json
{
  "command_progress": {
    "total_stages": 4,
    "completed_stages": 2, 
    "current_stage": "Stage 3: Analysis",
    "estimated_completion": "2 minutes",
    "stage_results": [
      {"stage": 1, "agent": "Jobs Agent", "status": "completed", "duration": "30s"},
      {"stage": 2, "agent": "Web Scraper", "status": "completed", "duration": "45s"},
      {"stage": 3, "agent": "Analytics", "status": "in_progress", "started": "timestamp"}
    ]
  }
}
```

### Enhanced Communication Protocol

#### Real-Time Coordination
1. **Agent Registration**: Agents register with message bus and declare capabilities
2. **Streaming Communication**: Real-time data streams between agents during execution
3. **Dynamic Coordination**: Agents negotiate optimal execution strategies
4. **Quality Feedback Loops**: Downstream agents provide improvement feedback
5. **Resource Negotiation**: Agents coordinate resource allocation dynamically

#### Message Bus Integration
- **Message Types**: progress_update, data_stream, error_alert, coordination_request, quality_feedback
- **Priority Queuing**: High/medium/low priority message handling
- **Broadcast Support**: Multi-agent coordination messages
- **Persistence**: Message logging for debugging and learning

#### Context Transfer Protocol
```markdown
## Enhanced Context Transfer
1. **Context Creation**: Enhanced context with reasoning chains
2. **Real-Time Updates**: Incremental context updates via message bus
3. **Quality Preservation**: 95% context retention across transfers
4. **Reasoning Continuity**: Decision rationale preserved and built upon
5. **Performance Tracking**: Context quality metrics updated continuously
```

## Quality Assurance

### Validation Points
- **Input Validation**: Each agent validates received data
- **Output Quality**: Confidence scoring for all results
- **Chain Integrity**: End-to-end data flow verification
- **User Satisfaction**: Final result meets user expectations

### Monitoring & Logging
```json
{
  "command_execution_log": {
    "command_id": "cmd_20250106_143022",
    "user_request": "original_user_input",
    "execution_path": ["Jobs Agent", "Web Scraper", "Analytics"],
    "timing": {
      "total_duration": "3m 45s",
      "stage_timings": {"jobs": "1m 10s", "scraper": "1m 30s", "analytics": "1m 5s"}
    },
    "success_rate": 100,
    "user_satisfaction": "awaiting_feedback"
  }
}
```

## Implementation Examples

### Basic Chain Command
```markdown
# Enhanced Complete Job Analyzer

## Agent Chain
1. **Email Processor Agent**
   - Input: Gmail query parameters
   - Output: Structured job notifications
   - Fallback: Manual email parsing

2. **Web Scraper Agent** (Parallel)
   - Input: Job URLs from email processor
   - Output: Full job descriptions
   - Condition: Only high-priority jobs (score >= 7.0)

3. **Analysis Agent**
   - Input: Combined email + scraped data
   - Output: Enhanced job analysis with scores
   - Fallback: Analysis with limited data if scraping failed

4. **Recommendation Agent**
   - Input: All analyzed jobs
   - Output: Prioritized action plan
   - Always executes
```

### Parallel Processing Command
```markdown
# Market Intelligence Report

## Parallel Data Gathering Stage
**Agents**: [LinkedIn Research, Company Analysis, Industry Trends]
**Mode**: Parallel execution
**Timeout**: 5 minutes
**Merge Strategy**: Comprehensive market overview

## Sequential Analysis Stage  
1. **Data Integration Agent**
   - Input: All parallel results
   - Output: Integrated dataset

2. **Report Generation Agent**
   - Input: Integrated dataset + report template
   - Output: Professional market report
```

## Production Infrastructure Components ✅

### Swarm Orchestration Framework
- **Location**: `${MAIA_ROOT}/claude/tools/orchestration/agent_swarm.py`
- **Purpose**: Lightweight multi-agent coordination with explicit handoffs
- **Features**: Context enrichment, handoff chain tracking, circular prevention, failure recovery
- **Usage**: `SwarmOrchestrator()` for orchestration, `AgentHandoff` for handoffs
- **Status**: ✅ **PRODUCTION ACTIVE** - 49 agents registered

### Context Management System
- **Location**: `${MAIA_ROOT}/claude/tools/orchestration/context_management.py`
- **Purpose**: Context preservation across agent handoffs
- **Features**: Context enrichment, reasoning chains, quality tracking
- **Usage**: `ContextManager()` for context operations
- **Status**: ✅ **PRODUCTION ACTIVE**

### Error Recovery System
- **Location**: `${MAIA_ROOT}/claude/tools/orchestration/error_recovery.py`
- **Purpose**: Intelligent error classification and automatic recovery
- **Features**: Pattern matching, circuit breakers, recovery strategies
- **Usage**: `ErrorRecovery()` for error handling
- **Status**: ✅ **PRODUCTION ACTIVE**

### Agent Loader
- **Location**: `${MAIA_ROOT}/claude/tools/orchestration/agent_loader.py`
- **Purpose**: Load and prepare agent prompts for Swarm execution
- **Features**: Agent registry (49 agents), context injection, handoff support detection
- **Usage**: `AgentLoader()` for loading agents
- **Status**: ✅ **PRODUCTION ACTIVE**

### Integration Guidelines

#### For Existing Commands
1. **Gradual Migration**: Update commands incrementally to use new infrastructure
2. **Backward Compatibility**: Old JSON handoff system remains functional
3. **Enhanced Features**: Opt-in to message bus and enhanced context
4. **Performance Monitoring**: Track improvements with new vs old system

#### Swarm Integration Pattern
```python
# Import Swarm orchestration infrastructure
from claude.tools.orchestration.agent_swarm import SwarmOrchestrator, AgentHandoff, AgentResult
from claude.tools.orchestration.context_management import ContextManager
from claude.tools.orchestration.error_recovery import ErrorRecovery

# Initialize orchestrator
orchestrator = SwarmOrchestrator()
context_manager = ContextManager()

# Execute workflow with handoffs
result = orchestrator.execute_with_handoffs(
    initial_agent="dns_specialist",
    task={"query": "Setup Azure Exchange Online with custom domain"},
    max_handoffs=5
)

# Agents declare handoffs explicitly
handoff = AgentHandoff(
    to_agent="azure_solutions_architect",
    context={"dns_complete": True, "records": [...]},
    reason="Azure expertise required"
)

return AgentResult(output=analysis, handoff=handoff)
```

This Swarm framework provides lightweight multi-agent coordination through explicit handoffs, perfect for conversation-driven architecture while maintaining clear audit trails and context preservation.
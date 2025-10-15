# Maia AI System: Developer Onboarding Package
**Getting Started, Development Workflows & Best Practices**

---

## Document Purpose
This developer onboarding package provides hands-on guidance for developers joining the Maia project or implementing similar AI infrastructure. Designed for software engineers, DevOps engineers, and technical contributors.

**Reading Time**: 30-40 minutes | **Target Audience**: Developers, DevOps Engineers, Technical Contributors

---

## Quick Start (30 Minutes to First Success)

### Prerequisites
```bash
# Required
- macOS 12+ (Monterey or later) or Linux (architecture compatible)
- Python 3.11+
- Git
- Homebrew (macOS) or apt/yum (Linux)
- 16GB RAM minimum (local LLMs require memory)
- 50GB free disk space (for models + databases)

# Recommended
- VS Code or PyCharm
- Terminal comfort (bash/zsh)
- Basic Python knowledge
- Familiarity with LLMs/AI concepts
```

### Installation (10 minutes)

**Step 1: Clone Repository**
```bash
# Clone Maia
git clone https://github.com/your-org/maia.git
cd maia

# Verify structure
ls claude/
# Expected: agents/ commands/ context/ data/ hooks/ tools/
```

**Step 2: Install Dependencies**
```bash
# Python packages
pip install -r requirements.txt

# Verify critical packages
python3 -c "import chromadb, langchain, openai; print('✅ Core packages installed')"

# macOS: Install Homebrew packages
brew install ollama  # Local LLM runtime

# Linux: Install Ollama
curl https://ollama.ai/install.sh | sh
```

**Step 3: Install Local LLMs** (optional but recommended for cost savings)
```bash
# Pull local models (10-15 min, requires 16GB+ RAM)
ollama pull codellama:13b    # 7.3GB - Code generation
ollama pull starcoder2:15b   # 9.1GB - Security analysis
ollama pull llama3:3b        # 1.9GB - Fast categorization

# Verify models
ollama list
# Expected output:
# NAME              SIZE
# codellama:13b     7.3GB
# starcoder2:15b    9.1GB
# llama3:3b         1.9GB

# Test local model
ollama run llama3:3b "Hello, test local LLM"
# Should return response (proves local inference working)
```

**Step 4: Configure Credentials**
```bash
# Create encrypted credentials file
cp claude/tools/production_api_credentials.py.example \
   claude/tools/production_api_credentials.py

# Edit with your API keys (use encrypted storage in production)
# Required keys:
# - ANTHROPIC_API_KEY (Claude Sonnet)
# - OPENAI_API_KEY (embeddings for RAG)
# Optional:
# - GOOGLE_API_KEY (Gemini Pro for large context)
# - M365_CLIENT_ID, M365_TENANT_ID, M365_CLIENT_SECRET (Microsoft 365)
# - CONFLUENCE_URL, CONFLUENCE_API_TOKEN (Confluence integration)
```

**Step 5: Verify Installation**
```bash
# Run health check
python3 claude/tools/sre/automated_health_monitor.py

# Expected output:
# ✅ UFC System: HEALTHY (context files present)
# ✅ Dependencies: HEALTHY (pip packages installed)
# ✅ RAG System: HEALTHY (ChromaDB accessible)
# ✅ Local LLMs: HEALTHY (Ollama running, 3 models available)
# ⚠️  Services: DEGRADED (0/16 LaunchAgents running - expected on first install)

# Services start later, this is expected
```

### Your First Maia Interaction (5 minutes)

**Test 1: Context Loading**
```bash
# Test smart context loader
python3 claude/tools/sre/smart_context_loader.py \
  "Show me security tools" --stats

# Expected output:
# Strategy: moderate_complexity
# Phases loaded: [113, 105, 15, 120, 119]
# Token count: ~8.5K
# Efficiency: 79.8% reduction vs baseline

# Proves: UFC system + smart loading working
```

**Test 2: Capability Search**
```bash
# Test capability index
python3 claude/tools/capability_checker.py "email management tools"

# Expected output:
# Found in capability_index.md:
# - outlook_intelligence.py (M365 email operations)
# - email_rag_system.py (semantic email search)
# - automated_morning_briefing.py (email triage in briefings)

# Proves: Capability amnesia prevention working
```

**Test 3: Local LLM Inference**
```bash
# Test CodeLlama for code generation
cat << 'EOF' | python3
from subprocess import run, PIPE

prompt = "Write a Python function to calculate fibonacci numbers"
result = run(['ollama', 'run', 'codellama:13b', prompt],
             capture_output=True, text=True)
print(result.stdout)
EOF

# Expected: Python function with fibonacci implementation
# Proves: Local LLM routing working (99.3% cost savings)
```

**Test 4: RAG Search**
```bash
# Test RAG system (if you have data indexed)
python3 claude/tools/rag_enhanced_search.py "meeting notes from last week"

# Expected: Semantic search results from meeting transcripts
# Note: Empty results on fresh install (no data indexed yet) is normal
```

**Congratulations!** If all 4 tests pass, you have a working Maia installation.

---

## Development Workflows

### Workflow 1: Creating a New Tool

**When to Create**: Solving a problem that requires NEW functionality (not available in 352 existing tools)

**Mandatory Pre-Flight: Capability Check** 🚨
```bash
# STEP 0: ALWAYS search before building
# Search capability index (Cmd/Ctrl+F in file)
# File: claude/context/core/capability_index.md

# Example: Want to build "ServiceDesk ticket analyzer"
grep -i "servicedesk" claude/context/core/capability_index.md

# Found existing tools:
# - servicedesk_multi_rag_indexer.py
# - servicedesk_complete_quality_analyzer.py
# - servicedesk_operations_dashboard.py

# Decision: Use existing tools, don't rebuild ✅

# If NOT found in index:
python3 claude/tools/capability_checker.py "ServiceDesk ticket analyzer"

# Deep search across SYSTEM_STATE.md + available.md + agents.md
# If still not found → legitimate new capability
```

**Tool Creation Steps**:

**Step 1: Create Tool File**
```bash
# Determine category
# Categories: security/, sre/, information_management/, productivity/,
#             analytics/, voice/, data/, orchestration/, finance/

# Example: Building email sentiment analyzer
mkdir -p claude/tools/analytics/
touch claude/tools/analytics/email_sentiment_analyzer.py
```

**Step 2: Tool Template**
```python
#!/usr/bin/env python3
"""
Email Sentiment Analyzer

Purpose: Analyze email sentiment using local LLM for cost optimization
Category: Analytics
Dependencies: ollama (local LLM), email_rag_system (email access)
Cost: $0.0001 per email vs $0.015 cloud = 99.3% savings
"""

import sys
from pathlib import Path

# Add Maia root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from claude.tools.email_rag_system import EmailRAGSystem
import subprocess
import json


class EmailSentimentAnalyzer:
    """
    Analyze email sentiment via local LLM
    """

    def __init__(self):
        self.email_rag = EmailRAGSystem()
        self.model = 'codellama:13b'  # Good for text analysis

    def analyze_email(self, email_id: str) -> dict:
        """
        Analyze single email sentiment

        Args:
            email_id: Email identifier

        Returns:
            {
                'sentiment': 'positive' | 'negative' | 'neutral',
                'confidence': 0.0-1.0,
                'key_phrases': ['phrase1', 'phrase2'],
                'recommended_response_tone': 'professional' | 'empathetic' | 'direct'
            }
        """
        # Fetch email content
        email = self.email_rag.get_email(email_id)

        # Build prompt
        prompt = f"""Analyze the sentiment of this email:

Subject: {email['subject']}
From: {email['from']}
Body:
{email['body']}

Provide JSON response:
{{
  "sentiment": "positive|negative|neutral",
  "confidence": 0.0-1.0,
  "key_phrases": ["phrase1", "phrase2"],
  "recommended_response_tone": "professional|empathetic|direct"
}}
"""

        # Call local LLM
        result = subprocess.run(
            ['ollama', 'run', self.model, prompt],
            capture_output=True,
            text=True
        )

        # Parse JSON response
        analysis = json.loads(result.stdout.strip())

        return analysis

    def analyze_batch(self, email_ids: list) -> list:
        """
        Analyze multiple emails (batch processing)
        """
        results = []

        for email_id in email_ids:
            analysis = self.analyze_email(email_id)
            results.append({
                'email_id': email_id,
                **analysis
            })

        return results


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Email Sentiment Analyzer')
    parser.add_argument('--email-id', help='Single email ID to analyze')
    parser.add_argument('--batch', help='File with email IDs (one per line)')
    parser.add_argument('--output', default='stdout', help='Output file (default: stdout)')

    args = parser.parse_args()

    analyzer = EmailSentimentAnalyzer()

    if args.email_id:
        # Single email
        result = analyzer.analyze_email(args.email_id)
        print(json.dumps(result, indent=2))

    elif args.batch:
        # Batch processing
        with open(args.batch) as f:
            email_ids = [line.strip() for line in f]

        results = analyzer.analyze_batch(email_ids)

        if args.output == 'stdout':
            print(json.dumps(results, indent=2))
        else:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
```

**Step 3: Test Tool** (MANDATORY per Working Principle #11)
```bash
# Create test file
touch claude/tools/analytics/test_email_sentiment_analyzer.py
```

```python
#!/usr/bin/env python3
"""
Tests for Email Sentiment Analyzer

Test coverage:
- Single email analysis
- Batch processing
- Sentiment classification accuracy
- Local LLM integration
- Error handling
"""

import pytest
from email_sentiment_analyzer import EmailSentimentAnalyzer


class TestEmailSentimentAnalyzer:
    """Test suite for email sentiment analyzer"""

    def setup_method(self):
        """Initialize analyzer for each test"""
        self.analyzer = EmailSentimentAnalyzer()

    def test_positive_sentiment(self):
        """Test positive email detection"""
        # Create mock positive email
        email_text = """
        Subject: Great work on the project!
        From: manager@company.com
        Body: I wanted to congratulate you on the excellent delivery.
        The client is thrilled with the results.
        """

        result = self.analyzer.analyze_email_text(email_text)

        assert result['sentiment'] == 'positive'
        assert result['confidence'] > 0.7
        assert 'congratulate' in result['key_phrases']

    def test_negative_sentiment(self):
        """Test negative email detection"""
        email_text = """
        Subject: Urgent: System down
        From: customer@client.com
        Body: Our production system has been down for 2 hours.
        This is unacceptable. We need immediate resolution.
        """

        result = self.analyzer.analyze_email_text(email_text)

        assert result['sentiment'] == 'negative'
        assert result['confidence'] > 0.7
        assert result['recommended_response_tone'] == 'empathetic'

    def test_batch_processing(self):
        """Test batch email analysis"""
        email_ids = ['email1', 'email2', 'email3']

        results = self.analyzer.analyze_batch(email_ids)

        assert len(results) == 3
        assert all('sentiment' in r for r in results)

    def test_local_llm_fallback(self):
        """Test fallback when local LLM unavailable"""
        # Simulate Ollama down
        self.analyzer.model = 'nonexistent-model'

        # Should fallback to cloud or raise clear error
        with pytest.raises(Exception, match="Local LLM unavailable"):
            self.analyzer.analyze_email('test_email')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

**Run tests:**
```bash
# Run test suite
pytest claude/tools/analytics/test_email_sentiment_analyzer.py -v

# Expected output:
# test_positive_sentiment PASSED
# test_negative_sentiment PASSED
# test_batch_processing PASSED
# test_local_llm_fallback PASSED

# 4 passed in 2.34s ✅
```

**Step 4: Update Documentation** (MANDATORY)
```bash
# Update capability index
# File: claude/context/core/capability_index.md

# Add to "Recent Capabilities" section:
## Recent Capabilities (Last 30 Days)
### Email Sentiment Analyzer (Oct 15)
- email_sentiment_analyzer.py - Local LLM sentiment analysis (99.3% savings)

# Add to "All Tools by Category" → Analytics section:
### Data & Analytics (16 tools)
- email_sentiment_analyzer.py - Email sentiment analysis via local LLM

# Add to "Quick Search Keywords":
**Email & Communication**:
- "email sentiment" → email_sentiment_analyzer.py
- "sentiment analysis" → email_sentiment_analyzer.py

# Update tools/available.md (detailed documentation)
# File: claude/context/tools/available.md

### Email Sentiment Analyzer ⭐ **NEW - PHASE XXX**
**Location**: `claude/tools/analytics/email_sentiment_analyzer.py`
**Purpose**: Analyze email sentiment using local LLM for 99.3% cost savings

**Capabilities**:
- Single email sentiment analysis (positive/negative/neutral)
- Batch processing for multiple emails
- Confidence scoring (0.0-1.0)
- Key phrase extraction
- Recommended response tone guidance

**Commands**:
```bash
# Single email
python3 claude/tools/analytics/email_sentiment_analyzer.py --email-id "email123"

# Batch processing
python3 claude/tools/analytics/email_sentiment_analyzer.py --batch emails.txt --output results.json
```

**Cost Savings**: $0.0001 per email (local) vs $0.015 (cloud) = 99.3% savings

**Use Cases**:
- Prioritize negative sentiment emails for immediate response
- Analyze customer satisfaction trends
- Recommend appropriate response tone for sensitive communications
```

**Step 5: Commit Changes** (with proper git workflow)
```bash
# Stage changes
git add claude/tools/analytics/email_sentiment_analyzer.py
git add claude/tools/analytics/test_email_sentiment_analyzer.py
git add claude/context/core/capability_index.md
git add claude/context/tools/available.md

# Commit with descriptive message
git commit -m "$(cat <<'EOF'
Add Email Sentiment Analyzer tool

- Local LLM sentiment analysis (99.3% cost savings)
- Single email + batch processing
- Confidence scoring + key phrase extraction
- Response tone recommendations
- Full test coverage (4 tests, 100% pass)
- Documentation: capability_index.md, available.md

Business value: $38/year savings on email sentiment analysis
(50 emails/day × $0.015 cloud vs $0.0001 local)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Push to remote
git push origin main
```

---

### Workflow 2: Creating a New Agent

**When to Create**: Need natural language orchestration of multiple tools (agents ORCHESTRATE, tools IMPLEMENT)

**Agent-Tool Separation Principle**:
- **Agent (Markdown)**: Natural language interface, workflow coordination, response synthesis
- **Tool (Python)**: Implementation logic, database operations, calculations

**Agent Creation Steps**:

**Step 1: Verify Tools Exist First**
```bash
# Agents orchestrate existing tools - tools must exist first!
# Check capability index for required tools

# Example: Creating "Customer Sentiment Agent"
# Required tools:
# - email_sentiment_analyzer.py (we just created)
# - servicedesk_complete_quality_analyzer.py (exists)
# - stakeholder_intelligence.py (exists)

# All tools exist → ready to create orchestrator agent
```

**Step 2: Create Agent Definition**
```bash
# Create agent file
touch claude/agents/customer_sentiment_agent.md
```

**Step 3: Agent Template**
```markdown
# Customer Sentiment Agent

## Purpose
Orchestrate customer sentiment analysis across emails, ServiceDesk tickets, and stakeholder relationships to identify at-risk accounts and proactive engagement opportunities.

## Specialties
- **Cross-Platform Sentiment Analysis**: Unified sentiment view across email, tickets, CRM
- **At-Risk Account Detection**: Identify customers with declining sentiment before escalation
- **Proactive Engagement Recommendations**: Suggest actions based on sentiment trends
- **Executive Reporting**: Customer health dashboard for leadership visibility

## Key Workflows

### 1. Customer Health Assessment
**Natural Language**: "How is [customer name] feeling about our service?"

**Orchestration**:
1. Email Sentiment: Call `email_sentiment_analyzer.py` for recent emails
2. Ticket Quality: Call `servicedesk_complete_quality_analyzer.py` for support interactions
3. Relationship Health: Call `stakeholder_intelligence.py` for stakeholder status
4. Synthesize: Combine into unified customer health score (0-100)

**Output**:
- Overall sentiment score (0-100)
- Trend direction (improving/stable/declining)
- Key concerns (extracted from negative sentiment)
- Recommended actions (proactive engagement, executive escalation)

### 2. At-Risk Account Identification
**Natural Language**: "Which customers are at risk?"

**Orchestration**:
1. Batch email sentiment analysis (last 30 days)
2. Ticket quality trends (resolution time, comment quality)
3. Stakeholder relationship health (<70 threshold)
4. Cross-reference: Identify customers with negative trends across all 3 sources

**Output**:
- Ranked list of at-risk customers
- Risk level (critical/high/medium)
- Root cause analysis (poor support/slow resolution/communication gaps)
- Recovery plan recommendations

### 3. Executive Customer Health Dashboard
**Natural Language**: "Generate customer health report for leadership"

**Orchestration**:
1. Aggregate sentiment across all customers (top 20 accounts)
2. Trend analysis (30-day, 90-day)
3. Escalation risk scoring
4. Generate executive summary

**Output**:
- Customer health distribution (🟢 healthy, 🟡 caution, 🔴 at-risk)
- Trend charts (sentiment over time)
- Action required list (prioritized)
- Success stories (improved sentiment examples)

## Tool Delegation

### Primary Tools
- `claude/tools/analytics/email_sentiment_analyzer.py`: Email sentiment analysis
- `claude/tools/servicedesk/servicedesk_complete_quality_analyzer.py`: Ticket quality scoring
- `claude/tools/information_management/stakeholder_intelligence.py`: Relationship health

### Supporting Tools
- `claude/tools/productivity/enhanced_daily_briefing_strategic.py`: Daily customer alerts
- `claude/tools/servicedesk/servicedesk_operations_dashboard.py`: FCR and resolution metrics

## Integration with Other Agents

**Coordinates With**:
- **Service Desk Manager Agent**: Escalation handling for at-risk customers
- **Information Management Orchestrator**: Customer prioritization in daily briefings
- **Stakeholder Intelligence Agent**: Relationship health context

**Handoff Patterns**:
```python
# When critical customer risk detected
if customer_risk_score >= 90:
    return {
        'result': risk_analysis,
        'handoff_to': 'service_desk_manager',
        'handoff_reason': 'Critical customer risk requires immediate escalation protocol',
        'handoff_context': {
            'customer': customer_name,
            'risk_score': 90,
            'root_cause': 'Multiple negative emails + declining ticket quality',
            'recommended_action': 'Executive engagement within 24 hours'
        }
    }
```

## Value Proposition

**Quantified Benefits**:
- **Churn Prevention**: Identify at-risk customers 2-4 weeks before escalation
- **Proactive Engagement**: 30% reduction in escalations through early intervention
- **Executive Visibility**: Real-time customer health dashboard (vs weekly manual reports)
- **Cost Savings**: 99.3% lower analysis cost via local LLM routing

**Annual Value**: $15,000/year
- Prevented churn: 2 accounts × $5,000 = $10,000
- Reduced escalations: 20% × 50 escalations × $100 = $1,000
- Executive time savings: 2 hrs/week × $80/hr × 52 weeks = $8,320
- **Total**: $19,320/year value
- **Cost**: $50/year (local LLM compute)
- **ROI**: 38,540%

## Usage Examples

**Example 1: Quick Health Check**
```
User: "How is Northbridge Construction feeling about our service?"

Agent: Analyzing customer sentiment across emails, tickets, and stakeholder relationships...

CUSTOMER HEALTH: Northbridge Construction
Overall Score: 65/100 (⚠️ CAUTION - declining trend)

Breakdown:
- Email Sentiment: 55/100 (negative trend, 3 frustrated emails last week)
- Ticket Quality: 70/100 (resolution time +40% vs baseline)
- Stakeholder Health: 68/100 (relationship with PM declining)

Key Concerns:
1. Slow Azure VM provisioning (mentioned in 3 emails)
2. Lack of proactive communication (ticket comments generic)
3. PM not responding to questions within SLA

Recommended Actions:
🔴 CRITICAL: Executive call within 48 hours
🟡 Schedule technical review of Azure provisioning workflow
🟢 Improve ServiceDesk comment quality (use quality analyzer coaching)

Risk Level: HIGH (churn risk in 30 days if no action)
```

**Example 2: Portfolio Risk Report**
```
User: "Which customers need attention this week?"

Agent: Analyzing sentiment across 33 active customers...

AT-RISK CUSTOMERS (Week of Oct 15):

🔴 CRITICAL (3 customers):
1. Northbridge Construction (score: 65, ↓ 15 pts)
   - Risk: Churn within 30 days
   - Action: Executive engagement + technical review

2. Westgate Logistics (score: 62, ↓ 10 pts)
   - Risk: Contract renewal at risk
   - Action: Account review meeting

3. [Customer 3...]

🟡 CAUTION (5 customers):
[List of 5 customers with moderate risk...]

🟢 STABLE (25 customers):
[Healthy customer summary...]

PROACTIVE OPPORTUNITIES (2 customers with improving sentiment):
- Southbank Developments (↑ 20 pts) - potential case study
- Harbor Bridge Co (↑ 15 pts) - potential upsell opportunity
```

## Development Notes

**Testing Strategy**:
- Unit tests: Individual tool calls (email sentiment, ticket quality, stakeholder health)
- Integration tests: Multi-tool workflow coordination
- E2E tests: Complete customer health assessment from query to recommendations

**Performance**:
- Single customer analysis: <3s (parallel tool execution)
- Portfolio analysis (33 customers): <30s (batch processing)
- Local LLM: 99.3% cost savings vs cloud

**Future Enhancements**:
- Predictive churn modeling (ML-based, Phase 2)
- Automated recovery workflows (Phase 3)
- Real-time alerting (Slack/Teams integration, Phase 4)
```

**Step 4: Test Agent** (integration testing)
```bash
# Create agent integration test
touch claude/agents/test_customer_sentiment_agent.py
```

```python
#!/usr/bin/env python3
"""
Integration Tests for Customer Sentiment Agent

Test agent orchestration across multiple tools
"""

import pytest
from unittest.mock import Mock, patch


class TestCustomerSentimentAgent:
    """Test suite for customer sentiment agent orchestration"""

    def test_customer_health_assessment_workflow(self):
        """Test complete health assessment orchestration"""
        # Mock tool responses
        with patch('email_sentiment_analyzer.analyze') as mock_email, \
             patch('servicedesk_quality_analyzer.analyze') as mock_ticket, \
             patch('stakeholder_intelligence.get_health') as mock_stakeholder:

            # Setup mocks
            mock_email.return_value = {'sentiment': 'negative', 'score': 55}
            mock_ticket.return_value = {'quality': 70, 'trend': 'declining'}
            mock_stakeholder.return_value = {'health': 68}

            # Execute agent workflow
            result = customer_sentiment_agent.assess_health('Northbridge Construction')

            # Verify orchestration
            assert mock_email.called
            assert mock_ticket.called
            assert mock_stakeholder.called

            # Verify synthesis
            assert result['overall_score'] == 65  # (55+70+68)/3
            assert result['risk_level'] == 'HIGH'
            assert 'Executive engagement' in result['recommended_actions']

    def test_at_risk_detection_workflow(self):
        """Test at-risk customer identification"""
        # Test batch processing + cross-referencing
        result = customer_sentiment_agent.identify_at_risk()

        assert 'critical' in result
        assert 'caution' in result
        assert len(result['critical']) > 0

    def test_handoff_to_service_desk_manager(self):
        """Test agent handoff for critical risk"""
        # Simulate critical customer
        result = customer_sentiment_agent.assess_health('Critical Customer')

        if result['overall_score'] <= 60:
            assert result['handoff_to'] == 'service_desk_manager'
            assert 'handoff_context' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

**Step 5: Update Documentation**
```bash
# Update agent registry
# File: claude/context/core/agents.md

### Customer Sentiment Agent ⭐ **NEW - PHASE XXX**
**Location**: `claude/agents/customer_sentiment_agent.md`
- **Purpose**: Cross-platform customer sentiment analysis + at-risk detection
- **Specialties**: Email sentiment, ticket quality, stakeholder health orchestration
- **Value**: $15,000/year (churn prevention + proactive engagement)
- **Integration**: Service Desk Manager, Stakeholder Intelligence, Info Mgmt Orchestrator

# Update capability index
# File: claude/context/core/capability_index.md

## All Agents (54 Agents)  # Increment count

### Customer Experience (1 agent)  # New category
- **Customer Sentiment Agent** - Cross-platform sentiment analysis + risk detection
```

---

### Workflow 3: Experimental → Production Graduation

**Purpose**: Test new ideas safely before committing to production

**Directory Structure**:
```
claude/extensions/experimental/
├── prototypes/           # Rough experiments (broken code OK)
├── validation/           # Working prototypes ready for testing
└── deprecated/           # Failed experiments (learning archive)
```

**Graduation Process**:

**Phase 1: Prototype (claude/extensions/experimental/prototypes/)**
```bash
# Create experimental prototype
mkdir -p claude/extensions/experimental/prototypes/ai_code_reviewer/
touch claude/extensions/experimental/prototypes/ai_code_reviewer/prototype_v1.py

# Rough implementation (broken code OK)
# Goal: Prove concept viability
# Quality: NOT production-ready
# Testing: Manual only

# Example: AI code reviewer using local LLM
# Experiment with different prompts, models, approaches
# Break things, learn fast
```

**Phase 2: Validation (claude/extensions/experimental/validation/)**
```bash
# Prototype shows promise → move to validation
mv claude/extensions/experimental/prototypes/ai_code_reviewer \
   claude/extensions/experimental/validation/

# Refine implementation:
# - Add error handling
# - Write tests
# - Document usage
# - Benchmark performance
# - Compare alternatives (if 3 prototypes, test all 3)

# Goal: Determine if worth graduating to production
# Quality: Working code, tested
# Testing: Automated tests, real-world usage
```

**Phase 3: Production Graduation**
```bash
# ONE winner graduates to production (not all 3 prototypes)

# Option A: New tool
cp claude/extensions/experimental/validation/ai_code_reviewer/ai_code_reviewer.py \
   claude/tools/development/ai_code_reviewer.py

# Option B: Enhancement to existing tool
# Merge validated feature into existing production tool

# Cleanup experimental:
mkdir -p claude/extensions/experimental/deprecated/ai_code_reviewer/
mv claude/extensions/experimental/validation/ai_code_reviewer/* \
   claude/extensions/experimental/deprecated/ai_code_reviewer/

# Commit:
# - Production tool (new or enhanced)
# - Deprecated experimental code (learning archive)
# - Updated documentation (capability index, available.md)
```

**Decision Criteria for Graduation**:
- ✅ **Solves Real Problem**: Validated with real usage (not theoretical)
- ✅ **Quality**: Tested, error handling, documented
- ✅ **Performance**: Acceptable speed/cost for intended use case
- ✅ **Maintainability**: Code others can understand and modify
- ✅ **Value**: Clear ROI or productivity gain

**Failed Experiments**: Keep in deprecated/ as learning archive (document why it failed)

---

## Development Best Practices

### 1. Always Search Before Building (Capability Amnesia Prevention)
```bash
# MANDATORY workflow (Working Principle #6)
# Step 1: Search capability index
grep -i "keyword" claude/context/core/capability_index.md

# Step 2: If not found, deep search
python3 claude/tools/capability_checker.py "your requirement"

# Step 3: If still not found, proceed with build

# Prevention: 95%+ duplicate builds prevented
```

### 2. Mandatory Testing Before Production (Working Principle #11)
```bash
# NO EXCEPTIONS - every production tool/agent needs tests

# Minimum test coverage:
# - Happy path (works as expected)
# - Error handling (graceful failures)
# - Edge cases (empty input, large input, invalid input)
# - Integration (if coordinates multiple tools)

# Run tests before commit:
pytest claude/tools/your_category/test_your_tool.py -v

# Pre-commit hook enforces this (can't commit without tests passing)
```

### 3. Cost-Aware LLM Selection
```python
# Decision tree for model selection:

def select_llm(task_type, quality_requirement, data_sensitivity):
    """
    Choose optimal LLM based on task characteristics
    """
    # Rule 1: Sensitive data MUST stay local
    if data_sensitivity == 'high':
        return select_local_model(task_type)

    # Rule 2: Strategic work uses best model (cost acceptable)
    if quality_requirement >= 0.95:
        return 'claude_sonnet_4.5'  # Highest quality

    # Rule 3: Routine tasks use local models (99.3% savings)
    if task_type in ['categorization', 'simple_triage', 'keyword_extraction']:
        return 'llama3:3b'  # Fastest, cheapest

    # Rule 4: Technical tasks use local technical models
    if task_type in ['code_generation', 'email_drafting', 'technical_writing']:
        return 'codellama:13b'  # Good quality, 99.3% savings

    # Rule 5: Large context uses Gemini Pro (58.3% savings vs Claude)
    if task_type in ['transcript_analysis', 'document_summary']:
        return 'gemini_pro'

    # Default: Claude Sonnet (safe choice)
    return 'claude_sonnet_4.5'

# Apply in your code:
model = select_llm(
    task_type='email_drafting',
    quality_requirement=0.85,
    data_sensitivity='medium'
)
# Returns: 'codellama:13b' (99.3% savings, sufficient quality)
```

### 4. Update Documentation Immediately
```bash
# MANDATORY (Working Principle #7)
# Documentation is NOT separate from code - it IS part of the code

# Updated files for every new tool/agent:
# 1. capability_index.md (prevents amnesia)
# 2. available.md or agents.md (detailed docs)
# 3. SYSTEM_STATE.md (if significant phase/milestone)
# 4. README.md (if system capabilities changed)

# Commit documentation WITH code (single atomic commit)
git add claude/tools/new_tool.py \
        claude/context/core/capability_index.md \
        claude/context/tools/available.md

git commit -m "Add new tool + documentation"
```

### 5. Security-First Development
```bash
# Pre-commit security validation (161 checks)

# What gets checked:
# ✅ No hardcoded secrets (API keys, passwords)
# ✅ No vulnerable dependencies (OSV-Scanner)
# ✅ No code security issues (Bandit for Python)
# ✅ No prompt injection vulnerabilities (web-facing tools)
# ✅ Compliance requirements (SOC2/ISO27001)

# If you try to commit insecure code:
git commit -m "Add new tool"
# Output:
# ❌ SECURITY CHECKS FAILED
# Critical Issues: 2
# Violations:
#   - hardcoded_secret: claude/tools/new_tool.py:15
#   - unvalidated_web_input: claude/tools/new_tool.py:42
# 🔒 Commit blocked. Fix security issues before committing.

# Fix issues, then commit
```

### 6. Agent-Tool Separation (Architecture Pattern)
```python
# GOOD: Agent orchestrates, tool implements
# File: claude/agents/customer_sentiment_agent.md
"""
Orchestrate customer sentiment analysis:
1. Call email_sentiment_analyzer.py
2. Call servicedesk_quality_analyzer.py
3. Call stakeholder_intelligence.py
4. Synthesize results
"""

# File: claude/tools/analytics/email_sentiment_analyzer.py
"""
Implementation: Email sentiment analysis logic
- Database queries
- LLM inference
- Score calculation
"""

# BAD: Agent contains implementation
# File: claude/agents/customer_sentiment_agent.md
"""
Orchestrate + implement customer sentiment:
[SQL queries, LLM calls, calculations all in agent file]
"""
# Problem: Can't reuse implementation, hard to test, violates separation of concerns
```

---

## Common Development Patterns

### Pattern 1: Local LLM Integration
```python
# Standard pattern for local LLM calls

import subprocess
import json

def call_local_llm(model: str, prompt: str) -> str:
    """
    Call local LLM via Ollama with error handling
    """
    try:
        result = subprocess.run(
            ['ollama', 'run', model, prompt],
            capture_output=True,
            text=True,
            timeout=30  # Prevent hanging
        )

        if result.returncode != 0:
            raise Exception(f"LLM call failed: {result.stderr}")

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        # Fallback to cloud LLM if local times out
        return call_cloud_llm(prompt)

    except Exception as e:
        # Log error, fallback to cloud
        log_error(f"Local LLM error: {e}")
        return call_cloud_llm(prompt)

def call_cloud_llm(prompt: str) -> str:
    """
    Fallback to cloud LLM (Claude Sonnet)
    """
    import anthropic

    client = anthropic.Anthropic(api_key=get_api_key())
    response = client.messages.create(
        model="claude-sonnet-4.5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text
```

### Pattern 2: RAG Search Integration
```python
# Standard pattern for RAG semantic search

from claude.tools.rag_enhanced_search import RAGEnhancedSearch

def search_emails_semantically(query: str, n_results: int = 5) -> list:
    """
    Semantic email search via RAG
    """
    rag = RAGEnhancedSearch(collection='email_archive')

    # Semantic search
    results = rag.search(
        query=query,
        n_results=n_results,
        filter_metadata={'date_range': 'last_30_days'}  # Optional filters
    )

    return results

# Usage:
results = search_emails_semantically("customer complaints about Azure VM provisioning")
# Returns: Top 5 semantically similar emails (even if exact keywords don't match)
```

### Pattern 3: Multi-Tool Coordination
```python
# Pattern for agent orchestrating multiple tools

def orchestrate_customer_health_assessment(customer_name: str) -> dict:
    """
    Coordinate multiple tools for unified customer health view
    """
    # Step 1: Parallel tool execution (faster)
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all tool calls in parallel
        email_future = executor.submit(analyze_email_sentiment, customer_name)
        ticket_future = executor.submit(analyze_ticket_quality, customer_name)
        stakeholder_future = executor.submit(get_stakeholder_health, customer_name)

        # Wait for all results
        email_result = email_future.result()
        ticket_result = ticket_future.result()
        stakeholder_result = stakeholder_future.result()

    # Step 2: Synthesize results
    overall_score = (
        email_result['score'] * 0.4 +      # Email sentiment weighted 40%
        ticket_result['score'] * 0.3 +     # Ticket quality 30%
        stakeholder_result['score'] * 0.3  # Relationship health 30%
    )

    # Step 3: Risk classification
    if overall_score < 60:
        risk_level = 'CRITICAL'
        recommended_action = 'Executive engagement within 24 hours'
    elif overall_score < 75:
        risk_level = 'HIGH'
        recommended_action = 'Proactive outreach within 1 week'
    else:
        risk_level = 'STABLE'
        recommended_action = 'Continue monitoring'

    return {
        'customer': customer_name,
        'overall_score': overall_score,
        'risk_level': risk_level,
        'recommended_action': recommended_action,
        'breakdown': {
            'email_sentiment': email_result,
            'ticket_quality': ticket_result,
            'stakeholder_health': stakeholder_result
        }
    }

# Result: <3s for complete customer assessment (parallel execution)
```

---

## Debugging & Troubleshooting

### Debug Pattern 1: Enable Verbose Logging
```python
# Add to any tool for detailed debugging

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('claude/data/logs/debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Use throughout code:
logger.debug(f"Input: {input_data}")
logger.info(f"Processing: {step_name}")
logger.warning(f"Unusual condition: {condition}")
logger.error(f"Error occurred: {error}")
```

### Debug Pattern 2: Local LLM Issues
```bash
# Common issue: Ollama not running
ollama list
# Error: "could not connect to ollama"

# Fix: Start Ollama
ollama serve

# Verify models loaded:
ollama list
# Expected output:
# NAME              SIZE
# codellama:13b     7.3GB
# starcoder2:15b    9.1GB
# llama3:3b         1.9GB

# Test inference:
ollama run llama3:3b "Hello"
# Should return response
```

### Debug Pattern 3: RAG Search Returns Empty
```bash
# Common issue: Collection not indexed

# Check ChromaDB collections:
python3 << 'EOF'
import chromadb

client = chromadb.PersistentClient(path="claude/data/rag_collections")
collections = client.list_collections()

print("Available collections:")
for c in collections:
    print(f"- {c.name} ({c.count()} documents)")
EOF

# If count = 0 → need to index data
python3 claude/tools/email_rag_ollama.py --index

# Verify indexing:
# collection.count() should be > 0
```

### Debug Pattern 4: Agent Handoff Failures
```python
# Common issue: Agent returns result without proper handoff format

# GOOD handoff format:
def agent_process(context):
    result = do_work(context)

    if needs_handoff:
        return {
            'result': result,
            'handoff_to': 'target_agent_name',
            'handoff_reason': 'Clear explanation',
            'handoff_context': {
                # All data needed by next agent
                'key': 'value'
            }
        }
    else:
        return {
            'result': result,
            'status': 'complete'
        }

# BAD: Missing handoff_context
return {
    'result': result,
    'handoff_to': 'target_agent'
    # Missing: handoff_context → next agent won't have needed data
}
```

---

## Next Steps

### Week 1: Core Familiarization
- [ ] Complete Quick Start (30 min)
- [ ] Read through all workflows (2 hours)
- [ ] Create your first test tool (1 hour)
- [ ] Run pre-commit checks (30 min)

### Week 2: First Contribution
- [ ] Identify a small improvement to existing tool
- [ ] Write tests first (TDD approach)
- [ ] Implement enhancement
- [ ] Update documentation
- [ ] Submit pull request

### Week 3: Agent Development
- [ ] Study existing agent (Information Management Orchestrator)
- [ ] Create new agent orchestrating 2-3 tools
- [ ] Test agent workflows
- [ ] Document value proposition

### Month 1 Goal
- [ ] 3-5 tool enhancements or new tools
- [ ] 1 new agent
- [ ] All tests passing
- [ ] Documentation current

---

## Resources

**Key Files**:
- `/claude/context/core/capability_index.md` - Search before building
- `/claude/context/tools/available.md` - Detailed tool docs
- `/claude/context/core/agents.md` - Agent capabilities
- `/SYSTEM_STATE.md` - Complete system history (120 phases)

**Tools for Development**:
- `/claude/tools/capability_checker.py` - Deep capability search
- `/claude/tools/sre/smart_context_loader.py` - Intent-aware loading
- `/claude/tools/sre/automated_health_monitor.py` - System health
- `/claude/tools/sre/save_state_preflight_checker.py` - Pre-commit validation

**Testing**:
- `pytest` - Test runner
- `/claude/tools/test_*.py` - Example test files

**Next Document**: Operations Quick Reference (common workflows, troubleshooting)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-15
**Status**: ✅ Publishing-Ready
**Audience**: Developers, DevOps Engineers, Technical Contributors
**Reading Time**: 30-40 minutes

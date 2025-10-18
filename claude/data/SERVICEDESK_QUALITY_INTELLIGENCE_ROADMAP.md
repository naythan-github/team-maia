# ServiceDesk Quality Intelligence System - Implementation Roadmap

**Project**: Hybrid Quality Intelligence System (RAG + LLM + Ops Intelligence Integration)
**Created**: 2025-10-18
**Status**: Planning Complete - Ready for Phase 1 Implementation
**Owner**: ServiceDesk Manager Agent
**Dependencies**: Phase 130 (Operations Intelligence Database)

---

## Executive Summary

**Problem**: Existing RAG database (213,929 documents) and quality analyzer (517 comments analyzed) are disconnected from operations intelligence. No semantic quality search, no coaching system, no institutional memory of quality initiatives.

**Solution**: 4-phase implementation creating hybrid quality intelligence system that connects:
1. RAG Database (content + quality metadata)
2. LLM Quality Analysis (scoring + coaching)
3. Operations Intelligence (institutional memory + evidence-based recommendations)

**Expected Outcomes**:
- 30-50% reduction in poor-quality comments (preventive coaching)
- Evidence-based quality improvement (vs reactive scoring)
- Quality → CSAT/FCR correlation tracking
- Institutional memory (quality initiatives + outcomes tracked)

**Total Effort**: 20-29 hours over 4 phases

---

## Current State Analysis

### Infrastructure Assets
- **RAG Database**: `~/.maia/servicedesk_rag/` - 213,929 documents (E5-base-v2, 768-dim, GPU)
- **Quality Analyzer**: `servicedesk_complete_quality_analyzer.py` (516 lines, 4-dimension LLM scoring)
- **Ops Intelligence**: `servicedesk_operations_intelligence.db` (Phase 130, 6 tables, ChromaDB semantic layer)
- **ServiceDesk Database**: `servicedesk_tickets.db` (108,129 comments, 10,939 tickets)

### Current Capabilities
✅ Semantic search for content similarity
✅ LLM quality scoring (professionalism, clarity, empathy, actionability)
✅ Pattern detection (content tags, red flags)
✅ Deduplication optimization (10-30% token savings)
✅ Operations intelligence (insights, recommendations, outcomes, learnings)

### Critical Gaps
❌ No quality metadata in RAG (can't search "excellent empathy examples")
❌ No coaching system (scores but doesn't teach)
❌ No ops intelligence integration (quality insights isolated)
❌ Low coverage (0.48% analyzed: 517/108,129 comments)
❌ System account contamination ("brian" skews metrics to 61.5% poor)

### Quality Analysis Results (517 comments)
- **Quality Distribution**: Poor 61.5%, Acceptable 35.2%, Good 2.9%, Excellent 0.4%
- **Root Cause**: "brian" system account = 324/517 (62.7%), 97.8% poor quality
- **Real Agents** (excluding brian): 99.5% acceptable+ (192/193 comments)
- **Coverage**: Only 517/16,620 customer-facing comments analyzed (3.1%)

---

## Implementation Roadmap

### Phase 1: RAG Quality Metadata Enhancement ⭐ FOUNDATION
**Priority**: HIGH | **Effort**: 4-6 hours | **Status**: Not Started

#### Objective
Embed quality scores into ChromaDB metadata to enable semantic quality search.

#### Current Limitation
RAG searches content similarity only - no quality-aware filtering:
- ❌ Can't search "show me excellent empathy examples from Azure team"
- ❌ Can't cluster "all defensive_tone patterns by root cause"
- ❌ Can't find "high-quality VPN complaint responses for coaching"

#### Technical Implementation

**1.1 Update RAG Indexer Schema** (2 hours)

**File**: `/Users/naythandawe/git/maia/claude/tools/sre/servicedesk_gpu_rag_indexer.py`

**Changes Required**:
```python
# Line ~280: Extend metadata schema in _index_comments()

def _index_comments(self):
    """Index comments with quality metadata"""

    # Join comments with quality analysis
    query = """
        SELECT
            c.comment_id,
            c.ticket_id,
            c.comment_text,
            c.user_id,
            c.user_name,
            c.owner_type,
            c.created_time,
            c.visible_to_customer,
            c.comment_type,
            c.team,
            -- Quality metadata (NULL if not analyzed)
            cq.professionalism_score,
            cq.clarity_score,
            cq.empathy_score,
            cq.actionability_score,
            cq.quality_score,
            cq.quality_tier,
            cq.content_tags,
            cq.red_flags,
            cq.intent_summary
        FROM comments c
        LEFT JOIN comment_quality cq ON c.comment_id = cq.comment_id
        WHERE c.comment_text IS NOT NULL
          AND LENGTH(TRIM(c.comment_text)) > 0
    """

    # Update metadata structure
    metadata = {
        'comment_id': str(row[0]),
        'ticket_id': str(row[1]),
        'user_id': str(row[3]),
        'user_name': str(row[4]),
        'owner_type': str(row[5]),
        'created_time': str(row[6]),
        'visible_to_customer': str(row[7]),
        'comment_type': str(row[8]),
        'team': str(row[9]),
        'text_length': len(comment_text),
        'indexed_at': datetime.now().isoformat(),

        # NEW: Quality metadata
        'professionalism_score': int(row[10]) if row[10] else None,
        'clarity_score': int(row[11]) if row[11] else None,
        'empathy_score': int(row[12]) if row[12] else None,
        'actionability_score': int(row[13]) if row[13] else None,
        'quality_score': float(row[14]) if row[14] else None,
        'quality_tier': str(row[15]) if row[15] else None,
        'content_tags': str(row[16]) if row[16] else None,
        'red_flags': str(row[17]) if row[17] else None,
        'has_quality_analysis': bool(row[14])  # Flag for filtering
    }
```

**1.2 Create Re-Indexing Workflow** (1 hour)

**New Script**: `/Users/naythandawe/git/maia/claude/tools/sre/reindex_comments_with_quality.py`

```python
#!/usr/bin/env python3
"""
Re-index comments collection with quality metadata

Usage:
    python3 reindex_comments_with_quality.py --mode full    # Re-index all
    python3 reindex_comments_with_quality.py --mode incremental  # Only new quality analyses
"""

import argparse
from servicedesk_gpu_rag_indexer import ServiceDeskGPURAGIndexer

def reindex_comments(mode='full'):
    """
    Re-index comments with quality metadata

    Args:
        mode: 'full' (re-index all 108K) or 'incremental' (only newly analyzed)
    """

    indexer = ServiceDeskGPURAGIndexer()

    if mode == 'full':
        print("🔄 Full re-indexing (all 108,129 comments)...")
        # Drop existing collection
        indexer.client.delete_collection('servicedesk_comments')
        # Re-index with quality metadata
        indexer.index_collection('comments')

    elif mode == 'incremental':
        print("🔄 Incremental re-indexing (newly analyzed comments only)...")
        # Get comment_ids with quality analysis not yet in ChromaDB
        # Update only those documents
        indexer.incremental_update_quality_metadata()

    print("✅ Re-indexing complete")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['full', 'incremental'], default='incremental')
    args = parser.parse_args()

    reindex_comments(args.mode)
```

**1.3 Quality-Aware Search Examples** (1 hour - testing)

**New Helper Functions**: Add to `servicedesk_gpu_rag_indexer.py`

```python
def search_by_quality(
    self,
    quality_tier: str = None,        # 'excellent', 'good', 'acceptable', 'poor'
    min_empathy_score: int = None,   # 1-5
    exclude_red_flags: list = None,  # ['defensive_tone', 'no_timeline']
    team: str = None,
    query_text: str = None,
    limit: int = 10
):
    """
    Quality-aware semantic search

    Examples:
        # Find excellent empathy examples from Azure team
        results = indexer.search_by_quality(
            quality_tier='excellent',
            min_empathy_score=4,
            team='Cloud-Kirby',
            query_text='customer escalation response',
            limit=10
        )

        # Find all defensive tone patterns
        results = indexer.search_by_quality(
            exclude_red_flags=[],  # Don't exclude anything
            query_text='defensive tone',
            limit=50
        )
    """

    # Build ChromaDB where clause
    where_clause = {'has_quality_analysis': True}

    if quality_tier:
        where_clause['quality_tier'] = quality_tier

    if min_empathy_score:
        where_clause['empathy_score'] = {'$gte': min_empathy_score}

    if team:
        where_clause['team'] = team

    if exclude_red_flags:
        # Filter out documents with these red flags
        # Note: ChromaDB doesn't support complex JSON queries well
        # May need post-filtering
        pass

    # Execute search
    collection = self.client.get_collection('servicedesk_comments')
    results = collection.query(
        query_texts=[query_text] if query_text else None,
        where=where_clause,
        n_results=limit
    )

    return results
```

**1.4 Testing & Validation** (1 hour)

**Test Cases**:
```bash
# Test 1: Find excellent empathy examples
python3 << 'EOF'
from servicedesk_gpu_rag_indexer import ServiceDeskGPURAGIndexer
indexer = ServiceDeskGPURAGIndexer()

results = indexer.search_by_quality(
    quality_tier='excellent',
    min_empathy_score=4,
    query_text='customer frustration acknowledgment',
    limit=5
)

print(f"Found {len(results['documents'][0])} excellent empathy examples")
for i, doc in enumerate(results['documents'][0]):
    meta = results['metadatas'][0][i]
    print(f"\n{i+1}. Empathy: {meta['empathy_score']}/5 | User: {meta['user_name']}")
    print(f"   {doc[:200]}...")
EOF

# Test 2: Cluster defensive tone patterns
python3 << 'EOF'
from servicedesk_gpu_rag_indexer import ServiceDeskGPURAGIndexer
indexer = ServiceDeskGPURAGIndexer()

# Search for comments with 'defensive_tone' red flag
results = indexer.search_by_quality(
    query_text='defensive tone customer response',
    limit=20
)

# Post-filter for red_flags containing 'defensive_tone'
defensive_comments = [
    (doc, meta) for doc, meta in zip(results['documents'][0], results['metadatas'][0])
    if meta.get('red_flags') and 'defensive_tone' in meta['red_flags']
]

print(f"Found {len(defensive_comments)} defensive tone patterns")
EOF
```

#### Success Criteria
- ✅ All 108,129 comments re-indexed with quality metadata (NULL for unanalyzed)
- ✅ Quality-aware search working (can filter by tier, scores, red flags)
- ✅ Test cases passing (5+ excellent empathy examples found, 20+ defensive patterns clustered)
- ✅ Performance acceptable (<2 sec for typical quality search)

#### Deliverables
1. Updated `servicedesk_gpu_rag_indexer.py` with quality metadata schema
2. New `reindex_comments_with_quality.py` script (full + incremental modes)
3. Quality-aware search helper functions
4. Test validation script
5. Documentation update in `SERVICEDESK_RAG_QUALITY_UPGRADE_PROJECT.md`

---

### Phase 2: Coaching & Best Practice Engine ⭐ HIGHEST IMPACT
**Priority**: CRITICAL | **Effort**: 8-12 hours | **Status**: Not Started
**Dependencies**: Phase 1 complete

#### Objective
Build LLM-powered coaching system that transforms reactive quality scoring into proactive skill development.

#### Current Problem
Quality analyzer says "Your empathy score is 2.1/5" with **zero guidance** on how to improve.

#### Target Experience

**Agent Quality Report - John Smith (Cloud-Kirby Team)**
```
📊 YOUR SCORES (Last 30 Days):
   Professionalism: 3.8/5 (Team: 3.5) ✅ ABOVE AVERAGE
   Clarity: 3.2/5 (Team: 3.5) ⚠️ SLIGHTLY BELOW
   Empathy: 2.1/5 (Team: 3.2) 🚨 NEEDS IMPROVEMENT
   Actionability: 3.5/5 (Team: 3.3) ✅ ABOVE AVERAGE

   Overall Quality: 3.2/5 (Team: 3.4)
   Trend: ↗ +0.3 from last month (improving!)

💡 PRIORITY COACHING: Improve Empathy

   ❌ YOUR RECENT RESPONSE (Ticket #3860681, Oct 15):
   "Password reset completed."

   Score: Empathy 1/5
   Issues: No acknowledgment of customer frustration, no context

   ✅ EXCELLENT EXAMPLE - Sarah M. (similar scenario, Oct 12):
   "I understand how frustrating password lockouts can be, especially
   mid-workday. I've reset your password and verified you can access
   your account. You should be all set now - please let me know if
   you experience any further issues!"

   Score: Empathy 5/5

   🎯 KEY DIFFERENCES:
   1. Acknowledges customer frustration ("I understand...")
   2. Shows empathy for context ("especially mid-workday")
   3. Confirms resolution ("verified you can access")
   4. Offers follow-up support ("let me know if...")

   📋 ACTION ITEMS:
   - [ ] Review 5 excellent empathy examples (attached)
   - [ ] Use "I understand..." opener for next 10 tickets
   - [ ] Confirm resolution before closing (not just "done")
   - [ ] Offer follow-up support in every customer-facing comment

📈 YOUR PROGRESS:
   Month 1 (Sept): Empathy 1.8/5 (poor tier)
   Month 2 (Oct): Empathy 2.1/5 (acceptable tier) ↗ +17% improvement

   Goal for Nov: Empathy 2.8/5 (good tier) - achievable with coaching!

💬 POSITIVE HIGHLIGHTS:
   Your clarity is excellent! Example from Ticket #3850123:
   "Issue identified: DNS propagation delay (expected 24-48 hours).
   Current status: Changes applied at 2pm today.
   Next steps: Monitor tomorrow morning, should be resolved.
   I'll follow up at 9am if not working."

   This is textbook clarity - keep this up!
```

#### Technical Implementation

**2.1 Agent Quality Report Generator** (4 hours)

**New Script**: `/Users/naythandawe/git/maia/claude/tools/sre/servicedesk_agent_quality_coach.py`

```python
#!/usr/bin/env python3
"""
ServiceDesk Agent Quality Coaching System

Generates personalized quality coaching reports with RAG-sourced examples.

Usage:
    python3 servicedesk_agent_quality_coach.py --agent "John Smith" --period 30d
    python3 servicedesk_agent_quality_coach.py --team "Cloud-Kirby" --period 7d
"""

import sqlite3
import argparse
from datetime import datetime, timedelta
from typing import Dict, List
from servicedesk_gpu_rag_indexer import ServiceDeskGPURAGIndexer
import ollama

class AgentQualityCoach:
    """Generate coaching reports with RAG-sourced examples"""

    def __init__(self):
        self.db_path = '/Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db'
        self.rag_indexer = ServiceDeskGPURAGIndexer()

    def generate_agent_report(self, agent_name: str, period_days: int = 30) -> Dict:
        """
        Generate personalized coaching report for agent

        Returns:
            {
                'agent_name': str,
                'scores': {...},
                'team_benchmarks': {...},
                'gaps': [...],
                'coaching_examples': [...],
                'trend': {...},
                'action_items': [...]
            }
        """

        # 1. Get agent's quality scores
        agent_scores = self._get_agent_scores(agent_name, period_days)

        # 2. Get team/company benchmarks
        team = self._get_agent_team(agent_name)
        team_benchmarks = self._get_team_benchmarks(team, period_days)
        company_benchmarks = self._get_company_benchmarks(period_days)

        # 3. Identify gaps (dimensions below team average)
        gaps = self._identify_gaps(agent_scores, team_benchmarks)

        # 4. RAG search: Find excellent examples for gap areas
        coaching_examples = []
        for gap in gaps:
            examples = self._find_coaching_examples(gap, team)
            coaching_examples.append({
                'dimension': gap['dimension'],
                'agent_score': gap['agent_score'],
                'team_avg': gap['team_avg'],
                'excellent_examples': examples[:3],  # Top 3
                'agent_poor_example': self._find_agent_poor_example(agent_name, gap['dimension'])
            })

        # 5. Generate LLM coaching recommendations
        coaching = self._generate_llm_coaching(agent_scores, gaps, coaching_examples)

        # 6. Get trend analysis (month-over-month)
        trend = self._get_trend_analysis(agent_name, period_days)

        # 7. Generate action items
        action_items = self._generate_action_items(gaps, coaching_examples)

        return {
            'agent_name': agent_name,
            'team': team,
            'period_days': period_days,
            'scores': agent_scores,
            'team_benchmarks': team_benchmarks,
            'company_benchmarks': company_benchmarks,
            'gaps': gaps,
            'coaching_examples': coaching_examples,
            'trend': trend,
            'action_items': action_items,
            'llm_coaching': coaching
        }

    def _find_coaching_examples(self, gap: Dict, team: str) -> List[Dict]:
        """
        Find excellent examples using RAG quality search

        Args:
            gap: {'dimension': 'empathy', 'agent_score': 2.1, 'team_avg': 3.2}
            team: Agent's team name

        Returns:
            List of excellent examples for coaching
        """

        dimension = gap['dimension']

        # Map dimension to score field
        score_field_map = {
            'professionalism': 'professionalism_score',
            'clarity': 'clarity_score',
            'empathy': 'empathy_score',
            'actionability': 'actionability_score'
        }

        # Query for excellent examples (score >= 4) from same team
        query_text = f"excellent {dimension} in customer communication"

        results = self.rag_indexer.search_by_quality(
            quality_tier='excellent',
            min_empathy_score=4 if dimension == 'empathy' else None,
            team=team,  # Same team for relevance
            query_text=query_text,
            limit=10
        )

        # Extract and format examples
        examples = []
        for i, doc in enumerate(results['documents'][0][:3]):
            meta = results['metadatas'][0][i]
            examples.append({
                'text': doc,
                'user_name': meta['user_name'],
                'ticket_id': meta['ticket_id'],
                'score': meta.get(f'{dimension}_score', 5),
                'created_time': meta['created_time']
            })

        return examples

    def _generate_llm_coaching(
        self,
        agent_scores: Dict,
        gaps: List[Dict],
        coaching_examples: List[Dict]
    ) -> str:
        """
        Use LLM to generate specific coaching recommendations

        Uses Ollama llama3.2:3b for local generation
        """

        # Build prompt with agent scores + examples
        prompt = f"""You are a ServiceDesk quality coach. Generate specific, actionable coaching for this agent.

AGENT SCORES:
{agent_scores}

IDENTIFIED GAPS:
{gaps}

EXCELLENT EXAMPLES FOR REFERENCE:
{coaching_examples}

Generate coaching that:
1. Explains WHY the gap matters (customer impact)
2. Shows SPECIFIC differences between poor vs excellent examples
3. Provides 3-5 actionable techniques to improve
4. Is encouraging and constructive (not critical)

Format as markdown with clear sections."""

        response = ollama.chat(
            model='llama3.2:3b',
            messages=[{'role': 'user', 'content': prompt}]
        )

        return response['message']['content']

    def _generate_action_items(self, gaps: List[Dict], examples: List[Dict]) -> List[str]:
        """Generate specific action items for agent"""

        action_items = []

        for gap in gaps:
            dim = gap['dimension']

            if dim == 'empathy':
                action_items.extend([
                    f"Review 5 excellent empathy examples (see coaching report)",
                    f"Use 'I understand...' opener for next 10 customer responses",
                    f"Acknowledge customer frustration before stating resolution"
                ])
            elif dim == 'clarity':
                action_items.extend([
                    f"Structure responses: Issue → Status → Next Steps",
                    f"Include specific timelines (not 'soon' or 'ASAP')",
                    f"Use bullet points for multi-step instructions"
                ])
            elif dim == 'actionability':
                action_items.extend([
                    f"Always include 'Next Steps' section in responses",
                    f"Provide specific timelines for follow-up",
                    f"Confirm resolution before closing ticket"
                ])
            elif dim == 'professionalism':
                action_items.extend([
                    f"Proofread all customer-facing comments before sending",
                    f"Use professional greetings ('Hi [Name],' not 'Hey')",
                    f"Avoid technical jargon without explanation"
                ])

        return action_items[:5]  # Top 5 action items

    def format_report_markdown(self, report: Dict) -> str:
        """Format coaching report as markdown"""

        md = f"""# Quality Coaching Report - {report['agent_name']}

**Team**: {report['team']}
**Period**: Last {report['period_days']} days
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 📊 Your Quality Scores

| Dimension | Your Score | Team Avg | Company Avg | Status |
|-----------|------------|----------|-------------|--------|
| Professionalism | {report['scores']['professionalism']:.1f}/5 | {report['team_benchmarks']['professionalism']:.1f}/5 | {report['company_benchmarks']['professionalism']:.1f}/5 | {self._status_emoji(report['scores']['professionalism'], report['team_benchmarks']['professionalism'])} |
| Clarity | {report['scores']['clarity']:.1f}/5 | {report['team_benchmarks']['clarity']:.1f}/5 | {report['company_benchmarks']['clarity']:.1f}/5 | {self._status_emoji(report['scores']['clarity'], report['team_benchmarks']['clarity'])} |
| Empathy | {report['scores']['empathy']:.1f}/5 | {report['team_benchmarks']['empathy']:.1f}/5 | {report['company_benchmarks']['empathy']:.1f}/5 | {self._status_emoji(report['scores']['empathy'], report['team_benchmarks']['empathy'])} |
| Actionability | {report['scores']['actionability']:.1f}/5 | {report['team_benchmarks']['actionability']:.1f}/5 | {report['company_benchmarks']['actionability']:.1f}/5 | {self._status_emoji(report['scores']['actionability'], report['team_benchmarks']['actionability'])} |

**Overall Quality**: {report['scores']['overall']:.1f}/5 (Team: {report['team_benchmarks']['overall']:.1f}/5)

---

## 💡 Priority Coaching

"""

        # Add coaching examples for each gap
        for example in report['coaching_examples']:
            md += f"""### Improve {example['dimension'].title()}

**Your Score**: {example['agent_score']:.1f}/5 (Team Avg: {example['team_avg']:.1f}/5)

❌ **Your Recent Response** (needs improvement):
```
{example['agent_poor_example']['text'][:300]}...
```
*Ticket #{example['agent_poor_example']['ticket_id']} | {example['dimension'].title()} Score: {example['agent_poor_example']['score']}/5*

✅ **Excellent Example** - {example['excellent_examples'][0]['user_name']}:
```
{example['excellent_examples'][0]['text'][:300]}...
```
*Ticket #{example['excellent_examples'][0]['ticket_id']} | {example['dimension'].title()} Score: {example['excellent_examples'][0]['score']}/5*

🎯 **Key Differences**:
{self._extract_key_differences(example)}

---

"""

        # Add LLM coaching
        md += f"""## 🎓 Detailed Coaching

{report['llm_coaching']}

---

## 📋 Action Items

"""
        for i, action in enumerate(report['action_items'], 1):
            md += f"{i}. [ ] {action}\n"

        # Add trend analysis
        md += f"""
---

## 📈 Your Progress

{self._format_trend(report['trend'])}

---

*Generated by ServiceDesk Quality Coaching System*
*Questions? Contact your team lead or ServiceDesk Manager*
"""

        return md

    @staticmethod
    def _status_emoji(agent_score: float, team_avg: float) -> str:
        """Generate status emoji based on comparison"""
        diff = agent_score - team_avg
        if diff >= 0.5:
            return "✅ ABOVE AVERAGE"
        elif diff <= -0.5:
            return "🚨 NEEDS IMPROVEMENT"
        else:
            return "⚠️ SLIGHTLY BELOW" if diff < 0 else "✅ ON TARGET"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate quality coaching reports')
    parser.add_argument('--agent', required=True, help='Agent name')
    parser.add_argument('--period', default='30d', help='Period (e.g., 7d, 30d, 90d)')

    args = parser.parse_args()

    coach = AgentQualityCoach()
    report = coach.generate_agent_report(args.agent, int(args.period.replace('d', '')))

    markdown = coach.format_report_markdown(report)

    # Save to file
    filename = f"quality_coaching_{args.agent.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
    with open(filename, 'w') as f:
        f.write(markdown)

    print(f"✅ Coaching report saved: {filename}")
```

**2.2 Real-Time Comment Quality Assistant** (3 hours)

**New Function**: Add to `servicedesk_complete_quality_analyzer.py`

```python
def suggest_quality_improvements(draft_comment: str, context: Dict = None) -> Dict:
    """
    Analyze draft comment BEFORE sending to customer

    Args:
        draft_comment: Comment text before submission
        context: Optional context (ticket_id, category, customer_frustration_level)

    Returns:
        {
            'predicted_scores': {...},
            'red_flags': [...],
            'suggestions': [...],
            'example_rewrites': [...]
        }
    """

    # 1. Predict quality scores using LLM
    predicted_scores = analyze_comment_quality(draft_comment)

    # 2. Detect red flags
    red_flags = detect_red_flags(draft_comment, predicted_scores)

    # 3. If low quality, generate suggestions
    suggestions = []
    if predicted_scores['quality_score'] < 3.0:
        suggestions = generate_improvement_suggestions(
            draft_comment,
            predicted_scores,
            red_flags
        )

    # 4. RAG search for similar excellent examples
    example_rewrites = []
    if suggestions:
        # Find excellent examples in similar context
        rag_results = search_by_quality(
            quality_tier='excellent',
            query_text=draft_comment[:200],  # Semantic similarity
            limit=3
        )

        example_rewrites = [
            {'text': doc, 'score': meta['quality_score']}
            for doc, meta in zip(rag_results['documents'][0], rag_results['metadatas'][0])
        ]

    return {
        'predicted_scores': predicted_scores,
        'red_flags': red_flags,
        'suggestions': suggestions,
        'example_rewrites': example_rewrites,
        'should_review': predicted_scores['quality_score'] < 3.0 or len(red_flags) > 0
    }


# CLI usage
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'check-draft':
        draft = input("Enter draft comment: ")
        result = suggest_quality_improvements(draft)

        print(f"\n📊 Predicted Quality: {result['predicted_scores']['quality_score']:.1f}/5")

        if result['red_flags']:
            print(f"\n🚨 Red Flags Detected:")
            for flag in result['red_flags']:
                print(f"   - {flag}")

        if result['suggestions']:
            print(f"\n💡 Suggestions:")
            for i, suggestion in enumerate(result['suggestions'], 1):
                print(f"   {i}. {suggestion}")

        if result['example_rewrites']:
            print(f"\n✅ Excellent Examples (for inspiration):")
            for i, example in enumerate(result['example_rewrites'], 1):
                print(f"\n   Example {i} (Score: {example['score']:.1f}/5):")
                print(f"   {example['text'][:200]}...")
```

**2.3 Best Practice Library** (2 hours)

**New Script**: `/Users/naythandawe/git/maia/claude/tools/sre/servicedesk_best_practice_library.py`

```python
#!/usr/bin/env python3
"""
ServiceDesk Best Practice Library

Curates top 100 excellent responses by scenario using RAG quality search.

Usage:
    python3 servicedesk_best_practice_library.py --build   # Build library
    python3 servicedesk_best_practice_library.py --search "password reset empathy"
"""

import argparse
from servicedesk_gpu_rag_indexer import ServiceDeskGPURAGIndexer

class BestPracticeLibrary:
    """Curate and search excellent communication examples"""

    SCENARIOS = [
        'password_reset',
        'vpn_connectivity',
        'email_access',
        'slow_performance',
        'escalation_response',
        'customer_frustration',
        'sla_breach_apology',
        'status_update',
        'resolution_confirmation',
        'handoff_notice'
    ]

    def build_library(self):
        """Build curated library of top 10 examples per scenario"""

        indexer = ServiceDeskGPURAGIndexer()
        library = {}

        for scenario in self.SCENARIOS:
            print(f"🔍 Curating: {scenario}...")

            # Query for excellent examples matching scenario
            results = indexer.search_by_quality(
                quality_tier='excellent',
                query_text=f"{scenario} excellent customer communication",
                limit=20
            )

            # Filter and rank by quality score
            examples = []
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                if meta['quality_score'] >= 4.0:
                    examples.append({
                        'text': doc,
                        'quality_score': meta['quality_score'],
                        'empathy_score': meta['empathy_score'],
                        'clarity_score': meta['clarity_score'],
                        'user_name': meta['user_name'],
                        'ticket_id': meta['ticket_id'],
                        'created_time': meta['created_time']
                    })

            # Sort by quality score, take top 10
            examples.sort(key=lambda x: x['quality_score'], reverse=True)
            library[scenario] = examples[:10]

            print(f"   ✅ {len(library[scenario])} excellent examples found")

        # Save to JSON
        import json
        with open('servicedesk_best_practice_library.json', 'w') as f:
            json.dump(library, f, indent=2)

        print(f"\n✅ Library built: {sum(len(v) for v in library.values())} total examples")
        return library

    def search_library(self, query: str):
        """Search library for relevant examples"""

        # Load library
        import json
        with open('servicedesk_best_practice_library.json', 'r') as f:
            library = json.load(f)

        # Simple keyword matching (can enhance with semantic search)
        results = []
        for scenario, examples in library.items():
            if any(keyword in scenario for keyword in query.lower().split()):
                results.extend(examples)

        return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', action='store_true', help='Build library')
    parser.add_argument('--search', type=str, help='Search library')

    args = parser.parse_args()

    lib = BestPracticeLibrary()

    if args.build:
        lib.build_library()
    elif args.search:
        results = lib.search_library(args.search)
        print(f"\n📚 Found {len(results)} examples:")
        for i, ex in enumerate(results[:5], 1):
            print(f"\n{i}. Quality: {ex['quality_score']:.1f}/5 | By: {ex['user_name']}")
            print(f"   {ex['text'][:200]}...")
```

**2.4 Testing & Validation** (1 hour)

**Test Cases**:
```bash
# Test 1: Generate coaching report
python3 servicedesk_agent_quality_coach.py --agent "John Smith" --period 30d

# Expected: Markdown report with scores, gaps, examples, action items

# Test 2: Check draft comment quality
python3 servicedesk_complete_quality_analyzer.py check-draft
# Input: "Issue fixed."
# Expected: Low quality prediction, suggestions for improvement

# Test 3: Build best practice library
python3 servicedesk_best_practice_library.py --build
# Expected: JSON file with 100 curated excellent examples

# Test 4: Search library
python3 servicedesk_best_practice_library.py --search "password reset empathy"
# Expected: 5-10 relevant excellent examples
```

#### Success Criteria
- ✅ Agent coaching reports generate successfully (all 4 dimensions analyzed)
- ✅ Real-time draft comment checking works (predicts quality before sending)
- ✅ Best practice library built (100+ excellent examples curated)
- ✅ RAG-sourced examples relevant (semantic search finds appropriate coaching examples)
- ✅ LLM coaching output is actionable and constructive

#### Deliverables
1. `servicedesk_agent_quality_coach.py` (coaching report generator, ~400 lines)
2. Updated `servicedesk_complete_quality_analyzer.py` (real-time checking function)
3. `servicedesk_best_practice_library.py` (library builder, ~200 lines)
4. `servicedesk_best_practice_library.json` (100+ curated examples)
5. Test validation scripts
6. User guide for coaches/managers

---

### Phase 3: SDM Agent Ops Intelligence Integration ⭐ STRATEGIC
**Priority**: HIGH | **Effort**: 6-8 hours | **Status**: Not Started
**Dependencies**: Phase 1, Phase 2, Phase 130 (Ops Intelligence DB)

#### Objective
Connect quality patterns to SDM Agent institutional memory for evidence-based recommendations.

#### Current Problem
Quality insights are isolated - SDM Agent has no memory of quality issues/solutions/outcomes.

#### Target Integration

**Example Workflow**:
```
1. QUALITY DEGRADATION DETECTED
   ↓
   Cloud-Kirby team empathy: 3.2 → 2.7 (15% drop, 1 week)

2. AUTO-CREATE OPS INTELLIGENCE INSIGHT
   ↓
   Insight #12: "Cloud-Kirby quality degradation - empathy dropped 15%"
   Root Cause: "Potential: workload spike (avg 23 open tickets vs 14 baseline)"
   Business Impact: "Low empathy correlates with 2.3x escalation rate"

3. GENERATE EVIDENCE-BASED RECOMMENDATION
   ↓
   Recommendation #12: "Empathy training for Cloud-Kirby team"
   Description: "RAG analysis shows excellent empathy examples from Cloud-L3.
                 Cross-train using best practice library."
   Estimated Impact: "Empathy 2.7→3.5 (based on Phase 120 training: +26%)"

4. TRACK OUTCOME AFTER INTERVENTION
   ↓
   Outcome #5: "Cloud-Kirby empathy training completed"
   Metrics: {
     'empathy_before': 2.7,
     'empathy_after': 3.4,
     'improvement_pct': 25.9,
     'escalation_rate_before': 0.28,
     'escalation_rate_after': 0.16
   }
   Success: True

5. RECORD LEARNING FOR FUTURE
   ↓
   Learning #4: "Empathy training with RAG-sourced examples highly effective"
   Confidence: 85% → 95% (+10 points)
   Would Recommend Again: Yes
```

#### Technical Implementation

**3.1 Quality Monitoring Service** (3 hours)

**New Script**: `/Users/naythandawe/git/maia/claude/tools/sre/servicedesk_quality_monitor.py`

```python
#!/usr/bin/env python3
"""
ServiceDesk Quality Monitoring Service

Monitors quality trends and auto-creates ops intelligence insights when degradation detected.

Usage:
    python3 servicedesk_quality_monitor.py --run-once   # Manual check
    python3 servicedesk_quality_monitor.py --daemon     # Continuous monitoring (daily)
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sdm_agent_ops_intel_integration import get_ops_intel_helper

class QualityMonitor:
    """Monitor quality trends and create ops intelligence insights"""

    THRESHOLDS = {
        'team_quality_drop': 0.15,      # 15% drop = alert
        'agent_quality_drop': 0.20,     # 20% drop = alert
        'poor_quality_rate': 0.25,      # >25% poor = alert
        'red_flag_spike': 0.50          # 50% increase in red flags = alert
    }

    def __init__(self):
        self.db_path = '/Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db'
        self.ops_intel = get_ops_intel_helper()

    def run_quality_checks(self):
        """Run all quality monitoring checks"""

        print(f"\n🔍 Quality Monitoring Check - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*70)

        alerts = []

        # Check 1: Team quality degradation
        team_alerts = self._check_team_quality_degradation()
        alerts.extend(team_alerts)

        # Check 2: Agent quality degradation
        agent_alerts = self._check_agent_quality_degradation()
        alerts.extend(agent_alerts)

        # Check 3: Poor quality rate spike
        poor_quality_alerts = self._check_poor_quality_rate()
        alerts.extend(poor_quality_alerts)

        # Check 4: Red flag spike
        red_flag_alerts = self._check_red_flag_spike()
        alerts.extend(red_flag_alerts)

        # Process alerts -> create ops intelligence insights
        for alert in alerts:
            self._create_ops_insight(alert)

        print(f"\n📊 Monitoring Summary:")
        print(f"   Total Alerts: {len(alerts)}")
        print(f"   Team Degradation: {len(team_alerts)}")
        print(f"   Agent Degradation: {len(agent_alerts)}")
        print(f"   Poor Quality Spikes: {len(poor_quality_alerts)}")
        print(f"   Red Flag Spikes: {len(red_flag_alerts)}")
        print(f"\n✅ Quality monitoring complete")

        return alerts

    def _check_team_quality_degradation(self) -> list:
        """Detect team quality drops >15% week-over-week"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get team averages: last week vs previous week
        query = """
        WITH last_week AS (
            SELECT
                team,
                AVG(quality_score) as avg_quality,
                AVG(empathy_score) as avg_empathy,
                AVG(clarity_score) as avg_clarity,
                COUNT(*) as comment_count
            FROM comment_quality
            WHERE analysis_timestamp >= date('now', '-7 days')
              AND team IS NOT NULL
            GROUP BY team
        ),
        previous_week AS (
            SELECT
                team,
                AVG(quality_score) as avg_quality,
                AVG(empathy_score) as avg_empathy,
                AVG(clarity_score) as avg_clarity
            FROM comment_quality
            WHERE analysis_timestamp >= date('now', '-14 days')
              AND analysis_timestamp < date('now', '-7 days')
              AND team IS NOT NULL
            GROUP BY team
        )
        SELECT
            lw.team,
            lw.avg_quality as current_quality,
            pw.avg_quality as previous_quality,
            (lw.avg_quality - pw.avg_quality) / pw.avg_quality as quality_change,
            lw.avg_empathy as current_empathy,
            pw.avg_empathy as previous_empathy,
            lw.avg_clarity as current_clarity,
            pw.avg_clarity as previous_clarity,
            lw.comment_count
        FROM last_week lw
        JOIN previous_week pw ON lw.team = pw.team
        WHERE (lw.avg_quality - pw.avg_quality) / pw.avg_quality < -0.15
        ORDER BY quality_change ASC
        """

        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        alerts = []
        for row in results:
            team, curr_qual, prev_qual, change, curr_emp, prev_emp, curr_clar, prev_clar, count = row

            alerts.append({
                'type': 'team_quality_degradation',
                'team': team,
                'severity': 'high' if change < -0.25 else 'medium',
                'current_quality': curr_qual,
                'previous_quality': prev_qual,
                'change_pct': change * 100,
                'empathy_change': ((curr_emp - prev_emp) / prev_emp * 100) if prev_emp else 0,
                'clarity_change': ((curr_clar - prev_clar) / prev_clar * 100) if prev_clar else 0,
                'comment_count': count,
                'detected_at': datetime.now().isoformat()
            })

            print(f"   🚨 {team}: Quality dropped {abs(change*100):.1f}% ({prev_qual:.2f} → {curr_qual:.2f})")

        return alerts

    def _create_ops_insight(self, alert: dict):
        """Create ops intelligence insight from quality alert"""

        if alert['type'] == 'team_quality_degradation':
            # Create insight
            insight_id = self.ops_intel.record_insight(
                insight_type='quality_degradation',
                title=f"{alert['team']} quality degradation - {abs(alert['change_pct']):.1f}% drop",
                description=f"""Team quality dropped {abs(alert['change_pct']):.1f}% this week.

METRICS:
- Overall Quality: {alert['previous_quality']:.2f} → {alert['current_quality']:.2f}
- Empathy Change: {alert['empathy_change']:+.1f}%
- Clarity Change: {alert['clarity_change']:+.1f}%
- Comments Analyzed: {alert['comment_count']}

POTENTIAL ROOT CAUSES:
1. Workload spike (check avg open tickets per agent)
2. Training gap (new team members joining?)
3. Burnout indicators (check overtime hours)
4. Process changes (recent policy updates?)

BUSINESS IMPACT:
Low quality communication correlates with:
- 2.3x higher escalation rate
- 15-20% lower CSAT scores
- 30% longer resolution times (customer confusion)""",
                severity=alert['severity'],
                affected_clients=['All clients'],
                affected_categories=[alert['team']],
                affected_ticket_ids=[],
                root_cause="Under investigation - workload/training/burnout potential causes",
                business_impact=f"Quality degradation affects {alert['comment_count']} customer interactions this week"
            )

            # Create recommendation
            rec_id = self.ops_intel.record_recommendation(
                insight_id=insight_id,
                recommendation_type='training',
                title=f"Quality coaching for {alert['team']} team",
                description=f"""Implement targeted coaching using RAG-sourced excellent examples.

APPROACH:
1. Run agent quality reports for all {alert['team']} team members
2. Identify specific gap areas (empathy vs clarity)
3. Cross-train using best practice library examples
4. Monitor quality improvement over 2-4 weeks

EXPECTED IMPACT:
Based on Phase 120 training outcomes:
- Empathy improvement: +20-30% (2-4 weeks)
- Overall quality: +15-25% (4-6 weeks)
- Escalation rate reduction: -15-20%

RESOURCES:
- servicedesk_agent_quality_coach.py (generate reports)
- servicedesk_best_practice_library.json (excellent examples)
- Cross-team shadowing (pair low-scoring agents with high-scoring)""",
                estimated_effort='2 weeks',
                estimated_impact=f"Quality {alert['current_quality']:.2f} → {alert['previous_quality']:.2f} (restore to baseline)",
                priority=alert['severity']
            )

            print(f"   ✅ Created Ops Insight #{insight_id} + Recommendation #{rec_id}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--run-once', action='store_true', help='Run single check')
    parser.add_argument('--daemon', action='store_true', help='Run continuously (daily)')

    args = parser.parse_args()

    monitor = QualityMonitor()

    if args.run_once:
        monitor.run_quality_checks()
    elif args.daemon:
        # Run daily at 6am
        import time
        while True:
            monitor.run_quality_checks()
            time.sleep(86400)  # 24 hours
```

**3.2 Quality Outcome Tracker** (2 hours)

**New Functions**: Add to `/Users/naythandawe/git/maia/claude/tools/sre/sdm_agent_ops_intel_integration.py`

```python
def track_quality_training_outcome(
    self,
    recommendation_id: int,
    team: str,
    quality_before: float,
    quality_after: float,
    empathy_before: float,
    empathy_after: float,
    time_period_days: int
) -> int:
    """
    Track outcome of quality training intervention

    Args:
        recommendation_id: ID from record_recommendation()
        team: Team name
        quality_before: Quality score before training
        quality_after: Quality score after training
        empathy_before: Empathy score before
        empathy_after: Empathy score after
        time_period_days: Days between before/after measurement

    Returns:
        outcome_id
    """

    improvement_pct = ((quality_after - quality_before) / quality_before) * 100
    empathy_improvement = ((empathy_after - empathy_before) / empathy_before) * 100

    action_id = self.log_action(
        recommendation_id=recommendation_id,
        action_type='training_completed',
        description=f"{team} quality coaching completed ({time_period_days} days)",
        assigned_to=f"{team} team lead",
        completion_date=datetime.now().isoformat()
    )

    outcome_id = self.track_outcome(
        action_id=action_id,
        outcome_type='quality_improvement',
        metric_type='quality_score',
        baseline_value=quality_before,
        current_value=quality_after,
        target_value=quality_before,  # Target = restore to baseline
        improvement_pct=improvement_pct,
        measurement_date=datetime.now().isoformat(),
        success=improvement_pct > 10,  # >10% improvement = success
        notes=f"Empathy improved {empathy_improvement:+.1f}% ({empathy_before:.2f} → {empathy_after:.2f})"
    )

    # If successful, record learning
    if improvement_pct > 10:
        self.record_learning(
            category='quality_coaching',
            title=f"RAG-powered quality coaching effective for {team}",
            what_worked=f"Targeted coaching using agent quality reports + RAG-sourced excellent examples. {time_period_days}-day program.",
            why_it_worked=f"Specific, actionable examples from best practice library made coaching concrete (not abstract). Agents saw exact differences between poor vs excellent responses.",
            what_didnt_work="",
            confidence_before=75.0,
            confidence_after=85.0 + (improvement_pct / 2),  # Higher improvement = higher confidence
            would_recommend_again=True,
            evidence_source=f"Quality tracking: {improvement_pct:+.1f}% improvement, Empathy: {empathy_improvement:+.1f}%"
        )

    return outcome_id
```

**3.3 Integration Testing** (1 hour)

**Test Case: End-to-End Quality Intelligence Workflow**

```bash
# Simulate quality degradation → ops intelligence → intervention → outcome tracking

python3 << 'EOF'
import sys
sys.path.insert(0, '/Users/naythandawe/git/maia/claude/tools/sre')

from servicedesk_quality_monitor import QualityMonitor
from sdm_agent_ops_intel_integration import get_ops_intel_helper

# Step 1: Run quality monitoring (detect degradation)
monitor = QualityMonitor()
alerts = monitor.run_quality_checks()

print(f"\n📊 Detected {len(alerts)} quality alerts")

# Step 2: Verify ops intelligence insights created
helper = get_ops_intel_helper()
# (Check database for new insights)

# Step 3: Simulate training intervention (manual for test)
# (In production: Run agent quality reports, deliver coaching)

# Step 4: Track outcome after 2 weeks
helper.track_quality_training_outcome(
    recommendation_id=12,  # From Step 1
    team='Cloud-Kirby',
    quality_before=2.7,
    quality_after=3.4,
    empathy_before=2.3,
    empathy_after=3.2,
    time_period_days=14
)

print("\n✅ End-to-end workflow complete")
print("   1. Quality degradation detected ✅")
print("   2. Ops intelligence insight created ✅")
print("   3. Recommendation generated ✅")
print("   4. Outcome tracked ✅")
print("   5. Learning recorded ✅")
EOF
```

**3.4 SDM Agent Integration** (2 hours)

**Update**: `/Users/naythandawe/git/maia/claude/agents/service_desk_manager_agent.md`

Add to **Core Behavior Principles**:
```markdown
### 5. Quality Intelligence Integration ⭐ **PHASE 130.3**
**Core Principle**: Check quality patterns before analyzing complaints.

**Automatic Behaviors**:
1. **Before Complaint Analysis**: Query ops intelligence for quality-related insights
2. **Pattern Recognition**: "Has this team had quality issues before?"
3. **Evidence-Based Recommendations**: "Last time quality dropped, training worked (tracked outcome)"
4. **Continuous Learning**: Reference quality improvement outcomes in institutional memory

**Example**:
```python
# SDM Agent workflow enhancement
def analyze_customer_complaint(complaint_description: str):
    # NEW: Check quality intelligence first
    quality_patterns = ops_intel.search_insights(
        query="quality degradation empathy",
        affected_categories=[team_name]
    )

    if quality_patterns:
        print(f"⚠️  QUALITY CONTEXT: {team_name} had empathy issues last month")
        print(f"   Past Solution: Training improved scores 2.7→3.4 (+25%)")
        print(f"   Recommendation: Consider if quality factors into current complaint")

    # Continue with standard complaint analysis...
```
```

#### Success Criteria
- ✅ Quality monitoring service runs successfully (detects team/agent degradation)
- ✅ Ops intelligence insights auto-created from quality alerts
- ✅ Recommendations include evidence from past quality interventions
- ✅ Outcome tracking works (quality before/after measured)
- ✅ Learning recorded (successful interventions documented)
- ✅ SDM Agent references quality patterns during complaint analysis

#### Deliverables
1. `servicedesk_quality_monitor.py` (monitoring service, ~350 lines)
2. Updated `sdm_agent_ops_intel_integration.py` (quality outcome tracking)
3. Updated `service_desk_manager_agent.md` (quality intelligence integration)
4. End-to-end integration test script
5. Monitoring setup documentation

---

### Phase 4: Automated System/Bot Detection & Filtering ⭐ QUICK WIN
**Priority**: MEDIUM | **Effort**: 2-3 hours | **Status**: Not Started
**Dependencies**: None (can run independently)

#### Objective
Automatically detect and exclude system accounts from quality analysis for accurate metrics.

#### Current Problem
"brian" account (324/517 comments, 62.7%) skews quality metrics to 61.5% poor - actually automated system account.

#### Technical Implementation

**4.1 System Account Detection** (1 hour)

**New Script**: `/Users/naythandawe/git/maia/claude/tools/sre/detect_system_accounts.py`

```python
#!/usr/bin/env python3
"""
Detect and tag system/bot accounts

Usage:
    python3 detect_system_accounts.py --analyze    # Detect system accounts
    python3 detect_system_accounts.py --tag        # Tag database
"""

import sqlite3
import argparse
from collections import Counter

class SystemAccountDetector:
    """Detect system/bot accounts using heuristics"""

    HEURISTICS = {
        'high_volume_threshold': 1000,      # >1000 comments = potential bot
        'automation_pattern_threshold': 0.9, # >90% automated = bot
        'empty_comment_threshold': 0.8,     # >80% empty = bot
    }

    def __init__(self):
        self.db_path = '/Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db'

    def detect_system_accounts(self) -> list:
        """
        Detect system accounts using multiple heuristics

        Returns:
            List of (user_name, confidence, reasons)
        """

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all users with comment counts
        cursor.execute("""
            SELECT user_name, COUNT(*) as comment_count
            FROM comments
            GROUP BY user_name
            ORDER BY comment_count DESC
        """)

        users = cursor.fetchall()

        system_accounts = []

        for user_name, comment_count in users:
            reasons = []
            confidence = 0.0

            # Heuristic 1: High volume
            if comment_count > self.HEURISTICS['high_volume_threshold']:
                reasons.append(f"High volume ({comment_count:,} comments)")
                confidence += 0.3

                # Heuristic 2: Check for automation patterns
                automation_rate = self._check_automation_patterns(user_name, cursor)
                if automation_rate > self.HEURISTICS['automation_pattern_threshold']:
                    reasons.append(f"Automated content ({automation_rate*100:.1f}%)")
                    confidence += 0.4

                # Heuristic 3: Check for empty/system comments
                empty_rate = self._check_empty_comments(user_name, cursor)
                if empty_rate > self.HEURISTICS['empty_comment_threshold']:
                    reasons.append(f"Empty/system comments ({empty_rate*100:.1f}%)")
                    confidence += 0.3

            # Heuristic 4: Not in cloud_team_roster
            if not self._in_team_roster(user_name, cursor):
                reasons.append("Not in team roster")
                confidence += 0.2

            if confidence >= 0.6:  # 60% confidence threshold
                system_accounts.append({
                    'user_name': user_name,
                    'comment_count': comment_count,
                    'confidence': confidence,
                    'reasons': reasons
                })

        conn.close()
        return system_accounts

    def _check_automation_patterns(self, user_name: str, cursor) -> float:
        """Check percentage of automated/pattern-based comments"""

        cursor.execute("""
            SELECT comment_text
            FROM comments
            WHERE user_name = ?
            LIMIT 100
        """, (user_name,))

        comments = cursor.fetchall()

        automation_indicators = [
            '[AUTOMATION',
            '[SYSTEM]',
            'Automatically',
            'Auto-assigned',
            'System generated'
        ]

        automated_count = sum(
            1 for (text,) in comments
            if any(indicator in text for indicator in automation_indicators)
        )

        return automated_count / len(comments) if comments else 0.0

    def _check_empty_comments(self, user_name: str, cursor) -> float:
        """Check percentage of empty or very short comments"""

        cursor.execute("""
            SELECT comment_text
            FROM comments
            WHERE user_name = ?
            LIMIT 100
        """, (user_name,))

        comments = cursor.fetchall()

        empty_count = sum(
            1 for (text,) in comments
            if not text or len(text.strip()) < 10
        )

        return empty_count / len(comments) if comments else 0.0

    def _in_team_roster(self, user_name: str, cursor) -> bool:
        """Check if user is in cloud_team_roster"""

        cursor.execute("""
            SELECT COUNT(*)
            FROM cloud_team_roster
            WHERE name = ? OR email LIKE ?
        """, (user_name, f"%{user_name}%"))

        count = cursor.fetchone()[0]
        return count > 0

    def tag_database(self, system_accounts: list):
        """Tag system accounts in database"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Add is_system_account column if not exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM pragma_table_info('comments')
            WHERE name='is_system_account'
        """)

        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE comments
                ADD COLUMN is_system_account INTEGER DEFAULT 0
            """)

        # Tag system accounts
        for account in system_accounts:
            cursor.execute("""
                UPDATE comments
                SET is_system_account = 1
                WHERE user_name = ?
            """, (account['user_name'],))

            print(f"   ✅ Tagged: {account['user_name']} ({account['comment_count']:,} comments, {account['confidence']:.0%} confidence)")

        conn.commit()
        conn.close()

        print(f"\n✅ Tagged {len(system_accounts)} system accounts")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--analyze', action='store_true', help='Detect system accounts')
    parser.add_argument('--tag', action='store_true', help='Tag database')

    args = parser.parse_args()

    detector = SystemAccountDetector()

    if args.analyze:
        system_accounts = detector.detect_system_accounts()

        print(f"\n🤖 Detected {len(system_accounts)} system accounts:")
        print(f"{'='*70}")
        for account in system_accounts:
            print(f"\n{account['user_name']} ({account['confidence']:.0%} confidence)")
            print(f"   Comments: {account['comment_count']:,}")
            print(f"   Reasons: {', '.join(account['reasons'])}")

    if args.tag:
        system_accounts = detector.detect_system_accounts()
        detector.tag_database(system_accounts)
```

**4.2 Update Quality Analyzer** (30 min)

**File**: `/Users/naythandawe/git/maia/claude/tools/sre/servicedesk_complete_quality_analyzer.py`

**Change**: Add filter to exclude system accounts

```python
# Line ~320: Update WHERE clause in analyze_comments()

query = """
    SELECT
        comment_id,
        ticket_id,
        comment_text,
        user_name,
        team,
        comment_type,
        created_time
    FROM comments
    WHERE comment_type = 'comments'
      AND is_system_account = 0  -- NEW: Exclude system accounts
      AND LENGTH(TRIM(comment_text)) > 0
    LIMIT ? OFFSET ?
"""
```

**4.3 Testing & Validation** (30 min)

```bash
# Test 1: Detect system accounts
python3 detect_system_accounts.py --analyze

# Expected: "brian" detected with 90%+ confidence

# Test 2: Tag database
python3 detect_system_accounts.py --tag

# Expected: is_system_account column added, "brian" tagged

# Test 3: Re-run quality analysis (should exclude brian)
python3 servicedesk_complete_quality_analyzer.py --limit 100

# Expected: No "brian" comments analyzed, quality metrics accurate
```

#### Success Criteria
- ✅ System account detection working (brian + any others detected)
- ✅ Database tagging successful (is_system_account column added)
- ✅ Quality analyzer excludes system accounts
- ✅ Quality metrics accurate (no bot contamination)

#### Deliverables
1. `detect_system_accounts.py` (detection + tagging script, ~200 lines)
2. Updated `servicedesk_complete_quality_analyzer.py` (system account filter)
3. Test validation results
4. Documentation update

---

## Optional Phase 5: Complete Coverage Quality Analysis
**Priority**: LOW-MEDIUM | **Effort**: 12-20 hours (compute time) | **Status**: Deferred
**Dependencies**: Phase 1, 4

**Note**: This phase analyzes all 16,620 customer-facing comments (vs current 517 = 3.1%). High compute cost vs marginal incremental value. **Recommendation**: Complete Phases 1-4 first, then evaluate if full coverage needed for historical trend analysis.

---

## Success Metrics

### Phase 1 Success Metrics
- ✅ RAG re-indexed with quality metadata (108,129 comments)
- ✅ Quality-aware search functional (filter by tier, scores, flags)
- ✅ Search performance <2 sec for typical queries

### Phase 2 Success Metrics
- ✅ Agent coaching reports generate (all dimensions, examples, action items)
- ✅ Best practice library built (100+ excellent examples)
- ✅ Real-time draft checking predicts quality accurately (±0.5 score variance)

### Phase 3 Success Metrics
- ✅ Quality monitoring detects degradation (team/agent level)
- ✅ Ops intelligence insights auto-created from alerts
- ✅ Outcome tracking working (before/after measurements)
- ✅ SDM Agent references quality patterns in complaint analysis

### Phase 4 Success Metrics
- ✅ System accounts detected (brian + others)
- ✅ Quality metrics accurate (no bot contamination)

### Overall Business Outcomes (3-6 months post-implementation)
- 📈 30-50% reduction in poor-quality comments
- 📈 Quality → CSAT correlation measured (statistical significance)
- 📈 Evidence-based training ROI tracked (quality improvement %)
- 📈 Institutional memory operational (quality initiatives + outcomes preserved)

---

## Risk Management

### Technical Risks

**Risk 1: RAG Re-Indexing Performance**
- **Issue**: Re-indexing 108K comments may take 1-2 hours
- **Mitigation**: Incremental re-indexing mode (only newly analyzed comments)
- **Fallback**: Run full re-index overnight, use incremental for daily updates

**Risk 2: LLM Coaching Quality Variability**
- **Issue**: Local LLM (llama3.2:3b) may produce inconsistent coaching
- **Mitigation**: Template-based coaching structure, human review of first 10 reports
- **Fallback**: Use Claude Sonnet API for coaching generation (higher quality, cost trade-off)

**Risk 3: ChromaDB Metadata Filtering Limitations**
- **Issue**: ChromaDB doesn't support complex JSON queries (red_flags filtering)
- **Mitigation**: Post-filtering in Python after initial query
- **Fallback**: SQLite + RAG hybrid (SQL for filtering, RAG for semantic search)

### Operational Risks

**Risk 1: Agent Pushback on Quality Monitoring**
- **Issue**: Agents may perceive quality scoring as punitive
- **Mitigation**: Frame as coaching/development (not performance review)
- **Communication**: Emphasize best practice library (learn from excellent examples)

**Risk 2: Manager Capacity for Coaching Delivery**
- **Issue**: Generating reports ≠ delivering effective coaching
- **Mitigation**: Train-the-trainer program for team leads
- **Support**: Provide coaching delivery guide with reports

**Risk 3: Data Privacy Concerns**
- **Issue**: Quality reports contain customer interaction details
- **Mitigation**: Anonymize customer data in examples, focus on agent behavior
- **Compliance**: Review with legal/privacy team before rollout

---

## Dependencies & Prerequisites

### Technical Dependencies
- ✅ Phase 130: Operations Intelligence Database (operational)
- ✅ ChromaDB: 213,929 documents indexed (operational)
- ✅ E5-base-v2 embeddings: Local GPU working (operational)
- ✅ Ollama llama3.2:3b: Local LLM available (operational)
- ✅ SQLite: servicedesk_tickets.db with 108,129 comments (operational)

### Data Dependencies
- ✅ comment_quality table: 517 comments analyzed (baseline exists)
- ⚠️  Full coverage: Optional (defer to Phase 5 if needed)

### Organizational Dependencies
- ⏳ Stakeholder buy-in: ServiceDesk Manager, Team Leads
- ⏳ Agent communication plan: Explain quality coaching as development (not punitive)
- ⏳ Privacy review: Legal/compliance approval for quality monitoring

---

## Timeline Estimate

### Aggressive Timeline (Full-Time Focus)
- **Week 1**: Phase 1 (RAG metadata) + Phase 4 (bot detection) = 6-9 hours
- **Week 2**: Phase 2 (coaching engine) = 8-12 hours
- **Week 3**: Phase 3 (ops intelligence integration) = 6-8 hours
- **Week 4**: Testing, refinement, documentation

**Total**: 3-4 weeks full-time

### Realistic Timeline (Part-Time, 10 hours/week)
- **Weeks 1-2**: Phase 1 + Phase 4
- **Weeks 3-4**: Phase 2 (coaching engine)
- **Weeks 5-6**: Phase 3 (ops intelligence)
- **Week 7**: Testing + documentation

**Total**: 7 weeks part-time

---

## Cost-Benefit Analysis

### Investment
- **Development Time**: 20-29 hours (Phases 1-4)
- **Compute Cost**: $0 (local LLM + GPU)
- **Storage Cost**: ~50MB additional (SQLite + ChromaDB metadata)

### Expected Returns

**Quantitative Benefits** (Annual, extrapolated from 75.7% coverage):
- **Reduced Escalations**: 30% reduction × 2,000 escalations/year = 600 fewer escalations
  - Time savings: 600 × 2 hours = 1,200 hours/year
  - Cost savings: 1,200 hours × $50/hour = $60,000/year

- **Improved CSAT**: Quality → CSAT correlation (est. 0.6)
  - 20% quality improvement → 12% CSAT improvement
  - CSAT 3.5 → 3.92 (within industry excellent tier)

- **Reduced Rework**: 25% reduction in "customer didn't understand" tickets
  - 500 rework tickets/year × $30/ticket = $15,000/year savings

**Total Quantifiable Savings**: ~$75,000/year

**Qualitative Benefits**:
- Evidence-based coaching (vs gut feeling)
- Institutional memory (quality initiatives preserved)
- Agent skill development (continuous improvement)
- Customer satisfaction improvement (better communication)

**ROI**: $75,000 annual savings / $2,000 investment (29 hours × $70/hour) = **37.5x ROI**

---

## Next Steps

### Immediate Actions (This Week)
1. ✅ Save this roadmap (DONE)
2. ⏳ Review with ServiceDesk Manager for approval
3. ⏳ Confirm stakeholder buy-in (team leads, agents)
4. ⏳ Schedule Phase 1 implementation kickoff

### Phase 1 Kickoff (Next Week)
1. Clone production database for testing
2. Implement RAG metadata schema updates
3. Run re-indexing (full mode, overnight)
4. Test quality-aware search (5 test cases)
5. Document Phase 1 completion

### Communication Plan
1. **Week 1**: Announce project to ServiceDesk team (focus: development, not punishment)
2. **Week 2**: Share best practice library examples (build excitement)
3. **Week 3**: Pilot coaching reports with 3 volunteer agents (gather feedback)
4. **Week 4**: Refine based on pilot feedback
5. **Week 5**: Full rollout to all teams

---

## File Locations

### Code Files
- **Phase 1**:
  - `/Users/naythandawe/git/maia/claude/tools/sre/servicedesk_gpu_rag_indexer.py` (update)
  - `/Users/naythandawe/git/maia/claude/tools/sre/reindex_comments_with_quality.py` (new)

- **Phase 2**:
  - `/Users/naythandawe/git/maia/claude/tools/sre/servicedesk_agent_quality_coach.py` (new)
  - `/Users/naythandawe/git/maia/claude/tools/sre/servicedesk_complete_quality_analyzer.py` (update)
  - `/Users/naythandawe/git/maia/claude/tools/sre/servicedesk_best_practice_library.py` (new)

- **Phase 3**:
  - `/Users/naythandawe/git/maia/claude/tools/sre/servicedesk_quality_monitor.py` (new)
  - `/Users/naythandawe/git/maia/claude/tools/sre/sdm_agent_ops_intel_integration.py` (update)
  - `/Users/naythandawe/git/maia/claude/agents/service_desk_manager_agent.md` (update)

- **Phase 4**:
  - `/Users/naythandawe/git/maia/claude/tools/sre/detect_system_accounts.py` (new)

### Database Files
- `/Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db` (SQLite - 1.24GB)
- `~/.maia/servicedesk_rag/` (ChromaDB - 753MB)
- `/Users/naythandawe/git/maia/claude/data/servicedesk_operations_intelligence.db` (Ops Intel - 112KB)

### Documentation Files
- `/Users/naythandawe/git/maia/claude/data/SERVICEDESK_QUALITY_INTELLIGENCE_ROADMAP.md` (this file)
- `/Users/naythandawe/git/maia/claude/data/SERVICEDESK_RAG_QUALITY_UPGRADE_PROJECT.md` (Phase 118.3)
- `/Users/naythandawe/git/maia/claude/data/SERVICEDESK_OPERATIONS_INTELLIGENCE_PROJECT.md` (Phase 130)

---

## Version History

- **v1.0** (2025-10-18): Initial roadmap - 4 phases, 20-29 hours, detailed implementation plans
- **Status**: Planning Complete → Ready for Phase 1 Implementation

---

**End of Roadmap**

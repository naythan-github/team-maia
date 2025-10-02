#!/usr/bin/env python3
"""
Smart CV Experience Selector
AI-powered experience selection and scoring for optimal CV creation.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ExperienceScore:
    """Scoring model for experience relevance"""
    exp_id: str
    employer: str
    title: str
    relevance_score: float
    keyword_matches: List[str]
    outcome_strength: float
    seniority_alignment: float
    recency_factor: float
    confidence: str

class SmartCVSelector:
    """Intelligent experience selection for CV optimization"""

    def __init__(self, career_data_dir: str = "get_path_manager().get_path('git_root') / 'claude' / 'data' / 'career'"):
        self.career_data_dir = Path(career_data_dir)
        self.experiences = {}
        self.job_requirements = {}
        self.load_career_databases()

    def load_career_databases(self):
        """Load all experience databases"""
        database_files = [
            "experiences_zetta.json",
            "experiences_telstra.json",
            "experiences_oneadvanced.json",
            "experiences_viadex.json",
            "experiences_halsion.json"
        ]

        for db_file in database_files:
            db_path = self.career_data_dir / db_file
            if db_path.exists():
                try:
                    with open(db_path, 'r') as f:
                        data = json.load(f)
                        employer = db_file.replace('experiences_', '').replace('.json', '')
                        experiences = data.get('experiences', [])
                        if experiences:
                            self.experiences[employer] = experiences
                            print(f"✅ Loaded {len(experiences)} experiences from {employer}")
                        else:
                            print(f"⚠️ No experiences found in {db_file}")
                except Exception as e:
                    print(f"❌ Error loading {db_file}: {e}")
            else:
                print(f"❌ File not found: {db_path}")

        total_experiences = sum(len(exps) for exps in self.experiences.values())
        print(f"📊 Total experiences loaded: {total_experiences} from {len(self.experiences)} employers")

    def analyze_job_description(self, job_text: str) -> Dict[str, Any]:
        """Extract key requirements from job description"""

        # Core competency patterns
        leadership_patterns = [
            r'lead(ing|ership)?', r'manage(r|ment)', r'direct(or|ing)?',
            r'stakeholder', r'team', r'oversight', r'governance'
        ]

        technical_patterns = [
            r'azure', r'cloud', r'technical', r'architecture', r'infrastructure',
            r'digital', r'transformation', r'solution', r'system'
        ]

        business_patterns = [
            r'business', r'strategy', r'commercial', r'outcome', r'value',
            r'revenue', r'cost', r'budget', r'roi', r'benefit'
        ]

        stakeholder_patterns = [
            r'stakeholder', r'executive', r'c-suite', r'board', r'client',
            r'customer', r'relationship', r'engagement', r'communication'
        ]

        job_lower = job_text.lower()

        requirements = {
            'leadership': self._count_pattern_matches(job_lower, leadership_patterns),
            'technical': self._count_pattern_matches(job_lower, technical_patterns),
            'business': self._count_pattern_matches(job_lower, business_patterns),
            'stakeholder': self._count_pattern_matches(job_lower, stakeholder_patterns)
        }

        # Extract specific keywords for matching
        keywords = self._extract_keywords(job_text)

        # Determine role seniority
        seniority = self._determine_seniority(job_text)

        return {
            'requirements': requirements,
            'keywords': keywords,
            'seniority': seniority,
            'total_weight': sum(requirements.values())
        }

    def score_experience(self, experience: Dict, job_analysis: Dict) -> ExperienceScore:
        """Score an experience against job requirements"""

        exp_text = f"{experience.get('title', '')} {experience.get('description', '')}".lower()
        job_keywords = job_analysis['keywords']
        job_requirements = job_analysis['requirements']

        # Keyword matching score (0.4 weight)
        keyword_matches = []
        keyword_score = 0
        for keyword in job_keywords:
            if keyword.lower() in exp_text:
                keyword_matches.append(keyword)
                keyword_score += 1
        keyword_score = min(keyword_score / len(job_keywords), 1.0) if job_keywords else 0

        # Outcome strength score (0.3 weight)
        outcome_indicators = ['$', '%', 'increased', 'reduced', 'improved', 'delivered', 'achieved']
        outcome_score = sum(1 for indicator in outcome_indicators if indicator in exp_text) / len(outcome_indicators)
        outcome_score = min(outcome_score, 1.0)

        # Seniority alignment score (0.2 weight)
        exp_seniority = self._assess_experience_seniority(experience)
        target_seniority = job_analysis['seniority']
        seniority_score = 1.0 if exp_seniority >= target_seniority else 0.7

        # Recency factor (0.1 weight)
        recency_score = self._calculate_recency_score(experience)

        # Weighted total score
        total_score = (
            keyword_score * 0.4 +
            outcome_score * 0.3 +
            seniority_score * 0.2 +
            recency_score * 0.1
        )

        # Confidence level
        confidence = "High" if total_score >= 0.7 else "Medium" if total_score >= 0.5 else "Low"

        return ExperienceScore(
            exp_id=experience.get('exp_id', 'unknown'),
            employer=experience.get('employer', 'unknown'),
            title=experience.get('title', 'untitled'),
            relevance_score=total_score,
            keyword_matches=keyword_matches,
            outcome_strength=outcome_score,
            seniority_alignment=seniority_score,
            recency_factor=recency_score,
            confidence=confidence
        )

    def select_optimal_experiences(self, job_text: str, target_count: int = 30) -> Dict[str, Any]:
        """Select optimal experiences for CV based on job requirements"""

        # Analyze job requirements
        job_analysis = self.analyze_job_description(job_text)

        # Score all experiences
        scored_experiences = []
        for employer, experiences in self.experiences.items():
            for exp in experiences:
                exp['employer'] = employer  # Add employer context
                score = self.score_experience(exp, job_analysis)
                scored_experiences.append((score, exp))

        # Sort by relevance score
        scored_experiences.sort(key=lambda x: x[0].relevance_score, reverse=True)

        # Select top experiences with diversity
        selected = self._diversified_selection(scored_experiences, target_count)

        return {
            'job_analysis': job_analysis,
            'selected_experiences': selected,
            'selection_stats': self._generate_selection_stats(selected),
            'recommendations': self._generate_recommendations(selected, job_analysis)
        }

    def _count_pattern_matches(self, text: str, patterns: List[str]) -> int:
        """Count pattern matches in text"""
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return count

    def _extract_keywords(self, job_text: str) -> List[str]:
        """Extract key terms from job description"""
        # Simple keyword extraction - could be enhanced with NLP
        words = re.findall(r'\b[a-zA-Z]{4,}\b', job_text.lower())
        # Filter common words
        common_words = {'with', 'have', 'will', 'work', 'team', 'role', 'this', 'that', 'they', 'from', 'been'}
        keywords = [w for w in set(words) if w not in common_words]
        return keywords[:20]  # Limit to top 20 keywords

    def _determine_seniority(self, job_text: str) -> int:
        """Determine job seniority level (1-5 scale)"""
        job_lower = job_text.lower()
        if any(term in job_lower for term in ['director', 'head of', 'chief', 'vp']):
            return 5
        elif any(term in job_lower for term in ['principal', 'senior manager', 'lead']):
            return 4
        elif any(term in job_lower for term in ['senior', 'manager']):
            return 3
        elif any(term in job_lower for term in ['specialist', 'analyst']):
            return 2
        else:
            return 1

    def _assess_experience_seniority(self, experience: Dict) -> int:
        """Assess seniority level of experience"""
        title = experience.get('title', '').lower()
        if any(term in title for term in ['director', 'head', 'chief', 'vp']):
            return 5
        elif any(term in title for term in ['principal', 'senior manager', 'lead']):
            return 4
        elif any(term in title for term in ['senior', 'manager']):
            return 3
        else:
            return 2

    def _calculate_recency_score(self, experience: Dict) -> float:
        """Calculate recency score based on experience timeline"""
        # Simple implementation - could be enhanced with actual date parsing
        employer = experience.get('employer', '').lower()
        if employer == 'zetta':  # Current employer
            return 1.0
        elif employer == 'telstra':  # Recent employer
            return 0.8
        else:  # Older employers
            return 0.6

    def _diversified_selection(self, scored_experiences: List[Tuple], target_count: int) -> List[Dict]:
        """Select experiences with employer diversity"""
        selected = []
        employer_counts = {}

        for score, exp in scored_experiences:
            if len(selected) >= target_count:
                break

            employer = exp.get('employer', 'unknown')
            current_count = employer_counts.get(employer, 0)

            # Limit per employer to ensure diversity
            max_per_employer = max(2, target_count // 5)  # At least 2, up to 1/5 of total

            if current_count < max_per_employer or score.relevance_score > 0.8:
                selected.append({
                    'experience': exp,
                    'score': score,
                    'selection_reason': f"Score: {score.relevance_score:.2f}, Keywords: {len(score.keyword_matches)}"
                })
                employer_counts[employer] = current_count + 1

        return selected

    def _generate_selection_stats(self, selected: List[Dict]) -> Dict[str, Any]:
        """Generate statistics about selected experiences"""
        if not selected:
            return {
                'total_selected': 0,
                'average_score': 0.0,
                'score_range': [0, 0],
                'employer_distribution': {},
                'high_confidence': 0
            }

        scores = [s['score'].relevance_score for s in selected]
        employers = [s['experience']['employer'] for s in selected]

        return {
            'total_selected': len(selected),
            'average_score': sum(scores) / len(scores),
            'score_range': [min(scores), max(scores)],
            'employer_distribution': {emp: employers.count(emp) for emp in set(employers)},
            'high_confidence': len([s for s in selected if s['score'].confidence == 'High'])
        }

    def _generate_recommendations(self, selected: List[Dict], job_analysis: Dict) -> List[str]:
        """Generate recommendations for CV optimization"""
        recommendations = []

        if not selected:
            recommendations.append("No experiences selected - check database connection and job analysis")
            return recommendations

        if len(selected) < 25:
            recommendations.append("Consider expanding experience selection for fuller CV")

        high_scores = [s for s in selected if s['score'].relevance_score > 0.7]
        if len(high_scores) < 10:
            recommendations.append("Low relevance scores - consider broader keyword matching")

        keyword_coverage = sum(len(s['score'].keyword_matches) for s in selected) / len(selected)
        if keyword_coverage < 3:
            recommendations.append("Increase keyword alignment with job description")

        return recommendations

def main():
    """Test the smart selector"""
    selector = SmartCVSelector()

    # Test with sample job description
    sample_job = """
    Senior Business Relationship Manager required for technology portfolio management.
    Lead stakeholder engagement across enterprise clients. Manage Azure cloud transformation
    initiatives. Drive business value delivery through strategic technology alignment.
    """

    results = selector.select_optimal_experiences(sample_job, target_count=25)

    print("🎯 Smart CV Selection Results")
    print(f"Job Analysis: {results['job_analysis']['requirements']}")
    print(f"Selected: {len(results['selected_experiences'])} experiences")
    print(f"Average Score: {results['selection_stats']['average_score']:.3f}")
    print(f"High Confidence: {results['selection_stats']['high_confidence']}")

    # Show top 5 selections
    print("\n🏆 Top 5 Selections:")
    for i, selection in enumerate(results['selected_experiences'][:5]):
        score = selection['score']
        exp = selection['experience']
        print(f"{i+1}. {exp['employer']}: {score.relevance_score:.3f} - {score.confidence}")

if __name__ == "__main__":
    main()

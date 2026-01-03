#!/usr/bin/env python3
"""
Enhanced Profile-Based Job Scorer - Phase 2 Implementation
Integrates ATS qualification screening + Naythan's USPs, experience patterns, and career trajectory
"""

import json
import re
import sys
import os
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add path for ATS qualification matcher
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from ats_qualification_matcher import ATSQualificationMatcher
except ImportError:
    print("⚠️ ATS Qualification Matcher not available - using basic scoring only")
    ATSQualificationMatcher = None

@dataclass
class USPMatcher:
    """Represents a Unique Selling Point with matching logic"""
    usp_id: str
    title: str
    description: str
    keywords: List[str]
    applicable_roles: List[str]
    weight: float

class EnhancedProfileScorer:
    def __init__(self):
        """Initialize with Naythan's profile data, USPs, and ATS qualification matcher"""
        self.profile = self._load_profile_data()
        self.usps = self._load_usp_data()
        self.company_tiers = self._load_company_tiers()
        self.role_preferences = self._load_role_preferences()

        # Initialize ATS qualification matcher
        if ATSQualificationMatcher:
            self.ats_matcher = ATSQualificationMatcher()
        else:
            self.ats_matcher = None

    def _load_profile_data(self) -> Dict:
        """Load core profile information"""
        return {
            'current_role': 'Senior Client Principal',
            'experience_level': 'Senior',
            'specializations': [
                'business relationship management',
                'portfolio governance',
                'cloud infrastructure',
                'azure specialization',
                'enterprise client management',
                'crisis management',
                'stakeholder management',
                'digital transformation'
            ],
            'industries': ['mining', 'energy', 'government', 'finance', 'aviation'],
            'location': 'Perth, Australia',
            'salary_min': 150000,
            'salary_target': 180000,
            'career_goals': {
                'short_term': ['Director', 'General Manager'],
                'long_term': ['CTO', 'C-suite']
            }
        }

    def _load_usp_data(self) -> List[USPMatcher]:
        """Load and structure USP data for matching"""
        return [
            USPMatcher(
                usp_id="USP001",
                title="The Crisis Navigator",
                description="Thrives when others panic, creating structure from chaos",
                keywords=[
                    'crisis', 'emergency', 'outage', 'incident', 'disaster', 'urgent',
                    'escalation', 'critical', 'fire-fighting', 'rapid response',
                    'pressure', 'chaos', 'structure', 'coordination'
                ],
                applicable_roles=[
                    'incident manager', 'crisis manager', 'emergency response',
                    'service delivery', 'operations manager', 'technical lead'
                ],
                weight=8.5  # High weight - unique differentiator
            ),
            USPMatcher(
                usp_id="USP002",
                title="The Complexity Untangler",
                description="Transforms complex situations into actionable paths",
                keywords=[
                    'complex', 'transformation', 'integration', 'multi-stakeholder',
                    'enterprise', 'strategic', 'roadmap', 'governance', 'framework',
                    'methodology', 'process improvement', 'optimization'
                ],
                applicable_roles=[
                    'business relationship manager', 'program manager', 'solution architect',
                    'transformation lead', 'strategy manager', 'enterprise architect'
                ],
                weight=9.0  # Highest weight - core strength
            ),
            USPMatcher(
                usp_id="USP003",
                title="The Fresh Perspective Catalyst",
                description="Brings outsider advantage for rapid transformation",
                keywords=[
                    'change management', 'innovation', 'transformation', 'improvement',
                    'catalyst', 'modernization', 'digital', 'agile', 'fresh perspective',
                    'organizational change', 'culture change', 'process innovation'
                ],
                applicable_roles=[
                    'change manager', 'transformation lead', 'innovation manager',
                    'digital transformation', 'organizational development'
                ],
                weight=7.5
            ),
            USPMatcher(
                usp_id="USP004",
                title="The Trust Bridge",
                description="Balances technical depth with commercial acumen",
                keywords=[
                    'stakeholder', 'c-suite', 'executive', 'commercial', 'business value',
                    'technical sales', 'solution design', 'customer facing',
                    'relationship management', 'account management', 'consulting'
                ],
                applicable_roles=[
                    'business relationship manager', 'account manager', 'solution architect',
                    'customer success', 'technical sales', 'consulting'
                ],
                weight=8.0
            )
        ]

    def _load_company_tiers(self) -> Dict:
        """Load company preference tiers with scoring"""
        return {
            'tier_1_premium': {
                'score': 10,
                'companies': ['PwC', 'Deloitte', 'KPMG', 'EY', 'McKinsey', 'BCG'],
                'patterns': ['big 4', 'big four', 'tier 1', 'premium consulting']
            },
            'tier_2_enterprise': {
                'score': 8,
                'companies': ['BHP', 'Woodside', 'Rio Tinto', 'Fortescue', 'Microsoft', 'Amazon'],
                'patterns': ['mining giant', 'energy major', 'fortune 500', 'asx 100']
            },
            'tier_3_government': {
                'score': 6,
                'companies': ['WA Government', 'Department of', 'RAC', 'City of Perth', 'DFES'],
                'patterns': ['government', 'public sector', 'department', 'council', 'authority']
            },
            'tier_4_mid_enterprise': {
                'score': 5,
                'companies': ['Telstra', 'Zetta', 'One Advanced', 'Halsion'],
                'patterns': ['established', 'mid-tier', 'regional']
            }
        }

    def _load_role_preferences(self) -> Dict:
        """Load role title preferences with scoring"""
        return {
            'perfect_match': {
                'score': 10,
                'titles': [
                    'senior business relationship manager', 'business relationship manager',
                    'senior brm', 'brm', 'senior client partner', 'client partner'
                ]
            },
            'strong_match': {
                'score': 8,
                'titles': [
                    'service delivery manager', 'customer success manager',
                    'account manager', 'principal consultant', 'solution architect'
                ]
            },
            'good_match': {
                'score': 6,
                'titles': [
                    'project manager', 'program manager', 'transformation manager',
                    'change manager', 'operations manager'
                ]
            },
            'potential_match': {
                'score': 4,
                'titles': [
                    'senior manager', 'principal', 'director', 'head of',
                    'strategy manager', 'portfolio manager'
                ]
            }
        }

    def score_job_enhanced(self, job: Dict) -> Tuple[float, Dict]:
        """Enhanced scoring using ATS qualification screening + profile data and USPs"""

        # Extract job data (handle None values)
        title = (job.get('title') or '').lower()
        company = (job.get('company') or '').lower()
        location = (job.get('location') or '').lower()
        salary_str = (job.get('salary') or '').lower()
        description = (job.get('description') or '').lower()

        # Combine text for analysis
        job_text = f"{title} {company} {description}".lower()

        # STAGE 1: ATS Qualification Screening (NEW)
        qualification_result = None
        if self.ats_matcher:
            try:
                salary_text = job.get('salary', job.get('salary_text', ''))
                # Always run salary check, only skip description-based checks if no description
                if description == 'description not available':
                    # Run salary-only screening for jobs without descriptions
                    qualification_result = self.ats_matcher.match_qualifications('', salary_text)
                else:
                    # Full ATS screening including description patterns
                    qualification_result = self.ats_matcher.match_qualifications(description, salary_text)

                # If fails ATS screening, return low score immediately
                if not qualification_result.passes_screen:
                    return qualification_result.qualification_score, {
                        'ats_screening': {
                            'passed': False,
                            'qualification_score': qualification_result.qualification_score,
                            'blockers': qualification_result.blockers_found,
                            'summary': qualification_result.qualification_summary
                        },
                        'filtered_out': True,
                        'reason': 'Failed ATS qualification screening',
                        'title': title
                    }
            except Exception as e:
                print(f"ATS screening error for {title}: {str(e)}")

        # STAGE 2: Traditional Enhanced Scoring (existing logic)
        # Apply PM exception logic - filter out generic Project Manager roles
        if self._is_generic_project_manager(title, description):
            return 0.0, {
                'filtered_out': True,
                'reason': 'Generic Project Manager role - lacks BRM/strategic components',
                'title': title
            }

        # Initialize scoring components
        scoring_breakdown = {
            'base_score': 5.0,
            'usp_matches': [],
            'company_tier_bonus': 0,
            'role_match_bonus': 0,
            'salary_bonus': 0,
            'location_bonus': 0,
            'experience_alignment': 0,
            'red_flags': [],
            'ats_screening': {
                'passed': qualification_result.passes_screen if qualification_result else True,
                'qualification_score': qualification_result.qualification_score if qualification_result else 10.0,
                'blockers': qualification_result.blockers_found if qualification_result else [],
                'soft_mismatches': qualification_result.soft_mismatches if qualification_result else [],
                'summary': qualification_result.qualification_summary if qualification_result else 'No ATS screening performed'
            },
            'final_score': 0
        }

        current_score = scoring_breakdown['base_score']

        # 1. USP Matching (Up to +15 points total)
        usp_bonus = 0
        for usp in self.usps:
            match_strength = self._calculate_usp_match(job_text, usp)
            if match_strength > 0:
                bonus = (match_strength * usp.weight) / 100  # Scale to reasonable bonus
                usp_bonus += bonus
                scoring_breakdown['usp_matches'].append({
                    'usp': usp.title,
                    'strength': match_strength,
                    'bonus': bonus,
                    'keywords_found': self._find_matching_keywords(job_text, usp.keywords)
                })

        current_score += min(usp_bonus, 4.0)  # Cap USP bonus at +4.0

        # 2. Company Tier Scoring (Up to +3.0 points)
        company_bonus = self._score_company_tier(company)
        scoring_breakdown['company_tier_bonus'] = company_bonus
        current_score += company_bonus

        # 3. Role Title Match (Up to +2.5 points)
        role_bonus = self._score_role_match(title)
        scoring_breakdown['role_match_bonus'] = role_bonus
        current_score += role_bonus

        # 4. Salary Alignment (Up to +1.5 points)
        salary_bonus = self._score_salary(salary_str)
        scoring_breakdown['salary_bonus'] = salary_bonus
        current_score += salary_bonus

        # 5. Location Preference (+0.5 points)
        if 'perth' in location or 'remote' in location or 'hybrid' in location:
            scoring_breakdown['location_bonus'] = 0.5
            current_score += 0.5

        # 6. Experience Level Alignment (+/- 1.0 points)
        exp_bonus = self._score_experience_alignment(job_text)
        scoring_breakdown['experience_alignment'] = exp_bonus
        current_score += exp_bonus

        # 7. Red Flag Detection (-0.5 to -5.0 points)
        red_flag_penalty = self._detect_red_flags(job_text)
        scoring_breakdown['red_flags'] = red_flag_penalty['flags']
        current_score += red_flag_penalty['penalty']

        # Final score capping and rounding
        final_score = max(0.0, min(10.0, current_score))
        scoring_breakdown['final_score'] = round(final_score, 1)

        return final_score, scoring_breakdown

    def _calculate_usp_match(self, job_text: str, usp: USPMatcher) -> float:
        """Calculate how well a job matches a specific USP (0-100)"""
        keyword_matches = 0
        role_matches = 0

        # Check keyword matches
        for keyword in usp.keywords:
            if keyword in job_text:
                keyword_matches += 1

        # Check role matches
        for role in usp.applicable_roles:
            if role in job_text:
                role_matches += 2  # Role matches worth more

        # Calculate match strength
        total_possible = len(usp.keywords) + (len(usp.applicable_roles) * 2)
        actual_matches = keyword_matches + role_matches

        match_percentage = (actual_matches / total_possible) * 100 if total_possible > 0 else 0

        return min(match_percentage, 100)

    def _find_matching_keywords(self, job_text: str, keywords: List[str]) -> List[str]:
        """Find which keywords actually matched"""
        return [kw for kw in keywords if kw in job_text]

    def _score_company_tier(self, company: str) -> float:
        """Score based on company tier preferences"""
        for tier_name, tier_data in self.company_tiers.items():
            # Check exact company matches
            for comp in tier_data['companies']:
                if comp.lower() in company:
                    return tier_data['score'] * 0.3  # Convert 10-point to 3-point scale

            # Check pattern matches
            for pattern in tier_data['patterns']:
                if pattern in company:
                    return tier_data['score'] * 0.25

        return 0

    def _score_role_match(self, title: str) -> float:
        """Score based on role title preferences"""
        for match_level, match_data in self.role_preferences.items():
            for role_title in match_data['titles']:
                if role_title in title:
                    return match_data['score'] * 0.25  # Convert 10-point to 2.5-point scale

        return 0

    def _score_salary(self, salary_str: str) -> float:
        """Score based on salary alignment"""
        if not salary_str:
            return 0

        # Extract numbers from salary string
        numbers = re.findall(r'[\d,]+', salary_str.replace(',', ''))
        if not numbers:
            return 0

        try:
            # Get the highest number (assuming it's max salary)
            salaries = [int(n) for n in numbers if len(n) >= 3]
            if not salaries:
                return 0

            max_salary = max(salaries)

            # Handle ranges and different formats
            if max_salary < 1000:  # Likely hourly or daily rate
                if 'hour' in salary_str or '/hr' in salary_str:
                    max_salary *= 2000  # ~40hrs/week * 50 weeks
                elif 'day' in salary_str or '/day' in salary_str:
                    max_salary *= 250  # ~250 working days

            # Score based on target ranges
            if max_salary >= 180000:  # Above target
                return 1.5
            elif max_salary >= 150000:  # At minimum
                return 1.0
            elif max_salary >= 120000:  # Close to minimum
                return 0.5
            else:
                return -1.0  # Below acceptable range

        except (ValueError, IndexError):
            return 0

    def _is_generic_project_manager(self, title: str, description: str) -> bool:
        """Filter out generic PM roles unless they contain BRM/strategic elements"""
        title = title.lower()
        description = description.lower()

        # Check if it's a PM role
        is_pm_role = any(pm_term in title for pm_term in [
            'project manager', 'programme manager', 'program manager'
        ])

        if not is_pm_role:
            return False

        # Load PM exception keywords from config
        try:
            config_path = Path(__file__).parent.parent / 'data' / 'job_monitor_config.json'
            with open(config_path, 'r') as f:
                config = json.load(f)
                pm_exceptions = config.get('keywords', {}).get('pm_exceptions', [])
        except (OSError, json.JSONDecodeError, KeyError):
            # Fallback exception keywords
            pm_exceptions = [
                'business relationship', 'client partner', 'stakeholder management',
                'portfolio governance', 'strategic planning', 'business strategy',
                'change management', 'transformation'
            ]

        # Check if description contains BRM/strategic elements
        has_brm_elements = any(exception in description for exception in pm_exceptions)

        # Also check for senior/strategic indicators
        strategic_indicators = [
            'senior', 'principal', 'lead', 'head', 'director',
            'strategic', 'enterprise', 'transformation', 'governance',
            'stakeholder', 'client relationship', 'business relationship'
        ]

        has_strategic_elements = any(indicator in description for indicator in strategic_indicators)

        # Filter out if it's PM role without BRM or strategic elements
        return not (has_brm_elements or has_strategic_elements)

    def _score_experience_alignment(self, job_text: str) -> float:
        """Score based on experience level alignment"""
        # Positive indicators
        senior_indicators = ['senior', 'principal', 'lead', 'manager', 'director']
        enterprise_indicators = ['enterprise', 'large scale', 'complex', 'strategic']

        # Negative indicators
        junior_indicators = ['junior', 'graduate', 'entry level', 'intern']

        score = 0

        for indicator in senior_indicators:
            if indicator in job_text:
                score += 0.2

        for indicator in enterprise_indicators:
            if indicator in job_text:
                score += 0.15

        for indicator in junior_indicators:
            if indicator in job_text:
                score -= 1.0

        return max(-1.0, min(1.0, score))

    def _detect_red_flags(self, job_text: str) -> Dict:
        """Detect potential red flags in job descriptions"""
        red_flags = []
        penalty = 0

        # Major red flags
        major_flags = [
            'unpaid', 'volunteer', 'commission only', 'equity only',
            'multi-level marketing', 'mlm', 'pyramid'
        ]

        # Warning flags
        warning_flags = [
            'urgent start', 'immediate start', 'work weekends',
            'long hours', 'high pressure', 'fast paced environment'
        ]

        # Experience mismatch flags
        mismatch_flags = [
            'graduate role', 'entry level', 'junior position',
            'first job', 'no experience required'
        ]

        for flag in major_flags:
            if flag in job_text:
                red_flags.append(f"Major: {flag}")
                penalty -= 3.0

        for flag in warning_flags:
            if flag in job_text:
                red_flags.append(f"Warning: {flag}")
                penalty -= 0.5

        for flag in mismatch_flags:
            if flag in job_text:
                red_flags.append(f"Level mismatch: {flag}")
                penalty -= 2.0

        return {'flags': red_flags, 'penalty': max(-5.0, penalty)}

    def generate_application_strategy(self, job: Dict, scoring_breakdown: Dict) -> Dict:
        """Generate application strategy based on scoring breakdown"""
        strategy = {
            'priority_level': 'Medium',
            'key_selling_points': [],
            'cover_letter_hooks': [],
            'interview_prep': [],
            'application_approach': 'Standard'
        }

        final_score = scoring_breakdown['final_score']

        # Determine priority
        if final_score >= 8.5:
            strategy['priority_level'] = 'High'
            strategy['application_approach'] = 'Personalized + Network'
        elif final_score >= 7.0:
            strategy['priority_level'] = 'Medium-High'
            strategy['application_approach'] = 'Targeted'
        elif final_score >= 5.5:
            strategy['priority_level'] = 'Medium'
        else:
            strategy['priority_level'] = 'Low'
            strategy['application_approach'] = 'Quick Apply'

        # Generate selling points based on USP matches
        for usp_match in scoring_breakdown['usp_matches']:
            if usp_match['strength'] > 20:  # Strong match
                strategy['key_selling_points'].append(usp_match['usp'])

                # Generate cover letter hooks
                if usp_match['usp'] == 'The Crisis Navigator':
                    strategy['cover_letter_hooks'].append(
                        "When critical systems fail and stakeholders panic, I create structure from chaos - like when I led the response to a major cloud outage affecting enterprise customers."
                    )
                elif usp_match['usp'] == 'The Complexity Untangler':
                    strategy['cover_letter_hooks'].append(
                        "I specialize in transforming complex multi-stakeholder challenges into clear, actionable roadmaps that drive measurable business outcomes."
                    )

        return strategy

def test_enhanced_scoring():
    """Test the enhanced scoring system"""
    scorer = EnhancedProfileScorer()

    # Test job examples
    test_jobs = [
        {
            'title': 'Senior Business Relationship Manager',
            'company': 'PwC Australia',
            'location': 'Perth, WA',
            'salary': '$160,000 - $180,000',
            'description': 'Lead complex stakeholder relationships and drive digital transformation initiatives across enterprise clients.'
        },
        {
            'title': 'Crisis Management Specialist',
            'company': 'BHP',
            'location': 'Perth, WA',
            'salary': '$140,000 - $160,000',
            'description': 'Manage critical incidents and emergency response procedures for mining operations.'
        },
        {
            'title': 'Graduate Project Manager',
            'company': 'Local Company',
            'location': 'Perth, WA',
            'salary': '$65,000 - $75,000',
            'description': 'Entry level position for recent graduates to learn project management.'
        }
    ]

    print("Enhanced Profile Scoring Test Results:")
    print("=" * 60)

    for i, job in enumerate(test_jobs, 1):
        score, breakdown = scorer.score_job_enhanced(job)
        strategy = scorer.generate_application_strategy(job, breakdown)

        print(f"\nJob {i}: {job['title']} at {job['company']}")
        print(f"Final Score: {score}/10 ({strategy['priority_level']} Priority)")

        print(f"\nScoring Breakdown:")
        print(f"  Base Score: {breakdown['base_score']}")
        print(f"  USP Matches: +{sum(m['bonus'] for m in breakdown['usp_matches']):.1f}")
        print(f"  Company Tier: +{breakdown['company_tier_bonus']:.1f}")
        print(f"  Role Match: +{breakdown['role_match_bonus']:.1f}")
        print(f"  Salary: +{breakdown['salary_bonus']:.1f}")

        if breakdown['usp_matches']:
            print(f"\nUSP Matches:")
            for match in breakdown['usp_matches']:
                print(f"  • {match['usp']}: {match['strength']:.0f}% match (+{match['bonus']:.2f})")

        print(f"\nApplication Strategy: {strategy['application_approach']}")
        if strategy['cover_letter_hooks']:
            print(f"Cover Letter Hook: {strategy['cover_letter_hooks'][0]}")

        print("-" * 50)

if __name__ == '__main__':
    test_enhanced_scoring()

#!/usr/bin/env python3
"""
Interview Analyst - JD Matching System

TDD Stub File - All methods raise NotImplementedError
Phase 223.2: Interview Analyst Agent
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ParsedJD:
    """Parsed Job Description with categorized requirements"""
    role_title: str = ""
    essential: List[str] = field(default_factory=list)
    desirable: List[str] = field(default_factory=list)
    nice_to_have: List[str] = field(default_factory=list)


@dataclass
class RequirementMatch:
    """Result of matching a requirement against interview content"""
    requirement: str
    match_strength: str  # STRONG, MODERATE, WEAK, NO_MATCH
    evidence: List[str]
    confidence: float


@dataclass
class FitReport:
    """Complete fit analysis report"""
    candidate_name: str
    role_title: str
    overall_fit_score: float
    breakdown: Dict[str, Any]
    recommendation: str
    summary: str


@dataclass
class CandidateRanking:
    """Ranking entry for candidate comparison"""
    candidate_name: str
    fit_score: float
    strengths: List[str]
    gaps: List[str]


@dataclass
class ComparisonReport:
    """Multi-candidate comparison report"""
    role_title: str
    rankings: List[CandidateRanking]
    summary: str


class JDParser:
    """Parse Job Descriptions into structured requirements"""

    # Section header patterns
    ESSENTIAL_PATTERNS = [
        r'essential\s*(?:requirements?|skills?|qualifications?)?:?',
        r'required\s*(?:skills?|qualifications?)?:?',
        r'must\s+have:?',
        r'requirements?:?'
    ]

    DESIRABLE_PATTERNS = [
        r'desirable\s*(?:skills?|qualifications?)?:?',
        r'preferred\s*(?:skills?|qualifications?)?:?',
        r'nice\s+to\s+have:?',
        r'bonus:?'
    ]

    NICE_TO_HAVE_PATTERNS = [
        r'nice\s+to\s+have:?',
        r'optional:?',
        r'bonus\s*(?:skills?)?:?'
    ]

    def parse(self, jd_text: str) -> ParsedJD:
        """Parse JD text into categorized requirements"""
        import re

        if not jd_text.strip():
            return ParsedJD()

        # Extract role title (first line or "Role:" pattern)
        lines = jd_text.strip().split('\n')
        role_title = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Check for "Role:" pattern
            role_match = re.match(r'^(?:role|position|title)\s*:\s*(.+)$', line, re.IGNORECASE)
            if role_match:
                role_title = role_match.group(1).strip()
                break
            # Otherwise use first non-empty line as title
            if not role_title and line and not self._is_bullet(line):
                role_title = line
                break

        # Parse requirements by section
        essential = []
        desirable = []
        nice_to_have = []

        current_section = 'essential'  # Default to essential
        text_lower = jd_text.lower()

        # Find section boundaries
        sections = self._split_into_sections(jd_text)

        for section_name, section_content in sections.items():
            requirements = self._extract_requirements(section_content)
            if section_name == 'essential':
                essential.extend(requirements)
            elif section_name == 'desirable':
                desirable.extend(requirements)
            elif section_name == 'nice_to_have':
                nice_to_have.extend(requirements)

        # If no sections found, treat all bullets as essential
        if not essential and not desirable and not nice_to_have:
            essential = self._extract_requirements(jd_text)

        return ParsedJD(
            role_title=role_title,
            essential=essential,
            desirable=desirable,
            nice_to_have=nice_to_have
        )

    def _split_into_sections(self, jd_text: str) -> Dict[str, str]:
        """Split JD into sections by header patterns"""
        import re

        sections = {}
        lines = jd_text.split('\n')
        current_section = 'essential'
        current_content = []

        for line in lines:
            line_lower = line.lower().strip()

            # Check for section headers
            section_found = None

            for pattern in self.NICE_TO_HAVE_PATTERNS:
                if re.search(pattern, line_lower):
                    section_found = 'nice_to_have'
                    break

            if not section_found:
                for pattern in self.DESIRABLE_PATTERNS:
                    if re.search(pattern, line_lower):
                        section_found = 'desirable'
                        break

            if not section_found:
                for pattern in self.ESSENTIAL_PATTERNS:
                    if re.search(pattern, line_lower):
                        section_found = 'essential'
                        break

            if section_found:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = section_found
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def _extract_requirements(self, text: str) -> List[str]:
        """Extract bullet-pointed requirements from text"""
        import re

        requirements = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            # Match various bullet formats: -, *, •, numbers
            bullet_match = re.match(r'^[-*•]\s*(.+)$', line)
            if bullet_match:
                req = bullet_match.group(1).strip()
                if req and len(req) > 3:  # Skip very short items
                    requirements.append(req)
            # Also match numbered items
            numbered_match = re.match(r'^\d+[.)]\s*(.+)$', line)
            if numbered_match:
                req = numbered_match.group(1).strip()
                if req and len(req) > 3:
                    requirements.append(req)

        return requirements

    def _is_bullet(self, line: str) -> bool:
        """Check if line is a bullet point"""
        import re
        return bool(re.match(r'^[-*•]\s', line.strip()) or re.match(r'^\d+[.)]\s', line.strip()))


class RequirementMatcher:
    """Match requirements against interview content"""

    # Semantic synonyms for common tech terms
    SYNONYMS = {
        'kubernetes': ['k8s', 'container orchestration', 'aks', 'eks', 'gke'],
        'terraform': ['iac', 'infrastructure as code', 'hcl'],
        'azure': ['microsoft cloud', 'az-'],
        'aws': ['amazon web services', 'ec2', 's3'],
        'leadership': ['led', 'managed', 'team lead', 'direct reports', 'mentored'],
        'python': ['py', 'django', 'flask'],
        'docker': ['containers', 'containerization', 'dockerfile'],
        'ci/cd': ['pipeline', 'continuous integration', 'devops', 'github actions', 'jenkins'],
    }

    def match(self, requirement: str, interview_segments: List[Dict]) -> RequirementMatch:
        """Match a single requirement against interview segments"""
        import re

        if not interview_segments:
            return RequirementMatch(
                requirement=requirement,
                match_strength="NO_MATCH",
                evidence=[],
                confidence=0.0
            )

        # Combine all segment text
        all_text = ' '.join(seg.get('text', '') for seg in interview_segments)
        all_text_lower = all_text.lower()
        requirement_lower = requirement.lower()

        # Extract key terms from requirement
        key_terms = self._extract_key_terms(requirement_lower)

        # Find matching segments
        matching_segments = []
        match_scores = []

        for segment in interview_segments:
            text = segment.get('text', '')
            text_lower = text.lower()

            # Score this segment
            score = self._score_segment(text_lower, key_terms)
            if score > 0:
                matching_segments.append(text)
                match_scores.append(score)

        # Determine match strength
        if not matching_segments:
            return RequirementMatch(
                requirement=requirement,
                match_strength="NO_MATCH",
                evidence=[],
                confidence=0.0
            )

        avg_score = sum(match_scores) / len(match_scores)
        max_score = max(match_scores)

        # Classify match strength
        if max_score >= 3 or (avg_score >= 2 and len(matching_segments) >= 3):
            match_strength = "STRONG"
            confidence = min(0.95, 0.7 + (max_score * 0.05))
        elif max_score >= 2 or (avg_score >= 1 and len(matching_segments) >= 2):
            match_strength = "MODERATE"
            confidence = min(0.75, 0.5 + (max_score * 0.05))
        else:
            match_strength = "WEAK"
            confidence = min(0.5, 0.3 + (max_score * 0.05))

        # Select best evidence (top 3 segments)
        evidence = sorted(zip(match_scores, matching_segments), reverse=True)[:3]
        evidence_texts = [text[:200] + "..." if len(text) > 200 else text for _, text in evidence]

        return RequirementMatch(
            requirement=requirement,
            match_strength=match_strength,
            evidence=evidence_texts,
            confidence=confidence
        )

    def _extract_key_terms(self, requirement: str) -> List[str]:
        """Extract key terms from a requirement string"""
        import re

        # Remove common words
        stop_words = {'experience', 'with', 'in', 'and', 'or', 'the', 'a', 'an',
                      'years', 'year', 'strong', 'good', 'knowledge', 'of', 'skills'}

        # Extract words
        words = re.findall(r'\b\w+\b', requirement.lower())
        key_terms = [w for w in words if w not in stop_words and len(w) > 2]

        # Add synonyms
        expanded_terms = list(key_terms)
        for term in key_terms:
            for base_term, synonyms in self.SYNONYMS.items():
                if term == base_term or term in synonyms:
                    expanded_terms.append(base_term)
                    expanded_terms.extend(synonyms)

        return list(set(expanded_terms))

    def _score_segment(self, segment_text: str, key_terms: List[str]) -> float:
        """Score how well a segment matches key terms"""
        score = 0

        for term in key_terms:
            if term in segment_text:
                score += 1
                # Bonus for multiple mentions
                count = segment_text.count(term)
                if count > 1:
                    score += min(count - 1, 2) * 0.5

        return score


class FitReportGenerator:
    """Generate fit analysis reports"""

    # Weights for requirement categories
    ESSENTIAL_WEIGHT = 0.60
    DESIRABLE_WEIGHT = 0.30
    NICE_TO_HAVE_WEIGHT = 0.10

    # Strength to score mapping
    STRENGTH_SCORES = {
        "STRONG": 100,
        "MODERATE": 70,
        "WEAK": 40,
        "NO_MATCH": 0
    }

    def generate(
        self,
        candidate_name: str,
        parsed_jd: ParsedJD,
        matches: List[RequirementMatch]
    ) -> FitReport:
        """Generate a fit report from JD and matches"""

        # Create lookup for matches by requirement
        match_lookup = {m.requirement: m for m in matches}

        # Score each category
        essential_results = []
        essential_score = 0
        for req in parsed_jd.essential:
            match = match_lookup.get(req)
            if match:
                essential_results.append({
                    "requirement": req,
                    "match_strength": match.match_strength,
                    "evidence": match.evidence,
                    "confidence": match.confidence
                })
                essential_score += self.STRENGTH_SCORES.get(match.match_strength, 0)

        desirable_results = []
        desirable_score = 0
        for req in parsed_jd.desirable:
            match = match_lookup.get(req)
            if match:
                desirable_results.append({
                    "requirement": req,
                    "match_strength": match.match_strength,
                    "evidence": match.evidence,
                    "confidence": match.confidence
                })
                desirable_score += self.STRENGTH_SCORES.get(match.match_strength, 0)

        nice_to_have_results = []
        nice_to_have_score = 0
        for req in parsed_jd.nice_to_have:
            match = match_lookup.get(req)
            if match:
                nice_to_have_results.append({
                    "requirement": req,
                    "match_strength": match.match_strength,
                    "evidence": match.evidence,
                    "confidence": match.confidence
                })
                nice_to_have_score += self.STRENGTH_SCORES.get(match.match_strength, 0)

        # Calculate weighted score
        total_essential = len(parsed_jd.essential) or 1
        total_desirable = len(parsed_jd.desirable) or 1
        total_nice_to_have = len(parsed_jd.nice_to_have) or 1

        essential_avg = essential_score / total_essential if parsed_jd.essential else 100
        desirable_avg = desirable_score / total_desirable if parsed_jd.desirable else 100
        nice_to_have_avg = nice_to_have_score / total_nice_to_have if parsed_jd.nice_to_have else 100

        # Weight based on what's present
        total_weight = 0
        weighted_score = 0

        if parsed_jd.essential:
            weighted_score += essential_avg * self.ESSENTIAL_WEIGHT
            total_weight += self.ESSENTIAL_WEIGHT
        if parsed_jd.desirable:
            weighted_score += desirable_avg * self.DESIRABLE_WEIGHT
            total_weight += self.DESIRABLE_WEIGHT
        if parsed_jd.nice_to_have:
            weighted_score += nice_to_have_avg * self.NICE_TO_HAVE_WEIGHT
            total_weight += self.NICE_TO_HAVE_WEIGHT

        overall_fit_score = weighted_score / total_weight if total_weight > 0 else 0

        # Generate recommendation
        recommendation = self._generate_recommendation(overall_fit_score, essential_results)

        # Generate summary
        summary = self._generate_summary(candidate_name, parsed_jd.role_title,
                                         overall_fit_score, essential_results)

        return FitReport(
            candidate_name=candidate_name,
            role_title=parsed_jd.role_title,
            overall_fit_score=round(overall_fit_score, 1),
            breakdown={
                "essential_results": essential_results,
                "desirable_results": desirable_results,
                "nice_to_have_results": nice_to_have_results,
                "essential_avg": round(essential_avg, 1),
                "desirable_avg": round(desirable_avg, 1),
                "nice_to_have_avg": round(nice_to_have_avg, 1)
            },
            recommendation=recommendation,
            summary=summary
        )

    def _generate_recommendation(self, score: float, essential_results: List[Dict]) -> str:
        """Generate hire recommendation based on score and essentials"""

        # Check for any NO_MATCH on essentials (dealbreaker)
        essential_gaps = [r for r in essential_results if r["match_strength"] == "NO_MATCH"]

        if essential_gaps:
            if len(essential_gaps) >= 2:
                return "DO_NOT_HIRE"
            elif score < 50:
                return "DO_NOT_HIRE"
            else:
                return "CONSIDER"

        if score >= 85:
            return "STRONG_HIRE"
        elif score >= 70:
            return "HIRE"
        elif score >= 50:
            return "CONSIDER"
        else:
            return "DO_NOT_HIRE"

    def _generate_summary(self, candidate_name: str, role_title: str,
                          score: float, essential_results: List[Dict]) -> str:
        """Generate human-readable summary"""

        strengths = [r["requirement"] for r in essential_results
                    if r["match_strength"] == "STRONG"]
        gaps = [r["requirement"] for r in essential_results
               if r["match_strength"] in ["NO_MATCH", "WEAK"]]

        summary_parts = [f"{candidate_name} scored {score:.0f}/100 for {role_title}."]

        if strengths:
            summary_parts.append(f"Strengths: {', '.join(strengths[:3])}.")
        if gaps:
            summary_parts.append(f"Gaps: {', '.join(gaps[:3])}.")

        return " ".join(summary_parts)


class InterviewAnalyst:
    """Main analyst class - orchestrates JD matching workflow"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.jd_parser = JDParser()
        self.matcher = RequirementMatcher()
        self.report_generator = FitReportGenerator()

    def analyze(self, jd_text: str, interview_data: Dict) -> FitReport:
        """Analyze interview against JD"""

        # Parse the JD
        parsed_jd = self.jd_parser.parse(jd_text)

        # Get interview segments
        segments = interview_data.get('segments', [])
        candidate_name = interview_data.get('candidate_name', 'Unknown')

        # Collect all requirements
        all_requirements = (
            parsed_jd.essential +
            parsed_jd.desirable +
            parsed_jd.nice_to_have
        )

        # Match each requirement against interview
        matches = []
        for requirement in all_requirements:
            match = self.matcher.match(requirement, segments)
            matches.append(match)

        # Generate report
        return self.report_generator.generate(candidate_name, parsed_jd, matches)

    def analyze_by_interview_id(self, jd_text: str, interview_id: str) -> FitReport:
        """Analyze interview by ID against JD"""
        from claude.tools.interview.interview_search_system import InterviewSearchSystem

        # Fetch interview from database
        system = InterviewSearchSystem()
        conn = system._get_connection()

        try:
            cursor = conn.execute("""
                SELECT i.candidate_name, s.speaker, s.text_content
                FROM interviews i
                JOIN interview_segments s ON i.interview_id = s.interview_id
                WHERE i.interview_id = ?
            """, (interview_id,))
            rows = cursor.fetchall()

            if not rows:
                raise ValueError(f"Interview not found: {interview_id}")

            candidate_name = rows[0]['candidate_name']
            segments = [
                {"speaker": row['speaker'], "text": row['text_content']}
                for row in rows
            ]

        finally:
            conn.close()

        # Build interview data dict
        interview_data = {
            "candidate_name": candidate_name,
            "segments": segments
        }

        return self.analyze(jd_text, interview_data)

    def compare(self, jd_text: str, interviews: List[Dict]) -> ComparisonReport:
        """Compare multiple candidates against same JD"""

        # Parse JD once
        parsed_jd = self.jd_parser.parse(jd_text)

        # Analyze each candidate
        rankings = []
        for interview in interviews:
            report = self.analyze(jd_text, interview)

            # Extract strengths and gaps
            essential_results = report.breakdown.get('essential_results', [])
            strengths = [r['requirement'] for r in essential_results
                        if r['match_strength'] == 'STRONG']
            gaps = [r['requirement'] for r in essential_results
                   if r['match_strength'] in ['NO_MATCH', 'WEAK']]

            rankings.append(CandidateRanking(
                candidate_name=report.candidate_name,
                fit_score=report.overall_fit_score,
                strengths=strengths,
                gaps=gaps
            ))

        # Sort by fit score descending
        rankings.sort(key=lambda r: r.fit_score, reverse=True)

        # Generate summary
        if rankings:
            top_candidate = rankings[0].candidate_name
            summary = f"Top candidate: {top_candidate} ({rankings[0].fit_score:.0f}/100)"
        else:
            summary = "No candidates to compare"

        return ComparisonReport(
            role_title=parsed_jd.role_title,
            rankings=rankings,
            summary=summary
        )

#!/usr/bin/env python3
"""
Enhanced CV Search System - ChromaDB RAG + Pre-Interview Questions + Bulk Comparison

Extends the CV Parser with:
- ChromaDB semantic search for CVs
- Pre-interview question generation from JD vs CV gaps
- Bulk candidate comparison with verification scores

Author: Maia System (SRE Principal Engineer)
Created: 2025-12-16 (Phase: CV Integration - Optional Enhancements)
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: chromadb not available. Semantic search disabled.")

from claude.tools.interview.cv_parser import CVParser, ParsedCV, SkillEntry
from claude.tools.interview.dual_source_matcher import (
    DualSourceMatcher,
    EnhancedInterviewAnalyst,
    EnhancedRequirementMatch,
    EnhancedFitReport
)
from claude.tools.interview.interview_analyst import JDParser, ParsedJD


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CVSearchResult:
    """Result from CV semantic search"""
    document_id: str
    candidate_name: str
    chunk_text: str
    relevance_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PreInterviewQuestions:
    """Generated pre-interview questions based on CV vs JD gaps"""
    candidate_name: str
    role_title: str
    skill_verification_questions: List[str]
    experience_depth_questions: List[str]
    gap_probing_questions: List[str]
    certification_questions: List[str]
    general_questions: List[str]


@dataclass
class CandidateComparison:
    """Single candidate in bulk comparison"""
    candidate_name: str
    overall_score: float
    cv_skills_count: int
    cv_certs_count: int
    jd_match_percentage: float
    strengths: List[str]
    gaps: List[str]
    recommendation: str


@dataclass
class BulkComparisonReport:
    """Bulk candidate comparison report"""
    role_title: str
    candidates: List[CandidateComparison]
    top_candidate: str
    comparison_matrix: Dict[str, Dict[str, Any]]
    generated_at: str


# =============================================================================
# ENHANCED CV SEARCH WITH CHROMADB
# =============================================================================

class EnhancedCVSearch:
    """
    Enhanced CV Search with ChromaDB semantic search.

    Features:
    - Semantic search across CV content
    - Skill-based filtering
    - Candidate similarity matching
    """

    def __init__(
        self,
        chroma_path: Optional[str] = None,
        embedding_model: str = "nomic-embed-text"
    ):
        self.chroma_path = chroma_path or os.path.join(
            MAIA_ROOT, "claude", "data", "rag_databases", "cv_rag"
        )
        self.embedding_model = embedding_model
        self.ollama_url = "http://localhost:11434"

        os.makedirs(self.chroma_path, exist_ok=True)

        self.cv_parser = CVParser()
        self._init_chromadb()

    def _init_chromadb(self):
        """Initialize ChromaDB collection"""
        if not CHROMADB_AVAILABLE:
            self.collection = None
            return

        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.chroma_client.get_or_create_collection(
            name="cv_content",
            metadata={
                "description": "CV content chunks with embeddings",
                "embedding_model": self.embedding_model,
                "hnsw:space": "cosine"
            }
        )

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embed",
                json={"model": self.embedding_model, "input": text},
                timeout=30
            )
            response.raise_for_status()
            return response.json()["embeddings"][0]
        except Exception as e:
            print(f"Embedding error: {e}")
            raise

    def index_cv(self, document_id: str, candidate_name: str, content_text: str) -> int:
        """
        Index CV content in ChromaDB.

        Args:
            document_id: Unique document ID
            candidate_name: Candidate's name
            content_text: Full CV text

        Returns:
            Number of chunks indexed
        """
        if not self.collection:
            print("ChromaDB not available, skipping indexing")
            return 0

        # Chunk text (512 tokens ~= 2000 chars)
        chunks = self._chunk_text(content_text, chunk_size=2000, overlap=200)

        documents = []
        metadatas = []
        ids = []
        embeddings = []

        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 50:
                continue

            embedding = self._get_embedding(chunk)

            documents.append(chunk)
            metadatas.append({
                "document_id": document_id,
                "candidate_name": candidate_name,
                "chunk_index": i,
                "chunk_length": len(chunk)
            })
            ids.append(f"{document_id}_chunk_{i}")
            embeddings.append(embedding)

        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )

        return len(documents)

    def _chunk_text(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end
                for punct in ['. ', '.\n', '\n\n']:
                    last_punct = text.rfind(punct, start + chunk_size // 2, end)
                    if last_punct > 0:
                        end = last_punct + len(punct)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap

        return chunks

    def semantic_search(
        self,
        query: str,
        n_results: int = 10,
        candidate_filter: Optional[str] = None
    ) -> List[CVSearchResult]:
        """
        Semantic search across CVs.

        Args:
            query: Search query
            n_results: Max results
            candidate_filter: Optional filter by candidate name

        Returns:
            List of CVSearchResult
        """
        if not self.collection:
            return []

        query_embedding = self._get_embedding(query)

        # Build filter
        where_filter = None
        if candidate_filter:
            where_filter = {"candidate_name": {"$eq": candidate_filter}}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )

        search_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i] if results['distances'] else 0
                relevance = 1 - distance

                search_results.append(CVSearchResult(
                    document_id=metadata['document_id'],
                    candidate_name=metadata['candidate_name'],
                    chunk_text=results['documents'][0][i],
                    relevance_score=relevance,
                    metadata=metadata
                ))

        return search_results

    def find_similar_candidates(
        self,
        reference_candidate: str,
        n_results: int = 5
    ) -> List[CVSearchResult]:
        """
        Find candidates with similar skills/experience.

        Args:
            reference_candidate: Name of reference candidate
            n_results: Number of similar candidates to find

        Returns:
            List of similar candidates
        """
        # Get reference candidate's CV text
        conn = self.cv_parser._get_connection()
        try:
            cursor = conn.execute(
                "SELECT content_text FROM candidate_documents WHERE candidate_name = ?",
                (reference_candidate,)
            )
            row = cursor.fetchone()
            if not row:
                return []

            # Search for similar content, excluding the reference
            results = self.semantic_search(row['content_text'][:1000], n_results * 2)

            # Filter out reference candidate and dedupe
            seen = set()
            filtered = []
            for r in results:
                if r.candidate_name != reference_candidate and r.candidate_name not in seen:
                    filtered.append(r)
                    seen.add(r.candidate_name)
                    if len(filtered) >= n_results:
                        break

            return filtered

        finally:
            conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get search system stats"""
        stats = {
            "chromadb_available": CHROMADB_AVAILABLE,
            "chroma_path": self.chroma_path
        }

        if self.collection:
            stats["indexed_chunks"] = self.collection.count()

        return stats


# =============================================================================
# PRE-INTERVIEW QUESTION GENERATOR
# =============================================================================

class PreInterviewQuestionGenerator:
    """
    Generates pre-interview questions based on JD vs CV analysis.

    Creates targeted questions to:
    - Verify skills claimed on CV
    - Probe experience depth
    - Explore gaps between JD requirements and CV
    """

    # Question templates by category
    SKILL_VERIFICATION_TEMPLATES = [
        "Your CV mentions {skill}. Can you describe a specific project where you used this?",
        "How would you rate your proficiency in {skill} from 1-10, and why?",
        "What's the most complex problem you've solved using {skill}?",
    ]

    EXPERIENCE_DEPTH_TEMPLATES = [
        "You've worked with {skill} for {years} years. What's changed in that technology during your time using it?",
        "Describe a situation where your {skill} expertise helped the team avoid a major issue.",
        "If you had to teach {skill} to a junior engineer, what would be the top 3 things you'd cover?",
    ]

    GAP_PROBING_TEMPLATES = [
        "The role requires {requirement}, but I didn't see this on your CV. Do you have any experience with this?",
        "How would you approach learning {requirement} if you needed to use it in this role?",
        "What transferable skills from your background would help you with {requirement}?",
    ]

    CERT_TEMPLATES = [
        "I see you have {cert}. What was the most challenging topic in that certification?",
        "How has having {cert} helped you in your practical work?",
        "Are you planning to pursue any additional certifications?",
    ]

    def __init__(self):
        self.jd_parser = JDParser()
        self.cv_parser = CVParser()

    def generate(
        self,
        jd_text: str,
        candidate_name: str
    ) -> PreInterviewQuestions:
        """
        Generate pre-interview questions for a candidate.

        Args:
            jd_text: Job description text
            candidate_name: Candidate's name

        Returns:
            PreInterviewQuestions with categorized questions
        """
        # Parse JD
        parsed_jd = self.jd_parser.parse(jd_text)

        # Get CV data
        cv_skills = self.cv_parser.get_skills(candidate_name)
        cv_certs = self.cv_parser.get_certifications(candidate_name)

        skill_names = {s['skill_name'].lower() for s in cv_skills}
        cert_codes = {c['cert_code'].upper() for c in cv_certs}

        # Generate questions by category
        skill_verification = self._generate_skill_verification(cv_skills)
        experience_depth = self._generate_experience_depth(cv_skills)
        gap_probing = self._generate_gap_probing(parsed_jd, skill_names)
        cert_questions = self._generate_cert_questions(cv_certs)
        general = self._generate_general_questions(parsed_jd)

        return PreInterviewQuestions(
            candidate_name=candidate_name,
            role_title=parsed_jd.role_title,
            skill_verification_questions=skill_verification,
            experience_depth_questions=experience_depth,
            gap_probing_questions=gap_probing,
            certification_questions=cert_questions,
            general_questions=general
        )

    def _generate_skill_verification(self, cv_skills: List[Dict]) -> List[str]:
        """Generate skill verification questions"""
        questions = []

        # Pick top skills (by category diversity)
        categories_seen = set()
        for skill in cv_skills[:10]:
            cat = skill.get('skill_category', 'general')
            if cat not in categories_seen:
                template = self.SKILL_VERIFICATION_TEMPLATES[len(questions) % len(self.SKILL_VERIFICATION_TEMPLATES)]
                questions.append(template.format(skill=skill['skill_name']))
                categories_seen.add(cat)

            if len(questions) >= 5:
                break

        return questions

    def _generate_experience_depth(self, cv_skills: List[Dict]) -> List[str]:
        """Generate experience depth questions"""
        questions = []

        for skill in cv_skills:
            years = skill.get('years_experience')
            if years and years >= 2:
                template = self.EXPERIENCE_DEPTH_TEMPLATES[len(questions) % len(self.EXPERIENCE_DEPTH_TEMPLATES)]
                questions.append(template.format(skill=skill['skill_name'], years=years))

            if len(questions) >= 3:
                break

        return questions

    def _generate_gap_probing(self, parsed_jd: ParsedJD, cv_skills: set) -> List[str]:
        """Generate questions for JD requirements not on CV"""
        questions = []

        all_requirements = parsed_jd.essential + parsed_jd.desirable

        for req in all_requirements:
            req_lower = req.lower()
            # Check if any CV skill matches this requirement
            matched = any(skill in req_lower for skill in cv_skills)

            if not matched:
                template = self.GAP_PROBING_TEMPLATES[len(questions) % len(self.GAP_PROBING_TEMPLATES)]
                questions.append(template.format(requirement=req))

            if len(questions) >= 4:
                break

        return questions

    def _generate_cert_questions(self, cv_certs: List[Dict]) -> List[str]:
        """Generate certification-related questions"""
        questions = []

        for cert in cv_certs[:2]:
            template = self.CERT_TEMPLATES[len(questions) % len(self.CERT_TEMPLATES)]
            questions.append(template.format(cert=cert['cert_code']))

        return questions

    def _generate_general_questions(self, parsed_jd: ParsedJD) -> List[str]:
        """Generate general role-fit questions"""
        return [
            f"What attracted you to this {parsed_jd.role_title} role?",
            "Describe your ideal team environment and working style.",
            "Where do you see your career in 2-3 years?",
        ]


# =============================================================================
# BULK CANDIDATE COMPARISON
# =============================================================================

class BulkCandidateComparator:
    """
    Compare multiple candidates against a JD with verification scores.

    Produces ranked comparison with:
    - Overall fit scores
    - CV/Interview alignment
    - Strengths and gaps matrix
    """

    def __init__(self):
        self.cv_parser = CVParser()
        self.jd_parser = JDParser()
        self.dual_matcher = DualSourceMatcher()

    def compare(
        self,
        jd_text: str,
        candidate_names: List[str],
        include_interview_data: bool = False
    ) -> BulkComparisonReport:
        """
        Compare multiple candidates against a JD.

        Args:
            jd_text: Job description text
            candidate_names: List of candidate names to compare
            include_interview_data: Whether to include interview verification

        Returns:
            BulkComparisonReport with rankings and comparison matrix
        """
        parsed_jd = self.jd_parser.parse(jd_text)
        all_requirements = parsed_jd.essential + parsed_jd.desirable + parsed_jd.nice_to_have

        candidates = []
        comparison_matrix = {}

        for name in candidate_names:
            # Get CV data
            cv_skills = self.cv_parser.get_skills(name)
            cv_certs = self.cv_parser.get_certifications(name)

            skill_names = [s['skill_name'].lower() for s in cv_skills]

            # Calculate JD match percentage
            matched_requirements = 0
            strengths = []
            gaps = []

            for req in all_requirements:
                req_lower = req.lower()
                matched = any(skill in req_lower or req_lower in skill for skill in skill_names)

                if matched:
                    matched_requirements += 1
                    if req in parsed_jd.essential:
                        strengths.append(req)
                else:
                    if req in parsed_jd.essential:
                        gaps.append(req)

            jd_match = (matched_requirements / len(all_requirements) * 100) if all_requirements else 0

            # Calculate overall score (weighted)
            essential_match = sum(1 for s in strengths) / len(parsed_jd.essential) if parsed_jd.essential else 1
            overall_score = (essential_match * 60) + (jd_match * 0.3) + (min(len(cv_certs) * 5, 10))

            # Determine recommendation
            if overall_score >= 70 and not gaps:
                recommendation = "STRONG_HIRE"
            elif overall_score >= 55:
                recommendation = "HIRE"
            elif overall_score >= 40:
                recommendation = "CONSIDER"
            else:
                recommendation = "PASS"

            candidate = CandidateComparison(
                candidate_name=name,
                overall_score=round(overall_score, 1),
                cv_skills_count=len(cv_skills),
                cv_certs_count=len(cv_certs),
                jd_match_percentage=round(jd_match, 1),
                strengths=strengths[:5],
                gaps=gaps[:5],
                recommendation=recommendation
            )
            candidates.append(candidate)

            # Build matrix row
            comparison_matrix[name] = {
                "score": candidate.overall_score,
                "skills": len(cv_skills),
                "certs": len(cv_certs),
                "match_%": jd_match,
                "recommendation": recommendation
            }

        # Sort by score
        candidates.sort(key=lambda c: c.overall_score, reverse=True)
        top_candidate = candidates[0].candidate_name if candidates else ""

        return BulkComparisonReport(
            role_title=parsed_jd.role_title,
            candidates=candidates,
            top_candidate=top_candidate,
            comparison_matrix=comparison_matrix,
            generated_at=datetime.now().isoformat()
        )

    def generate_comparison_table(self, report: BulkComparisonReport) -> str:
        """Generate markdown comparison table"""
        lines = [
            f"## Candidate Comparison: {report.role_title}",
            f"Generated: {report.generated_at}",
            "",
            "| Rank | Candidate | Score | Skills | Certs | JD Match | Recommendation |",
            "|------|-----------|-------|--------|-------|----------|----------------|"
        ]

        for i, c in enumerate(report.candidates, 1):
            lines.append(
                f"| {i} | {c.candidate_name} | {c.overall_score} | {c.cv_skills_count} | "
                f"{c.cv_certs_count} | {c.jd_match_percentage}% | {c.recommendation} |"
            )

        lines.extend([
            "",
            f"**Top Candidate:** {report.top_candidate}",
            "",
            "### Detailed Analysis"
        ])

        for c in report.candidates[:3]:  # Top 3 details
            lines.extend([
                f"\n#### {c.candidate_name} ({c.recommendation})",
                f"- **Score:** {c.overall_score}/100",
                f"- **Strengths:** {', '.join(c.strengths) if c.strengths else 'None identified'}",
                f"- **Gaps:** {', '.join(c.gaps) if c.gaps else 'None identified'}"
            ])

        return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for enhanced CV search"""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced CV Search & Analysis")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Semantic search
    search_parser = subparsers.add_parser('search', help='Semantic search across CVs')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=5, help='Max results')

    # Index CVs
    index_parser = subparsers.add_parser('index', help='Index all CVs in ChromaDB')

    # Generate questions
    questions_parser = subparsers.add_parser('questions', help='Generate pre-interview questions')
    questions_parser.add_argument('--candidate', required=True, help='Candidate name')
    questions_parser.add_argument('--jd', required=True, help='Path to JD file')

    # Compare candidates
    compare_parser = subparsers.add_parser('compare', help='Compare candidates against JD')
    compare_parser.add_argument('--jd', required=True, help='Path to JD file')
    compare_parser.add_argument('--candidates', nargs='+', required=True, help='Candidate names')

    # Similar candidates
    similar_parser = subparsers.add_parser('similar', help='Find similar candidates')
    similar_parser.add_argument('--candidate', required=True, help='Reference candidate')

    # Stats
    subparsers.add_parser('stats', help='Show system stats')

    args = parser.parse_args()

    if args.command == 'search':
        search = EnhancedCVSearch()
        results = search.semantic_search(args.query, args.limit)

        print(f"\nFound {len(results)} results for: '{args.query}'")
        for r in results:
            print(f"\n  [{r.relevance_score:.2f}] {r.candidate_name}")
            print(f"    {r.chunk_text[:150]}...")

    elif args.command == 'index':
        search = EnhancedCVSearch()
        cv_parser = CVParser()

        conn = cv_parser._get_connection()
        try:
            cursor = conn.execute("SELECT document_id, candidate_name, content_text FROM candidate_documents")
            rows = cursor.fetchall()

            total_chunks = 0
            for row in rows:
                chunks = search.index_cv(row['document_id'], row['candidate_name'], row['content_text'])
                total_chunks += chunks
                print(f"  Indexed {row['candidate_name']}: {chunks} chunks")

            print(f"\nTotal indexed: {total_chunks} chunks from {len(rows)} CVs")
        finally:
            conn.close()

    elif args.command == 'questions':
        with open(args.jd, 'r') as f:
            jd_text = f.read()

        generator = PreInterviewQuestionGenerator()
        questions = generator.generate(jd_text, args.candidate)

        print(f"\n{'='*60}")
        print(f"PRE-INTERVIEW QUESTIONS: {questions.candidate_name}")
        print(f"Role: {questions.role_title}")
        print(f"{'='*60}")

        if questions.skill_verification_questions:
            print("\n## Skill Verification")
            for i, q in enumerate(questions.skill_verification_questions, 1):
                print(f"  {i}. {q}")

        if questions.experience_depth_questions:
            print("\n## Experience Depth")
            for i, q in enumerate(questions.experience_depth_questions, 1):
                print(f"  {i}. {q}")

        if questions.gap_probing_questions:
            print("\n## Gap Probing")
            for i, q in enumerate(questions.gap_probing_questions, 1):
                print(f"  {i}. {q}")

        if questions.certification_questions:
            print("\n## Certifications")
            for i, q in enumerate(questions.certification_questions, 1):
                print(f"  {i}. {q}")

        print("\n## General")
        for i, q in enumerate(questions.general_questions, 1):
            print(f"  {i}. {q}")

    elif args.command == 'compare':
        with open(args.jd, 'r') as f:
            jd_text = f.read()

        comparator = BulkCandidateComparator()
        report = comparator.compare(jd_text, args.candidates)

        print(comparator.generate_comparison_table(report))

    elif args.command == 'similar':
        search = EnhancedCVSearch()
        results = search.find_similar_candidates(args.candidate)

        print(f"\nCandidates similar to {args.candidate}:")
        for r in results:
            print(f"  - {r.candidate_name} (similarity: {r.relevance_score:.2f})")

    elif args.command == 'stats':
        search = EnhancedCVSearch()
        stats = search.get_stats()

        print("\nEnhanced CV Search Stats:")
        for k, v in stats.items():
            print(f"  {k}: {v}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

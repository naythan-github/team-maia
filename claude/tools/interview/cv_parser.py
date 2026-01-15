#!/usr/bin/env python3
"""
CV Parser - Document ingestion and skill extraction for recruitment pipeline.

Extends the Interview Search System with CV/resume processing capabilities.
Supports docx extraction, skill parsing, and integration with ChromaDB RAG.

Related Tools:
- General PDF extraction: claude/tools/document/pdf_text_extractor.py
- Scanned document OCR: claude/tools/finance/receipt_ocr.py

Author: Maia System (SRE Principal Engineer)
Created: 2025-12-16 (Phase: CV Integration)
"""

import os
import sys
import re
import json
import uuid
import sqlite3
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict

# PDF extraction support
try:
    from PyPDF2 import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Add Maia root to path
MAIA_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(MAIA_ROOT))


# =============================================================================
# SCHEMA
# =============================================================================

CV_SCHEMA = """
-- CV Integration Schema Extension
-- Adds candidate document processing to interview_search.db

-- Core: Candidate documents (CVs, cover letters, etc.)
CREATE TABLE IF NOT EXISTS candidate_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT UNIQUE NOT NULL,
    candidate_name TEXT NOT NULL,
    document_type TEXT NOT NULL DEFAULT 'cv',
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    content_text TEXT,
    parsed_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(candidate_name, document_type, file_hash)
);

-- Extracted skills from CV (normalized for matching)
CREATE TABLE IF NOT EXISTS candidate_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    skill_category TEXT,
    proficiency_claimed TEXT,
    years_experience INTEGER,
    evidence_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES candidate_documents(document_id) ON DELETE CASCADE
);

-- Certifications (separate for direct lookup)
CREATE TABLE IF NOT EXISTS candidate_certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    cert_code TEXT NOT NULL,
    cert_name TEXT,
    issuer TEXT,
    date_obtained TEXT,
    expiry_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES candidate_documents(document_id) ON DELETE CASCADE
);

-- Experience entries
CREATE TABLE IF NOT EXISTS candidate_experience (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL,
    company_name TEXT,
    role_title TEXT,
    start_date TEXT,
    end_date TEXT,
    duration_months INTEGER,
    description TEXT,
    skills_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES candidate_documents(document_id) ON DELETE CASCADE
);

-- FTS5 for CV full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS candidate_docs_fts USING fts5(
    document_id,
    candidate_name,
    document_type,
    content_text,
    tokenize='porter unicode61'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_docs_candidate ON candidate_documents(candidate_name);
CREATE INDEX IF NOT EXISTS idx_docs_type ON candidate_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_docs_hash ON candidate_documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_skills_document ON candidate_skills(document_id);
CREATE INDEX IF NOT EXISTS idx_skills_name ON candidate_skills(skill_name);
CREATE INDEX IF NOT EXISTS idx_certs_document ON candidate_certifications(document_id);
CREATE INDEX IF NOT EXISTS idx_certs_code ON candidate_certifications(cert_code);
CREATE INDEX IF NOT EXISTS idx_exp_document ON candidate_experience(document_id);

-- View: Unified candidate profile
CREATE VIEW IF NOT EXISTS v_candidate_profile AS
SELECT
    cd.candidate_name,
    cd.document_id,
    cd.document_type,
    cd.created_at as cv_uploaded,
    (SELECT COUNT(*) FROM candidate_skills cs WHERE cs.document_id = cd.document_id) as skills_count,
    (SELECT COUNT(*) FROM candidate_certifications cc WHERE cc.document_id = cd.document_id) as certs_count,
    (SELECT COUNT(*) FROM candidate_experience ce WHERE ce.document_id = cd.document_id) as experience_entries,
    (SELECT SUM(ce.duration_months) FROM candidate_experience ce WHERE ce.document_id = cd.document_id) as total_experience_months,
    i.interview_id,
    i.interview_date,
    i.total_segments as interview_segments
FROM candidate_documents cd
LEFT JOIN interviews i ON cd.candidate_name = i.candidate_name
GROUP BY cd.document_id;

-- Trigger: Sync FTS on document insert
CREATE TRIGGER IF NOT EXISTS candidate_docs_fts_insert
AFTER INSERT ON candidate_documents
BEGIN
    INSERT INTO candidate_docs_fts(document_id, candidate_name, document_type, content_text)
    VALUES (NEW.document_id, NEW.candidate_name, NEW.document_type, NEW.content_text);
END;

-- Job Descriptions table
CREATE TABLE IF NOT EXISTS job_descriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jd_id TEXT UNIQUE NOT NULL,
    role_title TEXT NOT NULL,
    department TEXT,
    level TEXT,  -- associate, mid, senior, lead, etc.
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    content_text TEXT,
    parsed_data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(role_title, file_hash)
);

-- JD Requirements (Essential/Desirable)
CREATE TABLE IF NOT EXISTS jd_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jd_id TEXT NOT NULL,
    requirement_text TEXT NOT NULL,
    requirement_type TEXT NOT NULL,  -- essential, desirable, nice_to_have
    category TEXT,  -- skill, certification, experience, education
    skill_keywords TEXT,  -- comma-separated keywords for matching
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id) ON DELETE CASCADE
);

-- FTS5 for JD search
CREATE VIRTUAL TABLE IF NOT EXISTS jd_fts USING fts5(
    jd_id,
    role_title,
    content_text,
    tokenize='porter unicode61'
);

-- Indexes for JD tables
CREATE INDEX IF NOT EXISTS idx_jd_role ON job_descriptions(role_title);
CREATE INDEX IF NOT EXISTS idx_jd_level ON job_descriptions(level);
CREATE INDEX IF NOT EXISTS idx_req_jd ON jd_requirements(jd_id);
CREATE INDEX IF NOT EXISTS idx_req_type ON jd_requirements(requirement_type);

-- Trigger: Sync FTS on JD insert
CREATE TRIGGER IF NOT EXISTS jd_fts_insert
AFTER INSERT ON job_descriptions
BEGIN
    INSERT INTO jd_fts(jd_id, role_title, content_text)
    VALUES (NEW.jd_id, NEW.role_title, NEW.content_text);
END;
"""


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class JDRequirement:
    """Extracted requirement from JD"""
    text: str
    requirement_type: str  # essential, desirable, nice_to_have
    category: str = ""     # skill, certification, experience, education
    skill_keywords: List[str] = field(default_factory=list)


@dataclass
class ParsedJD:
    """Parsed job description"""
    role_title: str
    department: str = ""
    level: str = ""  # associate, mid, senior, lead
    essential_requirements: List[JDRequirement] = field(default_factory=list)
    desirable_requirements: List[JDRequirement] = field(default_factory=list)
    raw_text: str = ""
    parse_confidence: float = 0.0


@dataclass
class SkillEntry:
    """Extracted skill from CV"""
    name: str                           # Normalized lowercase
    category: str = ""                  # cloud, iac, language, database, etc.
    proficiency: Optional[str] = None   # expert, intermediate, beginner
    years: Optional[int] = None         # Years of experience if stated
    evidence: str = ""                  # Source text from CV


@dataclass
class CertEntry:
    """Extracted certification from CV"""
    code: str                           # AZ-104, AWS-SAA
    name: str = ""                      # Full name
    issuer: str = ""                    # Microsoft, AWS, etc.
    date_obtained: Optional[str] = None
    expiry: Optional[str] = None


@dataclass
class ExperienceEntry:
    """Extracted work experience from CV"""
    company: str
    title: str = ""
    start_date: str = ""
    end_date: Optional[str] = None      # None = current
    duration_months: int = 0
    description: str = ""
    skills_extracted: List[str] = field(default_factory=list)


@dataclass
class EducationEntry:
    """Extracted education from CV"""
    institution: str
    degree: str = ""
    field: str = ""
    year: Optional[int] = None


@dataclass
class ParsedCV:
    """Complete parsed CV structure"""
    candidate_name: str
    contact: Dict[str, str] = field(default_factory=dict)
    skills: List[SkillEntry] = field(default_factory=list)
    certifications: List[CertEntry] = field(default_factory=list)
    experience: List[ExperienceEntry] = field(default_factory=list)
    education: List[EducationEntry] = field(default_factory=list)
    raw_text: str = ""
    parse_confidence: float = 0.0


# =============================================================================
# SKILL PATTERNS
# =============================================================================

# Common tech skills with categories
SKILL_PATTERNS = {
    # Cloud platforms
    "azure": "cloud",
    "aws": "cloud",
    "gcp": "cloud",
    "google cloud": "cloud",

    # IaC / DevOps
    "terraform": "iac",
    "arm template": "iac",
    "bicep": "iac",
    "cloudformation": "iac",
    "ansible": "iac",
    "puppet": "iac",
    "chef": "iac",

    # Containers / Orchestration
    "kubernetes": "container",
    "k8s": "container",
    "docker": "container",
    "aks": "container",
    "eks": "container",
    "gke": "container",

    # Languages
    "python": "language",
    "powershell": "language",
    "bash": "language",
    "javascript": "language",
    "typescript": "language",
    "java": "language",
    "c#": "language",
    "go": "language",
    "rust": "language",

    # Databases
    "sql": "database",
    "mysql": "database",
    "postgresql": "database",
    "mongodb": "database",
    "cosmos db": "database",
    "dynamodb": "database",

    # Identity / Security
    "active directory": "identity",
    "azure ad": "identity",
    "entra id": "identity",
    "entra": "identity",
    "okta": "identity",
    "mfa": "security",
    "sso": "identity",

    # Microsoft 365
    "microsoft 365": "m365",
    "m365": "m365",
    "office 365": "m365",
    "exchange": "m365",
    "sharepoint": "m365",
    "teams": "m365",
    "intune": "endpoint",

    # Networking
    "vpn": "networking",
    "dns": "networking",
    "dhcp": "networking",
    "cisco": "networking",
    "meraki": "networking",
    "firewall": "networking",

    # Monitoring
    "prometheus": "monitoring",
    "grafana": "monitoring",
    "datadog": "monitoring",
    "splunk": "monitoring",
    "azure monitor": "monitoring",

    # CI/CD
    "jenkins": "cicd",
    "github actions": "cicd",
    "azure devops": "cicd",
    "gitlab ci": "cicd",
    "circleci": "cicd",

    # Virtualization
    "vmware": "virtualization",
    "hyper-v": "virtualization",
    "hyperv": "virtualization",
    "esxi": "virtualization",
}

# Certification patterns
CERT_PATTERNS = {
    r"AZ-\d{3}": "Microsoft",
    r"AZ-\d{4}": "Microsoft",
    r"MS-\d{3}": "Microsoft",
    r"SC-\d{3}": "Microsoft",
    r"DP-\d{3}": "Microsoft",
    r"AI-\d{3}": "Microsoft",
    r"PL-\d{3}": "Microsoft",
    r"MB-\d{3}": "Microsoft",
    r"AWS-SA[AP]": "AWS",
    r"AWS-[A-Z]{3}": "AWS",
    r"CKA": "CNCF",
    r"CKAD": "CNCF",
    r"CKS": "CNCF",
    r"CCNA": "Cisco",
    r"CCNP": "Cisco",
    r"CCIE": "Cisco",
    r"CISSP": "ISC2",
    r"CEH": "EC-Council",
    r"CompTIA [A-Za-z+]+": "CompTIA",
}


# =============================================================================
# CV PARSER
# =============================================================================

class CVParser:
    """
    CV Parser for recruitment pipeline.

    Extracts text from docx files, parses skills/certifications,
    and stores in SQLite + ChromaDB for hybrid search.

    Usage:
        parser = CVParser()
        result = parser.ingest("/path/to/cv.docx", "John Smith", "Cloud Engineer")
        skills = parser.get_skills("John Smith")
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        chroma_path: Optional[str] = None
    ):
        """
        Initialize CV Parser.

        Args:
            db_path: Path to SQLite database (default: interview_search.db)
            chroma_path: Path to ChromaDB store (default: cv_rag)
        """
        self.db_path = db_path or os.path.join(
            MAIA_ROOT, "claude", "data", "databases", "intelligence", "interview_search.db"
        )
        self.chroma_path = chroma_path or os.path.join(
            MAIA_ROOT, "claude", "data", "rag_databases", "cv_rag"
        )

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.chroma_path, exist_ok=True)

        # Initialize schema
        self._init_schema()

    def _init_schema(self):
        """Initialize CV schema in database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(CV_SCHEMA)
        conn.commit()
        conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # =========================================================================
    # TEXT EXTRACTION
    # =========================================================================

    def extract_text(self, file_path: str) -> str:
        """
        Extract text from document file.

        Supports: docx (via textutil), txt, md

        Args:
            file_path: Path to document

        Returns:
            Extracted text content
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = Path(file_path).suffix.lower()

        if ext == ".docx":
            return self._extract_docx(file_path)
        elif ext == ".pdf":
            return self._extract_pdf(file_path)
        elif ext in [".txt", ".md"]:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from docx using textutil (macOS)"""
        try:
            result = subprocess.run(
                ["textutil", "-convert", "txt", "-stdout", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout
            else:
                raise RuntimeError(f"textutil failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Text extraction timed out")
        except FileNotFoundError:
            # textutil not available (not macOS)
            raise RuntimeError("textutil not available - install python-docx as fallback")

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyPDF2"""
        if not PDF_SUPPORT:
            raise RuntimeError("PDF support not available - install PyPDF2: pip3 install PyPDF2")

        try:
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            full_text = "\n".join(text_parts)
            if not full_text.strip():
                raise RuntimeError("PDF appears to be image-based (no extractable text)")

            return full_text
        except Exception as e:
            raise RuntimeError(f"PDF extraction failed: {e}")

    def compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file for deduplication"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    # =========================================================================
    # SKILL EXTRACTION
    # =========================================================================

    def extract_skills(self, text: str) -> List[SkillEntry]:
        """
        Extract skills from CV text using pattern matching.

        Args:
            text: CV text content

        Returns:
            List of SkillEntry objects
        """
        text_lower = text.lower()
        skills = []
        seen = set()

        for skill_name, category in SKILL_PATTERNS.items():
            if skill_name in text_lower and skill_name not in seen:
                # Find evidence (context around skill mention)
                evidence = self._extract_evidence(text, skill_name)

                # Try to extract years
                years = self._extract_years(text, skill_name)

                skills.append(SkillEntry(
                    name=skill_name,
                    category=category,
                    years=years,
                    evidence=evidence
                ))
                seen.add(skill_name)

        return skills

    def _extract_evidence(self, text: str, skill: str, context_chars: int = 100) -> str:
        """Extract context around skill mention"""
        text_lower = text.lower()
        idx = text_lower.find(skill)
        if idx == -1:
            return ""

        start = max(0, idx - context_chars)
        end = min(len(text), idx + len(skill) + context_chars)

        return text[start:end].strip()

    def _extract_years(self, text: str, skill: str) -> Optional[int]:
        """Try to extract years of experience for a skill"""
        text_lower = text.lower()

        # Patterns like "5 years of Azure" or "Azure (5 years)"
        patterns = [
            rf"(\d+)\+?\s*years?\s+(?:of\s+)?{re.escape(skill)}",
            rf"{re.escape(skill)}\s*[\(\[]?\s*(\d+)\+?\s*years?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return int(match.group(1))

        return None

    def extract_certifications(self, text: str) -> List[CertEntry]:
        """
        Extract certifications from CV text.

        Args:
            text: CV text content

        Returns:
            List of CertEntry objects
        """
        certs = []
        seen = set()

        for pattern, issuer in CERT_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                code = match.upper()
                if code not in seen:
                    certs.append(CertEntry(
                        code=code,
                        issuer=issuer
                    ))
                    seen.add(code)

        return certs

    # =========================================================================
    # FULL PARSING
    # =========================================================================

    def parse(self, file_path: str, candidate_name: Optional[str] = None) -> ParsedCV:
        """
        Parse CV file into structured data.

        Args:
            file_path: Path to CV file
            candidate_name: Optional candidate name (extracted from filename if not provided)

        Returns:
            ParsedCV object with extracted data
        """
        # Extract text
        raw_text = self.extract_text(file_path)

        # Extract candidate name from filename if not provided
        if not candidate_name:
            filename = Path(file_path).stem
            # Try to extract name (usually before " - " or first part)
            parts = filename.split(" - ")
            candidate_name = parts[0].strip() if parts else filename

        # Extract skills and certs
        skills = self.extract_skills(raw_text)
        certs = self.extract_certifications(raw_text)

        # Calculate confidence based on extraction success
        confidence = 0.5  # Base confidence
        if skills:
            confidence += 0.2
        if certs:
            confidence += 0.2
        if len(raw_text) > 500:
            confidence += 0.1

        return ParsedCV(
            candidate_name=candidate_name,
            skills=skills,
            certifications=certs,
            raw_text=raw_text,
            parse_confidence=min(confidence, 1.0)
        )

    # =========================================================================
    # INGESTION
    # =========================================================================

    def ingest(
        self,
        cv_path: str,
        candidate_name: str,
        role_title: str = "",
        document_type: str = "cv"
    ) -> Dict[str, Any]:
        """
        Ingest a CV into the database.

        Args:
            cv_path: Path to CV file
            candidate_name: Candidate's name
            role_title: Target role (optional)
            document_type: Type of document (cv, cover_letter, etc.)

        Returns:
            Dict with ingestion result
        """
        print(f"\nIngesting CV: {candidate_name}")
        print(f"  File: {cv_path}")

        # Compute hash for deduplication
        file_hash = self.compute_file_hash(cv_path)

        conn = self._get_connection()
        try:
            # Check for existing document
            cursor = conn.execute(
                """SELECT document_id FROM candidate_documents
                   WHERE candidate_name = ? AND document_type = ? AND file_hash = ?""",
                (candidate_name, document_type, file_hash)
            )
            existing = cursor.fetchone()

            if existing:
                print(f"  Document already exists: {existing['document_id']}")
                return {
                    "status": "exists",
                    "document_id": existing['document_id'],
                    "candidate_name": candidate_name
                }

            # Parse CV
            parsed = self.parse(cv_path, candidate_name)
            print(f"  Parsed: {len(parsed.skills)} skills, {len(parsed.certifications)} certs")

            # Generate document ID
            document_id = str(uuid.uuid4())

            # Insert document record
            conn.execute(
                """INSERT INTO candidate_documents
                   (document_id, candidate_name, document_type, file_path, file_hash,
                    content_text, parsed_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (document_id, candidate_name, document_type, cv_path, file_hash,
                 parsed.raw_text, json.dumps(asdict(parsed)))
            )

            # Insert skills
            for skill in parsed.skills:
                conn.execute(
                    """INSERT INTO candidate_skills
                       (document_id, skill_name, skill_category, proficiency_claimed,
                        years_experience, evidence_text)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (document_id, skill.name, skill.category, skill.proficiency,
                     skill.years, skill.evidence)
                )

            # Insert certifications
            for cert in parsed.certifications:
                conn.execute(
                    """INSERT INTO candidate_certifications
                       (document_id, cert_code, cert_name, issuer, date_obtained, expiry_date)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (document_id, cert.code, cert.name, cert.issuer,
                     cert.date_obtained, cert.expiry)
                )

            conn.commit()
            print(f"  Stored: document_id={document_id}")

            return {
                "status": "success",
                "document_id": document_id,
                "candidate_name": candidate_name,
                "skills_count": len(parsed.skills),
                "certs_count": len(parsed.certifications),
                "parse_confidence": parsed.parse_confidence
            }

        finally:
            conn.close()

    # =========================================================================
    # SEARCH
    # =========================================================================

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search CVs using FTS5.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of matching documents
        """
        conn = self._get_connection()
        try:
            # Sanitize query
            safe_query = ' '.join(re.findall(r'\w+', query))
            if not safe_query:
                return []

            cursor = conn.execute(
                """SELECT
                       cd.document_id,
                       cd.candidate_name,
                       cd.document_type,
                       cd.created_at,
                       bm25(candidate_docs_fts) as score
                   FROM candidate_docs_fts fts
                   JOIN candidate_documents cd ON fts.document_id = cd.document_id
                   WHERE candidate_docs_fts MATCH ?
                   ORDER BY score
                   LIMIT ?""",
                (safe_query, limit)
            )

            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def get_skills(self, candidate_name: str) -> List[Dict[str, Any]]:
        """Get all skills for a candidate"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT cs.* FROM candidate_skills cs
                   JOIN candidate_documents cd ON cs.document_id = cd.document_id
                   WHERE cd.candidate_name = ?""",
                (candidate_name,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_certifications(self, candidate_name: str) -> List[Dict[str, Any]]:
        """Get all certifications for a candidate"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT cc.* FROM candidate_certifications cc
                   JOIN candidate_documents cd ON cc.document_id = cd.document_id
                   WHERE cd.candidate_name = ?""",
                (candidate_name,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    # =========================================================================
    # JD PARSING
    # =========================================================================

    def parse_jd(self, file_path: str, role_title: Optional[str] = None) -> ParsedJD:
        """
        Parse a Job Description file into structured data.

        Args:
            file_path: Path to JD file
            role_title: Optional role title (extracted from filename if not provided)

        Returns:
            ParsedJD object with extracted requirements
        """
        # Extract text
        raw_text = self.extract_text(file_path)

        # Extract role title from filename if not provided
        if not role_title:
            filename = Path(file_path).stem
            # Remove common suffixes
            role_title = filename.replace(" - Orro Cloud", "").strip()

        # Determine level from role title
        level = self._determine_level(role_title)

        # Extract requirements
        essential = self._extract_requirements(raw_text, "essential")
        desirable = self._extract_requirements(raw_text, "desirable")

        # Calculate confidence
        confidence = 0.5
        if essential:
            confidence += 0.25
        if desirable:
            confidence += 0.15
        if len(raw_text) > 200:
            confidence += 0.1

        return ParsedJD(
            role_title=role_title,
            level=level,
            essential_requirements=essential,
            desirable_requirements=desirable,
            raw_text=raw_text,
            parse_confidence=min(confidence, 1.0)
        )

    def _determine_level(self, role_title: str) -> str:
        """Determine job level from role title"""
        title_lower = role_title.lower()
        if "associate" in title_lower or "junior" in title_lower:
            return "associate"
        elif "senior" in title_lower:
            return "senior"
        elif "lead" in title_lower or "principal" in title_lower:
            return "lead"
        elif "manager" in title_lower or "director" in title_lower:
            return "management"
        else:
            return "mid"

    def _extract_requirements(self, text: str, req_type: str) -> List[JDRequirement]:
        """
        Extract requirements from JD text.

        Args:
            text: JD text content
            req_type: 'essential' or 'desirable'

        Returns:
            List of JDRequirement objects
        """
        requirements = []

        # Define section markers based on requirement type
        if req_type == "essential":
            markers = ["skills, knowledge & experience", "essential", "required", "must have", "requirements:", "experience"]
            end_markers = ["desirable", "nice to have", "preferred", "qualifications", "about the"]
        else:
            markers = ["desirable", "nice to have", "preferred", "bonus", "highly regarded"]
            end_markers = ["about the", "benefits", "what we offer", "how to apply", "qualifications"]

        text_lower = text.lower()

        # Find section start
        start_idx = -1
        for marker in markers:
            idx = text_lower.find(marker)
            if idx != -1:
                start_idx = idx
                break

        if start_idx == -1:
            # Fallback: extract all bullet points from the document
            start_idx = 0

        # Find section end
        end_idx = len(text)
        for marker in end_markers:
            idx = text_lower.find(marker, start_idx + 50)  # Look after start
            if idx != -1 and idx < end_idx:
                end_idx = idx

        # Extract section
        section = text[start_idx:end_idx]

        # Handle inline bullets (e.g., "• Point one. • Point two.")
        # Split on bullet characters
        bullet_pattern = r'[•\-\*·](?:\s)'
        parts = re.split(bullet_pattern, section)

        for part in parts:
            part = part.strip()
            # Clean up the part
            clean_line = re.sub(r'^[•\-*·\d.]+\s*', '', part).strip()

            # Handle sentences that end with periods
            if clean_line and len(clean_line) > 15:  # Skip very short parts
                # Extract skill keywords
                keywords = self._extract_skill_keywords(clean_line)

                requirements.append(JDRequirement(
                    text=clean_line,
                    requirement_type=req_type,
                    category=self._categorize_requirement(clean_line),
                    skill_keywords=keywords
                ))

        # Also check for newline-separated bullet points
        lines = section.split('\n')
        for line in lines:
            line = line.strip()
            # Check for bullet point markers at start of line
            if line.startswith(('•', '-', '*', '·')) or re.match(r'^\d+\.', line):
                clean_line = re.sub(r'^[•\-*·\d.]+\s*', '', line).strip()
                if len(clean_line) > 15 and clean_line not in [r.text for r in requirements]:
                    keywords = self._extract_skill_keywords(clean_line)
                    requirements.append(JDRequirement(
                        text=clean_line,
                        requirement_type=req_type,
                        category=self._categorize_requirement(clean_line),
                        skill_keywords=keywords
                    ))

        return requirements

    def _extract_skill_keywords(self, text: str) -> List[str]:
        """Extract skill keywords from requirement text"""
        keywords = []
        text_lower = text.lower()

        for skill_name in SKILL_PATTERNS.keys():
            if skill_name in text_lower:
                keywords.append(skill_name)

        return keywords

    def _categorize_requirement(self, text: str) -> str:
        """Categorize a requirement (skill, certification, experience, education)"""
        text_lower = text.lower()

        if any(word in text_lower for word in ["certified", "certification", "az-", "aws-", "gcp-"]):
            return "certification"
        elif any(word in text_lower for word in ["degree", "bachelor", "master", "phd", "education"]):
            return "education"
        elif any(word in text_lower for word in ["years", "experience", "worked"]):
            return "experience"
        else:
            return "skill"

    def ingest_jd(
        self,
        jd_path: str,
        role_title: Optional[str] = None,
        department: str = ""
    ) -> Dict[str, Any]:
        """
        Ingest a JD into the database.

        Args:
            jd_path: Path to JD file
            role_title: Role title (extracted from filename if not provided)
            department: Department name

        Returns:
            Dict with ingestion result
        """
        print(f"\nIngesting JD: {jd_path}")

        # Compute hash for deduplication
        file_hash = self.compute_file_hash(jd_path)

        # Parse JD first to get role_title if not provided
        parsed = self.parse_jd(jd_path, role_title)
        role_title = parsed.role_title

        print(f"  Role: {role_title}")

        conn = self._get_connection()
        try:
            # Check for existing JD
            cursor = conn.execute(
                """SELECT jd_id FROM job_descriptions
                   WHERE role_title = ? AND file_hash = ?""",
                (role_title, file_hash)
            )
            existing = cursor.fetchone()

            if existing:
                print(f"  JD already exists: {existing['jd_id']}")
                return {
                    "status": "exists",
                    "jd_id": existing['jd_id'],
                    "role_title": role_title
                }

            print(f"  Parsed: {len(parsed.essential_requirements)} essential, {len(parsed.desirable_requirements)} desirable")

            # Generate JD ID
            jd_id = str(uuid.uuid4())

            # Insert JD record
            conn.execute(
                """INSERT INTO job_descriptions
                   (jd_id, role_title, department, level, file_path, file_hash,
                    content_text, parsed_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (jd_id, role_title, department, parsed.level, jd_path, file_hash,
                 parsed.raw_text, json.dumps(asdict(parsed)))
            )

            # Insert requirements
            all_requirements = (
                parsed.essential_requirements +
                parsed.desirable_requirements
            )
            for req in all_requirements:
                conn.execute(
                    """INSERT INTO jd_requirements
                       (jd_id, requirement_text, requirement_type, category, skill_keywords)
                       VALUES (?, ?, ?, ?, ?)""",
                    (jd_id, req.text, req.requirement_type, req.category,
                     ','.join(req.skill_keywords))
                )

            conn.commit()
            print(f"  Stored: jd_id={jd_id}")

            return {
                "status": "success",
                "jd_id": jd_id,
                "role_title": role_title,
                "level": parsed.level,
                "essential_count": len(parsed.essential_requirements),
                "desirable_count": len(parsed.desirable_requirements),
                "parse_confidence": parsed.parse_confidence
            }

        finally:
            conn.close()

    def search_jd(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search JDs using FTS5.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of matching JDs
        """
        conn = self._get_connection()
        try:
            safe_query = ' '.join(re.findall(r'\w+', query))
            if not safe_query:
                return []

            cursor = conn.execute(
                """SELECT
                       jd.jd_id,
                       jd.role_title,
                       jd.level,
                       jd.created_at,
                       bm25(jd_fts) as score
                   FROM jd_fts fts
                   JOIN job_descriptions jd ON fts.jd_id = jd.jd_id
                   WHERE jd_fts MATCH ?
                   ORDER BY score
                   LIMIT ?""",
                (safe_query, limit)
            )

            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def get_jd(self, role_title: str) -> Optional[Dict[str, Any]]:
        """Get a JD by role title"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT * FROM job_descriptions WHERE role_title = ?""",
                (role_title,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def get_jd_requirements(self, jd_id: str, req_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get requirements for a JD"""
        conn = self._get_connection()
        try:
            if req_type:
                cursor = conn.execute(
                    """SELECT * FROM jd_requirements WHERE jd_id = ? AND requirement_type = ?""",
                    (jd_id, req_type)
                )
            else:
                cursor = conn.execute(
                    """SELECT * FROM jd_requirements WHERE jd_id = ?""",
                    (jd_id,)
                )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def list_jds(self) -> List[Dict[str, Any]]:
        """List all JDs"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """SELECT jd_id, role_title, level, created_at,
                          (SELECT COUNT(*) FROM jd_requirements r WHERE r.jd_id = j.jd_id AND r.requirement_type = 'essential') as essential_count,
                          (SELECT COUNT(*) FROM jd_requirements r WHERE r.jd_id = j.jd_id AND r.requirement_type = 'desirable') as desirable_count
                   FROM job_descriptions j
                   ORDER BY created_at DESC"""
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    # =========================================================================
    # STATS
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get CV and JD system statistics"""
        conn = self._get_connection()
        try:
            stats = {}

            # CV stats
            cursor = conn.execute("SELECT COUNT(*) as count FROM candidate_documents")
            stats['total_documents'] = cursor.fetchone()['count']

            cursor = conn.execute("SELECT COUNT(DISTINCT candidate_name) as count FROM candidate_documents")
            stats['unique_candidates'] = cursor.fetchone()['count']

            cursor = conn.execute("SELECT COUNT(*) as count FROM candidate_skills")
            stats['total_skills'] = cursor.fetchone()['count']

            cursor = conn.execute("SELECT COUNT(*) as count FROM candidate_certifications")
            stats['total_certifications'] = cursor.fetchone()['count']

            # JD stats
            cursor = conn.execute("SELECT COUNT(*) as count FROM job_descriptions")
            stats['total_jds'] = cursor.fetchone()['count']

            cursor = conn.execute("SELECT COUNT(*) as count FROM jd_requirements")
            stats['total_jd_requirements'] = cursor.fetchone()['count']

            cursor = conn.execute("SELECT COUNT(*) as count FROM jd_requirements WHERE requirement_type = 'essential'")
            stats['essential_requirements'] = cursor.fetchone()['count']

            cursor = conn.execute("SELECT COUNT(*) as count FROM jd_requirements WHERE requirement_type = 'desirable'")
            stats['desirable_requirements'] = cursor.fetchone()['count']

            return stats

        finally:
            conn.close()


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for CV and JD Parser"""
    import argparse

    parser = argparse.ArgumentParser(description="CV and JD Parser for Recruitment Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # CV Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest a CV')
    ingest_parser.add_argument('cv_path', help='Path to CV file')
    ingest_parser.add_argument('--name', required=True, help='Candidate name')
    ingest_parser.add_argument('--role', default='', help='Target role')

    # CV Search command
    search_parser = subparsers.add_parser('search', help='Search CVs')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=10, help='Max results')

    # JD Ingest command
    jd_ingest_parser = subparsers.add_parser('ingest-jd', help='Ingest a Job Description')
    jd_ingest_parser.add_argument('jd_path', help='Path to JD file')
    jd_ingest_parser.add_argument('--role', help='Role title (extracted from filename if not provided)')
    jd_ingest_parser.add_argument('--department', default='', help='Department name')

    # JD Search command
    jd_search_parser = subparsers.add_parser('search-jd', help='Search JDs')
    jd_search_parser.add_argument('query', help='Search query')
    jd_search_parser.add_argument('--limit', type=int, default=10, help='Max results')

    # List JDs command
    subparsers.add_parser('list-jds', help='List all JDs')

    # Stats command
    subparsers.add_parser('stats', help='Show statistics')

    args = parser.parse_args()

    cv_parser = CVParser()

    if args.command == 'ingest':
        result = cv_parser.ingest(args.cv_path, args.name, args.role)
        print(f"\nResult: {result['status']}")
        if result['status'] == 'success':
            print(f"  Skills: {result['skills_count']}")
            print(f"  Certs: {result['certs_count']}")

    elif args.command == 'search':
        results = cv_parser.search(args.query, args.limit)
        print(f"\nFound {len(results)} results:")
        for r in results:
            print(f"  - {r['candidate_name']} ({r['document_type']})")

    elif args.command == 'ingest-jd':
        result = cv_parser.ingest_jd(args.jd_path, args.role, args.department)
        print(f"\nResult: {result['status']}")
        if result['status'] == 'success':
            print(f"  Level: {result['level']}")
            print(f"  Essential: {result['essential_count']}")
            print(f"  Desirable: {result['desirable_count']}")

    elif args.command == 'search-jd':
        results = cv_parser.search_jd(args.query, args.limit)
        print(f"\nFound {len(results)} JDs:")
        for r in results:
            print(f"  - {r['role_title']} ({r['level']})")

    elif args.command == 'list-jds':
        jds = cv_parser.list_jds()
        print(f"\nJob Descriptions ({len(jds)} total):")
        for jd in jds:
            print(f"  - {jd['role_title']} ({jd['level']}) - {jd['essential_count']} essential, {jd['desirable_count']} desirable")

    elif args.command == 'stats':
        stats = cv_parser.get_stats()
        print("\nRecruitment Pipeline Statistics:")
        print("\n  CVs:")
        print(f"    Documents: {stats['total_documents']}")
        print(f"    Candidates: {stats['unique_candidates']}")
        print(f"    Skills: {stats['total_skills']}")
        print(f"    Certifications: {stats['total_certifications']}")
        print("\n  JDs:")
        print(f"    Total JDs: {stats['total_jds']}")
        print(f"    Requirements: {stats['total_jd_requirements']}")
        print(f"    Essential: {stats['essential_requirements']}")
        print(f"    Desirable: {stats['desirable_requirements']}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()

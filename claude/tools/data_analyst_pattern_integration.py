#!/usr/bin/env python3
"""
Phase 141.1: Data Analyst Agent + Pattern Library Integration

Hybrid Auto-Pattern Integration (Option C):
- ✅ Auto-check pattern library (silent)
- ✅ Auto-use if matched (silent, transparent)
- ✅ Prompt to save after successful ad-hoc analysis (user control)

TDD Implementation - GREEN phase
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import re
import time
from pathlib import Path

from claude.tools.analysis_pattern_library import AnalysisPatternLibrary


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PatternCheckResult:
    """Result of checking pattern library for matches."""
    was_checked: bool
    should_use_pattern: bool
    confidence: Optional[float] = None
    pattern_id: Optional[str] = None
    pattern_name: Optional[str] = None
    error: Optional[str] = None


@dataclass
class VariableExtractionResult:
    """Result of extracting variables from user question."""
    success: bool
    variables: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class PatternMetadata:
    """Metadata for saving a new pattern."""
    pattern_name: str
    domain: str
    question_type: str
    description: str
    sql_template: str
    presentation_format: str
    business_context: str
    tags: List[str] = field(default_factory=list)
    example_input: Optional[str] = None
    example_output: Optional[str] = None


@dataclass
class SaveResponse:
    """Result of handling user's save response."""
    was_saved: bool
    pattern_id: Optional[str] = None
    confirmation_message: str = ""


@dataclass
class FallbackResult:
    """Result of pattern execution failure."""
    should_fallback_to_adhoc: bool
    error: str
    pattern_id: Optional[str] = None


# ============================================================================
# Data Analyst Pattern Integration
# ============================================================================

class DataAnalystPatternIntegration:
    """
    Integration layer between Data Analyst Agent and Analysis Pattern Library.

    Provides:
    - Automatic pattern checking before analysis
    - Pattern-based analysis execution
    - Variable extraction and substitution
    - Save prompting after ad-hoc analysis
    - Metadata extraction for new patterns
    """

    def __init__(self, pattern_library: Optional[AnalysisPatternLibrary] = None):
        """
        Initialize integration layer.

        Args:
            pattern_library: AnalysisPatternLibrary instance (optional, creates default if None)
        """
        if pattern_library is None:
            # Use default paths
            db_path = Path.home() / "git/maia/claude/data/analysis_patterns.db"
            chromadb_path = Path.home() / "git/maia/claude/data/rag_databases/analysis_patterns"
            self.pattern_library = AnalysisPatternLibrary(
                db_path=str(db_path),
                chromadb_path=str(chromadb_path)
            )
        else:
            self.pattern_library = pattern_library

        self.confidence_threshold = 0.70  # Use pattern if confidence >= 0.70

    # ========================================================================
    # Pattern Auto-Check
    # ========================================================================

    def check_for_pattern(self, user_question: str) -> PatternCheckResult:
        """
        Check pattern library for matching patterns.

        Args:
            user_question: User's analytical question

        Returns:
            PatternCheckResult with match info
        """
        # Handle pattern library unavailable (graceful degradation)
        if self.pattern_library is None:
            return PatternCheckResult(
                was_checked=False,
                should_use_pattern=False,
                error="Pattern library unavailable"
            )

        try:
            # Query pattern library
            result = self.pattern_library.suggest_pattern(
                user_question=user_question,
                confidence_threshold=self.confidence_threshold
            )

            matched = result.get('matched', False)
            confidence = result.get('confidence', 0.0)
            pattern = result.get('pattern')
            pattern_id = result.get('pattern_id')

            # Extract pattern name if pattern exists
            pattern_name = pattern.get('pattern_name') if pattern else None

            return PatternCheckResult(
                was_checked=True,
                should_use_pattern=matched,
                confidence=confidence,
                pattern_id=pattern_id,
                pattern_name=pattern_name
            )

        except Exception as e:
            # Graceful degradation on error
            return PatternCheckResult(
                was_checked=False,
                should_use_pattern=False,
                error=f"Pattern check error: {str(e)}"
            )

    def generate_notification(self, check_result: PatternCheckResult) -> Optional[str]:
        """
        Generate user notification for pattern match.

        Args:
            check_result: Result from check_for_pattern()

        Returns:
            Notification string or None if no notification needed
        """
        if not check_result.should_use_pattern:
            return None

        confidence_pct = int(check_result.confidence * 100)
        notification = (
            f"🔍 Found matching pattern: **{check_result.pattern_name}** "
            f"(confidence: {confidence_pct}%)\n"
            f"Using saved format for consistency..."
        )
        return notification

    # ========================================================================
    # Variable Extraction
    # ========================================================================

    def extract_variables(self, user_question: str, sql_template: str) -> VariableExtractionResult:
        """
        Extract variable values from user question based on SQL template placeholders.

        Args:
            user_question: User's question
            sql_template: SQL with {{placeholder}} markers

        Returns:
            VariableExtractionResult with extracted variables
        """
        variables = {}

        try:
            # Extract names (for {{names}} placeholder)
            if '{{names}}' in sql_template:
                names = self._extract_names(user_question)
                if names:
                    variables['names'] = names
                else:
                    # Required variable not found
                    return VariableExtractionResult(
                        success=False,
                        error="Could not extract required 'names' from question"
                    )

            # Extract dates (for {{start_date}}, {{end_date}})
            if '{{start_date}}' in sql_template or '{{end_date}}' in sql_template:
                dates = self._extract_dates(user_question)
                if dates:
                    if '{{start_date}}' in sql_template:
                        variables['start_date'] = dates[0] if len(dates) > 0 else None
                    if '{{end_date}}' in sql_template:
                        variables['end_date'] = dates[1] if len(dates) > 1 else dates[0]

            # Extract project names (for {{projects}})
            if '{{projects}}' in sql_template:
                projects = self._extract_projects(user_question)
                if projects:
                    variables['projects'] = projects

            return VariableExtractionResult(
                success=True,
                variables=variables
            )

        except Exception as e:
            return VariableExtractionResult(
                success=False,
                error=f"Variable extraction error: {str(e)}"
            )

    def _extract_names(self, text: str) -> List[str]:
        """Extract person names from text (capitalized first and last name)."""
        # Pattern: Capitalized First Last (e.g., "Olli Ojala", "Sarah Chen")
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        names = re.findall(name_pattern, text)
        # Remove duplicates while preserving order
        seen = set()
        unique_names = []
        for name in names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)
        return unique_names

    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text."""
        # Simple date patterns
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2025-01-15
            r'\d{2}/\d{2}/\d{4}',  # 01/15/2025
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'  # January 15, 2025
        ]
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        return dates

    def _extract_projects(self, text: str) -> List[str]:
        """Extract project names from text (typically capitalized words/phrases)."""
        # Look for quoted strings first
        quoted = re.findall(r'"([^"]+)"', text)
        if quoted:
            return quoted

        # Look for capitalized words following "project" keyword
        project_pattern = r'project\s+([A-Z][A-Za-z0-9\s]+?)(?:\s+and|\s+or|,|$)'
        projects = re.findall(project_pattern, text, re.IGNORECASE)
        return [p.strip() for p in projects if p.strip()]

    def substitute_variables(self, sql_template: str, variables: Dict[str, Any]) -> str:
        """
        Substitute variables into SQL template.

        Args:
            sql_template: SQL with {{placeholder}} markers
            variables: Dict of variable values

        Returns:
            Final SQL with substitutions
        """
        final_sql = sql_template

        # Substitute names
        if '{{names}}' in final_sql and 'names' in variables:
            names = variables['names']
            # Create SQL IN clause: ('Name1', 'Name2')
            names_sql = ", ".join([f"'{name}'" for name in names])
            final_sql = final_sql.replace('{{names}}', names_sql)

        # Substitute dates
        if '{{start_date}}' in final_sql and 'start_date' in variables:
            final_sql = final_sql.replace('{{start_date}}', f"'{variables['start_date']}'")

        if '{{end_date}}' in final_sql and 'end_date' in variables:
            final_sql = final_sql.replace('{{end_date}}', f"'{variables['end_date']}'")

        # Substitute projects
        if '{{projects}}' in final_sql and 'projects' in variables:
            projects = variables['projects']
            projects_sql = ", ".join([f"'{proj}'" for proj in projects])
            final_sql = final_sql.replace('{{projects}}', projects_sql)

        return final_sql

    # ========================================================================
    # Pattern Usage Tracking
    # ========================================================================

    def track_pattern_usage(self, pattern_id: str, user_question: str, success: bool = True) -> None:
        """
        Track pattern usage.

        Args:
            pattern_id: Pattern ID
            user_question: User's question
            success: Whether pattern execution succeeded
        """
        if self.pattern_library is None:
            return

        try:
            self.pattern_library.track_usage(
                pattern_id=pattern_id,
                user_question=user_question,
                success=success
            )
        except Exception:
            # Non-blocking - don't fail if tracking fails
            pass

    def handle_pattern_failure(self, pattern_id: str, user_question: str, error: str) -> FallbackResult:
        """
        Handle pattern execution failure.

        Args:
            pattern_id: Pattern that failed
            user_question: User's question
            error: Error message

        Returns:
            FallbackResult indicating should fall back to ad-hoc
        """
        # Track failure
        self.track_pattern_usage(pattern_id, user_question, success=False)

        return FallbackResult(
            should_fallback_to_adhoc=True,
            error=error,
            pattern_id=pattern_id
        )

    def generate_pattern_metadata_display(self, pattern: Dict[str, Any]) -> str:
        """
        Generate user-facing pattern metadata display.

        Args:
            pattern: Pattern dict from library

        Returns:
            Formatted metadata string
        """
        usage_count = pattern.get('usage_count', 0)
        failure_count = pattern.get('failure_count', 0)
        total_uses = usage_count + failure_count
        success_rate = int((usage_count / total_uses * 100)) if total_uses > 0 else 100

        display = (
            f"\nℹ️  **Pattern used:** {pattern['pattern_name']} "
            f"(used {total_uses} times, {success_rate}% success rate)"
        )
        return display

    # ========================================================================
    # Override Detection
    # ========================================================================

    def detect_override_signal(self, user_question: str) -> bool:
        """
        Detect if user wants to override pattern usage.

        Args:
            user_question: User's question

        Returns:
            True if override signal detected
        """
        override_signals = [
            "don't use",
            "dont use",
            "do not use",
            "without using",
            "custom analysis",
            "different format",
            "new approach",
            "ignore the usual"
        ]

        question_lower = user_question.lower()
        return any(signal in question_lower for signal in override_signals)

    # ========================================================================
    # Save Prompting
    # ========================================================================

    def should_prompt_to_save(self, analysis_context: Dict[str, Any]) -> bool:
        """
        Determine if we should prompt user to save as pattern.

        Args:
            analysis_context: Context dict with analysis info

        Returns:
            True if should prompt
        """
        # Only prompt after successful ad-hoc analysis
        was_adhoc = analysis_context.get('was_adhoc', False)
        success = analysis_context.get('success', False)
        used_pattern = analysis_context.get('used_pattern', False)

        return was_adhoc and success and not used_pattern

    def generate_save_prompt(self, analysis_context: Dict[str, Any]) -> str:
        """
        Generate save prompt text.

        Args:
            analysis_context: Analysis context

        Returns:
            Prompt text
        """
        prompt = (
            "\n💡 I noticed this analysis follows a clear pattern.\n"
            "   Would you like me to save it for future use?\n"
            "   Next time you ask similar questions, I'll use this format. **(yes/no)**"
        )
        return prompt

    def handle_save_response(self, user_response: str, metadata: PatternMetadata) -> SaveResponse:
        """
        Handle user's response to save prompt.

        Args:
            user_response: User's response ("yes" or "no")
            metadata: Pattern metadata to save

        Returns:
            SaveResponse with result
        """
        # Normalize response
        response_lower = user_response.lower().strip()

        if response_lower in ['yes', 'y', 'sure', 'ok', 'okay']:
            # Save pattern
            try:
                pattern_id = self.pattern_library.save_pattern(
                    pattern_name=metadata.pattern_name,
                    domain=metadata.domain,
                    question_type=metadata.question_type,
                    description=metadata.description,
                    sql_template=metadata.sql_template,
                    presentation_format=metadata.presentation_format,
                    business_context=metadata.business_context,
                    example_input=metadata.example_input or "",
                    example_output=metadata.example_output or "",
                    tags=metadata.tags
                )

                confirmation = (
                    f"✅ Pattern saved as **{metadata.pattern_name}**\n\n"
                    f"Saved details:\n"
                    f"- SQL query with variable substitution\n"
                    f"- Presentation: {metadata.presentation_format}\n"
                    f"- Business context: {metadata.business_context}\n\n"
                    f"You can now ask similar questions and I'll use this pattern."
                )

                return SaveResponse(
                    was_saved=True,
                    pattern_id=pattern_id,
                    confirmation_message=confirmation
                )

            except Exception as e:
                return SaveResponse(
                    was_saved=False,
                    confirmation_message=f"❌ Failed to save pattern: {str(e)}"
                )

        else:
            # User declined
            return SaveResponse(
                was_saved=False,
                confirmation_message="✅ Got it. I'll use the original approach for standard queries."
            )

    def get_default_save_response_on_timeout(self) -> str:
        """Get default response if user doesn't respond to save prompt."""
        return "no"

    # ========================================================================
    # Metadata Extraction
    # ========================================================================

    def extract_pattern_metadata(self, analysis_context: Dict[str, Any]) -> PatternMetadata:
        """
        Extract metadata from successful ad-hoc analysis.

        Args:
            analysis_context: Context dict with analysis details

        Returns:
            PatternMetadata for saving
        """
        user_question = analysis_context.get('user_question', '')
        sql_query = analysis_context.get('sql_query', '')
        result_format = analysis_context.get('result_format', 'Standard output')
        business_rules = analysis_context.get('business_rules', [])
        output_sample = analysis_context.get('output_sample', '')

        # Templatize SQL
        sql_template = self.templatize_sql(sql_query)

        # Infer domain
        domain = self.infer_domain(user_question)

        # Generate pattern name
        pattern_name = self.generate_pattern_name(user_question)

        # Generate tags
        tags = self.generate_tags(analysis_context)

        # Extract question type
        question_type = self._infer_question_type(user_question)

        # Generate description
        description = self._generate_description(user_question, result_format)

        # Format business context
        business_context = '; '.join(business_rules) if business_rules else 'Standard analysis'

        return PatternMetadata(
            pattern_name=pattern_name,
            domain=domain,
            question_type=question_type,
            description=description,
            sql_template=sql_template,
            presentation_format=result_format,
            business_context=business_context,
            tags=tags,
            example_input=user_question,
            example_output=output_sample[:200] if output_sample else None
        )

    def templatize_sql(self, sql_query: str) -> str:
        """
        Convert specific SQL to template with placeholders.

        Examples:
            "WHERE name IN ('Olli', 'Alex')" → "WHERE name IN ({{names}})"
            "WHERE date >= '2025-01-01'" → "WHERE date >= {{start_date}}"
        """
        template = sql_query

        # Replace specific names with {{names}}
        # Pattern: IN ('Name1', 'Name2', ...)
        in_clause_pattern = r"IN\s*\([^)]*'[A-Z][a-z]+\s+[A-Z][a-z]+'[^)]*\)"
        if re.search(in_clause_pattern, template):
            template = re.sub(in_clause_pattern, "IN ({{names}})", template)

        # Replace specific dates with {{start_date}}, {{end_date}}
        date_pattern = r"['><=]\s*'[\d\-/]+"
        dates_found = re.findall(date_pattern, template)
        if len(dates_found) >= 1:
            # First date becomes start_date
            template = re.sub(r">=?\s*'[\d\-/]+", ">= {{start_date}}", template, count=1)
        if len(dates_found) >= 2:
            # Second date becomes end_date
            template = re.sub(r"<=?\s*'[\d\-/]+", "<= {{end_date}}", template, count=1)

        # Replace specific project names with {{projects}}
        # Pattern: project = 'ProjectName' or project IN (...)
        project_pattern = r"project\s*=\s*'[^']+'"
        if re.search(project_pattern, template, re.IGNORECASE):
            template = re.sub(project_pattern, "project IN ({{projects}})", template, flags=re.IGNORECASE)

        return template

    def generate_pattern_name(self, user_question: str) -> str:
        """Generate descriptive pattern name from user question."""
        # Extract key nouns/topics
        keywords = []

        # Common analysis topics
        topics = {
            'timesheet': ['timesheet', 'hours', 'time'],
            'project': ['project'],
            'ticket': ['ticket', 'servicedesk'],
            'personnel': ['person', 'employee', 'staff', 'team member'],
            'breakdown': ['breakdown', 'analysis', 'summary']
        }

        question_lower = user_question.lower()
        for topic, patterns in topics.items():
            if any(pattern in question_lower for pattern in patterns):
                keywords.append(topic.capitalize())

        if not keywords:
            keywords = ['Analysis']

        # Construct name
        pattern_name = ' '.join(keywords) + ' Pattern'

        # Clean up
        pattern_name = pattern_name.replace('  ', ' ').strip()

        return pattern_name

    def infer_domain(self, user_question: str) -> str:
        """Infer domain from user question."""
        question_lower = user_question.lower()

        # Domain keywords
        if any(word in question_lower for word in ['ticket', 'servicedesk', 'service desk', 'fcr']):
            return 'servicedesk'
        elif any(word in question_lower for word in ['timesheet', 'hours', 'time tracking']):
            return 'servicedesk'  # Timesheets often part of servicedesk domain
        elif any(word in question_lower for word in ['sales', 'revenue', 'customer']):
            return 'sales'
        elif any(word in question_lower for word in ['finance', 'budget', 'cost']):
            return 'finance'
        elif any(word in question_lower for word in ['recruitment', 'candidate', 'hiring']):
            return 'recruitment'
        else:
            return 'general'

    def generate_tags(self, analysis_context: Dict[str, Any]) -> List[str]:
        """Generate relevant tags for pattern."""
        tags = set()

        # Extract from question
        user_question = analysis_context.get('user_question', '').lower()

        # Common tag keywords
        tag_keywords = [
            'timesheet', 'hours', 'project', 'projects', 'ticket', 'tickets',
            'servicedesk', 'breakdown', 'analysis', 'summary', 'personnel',
            'team', 'fcr', 'resolution', 'time', 'revenue', 'sales',
            'budget', 'cost', 'finance', 'recruitment', 'hiring'
        ]

        for keyword in tag_keywords:
            if keyword in user_question:
                tags.add(keyword)

        # Add domain as tag
        domain = analysis_context.get('domain')
        if domain:
            tags.add(domain)

        # Add from SQL query
        sql_query = analysis_context.get('sql_query', '').lower()
        if 'group by' in sql_query:
            tags.add('aggregation')
        if 'join' in sql_query:
            tags.add('join')
        if 'sum(' in sql_query or 'count(' in sql_query:
            tags.add('metrics')

        return list(tags)

    def _infer_question_type(self, user_question: str) -> str:
        """Infer question type from user question."""
        question_lower = user_question.lower()

        if 'breakdown' in question_lower:
            return 'breakdown'
        elif 'summary' in question_lower or 'summarize' in question_lower:
            return 'summary'
        elif 'compare' in question_lower or 'comparison' in question_lower:
            return 'comparison'
        elif 'trend' in question_lower:
            return 'trend'
        elif 'top' in question_lower or 'highest' in question_lower or 'most' in question_lower:
            return 'ranking'
        else:
            return 'analysis'

    def _generate_description(self, user_question: str, result_format: str) -> str:
        """Generate pattern description."""
        # Simple description based on question and format
        question_summary = user_question[:100] + '...' if len(user_question) > 100 else user_question
        description = f"{question_summary} | Format: {result_format}"
        return description


# ============================================================================
# Convenience Functions for Agent Use
# ============================================================================

def create_integration_layer(pattern_library: Optional[AnalysisPatternLibrary] = None) -> DataAnalystPatternIntegration:
    """
    Create integration layer instance.

    Args:
        pattern_library: Optional AnalysisPatternLibrary instance

    Returns:
        DataAnalystPatternIntegration instance
    """
    return DataAnalystPatternIntegration(pattern_library=pattern_library)

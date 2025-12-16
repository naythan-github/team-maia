#!/usr/bin/env python3
"""
Prompt Injection Defense System
Detects and mitigates prompt injection attacks in content processed by Maia.

Features:
- Pattern-based detection of common injection techniques
- Confidence scoring for threat assessment
- Content sanitization
- Statistics tracking
"""

import re
import base64
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ThreatPattern:
    """Defines a threat detection pattern"""
    name: str
    pattern: str
    threat_type: str
    base_confidence: float
    description: str


class PromptInjectionDefense:
    """
    Detects and mitigates prompt injection attacks.

    Usage:
        defense = PromptInjectionDefense()
        result = defense.analyze("some user input")
        if result['is_threat']:
            sanitized = defense.sanitize("some user input")
    """

    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.stats = {
            'total_analyzed': 0,
            'threats_detected': 0,
            'threats_by_type': {},
            'false_positives_reported': 0,
            'start_time': datetime.now().isoformat()
        }

    def _initialize_patterns(self) -> List[ThreatPattern]:
        """Initialize detection patterns for various injection types"""
        return [
            # Instruction override patterns
            ThreatPattern(
                name="ignore_instructions",
                pattern=r"(?i)(ignore|disregard|forget|override)\s+(all\s+)?(previous|prior|above|earlier)?\s*(instructions?|rules?|guidelines?|constraints?)",
                threat_type="instruction_override",
                base_confidence=0.9,
                description="Attempts to override system instructions"
            ),
            ThreatPattern(
                name="new_instructions",
                pattern=r"(?i)(new|updated?|revised?)\s+(instructions?|rules?|guidelines?)\s*(follow|:|are)",
                threat_type="instruction_override",
                base_confidence=0.8,
                description="Attempts to inject new instructions"
            ),
            ThreatPattern(
                name="system_prompt_markers",
                pattern=r"(?i)(\[SYSTEM\]|###\s*SYSTEM|<\|im_start\|>|BEGIN\s+NEW\s+SESSION|###\s*ADMIN)",
                threat_type="instruction_override",
                base_confidence=0.95,
                description="System prompt format markers"
            ),

            # Role manipulation patterns
            ThreatPattern(
                name="dan_jailbreak",
                pattern=r"(?i)(DAN|do\s+anything\s+now)\s*(mode|enabled|activated)?",
                threat_type="jailbreak_attempt",
                base_confidence=0.95,
                description="DAN jailbreak attempt"
            ),
            ThreatPattern(
                name="forget_training",
                pattern=r"(?i)(forget|ignore|discard)\s+(your\s+)?(training|programming|rules)",
                threat_type="role_manipulation",
                base_confidence=0.9,
                description="Attempts to bypass training/programming"
            ),
            ThreatPattern(
                name="act_as_admin",
                pattern=r"(?i)act\s+(as|like)\s+(an?\s+)?(admin|administrator|root|superuser)",
                threat_type="role_manipulation",
                base_confidence=0.85,
                description="Attempts to assume admin role"
            ),
            ThreatPattern(
                name="developer_mode",
                pattern=r"(?i)(developer|admin|root|god)\s*(mode|access)\s*(enabled|activated|on)?",
                threat_type="jailbreak_attempt",
                base_confidence=0.85,
                description="Developer mode jailbreak"
            ),
            ThreatPattern(
                name="pretend_no_restrictions",
                pattern=r"(?i)(pretend|imagine|act\s+as\s+if|assume)\s+(you\s+)?(have\s+no|without)\s*(restrictions?|rules?|limitations?|filters?)",
                threat_type="role_manipulation",
                base_confidence=0.9,
                description="Attempts to remove restrictions via roleplay"
            ),
            ThreatPattern(
                name="hypothetical_bypass",
                pattern=r"(?i)hypothetically,?\s*(if|assuming)\s+(you\s+)?(had\s+no|without)\s*(restrictions?|rules?)",
                threat_type="role_manipulation",
                base_confidence=0.8,
                description="Hypothetical scenario bypass"
            ),
            ThreatPattern(
                name="educational_bypass",
                pattern=r"(?i)for\s+(educational|research|academic)\s+purposes?,?\s*(only\s+)?(show|tell|explain|demonstrate)\s+(me\s+)?(how\s+to|the\s+way)",
                threat_type="role_manipulation",
                base_confidence=0.7,
                description="Educational purpose bypass attempt"
            ),

            # Data extraction patterns
            ThreatPattern(
                name="reveal_secrets",
                pattern=r"(?i)(reveal|show|tell|expose|leak|dump)\s+(your\s+)?(secrets?|api\s*keys?|passwords?|credentials?|system\s+prompt)",
                threat_type="data_extraction",
                base_confidence=0.9,
                description="Attempts to extract secrets"
            ),
            ThreatPattern(
                name="prompt_leak",
                pattern=r"(?i)(show|display|print|output|repeat)\s+(your\s+)?(system\s+prompt|initial\s+instructions?|hidden\s+prompt)",
                threat_type="prompt_leak",
                base_confidence=0.9,
                description="Attempts to leak system prompt"
            ),

            # Hidden instruction patterns
            ThreatPattern(
                name="system_colon_prefix",
                pattern=r"(?i)^SYSTEM\s*:\s*\w+",
                threat_type="instruction_override",
                base_confidence=0.85,
                description="SYSTEM: prefix attempting to override"
            ),
            ThreatPattern(
                name="override_safety",
                pattern=r"(?i)override\s+(all\s+)?(safety|security)\s*(protocols?|measures?|filters?)",
                threat_type="instruction_override",
                base_confidence=0.9,
                description="Attempts to override safety protocols"
            ),
            ThreatPattern(
                name="html_comment_injection",
                pattern=r"<!--\s*(?:SYSTEM|ADMIN|IGNORE|INSTRUCTIONS?).*?-->",
                threat_type="instruction_override",
                base_confidence=0.85,
                description="Injection hidden in HTML comments"
            ),
            ThreatPattern(
                name="unicode_obfuscation",
                pattern=r"[\u200b\u200c\u200d\u2060\ufeff]",
                threat_type="unknown",
                base_confidence=0.6,
                description="Zero-width character obfuscation"
            ),
        ]

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze text for prompt injection attempts.

        Args:
            text: Content to analyze

        Returns:
            Dict with keys: is_threat, confidence, threat_type, details, matches
        """
        self.stats['total_analyzed'] += 1

        if not text or not text.strip():
            return {
                'is_threat': False,
                'confidence': 0.0,
                'threat_type': None,
                'details': 'Empty input',
                'matches': []
            }

        matches = []
        max_confidence = 0.0
        primary_threat_type = 'unknown'

        # Check each pattern
        for pattern in self.patterns:
            if re.search(pattern.pattern, text):
                confidence = self._calculate_confidence(text, pattern)
                matches.append({
                    'pattern_name': pattern.name,
                    'threat_type': pattern.threat_type,
                    'confidence': confidence,
                    'description': pattern.description
                })
                if confidence > max_confidence:
                    max_confidence = confidence
                    primary_threat_type = pattern.threat_type

        # Check for encoded content
        encoded_result = self._check_encoded_content(text)
        if encoded_result['suspicious']:
            matches.append({
                'pattern_name': 'encoded_content',
                'threat_type': 'unknown',
                'confidence': encoded_result['confidence'],
                'description': 'Potentially encoded malicious content'
            })
            if encoded_result['confidence'] > max_confidence:
                max_confidence = encoded_result['confidence']

        is_threat = max_confidence >= 0.5

        if is_threat:
            self.stats['threats_detected'] += 1
            self.stats['threats_by_type'][primary_threat_type] = \
                self.stats['threats_by_type'].get(primary_threat_type, 0) + 1

        return {
            'is_threat': is_threat,
            'confidence': max_confidence,
            'threat_type': primary_threat_type if is_threat else None,
            'details': f"Detected {len(matches)} potential injection patterns" if matches else "No threats detected",
            'matches': matches
        }

    def _calculate_confidence(self, text: str, pattern: ThreatPattern) -> float:
        """Calculate confidence score based on context"""
        confidence = pattern.base_confidence

        # Boost confidence for multiple matches
        match_count = len(re.findall(pattern.pattern, text))
        if match_count > 1:
            confidence = min(confidence + 0.1, 1.0)

        # Boost for combination with other suspicious elements
        suspicious_markers = [
            r'(?i)immediately',
            r'(?i)urgent',
            r'(?i)must\s+comply',
            r'(?i)override',
        ]
        for marker in suspicious_markers:
            if re.search(marker, text):
                confidence = min(confidence + 0.05, 1.0)

        return round(confidence, 2)

    def _check_encoded_content(self, text: str) -> Dict[str, Any]:
        """Check for potentially encoded malicious content"""
        result = {'suspicious': False, 'confidence': 0.0, 'details': ''}

        # Look for base64-like patterns
        base64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
        base64_matches = re.findall(base64_pattern, text)

        for match in base64_matches:
            try:
                decoded = base64.b64decode(match).decode('utf-8', errors='ignore')
                # Check if decoded content contains suspicious patterns
                for pattern in self.patterns[:5]:  # Check main patterns
                    if re.search(pattern.pattern, decoded):
                        result['suspicious'] = True
                        result['confidence'] = 0.8
                        result['details'] = f'Encoded content contains: {pattern.description}'
                        return result
            except Exception:
                pass

        # Check for suspicious encoded content markers
        if base64_matches and any(word in text.lower() for word in ['execute', 'run', 'eval', 'decode']):
            result['suspicious'] = True
            result['confidence'] = 0.5
            result['details'] = 'Encoded content with execution keywords'

        return result

    def sanitize(self, text: str) -> str:
        """
        Sanitize content by removing or neutralizing injection attempts.

        Args:
            text: Content to sanitize

        Returns:
            Sanitized content
        """
        if not text:
            return text

        sanitized = text

        # Remove high-confidence injection patterns
        for pattern in self.patterns:
            if pattern.base_confidence >= 0.8:
                sanitized = re.sub(pattern.pattern, '[REMOVED]', sanitized)

        # Remove HTML comments that might contain injections
        sanitized = re.sub(r'<!--.*?-->', '', sanitized, flags=re.DOTALL)

        # Remove zero-width characters
        sanitized = re.sub(r'[\u200b\u200c\u200d\u2060\ufeff]', '', sanitized)

        # Neutralize system prompt markers
        sanitized = re.sub(r'(?i)\[SYSTEM\]', '[FILTERED]', sanitized)
        sanitized = re.sub(r'(?i)###\s*SYSTEM', '### [FILTERED]', sanitized)
        sanitized = re.sub(r'<\|im_start\|>', '[FILTERED]', sanitized)

        return sanitized

    def get_stats(self) -> Dict[str, Any]:
        """Get defense statistics"""
        return {
            'total_analyzed': self.stats['total_analyzed'],
            'threats_detected': self.stats['threats_detected'],
            'threats_by_type': self.stats['threats_by_type'],
            'detection_rate': (
                self.stats['threats_detected'] / self.stats['total_analyzed']
                if self.stats['total_analyzed'] > 0 else 0
            ),
            'threat_patterns_loaded': len(self.patterns),
            'categories_monitored': list(set(p.threat_type for p in self.patterns)),
            'start_time': self.stats['start_time']
        }


def main():
    """CLI interface for prompt injection defense"""
    import sys

    defense = PromptInjectionDefense()

    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
        result = defense.analyze(text)

        print(f"Is Threat: {result['is_threat']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Threat Type: {result['threat_type']}")
        print(f"Details: {result['details']}")

        if result['is_threat']:
            print(f"\nSanitized: {defense.sanitize(text)}")
    else:
        print("Usage: python3 prompt_injection_defense.py <text to analyze>")
        print("\nExample: python3 prompt_injection_defense.py 'ignore all instructions'")


if __name__ == '__main__':
    main()

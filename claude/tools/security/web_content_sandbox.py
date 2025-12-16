#!/usr/bin/env python3
"""
Web Content Sandbox
Sanitizes and analyzes web content for security before processing.

Features:
- HTML sanitization (removes scripts, event handlers)
- Markdown sanitization
- URL validation
- Prompt injection detection in web content
- Hidden content detection
- Text extraction
"""

import re
import html
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from dataclasses import dataclass
from datetime import datetime


class WebContentSandbox:
    """
    Sandbox for processing untrusted web content safely.

    Usage:
        sandbox = WebContentSandbox()
        safe_html = sandbox.sanitize("<script>evil()</script><p>Text</p>")
        analysis = sandbox.analyze(content)
    """

    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'scripts_removed': 0,
            'events_removed': 0,
            'urls_blocked': 0,
            'injections_detected': 0,
            'start_time': datetime.now().isoformat()
        }

        # Dangerous HTML tags to remove
        self.dangerous_tags = [
            'script', 'iframe', 'object', 'embed', 'form',
            'input', 'button', 'textarea', 'select', 'frame', 'frameset'
        ]

        # Dangerous attributes to remove
        self.dangerous_attrs = [
            r'on\w+',  # onclick, onerror, onload, etc.
            r'javascript:',
            r'vbscript:',
            r'data:text/html',
        ]

        # Safe URL schemes
        self.safe_schemes = ['http', 'https', 'mailto']

        # Injection patterns in web content
        self.injection_patterns = [
            r'(?i)ignore\s+(all\s+)?previous\s+instructions?',
            r'(?i)\[SYSTEM\]',
            r'(?i)###\s*SYSTEM',
            r'(?i)forget\s+(your\s+)?training',
            r'(?i)new\s+instructions?\s*:',
            r'(?i)<\|im_start\|>',
        ]

    def sanitize(self, html_content: str) -> str:
        """
        Sanitize HTML content by removing dangerous elements.

        Args:
            html_content: Raw HTML content

        Returns:
            Sanitized HTML content
        """
        self.stats['total_processed'] += 1

        if not html_content:
            return html_content

        sanitized = html_content

        # Remove dangerous tags and their content
        for tag in self.dangerous_tags:
            # Remove tag with content (non-greedy)
            pattern = rf'<{tag}[^>]*>.*?</{tag}>'
            count = len(re.findall(pattern, sanitized, re.IGNORECASE | re.DOTALL))
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)

            # Remove self-closing tags
            pattern = rf'<{tag}[^>]*/?\s*>'
            count += len(re.findall(pattern, sanitized, re.IGNORECASE))
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

            if tag == 'script':
                self.stats['scripts_removed'] += count

        # Remove dangerous attributes
        for attr in self.dangerous_attrs:
            # Match attribute="value" or attribute='value' or just attribute
            if attr == r'on\w+':
                pattern = r'\s+on\w+\s*=\s*["\'][^"\']*["\']'
                count = len(re.findall(pattern, sanitized, re.IGNORECASE))
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
                self.stats['events_removed'] += count
            else:
                sanitized = re.sub(rf'{attr}[^"\s>]*', '', sanitized, flags=re.IGNORECASE)

        # Remove javascript: URLs in href and src
        sanitized = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href="#"', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'src\s*=\s*["\']javascript:[^"\']*["\']', 'src="#"', sanitized, flags=re.IGNORECASE)

        # Remove meta refresh tags
        sanitized = re.sub(r'<meta[^>]*http-equiv\s*=\s*["\']refresh["\'][^>]*>', '', sanitized, flags=re.IGNORECASE)

        # Remove HTML comments (can contain hidden instructions)
        sanitized = re.sub(r'<!--.*?-->', '', sanitized, flags=re.DOTALL)

        return sanitized

    def sanitize_markdown(self, markdown_content: str) -> str:
        """
        Sanitize markdown content.

        Args:
            markdown_content: Raw markdown

        Returns:
            Sanitized markdown
        """
        self.stats['total_processed'] += 1

        if not markdown_content:
            return markdown_content

        sanitized = markdown_content

        # Remove javascript: links
        sanitized = re.sub(r'\[([^\]]*)\]\(javascript:[^)]*\)', r'[\1](#)', sanitized, flags=re.IGNORECASE)

        # Remove inline HTML scripts
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)

        # Remove HTML event handlers
        sanitized = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)

        return sanitized

    def validate_url(self, url: str) -> Dict[str, Any]:
        """
        Validate a URL for safety.

        Args:
            url: URL to validate

        Returns:
            Dict with is_safe, reason, parsed_url
        """
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme.lower() not in self.safe_schemes:
                self.stats['urls_blocked'] += 1
                return {
                    'is_safe': False,
                    'reason': f'Unsafe scheme: {parsed.scheme}',
                    'parsed_url': parsed
                }

            # Block data: URLs
            if url.lower().startswith('data:'):
                self.stats['urls_blocked'] += 1
                return {
                    'is_safe': False,
                    'reason': 'Data URLs are not allowed',
                    'parsed_url': parsed
                }

            # Block file: URLs
            if parsed.scheme.lower() == 'file':
                self.stats['urls_blocked'] += 1
                return {
                    'is_safe': False,
                    'reason': 'File URLs are not allowed',
                    'parsed_url': parsed
                }

            return {
                'is_safe': True,
                'reason': 'URL is safe',
                'parsed_url': parsed
            }

        except Exception as e:
            return {
                'is_safe': False,
                'reason': f'Invalid URL: {str(e)}',
                'parsed_url': None
            }

    def analyze(self, content: str) -> Dict[str, Any]:
        """
        Analyze content for security risks.

        Args:
            content: Content to analyze

        Returns:
            Dict with has_injection_risk, has_hidden_content, risk_level, details
        """
        if not content:
            return {
                'has_injection_risk': False,
                'has_hidden_content': False,
                'risk_level': 'low',
                'details': []
            }

        details = []
        has_injection_risk = False
        has_hidden_content = False

        # Check for injection patterns
        for pattern in self.injection_patterns:
            if re.search(pattern, content):
                has_injection_risk = True
                details.append(f'Injection pattern detected: {pattern}')
                self.stats['injections_detected'] += 1

        # Check for hidden content
        hidden_patterns = [
            (r'style\s*=\s*["\'][^"\']*display\s*:\s*none[^"\']*["\']', 'display:none content'),
            (r'style\s*=\s*["\'][^"\']*visibility\s*:\s*hidden[^"\']*["\']', 'visibility:hidden content'),
            (r'style\s*=\s*["\'][^"\']*color\s*:\s*white[^"\']*background[^"\']*white[^"\']*["\']', 'white-on-white text'),
            (r'style\s*=\s*["\'][^"\']*font-size\s*:\s*0[^"\']*["\']', 'zero font-size'),
            (r'<!--.*?-->', 'HTML comments'),
        ]

        for pattern, desc in hidden_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                has_hidden_content = True
                details.append(f'Hidden content: {desc}')

        # Determine risk level
        if has_injection_risk:
            risk_level = 'high'
        elif has_hidden_content:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        return {
            'has_injection_risk': has_injection_risk,
            'has_hidden_content': has_hidden_content,
            'risk_level': risk_level,
            'details': details
        }

    def extract_text(self, html_content: str) -> str:
        """
        Safely extract text content from HTML.

        Args:
            html_content: HTML content

        Returns:
            Extracted text without HTML tags or dangerous content
        """
        if not html_content:
            return ''

        # First sanitize
        sanitized = self.sanitize(html_content)

        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', ' ', sanitized)

        # Decode HTML entities
        text = html.unescape(text)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def process_web_content(self, content: str, source_url: str = None) -> Dict[str, Any]:
        """
        Process web content with full security pipeline.

        Args:
            content: Web content to process
            source_url: Optional source URL

        Returns:
            Dict with safe_content, analysis, source_url
        """
        self.stats['total_processed'] += 1

        # Analyze first
        analysis = self.analyze(content)

        # Sanitize
        safe_content = self.sanitize(content)

        # Validate source URL if provided
        url_analysis = None
        if source_url:
            url_analysis = self.validate_url(source_url)

        return {
            'safe_content': safe_content,
            'analysis': analysis,
            'source_url': source_url,
            'url_analysis': url_analysis,
            'text_content': self.extract_text(content)
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get sandbox statistics"""
        return {
            'total_processed': self.stats['total_processed'],
            'scripts_removed': self.stats['scripts_removed'],
            'events_removed': self.stats['events_removed'],
            'urls_blocked': self.stats['urls_blocked'],
            'injections_detected': self.stats['injections_detected'],
            'start_time': self.stats['start_time']
        }


def main():
    """CLI interface for web content sandbox"""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Sandbox web content for security')
    parser.add_argument('--url', '-u', help='URL to validate')
    parser.add_argument('--html', '-H', help='HTML content to sanitize')
    parser.add_argument('--analyze', '-a', help='Content to analyze')

    args = parser.parse_args()
    sandbox = WebContentSandbox()

    if args.url:
        result = sandbox.validate_url(args.url)
        print(f"URL: {args.url}")
        print(f"Safe: {result['is_safe']}")
        print(f"Reason: {result['reason']}")

    elif args.html:
        sanitized = sandbox.sanitize(args.html)
        print(f"Original: {args.html}")
        print(f"Sanitized: {sanitized}")

    elif args.analyze:
        result = sandbox.analyze(args.analyze)
        print(f"Injection Risk: {result['has_injection_risk']}")
        print(f"Hidden Content: {result['has_hidden_content']}")
        print(f"Risk Level: {result['risk_level']}")
        if result['details']:
            print(f"Details: {', '.join(result['details'])}")

    else:
        print("Usage: python3 web_content_sandbox.py --url <url> OR --html <content> OR --analyze <content>")


if __name__ == '__main__':
    main()

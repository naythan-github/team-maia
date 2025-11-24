#!/usr/bin/env python3
"""
Output Validator - Agentic AI Enhancement Phase 2

Implements automated output validation:
  CURRENT: Generate -> Return to user
  AGENTIC: Generate -> Validate -> Fix if needed -> Return

Key Features:
- Code outputs: syntax check, basic validation
- Config outputs: JSON/YAML validation, schema check
- Documentation: completeness check
- Security: credential/secret detection

Author: Maia System
Created: 2025-11-24 (Agentic AI Enhancement Project - Phase 2)
"""

import ast
import json
import re
from typing import Dict, List, Optional, Any


class OutputValidator:
    """
    Automated Output Validation System.

    Validates code, configuration, and documentation outputs
    before delivery to catch errors proactively.
    """

    # Patterns for security checks
    SECRET_PATTERNS = [
        r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[\w\-]{20,}',
        r'(?i)(password|passwd|pwd)\s*[=:]\s*["\'][^"\']+["\']',
        r'(?i)(secret|token)\s*[=:]\s*["\']?[\w\-]{16,}',
        r'(?i)sk-[a-zA-Z0-9]{24,}',  # OpenAI-style keys
        r'(?i)ghp_[a-zA-Z0-9]{36}',  # GitHub tokens
        r'(?i)xox[baprs]-[\w-]+',  # Slack tokens
    ]

    # Dangerous SQL patterns
    DANGEROUS_SQL = [
        r'(?i)\bDROP\s+(TABLE|DATABASE|INDEX)',
        r'(?i)\bTRUNCATE\s+TABLE',
        r'(?i)\bDELETE\s+FROM\s+\w+\s*;?\s*$',  # DELETE without WHERE
        r'(?i)\bUPDATE\s+\w+\s+SET\s+.*;\s*$',  # UPDATE without WHERE
    ]

    def __init__(self):
        """Initialize Output Validator"""
        pass

    def validate_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Validate code syntax.

        Args:
            code: Code string to validate
            language: Programming language

        Returns:
            Dict with validation results
        """
        if language.lower() == "python":
            return self._validate_python(code)
        elif language.lower() in ("bash", "sh", "shell"):
            return self._validate_bash(code)
        else:
            return {'valid': True, 'errors': [], 'warnings': [], 'language': language}

    def _validate_python(self, code: str) -> Dict[str, Any]:
        """Validate Python syntax"""
        errors = []
        warnings = []

        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append({
                'type': 'syntax_error',
                'line': e.lineno,
                'message': str(e.msg),
                'text': e.text
            })

        # Check for common issues
        if 'import *' in code:
            warnings.append("Wildcard import detected - may cause namespace pollution")

        if re.search(r'\bexec\s*\(', code):
            warnings.append("exec() usage detected - potential security risk")

        if re.search(r'\beval\s*\(', code):
            warnings.append("eval() usage detected - potential security risk")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'language': 'python'
        }

    def _validate_bash(self, code: str) -> Dict[str, Any]:
        """Basic bash validation"""
        errors = []
        warnings = []

        # Check for unclosed quotes
        single_quotes = code.count("'") - code.count("\\'")
        double_quotes = code.count('"') - code.count('\\"')

        if single_quotes % 2 != 0:
            errors.append({'type': 'syntax_error', 'message': 'Unclosed single quote'})
        if double_quotes % 2 != 0:
            errors.append({'type': 'syntax_error', 'message': 'Unclosed double quote'})

        # Check for dangerous commands
        if re.search(r'rm\s+-rf\s+/', code):
            warnings.append("Dangerous rm -rf command detected")

        if re.search(r'>\s*/dev/sd[a-z]', code):
            warnings.append("Direct device write detected")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'language': 'bash'
        }

    def validate_json(self, json_str: str) -> Dict[str, Any]:
        """
        Validate JSON syntax.

        Args:
            json_str: JSON string to validate

        Returns:
            Dict with validation results
        """
        try:
            parsed = json.loads(json_str)
            return {
                'valid': True,
                'errors': [],
                'parsed': parsed
            }
        except json.JSONDecodeError as e:
            return {
                'valid': False,
                'errors': [{
                    'type': 'json_error',
                    'line': e.lineno,
                    'column': e.colno,
                    'message': e.msg
                }],
                'parsed': None
            }

    def validate_yaml(self, yaml_str: str) -> Dict[str, Any]:
        """
        Validate YAML syntax.

        Args:
            yaml_str: YAML string to validate

        Returns:
            Dict with validation results
        """
        try:
            import yaml
            parsed = yaml.safe_load(yaml_str)
            return {
                'valid': True,
                'errors': [],
                'parsed': parsed
            }
        except ImportError:
            # Fallback to basic checks if PyYAML not available
            errors = []
            lines = yaml_str.split('\n')
            indent_stack = [0]

            for i, line in enumerate(lines, 1):
                if line.strip() and not line.strip().startswith('#'):
                    # Get indentation
                    indent = len(line) - len(line.lstrip())
                    # Check for tabs
                    if '\t' in line[:indent]:
                        errors.append({
                            'type': 'yaml_error',
                            'line': i,
                            'message': 'Tabs not allowed in YAML indentation'
                        })

            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'parsed': None
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [{'type': 'yaml_error', 'message': str(e)}],
                'parsed': None
            }

    def validate_sql(self, sql: str) -> Dict[str, Any]:
        """
        Validate SQL for safety.

        Args:
            sql: SQL string to validate

        Returns:
            Dict with validation results
        """
        warnings = []

        for pattern in self.DANGEROUS_SQL:
            if re.search(pattern, sql):
                match = re.search(pattern, sql)
                warnings.append(f"Dangerous SQL pattern detected: {match.group(0)}")

        # Check for missing WHERE on DELETE/UPDATE
        if re.search(r'(?i)\bDELETE\s+FROM\b', sql) and not re.search(r'(?i)\bWHERE\b', sql):
            warnings.append("DELETE without WHERE clause detected")

        if re.search(r'(?i)\bUPDATE\s+\w+\s+SET\b', sql) and not re.search(r'(?i)\bWHERE\b', sql):
            warnings.append("UPDATE without WHERE clause detected")

        return {
            'valid': True,  # SQL syntax checking would need a parser
            'warnings': warnings,
            'safe': len(warnings) == 0
        }

    def validate_documentation(self, doc: str) -> Dict[str, Any]:
        """
        Validate documentation completeness.

        Args:
            doc: Documentation text

        Returns:
            Dict with completeness score and issues
        """
        score = 0.0
        issues = []
        sections_found = []

        # Check for title/header
        if re.search(r'^#\s+\w', doc, re.MULTILINE):
            score += 0.2
            sections_found.append('title')
        else:
            issues.append("Missing main title")

        # Check for overview/description
        if re.search(r'(?i)(overview|description|introduction|about)', doc):
            score += 0.15
            sections_found.append('overview')

        # Check for usage/examples
        if re.search(r'(?i)(usage|example|how to)', doc):
            score += 0.15
            sections_found.append('usage')

        # Check for code examples
        if re.search(r'```\w*\n', doc):
            score += 0.2
            sections_found.append('code_examples')
        else:
            issues.append("No code examples found")

        # Check for parameters/arguments section
        if re.search(r'(?i)(parameter|argument|option|flag)', doc):
            score += 0.15
            sections_found.append('parameters')

        # Check for returns/output section
        if re.search(r'(?i)(return|output|result)', doc):
            score += 0.15
            sections_found.append('returns')

        return {
            'complete': score >= 0.7,
            'score': score,
            'sections_found': sections_found,
            'issues': issues
        }

    def validate_config(self, config: Dict, schema: Dict) -> Dict[str, Any]:
        """
        Validate config against schema.

        Args:
            config: Configuration dict
            schema: JSON Schema dict

        Returns:
            Dict with validation results
        """
        errors = []

        # Basic schema validation
        if schema.get('type') == 'object':
            # Check required fields
            for req in schema.get('required', []):
                if req not in config:
                    errors.append(f"Missing required field: {req}")

            # Check property types
            for prop, prop_schema in schema.get('properties', {}).items():
                if prop in config:
                    value = config[prop]
                    expected_type = prop_schema.get('type')

                    if expected_type == 'string' and not isinstance(value, str):
                        errors.append(f"Field '{prop}' should be string")
                    elif expected_type == 'integer' and not isinstance(value, int):
                        errors.append(f"Field '{prop}' should be integer")
                    elif expected_type == 'boolean' and not isinstance(value, bool):
                        errors.append(f"Field '{prop}' should be boolean")
                    elif expected_type == 'array' and not isinstance(value, list):
                        errors.append(f"Field '{prop}' should be array")

                    # Check bounds
                    if isinstance(value, (int, float)):
                        if 'minimum' in prop_schema and value < prop_schema['minimum']:
                            errors.append(f"Field '{prop}' below minimum ({prop_schema['minimum']})")
                        if 'maximum' in prop_schema and value > prop_schema['maximum']:
                            errors.append(f"Field '{prop}' above maximum ({prop_schema['maximum']})")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def security_check(self, content: str) -> Dict[str, Any]:
        """
        Check content for security issues.

        Args:
            content: Content to check

        Returns:
            Dict with security findings
        """
        issues = []

        for pattern in self.SECRET_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                issues.append({
                    'type': 'hardcoded_secret',
                    'pattern': pattern[:30] + '...',
                    'count': len(matches)
                })

        return {
            'safe': len(issues) == 0,
            'issues': issues
        }

    def extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from markdown text.

        Args:
            text: Markdown text

        Returns:
            List of code blocks with language
        """
        pattern = r'```(\w*)\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)

        return [
            {'language': m[0] or 'unknown', 'code': m[1].strip()}
            for m in matches
        ]

    def validate_output(self, output: str) -> Dict[str, Any]:
        """
        Validate complete output with auto-detection.

        Args:
            output: Full output text

        Returns:
            Dict with validation results
        """
        code_blocks = self.extract_code_blocks(output)
        validations = []
        all_valid = True

        for block in code_blocks:
            lang = block['language'].lower()
            code = block['code']

            if lang in ('python', 'py'):
                result = self.validate_code(code, 'python')
            elif lang in ('json',):
                result = self.validate_json(code)
            elif lang in ('yaml', 'yml'):
                result = self.validate_yaml(code)
            elif lang in ('bash', 'sh', 'shell'):
                result = self.validate_code(code, 'bash')
            elif lang in ('sql',):
                result = self.validate_sql(code)
            else:
                result = {'valid': True, 'language': lang}

            validations.append({
                'language': lang,
                'valid': result.get('valid', True),
                'errors': result.get('errors', []),
                'warnings': result.get('warnings', [])
            })

            if not result.get('valid', True):
                all_valid = False

        # Security check on full output
        security = self.security_check(output)

        return {
            'code_blocks': code_blocks,
            'validations': validations,
            'all_valid': all_valid and security['safe'],
            'security': security
        }

    def validate_full_response(self, response: str) -> Dict[str, Any]:
        """
        Comprehensive validation of an agent response.

        Args:
            response: Full response text

        Returns:
            Dict with complete validation results
        """
        # Validate code blocks
        output_validation = self.validate_output(response)

        # Validate documentation quality
        doc_validation = self.validate_documentation(response)

        # Security check
        security = self.security_check(response)

        # Overall assessment
        overall_valid = (
            output_validation['all_valid'] and
            security['safe']
        )

        return {
            'overall_valid': overall_valid,
            'code_validations': output_validation['validations'],
            'code_blocks_count': len(output_validation['code_blocks']),
            'doc_score': doc_validation['score'],
            'doc_complete': doc_validation['complete'],
            'security_safe': security['safe'],
            'security_issues': security['issues']
        }


def main():
    """CLI for output validator"""
    import argparse

    parser = argparse.ArgumentParser(description="Output Validator")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Validate command
    val_parser = subparsers.add_parser('validate', help='Validate output')
    val_parser.add_argument('--file', '-f', help='File to validate')
    val_parser.add_argument('--text', '-t', help='Text to validate')
    val_parser.add_argument('--type', choices=['python', 'json', 'yaml', 'sql', 'full'],
                           default='full', help='Validation type')

    # Security command
    sec_parser = subparsers.add_parser('security', help='Security check')
    sec_parser.add_argument('--file', '-f', help='File to check')
    sec_parser.add_argument('--text', '-t', help='Text to check')

    args = parser.parse_args()

    validator = OutputValidator()

    if args.command == 'validate':
        if args.file:
            with open(args.file, 'r') as f:
                content = f.read()
        elif args.text:
            content = args.text
        else:
            print("Provide --file or --text")
            return 1

        if args.type == 'python':
            result = validator.validate_code(content, 'python')
        elif args.type == 'json':
            result = validator.validate_json(content)
        elif args.type == 'yaml':
            result = validator.validate_yaml(content)
        elif args.type == 'sql':
            result = validator.validate_sql(content)
        else:
            result = validator.validate_full_response(content)

        status = "✅ Valid" if result.get('valid', result.get('overall_valid', True)) else "❌ Invalid"
        print(f"{status}")

        if result.get('errors'):
            print("\nErrors:")
            for e in result['errors']:
                print(f"  - {e}")

    elif args.command == 'security':
        if args.file:
            with open(args.file, 'r') as f:
                content = f.read()
        elif args.text:
            content = args.text
        else:
            print("Provide --file or --text")
            return 1

        result = validator.security_check(content)
        status = "✅ Safe" if result['safe'] else "⚠️  Issues Found"
        print(f"{status}")

        if result['issues']:
            print("\nSecurity Issues:")
            for issue in result['issues']:
                print(f"  - {issue['type']}: {issue.get('count', 1)} occurrence(s)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

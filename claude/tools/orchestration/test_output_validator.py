#!/usr/bin/env python3
"""
Unit Tests for Output Validator

Phase 2 Agentic AI Enhancement: Automated Output Validation
Tests code, config, and documentation validation.
"""

import unittest
import tempfile
import os


class TestOutputValidator(unittest.TestCase):
    """Test OutputValidator class"""

    def setUp(self):
        """Create validator instance"""
        from output_validator import OutputValidator
        self.validator = OutputValidator()

    def test_initialization(self):
        """Test validator initializes correctly"""
        self.assertIsNotNone(self.validator)

    def test_validate_python_syntax_valid(self):
        """Test validating valid Python code"""
        code = '''
def hello():
    print("Hello, World!")
    return True

class MyClass:
    def __init__(self):
        self.value = 42
'''
        result = self.validator.validate_code(code, language="python")

        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)

    def test_validate_python_syntax_invalid(self):
        """Test detecting invalid Python syntax"""
        code = '''
def broken(
    print("missing close paren"
'''
        result = self.validator.validate_code(code, language="python")

        self.assertFalse(result['valid'])
        self.assertGreater(len(result['errors']), 0)

    def test_validate_json_valid(self):
        """Test validating valid JSON"""
        json_str = '{"name": "test", "value": 123, "nested": {"key": "value"}}'

        result = self.validator.validate_json(json_str)

        self.assertTrue(result['valid'])

    def test_validate_json_invalid(self):
        """Test detecting invalid JSON"""
        json_str = '{"name": "test", "value": 123,}'  # trailing comma

        result = self.validator.validate_json(json_str)

        self.assertFalse(result['valid'])

    def test_validate_yaml_valid(self):
        """Test validating valid YAML"""
        yaml_str = '''
name: test
config:
  key: value
  list:
    - item1
    - item2
'''
        result = self.validator.validate_yaml(yaml_str)

        self.assertTrue(result['valid'])

    def test_validate_yaml_invalid(self):
        """Test detecting invalid YAML"""
        yaml_str = '''
name: test
  bad_indent: value
 worse: here
'''
        result = self.validator.validate_yaml(yaml_str)

        self.assertFalse(result['valid'])

    def test_validate_shell_script(self):
        """Test validating shell script"""
        script = '''#!/bin/bash
echo "Hello"
if [ -f /tmp/test ]; then
    echo "File exists"
fi
'''
        result = self.validator.validate_code(script, language="bash")

        # Basic validation should pass
        self.assertTrue(result['valid'])

    def test_validate_documentation_complete(self):
        """Test validating complete documentation"""
        doc = '''
# Feature Documentation

## Overview
This feature does X, Y, and Z.

## Usage
Here's how to use it:

```python
from feature import Feature
f = Feature()
f.run()
```

## Parameters
- param1: Description
- param2: Description

## Returns
The output value.

## Examples
See the code block above.
'''
        result = self.validator.validate_documentation(doc)

        self.assertTrue(result['complete'])
        self.assertGreater(result['score'], 0.7)

    def test_validate_documentation_incomplete(self):
        """Test detecting incomplete documentation"""
        doc = '''
# Feature

Does something.
'''
        result = self.validator.validate_documentation(doc)

        self.assertFalse(result['complete'])
        self.assertLess(result['score'], 0.5)

    def test_validate_output_auto_detect_python(self):
        """Test auto-detection of Python code"""
        output = '''
Here's the solution:

```python
def solve():
    return 42
```
'''
        result = self.validator.validate_output(output)

        self.assertIn('code_blocks', result)
        self.assertGreater(len(result['code_blocks']), 0)

    def test_validate_output_auto_detect_json(self):
        """Test auto-detection of JSON in output"""
        output = '''
Here's the configuration:

```json
{"name": "test", "enabled": true}
```
'''
        result = self.validator.validate_output(output)

        self.assertTrue(result['all_valid'])

    def test_validate_sql_safe(self):
        """Test validating safe SQL"""
        sql = '''
SELECT u.name, u.email
FROM users u
WHERE u.active = true
ORDER BY u.created_at DESC
LIMIT 100;
'''
        result = self.validator.validate_sql(sql)

        self.assertTrue(result['valid'])
        self.assertEqual(len(result['warnings']), 0)

    def test_validate_sql_dangerous(self):
        """Test detecting dangerous SQL"""
        sql = 'DROP TABLE users;'

        result = self.validator.validate_sql(sql)

        self.assertGreater(len(result['warnings']), 0)

    def test_validate_config_schema(self):
        """Test validating config against schema"""
        config = {"name": "test", "port": 8080, "enabled": True}
        schema = {
            "type": "object",
            "required": ["name", "port"],
            "properties": {
                "name": {"type": "string"},
                "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "enabled": {"type": "boolean"}
            }
        }

        result = self.validator.validate_config(config, schema)

        self.assertTrue(result['valid'])

    def test_validate_config_schema_violation(self):
        """Test detecting schema violation"""
        config = {"name": "test", "port": "not_a_number"}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "port": {"type": "integer"}
            }
        }

        result = self.validator.validate_config(config, schema)

        self.assertFalse(result['valid'])

    def test_security_check_no_secrets(self):
        """Test security check passes for clean code"""
        code = '''
import os
api_key = os.environ.get("API_KEY")
'''
        result = self.validator.security_check(code)

        self.assertTrue(result['safe'])

    def test_security_check_hardcoded_secret(self):
        """Test security check catches hardcoded secrets"""
        code = '''
api_key = "sk-1234567890abcdefghijklmnop"
password = "supersecret123"
'''
        result = self.validator.security_check(code)

        self.assertFalse(result['safe'])
        self.assertGreater(len(result['issues']), 0)

    def test_validate_full_response(self):
        """Test validating full agent response"""
        response = '''
## Solution

Here's how to fix the issue:

1. First, update the configuration:

```yaml
server:
  port: 8080
  host: localhost
```

2. Then update the code:

```python
def main():
    config = load_config()
    return config
```

This should resolve the problem.
'''
        result = self.validator.validate_full_response(response)

        self.assertIn('overall_valid', result)
        self.assertIn('code_validations', result)
        self.assertIn('doc_score', result)


class TestCodeBlockExtraction(unittest.TestCase):
    """Test code block extraction"""

    def setUp(self):
        from output_validator import OutputValidator
        self.validator = OutputValidator()

    def test_extract_single_block(self):
        """Test extracting single code block"""
        text = '''
Some text

```python
print("hello")
```

More text
'''
        blocks = self.validator.extract_code_blocks(text)

        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]['language'], 'python')

    def test_extract_multiple_blocks(self):
        """Test extracting multiple code blocks"""
        text = '''
```python
x = 1
```

```javascript
const y = 2;
```

```json
{"key": "value"}
```
'''
        blocks = self.validator.extract_code_blocks(text)

        self.assertEqual(len(blocks), 3)


if __name__ == "__main__":
    print("Output Validator Unit Tests")
    print("=" * 60)
    unittest.main(verbosity=2)

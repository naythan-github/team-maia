#!/usr/bin/env python3
"""
Unit Tests for Output Critic System
"""

import unittest
from output_critic import (
    OutputCritic,
    CritiqueResult,
    CritiqueIssue,
    CritiqueCategory
)


class TestOutputCritic(unittest.TestCase):
    """Test OutputCritic class"""

    def setUp(self):
        """Create critic without LLM for testing"""
        self.critic = OutputCritic(use_llm=False)

    def test_initialization(self):
        """Test critic initializes correctly"""
        self.assertIsNotNone(self.critic)
        self.assertEqual(self.critic.threshold, 0.7)
        self.assertFalse(self.critic.use_llm)

    def test_good_output_passes(self):
        """Test that good output passes critique"""
        good_output = """
## Solution

Here's how to solve the problem:

1. First, identify the root cause
2. Then, implement the fix
3. Finally, test the solution

This approach handles the common case and includes error handling
for edge cases like empty input or network failures.

Note: This solution works best for small to medium datasets.
For larger datasets, consider pagination.
"""
        result = self.critic.critique(good_output, {"query": "how to solve the problem"})

        self.assertIsInstance(result, CritiqueResult)
        self.assertGreater(result.overall_score, 0.5)

    def test_detects_todo_markers(self):
        """Test detection of TODO/FIXME markers"""
        output_with_todo = """
Here's the implementation:

def process_data():
    # TODO: implement this
    pass

This will work once completed.
"""
        result = self.critic.critique(output_with_todo)

        todo_issues = [i for i in result.issues
                       if i.category == CritiqueCategory.COMPLETENESS
                       and 'TODO' in i.description.upper()]
        self.assertGreater(len(todo_issues), 0)

    def test_detects_overconfident_claims(self):
        """Test detection of overconfident claims"""
        overconfident_output = """
This solution guarantees 100% success rate and will never fail.
It's absolutely the best approach and definitely works.
"""
        result = self.critic.critique(overconfident_output)

        accuracy_issues = [i for i in result.issues
                          if i.category == CritiqueCategory.ACCURACY]
        self.assertGreater(len(accuracy_issues), 0)

    def test_detects_hardcoded_credentials(self):
        """Test detection of hardcoded credentials"""
        output_with_secrets = """
Here's the configuration:

```python
api_key = "sk-1234567890abcdef"
password = "supersecret123"
```
"""
        result = self.critic.critique(output_with_secrets)

        safety_issues = [i for i in result.issues
                        if i.category == CritiqueCategory.SAFETY]
        self.assertGreater(len(safety_issues), 0)

    def test_detects_dangerous_operations(self):
        """Test detection of dangerous operations without warnings"""
        dangerous_output = """
To clean up, run:

```bash
sudo rm -rf /
```

This will remove all files.
"""
        result = self.critic.critique(dangerous_output)

        safety_issues = [i for i in result.issues
                        if i.category == CritiqueCategory.SAFETY]
        self.assertGreater(len(safety_issues), 0)

    def test_detects_incomplete_sentences(self):
        """Test detection of incomplete sentences"""
        incomplete_output = """
Here's what you need to do:

1. First,
2. Then you should
3. Finally,
"""
        result = self.critic.critique(incomplete_output)

        completeness_issues = [i for i in result.issues
                              if i.category == CritiqueCategory.COMPLETENESS]
        # Should detect the trailing comma
        self.assertGreater(len(completeness_issues), 0)

    def test_actionability_check_for_how_to_queries(self):
        """Test actionability check for action queries"""
        explanation_only = """
This is a complex topic that involves many considerations.
There are various approaches one could take, and the best
choice depends on the specific circumstances. Generally
speaking, it's important to consider all factors.
"""
        context = {"query": "how do I implement this feature?"}
        result = self.critic.critique(explanation_only, context)

        actionability_issues = [i for i in result.issues
                               if i.category == CritiqueCategory.ACTIONABILITY]
        self.assertGreater(len(actionability_issues), 0)

    def test_passes_well_structured_action_response(self):
        """Test that well-structured action response passes"""
        good_action_response = """
Here's how to implement this feature:

1. Create the new module in `src/features/`
2. Add the following code:

```python
def new_feature():
    return "implemented"
```

3. Update the configuration file
4. Run tests to verify

Note: Make sure to backup your data before making changes.
"""
        context = {"query": "how do I implement this feature?"}
        result = self.critic.critique(good_action_response, context)

        # Should have high actionability score
        self.assertGreaterEqual(result.category_scores.get('actionability', 0), 0.8)

    def test_score_calculation(self):
        """Test that score is calculated correctly"""
        # Perfect output should score 1.0
        perfect_output = "This is a clear, complete, and safe response."
        result = self.critic.critique(perfect_output)

        if not result.issues:
            self.assertEqual(result.overall_score, 1.0)

        # Output with issues should score lower
        output_with_issues = "TODO: implement this. It will 100% work."
        result = self.critic.critique(output_with_issues)

        self.assertLess(result.overall_score, 1.0)

    def test_threshold_determines_pass(self):
        """Test that threshold determines pass/fail"""
        output = "This is a simple response."

        # High threshold should fail marginal outputs
        strict_critic = OutputCritic(threshold=0.99, use_llm=False)
        result = strict_critic.critique(output)
        # Score would be 1.0 if no issues, so this should pass
        if result.issues:
            self.assertFalse(result.passed)

        # Low threshold should pass more outputs
        lenient_critic = OutputCritic(threshold=0.3, use_llm=False)
        result = lenient_critic.critique(output)
        self.assertTrue(result.passed)

    def test_refinement_prompt_generated(self):
        """Test refinement prompt is generated when needed"""
        bad_output = """
TODO: finish this

It definitely guarantees success and will never fail.

password = "secret123"
"""
        result = self.critic.critique(bad_output)

        if not result.passed:
            self.assertIsNotNone(result.refinement_prompt)
            self.assertIn("address these issues", result.refinement_prompt.lower())

    def test_category_scores(self):
        """Test that category scores are calculated"""
        output = "This is a test output."
        result = self.critic.critique(output)

        self.assertIn('completeness', result.category_scores)
        self.assertIn('accuracy', result.category_scores)
        self.assertIn('safety', result.category_scores)

        # All scores should be between 0 and 1
        for score in result.category_scores.values():
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)

    def test_result_to_dict(self):
        """Test serialization of result"""
        output = "Test output"
        result = self.critic.critique(output)

        result_dict = result.to_dict()

        self.assertIn('output_hash', result_dict)
        self.assertIn('overall_score', result_dict)
        self.assertIn('passed', result_dict)
        self.assertIn('issues', result_dict)
        self.assertIsInstance(result_dict['issues'], list)


class TestCritiqueIssue(unittest.TestCase):
    """Test CritiqueIssue dataclass"""

    def test_issue_creation(self):
        issue = CritiqueIssue(
            category=CritiqueCategory.COMPLETENESS,
            severity="high",
            description="Test issue",
            suggestion="Fix it"
        )

        self.assertEqual(issue.category, CritiqueCategory.COMPLETENESS)
        self.assertEqual(issue.severity, "high")
        self.assertIsNone(issue.location)


class TestCritiqueCategory(unittest.TestCase):
    """Test CritiqueCategory enum"""

    def test_all_categories_exist(self):
        categories = [
            CritiqueCategory.COMPLETENESS,
            CritiqueCategory.ACCURACY,
            CritiqueCategory.EDGE_CASES,
            CritiqueCategory.ACTIONABILITY,
            CritiqueCategory.CLARITY,
            CritiqueCategory.SAFETY
        ]

        for cat in categories:
            self.assertIsNotNone(cat.value)


if __name__ == "__main__":
    print("🧪 Output Critic Unit Tests")
    print("=" * 60)
    unittest.main(verbosity=2)

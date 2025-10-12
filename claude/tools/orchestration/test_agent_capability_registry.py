"""
Test Suite for Agent Capability Registry

Tests:
1. Capability extraction from agent markdown
2. Registry discovery and indexing
3. Domain/skill/tool search
4. Query-to-agent matching
5. Scoring accuracy
6. Integration with Coordinator Agent
"""

import sys
from pathlib import Path

# Add orchestration directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_capability_registry import (
    CapabilityExtractor,
    CapabilityRegistry,
    AgentCapability,
    create_registry,
    match_agent
)


class TestCapabilityExtractor:
    """Test capability extraction from markdown"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.extractor = CapabilityExtractor()

    def test_agent_name_extraction(self):
        """Test 1: Extract agent name from filename"""
        test_cases = [
            ("dns_specialist_agent_v2.md", "dns_specialist"),
            ("azure_solutions_architect_agent.md", "azure_solutions_architect"),
            ("service_desk_manager_agent_v1.md", "service_desk_manager"),
        ]

        for filename, expected in test_cases:
            result = self.extractor._extract_agent_name(filename.replace('.md', ''))
            assert result == expected, f"Expected {expected}, got {result}"

        print("✅ Test 1: Agent name extraction - PASSED")
        self.passed += 1

    def test_version_detection(self):
        """Test 2: Detect agent version"""
        assert self.extractor._detect_version("agent_v2") == "v2"
        assert self.extractor._detect_version("agent_v1") == "v1"
        assert self.extractor._detect_version("agent") == "base"

        print("✅ Test 2: Version detection - PASSED")
        self.passed += 1

    def test_domain_extraction(self):
        """Test 3: Extract domains from content"""
        content = """
        This agent specializes in DNS configuration, SPF records, and DKIM authentication.
        It also handles Azure integration and security compliance.
        """

        domains = self.extractor._extract_domains(content)

        assert 'dns' in domains, f"Expected 'dns', got {domains}"
        assert 'azure' in domains, f"Expected 'azure', got {domains}"
        assert 'security' in domains, f"Expected 'security', got {domains}"

        print("✅ Test 3: Domain extraction - PASSED")
        self.passed += 1

    def test_skill_extraction(self):
        """Test 4: Extract skills from content"""
        content = """
        Expert at troubleshooting email issues, configuring authentication systems.
        Specializes in migration projects, architecture design, and automation.
        """

        skills = self.extractor._extract_skills(content)

        # Check for at least 3 skills
        assert len(skills) >= 3, f"Expected at least 3 skills, got {len(skills)}: {skills}"
        assert 'migration' in skills, f"Expected 'migration', got {skills}"
        assert 'architecture' in skills, f"Expected 'architecture', got {skills}"

        print("✅ Test 4: Skill extraction - PASSED")
        self.passed += 1

    def test_handoff_detection(self):
        """Test 5: Detect handoff capability"""
        content_with_handoff = "HANDOFF DECLARATION: To azure_solutions_architect"
        content_without_handoff = "Just a regular agent without handoffs"

        assert self.extractor._has_handoff_support(content_with_handoff) == True
        assert self.extractor._has_handoff_support(content_without_handoff) == False

        print("✅ Test 5: Handoff detection - PASSED")
        self.passed += 1

    def run_all(self):
        """Run all extractor tests"""
        print("\n=== CapabilityExtractor Test Suite ===\n")

        tests = [
            self.test_agent_name_extraction,
            self.test_version_detection,
            self.test_domain_extraction,
            self.test_skill_extraction,
            self.test_handoff_detection,
        ]

        for test in tests:
            try:
                test()
            except AssertionError as e:
                print(f"❌ {test.__doc__} - FAILED: {e}")
                self.failed += 1
            except Exception as e:
                print(f"❌ {test.__doc__} - ERROR: {e}")
                self.failed += 1

        print(f"\nCapabilityExtractor: {self.passed} passed, {self.failed} failed\n")
        return self.failed == 0


class TestCapabilityRegistry:
    """Test registry discovery and search"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.registry = create_registry()

    def test_agent_discovery(self):
        """Test 6: Discover agents from directory"""
        assert len(self.registry.capabilities) > 0, "No agents discovered"
        assert len(self.registry.capabilities) >= 40, f"Expected 40+ agents, got {len(self.registry.capabilities)}"

        print(f"✅ Test 6: Agent discovery - PASSED ({len(self.registry.capabilities)} agents)")
        self.passed += 1

    def test_domain_index(self):
        """Test 7: Domain indexing"""
        assert len(self.registry.domain_index) > 0, "No domains indexed"

        # Check specific domains exist
        assert 'dns' in self.registry.domain_index
        assert 'azure' in self.registry.domain_index
        assert 'security' in self.registry.domain_index

        print(f"✅ Test 7: Domain indexing - PASSED ({len(self.registry.domain_index)} domains)")
        self.passed += 1

    def test_find_by_domain(self):
        """Test 8: Find agents by domain"""
        dns_agents = self.registry.find_by_domain('dns')

        assert len(dns_agents) > 0, "No DNS agents found"
        assert any('dns' in agent.agent_name for agent in dns_agents), "Expected DNS specialist"

        print(f"✅ Test 8: Find by domain - PASSED ({len(dns_agents)} DNS agents)")
        self.passed += 1

    def test_find_by_skill(self):
        """Test 9: Find agents by skill"""
        migration_agents = self.registry.find_by_skill('migration')

        assert len(migration_agents) > 0, "No migration specialists found"

        print(f"✅ Test 9: Find by skill - PASSED ({len(migration_agents)} migration agents)")
        self.passed += 1

    def test_registry_stats(self):
        """Test 10: Registry statistics"""
        stats = self.registry.get_stats()

        assert 'total_agents' in stats
        assert 'domains' in stats
        assert 'handoff_capable' in stats
        assert stats['total_agents'] > 0

        print(f"✅ Test 10: Registry stats - PASSED")
        print(f"    Total agents: {stats['total_agents']}")
        print(f"    Handoff capable: {stats['handoff_capable']}")
        self.passed += 1

    def run_all(self):
        """Run all registry tests"""
        print("\n=== CapabilityRegistry Test Suite ===\n")

        tests = [
            self.test_agent_discovery,
            self.test_domain_index,
            self.test_find_by_domain,
            self.test_find_by_skill,
            self.test_registry_stats,
        ]

        for test in tests:
            try:
                test()
            except AssertionError as e:
                print(f"❌ {test.__doc__} - FAILED: {e}")
                self.failed += 1
            except Exception as e:
                print(f"❌ {test.__doc__} - ERROR: {e}")
                self.failed += 1

        print(f"\nCapabilityRegistry: {self.passed} passed, {self.failed} failed\n")
        return self.failed == 0


class TestCapabilityMatching:
    """Test query-to-agent matching"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.registry = create_registry()

    def test_dns_query_matching(self):
        """Test 11: DNS query matches DNS specialist"""
        query = "Setup email authentication with SPF and DKIM"
        matches = self.registry.match_query(query, top_k=3, min_score=0.4)

        assert len(matches) > 0, "No matches found"

        # DNS specialist should be in top 3
        top_agents = [name for name, score in matches]
        assert 'dns_specialist' in top_agents, f"DNS specialist not in top 3: {top_agents}"

        print(f"✅ Test 11: DNS query matching - PASSED")
        print(f"    Top match: {matches[0][0]} ({matches[0][1]:.3f})")
        self.passed += 1

    def test_azure_query_matching(self):
        """Test 12: Azure query matches Azure architect"""
        query = "Migrate users to Azure Exchange Online"
        matches = self.registry.match_query(query, top_k=3, min_score=0.4)

        assert len(matches) > 0, "No matches found"

        # Azure architect should be in top 3
        top_agents = [name for name, score in matches]
        has_azure = any('azure' in agent.lower() for agent in top_agents)
        assert has_azure, f"No Azure agent in top 3: {top_agents}"

        print(f"✅ Test 12: Azure query matching - PASSED")
        print(f"    Top match: {matches[0][0]} ({matches[0][1]:.3f})")
        self.passed += 1

    def test_cloud_architecture_matching(self):
        """Test 13: Cloud architecture query"""
        query = "Design cloud architecture for enterprise"
        matches = self.registry.match_query(query, top_k=3, min_score=0.4)

        assert len(matches) > 0, "No matches found"

        # Cloud architect should be top
        top_agent = matches[0][0]
        assert 'cloud' in top_agent.lower() or 'architect' in top_agent.lower(), \
            f"Expected cloud/architect, got {top_agent}"

        print(f"✅ Test 13: Cloud architecture matching - PASSED")
        print(f"    Top match: {matches[0][0]} ({matches[0][1]:.3f})")
        self.passed += 1

    def test_score_ranking(self):
        """Test 14: Scores are properly ranked"""
        query = "Setup DNS records"
        matches = self.registry.match_query(query, top_k=5, min_score=0.3)

        assert len(matches) >= 2, "Need at least 2 matches for ranking test"

        # Scores should be descending
        scores = [score for name, score in matches]
        assert scores == sorted(scores, reverse=True), "Scores not properly ranked"

        print(f"✅ Test 14: Score ranking - PASSED")
        self.passed += 1

    def test_min_score_threshold(self):
        """Test 15: Min score threshold works"""
        query = "xyz unknown query 123"
        matches = self.registry.match_query(query, top_k=5, min_score=0.8)

        # High threshold should filter most matches
        # (Unknown query unlikely to score >0.8)
        assert len(matches) < 5, f"Expected few matches with high threshold, got {len(matches)}"

        print(f"✅ Test 15: Min score threshold - PASSED")
        self.passed += 1

    def run_all(self):
        """Run all matching tests"""
        print("\n=== CapabilityMatching Test Suite ===\n")

        tests = [
            self.test_dns_query_matching,
            self.test_azure_query_matching,
            self.test_cloud_architecture_matching,
            self.test_score_ranking,
            self.test_min_score_threshold,
        ]

        for test in tests:
            try:
                test()
            except AssertionError as e:
                print(f"❌ {test.__doc__} - FAILED: {e}")
                self.failed += 1
            except Exception as e:
                print(f"❌ {test.__doc__} - ERROR: {e}")
                self.failed += 1

        print(f"\nCapabilityMatching: {self.passed} passed, {self.failed} failed\n")
        return self.failed == 0


def main():
    """Run all test suites"""
    print("=" * 70)
    print("AGENT CAPABILITY REGISTRY - TEST SUITE")
    print("=" * 70)

    # Run test suites
    extractor_tests = TestCapabilityExtractor()
    extractor_passed = extractor_tests.run_all()

    registry_tests = TestCapabilityRegistry()
    registry_passed = registry_tests.run_all()

    matching_tests = TestCapabilityMatching()
    matching_passed = matching_tests.run_all()

    # Summary
    total_passed = extractor_tests.passed + registry_tests.passed + matching_tests.passed
    total_failed = extractor_tests.failed + registry_tests.failed + matching_tests.failed

    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {total_passed / (total_passed + total_failed) * 100:.1f}%")
    print("=" * 70)

    if total_failed == 0:
        print("\n✅ ALL TESTS PASSED\n")
        return 0
    else:
        print(f"\n❌ {total_failed} TESTS FAILED\n")
        return 1


if __name__ == '__main__':
    exit(main())

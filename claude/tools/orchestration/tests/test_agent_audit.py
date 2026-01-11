"""
Tests for Feature 5.2: Agent Collaboration Audit (F020)
Scan all agents and report collaboration coverage.
"""

def test_scan_agents_for_collaborations():
    """Scan all agents and find those with Collaborations."""
    from claude.tools.orchestration.agent_audit import scan_agent_collaborations

    report = scan_agent_collaborations()

    assert "total_agents" in report
    assert "agents_with_collaborations" in report
    assert "agents_missing_collaborations" in report
    assert report["total_agents"] > 0

def test_audit_reports_coverage_percentage():
    """Audit calculates collaboration coverage percentage."""
    from claude.tools.orchestration.agent_audit import scan_agent_collaborations

    report = scan_agent_collaborations()

    assert "coverage_percentage" in report
    assert 0 <= report["coverage_percentage"] <= 100

def test_audit_identifies_key_agents_missing_collaborations():
    """Identify high-priority agents missing collaborations."""
    from claude.tools.orchestration.agent_audit import get_priority_agents_missing_collaborations

    # Priority agents that should have collaborations
    priority_agents = ["sre_principal_engineer", "security_specialist", "azure_solutions_architect"]

    missing = get_priority_agents_missing_collaborations(priority_agents)
    # Returns list of priority agents that need collaborations added
    assert isinstance(missing, list)

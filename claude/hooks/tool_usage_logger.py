#!/usr/bin/env python3
"""
Tool Usage Logger Hook
=====================

Integrates with Claude Code to automatically log tool usage events.
Called by user-prompt-submit hook to track actual tool utilization.
"""

import sys
import re
import json
from datetime import datetime
from pathlib import Path

# Add tools directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

try:
    from tool_usage_monitor import get_tool_monitor
except ImportError:
    print("Warning: tool_usage_monitor not available")
    sys.exit(0)

def extract_tool_usage_from_message(message: str) -> list:
    """
    Extract tool usage patterns from user message and system context
    """
    tools_used = []

    # Pattern matching for different tool invocation styles
    patterns = {
        'bash_command': r'(?:run|execute|bash).*?`([^`]+)`',
        'python_script': r'python3?\s+([^\s]+\.py)',
        'agent_invocation': r'(?:use|invoke|call).*?(agent|specialist)',
        'mcp_function': r'mcp__\w+__(\w+)',
        'command_execution': r'(?:command|cmd):\s*(\w+)',
        'file_operation': r'(?:read|write|edit).*?([^\s]+\.\w+)',
    }

    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, message.lower())
        for match in matches:
            tools_used.append({
                'name': match,
                'type': pattern_name,
                'context': message[:200],  # First 200 chars for context
            })

    return tools_used

def log_message_tools(message: str, response_context: str = ""):
    """
    Log tool usage based on message content
    """
    monitor = get_tool_monitor()
    tools_detected = extract_tool_usage_from_message(message)

    for tool_info in tools_detected:
        monitor.log_tool_usage(
            tool_name=tool_info['name'],
            tool_type=tool_info['type'],
            tool_path="",  # Path detection would require more context
            context=tool_info['context'],
            success=True,  # Assume success unless we have error info
            duration_seconds=None
        )

def main():
    """Main hook execution"""
    if len(sys.argv) < 2:
        return

    user_message = sys.argv[1]

    # Log tools mentioned in the user message
    log_message_tools(user_message)

    # Output usage guidance based on message analysis
    monitor = get_tool_monitor()

    # Check for tool discovery requirements
    research_keywords = ['research', 'analyze', 'investigate', 'study', 'explore']
    security_keywords = ['security', 'audit', 'scan', 'vulnerability', 'compliance']
    job_keywords = ['job', 'linkedin', 'resume', 'career', 'application']

    message_lower = user_message.lower()

    if any(keyword in message_lower for keyword in research_keywords):
        print("🔍 RESEARCH DOMAIN DETECTED")
        print("   📋 Available: researcher_agent.md, holiday_research_agent.md")
        print("   🐍 Tools: web_research_suite.py, market_intelligence_system.py")
        print("   ⚠️  Consider specialized research agents before generic tools")

    elif any(keyword in message_lower for keyword in security_keywords):
        print("🔒 SECURITY DOMAIN DETECTED")
        print("   📋 Available: security_review, vulnerability_scan, compliance_check")
        print("   🐍 Tools: local_security_scanner.py, secret_detector.py")
        print("   🤖 Agent: security_specialist_agent.md")
        print("   ⚠️  Use specialized security tools - avoid generic approaches")

    elif any(keyword in message_lower for keyword in job_keywords):
        print("💼 JOB SEARCH DOMAIN DETECTED")
        print("   📋 Available: complete_job_analyzer, automated_job_scraper")
        print("   🐍 Tools: batch_job_scraper.py, enhanced_profile_scorer.py")
        print("   🤖 Agents: jobs_agent.md, linkedin_optimizer.md")
        print("   ⚠️  Use job-specific tools for optimal results")

if __name__ == "__main__":
    main()

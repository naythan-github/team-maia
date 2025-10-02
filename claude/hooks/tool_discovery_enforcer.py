#!/usr/bin/env python3
"""
Tool Discovery Enforcement Hook
===============================

Forces systematic checking of existing tools before defaulting to generic approaches.
Addresses context utilization failure where tools are loaded but not used.

Hook triggers when specific patterns detected in user requests.
"""

import re
from pathlib import Path
from typing import List, Dict, Set

class ToolDiscoveryEnforcer:
    """Enforces systematic tool discovery before generic approaches"""

    def __init__(self):
        self.maia_root = Path(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))

        # Comprehensive domain triggers
        self.domain_triggers = {
            "security": {
                "security", "audit", "scan", "vulnerability", "compliance",
                "penetration", "assessment", "review", "analysis"
            },
            "research": {
                "research", "analyze", "investigate", "study", "migration",
                "comparison", "issues", "problems", "explore", "examine"
            },
            "job_search": {
                "job", "application", "linkedin", "resume", "career",
                "interview", "company", "role", "position", "employment"
            },
            "financial": {
                "financial", "investment", "tax", "superannuation", "money",
                "budget", "planning", "wealth", "portfolio", "savings"
            },
            "content": {
                "blog", "write", "content", "article", "documentation",
                "communication", "marketing", "strategy", "copy"
            },
            "technical": {
                "code", "development", "programming", "deployment",
                "infrastructure", "system", "technical", "engineering"
            }
        }

        self.tool_directories = {
            "security": self.maia_root / "claude/tools/security",
            "commands": self.maia_root / "claude/commands",
            "tools": self.maia_root / "claude/tools",
            "agents": self.maia_root / "claude/agents"
        }

    def detect_request_domain(self, request: str) -> Set[str]:
        """Detect what domain the user request falls into"""
        request_lower = request.lower()
        domains = set()

        # Check all domain triggers
        for domain, triggers in self.domain_triggers.items():
            if any(trigger in request_lower for trigger in triggers):
                domains.add(domain)

        return domains

    def get_available_tools(self, domain: str) -> Dict[str, List[str]]:
        """Get available tools for specific domain"""
        tools = {
            "commands": [],
            "python_tools": [],
            "agents": [],
            "specialized_dirs": []
        }

        domain_triggers = self.domain_triggers.get(domain, set())

        # Find domain-specific commands
        commands_dir = self.maia_root / "claude/commands"
        if commands_dir.exists():
            domain_commands = [
                f.stem for f in commands_dir.glob("*.md")
                if any(trigger in f.stem.lower() for trigger in domain_triggers)
            ]
            tools["commands"] = domain_commands

        # Find domain-specific agents
        agents_dir = self.maia_root / "claude/agents"
        if agents_dir.exists():
            domain_agents = [
                f.stem for f in agents_dir.glob("*.md")
                if any(trigger in f.stem.lower() for trigger in domain_triggers)
            ]

            # Add specific agent mappings for known domains
            if domain == "research":
                # Add research-capable agents
                research_agents = ["researcher", "holiday_research_agent", "company_research_agent", "blog_writer_agent"]
                for agent in research_agents:
                    agent_file = agents_dir / f"{agent}.md"
                    if agent_file.exists() and agent not in domain_agents:
                        domain_agents.append(agent)

            elif domain == "job_search":
                job_agents = ["jobs_agent", "linkedin_optimizer", "company_research_agent", "interview_prep_agent"]
                for agent in job_agents:
                    agent_file = agents_dir / f"{agent}.md"
                    if agent_file.exists() and agent not in domain_agents:
                        domain_agents.append(agent)

            elif domain == "financial":
                financial_agents = ["financial_advisor_agent", "financial_planner_agent"]
                for agent in financial_agents:
                    agent_file = agents_dir / f"{agent}.md"
                    if agent_file.exists() and agent not in domain_agents:
                        domain_agents.append(agent)

            tools["agents"] = domain_agents

        # Find domain-specific tools and directories
        if domain == "security":
            security_dir = self.maia_root / "claude/tools/security"
            if security_dir.exists():
                py_tools = [f.stem for f in security_dir.glob("*.py")]
                tools["python_tools"] = py_tools
                tools["specialized_dirs"].append("claude/tools/security/")

        # Add general tools directory scanning
        tools_dir = self.maia_root / "claude/tools"
        if tools_dir.exists():
            domain_py_tools = [
                f.stem for f in tools_dir.glob("*.py")
                if any(trigger in f.stem.lower() for trigger in domain_triggers)
            ]
            tools["python_tools"].extend(domain_py_tools)

        return tools

    def generate_enforcement_message(self, domain: str, available_tools: Dict) -> str:
        """Generate enforcement message for systematic tool checking"""
        message = f"""
🚨 TOOL DISCOVERY ENFORCEMENT TRIGGERED 🚨

Request Domain Detected: {domain.upper()}

🔍 BEFORE using generic approaches, you MUST check these existing tools:

"""

        if available_tools["commands"]:
            message += f"📋 Available Commands ({len(available_tools['commands'])}):\n"
            for cmd in available_tools["commands"]:
                message += f"   - {cmd}\n"
            message += "\n"

        if available_tools["python_tools"]:
            message += f"🐍 Available Python Tools ({len(available_tools['python_tools'])}):\n"
            for tool in available_tools["python_tools"]:
                message += f"   - {tool}\n"
            message += "\n"

        if available_tools["agents"]:
            message += f"🤖 Available Specialized Agents ({len(available_tools['agents'])}):\n"
            for agent in available_tools["agents"]:
                message += f"   - {agent}\n"
            message += "\n"

        if available_tools["specialized_dirs"]:
            message += f"📁 Specialized Directories:\n"
            for dir_path in available_tools["specialized_dirs"]:
                message += f"   - {dir_path}\n"
            message += "\n"

        message += """⚡ MANDATORY WORKFLOW:
1. ✅ Check existing tools FIRST
2. ✅ Use specialized tools if available
3. ✅ Only use generic approaches if gaps exist
4. ❌ DO NOT default to Task tool without checking

🎯 Follow Maia Principle: "Use Existing Tools First"
"""

        return message

    def check_request(self, user_request: str) -> str:
        """Main hook entry point - check if enforcement needed"""
        domains = self.detect_request_domain(user_request)

        if not domains:
            return ""  # No enforcement needed

        enforcement_messages = []
        for domain in domains:
            tools = self.get_available_tools(domain)
            if any(tools.values()):  # If we have tools available
                enforcement_messages.append(
                    self.generate_enforcement_message(domain, tools)
                )

        return "\n".join(enforcement_messages)

def main():
    """CLI interface for testing"""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python tool_discovery_enforcer.py 'user request'")
        sys.exit(1)

    enforcer = ToolDiscoveryEnforcer()
    result = enforcer.check_request(sys.argv[1])

    if result:
        print(result)
    else:
        print("No enforcement needed for this request")

if __name__ == "__main__":
    main()

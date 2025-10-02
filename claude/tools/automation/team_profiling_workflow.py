#!/usr/bin/env python3
"""
Team Profiling Workflow - Phase 1 Implementation
Leverages existing Maia infrastructure for immediate team intelligence capabilities
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add Maia tools to path
MAIA_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(MAIA_ROOT / "claude" / "tools"))

try:
    from smart_research_manager import SmartResearchManager
    from personal_knowledge_graph import PersonalKnowledgeGraph
except ImportError as e:
    print(f"⚠️  Import error: {e}")
    print("Running in standalone mode")

class TeamProfilingWorkflow:
    """Systematic team member research and profiling workflow"""
    
    def __init__(self):
        self.team_data_dir = MAIA_ROOT / "claude" / "data" / "team_intelligence"
        self.team_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize research manager
        try:
            self.research_manager = SmartResearchManager()
        except:
            self.research_manager = None
            print("⚠️  Smart Research Manager not available")
        
        # Initialize knowledge graph
        try:
            self.knowledge_graph = PersonalKnowledgeGraph()
        except:
            self.knowledge_graph = None
            print("⚠️  Personal Knowledge Graph not available")
    
    def research_team_member(self, name: str, role: str, email: str = None) -> Dict:
        """Research individual team member using existing infrastructure"""
        
        print(f"\n🔍 Researching: {name} ({role})")
        
        profile = {
            "name": name,
            "role": role,
            "email": email,
            "research_date": datetime.now().isoformat(),
            "data_sources": [],
            "professional_background": {},
            "technical_skills": [],
            "experience_level": "Unknown",
            "working_style_indicators": [],
            "key_relationships": [],
            "strengths": [],
            "development_areas": [],
            "strategic_value": ""
        }
        
        # Research using Smart Research Manager if available
        if self.research_manager:
            try:
                # Research professional background
                research_query = f"{name} {role} Orro Group LinkedIn professional background"
                research_results = self.research_manager.research(research_query, category="team_member")
                
                if research_results:
                    profile["professional_background"] = research_results
                    profile["data_sources"].append("Smart Research Manager")
                    
                    # Extract skills and experience from research
                    self._extract_profile_insights(profile, research_results)
                    
            except Exception as e:
                print(f"⚠️  Research error: {e}")
        
        # Store in knowledge graph if available
        if self.knowledge_graph:
            try:
                self.knowledge_graph.add_node(
                    name, 
                    "team_member", 
                    attributes=profile
                )
                profile["data_sources"].append("Knowledge Graph")
            except Exception as e:
                print(f"⚠️  Knowledge graph storage error: {e}")
        
        # Save profile to local storage
        profile_file = self.team_data_dir / f"{name.lower().replace(' ', '_')}_profile.json"
        with open(profile_file, 'w') as f:
            json.dump(profile, f, indent=2)
        
        print(f"✅ Profile saved: {profile_file}")
        return profile
    
    def _extract_profile_insights(self, profile: Dict, research_data: Dict):
        """Extract insights from research data"""
        
        # Simple keyword-based analysis (can be enhanced with LLM)
        text_content = str(research_data).lower()
        
        # Experience level indicators
        if any(word in text_content for word in ["senior", "lead", "principal", "manager"]):
            profile["experience_level"] = "Senior"
        elif any(word in text_content for word in ["junior", "graduate", "entry"]):
            profile["experience_level"] = "Junior"
        else:
            profile["experience_level"] = "Mid"
        
        # Technical skills extraction (basic)
        tech_keywords = [
            "python", "java", "javascript", "react", "azure", "aws", "kubernetes",
            "docker", "terraform", "ansible", "jenkins", "git", "sql", "nosql",
            "microservices", "api", "devops", "cloud", "agile", "scrum"
        ]
        
        found_skills = [skill for skill in tech_keywords if skill in text_content]
        profile["technical_skills"] = found_skills
    
    def analyze_team_dynamics(self) -> Dict:
        """Analyze complete team using stored profiles"""
        
        print("\n📊 Analyzing Team Dynamics...")
        
        # Load all team profiles
        profiles = []
        for profile_file in self.team_data_dir.glob("*_profile.json"):
            with open(profile_file) as f:
                profiles.append(json.load(f))
        
        if not profiles:
            return {"error": "No team profiles found"}
        
        analysis = {
            "team_size": len(profiles),
            "analysis_date": datetime.now().isoformat(),
            "experience_distribution": self._analyze_experience_distribution(profiles),
            "skill_matrix": self._analyze_skill_coverage(profiles),
            "capability_gaps": [],
            "development_opportunities": [],
            "collaboration_insights": [],
            "recommendations": []
        }
        
        # Generate insights
        self._generate_team_insights(analysis, profiles)
        
        # Save analysis
        analysis_file = self.team_data_dir / "team_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"✅ Team analysis saved: {analysis_file}")
        return analysis
    
    def _analyze_experience_distribution(self, profiles: List[Dict]) -> Dict:
        """Analyze experience level distribution"""
        distribution = {"Junior": 0, "Mid": 0, "Senior": 0, "Unknown": 0}
        
        for profile in profiles:
            level = profile.get("experience_level", "Unknown")
            distribution[level] += 1
        
        return distribution
    
    def _analyze_skill_coverage(self, profiles: List[Dict]) -> Dict:
        """Analyze technical skill coverage across team"""
        all_skills = {}
        
        for profile in profiles:
            for skill in profile.get("technical_skills", []):
                all_skills[skill] = all_skills.get(skill, 0) + 1
        
        return dict(sorted(all_skills.items(), key=lambda x: x[1], reverse=True))
    
    def _generate_team_insights(self, analysis: Dict, profiles: List[Dict]):
        """Generate actionable insights from team data"""
        
        # Experience distribution insights
        exp_dist = analysis["experience_distribution"]
        total = analysis["team_size"]
        
        if exp_dist["Senior"] / total < 0.3:
            analysis["recommendations"].append("Consider hiring more senior team members for mentorship")
        
        if exp_dist["Junior"] / total > 0.5:
            analysis["development_opportunities"].append("High mentoring demand - establish buddy system")
        
        # Skill gap analysis
        critical_skills = ["azure", "kubernetes", "terraform", "python"]
        skill_matrix = analysis["skill_matrix"]
        
        for skill in critical_skills:
            coverage = skill_matrix.get(skill, 0) / total
            if coverage < 0.5:
                analysis["capability_gaps"].append(f"Low {skill} coverage ({coverage:.0%})")
    
    def generate_team_report(self) -> str:
        """Generate human-readable team intelligence report"""
        
        # Load analysis
        analysis_file = self.team_data_dir / "team_analysis.json"
        if not analysis_file.exists():
            return "❌ No team analysis found. Run analyze_team_dynamics() first."
        
        with open(analysis_file) as f:
            analysis = json.load(f)
        
        report = f"""
# Team Intelligence Report - Orro Group
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Team Size**: {analysis['team_size']} members

## Experience Distribution
"""
        
        for level, count in analysis["experience_distribution"].items():
            percentage = (count / analysis["team_size"]) * 100
            report += f"- **{level}**: {count} members ({percentage:.0f}%)\n"
        
        report += f"""
## Top Technical Skills
"""
        
        skill_matrix = analysis["skill_matrix"]
        for skill, count in list(skill_matrix.items())[:10]:
            report += f"- **{skill}**: {count} team members\n"
        
        if analysis["capability_gaps"]:
            report += f"\n## Capability Gaps\n"
            for gap in analysis["capability_gaps"]:
                report += f"- ⚠️  {gap}\n"
        
        if analysis["recommendations"]:
            report += f"\n## Recommendations\n"
            for rec in analysis["recommendations"]:
                report += f"- 💡 {rec}\n"
        
        return report
    
    def list_team_profiles(self):
        """List all stored team profiles"""
        profiles = list(self.team_data_dir.glob("*_profile.json"))
        
        if not profiles:
            print("📝 No team profiles found")
            return
        
        print(f"\n👥 Team Profiles ({len(profiles)} members):")
        for profile_file in profiles:
            with open(profile_file) as f:
                profile = json.load(f)
            
            name = profile["name"]
            role = profile["role"]
            exp_level = profile.get("experience_level", "Unknown")
            skills_count = len(profile.get("technical_skills", []))
            
            print(f"  • {name} ({role}) - {exp_level} level, {skills_count} skills identified")


def main():
    """Command line interface"""
    if len(sys.argv) < 2:
        print("""
Team Profiling Workflow - Phase 1

Usage:
  python3 team_profiling_workflow.py research "Name" "Role" [email]
  python3 team_profiling_workflow.py analyze
  python3 team_profiling_workflow.py report
  python3 team_profiling_workflow.py list

Examples:
  python3 team_profiling_workflow.py research "John Smith" "Senior Cloud Engineer"
  python3 team_profiling_workflow.py analyze
  python3 team_profiling_workflow.py report
        """)
        return
    
    workflow = TeamProfilingWorkflow()
    command = sys.argv[1].lower()
    
    if command == "research":
        if len(sys.argv) < 4:
            print("❌ Usage: research 'Name' 'Role' [email]")
            return
        
        name = sys.argv[2]
        role = sys.argv[3]
        email = sys.argv[4] if len(sys.argv) > 4 else None
        
        profile = workflow.research_team_member(name, role, email)
        print(f"\n✅ Research complete for {name}")
        
    elif command == "analyze":
        analysis = workflow.analyze_team_dynamics()
        print("\n✅ Team analysis complete")
        
    elif command == "report":
        report = workflow.generate_team_report()
        print(report)
        
    elif command == "list":
        workflow.list_team_profiles()
        
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
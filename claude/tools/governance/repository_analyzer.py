#!/usr/bin/env python3
"""
Repository Health Analyzer - Phase 1 Component
Analyzes repository structure and identifies sprawl patterns
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class RepositoryAnalyzer:
    def __init__(self, repo_path: str = str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())):
        self.repo_path = Path(repo_path)
        self.analysis_results = {}
        
    def analyze_structure(self) -> Dict:
        """Comprehensive repository structure analysis"""
        print("🔍 Analyzing repository structure...")
        
        # File count analysis
        file_counts = self._count_files_by_location()
        
        # UFC compliance check
        ufc_compliance = self._check_ufc_compliance()
        
        # Sprawl indicators
        sprawl_indicators = self._identify_sprawl_patterns()
        
        # Tool organization analysis
        tool_analysis = self._analyze_tool_organization()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "repo_path": str(self.repo_path),
            "file_counts": file_counts,
            "ufc_compliance": ufc_compliance,
            "sprawl_indicators": sprawl_indicators,
            "tool_analysis": tool_analysis,
            "health_score": self._calculate_health_score(file_counts, ufc_compliance, sprawl_indicators, tool_analysis)
        }
        
        self.analysis_results = results
        return results
    
    def _count_files_by_location(self) -> Dict:
        """Count files in different repository locations"""
        counts = {
            "root_files": 0,
            "claude_tools": 0,
            "claude_agents": 0,
            "claude_context": 0,
            "archive_files": 0,
            "total_files": 0
        }
        
        for root, dirs, files in os.walk(self.repo_path):
            root_path = Path(root)
            
            # Skip .git directory
            if '.git' in root_path.parts:
                continue
                
            file_count = len(files)
            counts["total_files"] += file_count
            
            # Categorize by location
            if root_path == self.repo_path:
                counts["root_files"] = file_count
            elif "claude/tools" in str(root_path):
                counts["claude_tools"] += file_count
            elif "claude/agents" in str(root_path):
                counts["claude_agents"] += file_count
            elif "claude/context" in str(root_path):
                counts["claude_context"] += file_count
            elif "archive" in str(root_path):
                counts["archive_files"] += file_count
        
        return counts
    
    def _check_ufc_compliance(self) -> Dict:
        """Check UFC system compliance"""
        ufc_file = self.repo_path / "claude/context/ufc_system.md"
        hook_file = self.repo_path / "claude/hooks/user-prompt-submit"
        enforcer_file = self.repo_path / "claude/hooks/context_loading_enforcer.py"
        
        return {
            "ufc_system_exists": ufc_file.exists(),
            "enforcement_hook_exists": hook_file.exists(),
            "context_enforcer_exists": enforcer_file.exists(),
            "ufc_system_accessible": ufc_file.is_file() if ufc_file.exists() else False
        }
    
    def _identify_sprawl_patterns(self) -> List[Dict]:
        """Identify potential sprawl patterns"""
        patterns = []
        
        # Root directory file count
        root_files = list(self.repo_path.glob("*"))
        root_file_count = len([f for f in root_files if f.is_file()])
        
        if root_file_count > 20:
            patterns.append({
                "type": "root_sprawl",
                "severity": "high" if root_file_count > 30 else "medium",
                "count": root_file_count,
                "description": f"{root_file_count} files in root directory (target: <20)"
            })
        
        # Check for archive directories outside proper archive/ structure
        for root, dirs, files in os.walk(self.repo_path):
            relative_root = Path(root).relative_to(self.repo_path)
            
            for dir_name in dirs:
                if any(keyword in dir_name.lower() for keyword in ['archive', 'backup', 'old', 'legacy']):
                    # Allow archives in: archive/, archive/historical/, archive/historical/YYYY/, claude/data/governance_backups/
                    valid_archive_locations = [
                        'archive', 'archive/historical', 'claude/data/governance_backups'
                    ]
                    valid_archive_locations.extend([f'archive/historical/{year}' for year in range(2020, 2030)])
                    
                    # Check if current location is valid
                    is_valid_location = any(
                        str(relative_root).startswith(valid_loc) or str(relative_root) == valid_loc 
                        for valid_loc in valid_archive_locations
                    )
                    
                    if not is_valid_location:
                        patterns.append({
                            "type": "misplaced_archive",
                            "severity": "medium",
                            "path": os.path.join(root, dir_name),
                            "description": f"Archive directory outside archive/ folder: {dir_name}"
                        })
        
        return patterns
    
    def _analyze_tool_organization(self) -> Dict:
        """Analyze tool organization in claude/tools"""
        tools_path = self.repo_path / "claude/tools"
        
        if not tools_path.exists():
            return {"error": "Tools directory not found"}
        
        categories = {}
        total_tools = 0
        
        for category_dir in tools_path.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                tool_count = len([f for f in category_dir.rglob("*.py") if f.is_file()])
                categories[category_dir.name] = tool_count
                total_tools += tool_count
        
        return {
            "total_tools": total_tools,
            "categories": categories,
            "category_count": len(categories)
        }
    
    def _calculate_health_score(self, file_counts: Dict, ufc_compliance: Dict, sprawl_indicators: List, tool_analysis: Dict) -> float:
        """Calculate overall repository health score (0-10)"""
        score = 10.0
        
        # Penalize root file sprawl
        if file_counts["root_files"] > 20:
            penalty = min(3.0, (file_counts["root_files"] - 20) * 0.1)
            score -= penalty
        
        # Penalize missing UFC components
        ufc_components = sum(1 for v in ufc_compliance.values() if v)
        if ufc_components < len(ufc_compliance):
            score -= (len(ufc_compliance) - ufc_components) * 1.0
        
        # Penalize sprawl indicators
        for indicator in sprawl_indicators:
            if indicator["severity"] == "high":
                score -= 2.0
            elif indicator["severity"] == "medium":
                score -= 1.0
            else:
                score -= 0.5
        
        # Bonus for good tool organization
        if tool_analysis.get("category_count", 0) >= 8:
            score += 0.5
        
        return max(0.0, min(10.0, score))
    
    def save_analysis(self, output_path: str = None) -> str:
        """Save analysis results to file"""
        if not output_path:
            output_path = str(Path(__file__).parent.parent.parent / "data" / f"repository_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)
        
        return output_path
    
    def print_summary(self):
        """Print analysis summary"""
        if not self.analysis_results:
            print("❌ No analysis results available. Run analyze_structure() first.")
            return
        
        results = self.analysis_results
        
        print("\n" + "="*60)
        print("📊 REPOSITORY HEALTH ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"\n📁 File Counts:")
        for key, value in results['file_counts'].items():
            print(f"   {key}: {value}")
        
        print(f"\n🏛️ UFC Compliance:")
        for key, value in results['ufc_compliance'].items():
            status = "✅" if value else "❌"
            print(f"   {status} {key}: {value}")
        
        print(f"\n⚠️ Sprawl Indicators ({len(results['sprawl_indicators'])}):")
        if results['sprawl_indicators']:
            for pattern in results['sprawl_indicators']:
                severity_icon = "🔴" if pattern['severity'] == 'high' else "🟡"
                print(f"   {severity_icon} {pattern['type']}: {pattern['description']}")
        else:
            print("   ✅ No sprawl indicators detected")
        
        print(f"\n🛠️ Tool Organization:")
        tool_data = results['tool_analysis']
        if "error" not in tool_data:
            print(f"   Total Tools: {tool_data.get('total_tools', 0)}")
            print(f"   Categories: {tool_data.get('category_count', 0)}")
            if tool_data.get('categories'):
                for category, count in tool_data['categories'].items():
                    print(f"   {category}: {count} tools")
        else:
            print(f"   ❌ {tool_data['error']}")
        
        print(f"\n🎯 Health Score: {results['health_score']:.1f}/10.0")
        
        # Health score interpretation
        score = results['health_score']
        if score >= 8.5:
            print("   🟢 Excellent repository health")
        elif score >= 7.0:
            print("   🟡 Good repository health")
        elif score >= 5.0:
            print("   🟠 Fair repository health - some issues need attention")
        else:
            print("   🔴 Poor repository health - immediate action required")
        
        print("="*60)

def main():
    """Main function for CLI usage"""
    analyzer = RepositoryAnalyzer()
    
    print("🚀 Starting Repository Health Analysis...")
    results = analyzer.analyze_structure()
    
    analyzer.print_summary()
    
    # Save results
    output_file = analyzer.save_analysis()
    print(f"\n💾 Analysis saved to: {output_file}")
    
    return results

if __name__ == "__main__":
    main()
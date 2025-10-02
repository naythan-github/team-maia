#!/usr/bin/env python3
"""
Dashboard Repair Project
Systematic analysis and repair of all dashboard files for unified platform compatibility
"""

import os
import re
import ast
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DashboardAnalyzer:
    """Analyzes dashboard files to determine compatibility issues"""
    
    def __init__(self):
        self.maia_root = Path(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))
        self.dashboard_dir = self.maia_root / "claude/tools/📈_monitoring"
        
    def analyze_all_dashboards(self) -> Dict:
        """Analyze all dashboard files"""
        results = {}
        
        # Find all dashboard files
        dashboard_files = list(self.dashboard_dir.glob("*dashboard*.py"))
        dashboard_files = [f for f in dashboard_files if f.name != "unified_dashboard_platform.py"]
        
        logger.info(f"🔍 Analyzing {len(dashboard_files)} dashboard files")
        
        for file_path in dashboard_files:
            name = file_path.stem
            logger.info(f"📊 Analyzing: {name}")
            
            analysis = self.analyze_dashboard_file(file_path)
            results[name] = analysis
            
        return results
    
    def analyze_dashboard_file(self, file_path: Path) -> Dict:
        """Analyze a single dashboard file"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            analysis = {
                'file_path': str(file_path),
                'has_main_function': False,
                'main_function_type': None,
                'has_web_server': False,
                'server_framework': None,
                'port_handling': 'hardcoded',
                'service_mode_support': False,
                'environment_variable_support': False,
                'startup_method': None,
                'issues': [],
                'dependencies': [],
                'repair_needed': True
            }
            
            # Check for main function
            if 'def main(' in content:
                analysis['has_main_function'] = True
                analysis['main_function_type'] = self.detect_main_function_type(content)
                
            # Check for web server frameworks
            if 'from flask import' in content or 'Flask(' in content:
                analysis['has_web_server'] = True
                analysis['server_framework'] = 'flask'
            elif 'from dash import' in content or 'dash.Dash(' in content:
                analysis['has_web_server'] = True
                analysis['server_framework'] = 'dash'
            elif 'from streamlit' in content:
                analysis['has_web_server'] = True
                analysis['server_framework'] = 'streamlit'
                
            # Check port handling
            if 'DASHBOARD_PORT' in content or 'MAIA_DASHBOARD_PORT' in content:
                analysis['port_handling'] = 'environment_variable'
                analysis['environment_variable_support'] = True
                
            # Check service mode support
            if '--service-mode' in content or 'service_mode' in content:
                analysis['service_mode_support'] = True
                
            # Detect startup method
            analysis['startup_method'] = self.detect_startup_method(content)
            
            # Identify issues
            analysis['issues'] = self.identify_issues(analysis, content)
            
            # Extract dependencies
            analysis['dependencies'] = self.extract_dependencies(content)
            
            # Determine if repair is needed
            analysis['repair_needed'] = len(analysis['issues']) > 0
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze {file_path}: {e}")
            return {'error': str(e), 'repair_needed': True}
    
    def detect_main_function_type(self, content: str) -> str:
        """Detect what type of main function this is"""
        main_match = re.search(r'def main\(.*?\):(.*?)(?=\n\S|\Z)', content, re.DOTALL)
        if not main_match:
            return 'unknown'
            
        main_content = main_match.group(1)
        
        if 'argparse' in main_content or 'ArgumentParser' in main_content:
            return 'cli_tool'
        elif '.run(' in main_content or 'run_dashboard' in main_content:
            return 'web_server'
        elif 'print(' in main_content and '.run(' not in main_content:
            return 'demo_script'
        else:
            return 'other'
    
    def detect_startup_method(self, content: str) -> Optional[str]:
        """Detect how the dashboard starts its web server"""
        if '.run(' in content:
            if 'app.run(' in content:
                return 'flask_app_run'
            elif 'dashboard.run(' in content:
                return 'dashboard_run_method'
            else:
                return 'generic_run_method'
        elif 'run_dashboard(' in content:
            return 'run_dashboard_method'
        elif 'streamlit' in content:
            return 'streamlit_app'
        else:
            return None
    
    def identify_issues(self, analysis: Dict, content: str) -> List[str]:
        """Identify compatibility issues"""
        issues = []
        
        if not analysis['has_main_function']:
            issues.append("Missing main() function")
            
        if not analysis['has_web_server']:
            issues.append("No web server framework detected")
            
        if analysis['port_handling'] == 'hardcoded':
            issues.append("Uses hardcoded port instead of environment variables")
            
        if not analysis['service_mode_support'] and analysis['has_web_server']:
            issues.append("Missing --service-mode support")
            
        if analysis['main_function_type'] == 'cli_tool' and analysis['has_web_server']:
            issues.append("CLI tool structure but has web server capabilities")
            
        if analysis['main_function_type'] == 'demo_script':
            issues.append("Demo script, not configured as web service")
            
        # Check for missing if __name__ == "__main__" guard
        if 'if __name__ == "__main__":' not in content:
            issues.append("Missing if __name__ == '__main__' guard")
            
        return issues
    
    def extract_dependencies(self, content: str) -> List[str]:
        """Extract import dependencies"""
        dependencies = []
        
        # Find all import statements
        import_lines = re.findall(r'^(?:from|import)\s+([^\s\n]+)', content, re.MULTILINE)
        
        for imp in import_lines:
            if '.' in imp:
                base_package = imp.split('.')[0]
            else:
                base_package = imp
                
            if base_package not in ['os', 'sys', 'json', 'time', 'datetime', 'pathlib', 're']:
                dependencies.append(base_package)
                
        return list(set(dependencies))

class DashboardRepairer:
    """Repairs dashboard files for unified platform compatibility"""
    
    def __init__(self):
        self.maia_root = Path(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))
        
    def repair_dashboard(self, name: str, analysis: Dict) -> bool:
        """Repair a single dashboard"""
        logger.info(f"🔧 Repairing dashboard: {name}")
        
        file_path = Path(analysis['file_path'])
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            original_content = content
            
            # Apply repairs based on analysis
            if "Uses hardcoded port instead of environment variables" in analysis['issues']:
                content = self.fix_port_handling(content, analysis)
                
            if "Missing --service-mode support" in analysis['issues']:
                content = self.add_service_mode_support(content, analysis)
                
            if "Missing if __name__ == '__main__' guard" in analysis['issues']:
                content = self.add_main_guard(content)
                
            if analysis['main_function_type'] == 'demo_script':
                content = self.convert_demo_to_service(content, analysis)
                
            # Only write if changes were made
            if content != original_content:
                # Create backup
                backup_path = file_path.with_suffix('.py.backup')
                with open(backup_path, 'w') as f:
                    f.write(original_content)
                    
                # Write repaired version
                with open(file_path, 'w') as f:
                    f.write(content)
                    
                logger.info(f"✅ Repaired {name} (backup: {backup_path.name})")
                return True
            else:
                logger.info(f"ℹ️  No changes needed for {name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to repair {name}: {e}")
            return False
    
    def fix_port_handling(self, content: str, analysis: Dict) -> str:
        """Fix hardcoded port handling"""
        # Add environment variable imports if missing
        if "import os" not in content and "from os import" not in content:
            content = "import os\n" + content
            
        # Find and replace hardcoded port in main function
        if analysis['startup_method'] == 'flask_app_run':
            content = re.sub(
                r'def main\(\):',
                '''def main():
    """Main entry point"""
    import os''',
                content
            )
            
            # Replace hardcoded port in run calls
            content = re.sub(
                r'\.run\([^)]*port=\d+[^)]*\)',
                lambda m: m.group(0).replace('port=8050', 'port=int(os.environ.get("DASHBOARD_PORT", 8050))').replace('port=8051', 'port=int(os.environ.get("DASHBOARD_PORT", 8051))'),
                content
            )
            
        return content
    
    def add_service_mode_support(self, content: str, analysis: Dict) -> str:
        """Add --service-mode support to dashboard"""
        if analysis['server_framework'] in ['flask', 'dash']:
            # Find main function and modify it
            main_pattern = r'(def main\(\):.*?)(if __name__)'
            
            service_mode_code = '''
    # Check for service mode
    service_mode = "--service-mode" in sys.argv
    
    if service_mode:
        # Running as service - start dashboard server directly
        host = os.environ.get('DASHBOARD_HOST', '127.0.0.1')
        port = int(os.environ.get('DASHBOARD_PORT', '8050'))
        
        dashboard = ''' + self.get_dashboard_class_name(content) + '''()
        dashboard.run(host=host, port=port, debug=False)
    else:
        # Normal execution
'''
            
            replacement = r'\1' + service_mode_code + r'\2'
            content = re.sub(main_pattern, replacement, content, flags=re.DOTALL)
            
        return content
    
    def add_main_guard(self, content: str) -> str:
        """Add if __name__ == '__main__' guard"""
        if 'if __name__ == "__main__":' not in content:
            content += '''

if __name__ == "__main__":
    main()
'''
        return content
    
    def convert_demo_to_service(self, content: str, analysis: Dict) -> str:
        """Convert demo script to web service"""
        # This is more complex and depends on the specific dashboard
        # For now, just ensure it has proper structure
        return content
    
    def get_dashboard_class_name(self, content: str) -> str:
        """Extract the main dashboard class name"""
        class_match = re.search(r'class ([A-Z][A-Za-z]*Dashboard[A-Za-z]*)', content)
        if class_match:
            return class_match.group(1)
        return "Dashboard"

def main():
    """Main repair project execution"""
    print("🔧 Dashboard Repair Project")
    print("=" * 50)
    
    # Initialize components
    analyzer = DashboardAnalyzer()
    repairer = DashboardRepairer()
    
    # Analyze all dashboards
    print("\n📊 PHASE 1: ANALYSIS")
    print("-" * 20)
    
    results = analyzer.analyze_all_dashboards()
    
    # Print analysis summary
    print(f"\n📋 ANALYSIS SUMMARY")
    print("-" * 20)
    
    for name, analysis in results.items():
        if 'error' in analysis:
            print(f"❌ {name}: Analysis failed - {analysis['error']}")
            continue
            
        status = "✅" if not analysis['repair_needed'] else "🔧"
        print(f"{status} {name}:")
        print(f"   Type: {analysis['main_function_type']}")
        print(f"   Framework: {analysis.get('server_framework', 'none')}")
        print(f"   Port Handling: {analysis['port_handling']}")
        print(f"   Service Mode: {'✅' if analysis['service_mode_support'] else '❌'}")
        
        if analysis['issues']:
            print(f"   Issues: {', '.join(analysis['issues'])}")
        print()
    
    # Repair dashboards
    print("\n🔧 PHASE 2: REPAIR")
    print("-" * 20)
    
    repaired_count = 0
    for name, analysis in results.items():
        if 'error' in analysis or not analysis['repair_needed']:
            continue
            
        if repairer.repair_dashboard(name, analysis):
            repaired_count += 1
    
    print(f"\n✅ REPAIR COMPLETE")
    print(f"Repaired {repaired_count} dashboards")
    print("\n🧪 Next step: Test all dashboards with unified platform")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Dashboard Test Suite
Comprehensive testing of all dashboard files for functionality and integration
"""

import os
import time
import json
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DashboardTester:
    """Tests dashboard functionality and unified platform integration"""
    
    def __init__(self):
        self.maia_root = Path(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))
        self.dashboard_dir = self.maia_root / "claude/tools/📈_monitoring"
        self.platform_url = "http://127.0.0.1:8100"
        
    def test_all_dashboards(self) -> Dict:
        """Test all dashboards through unified platform"""
        logger.info("🧪 Starting Dashboard Test Suite")
        
        # Get list of dashboards from platform
        dashboards = self.get_registered_dashboards()
        
        results = {}
        for dashboard in dashboards:
            name = dashboard['name']
            if name == 'dashboard_repair_project':
                continue  # Skip our repair tool
                
            logger.info(f"🔬 Testing dashboard: {name}")
            result = self.test_dashboard(name, dashboard)
            results[name] = result
            
        return results
    
    def get_registered_dashboards(self) -> List[Dict]:
        """Get list of registered dashboards from platform"""
        try:
            response = requests.get(f"{self.platform_url}/api/dashboards", timeout=5)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get dashboard list: {e}")
            return []
    
    def test_dashboard(self, name: str, config: Dict) -> Dict:
        """Test individual dashboard"""
        result = {
            'name': name,
            'port': config['port'],
            'start_success': False,
            'health_check_success': False,
            'web_accessible': False,
            'content_loaded': False,
            'stop_success': False,
            'errors': [],
            'start_time': None,
            'response_time': None
        }
        
        try:
            # Test dashboard startup
            start_time = time.time()
            start_response = requests.post(
                f"{self.platform_url}/api/dashboard/{name}/start", 
                timeout=10
            )
            
            if start_response.status_code == 200:
                result['start_success'] = True
                result['start_time'] = time.time() - start_time
                
                # Wait for dashboard to initialize
                time.sleep(3)
                
                # Test health check
                health_response = requests.get(
                    f"{self.platform_url}/api/dashboard/{name}/health",
                    timeout=5
                )
                
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    result['health_check_success'] = health_data.get('healthy', False)
                    
                # Test direct web access
                web_start_time = time.time()
                try:
                    dashboard_response = requests.get(
                        f"http://127.0.0.1:{config['port']}", 
                        timeout=10
                    )
                    
                    if dashboard_response.status_code == 200:
                        result['web_accessible'] = True
                        result['response_time'] = time.time() - web_start_time
                        
                        # Check if content looks like a dashboard
                        content = dashboard_response.text.lower()
                        if any(keyword in content for keyword in ['dashboard', 'html', 'chart', 'graph', 'data']):
                            result['content_loaded'] = True
                            
                except Exception as e:
                    result['errors'].append(f"Web access failed: {e}")
                    
                # Test dashboard shutdown
                stop_response = requests.post(
                    f"{self.platform_url}/api/dashboard/{name}/stop",
                    timeout=5
                )
                
                if stop_response.status_code == 200:
                    result['stop_success'] = True
                    
            else:
                result['errors'].append(f"Start failed: HTTP {start_response.status_code}")
                
        except Exception as e:
            result['errors'].append(f"Test failed: {e}")
            
        return result
    
    def test_individual_dashboard_file(self, file_path: Path) -> Dict:
        """Test dashboard file individually (without platform)"""
        result = {
            'file_path': str(file_path),
            'syntax_valid': False,
            'imports_valid': False,
            'main_function_exists': False,
            'can_instantiate': False,
            'errors': []
        }
        
        try:
            # Test syntax
            with open(file_path, 'r') as f:
                content = f.read()
                
            compile(content, str(file_path), 'exec')
            result['syntax_valid'] = True
            
            # Test imports (basic check)
            try:
                import subprocess
                proc = subprocess.run(
                    ['python3', '-c', f'import sys; sys.path.insert(0, "{self.dashboard_dir}"); import {file_path.stem}'],
                    capture_output=True,
                    timeout=10,
                    cwd=self.maia_root
                )
                
                if proc.returncode == 0:
                    result['imports_valid'] = True
                else:
                    result['errors'].append(f"Import error: {proc.stderr.decode()}")
                    
            except Exception as e:
                result['errors'].append(f"Import test failed: {e}")
                
            # Check for main function
            if 'def main(' in content:
                result['main_function_exists'] = True
                
        except SyntaxError as e:
            result['errors'].append(f"Syntax error: {e}")
        except Exception as e:
            result['errors'].append(f"File test failed: {e}")
            
        return result
    
    def generate_report(self, platform_results: Dict, file_results: Dict = None) -> str:
        """Generate comprehensive test report"""
        report = ["🧪 Dashboard Test Suite Report", "=" * 50, ""]
        
        # Summary
        total_dashboards = len(platform_results)
        working_dashboards = sum(1 for r in platform_results.values() 
                               if r['start_success'] and r['web_accessible'])
        
        report.extend([
            f"📊 Summary: {working_dashboards}/{total_dashboards} dashboards working",
            f"🔧 Platform Integration: {self.platform_url}",
            f"⏰ Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ])
        
        # Dashboard Results
        report.extend(["🎯 Dashboard Test Results", "-" * 30, ""])
        
        for name, result in platform_results.items():
            status = "✅" if (result['start_success'] and result['web_accessible']) else "❌"
            report.append(f"{status} {name} (Port {result['port']}):")
            
            if result['start_success']:
                report.append(f"   ✓ Startup: {result['start_time']:.2f}s")
            else:
                report.append("   ✗ Startup: Failed")
                
            if result['health_check_success']:
                report.append("   ✓ Health Check: Passed")
            else:
                report.append("   ✗ Health Check: Failed")
                
            if result['web_accessible']:
                report.append(f"   ✓ Web Access: {result['response_time']:.2f}s")
            else:
                report.append("   ✗ Web Access: Failed")
                
            if result['content_loaded']:
                report.append("   ✓ Content: Dashboard detected")
            else:
                report.append("   ✗ Content: No dashboard content")
                
            if result['stop_success']:
                report.append("   ✓ Shutdown: Success")
            else:
                report.append("   ✗ Shutdown: Failed")
                
            if result['errors']:
                report.append(f"   🚨 Errors: {'; '.join(result['errors'])}")
                
            report.append("")
        
        # Recommendations
        report.extend(["💡 Recommendations", "-" * 20, ""])
        
        failed_dashboards = [name for name, r in platform_results.items() 
                           if not (r['start_success'] and r['web_accessible'])]
        
        if failed_dashboards:
            report.extend([
                "🔧 Dashboards needing attention:",
                *[f"  - {name}" for name in failed_dashboards],
                ""
            ])
            
        report.extend([
            "📈 Next Steps:",
            "  1. Fix failed dashboards based on error messages",
            "  2. Check missing dependencies",
            "  3. Verify environment variable support",
            "  4. Test individual dashboard files for syntax errors",
            ""
        ])
        
        return "\n".join(report)

def main():
    """Run dashboard test suite"""
    tester = DashboardTester()
    
    print("🧪 Dashboard Test Suite")
    print("=" * 50)
    
    # Test platform integration
    platform_results = tester.test_all_dashboards()
    
    # Generate and display report
    report = tester.generate_report(platform_results)
    print(report)
    
    # Save report to file
    report_file = tester.maia_root / "claude/data/dashboard_test_report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
        
    print(f"📄 Full report saved to: {report_file}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
LLM-Enhanced Dependency Scanner
Extends the base dependency scanner with local LLM analysis for intelligent code understanding
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import ast

# Add MAIA root to path for imports
_maia_root = Path(__file__).resolve().parents[3]
if str(_maia_root) not in sys.path:
    sys.path.insert(0, str(_maia_root))

# Import base scanner (relative import from same directory)
from claude.tools.governance.dependency_scanner import DependencyScanner

# Import local LLM infrastructure with fallback
try:
    from claude.tools.optimal_local_llm_interface import OptimalLocalLLMInterface, ModelType
    from claude.tools.production_llm_router import ProductionLLMRouter, TaskType, LLMProvider
    _llm_available = True
except ImportError:
    _llm_available = False
    OptimalLocalLLMInterface = None
    ProductionLLMRouter = None

class LLMEnhancedDependencyScanner(DependencyScanner):
    def __init__(self, repo_path: str = None):
        # Pass repo_path to parent (parent handles default calculation)
        super().__init__(repo_path)

        # Initialize local LLM interface (with fallback if unavailable)
        self.llm_available = _llm_available
        if _llm_available:
            self.llm_interface = OptimalLocalLLMInterface()
            self.router = ProductionLLMRouter()
        else:
            self.llm_interface = None
            self.router = None
        
        # LLM analysis settings
        self.use_llm_analysis = True
        self.llm_batch_size = 10  # Process files in batches for efficiency
        
        print("🤖 LLM-Enhanced Dependency Scanner initialized")
        print(f"📊 Local models available: {self._get_available_models()}")
    
    def _get_available_models(self) -> List[str]:
        """Get list of available local models"""
        try:
            import subprocess
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                return [line.split()[0] for line in lines if line.strip()]
            return []
        except Exception:
            return []
    
    def _analyze_import_context_with_llm(self, file_path: Path, broken_imports: List[Dict]) -> List[Dict]:
        """Use local LLM to analyze import context and suggest fixes"""
        if not self.use_llm_analysis or not broken_imports:
            return broken_imports
            
        try:
            # Read file content for context
            content = file_path.read_text(encoding='utf-8')
            
            # Prepare analysis prompt
            import_issues = []
            for imp in broken_imports[:5]:  # Limit to first 5 for efficiency
                import_issues.append(f"Line {imp['line_number']}: {imp['import_statement']}")
            
            analysis_prompt = f"""
Analyze these Python import issues in the context of the full file:

File: {file_path.name}
Import Issues:
{chr(10).join(import_issues)}

File Content (first 100 lines):
{chr(10).join(content.split(chr(10))[:100])}

For each import issue, determine:
1. Is this a critical failure or handled gracefully?
2. What's the likely fix (restore file, update path, install dependency)?
3. Priority level (critical/high/medium/low)
4. Confidence in analysis (high/medium/low)

Respond in JSON format:
{{
  "analysis": [
    {{
      "import": "import_name",
      "status": "critical|handled|recoverable",
      "fix_suggestion": "description of fix",
      "priority": "critical|high|medium|low",
      "confidence": "high|medium|low",
      "reasoning": "brief explanation"
    }}
  ],
  "file_assessment": "overall file health assessment"
}}
"""
            
            # Route to appropriate local model
            model_choice = self.router.route_task(
                prompt=analysis_prompt,
                context={
                    "task_type": "code_review",
                    "content_size": len(analysis_prompt),
                    "complexity": "medium"
                }
            )
            
            # Get LLM analysis using async method
            import asyncio
            response = asyncio.run(self.llm_interface.generate_response(
                prompt=analysis_prompt,
                model=None,  # Let it auto-select optimal model
                temperature=0.1,
                max_tokens=1000,
                include_maia_context=False  # Disable context compression for speed
            ))
            
            # Parse and enhance import analysis
            try:
                response_text = response.get('response', response.get('content', ''))
                llm_analysis = json.loads(response_text)
                enhanced_imports = self._merge_llm_analysis(broken_imports, llm_analysis)
                return enhanced_imports
            except json.JSONDecodeError:
                print(f"⚠️  LLM analysis parsing failed for {file_path.name}")
                print(f"     Raw response: {str(response)[:200]}...")
                return broken_imports
                
        except Exception as e:
            print(f"⚠️  LLM analysis failed for {file_path.name}: {e}")
            return broken_imports
    
    def _merge_llm_analysis(self, original_imports: List[Dict], llm_analysis: Dict) -> List[Dict]:
        """Merge LLM analysis with original import data"""
        enhanced = []
        
        for imp in original_imports:
            enhanced_imp = imp.copy()
            
            # Find matching analysis
            for analysis in llm_analysis.get('analysis', []):
                if analysis['import'] in imp['import_statement']:
                    enhanced_imp.update({
                        'llm_status': analysis.get('status', 'unknown'),
                        'llm_fix_suggestion': analysis.get('fix_suggestion', ''),
                        'llm_priority': analysis.get('priority', 'medium'),
                        'llm_confidence': analysis.get('confidence', 'medium'),
                        'llm_reasoning': analysis.get('reasoning', '')
                    })
                    break
            
            enhanced.append(enhanced_imp)
        
        return enhanced
    
    def _check_imports_in_file(self, file_path: Path) -> List[Dict]:
        """Enhanced import checking with LLM analysis"""
        # Get base analysis
        broken_imports = super()._check_imports_in_file(file_path)
        
        # Skip LLM analysis for files with no issues
        if not broken_imports:
            return broken_imports
        
        # Skip LLM analysis for excluded patterns or very large files
        if self._should_exclude_from_llm_analysis(file_path):
            return broken_imports
        
        # Enhance with LLM analysis
        enhanced_imports = self._analyze_import_context_with_llm(file_path, broken_imports)
        
        return enhanced_imports
    
    def _should_exclude_from_llm_analysis(self, file_path: Path) -> bool:
        """Determine if file should be excluded from LLM analysis"""
        # Skip very large files (>50KB)
        try:
            if file_path.stat().st_size > 50000:
                return True
        except:
            pass
            
        # Skip certain file types
        exclude_patterns = [
            '__pycache__',
            '.pyc',
            'test_',
            'archive/',
            'node_modules/',
        ]
        
        file_str = str(file_path)
        return any(pattern in file_str for pattern in exclude_patterns)
    
    def generate_llm_enhanced_recommendations(self) -> List[Dict]:
        """Generate repair recommendations using local LLM analysis"""
        if not self.scan_results:
            return []
        
        # Aggregate LLM insights
        llm_insights = self._aggregate_llm_insights()
        
        # Generate comprehensive recommendations
        recommendation_prompt = f"""
Based on dependency scan analysis, generate prioritized repair recommendations:

Scan Summary:
- Unprotected broken imports: {self.scan_results['scan_summary'].get('unprotected_broken_imports', 0)}
- Try-protected imports: {self.scan_results['scan_summary'].get('try_protected_imports', 0)}
- System integrity issues: {self.scan_results['scan_summary'].get('total_integrity_issues', 0)}

LLM Analysis Insights:
{json.dumps(llm_insights, indent=2)}

Generate a strategic repair plan with:
1. Top 5 highest priority fixes
2. Estimated effort for each fix
3. Dependencies between fixes
4. Risk assessment

Respond in JSON format with specific, actionable recommendations.
"""
        
        try:
            response = self.llm_interface.generate(
                prompt=recommendation_prompt,
                model_type=ModelType.CODE,
                temperature=0.2,
                max_tokens=1500
            )
            
            recommendations = json.loads(response.response)
            return recommendations.get('recommendations', [])
            
        except Exception as e:
            print(f"⚠️  LLM recommendation generation failed: {e}")
            return self._generate_repair_recommendations(self.scan_results)
    
    def _aggregate_llm_insights(self) -> Dict:
        """Aggregate insights from all LLM analyses"""
        insights = {
            'total_files_analyzed': 0,
            'critical_issues': 0,
            'recoverable_issues': 0,
            'handled_gracefully': 0,
            'common_fix_patterns': {},
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        for issue in self.scan_results.get('broken_imports', []):
            if 'llm_status' in issue:
                insights['total_files_analyzed'] += 1
                
                status = issue.get('llm_status', 'unknown')
                if status == 'critical':
                    insights['critical_issues'] += 1
                elif status == 'recoverable':
                    insights['recoverable_issues'] += 1
                elif status == 'handled':
                    insights['handled_gracefully'] += 1
                
                # Track confidence
                confidence = issue.get('llm_confidence', 'medium')
                insights['confidence_distribution'][confidence] += 1
                
                # Track fix patterns
                fix_suggestion = issue.get('llm_fix_suggestion', 'unknown')
                if fix_suggestion in insights['common_fix_patterns']:
                    insights['common_fix_patterns'][fix_suggestion] += 1
                else:
                    insights['common_fix_patterns'][fix_suggestion] = 1
        
        return insights
    
    def print_enhanced_summary(self):
        """Print summary with LLM analysis insights"""
        super().print_summary()
        
        if not self.use_llm_analysis:
            return
        
        print("\n" + "="*60)
        print("🤖 LLM ANALYSIS INSIGHTS")
        print("="*60)
        
        insights = self._aggregate_llm_insights()
        
        if insights['total_files_analyzed'] > 0:
            print(f"🔍 Files Analyzed: {insights['total_files_analyzed']}")
            print(f"🚨 Critical Issues: {insights['critical_issues']}")
            print(f"♻️  Recoverable Issues: {insights['recoverable_issues']}")
            print(f"✅ Handled Gracefully: {insights['handled_gracefully']}")
            
            print(f"\n📊 Confidence Distribution:")
            for level, count in insights['confidence_distribution'].items():
                print(f"   {level.title()}: {count}")
            
            if insights['common_fix_patterns']:
                print(f"\n🔧 Common Fix Patterns:")
                for pattern, count in sorted(insights['common_fix_patterns'].items(), 
                                           key=lambda x: x[1], reverse=True)[:5]:
                    if pattern != 'unknown':
                        print(f"   • {pattern} ({count} occurrences)")
        else:
            print("No LLM analysis performed on scanned files")

def main():
    """Main CLI interface for LLM-enhanced dependency scanning"""
    if len(sys.argv) < 2:
        print("LLM-Enhanced Dependency Scanner")
        print("Commands:")
        print("  scan     - Run comprehensive LLM-enhanced dependency scan")
        print("  summary  - Show summary of last scan with LLM insights")
        print("  recommendations - Generate LLM-enhanced repair recommendations")
        return
    
    scanner = LLMEnhancedDependencyScanner()
    command = sys.argv[1].lower()
    
    if command == "scan":
        print("🚀 Starting LLM-enhanced comprehensive dependency scan...")
        results = scanner.scan_all_dependencies()
        scanner.print_enhanced_summary()
        scanner.save_scan_results()
        
    elif command == "summary":
        scanner.print_enhanced_summary()
        
    elif command == "recommendations":
        if scanner.scan_results:
            recommendations = scanner.generate_llm_enhanced_recommendations()
            print("\n🤖 LLM-Enhanced Repair Recommendations:")
            print(json.dumps(recommendations, indent=2))
        else:
            print("❌ No scan results available. Run 'scan' first.")
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
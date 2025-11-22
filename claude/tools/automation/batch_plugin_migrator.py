#!/usr/bin/env python3
"""
Batch Plugin Migrator - Parallel Processing System
Efficiently migrates multiple tools to Maia 2.0 plugins with quality validation
"""

import asyncio
import concurrent.futures
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging
from enhanced_plugin_generator import EnhancedPluginGenerator
from claude.tools.core.path_manager import get_maia_root

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BatchMigrationManager:
    """Manages parallel migration of multiple tools"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.generator = EnhancedPluginGenerator()
        self.results = []
    
    def get_migration_candidates(self, tools_dir: str, limit: int = None) -> List[Tuple[str, str]]:
        """Get list of tools ready for migration"""
        tools_path = Path(tools_dir)
        python_files = list(tools_path.glob("*.py"))
        
        # Filter out system files and already migrated tools
        excluded_files = {
            "__init__.py", "__pycache__", "archive", "archived_broken_files_20250911",
            "local_llm_codegen.py", "enhanced_plugin_generator.py", "batch_plugin_migrator.py"
        }
        
        candidates = []
        for file_path in python_files:
            if file_path.name not in excluded_files and not file_path.name.startswith('.'):
                plugin_name = file_path.stem + "_plugin"
                candidates.append((str(file_path), plugin_name))
        
        # Sort by file size (smaller files first for faster testing)
        candidates.sort(key=lambda x: Path(x[0]).stat().st_size)
        
        if limit:
            candidates = candidates[:limit]
            
        logger.info(f"🎯 Found {len(candidates)} migration candidates")
        return candidates
    
    def migrate_single_tool(self, tool_info: Tuple[str, str]) -> Dict[str, Any]:
        """Migrate a single tool with comprehensive logging"""
        tool_path, plugin_name = tool_info
        start_time = time.time()
        
        try:
            logger.info(f"🔧 Migrating: {Path(tool_path).name} -> {plugin_name}")
            
            # Generate plugin with validation
            code, validation = self.generator.generate_plugin_with_validation(tool_path, plugin_name)
            
            # Save if successful
            output_path = f"${MAIA_ROOT}2/migrated_plugins/{plugin_name}.py"
            
            if validation["success"]:
                with open(output_path, 'w') as f:
                    f.write(code)
                logger.info(f"✅ Successfully migrated: {plugin_name}")
                status = "success"
            else:
                # Save with warning comment for manual review
                with open(output_path, 'w') as f:
                    f.write(f"# WARNING: Generated with validation issues\n")
                    f.write(f"# Issues: {validation.get('structure_message', '')}, {validation.get('syntax_message', '')}\n\n")
                    f.write(code)
                logger.warning(f"⚠️  Migrated with issues: {plugin_name}")
                status = "issues"
            
            processing_time = time.time() - start_time
            
            return {
                "tool_path": tool_path,
                "plugin_name": plugin_name,
                "status": status,
                "processing_time": processing_time,
                "validation": validation,
                "output_path": output_path,
                "code_size": len(code)
            }
            
        except Exception as e:
            logger.error(f"❌ Migration failed for {plugin_name}: {str(e)}")
            return {
                "tool_path": tool_path,
                "plugin_name": plugin_name,
                "status": "failed",
                "processing_time": time.time() - start_time,
                "error": str(e)
            }
    
    def migrate_batch_parallel(self, candidates: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Migrate tools in parallel batches"""
        logger.info(f"🚀 Starting parallel migration of {len(candidates)} tools")
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all migration tasks
            future_to_tool = {
                executor.submit(self.migrate_single_tool, tool_info): tool_info
                for tool_info in candidates
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_tool):
                result = future.result()
                self.results.append(result)
        
        total_time = time.time() - start_time
        
        # Generate summary statistics
        summary = self.generate_migration_summary(total_time)
        logger.info(f"🎉 Batch migration completed in {total_time:.1f}s")
        
        return summary
    
    def generate_migration_summary(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive migration summary"""
        successful = [r for r in self.results if r["status"] == "success"]
        issues = [r for r in self.results if r["status"] == "issues"]
        failed = [r for r in self.results if r["status"] == "failed"]
        
        summary = {
            "total_tools": len(self.results),
            "successful": len(successful),
            "with_issues": len(issues),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.results) * 100 if self.results else 0,
            "total_processing_time": total_time,
            "average_time_per_tool": total_time / len(self.results) if self.results else 0,
            "total_code_generated": sum(r.get("code_size", 0) for r in self.results),
            "results": self.results
        }
        
        return summary
    
    def save_migration_report(self, summary: Dict[str, Any], output_file: str = None):
        """Save detailed migration report"""
        if not output_file:
            timestamp = int(time.time())
            output_file = str(Path(__file__).parent.parent.parent / "data" / f"migration_report_{timestamp}.json")
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"📊 Migration report saved: {output_file}")
        return output_file

async def main():
    """Main batch migration execution"""
    if len(sys.argv) < 2:
        print("Usage: python3 batch_plugin_migrator.py <tools_directory> [batch_size] [max_workers]")
        sys.exit(1)
    
    tools_dir = sys.argv[1]
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    max_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    logger.info(f"🎯 Batch Migration Configuration:")
    logger.info(f"   Tools Directory: {tools_dir}")
    logger.info(f"   Batch Size: {batch_size}")
    logger.info(f"   Max Workers: {max_workers}")
    
    migrator = BatchMigrationManager(max_workers=max_workers)
    
    # Get migration candidates
    candidates = migrator.get_migration_candidates(tools_dir, limit=batch_size)
    
    if not candidates:
        logger.warning("No migration candidates found")
        return
    
    # Execute parallel migration
    summary = migrator.migrate_batch_parallel(candidates)
    
    # Save report
    report_file = migrator.save_migration_report(summary)
    
    # Print summary
    print(f"\n🎉 MIGRATION SUMMARY")
    print(f"📊 Total Tools: {summary['total_tools']}")
    print(f"✅ Successful: {summary['successful']}")
    print(f"⚠️  With Issues: {summary['with_issues']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
    print(f"⏱️  Total Time: {summary['total_processing_time']:.1f}s")
    print(f"📝 Report: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
import os
import re
from pathlib import Path
from datetime import datetime

class FileCategorizer:
    def __init__(self):
        self.categories = {
            'core_system': [],      # Essential system files
            'agents': [],           # Agent definitions
            'tools': [],            # Executable tools
            'commands': [],         # Workflow orchestrations
            'context': [],          # Context and configuration
            'experimental': [],     # Temporary/test files
            'deprecated': [],       # Old/unused files
            'documentation': [],    # README, guides, etc.
            'archive': [],          # Historical/archived files
            'uncategorized': []     # Everything else
        }

    def categorize_file(self, filepath):
        """Categorize file based on path and content analysis"""
        path_str = str(filepath).lower()

        # Archive identification (highest priority)
        if '/archive/' in path_str:
            return 'archive'

        # Core system identification
        if any(core in path_str for core in ['identity.md', 'ufc_system.md', 'systematic_thinking']):
            return 'core_system'

        # Agent identification
        if 'agent' in path_str and filepath.suffix == '.md':
            return 'agents'

        # Tool identification
        if '/tools/' in path_str and filepath.suffix == '.py':
            return 'tools'

        # Command identification
        if '/commands/' in path_str and filepath.suffix == '.md':
            return 'commands'

        # Context identification
        if '/context/' in path_str:
            return 'context'

        # Experimental/temporary identification
        if any(temp in path_str for temp in ['temp', 'test', 'experimental', 'backup']):
            return 'experimental'

        # Deprecated identification
        if any(old in path_str for old in ['old', 'deprecated', '_v2', '_backup', 'unused']):
            return 'deprecated'

        # Documentation identification
        if any(doc in path_str for doc in ['readme', 'doc', 'guide', '.md']) and 'context' not in path_str:
            return 'documentation'

        return 'uncategorized'

    def analyze_directory(self, base_path):
        """Analyze all files in directory structure"""
        base = Path(base_path)

        for pattern in ['**/*.md', '**/*.py']:
            for filepath in base.glob(pattern):
                if any(exclude in str(filepath) for exclude in ['.git', '__pycache__', '.pyc']):
                    continue

                category = self.categorize_file(filepath)
                self.categories[category].append(str(filepath))

        return self.categories

    def generate_report(self, output_file):
        """Generate categorization report"""
        with open(output_file, 'w') as f:
            f.write("# Maia File Categorization Report\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Files**: {sum(len(files) for files in self.categories.values())}\n\n")

            # Summary statistics
            f.write("## Summary Statistics\n\n")
            for category, files in sorted(self.categories.items(), key=lambda x: len(x[1]), reverse=True):
                f.write(f"- **{category.upper()}**: {len(files)} files\n")
            f.write("\n")

            # Detailed listings
            for category, files in sorted(self.categories.items()):
                f.write(f"## {category.upper()} ({len(files)} files)\n\n")
                if files:
                    for file in sorted(files):
                        f.write(f"- {file}\n")
                else:
                    f.write("- *No files in this category*\n")
                f.write("\n")

if __name__ == "__main__":
    categorizer = FileCategorizer()
    categories = categorizer.analyze_directory(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))
    categorizer.generate_report("claude/data/file_categorization_report.md")

    print("✅ Categorization complete")
    print(f"📊 Report saved to: claude/data/file_categorization_report.md")
    print(f"\n📈 Summary:")
    for category, files in sorted(categorizer.categories.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"   {category:.<20} {len(files):>4} files")
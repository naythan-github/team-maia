#!/usr/bin/env python3
"""
Context File Validator
Purpose: Verify all referenced context files actually exist
Created: 2025-09-30 - Post Phase 2 maintenance
"""

import re
from pathlib import Path
from claude.tools.core.path_manager import get_maia_root

def validate_context_references():
    """Validate that all files referenced in documentation actually exist"""
    base_path = Path(str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd()))

    # Core files that MUST exist
    required_core_files = [
        "claude/context/ufc_system.md",
        "claude/context/core/identity.md",
        "claude/context/core/systematic_thinking_protocol.md",
        "claude/context/core/model_selection_strategy.md",
        "claude/context/core/smart_context_loading.md",
    ]

    print("🔍 Validating Core Context Files")
    print("=" * 50)

    all_valid = True
    for file_path in required_core_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ MISSING: {file_path}")
            all_valid = False

    print("=" * 50)

    # Check smart_context_loading.md for file references
    smart_loading = base_path / "claude/context/core/smart_context_loading.md"
    if smart_loading.exists():
        with open(smart_loading, 'r') as f:
            content = f.read()

        # Extract file paths referenced in the documentation
        md_pattern = r'`(${MAIA_ROOT}/[^`]+\.md)`'
        referenced_files = re.findall(md_pattern, content)

        if referenced_files:
            print("\n🔍 Validating Referenced Files in smart_context_loading.md")
            print("=" * 50)

            for ref_file in set(referenced_files):
                ref_path = Path(ref_file)
                if ref_path.exists():
                    print(f"✅ {ref_path.relative_to(base_path)}")
                else:
                    print(f"❌ MISSING: {ref_path.relative_to(base_path)}")
                    all_valid = False

            print("=" * 50)

    if all_valid:
        print("\n✅ All context file references are valid!")
        return 0
    else:
        print("\n❌ Some context file references are broken!")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(validate_context_references())
#!/usr/bin/env python3
"""
Product Candidate Tracker - Track tools with organizational productization potential

Tracks Maia tools that could be re-engineered for broader organizational use.
Provides CRUD operations, filtering, reporting, and automatic suggestion of candidates.

Usage:
    python3 product_tracker.py add <tool> --potential high --audience org --value "description"
    python3 product_tracker.py list [--potential high] [--status ready]
    python3 product_tracker.py update <tool> --status ready
    python3 product_tracker.py remove <tool>
    python3 product_tracker.py report --format md
    python3 product_tracker.py suggest

Author: SRE Principal Engineer Agent (Maia)
Created: 2026-01-15
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

# Valid values for constrained fields
VALID_POTENTIALS = {"high", "medium", "low"}
VALID_AUDIENCES = {"team", "department", "org", "external"}
VALID_STATUSES = {"idea", "prototype", "ready", "in_progress", "shipped"}

# Default data path
DEFAULT_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "product_candidates.json"


@dataclass
class ProductCandidate:
    """A tool candidate for organizational productization"""

    tool: str
    path: str
    potential: Literal["high", "medium", "low"]
    audience: Literal["team", "department", "org", "external"]
    value: str
    changes_needed: List[str] = field(default_factory=list)
    status: Literal["idea", "prototype", "ready", "in_progress", "shipped"] = "idea"
    dependencies: List[str] = field(default_factory=list)
    added: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    updated: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate field values"""
        if self.potential not in VALID_POTENTIALS:
            raise ValueError(f"Invalid potential: {self.potential}. Must be one of {VALID_POTENTIALS}")
        if self.audience not in VALID_AUDIENCES:
            raise ValueError(f"Invalid audience: {self.audience}. Must be one of {VALID_AUDIENCES}")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {self.status}. Must be one of {VALID_STATUSES}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "tool": self.tool,
            "path": self.path,
            "potential": self.potential,
            "audience": self.audience,
            "value": self.value,
            "changes_needed": self.changes_needed,
            "status": self.status,
            "dependencies": self.dependencies,
            "added": self.added,
            "updated": self.updated,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductCandidate":
        """Create instance from dictionary"""
        return cls(
            tool=data["tool"],
            path=data["path"],
            potential=data["potential"],
            audience=data["audience"],
            value=data["value"],
            changes_needed=data.get("changes_needed", []),
            status=data.get("status", "idea"),
            dependencies=data.get("dependencies", []),
            added=data.get("added", datetime.now().strftime("%Y-%m-%d")),
            updated=data.get("updated", datetime.now().strftime("%Y-%m-%d")),
            notes=data.get("notes")
        )


class ProductTracker:
    """Track and manage product candidates"""

    def __init__(self, data_path: str = None):
        """Initialize tracker with data path"""
        self.data_path = Path(data_path) if data_path else DEFAULT_DATA_PATH
        self._candidates: Dict[str, ProductCandidate] = {}
        self.load()

    def add(self, candidate: ProductCandidate) -> bool:
        """Add a new candidate. Returns False if duplicate."""
        if candidate.tool in self._candidates:
            return False
        self._candidates[candidate.tool] = candidate
        self.save()
        return True

    def get(self, tool: str) -> Optional[ProductCandidate]:
        """Get candidate by tool name"""
        return self._candidates.get(tool)

    def list(self, **filters) -> List[ProductCandidate]:
        """List candidates with optional filters"""
        candidates = list(self._candidates.values())

        for key, value in filters.items():
            if value is not None:
                candidates = [c for c in candidates if getattr(c, key, None) == value]

        return candidates

    def update(self, tool: str, **updates) -> bool:
        """Update candidate fields. Returns False if not found."""
        if tool not in self._candidates:
            return False

        candidate = self._candidates[tool]

        for key, value in updates.items():
            if value is not None and hasattr(candidate, key):
                setattr(candidate, key, value)

        candidate.updated = datetime.now().strftime("%Y-%m-%d")
        self.save()
        return True

    def remove(self, tool: str) -> bool:
        """Remove candidate. Returns False if not found."""
        if tool not in self._candidates:
            return False
        del self._candidates[tool]
        self.save()
        return True

    def save(self) -> None:
        """Save candidates to JSON file"""
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "candidates": [c.to_dict() for c in self._candidates.values()]
        }
        self.data_path.write_text(json.dumps(data, indent=2))

    def load(self) -> None:
        """Load candidates from JSON file"""
        if not self.data_path.exists():
            return

        try:
            data = json.loads(self.data_path.read_text())
            for item in data.get("candidates", []):
                candidate = ProductCandidate.from_dict(item)
                self._candidates[candidate.tool] = candidate
        except (json.JSONDecodeError, KeyError):
            pass

    def suggest(self) -> List[Dict[str, Any]]:
        """Suggest tools that could be productized"""
        suggestions = self._scan_capabilities()

        # Filter out already tracked tools
        tracked = set(self._candidates.keys())
        suggestions = [s for s in suggestions if s["tool"] not in tracked]

        return suggestions

    def _scan_capabilities(self) -> List[Dict[str, Any]]:
        """Scan capabilities database for potential candidates"""
        suggestions = []

        # Try to query capabilities database
        try:
            import sqlite3
            db_path = Path(__file__).parent.parent.parent / "data" / "databases" / "system" / "capabilities.db"

            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                # Find tools that look general-purpose (not maia-specific in name)
                cursor.execute("""
                    SELECT name, path, purpose
                    FROM capabilities
                    WHERE type = 'tool'
                    AND name NOT LIKE '%maia%'
                    AND name NOT LIKE '%swarm%'
                    AND name NOT LIKE '%context%'
                    AND name NOT LIKE '%session%'
                    AND purpose IS NOT NULL
                    ORDER BY name
                    LIMIT 50
                """)

                for row in cursor.fetchall():
                    name, path, description = row
                    suggestions.append({
                        "tool": name,
                        "path": path or "",
                        "reason": (description or "")[:100]
                    })

                conn.close()
        except Exception:
            pass

        return suggestions

    def report(self, format: str = "md") -> str:
        """Generate report in specified format"""
        candidates = self.list()

        if format == "json":
            return json.dumps({"candidates": [c.to_dict() for c in candidates]}, indent=2)

        # Markdown format
        lines = [
            "# Product Candidates Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Total candidates: {len(candidates)}",
            "",
            "## Summary by Potential",
            "",
            "| Potential | Count |",
            "|-----------|-------|",
        ]

        for pot in ["high", "medium", "low"]:
            count = len([c for c in candidates if c.potential == pot])
            lines.append(f"| {pot} | {count} |")

        lines.extend([
            "",
            "## Candidates",
            "",
            "| Tool | Potential | Audience | Status | Value |",
            "|------|-----------|----------|--------|-------|"
        ])

        for c in sorted(candidates, key=lambda x: (
            {"high": 0, "medium": 1, "low": 2}[x.potential],
            x.tool
        )):
            lines.append(f"| {c.tool} | {c.potential} | {c.audience} | {c.status} | {c.value[:50]}{'...' if len(c.value) > 50 else ''} |")

        if not candidates:
            lines.append("| (no candidates) | - | - | - | - |")

        return "\n".join(lines)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Track tools with organizational productization potential",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--data-path", help="Path to data file")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a candidate")
    add_parser.add_argument("tool", help="Tool filename")
    add_parser.add_argument("--path", required=True, help="Tool directory path")
    add_parser.add_argument("--potential", required=True, choices=VALID_POTENTIALS, help="Potential level")
    add_parser.add_argument("--audience", required=True, choices=VALID_AUDIENCES, help="Target audience")
    add_parser.add_argument("--value", required=True, help="Business value description")
    add_parser.add_argument("--changes", nargs="*", default=[], help="Changes needed for productization")
    add_parser.add_argument("--status", choices=VALID_STATUSES, default="idea", help="Current status")
    add_parser.add_argument("--dependencies", nargs="*", default=[], help="External dependencies")
    add_parser.add_argument("--notes", help="Additional notes")

    # List command
    list_parser = subparsers.add_parser("list", help="List candidates")
    list_parser.add_argument("--potential", choices=VALID_POTENTIALS, help="Filter by potential")
    list_parser.add_argument("--status", choices=VALID_STATUSES, help="Filter by status")
    list_parser.add_argument("--audience", choices=VALID_AUDIENCES, help="Filter by audience")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update a candidate")
    update_parser.add_argument("tool", help="Tool to update")
    update_parser.add_argument("--potential", choices=VALID_POTENTIALS, help="New potential")
    update_parser.add_argument("--status", choices=VALID_STATUSES, help="New status")
    update_parser.add_argument("--audience", choices=VALID_AUDIENCES, help="New audience")
    update_parser.add_argument("--value", help="New value description")
    update_parser.add_argument("--notes", help="New notes")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a candidate")
    remove_parser.add_argument("tool", help="Tool to remove")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument("--format", choices=["md", "json"], default="md", help="Output format")

    # Suggest command
    subparsers.add_parser("suggest", help="Suggest potential candidates")

    args = parser.parse_args()

    # Initialize tracker
    tracker = ProductTracker(data_path=args.data_path) if args.data_path else ProductTracker()

    if args.command == "add":
        candidate = ProductCandidate(
            tool=args.tool,
            path=args.path,
            potential=args.potential,
            audience=args.audience,
            value=args.value,
            changes_needed=args.changes,
            status=args.status,
            dependencies=args.dependencies,
            notes=args.notes
        )
        if tracker.add(candidate):
            print(f"Added: {args.tool}")
        else:
            print(f"Already exists: {args.tool}")

    elif args.command == "list":
        filters = {}
        if args.potential:
            filters["potential"] = args.potential
        if args.status:
            filters["status"] = args.status
        if args.audience:
            filters["audience"] = args.audience

        candidates = tracker.list(**filters)

        if candidates:
            print(f"\n{'Tool':<30} {'Potential':<10} {'Audience':<12} {'Status':<12}")
            print("-" * 64)
            for c in candidates:
                print(f"{c.tool:<30} {c.potential:<10} {c.audience:<12} {c.status:<12}")
            print(f"\nTotal: {len(candidates)} candidates")
        else:
            print("No candidates found")

    elif args.command == "update":
        updates = {}
        if args.potential:
            updates["potential"] = args.potential
        if args.status:
            updates["status"] = args.status
        if args.audience:
            updates["audience"] = args.audience
        if args.value:
            updates["value"] = args.value
        if args.notes:
            updates["notes"] = args.notes

        if tracker.update(args.tool, **updates):
            print(f"Updated: {args.tool}")
        else:
            print(f"Not found: {args.tool}")

    elif args.command == "remove":
        if tracker.remove(args.tool):
            print(f"Removed: {args.tool}")
        else:
            print(f"Not found: {args.tool}")

    elif args.command == "report":
        print(tracker.report(format=args.format))

    elif args.command == "suggest":
        suggestions = tracker.suggest()
        if suggestions:
            print(f"\nSuggested candidates ({len(suggestions)} found):\n")
            for s in suggestions[:20]:  # Top 20
                print(f"  {s['tool']}")
                print(f"    Path: {s['path']}")
                print(f"    Reason: {s['reason'][:80]}...")
                print()
        else:
            print("No suggestions available (capabilities database may not exist)")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Confluence Organization Manager
Provides intelligent space organization, content analysis, and interactive placement capabilities
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import sqlite3
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from claude.tools.reliable_confluence_client import ReliableConfluenceClient

@dataclass
class SpaceHierarchy:
    """Represents a Confluence space hierarchy"""
    space_key: str
    space_name: str
    root_pages: List[Dict]
    total_pages: int
    max_depth: int
    organizational_patterns: List[str]

@dataclass
class ContentPlacement:
    """Represents a content placement recommendation"""
    space_key: str
    parent_id: Optional[str]
    parent_title: str
    path: str
    confidence: float
    reasoning: str

@dataclass
class OrganizationSuggestion:
    """Represents an organizational improvement suggestion"""
    suggestion_type: str
    description: str
    impact: str
    implementation_steps: List[str]
    priority: int

class ConfluenceOrganizationManager:
    """
    Intelligent Confluence organization manager with content analysis and interactive placement
    """
    
    def __init__(self):
        self.client = ReliableConfluenceClient()
        self.db_path = self._get_db_path()
        self._init_database()
        self.organization_patterns = self._load_organization_patterns()
    
    def _get_db_path(self) -> str:
        """Get the database path"""
        data_dir = project_root / "claude" / "data"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / "confluence_organization.db")
    
    def _init_database(self):
        """Initialize the SQLite database for organization tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Space hierarchy cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS space_hierarchies (
                space_key TEXT PRIMARY KEY,
                space_name TEXT,
                hierarchy_data TEXT,
                last_scanned TIMESTAMP,
                total_pages INTEGER,
                max_depth INTEGER
            )
        ''')
        
        # User placement preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS placement_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT,
                keywords TEXT,
                preferred_space TEXT,
                preferred_parent TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Organization suggestions history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS organization_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                space_key TEXT,
                action_type TEXT,
                description TEXT,
                result TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_organization_patterns(self) -> Dict[str, List[str]]:
        """Load common organizational patterns"""
        return {
            "project_management": [
                "Projects", "Planning", "Roadmaps", "Status Updates", "Meeting Notes"
            ],
            "technical_documentation": [
                "Architecture", "API Documentation", "Deployment Guides", "Troubleshooting", "Reference"
            ],
            "team_management": [
                "Team", "Processes", "Guidelines", "Training", "Resources"
            ],
            "company_knowledge": [
                "Policies", "Procedures", "Company Info", "HR", "Finance"
            ],
            "customer_facing": [
                "Client Documentation", "Support", "User Guides", "FAQs", "Onboarding"
            ]
        }
    
    def scan_confluence_spaces(self, space_keys: Optional[List[str]] = None) -> List[SpaceHierarchy]:
        """
        Scan Confluence spaces and analyze their organizational structure
        
        Args:
            space_keys: Specific spaces to scan, or None for all accessible spaces
            
        Returns:
            List of SpaceHierarchy objects with organizational analysis
        """
        print("🔍 Scanning Confluence spaces...")
        
        # Get spaces to scan
        if space_keys is None:
            spaces = self.client.list_spaces() or []
            space_keys = [space['key'] for space in spaces]
        
        hierarchies = []
        
        for space_key in space_keys:
            print(f"  📊 Analyzing space: {space_key}")
            hierarchy = self._analyze_space_structure(space_key)
            if hierarchy:
                hierarchies.append(hierarchy)
                self._cache_space_hierarchy(hierarchy)
        
        print(f"✅ Scanned {len(hierarchies)} spaces")
        return hierarchies
    
    def _analyze_space_structure(self, space_key: str) -> Optional[SpaceHierarchy]:
        """Analyze the structure of a specific space"""
        # Get all pages in the space
        search_results = self.client.search_content(
            query=f"space = {space_key}",
            space_key=space_key,
            limit=1000
        ) or []
        
        if not search_results:
            return None
        
        # Build hierarchy tree
        pages_by_id = {page['id']: page for page in search_results}
        root_pages = []
        max_depth = 0
        
        for page in search_results:
            # Check if this is a root page (no ancestors or ancestors not in this space)
            ancestors = page.get('ancestors', [])
            if not ancestors or not any(anc['id'] in pages_by_id for anc in ancestors):
                root_pages.append(page)
            
            # Calculate depth
            depth = len([anc for anc in ancestors if anc['id'] in pages_by_id])
            max_depth = max(max_depth, depth)
        
        # Identify organizational patterns
        patterns = self._identify_organizational_patterns(search_results)
        
        # Get space info
        spaces = self.client.list_spaces() or []
        space_name = next((s['name'] for s in spaces if s['key'] == space_key), space_key)
        
        return SpaceHierarchy(
            space_key=space_key,
            space_name=space_name,
            root_pages=root_pages,
            total_pages=len(search_results),
            max_depth=max_depth,
            organizational_patterns=patterns
        )
    
    def _identify_organizational_patterns(self, pages: List[Dict]) -> List[str]:
        """Identify organizational patterns in the page titles"""
        patterns = []
        titles = [page['title'].lower() for page in pages]
        
        for pattern_name, keywords in self.organization_patterns.items():
            matches = sum(1 for title in titles 
                         for keyword in keywords 
                         if keyword.lower() in title)
            if matches >= 2:  # At least 2 matches to consider it a pattern
                patterns.append(f"{pattern_name} ({matches} pages)")
        
        return patterns
    
    def _cache_space_hierarchy(self, hierarchy: SpaceHierarchy):
        """Cache space hierarchy in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO space_hierarchies 
            (space_key, space_name, hierarchy_data, last_scanned, total_pages, max_depth)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            hierarchy.space_key,
            hierarchy.space_name,
            json.dumps(hierarchy.root_pages),
            datetime.now(),
            hierarchy.total_pages,
            hierarchy.max_depth
        ))
        
        conn.commit()
        conn.close()
    
    def suggest_content_placement(self, content: str, title: str, 
                                content_type: Optional[str] = None) -> List[ContentPlacement]:
        """
        Analyze content and suggest optimal placement locations
        
        Args:
            content: The content to be placed
            title: The title of the content
            content_type: Optional content type hint
            
        Returns:
            List of ContentPlacement suggestions ranked by confidence
        """
        print(f"🧠 Analyzing content for placement: '{title}'")
        
        # Analyze content for keywords and topics
        keywords = self._extract_keywords(content + " " + title)
        detected_type = content_type or self._detect_content_type(content, title)
        
        print(f"  🏷️  Detected type: {detected_type}")
        print(f"  🔑 Keywords: {', '.join(keywords[:5])}")
        
        # Get cached space hierarchies
        hierarchies = self._get_cached_hierarchies()
        
        # Generate placement suggestions
        suggestions = []
        
        for hierarchy in hierarchies:
            space_suggestions = self._generate_space_suggestions(
                hierarchy, keywords, detected_type, title
            )
            suggestions.extend(space_suggestions)
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text content"""
        # Simple keyword extraction - can be enhanced with NLP
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Remove common words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'use', 'man', 'new',
            'now', 'way', 'may', 'say', 'each', 'which', 'their', 'time', 'will',
            'about', 'if', 'up', 'out', 'many', 'then', 'them', 'these', 'so',
            'some', 'what', 'only', 'into', 'know', 'take', 'year', 'your',
            'good', 'see', 'over', 'think', 'its', 'also', 'back', 'after',
            'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even',
            'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us'
        }
        
        keywords = [word for word in set(words) 
                   if word not in stop_words and len(word) > 3]
        
        # Return most common keywords (simple frequency count)
        from collections import Counter
        return [word for word, count in Counter(keywords).most_common(10)]
    
    def _detect_content_type(self, content: str, title: str) -> str:
        """Detect the type of content based on content and title"""
        text = (content + " " + title).lower()
        
        type_indicators = {
            "meeting_notes": ["meeting", "agenda", "minutes", "discussion", "action items"],
            "technical_doc": ["api", "architecture", "deployment", "configuration", "technical"],
            "project_plan": ["project", "plan", "roadmap", "milestone", "timeline", "sprint"],
            "process_guide": ["process", "procedure", "workflow", "guide", "steps", "how to"],
            "policy": ["policy", "guideline", "standard", "compliance", "regulation"],
            "training": ["training", "tutorial", "learning", "education", "course"],
            "reference": ["reference", "documentation", "manual", "specification"],
            "status_update": ["status", "update", "report", "progress", "summary"]
        }
        
        for content_type, indicators in type_indicators.items():
            matches = sum(1 for indicator in indicators if indicator in text)
            if matches >= 2:
                return content_type
        
        return "general_document"
    
    def _generate_space_suggestions(self, hierarchy: SpaceHierarchy, keywords: List[str], 
                                  content_type: str, title: str) -> List[ContentPlacement]:
        """Generate placement suggestions for a specific space"""
        suggestions = []
        
        # Check for direct keyword matches in page titles
        for page in hierarchy.root_pages:
            confidence = self._calculate_placement_confidence(
                page, keywords, content_type, title
            )
            
            if confidence > 0.3:  # Minimum confidence threshold
                suggestions.append(ContentPlacement(
                    space_key=hierarchy.space_key,
                    parent_id=page['id'],
                    parent_title=page['title'],
                    path=f"{hierarchy.space_name} > {page['title']}",
                    confidence=confidence,
                    reasoning=self._generate_placement_reasoning(
                        page, keywords, content_type, confidence
                    )
                ))
        
        # Also suggest root level placement
        root_confidence = self._calculate_root_placement_confidence(
            hierarchy, keywords, content_type
        )
        
        if root_confidence > 0.2:
            suggestions.append(ContentPlacement(
                space_key=hierarchy.space_key,
                parent_id=None,
                parent_title="Root Level",
                path=hierarchy.space_name,
                confidence=root_confidence,
                reasoning=f"Place at root level in {hierarchy.space_name} space"
            ))
        
        return suggestions
    
    def _calculate_placement_confidence(self, page: Dict, keywords: List[str], 
                                      content_type: str, title: str) -> float:
        """Calculate confidence score for placing content under a specific page"""
        confidence = 0.0
        page_title = page['title'].lower()
        
        # Keyword matching
        keyword_matches = sum(1 for keyword in keywords if keyword in page_title)
        confidence += (keyword_matches / max(len(keywords), 1)) * 0.4
        
        # Content type matching
        type_keywords = {
            "meeting_notes": ["meeting", "discussions", "notes"],
            "technical_doc": ["documentation", "technical", "architecture", "api"],
            "project_plan": ["projects", "planning", "roadmaps"],
            "process_guide": ["processes", "procedures", "guides"],
            "policy": ["policies", "governance", "compliance"],
            "training": ["training", "learning", "education"],
            "reference": ["reference", "documentation", "resources"],
            "status_update": ["updates", "reports", "status"]
        }
        
        if content_type in type_keywords:
            type_matches = sum(1 for keyword in type_keywords[content_type] 
                             if keyword in page_title)
            confidence += (type_matches / len(type_keywords[content_type])) * 0.3
        
        # Title similarity (simple)
        title_words = set(title.lower().split())
        page_words = set(page_title.split())
        common_words = title_words.intersection(page_words)
        if title_words:
            confidence += (len(common_words) / len(title_words)) * 0.3
        
        return min(confidence, 1.0)
    
    def _calculate_root_placement_confidence(self, hierarchy: SpaceHierarchy, 
                                           keywords: List[str], content_type: str) -> float:
        """Calculate confidence for root-level placement"""
        # Check if space patterns match content type
        confidence = 0.0
        
        for pattern in hierarchy.organizational_patterns:
            if content_type.replace("_", " ") in pattern.lower():
                confidence += 0.4
        
        # General space matching
        space_name_lower = hierarchy.space_name.lower()
        for keyword in keywords:
            if keyword in space_name_lower:
                confidence += 0.1
        
        return min(confidence, 0.8)  # Cap at 0.8 for root placement
    
    def _generate_placement_reasoning(self, page: Dict, keywords: List[str], 
                                    content_type: str, confidence: float) -> str:
        """Generate human-readable reasoning for placement suggestion"""
        reasons = []
        
        page_title = page['title'].lower()
        
        # Check keyword matches
        matched_keywords = [kw for kw in keywords if kw in page_title]
        if matched_keywords:
            reasons.append(f"Keywords match: {', '.join(matched_keywords[:3])}")
        
        # Check content type
        if content_type.replace("_", " ") in page_title:
            reasons.append(f"Content type matches: {content_type.replace('_', ' ')}")
        
        if confidence > 0.7:
            quality = "Excellent"
        elif confidence > 0.5:
            quality = "Good"
        else:
            quality = "Fair"
        
        base_reason = f"{quality} match based on"
        if reasons:
            return f"{base_reason} {', '.join(reasons)}"
        else:
            return f"{base_reason} general content analysis"
    
    def _get_cached_hierarchies(self) -> List[SpaceHierarchy]:
        """Get cached space hierarchies from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT space_key, space_name, hierarchy_data, total_pages, max_depth
            FROM space_hierarchies
            ORDER BY total_pages DESC
        ''')
        
        hierarchies = []
        for row in cursor.fetchall():
            try:
                root_pages = json.loads(row[2])
                hierarchies.append(SpaceHierarchy(
                    space_key=row[0],
                    space_name=row[1],
                    root_pages=root_pages,
                    total_pages=row[3],
                    max_depth=row[4],
                    organizational_patterns=[]  # Could cache this too
                ))
            except json.JSONDecodeError:
                continue
        
        conn.close()
        return hierarchies
    
    def interactive_folder_selection(self, suggestions: List[ContentPlacement]) -> Optional[ContentPlacement]:
        """
        Present interactive folder selection interface
        
        Args:
            suggestions: List of placement suggestions
            
        Returns:
            Selected ContentPlacement or None if cancelled
        """
        if not suggestions:
            print("❌ No placement suggestions available")
            return None
        
        print("\n📂 Content Placement Options:")
        print("=" * 50)
        
        for i, suggestion in enumerate(suggestions, 1):
            confidence_bar = "█" * int(suggestion.confidence * 10)
            print(f"{i}. {suggestion.path}")
            print(f"   Confidence: {confidence_bar} ({suggestion.confidence:.1%})")
            print(f"   Reason: {suggestion.reasoning}")
            print()
        
        print(f"{len(suggestions) + 1}. Create new folder (I'll help you organize)")
        print(f"{len(suggestions) + 2}. Cancel")
        
        while True:
            try:
                choice = input(f"\nSelect option (1-{len(suggestions) + 2}): ").strip()
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(suggestions):
                    selected = suggestions[choice_num - 1]
                    print(f"✅ Selected: {selected.path}")
                    return selected
                elif choice_num == len(suggestions) + 1:
                    return self._create_custom_folder_workflow()
                elif choice_num == len(suggestions) + 2:
                    print("❌ Cancelled")
                    return None
                else:
                    print(f"Please enter a number between 1 and {len(suggestions) + 2}")
            except ValueError:
                print("Please enter a valid number")
    
    def _create_custom_folder_workflow(self) -> Optional[ContentPlacement]:
        """Interactive workflow for creating custom folders"""
        print("\n🏗️  Custom Folder Creation")
        print("=" * 30)
        
        # Get available spaces
        spaces = self.client.list_spaces() or []
        if not spaces:
            print("❌ No accessible Confluence spaces found")
            return None
        
        # Space selection
        print("\nAvailable Spaces:")
        for i, space in enumerate(spaces, 1):
            print(f"{i}. {space['name']} ({space['key']})")
        
        while True:
            try:
                space_choice = input(f"\nSelect space (1-{len(spaces)}): ").strip()
                space_num = int(space_choice)
                if 1 <= space_num <= len(spaces):
                    selected_space = spaces[space_num - 1]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(spaces)}")
            except ValueError:
                print("Please enter a valid number")
        
        # Folder structure input
        folder_name = input("\nEnter folder/page name to create: ").strip()
        if not folder_name:
            print("❌ Folder name cannot be empty")
            return None
        
        # Parent page selection (optional)
        parent_choice = input("\nPlace under existing page? (y/n): ").strip().lower()
        parent_id = None
        parent_title = "Root Level"
        
        if parent_choice == 'y':
            # Simple parent selection - could be enhanced with search
            parent_input = input("Enter parent page title or ID: ").strip()
            if parent_input:
                # Try to find the page
                search_results = self.client.search_content(
                    query=f'title:"{parent_input}"',
                    space_key=selected_space['key'],
                    limit=5
                )
                if search_results:
                    print("\nFound pages:")
                    for i, page in enumerate(search_results, 1):
                        print(f"{i}. {page['title']}")
                    
                    try:
                        parent_choice = input(f"\nSelect parent (1-{len(search_results)}): ").strip()
                        parent_num = int(parent_choice)
                        if 1 <= parent_num <= len(search_results):
                            parent_page = search_results[parent_num - 1]
                            parent_id = parent_page['id']
                            parent_title = parent_page['title']
                    except (ValueError, IndexError):
                        print("Invalid selection, placing at root level")
        
        return ContentPlacement(
            space_key=selected_space['key'],
            parent_id=parent_id,
            parent_title=parent_title,
            path=f"{selected_space['name']} > {parent_title} > {folder_name}",
            confidence=1.0,  # User selected
            reasoning="Custom folder created by user selection"
        )
    
    def create_intelligent_folder(self, placement: ContentPlacement, 
                                folder_name: str) -> Optional[Dict]:
        """
        Create a new folder/page structure based on placement suggestion
        
        Args:
            placement: The placement location
            folder_name: Name of the folder to create
            
        Returns:
            Created page information or None if failed
        """
        print(f"🏗️  Creating folder: {folder_name}")
        print(f"   📍 Location: {placement.path}")
        
        # Create the folder page
        result = self.client.create_page(
            space_key=placement.space_key,
            title=folder_name,
            content=f"""
            <p>This is an organizational folder for related content.</p>
            <p><em>Created automatically by Confluence Organization Agent</em></p>
            <p><strong>Purpose:</strong> {placement.reasoning}</p>
            """,
            parent_id=placement.parent_id
        )
        
        if result:
            print(f"✅ Folder created successfully: {result.get('_links', {}).get('webui', 'Unknown URL')}")
            
            # Log the creation
            self._log_organization_action(
                placement.space_key,
                "folder_creation",
                f"Created folder '{folder_name}' under {placement.parent_title}",
                "success"
            )
        else:
            print(f"❌ Failed to create folder: {folder_name}")
            self._log_organization_action(
                placement.space_key,
                "folder_creation",
                f"Failed to create folder '{folder_name}'",
                "failed"
            )
        
        return result
    
    def _log_organization_action(self, space_key: str, action_type: str, 
                               description: str, result: str):
        """Log organization actions to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO organization_history 
            (space_key, action_type, description, result)
            VALUES (?, ?, ?, ?)
        ''', (space_key, action_type, description, result))
        
        conn.commit()
        conn.close()
    
    def get_organization_status(self) -> Dict[str, Any]:
        """Get current organization status and statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get space statistics
        cursor.execute('SELECT COUNT(*), SUM(total_pages) FROM space_hierarchies')
        spaces_count, total_pages = cursor.fetchone()
        
        # Get recent actions
        cursor.execute('''
            SELECT action_type, COUNT(*), result
            FROM organization_history 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY action_type, result
            ORDER BY COUNT(*) DESC
        ''')
        recent_actions = cursor.fetchall()
        
        conn.close()
        
        return {
            "spaces_analyzed": spaces_count or 0,
            "total_pages_scanned": total_pages or 0,
            "recent_actions": recent_actions,
            "last_scan": "Available in database",
            "status": "Active"
        }


def main():
    """Main function for testing and CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Confluence Organization Manager")
    parser.add_argument("command", choices=["scan", "status", "demo"], 
                       help="Command to execute")
    parser.add_argument("--spaces", nargs="*", 
                       help="Specific spaces to scan (default: all)")
    
    args = parser.parse_args()
    
    manager = ConfluenceOrganizationManager()
    
    if args.command == "scan":
        hierarchies = manager.scan_confluence_spaces(args.spaces)
        print(f"\n📊 Scan Results:")
        for hierarchy in hierarchies:
            print(f"  {hierarchy.space_name}: {hierarchy.total_pages} pages, depth {hierarchy.max_depth}")
            if hierarchy.organizational_patterns:
                print(f"    Patterns: {', '.join(hierarchy.organizational_patterns)}")
    
    elif args.command == "status":
        status = manager.get_organization_status()
        print("\n📈 Organization Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    
    elif args.command == "demo":
        # Demo content placement workflow
        demo_content = """
        This is a technical documentation page about API authentication.
        It covers OAuth implementation, API key management, and security best practices.
        The guide includes code examples and troubleshooting steps.
        """
        
        suggestions = manager.suggest_content_placement(
            demo_content, 
            "API Authentication Guide",
            "technical_doc"
        )
        
        if suggestions:
            selection = manager.interactive_folder_selection(suggestions)
            if selection:
                print(f"\n✅ Demo completed - would place content at: {selection.path}")
        else:
            print("❌ No suggestions generated for demo content")


if __name__ == "__main__":
    main()
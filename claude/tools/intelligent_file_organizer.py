#!/usr/bin/env python3
"""Intelligent File Organizer - Phase 2 Anti-Sprawl Implementation"""
from pathlib import Path

class IntelligentFileOrganizer:
    def __init__(self):
        self.categories = {
            'agents': ('claude/agents/', ['_agent', 'advisor', 'intelligence']),
            'tools': ('claude/tools/', ['.py', 'processor', 'manager']),
            'commands': ('claude/commands/', ['workflow', 'orchestration']),
            'context': ('claude/context/', ['context', 'config']),
            'experimental': ('claude/extensions/experimental/', ['temp', 'test', 'draft']),
            'archive': ('claude/extensions/archive/', ['old', 'deprecated', 'legacy']),
        }
    
    def suggest_organization(self, filepath: str) -> dict:
        """Suggest file organization based on content analysis"""
        path = Path(filepath)
        filename = path.name.lower()
        
        best_category = 'experimental'
        best_score = 0
        
        for category, (directory, keywords) in self.categories.items():
            score = sum(1 for kw in keywords if kw in filename or kw in str(path))
            if score > best_score:
                best_score = score
                best_category = category
        
        suggested_path = self.categories[best_category][0] + path.name
        
        return {
            'current': str(filepath),
            'suggested': suggested_path,
            'category': best_category,
            'confidence': min(100, best_score * 30),
            'action': 'move' if str(filepath) != suggested_path else 'keep'
        }

if __name__ == "__main__":
    import sys
    organizer = IntelligentFileOrganizer()
    
    if len(sys.argv) > 1:
        suggestion = organizer.suggest_organization(sys.argv[1])
        print(f"📁 Current: {suggestion['current']}")
        print(f"💡 Suggested: {suggestion['suggested']}")
        print(f"📊 Confidence: {suggestion['confidence']}%")
        print(f"🔧 Action: {suggestion['action']}")

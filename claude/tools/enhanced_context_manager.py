#!/usr/bin/env python3
"""
Enhanced Context Manager - Provides advanced context management capabilities
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json

class EnhancedContextManager:
    """Enhanced context management for intelligent systems"""
    
    def __init__(self):
        self.contexts = {}
        self.context_history = []
        
    def create_context(self, context_type: str = "general", **kwargs) -> Dict[str, Any]:
        """Create a new context with specified type and parameters"""
        context = {
            "type": context_type,
            "timestamp": str(Path().cwd()),  # Simple timestamp substitute
            "data": kwargs,
            "metadata": {
                "version": "1.0",
                "created_by": "enhanced_context_manager"
            }
        }
        
        context_id = f"{context_type}_{len(self.contexts)}"
        self.contexts[context_id] = context
        self.context_history.append(context_id)
        
        return context
    
    def get_enhanced_context(self, context_id: str = None, **filters) -> Dict[str, Any]:
        """Get enhanced context with optional filtering"""
        if context_id and context_id in self.contexts:
            return self.contexts[context_id]
        
        # Return most recent context if no ID specified
        if self.context_history:
            return self.contexts[self.context_history[-1]]
        
        # Return empty context as fallback
        return self.create_context("fallback")
    
    def update_context(self, context_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing context with new data"""
        if context_id in self.contexts:
            self.contexts[context_id]["data"].update(updates)
            return True
        return False
    
    def list_contexts(self) -> List[str]:
        """List all available context IDs"""
        return list(self.contexts.keys())

# Global context manager instance
_context_manager = None

def get_context_manager() -> EnhancedContextManager:
    """Get global context manager instance"""
    global _context_manager
    if _context_manager is None:
        _context_manager = EnhancedContextManager()
    return _context_manager

# Convenience functions
def create_context(context_type: str = "general", **kwargs) -> Dict[str, Any]:
    """Create context using global manager"""
    return get_context_manager().create_context(context_type, **kwargs)

def get_enhanced_context(context_id: str = None, **filters) -> Dict[str, Any]:
    """Get enhanced context using global manager"""
    return get_context_manager().get_enhanced_context(context_id, **filters)
#!/usr/bin/env python3
"""
Auto Backlog Capture Hook
Automatically captures recommendations and todos from Maia sessions
"""

import sys
import os
import re
from pathlib import Path

# Add Maia to path
sys.path.append(str(Path(__file__).resolve().parents[4] if 'claude/tools' in str(__file__) else Path.cwd()))

from claude.tools.backlog_manager import get_backlog_manager

def detect_recommendations_in_text(text: str) -> list:
    """Detect recommendations in Maia's output"""
    recommendations = []
    
    # Patterns that indicate recommendations
    patterns = [
        r"(?:recommend|suggest|propose|should|could).*?([^.!?]+[.!?])",
        r"next steps?:?\s*(.+?)(?:\n\n|\Z)",
        r"action items?:?\s*(.+?)(?:\n\n|\Z)",
        r"todo:?\s*(.+?)(?:\n|\Z)",
        r"consider:?\s*(.+?)(?:\n|\Z)"
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            rec_text = match.group(1).strip()
            if len(rec_text) > 10:  # Filter out too short items
                recommendations.append(rec_text)
    
    # Detect bullet point lists that look like recommendations
    bullet_patterns = [
        r"[-*•]\s*(.+?)(?:\n|$)",
        r"\d+\.\s*(.+?)(?:\n|$)"
    ]
    
    for pattern in bullet_patterns:
        matches = re.finditer(pattern, text, re.MULTILINE)
        for match in matches:
            item = match.group(1).strip()
            # Check if it looks like a recommendation
            if any(keyword in item.lower() for keyword in ['should', 'could', 'implement', 'create', 'add', 'update', 'fix']):
                if len(item) > 15:
                    recommendations.append(item)
    
    return recommendations

def detect_session_context(text: str) -> dict:
    """Extract session context from text"""
    context = {
        "session_type": "general",
        "topics": [],
        "priority_indicators": []
    }
    
    # Detect session type
    if any(word in text.lower() for word in ['mcp', 'server', 'email', 'integration']):
        context["session_type"] = "mcp_development"
    elif any(word in text.lower() for word in ['security', 'vulnerability', 'audit']):
        context["session_type"] = "security"
    elif any(word in text.lower() for word in ['agent', 'orchestration', 'workflow']):
        context["session_type"] = "agent_development"
    
    # Extract topics
    topic_patterns = [
        r"working on ([^,.!?]+)",
        r"implementing ([^,.!?]+)",
        r"building ([^,.!?]+)"
    ]
    
    for pattern in topic_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            topic = match.group(1).strip()
            if topic not in context["topics"]:
                context["topics"].append(topic)
    
    # Priority indicators
    if any(word in text.lower() for word in ['urgent', 'critical', 'asap', 'immediately']):
        context["priority_indicators"].append("high")
    elif any(word in text.lower() for word in ['future', 'later', 'eventually']):
        context["priority_indicators"].append("low")
    
    return context

def process_maia_output(output_text: str):
    """Process Maia's output and capture recommendations"""
    
    if not output_text or len(output_text) < 50:
        return  # Skip short outputs
    
    try:
        manager = get_backlog_manager()
        
        # Detect recommendations
        recommendations = detect_recommendations_in_text(output_text)
        
        if not recommendations:
            return  # No recommendations found
        
        # Get session context
        context = detect_session_context(output_text)
        
        # Add recommendations to backlog
        for rec in recommendations:
            # Determine priority
            priority = "medium"
            if context["priority_indicators"]:
                priority = context["priority_indicators"][0]
            elif any(word in rec.lower() for word in ['critical', 'urgent', 'important']):
                priority = "high"
            elif any(word in rec.lower() for word in ['future', 'later', 'consider']):
                priority = "low"
            
            # Determine category
            category = context["session_type"]
            
            # Clean up recommendation text
            rec_clean = re.sub(r'^[-*•]\s*', '', rec).strip()
            rec_clean = re.sub(r'^\d+\.\s*', '', rec_clean).strip()
            
            # Create title (first part) and description
            parts = rec_clean.split('.', 1)
            title = parts[0].strip()
            description = rec_clean if len(parts) == 1 else rec_clean
            
            # Add to backlog if not too similar to existing items
            if len(title) > 5 and len(title) < 100:
                manager.add_recommendation(
                    title=title,
                    description=description,
                    category=category,
                    priority=priority,
                    context=f"Auto-captured from {context['session_type']} session",
                    estimated_effort="unknown"
                )
        
        print(f"📋 Auto-captured {len(recommendations)} recommendations to backlog")
        
    except Exception as e:
        # Fail silently - don't interrupt Maia's operation
        pass

def main():
    """Main hook function"""
    if len(sys.argv) > 1:
        # Process input text
        input_text = sys.argv[1]
        process_maia_output(input_text)

if __name__ == "__main__":
    main()

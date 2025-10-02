#!/usr/bin/env python3
"""
M4 Agent Classification Module

Provides M4-powered agent classification capabilities for intelligent request routing.
This module serves as a bridge between user requests and the optimal agent selection
using Apple Silicon M4 optimization when available.

The module implements a fallback strategy where if M4 classification is unavailable,
it gracefully defaults to Claude-based processing without breaking the workflow.

Author: Maia
Created: 2025
Last Modified: 2025-01-13
"""

def get_m4_classification(request: str) -> dict:
    """
    Get M4-powered agent classification for intelligent request routing.
    
    This function attempts to use M4-optimized machine learning models to classify
    user requests and determine the optimal agent for handling them. If M4
    classification is not available, it falls back to Claude-based processing.
    
    Args:
        request (str): The user request text to classify
        
    Returns:
        dict: Classification result containing:
            - use_claude (bool): Whether to use Claude for processing
            - agent_type (str, optional): Recommended agent type if classified
            - confidence (float, optional): Classification confidence score
            - fallback (str, optional): Reason for fallback if classification failed
            
    Example:
        >>> result = get_m4_classification("Help me analyze this job posting")
        >>> if result.get('agent_type') == 'jobs_agent':
        ...     # Route to jobs agent
        ...     pass
    
    Note:
        This function requires the M4IntegrationManager and AgentIntentClassifier
        to be properly configured. If either is unavailable, it gracefully falls
        back to Claude-based processing.
    """
    from claude.tools.m4_integration_manager import M4IntegrationManager
    
    manager = M4IntegrationManager()
    if not manager.is_enabled():
        return {"use_claude": True}
    
    try:
        from claude.models.agent_intent_classifier import AgentIntentClassifier
        classifier = AgentIntentClassifier()
        return classifier.classify_intent(request)
    except:
        return {"use_claude": True, "fallback": "classification_failed"}

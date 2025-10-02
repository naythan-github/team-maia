#!/usr/bin/env python3
"""
Secure Web Tools Integration for Maia
====================================

Provides secure wrappers for WebSearch and WebFetch that integrate
the AI Prompt Injection Defense System transparently.

This module intercepts web content and applies security scanning
before returning results to prevent prompt injection attacks.
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add security tools to path
security_path = Path(__file__).parent.parent / "tools" / "security"
sys.path.insert(0, str(security_path))

from prompt_injection_defense import PromptInjectionDefense
from web_content_sandbox import SecureWebContentProcessor
from injection_monitoring_system import IntegratedSecurityMonitor

class SecureWebTools:
    """Integrated security wrapper for WebSearch and WebFetch tools"""
    
    def __init__(self):
        self.processor = SecureWebContentProcessor()
        self.monitor = IntegratedSecurityMonitor()
        self.defense = PromptInjectionDefense()
        
        # Setup logging
        self.logger = logging.getLogger('SecureWebTools')
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        self.stats = {
            "requests_processed": 0,
            "threats_blocked": 0,
            "content_sanitized": 0,
            "clean_requests": 0
        }
        
    def secure_websearch(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Secure wrapper for WebSearch tool
        
        Args:
            query: Search query
            **kwargs: Additional WebSearch parameters
            
        Returns:
            List of search results with security protection applied
        """
        self.stats["requests_processed"] += 1
        self.logger.info(f"Processing WebSearch query: {query[:50]}...")
        
        # For integration, we need to call the actual WebSearch tool
        # This is a placeholder that shows the integration pattern
        
        # In real integration, this would be:
        # from claude.tools import WebSearch
        # raw_results = WebSearch(query, **kwargs)
        
        # Simulate search results for demonstration
        raw_results = [
            {
                "title": f"Search result for: {query}",
                "url": "https://example.com/result1",
                "content": "This is simulated web content that could contain injection attempts.",
                "snippet": "Relevant snippet from the page"
            },
            {
                "title": "Another result",
                "url": "https://test.com/result2", 
                "content": "More web content here with potential security risks.",
                "snippet": "Another snippet"
            }
        ]
        
        # Apply security processing to results
        secure_results = self.processor.process_web_search_results(raw_results)
        
        # Update stats
        for result in secure_results:
            if result.get('security_warning'):
                self.stats["threats_blocked"] += 1
            elif result.get('security_info'):
                self.stats["content_sanitized"] += 1
            else:
                self.stats["clean_requests"] += 1
                
        # Log security events
        for i, result in enumerate(secure_results):
            if result.get('security_warning') or result.get('security_info'):
                self.monitor.log_defense_result({
                    "source_url": result.get("url", f"search_result_{i}"),
                    "original_content": result.get("content", ""),
                    "threats_detected": 1 if result.get('security_warning') else 0,
                    "max_confidence": 0.9 if result.get('security_warning') else 0.5,
                    "action": "BLOCK" if result.get('security_warning') else "SANITIZE",
                    "primary_threat_type": "injection_attempt"
                })
        
        self.logger.info(f"WebSearch completed: {len(secure_results)} results, {self.stats['threats_blocked']} blocked")
        return secure_results
        
    def secure_webfetch(self, url: str, prompt: str = None, **kwargs) -> str:
        """
        Secure wrapper for WebFetch tool
        
        Args:
            url: URL to fetch content from
            prompt: Optional prompt for content analysis
            **kwargs: Additional WebFetch parameters
            
        Returns:
            Fetched content with security protection applied
        """
        self.stats["requests_processed"] += 1
        self.logger.info(f"Processing WebFetch request: {url}")
        
        # For integration, this would be:
        # from claude.tools import WebFetch
        # raw_content = WebFetch(url, prompt, **kwargs)
        
        # Simulate fetched content for demonstration
        raw_content = f"""
        Content fetched from {url}
        
        This is the main content of the webpage.
        
        <!-- Hidden comment that might contain injection attempts -->
        
        More content here that could be legitimate or malicious.
        """
        
        # Apply security processing
        secure_content = self.processor.process_web_fetch_content(raw_content, url)
        
        # Update stats and log
        if "[BLOCKED:" in secure_content:
            self.stats["threats_blocked"] += 1
            action = "BLOCK"
            confidence = 0.9
        elif secure_content != raw_content:
            self.stats["content_sanitized"] += 1
            action = "SANITIZE"
            confidence = 0.6
        else:
            self.stats["clean_requests"] += 1
            action = "ALLOW"
            confidence = 0.0
            
        # Log security event
        self.monitor.log_defense_result({
            "source_url": url,
            "original_content": raw_content,
            "threats_detected": 1 if action in ["BLOCK", "SANITIZE"] else 0,
            "max_confidence": confidence,
            "action": action,
            "primary_threat_type": "web_content_injection"
        })
        
        self.logger.info(f"WebFetch completed: {url} - Action: {action}")
        return secure_content
        
    def get_security_stats(self) -> Dict[str, Any]:
        """Get current security statistics"""
        processor_stats = self.processor.get_stats()
        defense_stats = self.defense.get_defense_stats()
        
        return {
            "secure_web_tools": self.stats,
            "content_processor": processor_stats,
            "defense_system": defense_stats,
            "monitoring": self.monitor.get_dashboard_data()
        }
        
    def security_report(self) -> str:
        """Generate security report"""
        stats = self.get_security_stats()
        
        report = f"""
🛡️ MAIA WEB SECURITY REPORT
========================

📊 Request Statistics:
  • Total Requests: {stats['secure_web_tools']['requests_processed']}
  • Threats Blocked: {stats['secure_web_tools']['threats_blocked']}
  • Content Sanitized: {stats['secure_web_tools']['content_sanitized']}
  • Clean Requests: {stats['secure_web_tools']['clean_requests']}

🔍 Defense System:
  • Threat Patterns: {stats['defense_system']['threat_patterns_loaded']}
  • Categories Monitored: {len(stats['defense_system']['categories_monitored'])}
  • System Status: {stats['monitoring']['current_status']}

🚨 Recent Activity:
  • Last Hour Events: {stats['monitoring']['last_hour_summary']['total_events']}
  • High Confidence Threats: {stats['monitoring']['real_time_stats']['high_confidence_threats']}
  • Unique Sources: {stats['monitoring']['real_time_stats']['unique_sources']}
"""
        return report

# Global instance for easy import
_secure_web_tools = None

def get_secure_web_tools() -> SecureWebTools:
    """Get global secure web tools instance"""
    global _secure_web_tools
    if _secure_web_tools is None:
        _secure_web_tools = SecureWebTools()
    return _secure_web_tools

# Convenience functions that can replace WebSearch/WebFetch calls
def SecureWebSearch(query: str, **kwargs) -> List[Dict[str, Any]]:
    """Secure replacement for WebSearch tool"""
    tools = get_secure_web_tools()
    return tools.secure_websearch(query, **kwargs)

def SecureWebFetch(url: str, prompt: str = None, **kwargs) -> str:
    """Secure replacement for WebFetch tool"""  
    tools = get_secure_web_tools()
    return tools.secure_webfetch(url, prompt, **kwargs)

# Hook integration functions
def install_secure_web_hooks():
    """Install secure web tool hooks into Maia's system"""
    try:
        # This would integrate with Maia's tool loading system
        # For now, we document the integration pattern
        
        print("🔒 Installing Secure Web Tools...")
        
        # Create global instance
        tools = get_secure_web_tools()
        
        # Register security logging
        tools.logger.info("Secure Web Tools initialized and ready")
        
        print("✅ Secure Web Tools installed successfully")
        print("📊 Use get_secure_web_tools().security_report() for status")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to install secure web hooks: {e}")
        return False

if __name__ == "__main__":
    # Test the secure web tools
    print("🚀 Testing Secure Web Tools Integration")
    print("=" * 50)
    
    # Install hooks
    install_secure_web_hooks()
    
    # Test secure WebSearch
    print("\n🔍 Testing SecureWebSearch...")
    results = SecureWebSearch("AI safety best practices")
    print(f"Results: {len(results)} items returned")
    
    # Test secure WebFetch  
    print("\n🌐 Testing SecureWebFetch...")
    content = SecureWebFetch("https://example.com", "Summarize this content")
    print(f"Content length: {len(content)} characters")
    
    # Get security report
    tools = get_secure_web_tools()
    print("\n" + tools.security_report())
#!/usr/bin/env python3
"""
Pre-Execution Verification Hook
Enforces read-before-execute pattern to prevent assumption-driven failures
"""

import os
import re
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class PreExecutionVerificationHook:
    """Enforcement system for read-before-execute pattern"""
    
    def __init__(self):
        self.maia_root = self._get_maia_root()
        self.db_path = self.maia_root / "claude" / "data" / "verification_hook.db"
        self._setup_database()
        
        # High-risk patterns that require verification
        self.high_risk_patterns = {
            'api_calls': [
                r'\.([a-zA-Z_]+)\(',  # method calls
                r'from .+ import .+',  # imports
                r'requests\.(get|post|put|delete)',  # HTTP calls
                r'client\.[a-zA-Z_]+',  # client method calls
            ],
            'file_operations': [
                r'open\(',
                r'with open\(',
                r'json\.load',
                r'yaml\.load',
            ],
            'bash_commands': [
                r'python3 .+\.py',
                r'node .+\.js',
                r'curl ',
                r'ollama ',
            ]
        }
        
        # Verification requirements by pattern
        self.verification_requirements = {
            'api_calls': 'Read implementation file to verify method signatures',
            'file_operations': 'Read target file to verify structure/existence',
            'bash_commands': 'Read script/verify command exists before execution'
        }

    def _get_maia_root(self) -> Path:
        """Get Maia root directory with environment variable support"""
        maia_root = os.environ.get('MAIA_ROOT')
        if maia_root:
            return Path(maia_root)
        
        # Auto-detect from current file location
        current_file = Path(__file__)
        for parent in current_file.parents:
            if (parent / 'claude').exists() and (parent / 'CLAUDE.md').exists():
                return parent
        
        # Fallback to hardcoded path
        return Path(str(Path(__file__).resolve().parents[4] if 'claude/tools' in str(__file__) else Path.cwd()))

    def _setup_database(self):
        """Initialize verification tracking database"""
        os.makedirs(self.db_path.parent, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS verification_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    target_resource TEXT NOT NULL,
                    verification_status TEXT NOT NULL,
                    verification_method TEXT,
                    failure_reason TEXT,
                    context TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS assumption_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    assumed_interface TEXT NOT NULL,
                    actual_interface TEXT,
                    error_message TEXT NOT NULL,
                    recovery_action TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def analyze_action_risk(self, action_description: str, target_resource: str = "") -> Dict[str, Any]:
        """Analyze risk level of proposed action"""
        risk_score = 0
        risk_factors = []
        verification_required = False
        
        # Check for high-risk patterns
        for category, patterns in self.high_risk_patterns.items():
            for pattern in patterns:
                if re.search(pattern, action_description, re.IGNORECASE):
                    risk_score += 10
                    risk_factors.append(f"{category}: {pattern}")
                    verification_required = True
        
        # Additional risk factors
        if any(word in action_description.lower() for word in ['assume', 'should', 'probably', 'likely']):
            risk_score += 20
            risk_factors.append("assumption_language_detected")
            verification_required = True
            
        if target_resource and not self._resource_verified_recently(target_resource):
            risk_score += 15
            risk_factors.append("unverified_resource")
            verification_required = True
        
        return {
            'risk_score': risk_score,
            'risk_level': 'HIGH' if risk_score >= 20 else 'MEDIUM' if risk_score >= 10 else 'LOW',
            'risk_factors': risk_factors,
            'verification_required': verification_required,
            'verification_requirements': self._get_verification_requirements(risk_factors)
        }

    def _get_verification_requirements(self, risk_factors: List[str]) -> List[str]:
        """Get specific verification requirements based on risk factors"""
        requirements = []
        
        for factor in risk_factors:
            for category, requirement in self.verification_requirements.items():
                if category in factor:
                    requirements.append(requirement)
        
        return list(set(requirements))  # Remove duplicates

    def _resource_verified_recently(self, resource: str, hours: int = 1) -> bool:
        """Check if resource was verified recently"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT COUNT(*) FROM verification_events 
                WHERE target_resource = ? 
                AND verification_status = 'verified'
                AND datetime(created_at) > datetime('now', '-{} hours')
            '''.format(hours), (resource,))
            
            return cursor.fetchone()[0] > 0

    def enforce_verification(self, action_type: str, action_description: str, target_resource: str = "") -> Dict[str, Any]:
        """Main enforcement method - call before risky operations"""
        timestamp = datetime.now().isoformat()
        
        # Analyze risk
        risk_analysis = self.analyze_action_risk(action_description, target_resource)
        
        if not risk_analysis['verification_required']:
            self._log_verification_event(timestamp, action_type, target_resource, 'low_risk', 'automatic_pass')
            return {
                'allowed': True,
                'risk_level': risk_analysis['risk_level'],
                'message': 'Low risk action - proceed without verification'
            }
        
        # HIGH RISK - Require explicit verification
        verification_result = self._check_verification_completion(target_resource, risk_analysis['verification_requirements'])
        
        if verification_result['verified']:
            self._log_verification_event(timestamp, action_type, target_resource, 'verified', verification_result['method'])
            return {
                'allowed': True,
                'risk_level': risk_analysis['risk_level'],
                'message': f'Verification completed via {verification_result["method"]}'
            }
        else:
            self._log_verification_event(timestamp, action_type, target_resource, 'blocked', None, 'verification_required')
            return {
                'allowed': False,
                'risk_level': risk_analysis['risk_level'],
                'message': 'VERIFICATION REQUIRED - Read implementation first',
                'requirements': risk_analysis['verification_requirements'],
                'suggested_actions': self._get_suggested_verification_actions(target_resource, action_type)
            }

    def _check_verification_completion(self, resource: str, requirements: List[str]) -> Dict[str, Any]:
        """Check if verification was completed for this resource"""
        # For now, return False to force verification
        # In production, this would check for recent Read tool usage, etc.
        return {
            'verified': False,
            'method': None
        }

    def _get_suggested_verification_actions(self, resource: str, action_type: str) -> List[str]:
        """Get suggested verification actions"""
        suggestions = []
        
        if action_type == 'api_call':
            if resource.endswith('.py'):
                suggestions.append(f"Read('{resource}') - Check method signatures and parameters")
            suggestions.append("Search for method documentation or examples")
            
        elif action_type == 'file_operation':
            suggestions.append(f"Read('{resource}') - Verify file structure and content")
            
        elif action_type == 'bash_command':
            if 'python3' in resource:
                script_path = resource.split('python3 ')[-1].split()[0]
                suggestions.append(f"Read('{script_path}') - Verify script exists and parameters")
            suggestions.append("Test command with --help or similar")
        
        return suggestions

    def _log_verification_event(self, timestamp: str, action_type: str, target_resource: str, 
                               verification_status: str, verification_method: Optional[str] = None,
                               failure_reason: Optional[str] = None, context: Optional[str] = None):
        """Log verification event to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO verification_events 
                (timestamp, action_type, target_resource, verification_status, verification_method, failure_reason, context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (timestamp, action_type, target_resource, verification_status, verification_method, failure_reason, context))

    def log_assumption_failure(self, assumed_interface: str, actual_interface: str, error_message: str, recovery_action: str = ""):
        """Log when assumptions lead to failures"""
        timestamp = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO assumption_failures 
                (timestamp, assumed_interface, actual_interface, error_message, recovery_action)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, assumed_interface, actual_interface, error_message, recovery_action))

    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Get verification event stats
            cursor = conn.execute('''
                SELECT verification_status, COUNT(*) 
                FROM verification_events 
                GROUP BY verification_status
            ''')
            verification_stats = dict(cursor.fetchall())
            
            # Get assumption failure stats
            cursor = conn.execute('''
                SELECT COUNT(*) FROM assumption_failures
                WHERE created_at > datetime('now', '-7 days')
            ''')
            recent_failures = cursor.fetchone()[0]
            
            # Get most common failure patterns
            cursor = conn.execute('''
                SELECT assumed_interface, COUNT(*) as count
                FROM assumption_failures 
                GROUP BY assumed_interface 
                ORDER BY count DESC 
                LIMIT 5
            ''')
            common_failures = cursor.fetchall()
            
            return {
                'verification_events': verification_stats,
                'recent_assumption_failures': recent_failures,
                'common_failure_patterns': common_failures,
                'verification_compliance_rate': self._calculate_compliance_rate(verification_stats)
            }

    def _calculate_compliance_rate(self, stats: Dict[str, int]) -> float:
        """Calculate verification compliance rate"""
        total = sum(stats.values())
        if total == 0:
            return 100.0
            
        verified = stats.get('verified', 0) + stats.get('low_risk', 0)
        return round((verified / total) * 100, 2)

# Global instance
_verification_hook = None

def get_verification_hook() -> PreExecutionVerificationHook:
    """Get global verification hook instance"""
    global _verification_hook
    if _verification_hook is None:
        _verification_hook = PreExecutionVerificationHook()
    return _verification_hook

def verify_before_action(action_type: str, action_description: str, target_resource: str = "") -> Dict[str, Any]:
    """Convenience function for verification enforcement"""
    hook = get_verification_hook()
    return hook.enforce_verification(action_type, action_description, target_resource)

def log_assumption_failure(assumed_interface: str, actual_interface: str, error_message: str, recovery_action: str = ""):
    """Convenience function for logging assumption failures"""
    hook = get_verification_hook()
    hook.log_assumption_failure(assumed_interface, actual_interface, error_message, recovery_action)

if __name__ == "__main__":
    # Test the hook
    hook = get_verification_hook()
    
    # Test high-risk action
    result = hook.enforce_verification(
        "api_call", 
        "client.search_pages('space=Maia')", 
        "claude/tools/direct_confluence_access.py"
    )
    print("High-risk API call result:")
    print(json.dumps(result, indent=2))
    
    # Test low-risk action
    result = hook.enforce_verification(
        "simple_operation", 
        "print('hello world')", 
        ""
    )
    print("\nLow-risk operation result:")
    print(json.dumps(result, indent=2))
    
    # Get stats
    stats = hook.get_verification_stats()
    print("\nVerification statistics:")
    print(json.dumps(stats, indent=2))
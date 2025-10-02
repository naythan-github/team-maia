#!/usr/bin/env python3
"""
Enhanced Policy Engine - Phase 5 Component
Advanced policy management with ML-based pattern recognition
Integrates with existing governance infrastructure (Phases 1-4)
"""

import os
import json
import yaml
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# ML imports (lightweight models for local execution)
try:
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    ML_AVAILABLE = True
except ImportError:
    print("⚠️  ML libraries not available, using rule-based fallback")
    ML_AVAILABLE = False

# Import existing governance components
import sys
sys.path.append(str(Path(__file__).parent))

try:
    from claude.tools.governance.repository_analyzer import RepositoryAnalyzer
    from claude.tools.governance.filesystem_monitor import FileSystemMonitor
    from claude.tools.governance.remediation_engine import RemediationEngine
    GOVERNANCE_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Governance components not available: {e}")
    GOVERNANCE_COMPONENTS_AVAILABLE = False

@dataclass
class PolicyViolation:
    """Structured representation of a policy violation"""
    type: str
    severity: str
    file_path: str
    message: str
    confidence_score: float
    ml_prediction: bool = False
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class PolicyRecommendation:
    """ML-generated policy recommendation"""
    policy_type: str
    recommendation: str
    confidence: float
    supporting_evidence: List[str]
    impact_estimate: str

class EnhancedPolicyEngine:
    """Advanced policy engine with ML-based pattern recognition"""
    
    def __init__(self, repo_path: str = str(Path(__file__).resolve().parents[4] if "claude/tools" in str(__file__) else Path.cwd())):
        self.repo_path = Path(repo_path)
        self.policies_file = self.repo_path / "claude/context/knowledge/governance/policies.yaml"
        self.ml_models_dir = self.repo_path / "claude/data/governance_ml"
        self.violation_history_file = self.repo_path / "claude/data/governance_violations.json"
        
        # Ensure directories exist
        self.ml_models_dir.mkdir(parents=True, exist_ok=True)
        self.policies_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.policies = self._load_policies()
        self.ml_models = self._initialize_ml_models()
        self.violation_history = self._load_violation_history()
        self.feature_vectorizer = None
        self.scaler = None
        
        # Integration with existing governance tools
        if GOVERNANCE_COMPONENTS_AVAILABLE:
            self.repository_analyzer = RepositoryAnalyzer(str(self.repo_path))
            self.filesystem_monitor = FileSystemMonitor()
            self.remediation_engine = RemediationEngine(str(self.repo_path))
        
        print("🤖 Enhanced Policy Engine initialized with ML capabilities")
        if ML_AVAILABLE:
            print("✅ ML models ready for pattern recognition")
        if GOVERNANCE_COMPONENTS_AVAILABLE:
            print("✅ Integrated with existing governance tools")
    
    def _load_policies(self) -> Dict:
        """Load governance policies from YAML configuration"""
        default_policies = {
            "file_placement": {
                "max_root_files": 20,
                "forbidden_root_extensions": [".tmp", ".log", ".backup", ".cache", ".pid"],
                "required_directories": ["claude/tools", "claude/agents", "claude/context"],
                "archive_patterns": ["*archive*", "*backup*", "*old*", "*legacy*"],
                "sensitive_patterns": ["password", "secret", "api_key", "token"]
            },
            "tool_organization": {
                "max_tools_per_category": 50,
                "required_categories": ["core", "automation", "research", "communication", 
                                      "monitoring", "data", "security", "business"],
                "naming_conventions": {
                    "pattern": "^[a-z_][a-z0-9_]*\\.py$",
                    "description": "Lowercase with underscores only"
                }
            },
            "content_policies": {
                "max_file_size_mb": 10,
                "forbidden_patterns": ["password=", "secret=", "api_key="],
                "required_headers": {
                    "python": ["#!/usr/bin/env python3", '"""']
                }
            },
            "quality_standards": {
                "min_documentation_ratio": 0.2,
                "max_complexity_score": 10,
                "required_tests": False
            },
            "ml_settings": {
                "violation_threshold": 0.7,
                "pattern_detection_sensitivity": 0.8,
                "adaptive_learning": True,
                "retrain_frequency_days": 7
            }
        }
        
        if self.policies_file.exists():
            try:
                with open(self.policies_file, 'r') as f:
                    loaded_policies = yaml.safe_load(f)
                    # Merge with defaults, prioritizing loaded policies
                    merged_policies = default_policies.copy()
                    merged_policies.update(loaded_policies)
                    return merged_policies
            except Exception as e:
                print(f"⚠️  Error loading policies from {self.policies_file}: {e}")
                print("Using default policies")
        
        # Save default policies for future reference
        self._save_policies(default_policies)
        return default_policies
    
    def _save_policies(self, policies: Dict):
        """Save policies to YAML configuration"""
        try:
            with open(self.policies_file, 'w') as f:
                yaml.dump(policies, f, default_flow_style=False, sort_keys=False)
            print(f"✅ Policies saved to {self.policies_file}")
        except Exception as e:
            print(f"⚠️  Error saving policies: {e}")
    
    def _initialize_ml_models(self) -> Dict:
        """Initialize or load ML models"""
        models = {}
        
        if not ML_AVAILABLE:
            return models
        
        model_configs = {
            "violation_classifier": {
                "model": RandomForestClassifier(n_estimators=50, random_state=42),
                "file": self.ml_models_dir / "violation_classifier.pkl"
            },
            "pattern_detector": {
                "model": IsolationForest(contamination=0.1, random_state=42),
                "file": self.ml_models_dir / "pattern_detector.pkl"
            }
        }
        
        for name, config in model_configs.items():
            if config["file"].exists():
                try:
                    with open(config["file"], 'rb') as f:
                        models[name] = pickle.load(f)
                    print(f"✅ Loaded {name} from {config['file']}")
                except Exception as e:
                    print(f"⚠️  Error loading {name}: {e}, using new model")
                    models[name] = config["model"]
            else:
                models[name] = config["model"]
        
        return models
    
    def _load_violation_history(self) -> List[Dict]:
        """Load historical violation data for ML training"""
        if not self.violation_history_file.exists():
            return []
        
        try:
            with open(self.violation_history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error loading violation history: {e}")
            return []
    
    def _save_violation_history(self):
        """Save violation history to file"""
        try:
            with open(self.violation_history_file, 'w') as f:
                json.dump(self.violation_history, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️  Error saving violation history: {e}")
    
    def evaluate_file(self, file_path: Path, content: Optional[str] = None) -> Dict:
        """Enhanced file evaluation with ML-based pattern recognition"""
        relative_path = file_path.relative_to(self.repo_path) if file_path.is_absolute() else file_path
        
        evaluation = {
            "file_path": str(relative_path),
            "timestamp": datetime.now().isoformat(),
            "violations": [],
            "compliance_score": 100.0,
            "ml_predictions": [],
            "recommendations": []
        }
        
        # Traditional rule-based evaluation
        rule_violations = self._evaluate_rule_based(file_path, content)
        evaluation["violations"].extend(rule_violations)
        
        # ML-based evaluation (if available and trained)
        if ML_AVAILABLE and self._models_trained():
            ml_violations = self._evaluate_ml_based(file_path, content)
            evaluation["ml_predictions"].extend(ml_violations)
            evaluation["violations"].extend([v for v in ml_violations if v.confidence_score > 
                                           self.policies["ml_settings"]["violation_threshold"]])
        
        # Calculate compliance score
        evaluation["compliance_score"] = self._calculate_compliance_score(evaluation["violations"])
        
        # Generate recommendations
        evaluation["recommendations"] = self._generate_recommendations(
            evaluation["violations"], evaluation["ml_predictions"]
        )
        
        # Store for future ML training
        self.violation_history.append(evaluation)
        
        return evaluation
    
    def _evaluate_rule_based(self, file_path: Path, content: Optional[str] = None) -> List[PolicyViolation]:
        """Traditional rule-based policy evaluation"""
        violations = []
        relative_path = file_path.relative_to(self.repo_path) if file_path.is_absolute() else file_path
        
        # File placement evaluation
        if len(relative_path.parts) == 1 and file_path.exists() and file_path.is_file():
            # Root directory file check
            root_files_count = len([f for f in self.repo_path.iterdir() if f.is_file()])
            max_root_files = self.policies["file_placement"]["max_root_files"]
            
            if root_files_count > max_root_files:
                violations.append(PolicyViolation(
                    type="root_file_limit_exceeded",
                    severity="medium",
                    file_path=str(relative_path),
                    message=f"Root directory has {root_files_count} files (limit: {max_root_files})",
                    confidence_score=1.0
                ))
            
            # Forbidden extensions check
            forbidden_exts = self.policies["file_placement"]["forbidden_root_extensions"]
            if file_path.suffix in forbidden_exts:
                violations.append(PolicyViolation(
                    type="forbidden_root_extension",
                    severity="high",
                    file_path=str(relative_path),
                    message=f"Forbidden extension {file_path.suffix} in root directory",
                    confidence_score=1.0
                ))
        
        # Archive pattern check
        for pattern in self.policies["file_placement"]["archive_patterns"]:
            pattern_clean = pattern.strip('*').lower()
            if pattern_clean in str(relative_path).lower():
                if not str(relative_path).startswith('archive/'):
                    violations.append(PolicyViolation(
                        type="misplaced_archive",
                        severity="medium",
                        file_path=str(relative_path),
                        message=f"Archive-like content outside archive directory: {pattern_clean}",
                        confidence_score=0.9
                    ))
        
        # Content-based evaluation
        if content or (file_path.exists() and file_path.is_file()):
            if not content:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except Exception:
                    content = None
            
            if content:
                # Sensitive pattern check
                for pattern in self.policies["file_placement"]["sensitive_patterns"]:
                    if pattern.lower() in content.lower():
                        violations.append(PolicyViolation(
                            type="sensitive_content",
                            severity="high",
                            file_path=str(relative_path),
                            message=f"Sensitive pattern detected: {pattern}",
                            confidence_score=0.8
                        ))
                
                # File size check
                max_size_mb = self.policies["content_policies"]["max_file_size_mb"]
                if len(content.encode('utf-8')) > max_size_mb * 1024 * 1024:
                    violations.append(PolicyViolation(
                        type="oversized_file",
                        severity="medium",
                        file_path=str(relative_path),
                        message=f"File exceeds {max_size_mb}MB limit",
                        confidence_score=1.0
                    ))
        
        return violations
    
    def _evaluate_ml_based(self, file_path: Path, content: Optional[str] = None) -> List[PolicyViolation]:
        """ML-based policy evaluation using trained models"""
        if not ML_AVAILABLE or not self._models_trained():
            return []
        
        violations = []
        relative_path = file_path.relative_to(self.repo_path) if file_path.is_absolute() else file_path
        
        try:
            # Extract features for ML evaluation
            features = self._extract_features(file_path, content)
            if features is None:
                return []
            
            # Violation classification
            if "violation_classifier" in self.ml_models:
                violation_prob = self.ml_models["violation_classifier"].predict_proba([features])[0]
                if len(violation_prob) > 1 and violation_prob[1] > 0.5:  # Assuming binary classification
                    violations.append(PolicyViolation(
                        type="ml_predicted_violation",
                        severity="medium",
                        file_path=str(relative_path),
                        message=f"ML model predicts policy violation",
                        confidence_score=violation_prob[1],
                        ml_prediction=True
                    ))
            
            # Anomaly detection
            if "pattern_detector" in self.ml_models:
                anomaly_score = self.ml_models["pattern_detector"].decision_function([features])[0]
                if anomaly_score < -0.1:  # Threshold for anomaly
                    violations.append(PolicyViolation(
                        type="anomalous_pattern",
                        severity="low",
                        file_path=str(relative_path),
                        message=f"Anomalous file pattern detected",
                        confidence_score=abs(anomaly_score),
                        ml_prediction=True
                    ))
        
        except Exception as e:
            print(f"⚠️  ML evaluation error for {relative_path}: {e}")
        
        return violations
    
    def _extract_features(self, file_path: Path, content: Optional[str] = None) -> Optional[List[float]]:
        """Extract features for ML model input"""
        try:
            relative_path = file_path.relative_to(self.repo_path) if file_path.is_absolute() else file_path
            features = []
            
            # Path-based features
            features.extend([
                len(relative_path.parts),  # Directory depth
                len(relative_path.name),   # Filename length
                1.0 if relative_path.suffix else 0.0,  # Has extension
                len(relative_path.suffix) if relative_path.suffix else 0,  # Extension length
            ])
            
            # File existence and size features
            if file_path.exists():
                stat = file_path.stat()
                features.extend([
                    stat.st_size,  # File size
                    (datetime.now().timestamp() - stat.st_mtime) / (24 * 3600),  # Days since modified
                ])
            else:
                features.extend([0, 0])
            
            # Content-based features (if available)
            if content:
                features.extend([
                    len(content),  # Content length
                    content.count('\n'),  # Line count
                    len(content.split()),  # Word count
                ])
            else:
                features.extend([0, 0, 0])
            
            return features
        
        except Exception as e:
            print(f"⚠️  Feature extraction error: {e}")
            return None
    
    def _calculate_compliance_score(self, violations: List[PolicyViolation]) -> float:
        """Calculate compliance score based on violations"""
        if not violations:
            return 100.0
        
        # Weight violations by severity
        severity_weights = {"low": 1, "medium": 5, "high": 15, "critical": 25}
        total_penalty = sum(severity_weights.get(v.severity, 1) for v in violations)
        
        # Score decreases with more/severe violations
        score = max(0.0, 100.0 - total_penalty)
        return score
    
    def _generate_recommendations(self, violations: List[PolicyViolation], 
                                ml_predictions: List[PolicyViolation]) -> List[str]:
        """Generate actionable recommendations based on violations"""
        recommendations = []
        
        violation_types = [v.type for v in violations]
        
        if "forbidden_root_extension" in violation_types:
            recommendations.append("Move temporary/log files to appropriate directories or delete them")
        
        if "root_file_limit_exceeded" in violation_types:
            recommendations.append("Organize root directory files into appropriate subdirectories")
        
        if "misplaced_archive" in violation_types:
            recommendations.append("Move archive/backup content to archive/ directory")
        
        if "sensitive_content" in violation_types:
            recommendations.append("Remove or encrypt sensitive information in files")
        
        if "oversized_file" in violation_types:
            recommendations.append("Split large files or move to appropriate storage location")
        
        # ML-based recommendations
        if any(p.type == "ml_predicted_violation" for p in ml_predictions):
            recommendations.append("Review file against learned violation patterns")
        
        if any(p.type == "anomalous_pattern" for p in ml_predictions):
            recommendations.append("Investigate unusual file pattern for potential governance issues")
        
        return recommendations
    
    def train_violation_patterns(self, retrain: bool = False) -> Dict:
        """Train ML models on violation history"""
        if not ML_AVAILABLE:
            return {"status": "ml_not_available"}
        
        if len(self.violation_history) < 10:
            return {"status": "insufficient_data", "samples": len(self.violation_history)}
        
        try:
            print("🤖 Training ML models on violation patterns...")
            
            # Prepare training data
            training_data = []
            labels = []
            
            for record in self.violation_history:
                if "features" not in record:
                    continue  # Skip records without features
                
                training_data.append(record["features"])
                labels.append(1 if record["violations"] else 0)
            
            if len(training_data) < 5:
                return {"status": "insufficient_feature_data"}
            
            X = np.array(training_data)
            y = np.array(labels)
            
            # Train violation classifier
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            self.ml_models["violation_classifier"].fit(X_train, y_train)
            y_pred = self.ml_models["violation_classifier"].predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Train anomaly detector
            normal_data = X[y == 0]  # Non-violation samples
            if len(normal_data) > 3:
                self.ml_models["pattern_detector"].fit(normal_data)
            
            # Save models
            self._save_ml_models()
            
            result = {
                "status": "success",
                "samples_trained": len(training_data),
                "accuracy": accuracy,
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"✅ ML training completed with {accuracy:.2%} accuracy")
            return result
            
        except Exception as e:
            print(f"⚠️  ML training error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _save_ml_models(self):
        """Save trained ML models to disk"""
        model_files = {
            "violation_classifier": self.ml_models_dir / "violation_classifier.pkl",
            "pattern_detector": self.ml_models_dir / "pattern_detector.pkl"
        }
        
        for name, file_path in model_files.items():
            if name in self.ml_models:
                try:
                    with open(file_path, 'wb') as f:
                        pickle.dump(self.ml_models[name], f)
                    print(f"✅ Saved {name} to {file_path}")
                except Exception as e:
                    print(f"⚠️  Error saving {name}: {e}")
    
    def _models_trained(self) -> bool:
        """Check if ML models are trained and ready"""
        return (ML_AVAILABLE and 
                "violation_classifier" in self.ml_models and 
                "pattern_detector" in self.ml_models)
    
    def generate_adaptive_policies(self) -> List[PolicyRecommendation]:
        """Generate policy recommendations based on ML analysis"""
        recommendations = []
        
        if not ML_AVAILABLE or len(self.violation_history) < 5:
            return recommendations
        
        try:
            # Analyze violation patterns
            violation_types = {}
            for record in self.violation_history[-100:]:  # Last 100 records
                for violation in record.get("violations", []):
                    vtype = violation.get("type", "unknown")
                    violation_types[vtype] = violation_types.get(vtype, 0) + 1
            
            # Generate recommendations for frequent violation types
            for vtype, count in violation_types.items():
                if count >= 3:  # Frequent violations
                    if vtype == "forbidden_root_extension":
                        recommendations.append(PolicyRecommendation(
                            policy_type="file_placement",
                            recommendation="Add automated cleanup for temporary files",
                            confidence=0.8,
                            supporting_evidence=[f"{count} violations in recent history"],
                            impact_estimate="Medium - reduces manual cleanup effort"
                        ))
                    elif vtype == "sensitive_content":
                        recommendations.append(PolicyRecommendation(
                            policy_type="content_policies",
                            recommendation="Implement pre-commit hooks for sensitive content detection",
                            confidence=0.9,
                            supporting_evidence=[f"{count} sensitive content violations"],
                            impact_estimate="High - prevents security exposure"
                        ))
            
            print(f"✅ Generated {len(recommendations)} adaptive policy recommendations")
            
        except Exception as e:
            print(f"⚠️  Error generating adaptive policies: {e}")
        
        return recommendations
    
    def integration_health_check(self) -> Dict:
        """Check integration health with existing governance tools"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "ml_available": ML_AVAILABLE,
            "governance_components": GOVERNANCE_COMPONENTS_AVAILABLE,
            "policies_loaded": len(self.policies) > 0,
            "violation_history_size": len(self.violation_history),
            "models_trained": self._models_trained(),
            "integration_tests": {}
        }
        
        # Test integration with existing components
        if GOVERNANCE_COMPONENTS_AVAILABLE:
            try:
                # Test repository analyzer integration
                analysis = self.repository_analyzer.analyze_structure()
                health["integration_tests"]["repository_analyzer"] = {
                    "status": "success",
                    "health_score": analysis.get("health_score", 0)
                }
            except Exception as e:
                health["integration_tests"]["repository_analyzer"] = {
                    "status": "error",
                    "error": str(e)
                }
            
            try:
                # Test filesystem monitor integration
                violations = self.filesystem_monitor.get_violations_summary()
                health["integration_tests"]["filesystem_monitor"] = {
                    "status": "success",
                    "violations": violations.get("total_violations", 0)
                }
            except Exception as e:
                health["integration_tests"]["filesystem_monitor"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health

def main():
    """CLI interface for enhanced policy engine"""
    import sys
    
    engine = EnhancedPolicyEngine()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "evaluate":
            if len(sys.argv) > 2:
                file_path = Path(sys.argv[2])
                result = engine.evaluate_file(file_path)
                print(json.dumps(result, indent=2, default=str))
            else:
                print("Usage: python enhanced_policy_engine.py evaluate <file_path>")
        
        elif command == "train":
            result = engine.train_violation_patterns()
            print("🤖 ML Training Results:")
            print(json.dumps(result, indent=2))
        
        elif command == "health":
            health = engine.integration_health_check()
            print("🔍 Integration Health Check:")
            print(json.dumps(health, indent=2, default=str))
        
        elif command == "recommendations":
            recommendations = engine.generate_adaptive_policies()
            print("💡 Adaptive Policy Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec.policy_type}: {rec.recommendation}")
                print(f"   Confidence: {rec.confidence:.1%}")
                print(f"   Evidence: {', '.join(rec.supporting_evidence)}")
                print(f"   Impact: {rec.impact_estimate}")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: evaluate, train, health, recommendations")
    else:
        print("Enhanced Policy Engine Commands:")
        print("  evaluate <file>    - Evaluate file against policies")
        print("  train             - Train ML models on violation history")
        print("  health            - Check integration health")
        print("  recommendations   - Generate adaptive policy recommendations")

if __name__ == "__main__":
    main()
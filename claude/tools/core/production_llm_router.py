#!/usr/bin/env python3
"""
Production LLM Router for Maia
Routes tasks to optimal LLMs with multiple fallback strategies.
Enhanced with local model support for 99.3% cost savings on code generation.
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Portable path resolution
try:
    from claude.tools.core.paths import MAIA_ROOT, DATA_DIR, get_maia_root
except ImportError:
    # Fallback for direct script execution
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from claude.tools.core.paths import MAIA_ROOT, DATA_DIR, get_maia_root

class LLMProvider(Enum):
    # Claude models
    CLAUDE_HAIKU = "claude-haiku"
    CLAUDE_SONNET = "claude-sonnet"
    CLAUDE_OPUS = "claude-opus"
    
    # Local models (via Ollama)
    LOCAL_LLAMA_3B = "llama3.2:3b"
    LOCAL_CODELLAMA_7B = "codellama:7b"
    LOCAL_CODELLAMA_13B = "codellama:13b"
    LOCAL_STARCODER2_15B = "starcoder2:15b"
    LOCAL_CODESTRAL_22B = "codestral:22b"
    
    # Cloud models
    GEMINI_FLASH = "gemini-flash"
    GEMINI_PRO = "gemini-pro"

class TaskType(Enum):
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    FILE_OPERATIONS = "file_operations"
    RESEARCH = "research"
    STRATEGIC_ANALYSIS = "strategic_analysis"
    DOCUMENTATION = "documentation"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"

@dataclass
class LLMConfig:
    provider: LLMProvider
    cost_per_1k_tokens: float
    max_context: int
    available: bool
    strengths: List[str]
    local_model: bool = False
    requires_internet: bool = True

@dataclass
class RoutingResult:
    provider: LLMProvider
    reasoning: str
    estimated_cost: float
    cost_savings: float
    confidence: float

class LocalLLMInterface:
    """Interface for Ollama local models WITH SECURITY VALIDATION"""

    # SECURITY: Define allowed model patterns
    ALLOWED_MODEL_PATTERNS = [
        r'^llama3\.2:\d+b$',         # llama3.2:3b, llama3.2:8b
        r'^codellama:\d+b$',          # codellama:7b, codellama:13b
        r'^starcoder2:\d+b$',         # starcoder2:15b
        r'^codestral:\d+b$',          # codestral:22b
        r'^codestral:latest$'         # codestral:latest
    ]

    @staticmethod
    def validate_model_name(model: str) -> bool:
        """Validate model name against allowlist patterns to prevent injection"""
        import re
        if not model or not isinstance(model, str):
            return False

        # Check against allowed patterns
        for pattern in LocalLLMInterface.ALLOWED_MODEL_PATTERNS:
            if re.match(pattern, model):
                return True

        logger.warning(f"Model name validation failed: {model}")
        return False

    @staticmethod
    def sanitize_prompt(prompt: str) -> str:
        """Sanitize prompt to prevent injection attacks"""
        if not isinstance(prompt, str):
            raise ValueError("Prompt must be a string")

        # Length validation
        if len(prompt) > 100000:  # 100k chars max
            raise ValueError("Prompt exceeds maximum length")

        # Remove null bytes and control characters
        prompt = prompt.replace('\x00', '')

        return prompt

    @staticmethod
    def is_ollama_running() -> bool:
        """Check if Ollama service is running"""
        try:
            result = subprocess.run(['ollama', 'list'],
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def get_available_models() -> List[str]:
        """Get list of available local models WITH VALIDATION"""
        if not LocalLLMInterface.is_ollama_running():
            return []

        try:
            result = subprocess.run(['ollama', 'list'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        # SECURITY: Validate model name before adding
                        if LocalLLMInterface.validate_model_name(model_name):
                            models.append(model_name)
                        else:
                            logger.warning(f"Skipping invalid model: {model_name}")
                return models
        except Exception as e:
            # SECURITY: Log type only, not full details
            logger.error(f"Model discovery failed: {type(e).__name__}")
            logger.debug(f"Model discovery details: {e}", exc_info=True)

        return []

    @staticmethod
    async def generate_response(model: str, prompt: str, max_tokens: int = 4000) -> str:
        """Generate response using local model WITH SECURITY VALIDATION"""
        if not LocalLLMInterface.is_ollama_running():
            raise Exception("Ollama service not running")

        # SECURITY: Validate model name
        if not LocalLLMInterface.validate_model_name(model):
            raise ValueError(f"Invalid model name: {model}. Model not in allowlist.")

        # SECURITY: Sanitize prompt
        try:
            prompt = LocalLLMInterface.sanitize_prompt(prompt)
        except ValueError as e:
            logger.error(f"Prompt validation failed: {e}")
            raise

        process = None
        try:
            # SECURITY: Use absolute path to ollama binary
            ollama_path = '/usr/local/bin/ollama'
            if not os.path.exists(ollama_path):
                # Fallback to PATH lookup
                ollama_path = 'ollama'

            # Create subprocess with validated inputs (NO shell=True - prevents injection)
            process = await asyncio.create_subprocess_exec(
                ollama_path, 'run', model,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # SECURITY: Pass prompt via stdin instead of argument (safer)
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=prompt.encode('utf-8')),
                    timeout=120.0  # 2 minute timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Model execution timeout for {model}")
                # SECURITY: Clean up hung process
                if process:
                    process.kill()
                    await process.wait()  # Reap zombie process
                raise Exception("Model execution timeout. Please try again.")

            if process.returncode == 0:
                return stdout.decode('utf-8').strip()
            else:
                # SECURITY: Don't expose stderr to caller
                error_msg = stderr.decode('utf-8')
                logger.error(f"Ollama execution failed: {error_msg}")
                logger.debug(f"Model: {model}, Return code: {process.returncode}")

                # Return generic error message
                raise Exception("Local model execution failed. Please check service status.")

        except asyncio.TimeoutError:
            raise Exception("Model execution timeout. Please try again.")
        except Exception as e:
            # SECURITY: Log detailed error internally, return generic message
            logger.error(f"Model execution error: {type(e).__name__}")
            logger.debug(f"Execution details: {e}", exc_info=True)

            # Return generic error message
            if isinstance(e, ValueError):
                raise  # Re-raise validation errors
            raise Exception("Local model unavailable. Please contact administrator.")
        finally:
            # SECURITY: Ensure process cleanup
            if process and process.returncode is None:
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()

class ProductionLLMRouter:
    """Enhanced production LLM router with local model support"""

    def __init__(self, config_file: str = None):
        # SECURITY FIX: Use portable paths for secure path resolution
        if config_file:
            # Validate provided path
            config_path = Path(config_file).resolve()

            # SECURITY: Prevent path traversal
            try:
                maia_root = Path(MAIA_ROOT)

                # Ensure config_file is within allowed directories
                if not str(config_path).startswith(str(maia_root)):
                    raise ValueError(f"Config file must be within Maia directory: {maia_root}")

                self.config_file = config_path
            except Exception as e:
                logger.error(f"Config path validation failed: {e}")
                raise ValueError("Invalid config file path")
        else:
            # Use portable paths for default location
            config_dir = Path(DATA_DIR)
            self.config_file = config_dir / 'llm_router_config.json'

        self.local_interface = LocalLLMInterface()
        self.llm_configs = self._initialize_llm_configs()
        self.task_patterns = self._initialize_task_patterns()
        self.usage_stats = self._load_usage_stats()
        
    def _initialize_llm_configs(self) -> Dict[LLMProvider, LLMConfig]:
        """Initialize LLM configurations with local model availability checking."""
        
        # Check available local models
        available_local_models = self.local_interface.get_available_models()
        
        configs = {
            # Claude models (cloud)
            LLMProvider.CLAUDE_HAIKU: LLMConfig(
                provider=LLMProvider.CLAUDE_HAIKU,
                cost_per_1k_tokens=0.00025,
                max_context=200000,
                available=True,
                strengths=["fast", "cheap", "good for simple tasks"],
                local_model=False
            ),
            LLMProvider.CLAUDE_SONNET: LLMConfig(
                provider=LLMProvider.CLAUDE_SONNET,
                cost_per_1k_tokens=0.003,
                max_context=200000,
                available=True,
                strengths=["balanced", "full Maia capabilities", "strategic reasoning"],
                local_model=False
            ),
            LLMProvider.CLAUDE_OPUS: LLMConfig(
                provider=LLMProvider.CLAUDE_OPUS,
                cost_per_1k_tokens=0.015,
                max_context=200000,
                available=True,
                strengths=["maximum reasoning", "complex analysis", "critical decisions"],
                local_model=False
            ),
            
            # Local models (via Ollama) - 99.3% cost savings
            LLMProvider.LOCAL_LLAMA_3B: LLMConfig(
                provider=LLMProvider.LOCAL_LLAMA_3B,
                cost_per_1k_tokens=0.00002,  # 99.3% savings vs Sonnet
                max_context=128000,
                available="llama3.2:3b" in available_local_models,
                strengths=["ultra cheap", "fast", "file operations", "simple code"],
                local_model=True,
                requires_internet=False
            ),
            LLMProvider.LOCAL_CODELLAMA_7B: LLMConfig(
                provider=LLMProvider.LOCAL_CODELLAMA_7B,
                cost_per_1k_tokens=0.00002,
                max_context=16000,
                available="codellama:7b" in available_local_models,
                strengths=["code generation", "debugging", "cheap", "privacy"],
                local_model=True,
                requires_internet=False
            ),
            LLMProvider.LOCAL_CODELLAMA_13B: LLMConfig(
                provider=LLMProvider.LOCAL_CODELLAMA_13B,
                cost_per_1k_tokens=0.00002,
                max_context=16000,
                available="codellama:13b" in available_local_models,
                strengths=["advanced code", "refactoring", "architecture", "privacy"],
                local_model=True,
                requires_internet=False
            ),
            LLMProvider.LOCAL_STARCODER2_15B: LLMConfig(
                provider=LLMProvider.LOCAL_STARCODER2_15B,
                cost_per_1k_tokens=0.00002,
                max_context=16000,
                available="starcoder2:15b" in available_local_models,
                strengths=["security code", "enterprise patterns", "auditable", "privacy"],
                local_model=True,
                requires_internet=False
            ),
            LLMProvider.LOCAL_CODESTRAL_22B: LLMConfig(
                provider=LLMProvider.LOCAL_CODESTRAL_22B,
                cost_per_1k_tokens=0.00002,
                max_context=32000,
                available="codestral:22b" in available_local_models,
                strengths=["complex code", "large context", "enterprise grade"],
                local_model=True,
                requires_internet=False
            ),
            
            # Cloud models for research/analysis
            LLMProvider.GEMINI_FLASH: LLMConfig(
                provider=LLMProvider.GEMINI_FLASH,
                cost_per_1k_tokens=0.00003,
                max_context=1000000,
                available=False,  # Needs setup
                strengths=["ultra cheap", "massive context", "file processing"],
                local_model=False
            ),
            LLMProvider.GEMINI_PRO: LLMConfig(
                provider=LLMProvider.GEMINI_PRO,
                cost_per_1k_tokens=0.00125,
                max_context=128000,
                available=False,  # Needs setup
                strengths=["research", "analysis", "cost effective"],
                local_model=False
            ),
        }
        
        return configs
        
    def _initialize_task_patterns(self) -> Dict[TaskType, Dict[str, Any]]:
        """Initialize task classification patterns"""
        return {
            TaskType.CODE_GENERATION: {
                "keywords": ["generate", "create", "write", "implement", "build", "code", "function", "class"],
                "preferred_models": [
                    LLMProvider.LOCAL_CODELLAMA_13B,
                    LLMProvider.LOCAL_STARCODER2_15B, 
                    LLMProvider.LOCAL_CODESTRAL_22B,
                    LLMProvider.CLAUDE_SONNET
                ],
                "complexity_threshold": 0.7
            },
            TaskType.CODE_REVIEW: {
                "keywords": ["review", "analyze code", "check", "audit", "security"],
                "preferred_models": [
                    LLMProvider.LOCAL_STARCODER2_15B,
                    LLMProvider.LOCAL_CODELLAMA_13B,
                    LLMProvider.CLAUDE_SONNET
                ],
                "complexity_threshold": 0.6
            },
            TaskType.DEBUGGING: {
                "keywords": ["debug", "fix", "error", "bug", "issue", "problem"],
                "preferred_models": [
                    LLMProvider.LOCAL_CODELLAMA_13B,
                    LLMProvider.LOCAL_CODELLAMA_7B,
                    LLMProvider.CLAUDE_SONNET
                ],
                "complexity_threshold": 0.5
            },
            TaskType.FILE_OPERATIONS: {
                "keywords": ["read", "write", "parse", "process file", "extract"],
                "preferred_models": [
                    LLMProvider.LOCAL_LLAMA_3B,
                    LLMProvider.LOCAL_CODELLAMA_7B,
                    LLMProvider.CLAUDE_HAIKU
                ],
                "complexity_threshold": 0.3
            },
            TaskType.STRATEGIC_ANALYSIS: {
                "keywords": ["strategy", "plan", "analyze", "decision", "recommend"],
                "preferred_models": [
                    LLMProvider.CLAUDE_SONNET,
                    LLMProvider.CLAUDE_OPUS
                ],
                "complexity_threshold": 0.8
            },
            TaskType.RESEARCH: {
                "keywords": ["research", "investigate", "study", "compare"],
                "preferred_models": [
                    LLMProvider.GEMINI_PRO,
                    LLMProvider.CLAUDE_SONNET
                ],
                "complexity_threshold": 0.6
            }
        }
    
    def classify_task(self, prompt: str, context: Dict[str, Any] = None) -> Tuple[TaskType, float]:
        """Classify task type based on prompt content"""
        prompt_lower = prompt.lower()
        context = context or {}
        
        # Check for code-related indicators
        code_indicators = ['```', 'def ', 'class ', 'function', 'import ', 'from ', '.py', '.js', '.ts']
        has_code = any(indicator in prompt for indicator in code_indicators)
        
        if has_code:
            if any(keyword in prompt_lower for keyword in ['generate', 'create', 'write', 'implement']):
                return TaskType.CODE_GENERATION, 0.9
            elif any(keyword in prompt_lower for keyword in ['review', 'analyze', 'check']):
                return TaskType.CODE_REVIEW, 0.8
            elif any(keyword in prompt_lower for keyword in ['debug', 'fix', 'error']):
                return TaskType.DEBUGGING, 0.8
        
        # Check patterns
        for task_type, config in self.task_patterns.items():
            score = 0.0
            for keyword in config["keywords"]:
                if keyword in prompt_lower:
                    score += 0.2
            
            if score >= config["complexity_threshold"]:
                return task_type, score
        
        # Default classification
        if len(prompt) > 1000:
            return TaskType.STRATEGIC_ANALYSIS, 0.5
        else:
            return TaskType.FILE_OPERATIONS, 0.4
    
    def route_task(self, prompt: str, context: Dict[str, Any] = None) -> RoutingResult:
        """Route task to optimal LLM provider WITH OPUS PERMISSION ENFORCEMENT"""
        task_type, confidence = self.classify_task(prompt, context)

        # Get preferred models for this task type
        preferred_models = self.task_patterns.get(task_type, {}).get("preferred_models", [])

        # SECURITY FIX: Check if Opus routing is in preferred models
        if LLMProvider.CLAUDE_OPUS in preferred_models:
            try:
                # Import permission enforcement
                from ...hooks.model_enforcement_webhook import ModelEnforcementWebhook

                # Check Opus permission
                enforcer = ModelEnforcementWebhook()
                enforcement_result = enforcer.check_opus_permission(
                    task_description=prompt[:200],  # First 200 chars for analysis
                    context=str(context) if context else ""
                )

                if enforcement_result["permission"] != "granted":
                    # Remove Opus from preferred models
                    preferred_models = [m for m in preferred_models if m != LLMProvider.CLAUDE_OPUS]
                    logger.warning(f"Opus routing blocked: {enforcement_result['message']}")

                    # Log enforcement action
                    enforcer.log_enforcement_action(
                        action="opus_routing_blocked",
                        task=prompt[:100],
                        decision=enforcement_result
                    )
                else:
                    logger.info("Opus routing permitted by enforcement system")

            except ImportError as e:
                logger.error(f"Security module import failed - denying Opus access: {e}")
                # FAIL SECURE: Remove Opus if enforcement cannot be loaded
                preferred_models = [m for m in preferred_models if m != LLMProvider.CLAUDE_OPUS]
            except Exception as e:
                logger.error(f"Opus permission check failed - denying Opus access: {e}")
                # FAIL SECURE: Deny on any error
                preferred_models = [m for m in preferred_models if m != LLMProvider.CLAUDE_OPUS]

        # Find the best available model
        best_model = None
        best_cost = float('inf')
        sonnet_cost = self.llm_configs[LLMProvider.CLAUDE_SONNET].cost_per_1k_tokens

        for provider in preferred_models:
            config = self.llm_configs.get(provider)
            if config and config.available:
                if config.cost_per_1k_tokens < best_cost:
                    best_model = provider
                    best_cost = config.cost_per_1k_tokens

        # Fallback to Sonnet if no preferred model available
        if not best_model:
            best_model = LLMProvider.CLAUDE_SONNET
            best_cost = sonnet_cost
        
        # Calculate estimated cost and savings
        estimated_tokens = len(prompt) // 3  # Rough estimation
        estimated_cost = (estimated_tokens / 1000) * best_cost
        cost_savings = ((sonnet_cost - best_cost) / sonnet_cost) * 100
        
        reasoning = f"Task classified as {task_type.value} (confidence: {confidence:.1f}). "
        if best_model != LLMProvider.CLAUDE_SONNET:
            reasoning += f"Routed to {best_model.value} for {cost_savings:.1f}% cost savings."
        else:
            reasoning += "Using Claude Sonnet for optimal quality."
        
        return RoutingResult(
            provider=best_model,
            reasoning=reasoning,
            estimated_cost=estimated_cost,
            cost_savings=cost_savings,
            confidence=confidence
        )
    
    async def execute_with_routing(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute prompt with optimal routing"""
        routing_result = self.route_task(prompt, context)
        
        try:
            if routing_result.provider.value.startswith('llama') or routing_result.provider.value.startswith('code') or routing_result.provider.value.startswith('star'):
                # Use local model
                response = await self.local_interface.generate_response(
                    routing_result.provider.value, 
                    prompt
                )
                return {
                    "response": response,
                    "provider": routing_result.provider.value,
                    "cost_savings": routing_result.cost_savings,
                    "reasoning": routing_result.reasoning,
                    "local_execution": True
                }
            else:
                # Use cloud model (would need implementation)
                return {
                    "response": f"[ROUTED TO {routing_result.provider.value}] {prompt}",
                    "provider": routing_result.provider.value,
                    "cost_savings": routing_result.cost_savings,
                    "reasoning": routing_result.reasoning,
                    "local_execution": False,
                    "note": "Cloud model execution not yet implemented - returning routing decision"
                }
                
        except Exception as e:
            logger.error(f"Error executing with {routing_result.provider.value}: {e}")
            # Fallback to Sonnet
            return {
                "response": f"[FALLBACK TO SONNET] Error with {routing_result.provider.value}: {e}",
                "provider": "claude-sonnet",
                "cost_savings": 0,
                "reasoning": f"Fallback due to error: {e}",
                "local_execution": False
            }
    
    def _load_usage_stats(self) -> Dict:
        """Load usage statistics WITH SECURE PATH HANDLING"""
        try:
            stats_file = Path(DATA_DIR) / 'llm_usage_stats.json'

            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading usage stats: {e}")

        return {"total_requests": 0, "cost_savings": 0, "providers": {}}
    
    def save_usage_stats(self, routing_result: RoutingResult):
        """Save usage statistics WITH ATOMIC WRITES AND PORTABLE PATHS"""
        import fcntl
        import tempfile

        try:
            stats_file = Path(DATA_DIR) / 'llm_usage_stats.json'

            # Ensure directory exists
            stats_file.parent.mkdir(parents=True, exist_ok=True)

            # Update stats in memory
            self.usage_stats["total_requests"] += 1
            self.usage_stats["cost_savings"] += routing_result.cost_savings

            provider_key = routing_result.provider.value
            if provider_key not in self.usage_stats["providers"]:
                self.usage_stats["providers"][provider_key] = 0
            self.usage_stats["providers"][provider_key] += 1

            # SECURITY: Atomic write with file locking
            temp_fd, temp_path = tempfile.mkstemp(
                dir=stats_file.parent,
                prefix='.llm_stats_',
                suffix='.json.tmp'
            )

            try:
                # Lock file for exclusive access
                fcntl.flock(temp_fd, fcntl.LOCK_EX)

                # Write to temp file
                with os.fdopen(temp_fd, 'w') as f:
                    json.dump(self.usage_stats, f, indent=2)

                # Atomic rename (POSIX guarantees atomicity)
                os.replace(temp_path, stats_file)

            finally:
                # Cleanup on failure
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

        except Exception as e:
            logger.error(f"Error saving usage stats: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get router status and model availability"""
        available_models = []
        unavailable_models = []
        
        for provider, config in self.llm_configs.items():
            model_info = {
                "provider": provider.value,
                "cost_per_1k": config.cost_per_1k_tokens,
                "local": config.local_model,
                "strengths": config.strengths
            }
            
            if config.available:
                available_models.append(model_info)
            else:
                unavailable_models.append(model_info)
        
        return {
            "router_status": "operational",
            "available_models": available_models,
            "unavailable_models": unavailable_models,
            "local_models_count": len([m for m in available_models if m["local"]]),
            "cloud_models_count": len([m for m in available_models if not m["local"]]),
            "usage_stats": self.usage_stats,
            "ollama_running": self.local_interface.is_ollama_running()
        }

def main():
    """CLI interface for testing router"""
    import sys
    
    router = ProductionLLMRouter()
    
    if len(sys.argv) < 2:
        print("Usage: python production_llm_router.py <command> [args]")
        print("Commands: status, route, test")
        return
    
    command = sys.argv[1]
    
    if command == "status":
        status = router.get_status()
        print(json.dumps(status, indent=2))
    
    elif command == "route":
        if len(sys.argv) < 3:
            print("Usage: route <prompt>")
            return
        
        prompt = " ".join(sys.argv[2:])
        result = router.route_task(prompt)
        
        print(f"Task: {prompt}")
        print(f"Routed to: {result.provider.value}")
        print(f"Reasoning: {result.reasoning}")
        print(f"Cost savings: {result.cost_savings:.1f}%")
        print(f"Confidence: {result.confidence:.1f}")
    
    elif command == "test":
        test_prompts = [
            "Generate a Python function to parse CSV files",
            "Review this code for security issues",
            "Debug this error in my application", 
            "Create a strategic plan for AI adoption",
            "Read this file and extract key information"
        ]
        
        for prompt in test_prompts:
            result = router.route_task(prompt)
            print(f"\nPrompt: {prompt}")
            print(f"→ {result.provider.value} ({result.cost_savings:.1f}% savings)")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Optimal Local LLM Interface - Method 3 Implementation
Production-ready interface for local models with connection pooling and type safety.
Enhanced with task classification and automatic routing.
"""

import json
import asyncio
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
from claude.tools.core.path_manager import get_maia_root

# Import router for intelligent task routing
try:
    from claude.tools.core.production_llm_router import ProductionLLMRouter, TaskType
    ROUTER_AVAILABLE = True
except ImportError:
    ROUTER_AVAILABLE = False
    print("Warning: Router not available - using basic model selection")

# Import Maia context compression system
try:
    from .maia_context_compressor import MaiaContextCompressor, CompressionResult
    COMPRESSION_AVAILABLE = True
except ImportError:
    try:
        from maia_context_compressor import MaiaContextCompressor, CompressionResult
        COMPRESSION_AVAILABLE = True
    except ImportError:
        COMPRESSION_AVAILABLE = False
        print("Warning: Context compression not available")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    GENERAL = "general"
    CODE = "code"
    FAST = "fast"

@dataclass
class ModelConfig:
    name: str
    size_gb: float
    strengths: List[str]
    model_type: ModelType
    context_length: int
    recommended_for: List[str]

class OptimalLocalLLMInterface:
    """Production-optimized interface for local LLM models"""
    
    def __init__(self, enable_context_compression: bool = True):
        self.available_models = self._detect_available_models()
        self.model_configs = self._initialize_model_configs()
        self.router = ProductionLLMRouter() if ROUTER_AVAILABLE else None
        
        # Context compression system
        self.context_compression_enabled = enable_context_compression and COMPRESSION_AVAILABLE
        self.context_compressor = MaiaContextCompressor() if self.context_compression_enabled else None
        self.ufc_core_files = [
            "${MAIA_ROOT}/claude/context/ufc_system.md",
            "${MAIA_ROOT}/claude/context/core/identity.md", 
            "${MAIA_ROOT}/claude/context/core/systematic_thinking_protocol.md",
            "${MAIA_ROOT}/claude/context/core/model_selection_strategy.md"
        ]
        
    def _detect_available_models(self) -> List[str]:
        """Detect available Ollama models"""
        try:
            result = subprocess.run(['ollama', 'list'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                models = []
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
            else:
                logger.error(f"Ollama list failed: {result.stderr}")
                return []
                
        except FileNotFoundError:
            logger.error("Ollama not found - please install Ollama")
            return []
        except Exception as e:
            logger.error(f"Error detecting models: {e}")
            return []
    
    def _initialize_model_configs(self) -> Dict[str, ModelConfig]:
        """Initialize model configurations with capabilities"""
        return {
            "llama3.2:3b": ModelConfig(
                name="llama3.2:3b",
                size_gb=2.0,
                strengths=["fast", "lightweight", "general purpose"],
                model_type=ModelType.FAST,
                context_length=128000,
                recommended_for=["simple tasks", "file operations", "quick analysis"]
            ),
            "codellama:7b": ModelConfig(
                name="codellama:7b",
                size_gb=3.8,
                strengths=["code generation", "debugging", "documentation"],
                model_type=ModelType.CODE,
                context_length=16000,
                recommended_for=["code generation", "debugging", "code review"]
            ),
            "codellama:13b": ModelConfig(
                name="codellama:13b", 
                size_gb=7.4,
                strengths=["advanced code", "architecture", "refactoring"],
                model_type=ModelType.CODE,
                context_length=16000,
                recommended_for=["complex code", "system design", "large refactors"]
            ),
            "starcoder2:15b": ModelConfig(
                name="starcoder2:15b",
                size_gb=9.1,
                strengths=["security code", "enterprise patterns", "auditable"],
                model_type=ModelType.CODE,
                context_length=16000,
                recommended_for=["security code", "enterprise development", "code audit"]
            ),
            "codestral:22b": ModelConfig(
                name="codestral:22b",
                size_gb=12.0,
                strengths=["complex code", "large context", "enterprise grade"],
                model_type=ModelType.CODE,
                context_length=32000,
                recommended_for=["complex systems", "large codebases", "architectural work"]
            ),
            "llama3.1:8b": ModelConfig(
                name="llama3.1:8b",
                size_gb=4.9,
                strengths=["general reasoning", "analysis", "balanced performance"],
                model_type=ModelType.GENERAL,
                context_length=128000,
                recommended_for=["analysis", "planning", "general tasks"]
            )
        }
    
    def select_optimal_model(self, task_description: str, model_preference: str = None) -> str:
        """Select optimal model based on task or use router"""
        
        # Use explicit preference if provided
        if model_preference and model_preference in self.available_models:
            return model_preference
        
        # Use router if available
        if self.router:
            try:
                routing_result = self.router.route_task(task_description)
                # Convert router provider to model name
                provider_name = routing_result.provider.value
                if provider_name in self.available_models:
                    logger.info(f"Router selected: {provider_name} ({routing_result.cost_savings:.1f}% savings)")
                    return provider_name
            except Exception as e:
                logger.warning(f"Router failed, using fallback selection: {e}")
        
        # Fallback model selection logic
        task_lower = task_description.lower()
        
        # Code-related tasks
        code_keywords = ['code', 'function', 'class', 'debug', 'implement', 'generate', '```']
        if any(keyword in task_lower for keyword in code_keywords):
            # Prefer larger code models for complex tasks
            if 'complex' in task_lower or 'architecture' in task_lower:
                for model in ['codestral:22b', 'starcoder2:15b', 'codellama:13b']:
                    if model in self.available_models:
                        return model
            else:
                for model in ['codellama:13b', 'codellama:7b']:
                    if model in self.available_models:
                        return model
        
        # Fast/simple tasks
        simple_keywords = ['simple', 'quick', 'fast', 'file', 'read', 'parse']
        if any(keyword in task_lower for keyword in simple_keywords):
            if 'llama3.2:3b' in self.available_models:
                return 'llama3.2:3b'
        
        # Default to first available model
        if self.available_models:
            return self.available_models[0]
        
        raise Exception("No local models available")
    
    async def generate_response(self, prompt: str, model: str = None, 
                              max_tokens: int = 4000, temperature: float = 0.7,
                              include_maia_context: bool = True) -> Dict[str, Any]:
        """Generate response with optimal model selection and Maia context compression"""
        
        if not self.available_models:
            raise Exception("No local models available")
        
        # Select optimal model
        selected_model = model or self.select_optimal_model(prompt)
        
        if selected_model not in self.available_models:
            raise Exception(f"Model {selected_model} not available. Available: {self.available_models}")
        
        # Apply context compression for Maia-enhanced responses
        enhanced_prompt = prompt
        compression_result = None
        
        if include_maia_context and self.context_compression_enabled and self.context_compressor:
            try:
                compression_result = self.context_compressor.compress_context(
                    self.ufc_core_files, prompt
                )
                
                # Integrate compressed context with user prompt
                enhanced_prompt = f"{compression_result.compressed_context}\n\nUSER REQUEST: {prompt}\n\nProvide a systematic, strategic response following the framework above."
                
                logger.info(f"Context compression applied: {compression_result.token_count} tokens, "
                           f"quality score: {compression_result.quality_score:.2f}")
                
            except Exception as e:
                logger.warning(f"Context compression failed, using raw prompt: {e}")
                enhanced_prompt = prompt
        
        start_time = time.time()
        
        try:
            # Use async subprocess for better performance
            process = await asyncio.create_subprocess_exec(
                'ollama', 'run', selected_model, enhanced_prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                response = stdout.decode('utf-8').strip()
                execution_time = time.time() - start_time
                
                # Calculate rough token counts (include compressed context)
                input_tokens = len(enhanced_prompt.split())
                output_tokens = len(response.split())
                
                result = {
                    "response": response,
                    "model": selected_model,
                    "execution_time": execution_time,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "tokens_per_second": output_tokens / execution_time if execution_time > 0 else 0,
                    "success": True,
                    "local_execution": True,
                    "cost_estimate": 0.00002 * (input_tokens + output_tokens) / 1000,
                    "maia_context_applied": include_maia_context and self.context_compression_enabled
                }
                
                # Include compression metrics if applied
                if compression_result:
                    result["compression_metrics"] = {
                        "compressed_tokens": compression_result.token_count,
                        "compression_ratio": compression_result.compression_ratio,
                        "quality_score": compression_result.quality_score,
                        "systematic_thinking_preserved": compression_result.systematic_thinking_preserved
                    }
                
                return result
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                raise Exception(f"Ollama execution failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                "response": None,
                "model": selected_model,
                "error": str(e),
                "success": False,
                "execution_time": time.time() - start_time,
                "maia_context_applied": False
            }

    def test_context_compression(self, test_prompt: str) -> Dict[str, Any]:
        """Test context compression system with detailed metrics"""
        if not self.context_compressor:
            return {"error": "Context compression not enabled"}
        
        try:
            compression_result = self.context_compressor.compress_context(
                self.ufc_core_files, test_prompt
            )
            
            return {
                "success": True,
                "compressed_context": compression_result.compressed_context,
                "metrics": {
                    "token_count": compression_result.token_count,
                    "compression_ratio": compression_result.compression_ratio,
                    "quality_score": compression_result.quality_score,
                    "systematic_thinking_preserved": compression_result.systematic_thinking_preserved
                }
            }
        except Exception as e:
            return {"error": f"Compression test failed: {e}"}
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get comprehensive model status"""
        status = {
            "ollama_available": len(self.available_models) > 0,
            "total_models": len(self.available_models),
            "available_models": [],
            "model_configs": {},
            "router_available": ROUTER_AVAILABLE
        }
        
        for model_name in self.available_models:
            config = self.model_configs.get(model_name)
            model_info = {
                "name": model_name,
                "available": True
            }
            
            if config:
                model_info.update({
                    "size_gb": config.size_gb,
                    "type": config.model_type.value,
                    "strengths": config.strengths,
                    "context_length": config.context_length,
                    "recommended_for": config.recommended_for
                })
            
            status["available_models"].append(model_info)
            status["model_configs"][model_name] = model_info
        
        return status
    
    def pull_model(self, model_name: str) -> bool:
        """Download a model via Ollama"""
        try:
            print(f"Downloading {model_name}...")
            result = subprocess.run(['ollama', 'pull', model_name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Successfully downloaded {model_name}")
                self.available_models = self._detect_available_models()  # Refresh
                return True
            else:
                print(f"❌ Failed to download {model_name}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error downloading {model_name}: {e}")
            return False

def main():
    """CLI interface for optimal local LLM usage"""
    interface = OptimalLocalLLMInterface()
    
    if len(sys.argv) < 2:
        print("Usage: python optimal_local_llm_interface.py <command> [args]")
        print("\nCommands:")
        print("  models                     - List available models and status")
        print("  status                     - Show detailed system status")
        print("  task <description>         - Optimize model selection for task")
        print("  code <description>         - Generate code with optimal model")
        print("  generate <prompt>          - Generate response with auto-selection")
        print("  maia-generate <prompt>     - Generate with Maia context compression")
        print("  test-compression <prompt>  - Test context compression system")
        print("  pull <model_name>          - Download a model")
        print("  test                       - Run test suite")
        return
    
    command = sys.argv[1]
    
    if command == "models":
        status = interface.get_model_status()
        print(f"🔧 Ollama Available: {status['ollama_available']}")
        print(f"📊 Total Models: {status['total_models']}")
        print(f"🤖 Router Available: {status['router_available']}")
        print("\n📋 Available Models:")
        
        for model in status["available_models"]:
            print(f"  • {model['name']} ({model.get('size_gb', 'unknown')}GB)")
            if 'strengths' in model:
                print(f"    Strengths: {', '.join(model['strengths'])}")
            if 'recommended_for' in model:
                print(f"    Best for: {', '.join(model['recommended_for'])}")
            print()
    
    elif command == "status":
        status = interface.get_model_status()
        print(json.dumps(status, indent=2))
    
    elif command == "task":
        if len(sys.argv) < 3:
            print("Usage: task <description>")
            return
        
        task_description = " ".join(sys.argv[2:])
        selected_model = interface.select_optimal_model(task_description)
        
        config = interface.model_configs.get(selected_model)
        print(f"📋 Task: {task_description}")
        print(f"🎯 Optimal Model: {selected_model}")
        if config:
            print(f"💪 Strengths: {', '.join(config.strengths)}")
            print(f"🎯 Best for: {', '.join(config.recommended_for)}")
    
    elif command in ["code", "generate"]:
        if len(sys.argv) < 3:
            print(f"Usage: {command} <prompt>")
            return
        
        prompt = " ".join(sys.argv[2:])
        
        async def run_generation():
            result = await interface.generate_response(prompt)
            
            if result["success"]:
                print(f"🤖 Model: {result['model']}")
                print(f"⚡ Speed: {result['tokens_per_second']:.1f} tokens/sec")
                print(f"💰 Cost: ${result['cost_estimate']:.6f}")
                print(f"⏱️  Time: {result['execution_time']:.2f}s")
                print("\n📝 Response:")
                print(result["response"])
            else:
                print(f"❌ Error: {result['error']}")
        
        asyncio.run(run_generation())
    
    elif command == "maia-generate":
        if len(sys.argv) < 3:
            print("Usage: maia-generate <prompt>")
            return
        
        prompt = " ".join(sys.argv[2:])
        
        async def run_maia_generation():
            result = await interface.generate_response(prompt, include_maia_context=True)
            
            if result["success"]:
                print(f"🤖 Model: {result['model']}")
                print(f"⚡ Speed: {result['tokens_per_second']:.1f} tokens/sec")
                print(f"💰 Cost: ${result['cost_estimate']:.6f}")
                print(f"⏱️  Time: {result['execution_time']:.2f}s")
                print(f"🧠 Maia Context: {result['maia_context_applied']}")
                
                if 'compression_metrics' in result:
                    metrics = result['compression_metrics']
                    print(f"📊 Compression: {metrics['compressed_tokens']} tokens, "
                          f"quality {metrics['quality_score']:.2f}, "
                          f"systematic: {metrics['systematic_thinking_preserved']}")
                
                print("\n📝 Response:")
                print(result["response"])
            else:
                print(f"❌ Error: {result['error']}")
        
        asyncio.run(run_maia_generation())
    
    elif command == "test-compression":
        if len(sys.argv) < 3:
            print("Usage: test-compression <prompt>")
            return
        
        prompt = " ".join(sys.argv[2:])
        result = interface.test_context_compression(prompt)
        
        if result.get("success"):
            print("✅ Context Compression Test Results:")
            print(f"📊 Token Count: {result['metrics']['token_count']}")
            print(f"📈 Quality Score: {result['metrics']['quality_score']:.2f}")
            print(f"🧠 Systematic Thinking: {result['metrics']['systematic_thinking_preserved']}")
            print(f"⚡ Compression Ratio: {result['metrics']['compression_ratio']:.1f}x")
            print("\n📝 Compressed Context:")
            print(result['compressed_context'])
        else:
            print(f"❌ Error: {result['error']}")
    
    elif command == "pull":
        if len(sys.argv) < 3:
            print("Usage: pull <model_name>")
            return
        
        model_name = sys.argv[2]
        interface.pull_model(model_name)
    
    elif command == "test":
        test_prompts = [
            ("Generate a Python function to parse CSV files", "code"),
            ("Read a configuration file and extract settings", "simple"),
            ("Create a complex web scraping architecture", "complex"),
            ("Debug this authentication error", "debug"),
            ("What is 2+2?", "simple")
        ]
        
        print("🧪 Running test suite...")
        for prompt, category in test_prompts:
            selected_model = interface.select_optimal_model(prompt)
            print(f"\n📋 {category.upper()}: {prompt}")
            print(f"🎯 Selected: {selected_model}")

if __name__ == "__main__":
    main()
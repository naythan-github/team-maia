#!/usr/bin/env python3
"""
Test suite for Maia context compression system
"""

import asyncio
from claude.tools.core.maia_context_compressor import MaiaContextCompressor
from claude.tools.core.optimal_local_llm_interface import OptimalLocalLLMInterface
from claude.tools.core.path_manager import get_maia_root

class ContextCompressionTests:
    def __init__(self):
        self.compressor = MaiaContextCompressor()
        self.llm_interface = OptimalLocalLLMInterface()
    
    async def test_compression_quality(self):
        """Test compression maintains systematic thinking"""
        test_prompts = [
            "Analyze the best approach for implementing microservices architecture",
            "Debug this authentication error in my application", 
            "Generate a Python function to parse CSV files",
            "Create a strategic plan for AI adoption in my organization"
        ]
        
        results = []
        for prompt in test_prompts:
            # Test compression
            compression_result = self.compressor.compress_context(
                ["${MAIA_ROOT}/claude/context/ufc_system.md",
                 "${MAIA_ROOT}/claude/context/core/identity.md"],
                prompt
            )
            
            # Test local LLM response with compression
            response = await self.llm_interface.generate_response(
                prompt, include_maia_context=True
            )
            
            # Validate systematic thinking in response
            systematic_indicators = [
                "problem analysis", "solution", "recommendation", 
                "pros", "cons", "risk", "implementation"
            ]
            
            systematic_score = sum(1 for indicator in systematic_indicators 
                                 if indicator.lower() in response["response"].lower())
            
            results.append({
                "prompt": prompt,
                "compression_quality": compression_result.quality_score,
                "systematic_score": systematic_score / len(systematic_indicators),
                "token_count": compression_result.token_count,
                "response_quality": "HIGH" if systematic_score >= 4 else "LOW"
            })
        
        return results
    
    async def test_cost_preservation(self):
        """Validate 90%+ cost savings maintained"""
        test_prompt = "Analyze and recommend the best cloud architecture for a fintech startup"
        
        # Test with compression
        compressed_response = await self.llm_interface.generate_response(
            test_prompt, include_maia_context=True
        )
        
        # Test without compression
        raw_response = await self.llm_interface.generate_response(
            test_prompt, include_maia_context=False
        )
        
        # Cost comparison (local models = $0.00002/1k tokens vs Sonnet = $0.003/1k tokens)
        sonnet_cost = (len(test_prompt.split()) / 1000) * 0.003
        local_cost = compressed_response["cost_estimate"]
        
        cost_savings = ((sonnet_cost - local_cost) / sonnet_cost) * 100
        
        return {
            "cost_savings_percentage": cost_savings,
            "target_achieved": cost_savings >= 90,
            "compression_overhead": compressed_response["input_tokens"] - len(test_prompt.split()),
            "quality_maintained": compressed_response.get("compression_metrics", {}).get("quality_score", 0) >= 0.7
        }

async def run_validation_suite():
    """Run complete validation suite"""
    tests = ContextCompressionTests()
    
    print("🧪 Running Context Compression Validation Suite...")
    
    # Test 1: Compression Quality
    quality_results = await tests.test_compression_quality()
    print("\n📊 Compression Quality Results:")
    for result in quality_results:
        print(f"  Prompt: {result['prompt'][:50]}...")
        print(f"  Compression Quality: {result['compression_quality']:.2f}")
        print(f"  Systematic Score: {result['systematic_score']:.2f}")
        print(f"  Token Count: {result['token_count']}")
        print(f"  Response Quality: {result['response_quality']}")
        print()
    
    # Test 2: Cost Preservation  
    cost_results = await tests.test_cost_preservation()
    print("💰 Cost Preservation Results:")
    print(f"  Cost Savings: {cost_results['cost_savings_percentage']:.1f}%")
    print(f"  Target Achieved (90%+): {cost_results['target_achieved']}")
    print(f"  Compression Overhead: {cost_results['compression_overhead']} tokens")
    print(f"  Quality Maintained: {cost_results['quality_maintained']}")
    
    # Overall validation
    overall_success = (
        all(r['compression_quality'] >= 0.7 for r in quality_results) and
        cost_results['target_achieved'] and
        cost_results['quality_maintained']
    )
    
    print(f"\n✅ Overall Validation: {'PASSED' if overall_success else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(run_validation_suite())
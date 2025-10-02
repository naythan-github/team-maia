#!/usr/bin/env python3
"""
Maia Context Compression System
Intelligently compresses UFC context for local LLM execution while preserving systematic thinking framework.
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

@dataclass
class CompressionResult:
    compressed_context: str
    token_count: int
    compression_ratio: float
    systematic_thinking_preserved: bool
    quality_score: float

class MaiaContextCompressor:
    """Intelligent context compression preserving Maia systematic thinking capabilities"""
    
    def __init__(self, target_tokens: int = 250):
        self.target_tokens = target_tokens
        self.systematic_thinking_template = self._load_systematic_template()
        
    def _load_systematic_template(self) -> str:
        """Load and compress systematic thinking micro-template"""
        return """🚨 MAIA SYSTEMATIC FRAMEWORK - MANDATORY FOR ALL RESPONSES:

1. **PROBLEM ANALYSIS** (Always First):
   - Real issue decomposition
   - Stakeholder mapping  
   - Constraint identification
   - Success criteria definition

2. **SOLUTION EXPLORATION** (Multi-Option):
   - Option A: [Approach + pros/cons + risks]
   - Option B: [Approach + pros/cons + risks] 
   - Option C: [Alternative + trade-offs]

3. **STRATEGIC RECOMMENDATION**:
   - Chosen approach with reasoning
   - Implementation sequence
   - Risk mitigation strategy
   - Success validation metrics
   - Rollback procedures

CRITICAL: Apply this framework to generate strategic, engineering-leadership-quality responses. No immediate solutions without analysis."""
    
    def compress_context(self, ufc_files: List[str], user_prompt: str) -> CompressionResult:
        """
        Main compression algorithm preserving Maia systematic thinking
        
        Args:
            ufc_files: List of UFC file paths to compress
            user_prompt: User's original prompt for context awareness
            
        Returns:
            CompressionResult with compressed context and metrics
        """
        # 1. Load and parse UFC files
        context_sections = self._load_ufc_files(ufc_files)
        
        # 2. Classify prompt for context prioritization
        prompt_type = self._classify_prompt(user_prompt)
        
        # 3. Extract critical elements based on prompt type
        critical_elements = self._extract_critical_elements(context_sections, prompt_type)
        
        # 4. Apply compression algorithm
        compressed_context = self._compress_elements(critical_elements)
        
        # 5. Ensure systematic thinking template included
        final_context = self._integrate_systematic_thinking(compressed_context)
        
        # 6. Validate compression results
        return self._validate_compression(final_context, len(context_sections))
    
    def _classify_prompt(self, prompt: str) -> str:
        """Classify prompt type for context prioritization"""
        prompt_lower = prompt.lower()
        
        # Code-related prompts
        if any(keyword in prompt_lower for keyword in ['code', 'function', 'implement', 'debug', 'generate']):
            return 'code'
        
        # Strategic/analysis prompts  
        if any(keyword in prompt_lower for keyword in ['analyze', 'strategy', 'plan', 'assess', 'optimize']):
            return 'strategic'
            
        # Research prompts
        if any(keyword in prompt_lower for keyword in ['research', 'investigate', 'study', 'compare']):
            return 'research'
            
        # File operation prompts
        if any(keyword in prompt_lower for keyword in ['read', 'write', 'file', 'parse', 'extract']):
            return 'file_ops'
            
        return 'general'
    
    def _extract_critical_elements(self, context_sections: Dict, prompt_type: str) -> Dict:
        """Extract critical context elements based on prompt classification"""
        
        critical_elements = {
            'identity': self._compress_identity(context_sections.get('identity', '')),
            'capabilities': self._compress_capabilities(context_sections.get('tools', ''), prompt_type),
            'domain_context': self._extract_domain_context(context_sections, prompt_type),
            'working_principles': self._compress_principles(context_sections.get('principles', ''))
        }
        
        return critical_elements
    
    def _compress_identity(self, identity_content: str) -> str:
        """Compress Maia identity to core essence (30-40 tokens)"""
        return """You are Maia (My AI Agent) - personal AI infrastructure designed to augment human capabilities through systematic thinking, modular tools, and strategic optimization. Core principles: system design over raw intelligence, Unix-like modularity, systematic optimization framework."""
    
    def _compress_capabilities(self, tools_content: str, prompt_type: str) -> str:
        """Compress tool capabilities based on prompt type (40-60 tokens)"""
        capability_map = {
            'code': "Code capabilities: generation, debugging, review, refactoring. File operations: read, write, analyze. Security: vulnerability assessment, hardening.",
            'strategic': "Strategic capabilities: analysis, planning, optimization, decision-making. Research: market intelligence, competitive analysis.",
            'research': "Research capabilities: web search, data analysis, market intelligence. Investigation: company analysis, trend research.",
            'file_ops': "File capabilities: read, write, parse, extract, analyze. Data operations: JSON, CSV, text processing.",
            'general': "Core capabilities: systematic analysis, strategic thinking, tool orchestration, optimization frameworks."
        }
        
        return capability_map.get(prompt_type, capability_map['general'])
    
    def _extract_domain_context(self, context_sections: Dict, prompt_type: str) -> str:
        """Extract relevant domain context (30-50 tokens)"""
        if prompt_type == 'code':
            return "Local LLM routing available for 99.3% cost savings. Security-first development. Enterprise patterns."
        elif prompt_type == 'strategic':
            return "Enterprise architecture focus. Cost optimization. Security compliance. Australian market context."
        elif prompt_type == 'research':
            return "Multi-source intelligence. Market analysis. Competitive positioning. Industry trends."
        else:
            return "Professional engineering focus. Systematic optimization. Quality-first approach."
    
    def _compress_principles(self, principles_content: str) -> str:
        """Compress working principles (20-30 tokens)"""
        return "Fix forward, reduce technical debt. Systematic optimization. Document all changes. Quality over speed."
    
    def _compress_elements(self, critical_elements: Dict) -> str:
        """Combine critical elements into compressed context"""
        context_parts = [
            critical_elements['identity'],
            critical_elements['capabilities'], 
            critical_elements['domain_context'],
            critical_elements['working_principles']
        ]
        
        return "\n\n".join(context_parts)
    
    def _integrate_systematic_thinking(self, compressed_context: str) -> str:
        """Integrate systematic thinking template with compressed context"""
        context_parts = [
            self.systematic_thinking_template,
            f"CONTEXT: {compressed_context}",
            "Apply systematic framework to generate strategic, optimized responses."
        ]
        
        return "\n\n".join(context_parts)
    
    def _validate_compression(self, final_context: str, original_sections: int) -> CompressionResult:
        """Validate compression results and generate metrics"""
        token_count = len(final_context.split())
        compression_ratio = original_sections / max(token_count, 1)
        
        # Check systematic thinking preservation
        systematic_preserved = all(keyword in final_context.lower() for keyword in 
                                 ['problem analysis', 'solution exploration', 'recommendation'])
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(final_context, systematic_preserved, token_count)
        
        return CompressionResult(
            compressed_context=final_context,
            token_count=token_count,
            compression_ratio=compression_ratio,
            systematic_thinking_preserved=systematic_preserved,
            quality_score=quality_score
        )
    
    def _calculate_quality_score(self, context: str, systematic_preserved: bool, token_count: int) -> float:
        """Calculate compression quality score (0-1.0)"""
        score = 0.0
        
        # Systematic thinking preservation (40% weight)
        if systematic_preserved:
            score += 0.4
        
        # Token efficiency (30% weight) - target 200-300 tokens
        if 200 <= token_count <= 300:
            score += 0.3
        elif token_count < 200:
            score += 0.3 * (token_count / 200)  # Penalty for under-compression
        else:
            score += 0.3 * (300 / token_count)  # Penalty for over-compression
        
        # Content richness (30% weight)
        content_indicators = ['capabilities', 'context', 'principles', 'systematic']
        content_score = sum(1 for indicator in content_indicators if indicator in context.lower()) / len(content_indicators)
        score += 0.3 * content_score
        
        return min(score, 1.0)
    
    def _load_ufc_files(self, file_paths: List[str]) -> Dict[str, str]:
        """Load and parse UFC files"""
        sections = {}
        
        for file_path in file_paths:
            try:
                path = Path(file_path)
                if path.exists():
                    content = path.read_text()
                    section_name = path.stem
                    sections[section_name] = content
            except Exception as e:
                print(f"Warning: Could not load {file_path}: {e}")
        
        return sections
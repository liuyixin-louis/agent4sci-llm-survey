#!/usr/bin/env python3
"""
Run REAL experiments with actual Claude CLI calls
"""

import sys
import json
import subprocess
from pathlib import Path

def call_claude_directly(prompt: str, model: str = "haiku") -> str:
    """Call Claude CLI directly with subprocess."""
    cmd = [
        "claude", 
        "-m", model,
        "-p", prompt,
        "--output-format", "text",
        "--no-stream"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Timeout"
    except Exception as e:
        return f"Error: {e}"

def test_baseline_vs_iterative():
    """Test baseline vs iterative approach with real LLM calls."""
    
    # Test papers
    papers = [
        "Paper 1: Attention Is All You Need - Introduces transformer architecture",
        "Paper 2: BERT - Bidirectional pre-training for language understanding",
        "Paper 3: GPT-3 - Few-shot learning with large language models"
    ]
    
    papers_text = "\n".join(papers)
    
    print("="*60)
    print("REAL EXPERIMENT: Baseline vs Iterative")
    print("="*60)
    
    # 1. Baseline approach (single pass)
    print("\n1️⃣ BASELINE System (AutoSurvey-style)...")
    baseline_prompt = f"""Generate a brief survey about transformer models based on these papers:
{papers_text}

Create 3 sections with clear structure. Be concise."""
    
    baseline_result = call_claude_directly(baseline_prompt, model="haiku")
    print(f"Baseline output length: {len(baseline_result)} chars")
    
    # 2. Iterative approach (with verification)
    print("\n2️⃣ ITERATIVE System (Our approach)...")
    
    # First pass
    print("   Iteration 1: Initial generation...")
    initial = call_claude_directly(baseline_prompt, model="haiku")
    
    # Verification
    print("   Iteration 2: Verification...")
    verify_prompt = f"""Evaluate this survey and score it (1-5) on:
- Coverage: Does it cover key papers?
- Structure: Is it well organized?
- Citations: Are claims supported?

Survey:
{initial[:500]}...

Provide scores and identify the weakest area."""
    
    verification = call_claude_directly(verify_prompt, model="haiku")
    print(f"   Verification result: {verification[:100]}...")
    
    # Improvement
    print("   Iteration 3: Targeted improvement...")
    improve_prompt = f"""Improve the weakest aspects of this survey based on the verification:
{initial[:500]}...

Focus on improving structure and adding missing citations."""
    
    improved = call_claude_directly(improve_prompt, model="haiku")
    print(f"   Final output length: {len(improved)} chars")
    
    # 3. Compare results
    print("\n📊 RESULTS:")
    print(f"Baseline length: {len(baseline_result)} chars")
    print(f"Iterative length: {len(improved)} chars")
    
    # Simple quality check
    baseline_has_sections = baseline_result.count("##") >= 2
    iterative_has_sections = improved.count("##") >= 2
    
    print(f"Baseline has sections: {baseline_has_sections}")
    print(f"Iterative has sections: {iterative_has_sections}")
    
    # Measure improvement
    if len(improved) > len(baseline_result):
        improvement = ((len(improved) - len(baseline_result)) / len(baseline_result)) * 100
        print(f"\n✅ Improvement: +{improvement:.1f}% content")
    else:
        print("\n❌ No significant improvement detected")
    
    print("\n" + "="*60)
    print("EXPERIMENT COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_baseline_vs_iterative()
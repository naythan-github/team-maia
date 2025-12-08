#!/usr/bin/env python3
"""
Test Local LLM Models for Email Intelligence Tasks
Compare Llama 3.1 8B, Gemma2 9B, and Mistral 7B on:
1. Email categorization (URGENT/PROJECT/FYI)
2. Action item extraction
3. Sentiment analysis

Author: Maia System
Created: 2025-11-21
"""

import json
import time
import requests
from typing import Dict, List

# Test email samples
TEST_EMAILS = [
    {
        "id": 1,
        "from": "brett.lester@moirgroup.com.au",
        "subject": "URGENT: IT Glue export needed by COB today",
        "content": "Hi Naythan, Can you please send through the IT Glue export for Moir Group? We need this by 5pm today for the MSP transition. Thanks, Brett",
        "expected_category": "URGENT",
        "expected_action": "Send IT Glue export to Moir Group by 5pm today",
        "expected_sentiment": "NEUTRAL"
    },
    {
        "id": 2,
        "from": "amrit.sohal@orro.group",
        "subject": "RE: Kirby ServiceDesk ticket #4821",
        "content": "Naythan, I've escalated this three times now and still no resolution. The client is threatening to escalate to C-level if we don't fix this by EOD. This is getting really frustrating.",
        "expected_category": "URGENT",
        "expected_action": "Resolve Kirby ticket #4821 by EOD",
        "expected_sentiment": "FRUSTRATED"
    },
    {
        "id": 3,
        "from": "newsletter@microsoft.com",
        "subject": "Azure Weekly Digest - November 2025",
        "content": "This week in Azure: New features in Azure AD, cost optimization tips, and upcoming webinars.",
        "expected_category": "FYI",
        "expected_action": None,
        "expected_sentiment": "NEUTRAL"
    },
    {
        "id": 4,
        "from": "con.alexakis@orro.group",
        "subject": "Contoso migration - Phase 2 update",
        "content": "Quick update on Contoso migration. Phase 1 complete, moving to Phase 2 next week. Will need your help with the Azure Lighthouse setup. Let me know when you're free to discuss.",
        "expected_category": "PROJECT",
        "expected_action": "Schedule meeting with Con about Azure Lighthouse setup",
        "expected_sentiment": "POSITIVE"
    }
]

MODELS_TO_TEST = [
    "llama3.1:8b",
    "gemma2:9b",
    "mistral:7b"
]


def call_ollama(model: str, prompt: str, temperature: float = 0.1) -> Dict:
    """Call Ollama API and measure performance"""
    start_time = time.time()

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False
            },
            timeout=60
        )

        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "response": data.get("response", ""),
                "elapsed": elapsed,
                "tokens": data.get("eval_count", 0),
                "tokens_per_sec": data.get("eval_count", 0) / elapsed if elapsed > 0 else 0
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "elapsed": elapsed
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "elapsed": time.time() - start_time
        }


def test_categorization(model: str) -> Dict:
    """Test email categorization accuracy"""
    print(f"\n📋 Testing categorization with {model}...")

    # Build prompt
    email_summaries = [
        f"Email {e['id']}: From {e['from']}, Subject: {e['subject']}, Content: {e['content'][:200]}"
        for e in TEST_EMAILS
    ]

    prompt = f"""Categorize these emails as URGENT, PROJECT, or FYI.

URGENT = Requires immediate action today (deadlines, escalations, critical issues)
PROJECT = Important work updates, ongoing coordination
FYI = Informational, low priority, newsletters

Emails:
{chr(10).join(email_summaries)}

Respond ONLY with JSON:
{{"1": "URGENT", "2": "URGENT", "3": "FYI", "4": "PROJECT"}}"""

    result = call_ollama(model, prompt)

    if not result["success"]:
        return {"model": model, "task": "categorization", "error": result["error"]}

    # Parse response and check accuracy
    try:
        # Extract JSON from response
        response_text = result["response"].strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        categorization = json.loads(response_text)

        # Check accuracy
        correct = 0
        for email in TEST_EMAILS:
            predicted = categorization.get(str(email["id"]), "UNKNOWN")
            if predicted == email["expected_category"]:
                correct += 1

        accuracy = (correct / len(TEST_EMAILS)) * 100

        return {
            "model": model,
            "task": "categorization",
            "accuracy": accuracy,
            "correct": correct,
            "total": len(TEST_EMAILS),
            "elapsed": result["elapsed"],
            "tokens_per_sec": result["tokens_per_sec"],
            "response": categorization
        }

    except json.JSONDecodeError:
        return {
            "model": model,
            "task": "categorization",
            "error": "Invalid JSON response",
            "raw_response": result["response"][:200]
        }


def test_action_extraction(model: str) -> Dict:
    """Test action item extraction accuracy"""
    print(f"\n📝 Testing action extraction with {model}...")

    # Focus on emails with action items
    action_emails = [e for e in TEST_EMAILS if e["expected_action"]]

    email_texts = [
        f"Email {e['id']}: From {e['from']}, Subject: {e['subject']}, Content: {e['content']}"
        for e in action_emails
    ]

    prompt = f"""Extract action items from these emails. List the task and who requested it.

Emails:
{chr(10).join(email_texts)}

Respond ONLY with JSON:
{{
  "action_items": [
    {{"email_id": 1, "task": "description", "requester": "email"}}
  ]
}}"""

    result = call_ollama(model, prompt)

    if not result["success"]:
        return {"model": model, "task": "action_extraction", "error": result["error"]}

    try:
        response_text = result["response"].strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        data = json.loads(response_text)
        action_items = data.get("action_items", [])

        # Check if we found the right number
        recall = (len(action_items) / len(action_emails)) * 100

        return {
            "model": model,
            "task": "action_extraction",
            "recall": recall,
            "found": len(action_items),
            "expected": len(action_emails),
            "elapsed": result["elapsed"],
            "tokens_per_sec": result["tokens_per_sec"],
            "actions": action_items
        }

    except json.JSONDecodeError:
        return {
            "model": model,
            "task": "action_extraction",
            "error": "Invalid JSON response",
            "raw_response": result["response"][:200]
        }


def test_sentiment(model: str) -> Dict:
    """Test sentiment analysis accuracy"""
    print(f"\n😊 Testing sentiment analysis with {model}...")

    # Pick email with clear sentiment
    test_email = TEST_EMAILS[1]  # Frustrated email from Amrit

    prompt = f"""Analyze the sentiment of this email. Is the sender POSITIVE, NEUTRAL, CONCERNED, or FRUSTRATED?

From: {test_email['from']}
Subject: {test_email['subject']}
Content: {test_email['content']}

Respond ONLY with JSON:
{{"sentiment": "FRUSTRATED", "confidence": 90}}"""

    result = call_ollama(model, prompt, temperature=0.2)

    if not result["success"]:
        return {"model": model, "task": "sentiment", "error": result["error"]}

    try:
        response_text = result["response"].strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        data = json.loads(response_text)
        predicted = data.get("sentiment", "UNKNOWN")

        correct = predicted == test_email["expected_sentiment"]

        return {
            "model": model,
            "task": "sentiment",
            "correct": correct,
            "predicted": predicted,
            "expected": test_email["expected_sentiment"],
            "confidence": data.get("confidence", 0),
            "elapsed": result["elapsed"],
            "tokens_per_sec": result["tokens_per_sec"]
        }

    except json.JSONDecodeError:
        return {
            "model": model,
            "task": "sentiment",
            "error": "Invalid JSON response",
            "raw_response": result["response"][:200]
        }


def main():
    """Run comprehensive model comparison"""
    print("="*70)
    print("🧪 LOCAL LLM EMAIL INTELLIGENCE BENCHMARK")
    print("="*70)
    print(f"\nTesting {len(MODELS_TO_TEST)} models on {len(TEST_EMAILS)} test emails")
    print(f"Models: {', '.join(MODELS_TO_TEST)}")

    results = []

    for model in MODELS_TO_TEST:
        print(f"\n{'='*70}")
        print(f"🤖 Testing {model}")
        print(f"{'='*70}")

        # Test categorization
        cat_result = test_categorization(model)
        results.append(cat_result)

        if "accuracy" in cat_result:
            print(f"   ✅ Categorization: {cat_result['accuracy']:.1f}% accuracy ({cat_result['elapsed']:.1f}s)")
        else:
            print(f"   ❌ Categorization: {cat_result.get('error', 'Failed')}")

        time.sleep(1)  # Brief pause between tests

        # Test action extraction
        action_result = test_action_extraction(model)
        results.append(action_result)

        if "recall" in action_result:
            print(f"   ✅ Action Extraction: {action_result['recall']:.1f}% recall ({action_result['elapsed']:.1f}s)")
        else:
            print(f"   ❌ Action Extraction: {action_result.get('error', 'Failed')}")

        time.sleep(1)

        # Test sentiment
        sent_result = test_sentiment(model)
        results.append(sent_result)

        if "correct" in sent_result:
            status = "✅" if sent_result["correct"] else "❌"
            print(f"   {status} Sentiment: {sent_result['predicted']} (expected {sent_result['expected']}, {sent_result['elapsed']:.1f}s)")
        else:
            print(f"   ❌ Sentiment: {sent_result.get('error', 'Failed')}")

    # Print summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY RESULTS")
    print(f"{'='*70}\n")

    print(f"{'Model':<20} {'Task':<20} {'Score':<15} {'Speed':<15}")
    print("-"*70)

    for r in results:
        model = r['model'].split(':')[0]
        task = r['task']

        if "accuracy" in r:
            score = f"{r['accuracy']:.1f}% accuracy"
        elif "recall" in r:
            score = f"{r['recall']:.1f}% recall"
        elif "correct" in r:
            score = "✅ Correct" if r["correct"] else "❌ Wrong"
        else:
            score = "❌ Failed"

        speed = f"{r.get('elapsed', 0):.1f}s"
        if r.get('tokens_per_sec', 0) > 0:
            speed += f" ({r['tokens_per_sec']:.1f} t/s)"

        print(f"{model:<20} {task:<20} {score:<15} {speed:<15}")

    # Recommendations
    print(f"\n{'='*70}")
    print("💡 RECOMMENDATIONS")
    print(f"{'='*70}\n")

    # Calculate average performance
    model_scores = {}
    for model in MODELS_TO_TEST:
        model_name = model.split(':')[0]
        model_results = [r for r in results if r['model'] == model]

        total_score = 0
        count = 0

        for r in model_results:
            if "accuracy" in r:
                total_score += r["accuracy"]
                count += 1
            elif "recall" in r:
                total_score += r["recall"]
                count += 1
            elif "correct" in r and r["correct"]:
                total_score += 100
                count += 1

        avg_score = total_score / count if count > 0 else 0
        avg_speed = sum(r.get("elapsed", 0) for r in model_results) / len(model_results)

        model_scores[model_name] = {
            "score": avg_score,
            "speed": avg_speed
        }

    # Find best model
    best_model = max(model_scores.items(), key=lambda x: x[1]["score"])
    fastest_model = min(model_scores.items(), key=lambda x: x[1]["speed"])

    print(f"🏆 Best Overall Quality: {best_model[0]} ({best_model[1]['score']:.1f}% avg score)")
    print(f"⚡ Fastest: {fastest_model[0]} ({fastest_model[1]['speed']:.1f}s avg)")

    # Print detailed scores
    print(f"\nDetailed Scores:")
    for model, scores in sorted(model_scores.items(), key=lambda x: x[1]["score"], reverse=True):
        print(f"  {model}: {scores['score']:.1f}% quality, {scores['speed']:.1f}s speed")

    print(f"\n{'='*70}")


if __name__ == "__main__":
    main()

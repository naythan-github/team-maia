# Quick Labeling Guide - 100 Comment Test Dataset

## File
`sentiment_test_100.csv` - Now open in your spreadsheet app

## Distribution
- 40 keyword-positive
- 40 keyword-negative
- 20 keyword-neutral

## How to Label (Column F: manual_sentiment)

### **Positive**
Customer is happy, satisfied, thankful, or problem is resolved.

**Examples**:
- "Thank you for your help!"
- "All working now, appreciate it"
- "Great service, problem solved"

### **Negative**
Customer is frustrated, angry, has unresolved problems.

**Examples**:
- "Still not working, very frustrated"
- "This is urgent, need help now"
- "System keeps failing"

### **Neutral**
Informational, no clear emotion, or just updates.

**Examples**:
- "I will call you back tomorrow"
- "Here is the requested information"
- "Ticket escalated to Level 2"

### **Mixed**
Contains both positive AND negative sentiment.

**Examples**:
- "Thanks for trying, but it's still broken"
- "Appreciate the quick response, however the issue persists"
- "Great communication, terrible outcome"

## Confidence Scale (Column G)

- **5** = Very confident in this label
- **4** = Confident
- **3** = Moderately confident (default)
- **2** = Somewhat unsure
- **1** = Very unsure, could go either way

## Notes (Column H) - Optional

Add notes for edge cases:
- "Sarcasm: 'Great, another delay'"
- "Negation: 'no problem' vs 'no, problem!'"
- "Mixed: thanks but still broken"
- "Unclear context"

## Time Estimate
- **100 comments**: 25-35 minutes
- **Aim for quality over speed**

## Tips
1. Read the FULL comment text
2. Consider the overall tone
3. When in doubt, mark confidence lower (2-3)
4. Keywords can be misleading - trust your judgment
5. Skip very ambiguous ones (leave blank) - we'll handle those

## After Labeling

Save the CSV and run:

```bash
# Test keyword baseline
python3 claude/tools/sre/sentiment_model_tester.py \
  --validation-csv tests/sentiment_validation/sentiment_test_100.csv \
  --model keyword_baseline

# Test best available model (llama3.1:8b)
python3 claude/tools/sre/sentiment_model_tester.py \
  --validation-csv tests/sentiment_validation/sentiment_test_100.csv \
  --model llama3.1:8b

# Compare all models
python3 claude/tools/sre/sentiment_model_tester.py \
  --validation-csv tests/sentiment_validation/sentiment_test_100.csv \
  --all
```

This will show if LLM-based sentiment is worth implementing!

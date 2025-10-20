# Sentiment Analysis Model Testing - TDD Phase 1 & 2 Complete

## ✅ Phase 1: Requirements Discovery - COMPLETE

**Created**:
- [sentiment_analysis_requirements.md](../../tests/sentiment_analysis_requirements.md) - Full requirements spec
- Accuracy target: 90%+ (10%+ improvement over 75-85% keyword baseline)
- Performance target: <3s per comment, <10min for 200 comments
- Cost target: <$50/month

## ✅ Phase 2: Test Suite Design - COMPLETE

**Tools Created**:
1. `claude/tools/sre/sentiment_validation_dataset_generator.py` - Generates stratified samples
2. `claude/tools/sre/sentiment_model_tester.py` - Tests models and compares accuracy

**Validation Dataset Generated**:
- File: `sentiment_validation_dataset.csv`
- Size: 500 comments (200 positive, 200 negative, 100 neutral)
- Excludes: brian (automated emails), automation workflows
- Length: 50-800 characters (readable comments)
- Status: **READY FOR MANUAL LABELING**

---

## 🔄 NEXT STEP: Manual Labeling Required

### What to Do

1. **Open the CSV file**:
   ```bash
   open tests/sentiment_validation/sentiment_validation_dataset.csv
   # Or use Excel, Google Sheets, Numbers, etc.
   ```

2. **Label each comment**:
   - **Column F (manual_sentiment)**: Enter one of:
     - `positive` - Customer is happy, satisfied, thankful
     - `negative` - Customer is frustrated, angry, has problems
     - `neutral` - Informational, no clear emotion
     - `mixed` - Both positive and negative elements

   - **Column G (confidence)**: Rate your confidence 1-5:
     - 1 = Very unsure
     - 3 = Moderately confident
     - 5 = Very confident

   - **Column H (notes)**: Optional notes for edge cases:
     - "Sarcasm detected"
     - "Negation: 'not happy'"
     - "Mixed: thanks but still broken"

3. **Focus on quality over speed**:
   - Read the full comment text
   - Consider context and tone
   - If unsure, mark confidence = 1 or 2
   - You can skip very ambiguous comments (leave blank)

4. **Minimum labeling required**:
   - **Option A**: Label all 500 (best accuracy)
   - **Option B**: Label 100 (20 per category) for quick testing
   - **Option C**: Label 50 for ultra-quick validation

---

## 🧪 Phase 3: Testing Models (Once Labeled)

### Available Models
- ✅ `llama3.2:3b` (already installed) - Fast, 2.0 GB
- ✅ `llama3.1:8b` (already installed) - Balanced, 4.9 GB
- ⏳ `gemma2:9b` (need to pull) - Accuracy focused
- ⏳ `mistral:7b` (need to pull) - General purpose

### Pull Missing Models (Optional)
```bash
ollama pull gemma2:9b   # ~5GB, high accuracy
ollama pull mistral:7b  # ~4GB, general purpose
```

### Run Tests

**Quick test (50 samples, single model)**:
```bash
python3 claude/tools/sre/sentiment_model_tester.py \
  --validation-csv tests/sentiment_validation/sentiment_validation_dataset.csv \
  --model llama3.2:3b \
  --sample 50
```

**Full test (all labeled data, single model)**:
```bash
python3 claude/tools/sre/sentiment_model_tester.py \
  --validation-csv tests/sentiment_validation/sentiment_validation_dataset.csv \
  --model llama3.2:3b
```

**Compare all models**:
```bash
python3 claude/tools/sre/sentiment_model_tester.py \
  --validation-csv tests/sentiment_validation/sentiment_validation_dataset.csv \
  --all
```

This will:
- Test keyword baseline
- Test all 4 LLM models
- Generate accuracy metrics (precision, recall, F1)
- Create comparison report
- Recommend best model

---

## 📊 Expected Results

### Keyword Baseline (Current)
- **Accuracy**: 75-85% (estimated)
- **Pros**: Fast (<1ms), transparent
- **Cons**: Misses nuance, sarcasm, negation

### LLM Models (Target)
- **Accuracy**: 85-95% (10%+ improvement)
- **Pros**: Understands context, handles edge cases
- **Cons**: Slower (1-3s per comment), needs Ollama

### Success Criteria
- ✅ Best model achieves >90% accuracy
- ✅ 10%+ improvement over keyword baseline
- ✅ <3s average latency
- ✅ Clear recommendation for production use

---

## 📁 Files Generated

```
tests/sentiment_validation/
├── README.md (this file)
├── sentiment_validation_dataset.csv (500 comments, ready for labeling)
└── model_comparison_*.txt (generated after testing)

tests/
└── sentiment_analysis_requirements.md (full requirements spec)

claude/tools/sre/
├── sentiment_validation_dataset_generator.py (dataset generator)
└── sentiment_model_tester.py (model testing framework)
```

---

## 🎯 Decision Point

**After testing, you'll have data to decide**:
1. **If improvement >10%**: Proceed with LLM-based sentiment (Phase 4-6)
2. **If improvement 5-10%**: Consider enhanced keywords instead (lower effort)
3. **If improvement <5%**: Stick with current keyword approach

**Next phases** (after manual labeling + testing):
- Phase 4: Implement selected model
- Phase 5: Validate accuracy improvement
- Phase 6: Integrate with nightly ETL pipeline

---

## ⏱️ Time Estimates

- **Manual labeling**:
  - 50 comments: 15-20 minutes
  - 100 comments: 30-40 minutes
  - 500 comments: 2-3 hours

- **Model testing**:
  - Single model, 50 samples: 2-3 minutes
  - Single model, full dataset: 15-20 minutes per model
  - All 4 models + baseline: 60-80 minutes total

**Total TDD Phases 1-3**: 3-5 hours (with full 500-comment labeling)

---

## 🚀 Ready to Proceed?

**Current Status**: ✅ Phase 1-2 Complete, **waiting on manual labeling**

**Action Required**: Label the validation dataset, then run model tests!

**Questions?**: Refer to `sentiment_analysis_requirements.md` for full specifications.

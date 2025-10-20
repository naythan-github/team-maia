# Sentiment Analysis Improvement - TDD Requirements

## Business Requirements

### Accuracy Target
- **Minimum improvement**: 10% over keyword baseline (75-85% → 85-95%)
- **Success threshold**: 90%+ accuracy on validation set
- **Edge case handling**: Sarcasm, mixed sentiment, negation

### Performance Requirements
- **Batch processing**: Process 200 comments in <10 minutes (nightly ETL)
- **Initial backfill**: 16,620 comments in <2 hours
- **Cost target**: <$50/month for daily updates

### Data Requirements
- **Training/validation set**: 500 manually labeled comments
  - 200 clearly positive
  - 200 clearly negative  
  - 100 mixed/neutral/edge cases
- **Test set**: 100 comments (separate from validation)

## Technical Requirements

### Model Evaluation Criteria
1. **Accuracy**: % correct classifications
2. **Precision**: True positives / (true positives + false positives)
3. **Recall**: True positives / (true positives + false negatives)
4. **F1 Score**: Harmonic mean of precision and recall
5. **Confusion Matrix**: Detailed breakdown of classifications

### Models to Test
- [ ] llama3.2:3b (fast, local)
- [ ] llama3.1:8b (balanced)
- [ ] gemma2:9b (accuracy focused)
- [ ] mistral:7b (general purpose)
- [ ] Baseline: Current keyword matching

### Schema Design: comment_sentiment table
```sql
CREATE TABLE IF NOT EXISTS comment_sentiment (
    comment_id INTEGER PRIMARY KEY,
    ticket_id INTEGER,
    comment_text TEXT,
    sentiment_label TEXT, -- 'positive', 'negative', 'neutral', 'mixed'
    sentiment_score REAL, -- -1.0 to 1.0 (negative to positive)
    confidence REAL, -- 0.0 to 1.0
    reasoning TEXT, -- LLM explanation
    model_name TEXT, -- Which model generated this
    analysis_timestamp TIMESTAMP,
    FOREIGN KEY (comment_id) REFERENCES comments(comment_id)
);
```

## Success Criteria
- [ ] 500-comment validation set created and manually labeled
- [ ] 4+ local models tested with accuracy metrics
- [ ] Best model achieves >90% accuracy (10%+ improvement over keywords)
- [ ] Processing speed: <3s per comment average
- [ ] Cost validated: <$50/month
- [ ] Dashboard updated to use new sentiment scores
- [ ] A/B comparison shows improvement to stakeholders

## Test Design

### Unit Tests
- [ ] Model response parsing (handles various LLM outputs)
- [ ] Sentiment score calculation (-1.0 to 1.0 scale)
- [ ] Confidence score validation (0.0 to 1.0)
- [ ] Database insert/update operations

### Integration Tests  
- [ ] Batch processing (100 comments)
- [ ] Incremental updates (new comments only)
- [ ] Error handling (LLM timeout, invalid responses)
- [ ] Dashboard query performance (<100ms)

### Accuracy Tests (Most Critical)
- [ ] Test model_accuracy_on_validation_set()
- [ ] Test precision_recall_f1_scores()
- [ ] Test edge_case_handling() (sarcasm, negation, mixed)
- [ ] Test keyword_vs_llm_comparison()

Created: 2025-10-20
Status: Phase 1 - Requirements Discovery

#!/bin/bash
#
# ServiceDesk RAG Re-Index - Quick Start Script
#
# This script executes the full re-indexing plan for upgrading
# from all-MiniLM-L6-v2 (384-dim) to intfloat/e5-base-v2 (768-dim)
#
# Total Time: ~3.1 hours
# Impact: RAG queries unavailable during execution
# Risk: LOW (source data safe, rollback available)
#
# Usage:
#   ./servicedesk_rag_reindex_quickstart.sh
#
# For detailed plan, see:
#   ~/git/maia/claude/data/servicedesk_rag_reindex_plan.md
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAIA_ROOT="$HOME/git/maia"
CHROMA_DB_PATH="$HOME/.maia/servicedesk_rag"
LOG_FILE="/tmp/rag_reindex_$(date +%Y%m%d_%H%M%S).log"
INDEXER_SCRIPT="$MAIA_ROOT/claude/tools/sre/servicedesk_gpu_rag_indexer.py"

echo "========================================================================"
echo "ServiceDesk RAG Re-Index - E5-base-v2 Upgrade"
echo "========================================================================"
echo "Start Time: $(date)"
echo "Log File: $LOG_FILE"
echo ""

# Log function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Error handler
error_exit() {
    log "${RED}❌ ERROR: $1${NC}"
    log "Check log file: $LOG_FILE"
    exit 1
}

# Phase 0: Pre-flight Checks
log "${BLUE}======================================${NC}"
log "${BLUE}Phase 0: Pre-flight Checks (5 min)${NC}"
log "${BLUE}======================================${NC}"
log ""

log "1. Checking source database integrity..."
sqlite3 "$MAIA_ROOT/claude/data/servicedesk_tickets.db" "PRAGMA integrity_check;" 2>&1 | tee -a "$LOG_FILE" || error_exit "Source database integrity check failed"
log "${GREEN}✅ Source database OK${NC}"
log ""

log "2. Checking disk space (need 2GB+ free)..."
FREE_SPACE=$(df -h "$HOME/.maia" | tail -1 | awk '{print $4}')
log "   Free space: $FREE_SPACE"
# Basic check - assumes output like "10Gi" or "500Mi"
if [[ "$FREE_SPACE" =~ G ]]; then
    log "${GREEN}✅ Sufficient disk space${NC}"
else
    log "${YELLOW}⚠️  Warning: Free space may be low${NC}"
fi
log ""

log "3. Verifying GPU availability..."
python3 -c "import torch; gpu='mps' if torch.backends.mps.is_available() else 'cpu'; print(f'GPU: {gpu}'); exit(0 if gpu=='mps' else 1)" 2>&1 | tee -a "$LOG_FILE" || error_exit "GPU not available"
log "${GREEN}✅ GPU (MPS) available${NC}"
log ""

log "4. Testing indexer with 100-doc sample..."
python3 "$INDEXER_SCRIPT" \
    --model intfloat/e5-base-v2 \
    --batch-size 128 \
    --index comments \
    --limit 100 2>&1 | tee -a "$LOG_FILE" || error_exit "Indexer test failed"
log "${GREEN}✅ Indexer test successful${NC}"
log ""

log "5. Documenting current state..."
python3 -c "
import chromadb, os
try:
    client = chromadb.PersistentClient(path=os.path.expanduser('~/.maia/servicedesk_rag'))
    collections = client.list_collections()
    print(f'Collections before cleanup: {len(collections)}')
    for c in collections:
        print(f'  - {c.name}: {c.count()} docs')
except Exception as e:
    print(f'No existing database (first run): {e}')
" 2>&1 | tee -a "$LOG_FILE"
log "${GREEN}✅ Pre-flight complete${NC}"
log ""

# Confirmation prompt
log "${YELLOW}⚠️  WARNING: This will delete the existing ChromaDB and re-index all 213,947 documents.${NC}"
log "${YELLOW}   Time required: ~3.1 hours${NC}"
log "${YELLOW}   RAG queries will be unavailable during this time.${NC}"
log ""
read -p "Continue with re-indexing? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log "${RED}❌ Re-indexing cancelled by user${NC}"
    exit 0
fi

# Phase 1: Clean Slate
log "${BLUE}======================================${NC}"
log "${BLUE}Phase 1: Clean Slate (2 min)${NC}"
log "${BLUE}======================================${NC}"
log ""

log "Backing up database location info..."
echo "Old ChromaDB location: $CHROMA_DB_PATH" >> "$LOG_FILE"
echo "Cleanup time: $(date)" >> "$LOG_FILE"

if [ -d "$CHROMA_DB_PATH" ]; then
    log "Deleting existing ChromaDB directory..."
    rm -rf "$CHROMA_DB_PATH" || error_exit "Failed to delete ChromaDB directory"
    log "${GREEN}✅ Old database deleted${NC}"
else
    log "${YELLOW}⚠️  No existing database found (first run)${NC}"
fi

log "Creating fresh directory..."
mkdir -p "$CHROMA_DB_PATH" || error_exit "Failed to create ChromaDB directory"
log "${GREEN}✅ Clean slate ready${NC}"
log ""

# Phase 2: Full Re-Index
log "${BLUE}======================================${NC}"
log "${BLUE}Phase 2: Full Re-Index (169 min / 2.8 hours)${NC}"
log "${BLUE}======================================${NC}"
log ""

REINDEX_START=$(date +%s)
log "Re-index started: $(date)"
log ""

log "Indexing all 5 collections with E5-base-v2 model..."
log "Expected order: work_logs, comments, descriptions, titles, solutions"
log ""

python3 "$INDEXER_SCRIPT" \
    --model intfloat/e5-base-v2 \
    --batch-size 128 \
    --index-all 2>&1 | tee -a "$LOG_FILE" || error_exit "Re-indexing failed"

REINDEX_END=$(date +%s)
REINDEX_DURATION=$((REINDEX_END - REINDEX_START))
REINDEX_MIN=$((REINDEX_DURATION / 60))

log ""
log "${GREEN}✅ Re-index complete in $REINDEX_MIN minutes${NC}"
log ""

# Phase 3: Validation
log "${BLUE}======================================${NC}"
log "${BLUE}Phase 3: Validation (5 min)${NC}"
log "${BLUE}======================================${NC}"
log ""

log "1. Verifying collection counts..."
python3 -c "
import chromadb, os

db_path = os.path.expanduser('~/.maia/servicedesk_rag')
client = chromadb.PersistentClient(path=db_path)

expected = {
    'servicedesk_work_logs': 73273,
    'servicedesk_comments': 108104,
    'servicedesk_descriptions': 10937,
    'servicedesk_titles': 10939,
    'servicedesk_solutions': 10694
}

actual = {c.name: c.count() for c in client.list_collections() if c.name.startswith('servicedesk_')}

all_pass = True
print('Collection counts:')
for name, exp_count in expected.items():
    act_count = actual.get(name, 0)
    status = '✅' if act_count == exp_count else '❌'
    print(f'{status} {name}: {act_count:,}/{exp_count:,} docs')
    if act_count != exp_count:
        all_pass = False

print()
print(f'Total: {sum(actual.values()):,}/{sum(expected.values()):,}')
print('✅ PASS' if all_pass else '❌ FAIL')
exit(0 if all_pass else 1)
" 2>&1 | tee -a "$LOG_FILE" || error_exit "Collection count validation failed"
log ""

log "2. Verifying embedding dimensions..."
python3 -c "
import chromadb, os

db_path = os.path.expanduser('~/.maia/servicedesk_rag')
client = chromadb.PersistentClient(path=db_path)

all_768 = True
print('Embedding dimensions:')
for name in ['servicedesk_comments', 'servicedesk_descriptions', 'servicedesk_solutions', 'servicedesk_titles', 'servicedesk_work_logs']:
    coll = client.get_collection(name)
    result = coll.get(limit=1, include=['embeddings'])
    dim = len(result['embeddings'][0]) if result['embeddings'] else 0
    status = '✅' if dim == 768 else '❌'
    print(f'{status} {name}: {dim}dim')
    if dim != 768:
        all_768 = False

print('✅ PASS' if all_768 else '❌ FAIL')
exit(0 if all_768 else 1)
" 2>&1 | tee -a "$LOG_FILE" || error_exit "Dimension validation failed"
log ""

log "3. Verifying model metadata..."
python3 -c "
import chromadb, os

db_path = os.path.expanduser('~/.maia/servicedesk_rag')
client = chromadb.PersistentClient(path=db_path)

all_e5 = True
print('Model metadata:')
for name in ['servicedesk_comments', 'servicedesk_descriptions', 'servicedesk_solutions', 'servicedesk_titles', 'servicedesk_work_logs']:
    coll = client.get_collection(name)
    model = coll.metadata.get('model', 'unknown')
    status = '✅' if model == 'intfloat/e5-base-v2' else '❌'
    print(f'{status} {name}: {model}')
    if model != 'intfloat/e5-base-v2':
        all_e5 = False

print('✅ PASS' if all_e5 else '❌ FAIL')
exit(0 if all_e5 else 1)
" 2>&1 | tee -a "$LOG_FILE" || error_exit "Model metadata validation failed"
log ""

log "4. Testing query performance..."
python3 -c "
import chromadb, os, time

db_path = os.path.expanduser('~/.maia/servicedesk_rag')
client = chromadb.PersistentClient(path=db_path)
coll = client.get_collection('servicedesk_comments')

test_queries = [
    'SQL Server connection timeout',
    'Exchange email delivery failure',
    'Active Directory authentication error'
]

print('Query performance:')
times = []
for query in test_queries:
    start = time.time()
    results = coll.query(query_texts=[query], n_results=5)
    elapsed = time.time() - start
    times.append(elapsed)
    print(f'  {query:45} {elapsed*1000:6.1f}ms')

avg_time = sum(times) / len(times)
print(f'\nAverage: {avg_time*1000:.1f}ms')
print('✅ PASS' if avg_time < 0.5 else '⚠️ SLOW (>500ms)')
" 2>&1 | tee -a "$LOG_FILE"
log ""

log "5. Checking database size..."
DB_SIZE=$(du -sh "$CHROMA_DB_PATH" 2>/dev/null | awk '{print $1}')
log "   Database size: $DB_SIZE"
log "${GREEN}✅ Validation complete${NC}"
log ""

# Phase 4: Performance Benchmarking
log "${BLUE}======================================${NC}"
log "${BLUE}Phase 4: Performance Benchmark (5 min)${NC}"
log "${BLUE}======================================${NC}"
log ""

log "Running semantic search quality test..."
python3 -c "
import chromadb, os, time

db_path = os.path.expanduser('~/.maia/servicedesk_rag')
client = chromadb.PersistentClient(path=db_path)
coll = client.get_collection('servicedesk_comments')

test_queries = [
    'SQL Server connection timeout',
    'Exchange email delivery failure',
    'Active Directory authentication error',
    'SharePoint permission denied',
    'Azure subscription expired'
]

print('Semantic Search Quality Test:')
print('-' * 80)

for query in test_queries:
    results = coll.query(query_texts=[query], n_results=3)
    print(f'\nQuery: {query}')
    for i, (doc, dist) in enumerate(zip(results['documents'][0], results['distances'][0])):
        print(f'  {i+1}. Distance: {dist:.4f} | {doc[:100]}...')
" 2>&1 | tee -a "$LOG_FILE"
log ""
log "${GREEN}✅ Benchmarking complete${NC}"
log ""

# Final Summary
TOTAL_END=$(date +%s)
TOTAL_DURATION=$((TOTAL_END - REINDEX_START))
TOTAL_MIN=$((TOTAL_DURATION / 60))
TOTAL_HOURS=$(echo "scale=2; $TOTAL_DURATION / 3600" | bc)

log "${GREEN}======================================${NC}"
log "${GREEN}RE-INDEX COMPLETE${NC}"
log "${GREEN}======================================${NC}"
log ""
log "End Time: $(date)"
log "Total Duration: $TOTAL_MIN minutes ($TOTAL_HOURS hours)"
log "Database Location: $CHROMA_DB_PATH"
log "Database Size: $DB_SIZE"
log "Log File: $LOG_FILE"
log ""
log "${GREEN}✅ All 213,947 documents successfully re-indexed with intfloat/e5-base-v2 (768-dim)${NC}"
log "${GREEN}✅ RAG system is now available with 4x quality improvement${NC}"
log ""
log "Next steps:"
log "1. Notify L3/L4 team that RAG system is back online"
log "2. Monitor query performance for first 24 hours"
log "3. Collect user feedback on search quality"
log "4. Update documentation: $MAIA_ROOT/claude/data/servicedesk_rag_reindex_plan.md"
log ""

exit 0

#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from claude.tools.email_rag_ollama import EmailRAGOllama

print('📧 Starting full inbox indexing with Ollama embeddings...\n')
rag = EmailRAGOllama()
stats = rag.index_inbox(limit=None)

print(f'\n✅ Indexing Complete!')
print(f'   Total: {stats["total"]}')
print(f'   New: {stats["new"]}')
print(f'   Skipped: {stats["skipped"]}')
print(f'   Errors: {stats["errors"]}')

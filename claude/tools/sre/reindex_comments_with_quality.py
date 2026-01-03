#!/usr/bin/env python3
"""
Resumable RAG Re-Indexing with Quality Metadata

Re-indexes the comments collection with checkpoint-based recovery for failure resilience.

Usage:
    python3 reindex_comments_with_quality.py --mode full        # Full re-index (drops collection)
    python3 reindex_comments_with_quality.py --mode incremental # Only new quality analyses
    python3 reindex_comments_with_quality.py --resume           # Resume from last checkpoint

Features:
    - Checkpoint every 1,000 documents (prevents 1-2 hour re-work on failure)
    - Resumable from last checkpoint
    - Progress tracking
    - ETA calculation
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import time

from servicedesk_gpu_rag_indexer import GPURAGIndexer


class ResumableReIndexer:
    """Re-index with checkpoint support for failure recovery"""

    CHECKPOINT_FILE = Path(__file__).parent.parent.parent / 'data' / '.reindex_checkpoint.json'
    CHECKPOINT_INTERVAL = 1000  # Save every 1000 documents

    def __init__(self, indexer: GPURAGIndexer):
        self.indexer = indexer

    def reindex_with_checkpoints(self, mode='full'):
        """
        Re-index with automatic checkpoint saving

        Args:
            mode: 'full' (drop + re-index all) or 'incremental' (only new quality analyses)
        """

        print(f"\n{'='*70}")
        print(f"RESUMABLE RE-INDEXING: comments collection")
        print(f"{'='*70}")
        print(f"Mode: {mode}")
        print(f"Checkpoint interval: {self.CHECKPOINT_INTERVAL:,} documents")

        # Load checkpoint if exists
        checkpoint = self._load_checkpoint()

        if mode == 'full':
            if checkpoint and checkpoint.get('status') == 'in_progress':
                resume = input(f"\n⚠️  Found in-progress checkpoint (last processed: {checkpoint.get('last_processed', 0):,}). Resume? (y/n): ")
                if resume.lower() == 'y':
                    start_offset = checkpoint.get('last_processed', 0)
                    print(f"📍 Resuming from offset {start_offset:,}")
                else:
                    # Drop collection and start fresh
                    print(f"🗑️  Dropping existing collection...")
                    try:
                        self.indexer.client.delete_collection('servicedesk_comments')
                        print(f"   ✅ Collection dropped")
                    except Exception:
                        print(f"   ℹ️  Collection doesn't exist (first run)")

                    start_offset = 0
                    self._clear_checkpoint()
            else:
                # Drop collection and start fresh
                print(f"🗑️  Dropping existing collection...")
                try:
                    self.indexer.client.delete_collection('servicedesk_comments')
                    print(f"   ✅ Collection dropped")
                except Exception:
                    print(f"   ℹ️  Collection doesn't exist (first run)")

                start_offset = 0
                self._clear_checkpoint()

        elif mode == 'incremental':
            # Incremental: Only index new quality analyses
            print(f"📊 Incremental mode - indexing newly analyzed comments only")
            start_offset = 0
            # TODO: Implement incremental logic (query for comments with quality analysis not yet in ChromaDB)
            print(f"⚠️  Incremental mode not yet implemented - using full re-index")
            mode = 'full'

        # Create or get collection
        collection = self.indexer.client.get_or_create_collection(
            name='servicedesk_comments',
            metadata={"description": "ServiceDesk comments with quality metadata"}
        )

        # Fetch documents
        print(f"\n📥 Fetching documents from database...")
        start_fetch = time.time()
        documents = self.indexer.fetch_documents('comments')
        fetch_time = time.time() - start_fetch

        total_docs = len(documents)
        print(f"   ✅ Fetched {total_docs:,} documents in {fetch_time:.1f}s")

        if start_offset > 0:
            print(f"   ⏩ Skipping first {start_offset:,} documents (already indexed)")

        # Index in batches with checkpoints
        print(f"\n🚀 Starting indexing...")
        start_index = time.time()
        total_indexed = 0

        for offset in range(start_offset, total_docs, self.CHECKPOINT_INTERVAL):
            try:
                batch_end = min(offset + self.CHECKPOINT_INTERVAL, total_docs)
                batch_docs = documents[offset:batch_end]
                batch_size = len(batch_docs)

                # Prepare batch
                ids = []
                texts = []
                metadatas = []

                for doc in batch_docs:
                    # Truncate very long texts
                    text = doc['text']
                    if len(text) > 5000:
                        text = text[:5000] + "... [truncated]"

                    # Build metadata
                    metadata = {
                        'text_length': len(text),
                        'indexed_at': datetime.now().isoformat()
                    }

                    # Copy all other fields as metadata
                    for key, value in doc.items():
                        if key not in ['id', 'text']:
                            if value is not None:
                                # Convert to string or int based on field
                                if 'score' in key and value != '':
                                    try:
                                        metadata[key] = int(value) if key.endswith('_score') and key != 'quality_score' else float(value)
                                    except (ValueError, TypeError):
                                        metadata[key] = str(value)
                                elif key == 'has_quality_analysis':
                                    metadata[key] = int(value)
                                else:
                                    metadata[key] = str(value)

                    ids.append(doc['id'])
                    texts.append(text)
                    metadatas.append(metadata)

                # Generate embeddings on GPU
                embeddings = self.indexer.model.encode(
                    texts,
                    batch_size=self.indexer.batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True
                )

                # Add to ChromaDB
                collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas,
                    embeddings=embeddings.tolist()
                )

                total_indexed += batch_size

                # Save checkpoint
                self._save_checkpoint({
                    'last_processed': batch_end,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'in_progress',
                    'mode': mode,
                    'total_docs': total_docs
                })

                # Progress update
                elapsed = time.time() - start_index
                rate = total_indexed / elapsed if elapsed > 0 else 0
                eta = (total_docs - batch_end) / rate if rate > 0 else 0

                print(f"   ✓ Checkpoint: {batch_end:,}/{total_docs:,} ({100*batch_end/total_docs:.1f}%) - "
                      f"Rate: {rate:.0f} docs/s - ETA: {eta/60:.1f}m")

            except Exception as e:
                print(f"\n   ✗ Batch failed at offset {offset}: {e}")
                print(f"   💾 Checkpoint saved - run with --resume to continue from {offset:,}")
                raise

        # Mark complete
        index_time = time.time() - start_index
        total_time = fetch_time + index_time

        self._save_checkpoint({
            'last_processed': total_docs,
            'timestamp': datetime.now().isoformat(),
            'status': 'complete',
            'mode': mode,
            'total_docs': total_docs,
            'total_time': total_time
        })

        print(f"\n✅ RE-INDEXING COMPLETE:")
        print(f"   Documents indexed: {total_indexed:,}")
        print(f"   Fetch time: {fetch_time:.1f}s")
        print(f"   Index time: {index_time:.1f}s ({total_indexed/index_time:.1f} docs/sec)")
        print(f"   Total time: {total_time:.1f}s ({total_time/60:.1f}m)")
        print(f"   Collection: servicedesk_comments")

        # Show quality statistics
        print(f"\n📊 Quality Metadata Statistics:")
        stats = self.indexer.get_quality_statistics()

        if stats.get('error'):
            print(f"   ⚠️  {stats['error']}")
        else:
            print(f"   Total analyzed: {stats['total_analyzed']:,} comments")
            print(f"   Coverage: {stats['total_analyzed']/total_docs*100:.1f}% of total")
            print(f"   Quality avg: {stats['quality_score']['avg']:.2f}/5.0")

    def _load_checkpoint(self) -> dict:
        """Load checkpoint file"""
        if self.CHECKPOINT_FILE.exists():
            with open(self.CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_checkpoint(self, checkpoint: dict):
        """Save checkpoint file"""
        with open(self.CHECKPOINT_FILE, 'w') as f:
            json.dump(checkpoint, f, indent=2)

    def _clear_checkpoint(self):
        """Clear checkpoint file"""
        if self.CHECKPOINT_FILE.exists():
            self.CHECKPOINT_FILE.unlink()


def main():
    parser = argparse.ArgumentParser(description="Resumable RAG Re-Indexing")
    parser.add_argument('--mode', choices=['full', 'incremental'], default='full',
                       help='full=drop+reindex all, incremental=only new quality analyses')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from last checkpoint (auto-detected in full mode)')

    args = parser.parse_args()

    # Initialize indexer
    indexer = GPURAGIndexer()

    # Create resumable reindexer
    reindexer = ResumableReIndexer(indexer)

    # Run re-indexing
    reindexer.reindex_with_checkpoints(mode=args.mode)


if __name__ == '__main__':
    main()

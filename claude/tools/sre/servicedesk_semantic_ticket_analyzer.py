#!/usr/bin/env python3
"""
ServiceDesk Semantic Ticket Analyzer

Deep semantic analysis of all tickets using E5-base-v2 embeddings + clustering.
Categorizes tickets by actual issue type, extracts resolutions, and identifies patterns.

Similar to networking analysis but comprehensive across ALL ticket categories.

Workflow:
1. Index all tickets (descriptions + solutions) with E5-base-v2 embeddings
2. Perform semantic clustering (UMAP + HDBSCAN) to find natural categories
3. Analyze each cluster to extract:
   - Common issue patterns
   - Typical resolutions
   - Success indicators
4. Generate comprehensive categorization report

Performance:
- 10,939 tickets indexed in ~5-10 minutes (GPU-accelerated)
- Clustering in ~2-3 minutes
- Full analysis in <15 minutes

Created: 2025-10-27
Author: Maia SDM Agent
"""

import os
import sys
import sqlite3
import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import time
import numpy as np

MAIA_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = MAIA_ROOT / "claude/data/servicedesk_tickets.db"

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    import torch
    import umap
    import hdbscan
    from sklearn.metrics import silhouette_score
except ImportError as e:
    print("❌ Missing dependencies.")
    print("   Install: pip3 install sentence-transformers torch chromadb umap-learn hdbscan scikit-learn")
    print(f"   Error: {e}")
    sys.exit(1)


class SemanticTicketAnalyzer:
    """Semantic analysis and categorization of ServiceDesk tickets"""

    def __init__(self, db_path: str = None, model_name: str = "intfloat/e5-base-v2"):
        """
        Initialize semantic analyzer

        Args:
            db_path: Path to SQLite database
            model_name: HuggingFace model (E5-base-v2 recommended for quality)
        """
        self.db_path = db_path or str(DB_PATH)
        self.model_name = model_name

        # ChromaDB storage
        self.rag_db_path = os.path.expanduser("~/.maia/servicedesk_semantic_analysis")
        os.makedirs(self.rag_db_path, exist_ok=True)

        # Results storage
        self.results_path = MAIA_ROOT / "claude/data/servicedesk_semantic_analysis_results.json"

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.rag_db_path)

        # Check for GPU
        self.device = self._get_device()

        print(f"✅ Semantic Ticket Analyzer initialized")
        print(f"   Model: {model_name}")
        print(f"   Device: {self.device}")
        print(f"   Database: {self.db_path}")
        print(f"   ChromaDB: {self.rag_db_path}")
        print(f"   Results: {self.results_path}")

        # Load model
        print(f"\n📥 Loading embedding model...")
        start = time.time()
        self.model = SentenceTransformer(model_name)

        if self.device != 'cpu':
            self.model.to(self.device)
            print(f"   ✅ Model loaded on {self.device} in {time.time()-start:.1f}s")
        else:
            print(f"   ⚠️  GPU not available, using CPU (slower)")

    def _get_device(self) -> str:
        """Detect best available device (MPS > CUDA > CPU)"""
        if torch.backends.mps.is_available():
            return "mps"  # Apple Silicon Metal
        elif torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"

    def index_tickets(self, force_reindex: bool = False) -> int:
        """
        Index all tickets with E5-base-v2 embeddings

        Args:
            force_reindex: Delete existing collection and reindex

        Returns:
            Number of tickets indexed
        """
        collection_name = "tickets_semantic"

        # Check if already indexed
        try:
            collection = self.client.get_collection(name=collection_name)
            existing_count = collection.count()

            if existing_count > 0 and not force_reindex:
                print(f"\n✅ Collection '{collection_name}' already exists with {existing_count:,} tickets")
                print(f"   Use --force-reindex to rebuild")
                return existing_count
            elif force_reindex:
                print(f"\n🗑️  Deleting existing collection...")
                self.client.delete_collection(name=collection_name)
        except:
            pass

        print(f"\n📊 Indexing tickets from database...")

        # Connect to database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Query tickets with descriptions and solutions
        query = """
        SELECT
            "TKT-Ticket ID" as ticket_id,
            "TKT-Title" as title,
            "TKT-Description" as description,
            "TKT-Solution" as solution,
            "TKT-Category" as category,
            "TKT-Status" as status,
            "TKT-Account Name" as account_name,
            "TKT-Created Time" as created_time,
            "TKT-Closed Time" as closed_time,
            "TKT-Assigned To User" as assigned_to,
            "TKT-Root Cause Category" as root_cause
        FROM tickets
        WHERE ("TKT-Description" IS NOT NULL AND "TKT-Description" != '')
           OR ("TKT-Solution" IS NOT NULL AND "TKT-Solution" != '')
        ORDER BY "TKT-Created Time" DESC
        """

        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        print(f"   Found {len(rows):,} tickets with descriptions/solutions")

        # Create ChromaDB collection
        collection = self.client.create_collection(
            name=collection_name,
            metadata={
                "description": "Semantic embeddings of ServiceDesk tickets (descriptions + solutions)",
                "model": self.model_name,
                "indexed_at": datetime.now().isoformat()
            }
        )

        # Batch process embeddings
        batch_size = 64
        batch_ids = []
        batch_texts = []
        batch_metadata = []

        total_indexed = 0
        start_time = time.time()

        for i, row in enumerate(rows):
            ticket_id = row["ticket_id"]

            # Combine description and solution for richer semantic representation
            text_parts = []
            if row["description"]:
                text_parts.append(f"Issue: {row['description']}")
            if row["solution"]:
                text_parts.append(f"Resolution: {row['solution']}")

            if not text_parts:
                continue

            text = " | ".join(text_parts)

            # Prepare batch data
            batch_ids.append(str(ticket_id))
            batch_texts.append(text)
            batch_metadata.append({
                "ticket_id": str(ticket_id),
                "title": row["title"] or "",
                "category": row["category"] or "Unknown",
                "status": row["status"] or "Unknown",
                "account_name": row["account_name"] or "Unknown",
                "created_time": row["created_time"] or "",
                "closed_time": row["closed_time"] or "",
                "assigned_to": row["assigned_to"] or "",
                "root_cause": row["root_cause"] or "",
                "has_description": bool(row["description"]),
                "has_solution": bool(row["solution"])
            })

            # Process batch when full
            if len(batch_ids) >= batch_size:
                embeddings = self.model.encode(batch_texts, show_progress_bar=False, convert_to_numpy=True)

                collection.add(
                    ids=batch_ids,
                    embeddings=embeddings.tolist(),
                    documents=batch_texts,
                    metadatas=batch_metadata
                )

                total_indexed += len(batch_ids)

                # Progress
                elapsed = time.time() - start_time
                rate = total_indexed / elapsed
                eta = (len(rows) - total_indexed) / rate if rate > 0 else 0
                print(f"   Indexed {total_indexed:,}/{len(rows):,} tickets ({rate:.0f} docs/sec, ETA: {eta/60:.1f} min)")

                # Clear batch
                batch_ids = []
                batch_texts = []
                batch_metadata = []

        # Process remaining batch
        if batch_ids:
            embeddings = self.model.encode(batch_texts, show_progress_bar=False, convert_to_numpy=True)

            collection.add(
                ids=batch_ids,
                embeddings=embeddings.tolist(),
                documents=batch_texts,
                metadatas=batch_metadata
            )

            total_indexed += len(batch_ids)

        elapsed = time.time() - start_time
        rate = total_indexed / elapsed

        print(f"\n✅ Indexing complete!")
        print(f"   Total tickets: {total_indexed:,}")
        print(f"   Time: {elapsed/60:.1f} minutes")
        print(f"   Rate: {rate:.0f} docs/sec")

        conn.close()
        return total_indexed

    def perform_clustering(self, n_neighbors: int = 15, min_cluster_size: int = 25, min_samples: int = 10) -> Dict:
        """
        Perform semantic clustering on ticket embeddings

        Args:
            n_neighbors: UMAP parameter (15 recommended for 10K docs)
            min_cluster_size: HDBSCAN min cluster size (25 = ~0.2% of 10K tickets)
            min_samples: HDBSCAN min samples (10 for noise tolerance)

        Returns:
            Dictionary with clustering results
        """
        print(f"\n🔬 Performing semantic clustering...")
        print(f"   UMAP neighbors: {n_neighbors}")
        print(f"   HDBSCAN min_cluster_size: {min_cluster_size}")
        print(f"   HDBSCAN min_samples: {min_samples}")

        # Get collection
        collection = self.client.get_collection(name="tickets_semantic")

        # Get all embeddings
        results = collection.get(include=['embeddings', 'metadatas', 'documents'])
        embeddings = np.array(results['embeddings'])
        metadatas = results['metadatas']
        documents = results['documents']

        print(f"\n   Retrieved {len(embeddings):,} embeddings (shape: {embeddings.shape})")

        # UMAP dimensionality reduction
        print(f"\n📉 UMAP dimensionality reduction...")
        start = time.time()
        reducer = umap.UMAP(
            n_neighbors=n_neighbors,
            n_components=10,  # Reduce to 10D for clustering
            metric='cosine',
            random_state=42
        )
        reduced_embeddings = reducer.fit_transform(embeddings)
        print(f"   ✅ UMAP complete in {time.time()-start:.1f}s (shape: {reduced_embeddings.shape})")

        # HDBSCAN clustering
        print(f"\n🎯 HDBSCAN clustering...")
        start = time.time()
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            metric='euclidean',
            cluster_selection_method='eom'  # Excess of Mass (better for varied cluster sizes)
        )
        cluster_labels = clusterer.fit_predict(reduced_embeddings)
        print(f"   ✅ Clustering complete in {time.time()-start:.1f}s")

        # Analyze clusters
        unique_labels = set(cluster_labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = list(cluster_labels).count(-1)

        print(f"\n📊 Clustering Results:")
        print(f"   Total clusters: {n_clusters}")
        print(f"   Noise points: {n_noise:,} ({n_noise/len(cluster_labels)*100:.1f}%)")

        # Calculate silhouette score (excluding noise)
        if n_clusters > 1:
            mask = cluster_labels != -1
            if mask.sum() > 0:
                silhouette = silhouette_score(reduced_embeddings[mask], cluster_labels[mask])
                print(f"   Silhouette score: {silhouette:.3f} (quality: {'excellent' if silhouette > 0.5 else 'good' if silhouette > 0.3 else 'moderate'})")

        # Organize by cluster
        clusters = defaultdict(list)
        for idx, label in enumerate(cluster_labels):
            clusters[label].append({
                'index': idx,
                'metadata': metadatas[idx],
                'document': documents[idx]
            })

        # Sort clusters by size
        sorted_clusters = sorted(
            [(label, items) for label, items in clusters.items() if label != -1],
            key=lambda x: len(x[1]),
            reverse=True
        )

        print(f"\n🔢 Top 10 Largest Clusters:")
        for i, (label, items) in enumerate(sorted_clusters[:10], 1):
            print(f"   {i:2d}. Cluster {label}: {len(items):,} tickets ({len(items)/len(cluster_labels)*100:.1f}%)")

        return {
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'cluster_labels': cluster_labels.tolist(),
            'clusters': dict(clusters),
            'sorted_clusters': sorted_clusters,
            'silhouette_score': silhouette if n_clusters > 1 else None
        }

    def analyze_clusters(self, clustering_results: Dict) -> Dict:
        """
        Analyze each cluster to extract patterns, issues, and resolutions

        Args:
            clustering_results: Output from perform_clustering()

        Returns:
            Dictionary with cluster analysis
        """
        print(f"\n🔍 Analyzing clusters for patterns...")

        sorted_clusters = clustering_results['sorted_clusters']
        cluster_analysis = []

        for cluster_id, items in sorted_clusters:
            cluster_size = len(items)

            # Extract metadata
            categories = Counter([item['metadata']['category'] for item in items])
            statuses = Counter([item['metadata']['status'] for item in items])
            accounts = Counter([item['metadata']['account_name'] for item in items])
            root_causes = Counter([item['metadata']['root_cause'] for item in items if item['metadata']['root_cause']])

            # Sample tickets for manual review
            sample_tickets = items[:5]  # Top 5 for each cluster

            # Identify common keywords in descriptions/solutions
            all_text = " ".join([item['document'].lower() for item in items])
            # Simple keyword extraction (can be enhanced with TF-IDF)
            common_words = self._extract_keywords(all_text)

            cluster_info = {
                'cluster_id': cluster_id,
                'size': cluster_size,
                'percentage': cluster_size / clustering_results['n_clusters'] * 100,
                'top_categories': categories.most_common(3),
                'top_statuses': statuses.most_common(3),
                'top_accounts': accounts.most_common(3),
                'top_root_causes': root_causes.most_common(3),
                'common_keywords': common_words[:10],
                'sample_tickets': [
                    {
                        'ticket_id': s['metadata']['ticket_id'],
                        'title': s['metadata']['title'],
                        'category': s['metadata']['category'],
                        'document': s['document'][:500]  # First 500 chars
                    }
                    for s in sample_tickets
                ]
            }

            cluster_analysis.append(cluster_info)

            print(f"\n   Cluster {cluster_id} ({cluster_size:,} tickets, {cluster_size/clustering_results['n_clusters']*100:.1f}%):")
            print(f"     Top Category: {categories.most_common(1)[0][0]} ({categories.most_common(1)[0][1]} tickets)")
            if root_causes:
                print(f"     Top Root Cause: {root_causes.most_common(1)[0][0]}")
            print(f"     Keywords: {', '.join(common_words[:5])}")

        return {
            'clusters': cluster_analysis,
            'total_analyzed': len(sorted_clusters),
            'analyzed_at': datetime.now().isoformat()
        }

    def _extract_keywords(self, text: str, top_n: int = 20) -> List[str]:
        """
        Simple keyword extraction (TF-IDF style)

        Args:
            text: Combined text from cluster
            top_n: Number of keywords to extract

        Returns:
            List of top keywords
        """
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'what', 'which', 'who', 'when', 'where', 'why', 'how', 'issue',
            'resolution', 'ticket', 'user', 'client', 'customer'
        }

        # Tokenize and count
        words = text.lower().split()
        word_counts = Counter([
            word.strip('.,;:!?"\'()[]{}')
            for word in words
            if len(word) > 3 and word.strip('.,;:!?"\'()[]{}') not in stop_words
        ])

        return [word for word, count in word_counts.most_common(top_n)]

    def save_results(self, clustering_results: Dict, analysis_results: Dict):
        """Save results to JSON file"""
        # Convert numpy float32 to Python float for JSON serialization
        silhouette = clustering_results.get('silhouette_score')
        if silhouette is not None:
            silhouette = float(silhouette)

        results = {
            'metadata': {
                'analyzed_at': datetime.now().isoformat(),
                'model': self.model_name,
                'total_tickets': len(clustering_results['cluster_labels'])
            },
            'clustering': {
                'n_clusters': int(clustering_results['n_clusters']),
                'n_noise': int(clustering_results['n_noise']),
                'silhouette_score': silhouette
            },
            'clusters': analysis_results['clusters']
        }

        with open(self.results_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Results saved to: {self.results_path}")
        print(f"   Size: {self.results_path.stat().st_size / 1024:.1f} KB")

    def generate_report(self, analysis_results: Dict) -> str:
        """
        Generate human-readable markdown report

        Args:
            analysis_results: Output from analyze_clusters()

        Returns:
            Markdown report
        """
        report_lines = [
            "# ServiceDesk Semantic Ticket Analysis Report",
            f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Model**: {self.model_name}",
            f"**Total Clusters**: {len(analysis_results['clusters'])}",
            "\n---\n",
            "## Executive Summary\n",
            f"Analyzed {len(analysis_results['clusters'])} distinct ticket categories using semantic clustering.\n"
        ]

        # Cluster details
        report_lines.append("\n## Cluster Details\n")

        for i, cluster in enumerate(analysis_results['clusters'][:20], 1):  # Top 20 clusters
            report_lines.append(f"\n### {i}. Cluster {cluster['cluster_id']} ({cluster['size']:,} tickets, {cluster['percentage']:.1f}%)\n")

            # Top categories
            report_lines.append(f"**Top Categories**:")
            for cat, count in cluster['top_categories']:
                report_lines.append(f"- {cat}: {count} tickets")

            # Top root causes
            if cluster['top_root_causes']:
                report_lines.append(f"\n**Top Root Causes**:")
                for cause, count in cluster['top_root_causes']:
                    report_lines.append(f"- {cause}: {count} tickets")

            # Keywords
            report_lines.append(f"\n**Common Keywords**: {', '.join(cluster['common_keywords'][:10])}")

            # Sample tickets
            report_lines.append(f"\n**Sample Tickets**:")
            for sample in cluster['sample_tickets'][:3]:
                report_lines.append(f"- **{sample['ticket_id']}**: {sample['title']}")
                report_lines.append(f"  - Category: {sample['category']}")
                report_lines.append(f"  - Excerpt: {sample['document'][:200]}...")

        return "\n".join(report_lines)


def main():
    parser = argparse.ArgumentParser(description="ServiceDesk Semantic Ticket Analyzer")
    parser.add_argument('--db-path', type=str, help="Path to SQLite database")
    parser.add_argument('--force-reindex', action='store_true', help="Force reindex of tickets")
    parser.add_argument('--skip-index', action='store_true', help="Skip indexing (use existing)")
    parser.add_argument('--n-neighbors', type=int, default=15, help="UMAP n_neighbors (default: 15)")
    parser.add_argument('--min-cluster-size', type=int, default=25, help="HDBSCAN min_cluster_size (default: 25)")
    parser.add_argument('--min-samples', type=int, default=10, help="HDBSCAN min_samples (default: 10)")
    parser.add_argument('--output-report', type=str, help="Path to save markdown report")

    args = parser.parse_args()

    analyzer = SemanticTicketAnalyzer(db_path=args.db_path)

    # Step 1: Index tickets
    if not args.skip_index:
        analyzer.index_tickets(force_reindex=args.force_reindex)
    else:
        print("\n⏭️  Skipping indexing (using existing collection)")

    # Step 2: Cluster tickets
    clustering_results = analyzer.perform_clustering(
        n_neighbors=args.n_neighbors,
        min_cluster_size=args.min_cluster_size,
        min_samples=args.min_samples
    )

    # Step 3: Analyze clusters
    analysis_results = analyzer.analyze_clusters(clustering_results)

    # Step 4: Save results
    analyzer.save_results(clustering_results, analysis_results)

    # Step 5: Generate report
    report = analyzer.generate_report(analysis_results)

    if args.output_report:
        report_path = Path(args.output_report)
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_path}")
    else:
        print("\n" + "="*80)
        print(report)
        print("="*80)

    print(f"\n✅ Analysis complete!")


if __name__ == "__main__":
    main()

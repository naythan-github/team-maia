#!/usr/bin/env python3
"""
Intelligent Feature Matcher
Uses semantic similarity to detect feature overlaps across vendors

Created: 2025-10-06
Purpose: Accurate feature overlap detection despite different vendor terminology
Model: paraphrase-MiniLM-L6-v2 (optimized for paraphrase detection)
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
import numpy as np
from sentence_transformers import SentenceTransformer

class IntelligentFeatureMatcher:
    """Semantic feature matching using paraphrase detection model"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            maia_root = Path(__file__).parent.parent.parent
            self.data_dir = maia_root / "claude" / "data" / "product_intelligence"
        else:
            self.data_dir = Path(data_dir)

        self.products = {}
        print("🧠 Loading paraphrase detection model (paraphrase-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        print("✅ Model loaded\n")
        self.load_products()

    def load_products(self):
        """Load all product JSON files"""
        if not self.data_dir.exists():
            print(f"❌ Data directory not found: {self.data_dir}")
            return

        for json_file in self.data_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    product_data = json.load(f)
                    product_name = product_data.get('product_name', json_file.stem)
                    self.products[product_name] = product_data
            except Exception as e:
                print(f"❌ Error loading {json_file}: {e}")

    def extract_all_features_with_context(self) -> List[Dict]:
        """Extract all features with full context for matching"""
        all_features = []

        for product_name, product_data in self.products.items():
            capabilities = product_data.get('capabilities', {})

            for cap_name, cap_data in capabilities.items():
                features = cap_data.get('features', [])

                for feature in features:
                    feature_name = feature.get('name', '')
                    feature_desc = feature.get('description', '')

                    if feature_name:
                        # Create rich context for embedding
                        full_text = f"{feature_name}. {feature_desc}".strip()

                        all_features.append({
                            'product': product_name,
                            'capability': cap_name,
                            'name': feature_name,
                            'description': feature_desc,
                            'full_text': full_text,
                            'tier': feature.get('tier', 'All')
                        })

        return all_features

    def find_similar_features(self, threshold: float = 0.70) -> List[Dict]:
        """Find semantically similar features across products using embeddings"""
        print("🔍 Extracting features with context...")
        all_features = self.extract_all_features_with_context()
        print(f"✅ Found {len(all_features)} total features\n")

        print("🧠 Generating embeddings using paraphrase detection model...")
        # Batch encode all features for efficiency
        texts = [f['full_text'] for f in all_features]
        embeddings = self.model.encode(texts, show_progress_bar=True, batch_size=32)

        # Store embeddings
        for feature, embedding in zip(all_features, embeddings):
            feature['embedding'] = embedding

        print(f"✅ Generated {len(all_features)} embeddings\n")

        print(f"🔍 Finding similar features (threshold: {threshold*100:.0f}%)...")
        similar_groups = []
        comparison_count = 0

        # Compare all features pairwise
        for i in range(len(all_features)):
            for j in range(i + 1, len(all_features)):
                feature1 = all_features[i]
                feature2 = all_features[j]

                # Skip if same product
                if feature1['product'] == feature2['product']:
                    continue

                comparison_count += 1

                # Calculate cosine similarity
                similarity = float(np.dot(feature1['embedding'], feature2['embedding']) /
                                 (np.linalg.norm(feature1['embedding']) * np.linalg.norm(feature2['embedding'])))

                if similarity >= threshold:
                    similar_groups.append({
                        'similarity': similarity,
                        'feature1': {
                            'product': feature1['product'],
                            'capability': feature1['capability'],
                            'name': feature1['name'],
                            'description': feature1['description']
                        },
                        'feature2': {
                            'product': feature2['product'],
                            'capability': feature2['capability'],
                            'name': feature2['name'],
                            'description': feature2['description']
                        }
                    })

        # Sort by similarity (descending)
        similar_groups.sort(key=lambda x: x['similarity'], reverse=True)

        print(f"✅ Compared {comparison_count} feature pairs")
        print(f"✅ Found {len(similar_groups)} similar feature pairs above {threshold*100:.0f}% threshold\n")

        return similar_groups

    def generate_overlap_report(self, threshold: float = 0.70) -> str:
        """Generate comprehensive overlap report"""
        similar_pairs = self.find_similar_features(threshold=threshold)

        report = []
        report.append("=" * 80)
        report.append("INTELLIGENT FEATURE OVERLAP ANALYSIS")
        report.append(f"Model: paraphrase-MiniLM-L6-v2 (optimized for paraphrase detection)")
        report.append(f"Semantic Similarity Threshold: {threshold*100:.0f}%")
        report.append("=" * 80)
        report.append("")

        if not similar_pairs:
            report.append(f"✅ No significant feature overlaps detected at {threshold*100:.0f}% threshold")
            report.append("\nTry lowering threshold (e.g., --threshold 0.60) to find more matches")
            return "\n".join(report)

        report.append(f"🔍 Found {len(similar_pairs)} feature overlaps across products:\n")

        # Group by similarity score ranges
        high_similarity = [p for p in similar_pairs if p['similarity'] >= 0.85]
        medium_similarity = [p for p in similar_pairs if 0.75 <= p['similarity'] < 0.85]
        moderate_similarity = [p for p in similar_pairs if threshold <= p['similarity'] < 0.75]

        if high_similarity:
            report.append("=" * 80)
            report.append(f"🔴 HIGH SIMILARITY (≥85%): {len(high_similarity)} overlaps")
            report.append("   ⚠️  These are likely DUPLICATE capabilities - strong consolidation candidates")
            report.append("=" * 80)
            report.append("")
            for idx, pair in enumerate(high_similarity[:15], 1):  # Top 15
                report.append(f"{idx}. {pair['similarity']:.1%} Match:")
                report.append(f"   • {pair['feature1']['product']}: \"{pair['feature1']['name']}\"")
                if pair['feature1']['description']:
                    report.append(f"     → {pair['feature1']['description']}")
                report.append(f"   • {pair['feature2']['product']}: \"{pair['feature2']['name']}\"")
                if pair['feature2']['description']:
                    report.append(f"     → {pair['feature2']['description']}")
                report.append("")

        if medium_similarity:
            report.append("=" * 80)
            report.append(f"🟡 MEDIUM SIMILARITY (75-85%): {len(medium_similarity)} overlaps")
            report.append("   ⚠️  Likely overlapping with minor differences - review for consolidation")
            report.append("=" * 80)
            report.append("")
            for idx, pair in enumerate(medium_similarity[:10], 1):  # Top 10
                report.append(f"{idx}. {pair['similarity']:.1%} Match:")
                report.append(f"   • {pair['feature1']['product']}: \"{pair['feature1']['name']}\"")
                report.append(f"   • {pair['feature2']['product']}: \"{pair['feature2']['name']}\"")
                report.append("")

        if moderate_similarity and len(moderate_similarity) <= 20:
            report.append("=" * 80)
            report.append(f"🟢 MODERATE SIMILARITY ({threshold*100:.0f}-75%): {len(moderate_similarity)} overlaps")
            report.append("   ℹ️  Related capabilities with some overlap - potential synergies")
            report.append("=" * 80)
            report.append("")
            for idx, pair in enumerate(moderate_similarity[:10], 1):
                report.append(f"{idx}. {pair['similarity']:.1%} Match:")
                report.append(f"   • {pair['feature1']['product']}: \"{pair['feature1']['name']}\"")
                report.append(f"   • {pair['feature2']['product']}: \"{pair['feature2']['name']}\"")
                report.append("")

        # Product pair analysis
        report.append("=" * 80)
        report.append("OVERLAP BY PRODUCT PAIR")
        report.append("=" * 80)
        report.append("")

        product_pairs = defaultdict(list)
        for pair in similar_pairs:
            key = tuple(sorted([pair['feature1']['product'], pair['feature2']['product']]))
            product_pairs[key].append(pair)

        for products, pairs in sorted(product_pairs.items(), key=lambda x: len(x[1]), reverse=True):
            report.append(f"📦 {products[0]} ↔ {products[1]}")
            report.append(f"   {len(pairs)} overlapping features")
            avg_similarity = sum(p['similarity'] for p in pairs) / len(pairs)
            report.append(f"   Average similarity: {avg_similarity:.1%}")

            # Show top 3 overlaps for this pair
            top_overlaps = sorted(pairs, key=lambda x: x['similarity'], reverse=True)[:3]
            for overlap in top_overlaps:
                report.append(f"   • {overlap['similarity']:.1%}: {overlap['feature1']['name']} ≈ {overlap['feature2']['name']}")
            report.append("")

        # Summary statistics
        report.append("=" * 80)
        report.append("SUMMARY STATISTICS")
        report.append("=" * 80)
        report.append("")
        report.append(f"Total overlapping feature pairs: {len(similar_pairs)}")
        report.append(f"  • High overlap (≥85%): {len(high_similarity)}")
        report.append(f"  • Medium overlap (75-85%): {len(medium_similarity)}")
        report.append(f"  • Moderate overlap ({threshold*100:.0f}-75%): {len(moderate_similarity)}")
        report.append("")
        report.append(f"Product pairs with overlaps: {len(product_pairs)}")
        report.append("")

        return "\n".join(report)

    def save_similarity_matrix(self, threshold: float = 0.70, output_file: str = None):
        """Save detailed similarity analysis to JSON"""
        if output_file is None:
            output_file = self.data_dir / "feature_similarity_analysis.json"

        similar_pairs = self.find_similar_features(threshold=threshold)

        output_data = {
            'analysis_date': '2025-10-06',
            'model': 'paraphrase-MiniLM-L6-v2',
            'threshold': threshold,
            'total_overlaps': len(similar_pairs),
            'overlaps': similar_pairs
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"✅ Similarity analysis saved to: {output_file}")
        return output_file


def main():
    """CLI interface for intelligent feature matching"""
    import argparse

    parser = argparse.ArgumentParser(description="Intelligent feature overlap detection using semantic similarity")
    parser.add_argument('--threshold', type=float, default=0.70, help='Similarity threshold (0.0-1.0, default: 0.70)')
    parser.add_argument('--report', action='store_true', help='Generate overlap report')
    parser.add_argument('--save', action='store_true', help='Save similarity matrix to JSON')
    parser.add_argument('--output', type=str, help='Output file path')

    args = parser.parse_args()

    matcher = IntelligentFeatureMatcher()

    if not matcher.products:
        print("❌ No products loaded. Check data directory.")
        return

    if args.save:
        matcher.save_similarity_matrix(threshold=args.threshold, output_file=args.output)

    if args.report or not args.save:
        # Default: run analysis and show report
        report = matcher.generate_overlap_report(threshold=args.threshold)
        print(report)

        if args.output and args.report:
            Path(args.output).write_text(report)
            print(f"\n✅ Report saved to: {args.output}")


if __name__ == "__main__":
    main()

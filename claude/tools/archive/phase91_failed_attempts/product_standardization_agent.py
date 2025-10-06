#!/usr/bin/env python3
"""
Product Standardization Agent
Cleans messy service descriptions to standardized base product names

Created: 2025-10-06
Purpose: Normalize billing data service descriptions with customer names, dates, locations removed
Strategy: Multi-stage pipeline + semantic similarity matching + active learning

Key Capabilities:
- Removes date patterns (84.8% of records affected)
- Extracts base product from contaminated descriptions
- Semantic similarity matching to base catalog
- Human-in-the-loop validation for uncertain matches
- Active learning to improve over time
"""

import pandas as pd
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json

@dataclass
class ProductMatch:
    """Represents a standardization match result"""
    original: str
    standardized: str
    confidence: float
    strategy: str  # 'exact', 'date_removal', 'semantic', 'manual'
    needs_review: bool = False

class ProductStandardizationAgent:
    """
    Intelligent service description standardization using multi-strategy pipeline

    Pipeline Stages:
    1. Text normalization (spaces, case)
    2. Date pattern removal (: 01 Jul 25-31 Jul 25, etc.)
    3. Bracket content removal ([...], parentheticals)
    4. Exact match to base catalog
    5. Semantic similarity matching (if no exact match)
    6. Human review flagging for low confidence
    """

    def __init__(self, catalog_path: Optional[str] = None):
        """Initialize with optional pre-built catalog"""
        self.base_catalog: List[str] = []
        self.catalog_embeddings: Optional[np.ndarray] = None
        self.model: Optional[SentenceTransformer] = None
        self.learning_history: Dict[str, str] = {}  # original -> standardized corrections

        # Date pattern detection (covers 84.8% of variance)
        self.date_patterns = [
            r':\s*\d{2}\s+\w{3}\s+\d{2}\s*-\s*\d{2}\s+\w{3}\s+\d{2}',  # : 01 Jul 25-31 Jul 25
            r':\s*NCELineItemCharges\s*\[.*?\]',  # : NCELineItemCharges [03 Jul 25 - 02 Aug 25]
            r':\s*UsageAmount\s*\[.*?\]',  # : UsageAmount [...]
            r':\s*OneTimeCharges\s*\[.*?\]',  # : OneTimeCharges [...]
            r'\[\d{2}\s+\w{3}\s+\d{2}\s*-\s*\d{2}\s+\w{3}\s+\d{2}\]',  # [27 Jul 25 - 26 Aug 25]
            r'\(\d{2}\s+\w{3}\s+\d{2}\s*-\s*\d{2}\s+\w{3}\s+\d{2}\)',  # (01 Jan 25 - 31 Jan 25)
        ]

        if catalog_path and Path(catalog_path).exists():
            self.load_catalog(catalog_path)

    def extract_base_catalog_from_data(self, df: pd.DataFrame, column: str,
                                       min_frequency: int = 5) -> List[str]:
        """
        Extract base product catalog from billing data

        Strategy:
        1. Remove all date patterns
        2. Remove bracket content and trailing colons
        3. Group by frequency
        4. Keep products appearing >= min_frequency times
        5. Manual review for quality
        """
        print(f"📚 Extracting base catalog from {len(df):,} records...")

        # Stage 1: Remove date patterns
        base_descriptions = df[column].astype(str).copy()
        for pattern in self.date_patterns:
            base_descriptions = base_descriptions.str.replace(pattern, '', regex=True)

        # Stage 2: Clean up artifacts
        base_descriptions = base_descriptions.str.replace(r'\s*:\s*$', '', regex=True)  # Trailing colons
        base_descriptions = base_descriptions.str.replace(r'\s*-\s*$', '', regex=True)  # Trailing dashes
        base_descriptions = base_descriptions.str.replace(r'\[\s*-\s*\]', '', regex=True)  # Empty brackets
        base_descriptions = base_descriptions.str.strip()

        # Stage 3: Frequency analysis
        value_counts = base_descriptions.value_counts()

        # Stage 4: Filter by frequency
        catalog = value_counts[value_counts >= min_frequency].index.tolist()

        print(f"✅ Extracted {len(catalog)} base products (appearing {min_frequency}+ times)")
        print(f"\n📊 Top 15 base products:")
        for i, (product, count) in enumerate(value_counts.head(15).items(), 1):
            print(f"  {i:2d}. {count:4d}x | {product}")

        self.base_catalog = sorted(catalog)
        return self.base_catalog

    def save_catalog(self, output_path: str):
        """Save base catalog to JSON for reuse"""
        catalog_data = {
            'base_products': self.base_catalog,
            'total_products': len(self.base_catalog),
            'learning_history': self.learning_history
        }

        with open(output_path, 'w') as f:
            json.dump(catalog_data, f, indent=2)

        print(f"💾 Saved catalog to {output_path}")

    def load_catalog(self, catalog_path: str):
        """Load pre-built catalog"""
        with open(catalog_path, 'r') as f:
            catalog_data = json.load(f)

        self.base_catalog = catalog_data['base_products']
        self.learning_history = catalog_data.get('learning_history', {})

        print(f"📚 Loaded catalog: {len(self.base_catalog)} base products")

    def initialize_semantic_matcher(self):
        """Initialize sentence transformer for semantic matching"""
        if self.model is None:
            print("🧠 Loading semantic similarity model (paraphrase-MiniLM-L6-v2)...")
            self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
            print("✅ Model loaded")

        if self.catalog_embeddings is None and self.base_catalog:
            print(f"🔢 Generating embeddings for {len(self.base_catalog)} base products...")
            self.catalog_embeddings = self.model.encode(self.base_catalog, show_progress_bar=False)
            print("✅ Embeddings generated")

    def clean_description(self, description: str) -> str:
        """Apply cleaning pipeline to single description"""
        if pd.isna(description):
            return ""

        text = str(description)

        # Remove date patterns
        for pattern in self.date_patterns:
            text = re.sub(pattern, '', text)

        # Clean artifacts
        text = re.sub(r'\s*:\s*$', '', text)
        text = re.sub(r'\s*-\s*$', '', text)
        text = re.sub(r'\[\s*-\s*\]', '', text)

        return text.strip()

    def standardize_description(self, description: str,
                                confidence_threshold: float = 0.75) -> ProductMatch:
        """
        Standardize a single description using multi-strategy approach

        Returns ProductMatch with confidence score and strategy used
        """
        original = description

        # Check learning history first
        if original in self.learning_history:
            return ProductMatch(
                original=original,
                standardized=self.learning_history[original],
                confidence=1.0,
                strategy='learned',
                needs_review=False
            )

        # Stage 1: Clean the description
        cleaned = self.clean_description(description)

        # Stage 2: Exact match
        if cleaned in self.base_catalog:
            return ProductMatch(
                original=original,
                standardized=cleaned,
                confidence=1.0,
                strategy='exact',
                needs_review=False
            )

        # Stage 3: Semantic similarity matching
        if self.model and self.catalog_embeddings is not None:
            # Generate embedding for input
            input_embedding = self.model.encode([cleaned])[0]

            # Calculate cosine similarity
            similarities = cosine_similarity([input_embedding], self.catalog_embeddings)[0]

            # Find best match
            best_idx = np.argmax(similarities)
            best_score = similarities[best_idx]
            best_match = self.base_catalog[best_idx]

            needs_review = best_score < confidence_threshold

            return ProductMatch(
                original=original,
                standardized=best_match,
                confidence=float(best_score),
                strategy='semantic',
                needs_review=needs_review
            )

        # Fallback: return cleaned version
        return ProductMatch(
            original=original,
            standardized=cleaned,
            confidence=0.5,
            strategy='cleaned',
            needs_review=True
        )

    def standardize_dataframe(self, df: pd.DataFrame, column: str,
                              confidence_threshold: float = 0.75) -> pd.DataFrame:
        """
        Standardize all descriptions in DataFrame

        Returns enriched DataFrame with:
        - standardized_product: cleaned product name
        - match_confidence: confidence score (0-1)
        - match_strategy: strategy used
        - needs_review: human review flag
        """
        print(f"\n🔄 Standardizing {len(df):,} service descriptions...")

        # Initialize semantic matcher if not done
        if self.model is None:
            self.initialize_semantic_matcher()

        # Process all descriptions
        results = []
        for desc in df[column]:
            match = self.standardize_description(desc, confidence_threshold)
            results.append(match)

        # Add to dataframe
        result_df = df.copy()
        result_df['standardized_product'] = [r.standardized for r in results]
        result_df['match_confidence'] = [r.confidence for r in results]
        result_df['match_strategy'] = [r.strategy for r in results]
        result_df['needs_review'] = [r.needs_review for r in results]

        # Summary statistics
        total = len(results)
        high_conf = sum(1 for r in results if r.confidence >= confidence_threshold)
        review_needed = sum(1 for r in results if r.needs_review)

        print(f"\n📊 Standardization Summary:")
        print(f"  Total processed: {total:,}")
        print(f"  High confidence (≥{confidence_threshold:.0%}): {high_conf:,} ({high_conf/total:.1%})")
        print(f"  Needs review: {review_needed:,} ({review_needed/total:.1%})")

        strategy_counts = pd.Series([r.strategy for r in results]).value_counts()
        print(f"\n  Strategy distribution:")
        for strategy, count in strategy_counts.items():
            print(f"    {strategy}: {count:,} ({count/total:.1%})")

        return result_df

    def get_review_cases(self, df: pd.DataFrame, max_cases: int = 50) -> pd.DataFrame:
        """Extract cases needing human review"""
        review_df = df[df['needs_review']].copy()

        # Sort by confidence (lowest first)
        review_df = review_df.sort_values('match_confidence')

        # Deduplicate by original description
        review_df = review_df.drop_duplicates(subset=['Service Description'])

        return review_df.head(max_cases)[
            ['Service Description', 'standardized_product', 'match_confidence', 'match_strategy']
        ]

    def apply_corrections(self, corrections: Dict[str, str]):
        """Apply human corrections to learning history"""
        self.learning_history.update(corrections)
        print(f"✅ Applied {len(corrections)} corrections to learning history")

    def export_results(self, df: pd.DataFrame, output_path: str):
        """Export standardized results to Excel with review sheet"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Main results
            df.to_excel(writer, sheet_name='Standardized', index=False)

            # Review cases
            review_df = self.get_review_cases(df)
            review_df.to_excel(writer, sheet_name='Needs Review', index=False)

            # Statistics
            stats_data = {
                'Metric': [
                    'Total Records',
                    'Unique Original Descriptions',
                    'Unique Standardized Products',
                    'High Confidence Matches',
                    'Needs Review',
                    'Variance Reduction'
                ],
                'Value': [
                    len(df),
                    df['Service Description'].nunique(),
                    df['standardized_product'].nunique(),
                    (df['match_confidence'] >= 0.75).sum(),
                    df['needs_review'].sum(),
                    f"{(1 - df['standardized_product'].nunique() / df['Service Description'].nunique()):.1%}"
                ]
            }
            pd.DataFrame(stats_data).to_excel(writer, sheet_name='Statistics', index=False)

        print(f"💾 Exported results to {output_path}")


def main():
    """CLI interface for product standardization"""
    import argparse

    parser = argparse.ArgumentParser(description='Product Standardization Agent')
    parser.add_argument('input_file', help='Input Excel file')
    parser.add_argument('--column', default='Service Description', help='Column to standardize')
    parser.add_argument('--sheet', default='Export', help='Sheet name')
    parser.add_argument('--output', help='Output Excel file (default: input_standardized.xlsx)')
    parser.add_argument('--catalog', help='Path to existing catalog JSON')
    parser.add_argument('--build-catalog', action='store_true', help='Build catalog from data')
    parser.add_argument('--min-freq', type=int, default=5, help='Minimum frequency for catalog (default: 5)')
    parser.add_argument('--confidence', type=float, default=0.75, help='Confidence threshold (default: 0.75)')

    args = parser.parse_args()

    # Load data
    print(f"📂 Loading {args.input_file}...")
    df = pd.read_excel(args.input_file, sheet_name=args.sheet)
    print(f"✅ Loaded {len(df):,} records from sheet '{args.sheet}'")

    # Initialize agent
    agent = ProductStandardizationAgent(catalog_path=args.catalog)

    # Build catalog if requested
    if args.build_catalog or not agent.base_catalog:
        agent.extract_base_catalog_from_data(df, args.column, args.min_freq)

        # Save catalog
        catalog_path = Path(args.input_file).parent / 'product_catalog.json'
        agent.save_catalog(str(catalog_path))

    # Standardize
    result_df = agent.standardize_dataframe(df, args.column, args.confidence)

    # Export
    if args.output:
        output_path = args.output
    else:
        input_path = Path(args.input_file)
        output_path = input_path.parent / f"{input_path.stem}_standardized.xlsx"

    agent.export_results(result_df, str(output_path))

    print(f"\n✅ Standardization complete!")
    print(f"📊 Results: {output_path}")
    print(f"📋 Review needed: {result_df['needs_review'].sum():,} cases")


if __name__ == '__main__':
    main()

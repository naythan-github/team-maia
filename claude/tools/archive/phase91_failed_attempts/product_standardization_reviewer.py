#!/usr/bin/env python3
"""
Product Standardization Interactive Reviewer
Makes it easy to review and correct product standardization results

Created: 2025-10-06
Purpose: Guided review workflow for product standardization quality assurance
"""

import pandas as pd
from pathlib import Path
import json
from typing import Dict, List, Optional
import sys

class ProductStandardizationReviewer:
    """Interactive review workflow for standardization results"""

    def __init__(self, standardized_file: str):
        self.file_path = Path(standardized_file)
        self.df = pd.read_excel(standardized_file, sheet_name='Standardized')
        self.corrections: Dict[str, str] = {}
        self.review_complete = False

    def get_review_priorities(self) -> Dict[str, pd.DataFrame]:
        """
        Organize review work into prioritized categories

        Returns dict with:
        - easy_wins: High-frequency low-confidence items (decide once, apply many times)
        - high_variance: Products with many input variations (check consistency)
        - one_offs: Single occurrence items (low priority)
        - high_risk: Low confidence with high dollar amounts
        """
        low_conf = self.df[self.df['match_confidence'] < 0.75].copy()

        # Priority 1: Easy wins - decide once, apply many times
        easy_wins = low_conf.groupby('Shortened Description').agg({
            'standardized_product': 'first',
            'match_confidence': 'first',
            'Customer Number': 'count',
            'Invoice Line Amount': 'sum'
        }).rename(columns={
            'Customer Number': 'occurrences',
            'Invoice Line Amount': 'total_value'
        })
        easy_wins = easy_wins[easy_wins['occurrences'] > 1].sort_values(
            ['occurrences', 'total_value'], ascending=[False, False]
        )

        # Priority 2: High variance products (many inputs → same output)
        variance_analysis = low_conf.groupby('standardized_product').agg({
            'Shortened Description': lambda x: list(x.unique()),
            'match_confidence': 'mean',
            'Customer Number': 'count'
        }).rename(columns={
            'Shortened Description': 'input_variations',
            'match_confidence': 'avg_confidence',
            'Customer Number': 'total_records'
        })
        variance_analysis['variation_count'] = variance_analysis['input_variations'].apply(len)
        high_variance = variance_analysis[variance_analysis['variation_count'] > 5].sort_values(
            'variation_count', ascending=False
        )

        # Priority 3: High dollar low confidence
        high_risk = low_conf.copy()
        high_risk['total_value'] = high_risk.groupby('Shortened Description')['Invoice Line Amount'].transform('sum')
        high_risk = high_risk[high_risk['total_value'] > 1000].drop_duplicates('Shortened Description')
        high_risk = high_risk.sort_values('total_value', ascending=False)

        # Priority 4: One-offs (low priority)
        one_offs = low_conf.groupby('Shortened Description').filter(
            lambda x: len(x) == 1
        ).drop_duplicates('Shortened Description')

        return {
            'easy_wins': easy_wins,
            'high_variance': high_variance,
            'high_risk': high_risk,
            'one_offs': one_offs
        }

    def interactive_review_easy_wins(self, max_items: int = 20):
        """
        Interactive CLI review of easy wins

        For each item, show:
        - Input description
        - AI's suggested match
        - Confidence score
        - Number of occurrences
        - Total dollar value

        Options:
        1. Accept AI suggestion
        2. Provide correct product name
        3. Mark as "New Product" (add to catalog)
        4. Skip for now
        """
        priorities = self.get_review_priorities()
        easy_wins = priorities['easy_wins'].head(max_items)

        print("\n" + "=" * 80)
        print("🎯 EASY WINS REVIEW - Decide once, apply to multiple records")
        print("=" * 80)
        print(f"\nReviewing {len(easy_wins)} items (sorted by frequency and value)\n")

        for idx, (input_desc, row) in enumerate(easy_wins.iterrows(), 1):
            print("\n" + "-" * 80)
            print(f"\n📋 Item {idx}/{len(easy_wins)}")
            print(f"\n  INPUT:      {input_desc}")
            print(f"  AI MATCHED: {row['standardized_product']}")
            print(f"  Confidence: {row['match_confidence']:.1%}")
            print(f"  Occurs:     {row['occurrences']:.0f} times")
            print(f"  Total $:    ${row['total_value']:,.2f}")

            print("\n  Options:")
            print("    1. Accept AI match")
            print("    2. Enter correct product name")
            print("    3. Mark as 'New Product' (not in catalog)")
            print("    4. Skip for now")
            print("    q. Quit review")

            choice = input("\n  Your choice (1-4, q): ").strip().lower()

            if choice == 'q':
                print("\n⏸️  Review paused. Progress saved.")
                break
            elif choice == '1':
                print(f"  ✅ Accepted: {row['standardized_product']}")
                # Already correct, no correction needed
            elif choice == '2':
                correct_name = input("  Enter correct product name: ").strip()
                if correct_name:
                    self.corrections[input_desc] = correct_name
                    print(f"  ✅ Corrected to: {correct_name}")
            elif choice == '3':
                self.corrections[input_desc] = f"NEW: {input_desc}"
                print(f"  ✅ Marked as new product")
            elif choice == '4':
                print("  ⏭️  Skipped")
            else:
                print("  ⚠️  Invalid choice, skipping...")

        print("\n" + "=" * 80)
        print(f"✅ Review complete! {len(self.corrections)} corrections made")
        print("=" * 80)

    def show_summary_stats(self):
        """Show helpful summary before review"""
        priorities = self.get_review_priorities()

        print("\n" + "=" * 80)
        print("📊 REVIEW WORKLOAD SUMMARY")
        print("=" * 80)

        total_low_conf = len(self.df[self.df['match_confidence'] < 0.75])

        print(f"\n  Total low confidence (<75%): {total_low_conf:,} records")
        print(f"\n  But only need to review:")
        print(f"    • {len(priorities['easy_wins']):3d} unique items (appear multiple times)")
        print(f"    • {len(priorities['high_risk']):3d} high-value items (>${1000:,})")
        print(f"    • {len(priorities['one_offs']):3d} one-offs (can defer)")

        print(f"\n  Impact of reviewing easy wins:")
        easy_win_coverage = priorities['easy_wins']['occurrences'].sum()
        print(f"    Reviewing {len(priorities['easy_wins'])} items fixes {easy_win_coverage} records")
        print(f"    Coverage: {easy_win_coverage/total_low_conf:.1%} of low-confidence data")

        print("\n  Recommendation: Start with easy wins (20-30 minutes)")
        print("=" * 80)

    def apply_corrections(self) -> pd.DataFrame:
        """Apply corrections to dataframe"""
        if not self.corrections:
            print("⚠️  No corrections to apply")
            return self.df

        print(f"\n🔄 Applying {len(self.corrections)} corrections...")

        df_corrected = self.df.copy()
        for input_desc, correct_product in self.corrections.items():
            mask = df_corrected['Shortened Description'] == input_desc
            count = mask.sum()
            df_corrected.loc[mask, 'standardized_product'] = correct_product
            df_corrected.loc[mask, 'match_confidence'] = 1.0
            df_corrected.loc[mask, 'match_strategy'] = 'manual'
            df_corrected.loc[mask, 'needs_review'] = False
            print(f"  ✅ Corrected {count} records: {input_desc[:60]}")

        return df_corrected

    def export_corrections(self, output_file: Optional[str] = None):
        """Export corrected data to Excel"""
        df_corrected = self.apply_corrections()

        if output_file is None:
            output_file = self.file_path.parent / f"{self.file_path.stem}_REVIEWED.xlsx"

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main results
            df_corrected.to_excel(writer, sheet_name='Standardized', index=False)

            # Updated review cases (excluding corrected items)
            still_needs_review = df_corrected[
                (df_corrected['needs_review']) &
                (df_corrected['match_confidence'] < 0.75)
            ].drop_duplicates('Shortened Description').head(50)

            still_needs_review[[
                'Shortened Description', 'standardized_product',
                'match_confidence', 'match_strategy'
            ]].to_excel(writer, sheet_name='Still Needs Review', index=False)

            # Corrections applied
            corrections_df = pd.DataFrame([
                {'Input': k, 'Corrected_To': v}
                for k, v in self.corrections.items()
            ])
            corrections_df.to_excel(writer, sheet_name='Corrections Applied', index=False)

            # Statistics
            stats_data = {
                'Metric': [
                    'Total Records',
                    'Original Low Confidence',
                    'Corrections Applied',
                    'Records Fixed',
                    'Still Needs Review',
                    'Overall Confidence Rate'
                ],
                'Value': [
                    len(df_corrected),
                    len(self.df[self.df['match_confidence'] < 0.75]),
                    len(self.corrections),
                    len(self.df[self.df['Shortened Description'].isin(self.corrections.keys())]),
                    len(still_needs_review),
                    f"{(df_corrected['match_confidence'] >= 0.75).sum() / len(df_corrected):.1%}"
                ]
            }
            pd.DataFrame(stats_data).to_excel(writer, sheet_name='Review Statistics', index=False)

        print(f"\n💾 Exported reviewed data to: {output_file}")
        print(f"   {len(self.corrections)} corrections applied")
        print(f"   {len(still_needs_review)} items still need review")

        return output_file

    def save_corrections_to_catalog(self, catalog_path: str):
        """Save corrections to learning history in catalog"""
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)

        # Add to learning history
        if 'learning_history' not in catalog:
            catalog['learning_history'] = {}

        catalog['learning_history'].update(self.corrections)

        # Add new products to base catalog
        new_products = [v for v in self.corrections.values() if v.startswith('NEW: ')]
        for new_prod in new_products:
            clean_name = new_prod.replace('NEW: ', '')
            if clean_name not in catalog['base_products']:
                catalog['base_products'].append(clean_name)

        catalog['total_products'] = len(catalog['base_products'])

        with open(catalog_path, 'w') as f:
            json.dump(catalog, f, indent=2)

        print(f"💾 Saved {len(self.corrections)} corrections to catalog")
        print(f"   Added {len(new_products)} new products to base catalog")


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='Review product standardization results')
    parser.add_argument('input_file', help='Standardized Excel file to review')
    parser.add_argument('--max-items', type=int, default=20, help='Max items to review (default: 20)')
    parser.add_argument('--output', help='Output file for reviewed data')
    parser.add_argument('--catalog', help='Catalog file to update with corrections')
    parser.add_argument('--summary-only', action='store_true', help='Show summary stats only')

    args = parser.parse_args()

    # Initialize reviewer
    reviewer = ProductStandardizationReviewer(args.input_file)

    # Show summary
    reviewer.show_summary_stats()

    if args.summary_only:
        return

    # Interactive review
    print("\n🎯 Starting interactive review...\n")
    reviewer.interactive_review_easy_wins(max_items=args.max_items)

    # Export results
    if reviewer.corrections:
        output_file = reviewer.export_corrections(args.output)

        # Update catalog if provided
        if args.catalog:
            reviewer.save_corrections_to_catalog(args.catalog)

        print(f"\n✅ Review complete!")
        print(f"   Results: {output_file}")
    else:
        print("\n⚠️  No corrections made")


if __name__ == '__main__':
    main()

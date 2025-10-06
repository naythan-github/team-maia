#!/usr/bin/env python3
"""
Product Intelligence Analyzer
Analyzes feature overlap and utilization gaps across MSP/IT product portfolio

Created: 2025-10-06
Purpose: Portfolio optimization for Orro's SaaS products
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class ProductIntelligenceAnalyzer:
    """Analyze feature overlap and gaps across product portfolio"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            maia_root = Path(__file__).parent.parent.parent
            self.data_dir = maia_root / "claude" / "data" / "product_intelligence"
        else:
            self.data_dir = Path(data_dir)

        self.products = {}
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
                    print(f"✅ Loaded: {product_name}")
            except Exception as e:
                print(f"❌ Error loading {json_file}: {e}")

    def get_all_capabilities(self) -> Dict[str, List[str]]:
        """Extract all capability categories across all products"""
        capabilities = defaultdict(list)

        for product_name, product_data in self.products.items():
            product_caps = product_data.get('capabilities', {})
            for cap_category in product_caps.keys():
                capabilities[cap_category].append(product_name)

        return dict(capabilities)

    def analyze_feature_overlap(self) -> Dict[str, Dict]:
        """Identify feature overlaps across products"""
        overlaps = {}

        # Define capability mappings for overlap detection
        capability_groups = {
            "Patch Management": {
                "products": [],
                "features": set()
            },
            "Remote Monitoring": {
                "products": [],
                "features": set()
            },
            "Remote Access": {
                "products": [],
                "features": set()
            },
            "Asset Management": {
                "products": [],
                "features": set()
            },
            "Documentation": {
                "products": [],
                "features": set()
            },
            "Automation": {
                "products": [],
                "features": set()
            },
            "Security": {
                "products": [],
                "features": set()
            },
            "Reporting": {
                "products": [],
                "features": set()
            },
            "Integration": {
                "products": [],
                "features": set()
            }
        }

        # Analyze each product's capabilities
        for product_name, product_data in self.products.items():
            capabilities = product_data.get('capabilities', {})

            for cap_name, cap_data in capabilities.items():
                # Map to standardized categories
                for group_name in capability_groups.keys():
                    if group_name.lower() in cap_name.lower() or any(
                        keyword in cap_name.lower()
                        for keyword in [group_name.lower().split()[0]]
                    ):
                        capability_groups[group_name]["products"].append(product_name)

                        # Extract feature names
                        features = cap_data.get('features', [])
                        for feature in features:
                            feature_name = feature.get('name', '')
                            if feature_name:
                                capability_groups[group_name]["features"].add(feature_name)

        # Identify overlaps (2+ products with same capability)
        for group_name, group_data in capability_groups.items():
            product_list = list(set(group_data["products"]))  # Deduplicate
            if len(product_list) >= 2:
                overlaps[group_name] = {
                    "products": product_list,
                    "overlap_count": len(product_list),
                    "feature_examples": list(group_data["features"])[:5]  # Top 5 features
                }

        return overlaps

    def analyze_pricing_comparison(self) -> Dict[str, Dict]:
        """Compare pricing models and costs across products"""
        pricing = {}

        for product_name, product_data in self.products.items():
            pricing_data = product_data.get('pricing', {})
            pricing[product_name] = {
                "model": pricing_data.get('model', 'Not available'),
                "tiers": pricing_data.get('tiers', []),
                "notes": pricing_data.get('notes', '')
            }

        return pricing

    def get_product_categories(self) -> Dict[str, List[str]]:
        """Group products by primary category"""
        categories = defaultdict(list)

        for product_name, product_data in self.products.items():
            category = product_data.get('category', 'Unknown')
            categories[category].append(product_name)

        return dict(categories)

    def generate_overlap_report(self) -> str:
        """Generate comprehensive feature overlap report"""
        report = []
        report.append("=" * 80)
        report.append("FEATURE OVERLAP ANALYSIS")
        report.append("=" * 80)
        report.append("")

        overlaps = self.analyze_feature_overlap()

        if not overlaps:
            report.append("✅ No significant feature overlaps detected")
            return "\n".join(report)

        report.append(f"🔍 Found {len(overlaps)} capability areas with overlaps:\n")

        for capability, data in sorted(overlaps.items(), key=lambda x: x[1]['overlap_count'], reverse=True):
            report.append(f"📦 {capability}")
            report.append(f"   Products: {', '.join(data['products'])} ({data['overlap_count']} products)")
            report.append(f"   Risk: {'⚠️  HIGH' if data['overlap_count'] >= 3 else '⚠️  MEDIUM'} - Potential duplicate spend")

            if data['feature_examples']:
                report.append(f"   Sample Features:")
                for feature in data['feature_examples'][:3]:
                    report.append(f"      • {feature}")
            report.append("")

        return "\n".join(report)

    def generate_category_summary(self) -> str:
        """Generate product category summary"""
        report = []
        report.append("=" * 80)
        report.append("PRODUCT CATEGORY SUMMARY")
        report.append("=" * 80)
        report.append("")

        categories = self.get_product_categories()

        for category, products in sorted(categories.items()):
            report.append(f"📂 {category}")
            for product in products:
                product_data = self.products[product]
                vendor = product_data.get('vendor', 'Unknown')
                focus = product_data.get('primary_focus', '')
                report.append(f"   • {product} ({vendor})")
                if focus:
                    report.append(f"     Focus: {focus}")
            report.append("")

        return "\n".join(report)

    def generate_full_analysis(self, output_file: str = None) -> str:
        """Generate complete analysis report"""
        report = []

        # Header
        report.append("=" * 80)
        report.append("ORRO MSP PRODUCT PORTFOLIO ANALYSIS")
        report.append("=" * 80)
        report.append(f"Products Analyzed: {len(self.products)}")
        report.append(f"Analysis Date: 2025-10-06")
        report.append("")

        # Category Summary
        report.append(self.generate_category_summary())

        # Feature Overlap Analysis
        report.append(self.generate_overlap_report())

        # Pricing Comparison
        report.append("=" * 80)
        report.append("PRICING COMPARISON")
        report.append("=" * 80)
        report.append("")

        pricing = self.analyze_pricing_comparison()
        for product, price_data in sorted(pricing.items()):
            report.append(f"💰 {product}")
            report.append(f"   Model: {price_data['model']}")

            if price_data['tiers']:
                report.append(f"   Tiers:")
                for tier in price_data['tiers']:
                    tier_name = tier.get('name', 'Unknown')
                    tier_price = tier.get('price', 'Not available')
                    report.append(f"      • {tier_name}: {tier_price}")

            if price_data['notes']:
                report.append(f"   Notes: {price_data['notes']}")
            report.append("")

        # Capability Matrix
        report.append("=" * 80)
        report.append("CAPABILITY MATRIX")
        report.append("=" * 80)
        report.append("")

        all_caps = self.get_all_capabilities()
        for cap, products in sorted(all_caps.items()):
            report.append(f"🔧 {cap}: {', '.join(products)}")

        report.append("")
        report.append("=" * 80)
        report.append("END OF ANALYSIS")
        report.append("=" * 80)

        full_report = "\n".join(report)

        # Save to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(full_report)
            print(f"\n✅ Full analysis saved to: {output_file}")

        return full_report

def main():
    """CLI interface for product intelligence analysis"""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze MSP product portfolio for overlaps and gaps")
    parser.add_argument('--overlap', action='store_true', help='Show feature overlap analysis')
    parser.add_argument('--categories', action='store_true', help='Show product category summary')
    parser.add_argument('--full', action='store_true', help='Generate full analysis report')
    parser.add_argument('--output', type=str, help='Save full report to file')

    args = parser.parse_args()

    analyzer = ProductIntelligenceAnalyzer()

    if not analyzer.products:
        print("❌ No products loaded. Check data directory.")
        return

    print(f"\n✅ Loaded {len(analyzer.products)} products\n")

    if args.overlap:
        print(analyzer.generate_overlap_report())
    elif args.categories:
        print(analyzer.generate_category_summary())
    elif args.full or args.output:
        report = analyzer.generate_full_analysis(output_file=args.output)
        if not args.output:
            print(report)
    else:
        # Default: show overlap analysis
        print(analyzer.generate_overlap_report())

if __name__ == "__main__":
    main()

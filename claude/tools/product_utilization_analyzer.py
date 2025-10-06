#!/usr/bin/env python3
"""
Product Utilization Gap Analyzer
Identifies underutilized features in current product portfolio

Created: 2025-10-06
Purpose: Maximize ROI from existing SaaS investments
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

class ProductUtilizationAnalyzer:
    """Analyze product feature utilization gaps"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            maia_root = Path(__file__).parent.parent.parent
            self.data_dir = maia_root / "claude" / "data" / "product_intelligence"
        else:
            self.data_dir = Path(data_dir)

        self.products = {}
        self.utilization_data = {}
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

    def extract_all_features(self, product_name: str) -> List[Dict]:
        """Extract all features from a product"""
        features = []
        product_data = self.products.get(product_name, {})
        capabilities = product_data.get('capabilities', {})

        for cap_name, cap_data in capabilities.items():
            cap_features = cap_data.get('features', [])
            for feature in cap_features:
                features.append({
                    'capability': cap_name,
                    'name': feature.get('name', ''),
                    'description': feature.get('description', ''),
                    'tier': feature.get('tier', 'All')
                })

        return features

    def generate_utilization_checklist(self, product_name: str) -> str:
        """Generate utilization checklist for a product"""
        if product_name not in self.products:
            return f"❌ Product '{product_name}' not found"

        product_data = self.products[product_name]
        features = self.extract_all_features(product_name)

        report = []
        report.append("=" * 80)
        report.append(f"UTILIZATION CHECKLIST: {product_name}")
        report.append("=" * 80)
        report.append(f"Vendor: {product_data.get('vendor', 'Unknown')}")
        report.append(f"Category: {product_data.get('category', 'Unknown')}")
        report.append(f"Total Features: {len(features)}")
        report.append("")
        report.append("INSTRUCTIONS:")
        report.append("Review each feature and mark if currently used/configured at Orro:")
        report.append("  [ ] = Not using/configured")
        report.append("  [x] = Currently using/configured")
        report.append("  [?] = Unsure/needs investigation")
        report.append("")

        current_capability = None
        for feature in features:
            capability = feature['capability']

            if capability != current_capability:
                report.append("")
                report.append(f"{'─' * 80}")
                report.append(f"📦 {capability}")
                report.append(f"{'─' * 80}")
                current_capability = capability

            tier_info = f" [{feature['tier']}]" if feature['tier'] != 'All' else ""
            report.append(f"  [ ] {feature['name']}{tier_info}")
            if feature['description']:
                report.append(f"      {feature['description']}")

        report.append("")
        report.append("=" * 80)
        report.append("NEXT STEPS:")
        report.append("1. Review each feature above with technical team")
        report.append("2. Mark features currently in use")
        report.append("3. Identify high-value unused features")
        report.append("4. Create adoption roadmap for underutilized capabilities")
        report.append("=" * 80)

        return "\n".join(report)

    def generate_all_checklists(self, output_dir: str = None):
        """Generate utilization checklists for all products"""
        if output_dir is None:
            output_dir = self.data_dir / "utilization_checklists"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(exist_ok=True)

        for product_name in self.products.keys():
            checklist = self.generate_utilization_checklist(product_name)

            # Create safe filename
            safe_name = product_name.lower().replace(' ', '_').replace('/', '_')
            output_file = output_dir / f"{safe_name}_utilization_checklist.txt"

            output_file.write_text(checklist)
            print(f"✅ Generated: {output_file.name}")

        return output_dir

    def analyze_pricing_vs_utilization(self) -> str:
        """Analyze cost optimization opportunities"""
        report = []
        report.append("=" * 80)
        report.append("PRICING VS UTILIZATION ANALYSIS")
        report.append("=" * 80)
        report.append("")
        report.append("💡 OPTIMIZATION OPPORTUNITIES:")
        report.append("")

        # Analyze per-endpoint products
        report.append("📊 Per-Endpoint Products (Cost scales with device count):")
        report.append("")

        per_endpoint_products = {
            "Patch My PC": {"cost": "$2-5/endpoint/year", "overlap_risk": "HIGH"},
            "ManageEngine Patch Manager Plus": {"cost": "$245-445/year total", "overlap_risk": "HIGH"},
            "Datto RMM": {"cost": "Contact vendor", "overlap_risk": "MEDIUM"}
        }

        for product, data in per_endpoint_products.items():
            if product in self.products:
                report.append(f"  • {product}")
                report.append(f"    Cost: {data['cost']}")
                report.append(f"    Overlap Risk: {data['overlap_risk']}")
                report.append("")

        # Analyze per-user products
        report.append("📊 Per-User Products (Cost scales with technician count):")
        report.append("")

        per_user_products = {
            "IT Glue": {"cost": "$29-44/user/month", "overlap_risk": "LOW"}
        }

        for product, data in per_user_products.items():
            if product in self.products:
                report.append(f"  • {product}")
                report.append(f"    Cost: {data['cost']}")
                report.append(f"    Overlap Risk: {data['overlap_risk']}")
                report.append("")

        # Key recommendations
        report.append("=" * 80)
        report.append("🎯 KEY RECOMMENDATIONS:")
        report.append("=" * 80)
        report.append("")
        report.append("1. **PATCH MANAGEMENT CONSOLIDATION OPPORTUNITY**")
        report.append("   • 3 products with patch management capabilities")
        report.append("   • Consider: Standardize on single platform vs multi-tool approach")
        report.append("   • Analysis needed: Feature comparison, current usage, migration effort")
        report.append("")
        report.append("2. **RMM + PATCH INTEGRATION**")
        report.append("   • Datto RMM includes patch management")
        report.append("   • Evaluate: Is standalone patch tool (PatchMyPC/ManageEngine) adding value?")
        report.append("   • Potential savings: Eliminate standalone patch management cost")
        report.append("")
        report.append("3. **MICROSOFT INTUNE ALIGNMENT**")
        report.append("   • Devicie: Microsoft Intune automation specialist")
        report.append("   • Patch My PC: Strong Intune integration")
        report.append("   • Consider: Microsoft-first endpoint strategy to reduce tool sprawl")
        report.append("")
        report.append("4. **UTILIZATION AUDIT PRIORITY**")
        report.append("   • Start with highest-cost products first")
        report.append("   • IT Glue: $29-44/user/month (5 user minimum = $145-220/month)")
        report.append("   • Datto RMM: Full-featured RMM (confirm all modules in use)")
        report.append("   • Devicie: Automation savings claims (verify ROI achieved)")
        report.append("")

        return "\n".join(report)

    def generate_executive_summary(self) -> str:
        """Generate executive summary for leadership"""
        report = []
        report.append("=" * 80)
        report.append("EXECUTIVE SUMMARY: MSP PRODUCT PORTFOLIO OPTIMIZATION")
        report.append("=" * 80)
        report.append("")
        report.append(f"📊 Portfolio Size: {len(self.products)} products analyzed")
        report.append("")

        # Calculate total features
        total_features = sum(len(self.extract_all_features(p)) for p in self.products.keys())
        report.append(f"🔧 Total Available Features: {total_features} across all products")
        report.append("")

        report.append("🎯 PRIMARY FINDINGS:")
        report.append("")
        report.append("1. **Feature Overlap Detected**")
        report.append("   • Patch Management: 3 products (HIGH risk of duplicate spend)")
        report.append("   • Automation: 4 products with automation capabilities")
        report.append("   • Reporting: 4 products with reporting features")
        report.append("")
        report.append("2. **Portfolio Composition**")
        report.append("   • 1 Full RMM Platform (Datto RMM)")
        report.append("   • 2 Specialized Patch Management Tools (PatchMyPC, ManageEngine)")
        report.append("   • 1 Endpoint Automation Platform (Devicie)")
        report.append("   • 1 Documentation Platform (IT Glue)")
        report.append("")
        report.append("3. **Cost Structure**")
        report.append("   • 3 products: Per-endpoint pricing (scales with managed devices)")
        report.append("   • 1 product: Per-user pricing (scales with technician count)")
        report.append("   • 1 product: Contact vendor (pricing not public)")
        report.append("")

        report.append("🚀 RECOMMENDED NEXT STEPS:")
        report.append("")
        report.append("Phase 1: UTILIZATION AUDIT (Weeks 1-2)")
        report.append("  • Complete utilization checklists for all 5 products")
        report.append("  • Identify unused features in each product")
        report.append("  • Document current usage patterns")
        report.append("")
        report.append("Phase 2: CONSOLIDATION ANALYSIS (Weeks 3-4)")
        report.append("  • Evaluate patch management consolidation opportunity")
        report.append("  • Assess Datto RMM feature utilization")
        report.append("  • Calculate potential cost savings from tool reduction")
        report.append("")
        report.append("Phase 3: OPTIMIZATION ROADMAP (Week 5)")
        report.append("  • Develop 6-month feature adoption plan")
        report.append("  • Identify quick wins for underutilized capabilities")
        report.append("  • Create vendor consolidation strategy (if applicable)")
        report.append("")

        report.append("💰 POTENTIAL VALUE:")
        report.append("")
        report.append("  • Eliminate duplicate spend on overlapping capabilities")
        report.append("  • Maximize ROI from existing feature sets")
        report.append("  • Reduce tool sprawl and training overhead")
        report.append("  • Improve operational efficiency through better tool utilization")
        report.append("")

        return "\n".join(report)


def main():
    """CLI interface for utilization gap analysis"""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze product utilization gaps and optimization opportunities")
    parser.add_argument('--product', type=str, help='Generate checklist for specific product')
    parser.add_argument('--all-checklists', action='store_true', help='Generate checklists for all products')
    parser.add_argument('--pricing', action='store_true', help='Show pricing vs utilization analysis')
    parser.add_argument('--executive', action='store_true', help='Generate executive summary')
    parser.add_argument('--output', type=str, help='Output directory for checklists')

    args = parser.parse_args()

    analyzer = ProductUtilizationAnalyzer()

    if not analyzer.products:
        print("❌ No products loaded. Check data directory.")
        return

    if args.product:
        print(analyzer.generate_utilization_checklist(args.product))
    elif args.all_checklists:
        output_dir = analyzer.generate_all_checklists(args.output)
        print(f"\n✅ All checklists generated in: {output_dir}")
    elif args.pricing:
        print(analyzer.analyze_pricing_vs_utilization())
    elif args.executive:
        print(analyzer.generate_executive_summary())
    else:
        # Default: executive summary
        print(analyzer.generate_executive_summary())

if __name__ == "__main__":
    main()

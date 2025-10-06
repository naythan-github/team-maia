#!/usr/bin/env python3
"""
Product Standardization Fixer
Applies intelligent rules to fix obvious garbage matches before semantic AI guessing

Created: 2025-10-06
Purpose: Rule-based product categorization to prevent stupid AI matches
"""

import pandas as pd
import re
from typing import Optional, Tuple

class ProductStandardizationFixer:
    """Fix garbage matches with actual business logic"""

    def __init__(self):
        self.rules = self._build_rules()

    def _build_rules(self):
        """
        Build rule-based categorization

        Rules are applied in order (first match wins)
        Each rule returns (category, base_product, confidence)
        """
        return [
            # HARDWARE - Physical equipment
            (r'macbook|iphone|ipad|apple\s+m[0-9]', 'Hardware', 'Apple Hardware', 1.0),
            (r'meraki.*adapter|meraki.*power|switch|router|firewall|access point', 'Hardware', 'Network Hardware', 1.0),
            (r'ruggedized.*switch|poe\s+switch', 'Hardware', 'Network Hardware', 1.0),

            # SHIPPING & FREIGHT
            (r'^freight$|^shipping$', 'Logistics', 'Freight/Shipping', 1.0),

            # INTERNET - Extract speed if possible
            (r'internet.*1000\s*mbps|1000mbps.*internet|gigabit', 'Internet', 'Internet - 1000Mbps', 0.95),
            (r'internet.*400\s*mbps|400mbps.*internet', 'Internet', 'Internet - 400Mbps', 0.95),
            (r'internet.*100\s*mbps|100mbps.*internet', 'Internet', 'Internet - 100Mbps', 0.95),
            (r'internet.*nbn|nbn.*internet', 'Internet', 'Internet - NBN', 0.90),
            (r'internet|broadband', 'Internet', 'Internet Service', 0.85),

            # TELEPHONY
            (r'1300\s*number|1800\s*number', 'Telephony', 'Hosted Number Service', 1.0),
            (r'direct\s*inward\s*dial|did\s', 'Telephony', 'Direct Inward Dial', 1.0),
            (r'sip\s*trunk|sip\s*line', 'Telephony', 'SIP Trunking', 0.95),
            (r'3cx', 'Telephony', '3CX Phone System', 0.95),
            (r'hosted.*voice|voice.*hosted', 'Telephony', 'Hosted Voice Service', 0.90),

            # BACKUP & DISASTER RECOVERY
            (r'datto|backup.*license|replication', 'Backup', 'Backup/DR Service', 0.95),

            # EMAIL SERVICES
            (r'sendgrid|twilio|smtp\s*service', 'Email Services', 'Email Delivery Service', 0.95),

            # DOMAIN & WEB HOSTING
            (r'domain.*registration|\.com\.au|\.com\s', 'Web Services', 'Domain Registration', 1.0),
            (r'web\s*hosting|hosting.*service', 'Web Services', 'Web Hosting', 0.95),

            # CUSTOMER-SPECIFIC ITEMS (don't try to match)
            (r'phocus|selcomm|bellamy', 'Custom', 'Customer-Specific Item', 0.90),

            # LOCATION-BASED (addresses in description)
            (r'street|drive|esplanade|court|avenue|nsw|qld|vic|sa|wa|nt|act', 'Location-Specific', 'Site-Specific Service', 0.85),

            # USAGE/BILLING ITEMS
            (r'usageamount|usage\s*charge|billing|invoice\s*for', 'Billing', 'Usage/Billing Item', 0.90),
            (r'^\s*december|^\s*january|^\s*february', 'Billing', 'Period Billing Item', 0.90),

            # ONSITE SERVICES
            (r'onsite|on-site|physical\s*resource', 'Professional Services', 'Onsite Support', 1.0),

            # SUPPORT CONTRACTS
            (r'support\s*-\s*platinum|support\s*-\s*premium|dedicated\s*support', 'Support', 'Premium Support Contract', 0.95),
            (r'maintenance.*annual|annual.*maintenance', 'Support', 'Annual Maintenance', 0.95),
        ]

    def apply_rules(self, description: str) -> Optional[Tuple[str, str, float]]:
        """
        Apply rules to description

        Returns (category, product, confidence) or None if no rule matches
        """
        if pd.isna(description):
            return None

        desc_lower = str(description).lower()

        for pattern, category, product, confidence in self.rules:
            if re.search(pattern, desc_lower):
                return (category, product, confidence)

        return None

    def fix_dataframe(self, df: pd.DataFrame, column: str = 'Shortened Description') -> pd.DataFrame:
        """
        Apply rules to fix garbage matches

        Strategy:
        1. Apply rules first (high confidence)
        2. Keep existing matches if >75% confidence AND no rule override
        3. Mark low confidence + no rule match as "NEEDS CATEGORIZATION"
        """
        df_fixed = df.copy()

        fixes_applied = 0
        for idx, row in df_fixed.iterrows():
            description = row[column]
            current_match = row.get('standardized_product', '')
            current_confidence = row.get('match_confidence', 0)

            # Try rules first
            rule_result = self.apply_rules(description)

            if rule_result:
                category, product, confidence = rule_result

                # Apply rule if:
                # 1. Current confidence is low (<75%), OR
                # 2. Rule confidence is higher
                if current_confidence < 0.75 or confidence > current_confidence:
                    df_fixed.at[idx, 'standardized_product'] = product
                    df_fixed.at[idx, 'match_confidence'] = confidence
                    df_fixed.at[idx, 'match_strategy'] = 'rule-based'
                    df_fixed.at[idx, 'needs_review'] = False
                    df_fixed.at[idx, 'product_category'] = category
                    fixes_applied += 1

            elif current_confidence < 0.50:
                # No rule match AND low confidence = needs manual categorization
                df_fixed.at[idx, 'standardized_product'] = 'NEEDS CATEGORIZATION'
                df_fixed.at[idx, 'match_strategy'] = 'failed'
                df_fixed.at[idx, 'needs_review'] = True
                df_fixed.at[idx, 'product_category'] = 'Unknown'

        print(f"✅ Applied {fixes_applied} rule-based fixes")
        return df_fixed


def main():
    """Fix the garbage matches"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python product_standardization_fixer.py <standardized_file.xlsx>")
        sys.exit(1)

    input_file = sys.argv[1]

    print(f"📂 Loading {input_file}...")
    df = pd.read_excel(input_file, sheet_name='Standardized')

    print(f"📊 Original stats:")
    print(f"   Low confidence (<75%): {(df['match_confidence'] < 0.75).sum()}")
    print(f"   Very low (<50%): {(df['match_confidence'] < 0.50).sum()}")

    # Apply fixes
    fixer = ProductStandardizationFixer()
    df_fixed = fixer.fix_dataframe(df)

    print(f"\n📊 After rule-based fixes:")
    print(f"   Low confidence (<75%): {(df_fixed['match_confidence'] < 0.75).sum()}")
    print(f"   Very low (<50%): {(df_fixed['match_confidence'] < 0.50).sum()}")
    print(f"   Needs categorization: {(df_fixed['standardized_product'] == 'NEEDS CATEGORIZATION').sum()}")

    # Export
    from pathlib import Path
    output_file = Path(input_file).parent / f"{Path(input_file).stem}_FIXED.xlsx"

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_fixed.to_excel(writer, sheet_name='Standardized', index=False)

        # Show what was fixed
        fixes = df_fixed[df_fixed['match_strategy'] == 'rule-based'].drop_duplicates('Shortened Description')
        fixes[['Shortened Description', 'standardized_product', 'product_category', 'match_confidence']].to_excel(
            writer, sheet_name='Rule-Based Fixes', index=False
        )

        # Show what still needs work
        needs_work = df_fixed[df_fixed['standardized_product'] == 'NEEDS CATEGORIZATION'].drop_duplicates('Shortened Description')
        needs_work[['Shortened Description', 'match_confidence']].to_excel(
            writer, sheet_name='Needs Categorization', index=False
        )

    print(f"\n💾 Exported fixed data to: {output_file}")


if __name__ == '__main__':
    main()

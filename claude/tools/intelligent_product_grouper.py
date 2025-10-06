#!/usr/bin/env python3
"""
Intelligent Product Grouper
Actually groups similar product variants to base products

Created: 2025-10-06
Purpose: Reduce variance by intelligently grouping product variants
"""

import pandas as pd
import re
from typing import Tuple

class IntelligentProductGrouper:
    """Group product variants to base products using business logic"""

    def standardize_product(self, description: str) -> Tuple[str, float, str]:
        """
        Extract base product from variant description

        Returns: (standardized_product, confidence, strategy)
        """
        if pd.isna(description):
            return ("Unknown", 0.0, "empty")

        desc = str(description).strip()
        desc_lower = desc.lower()

        # Microsoft 365 grouping
        if 'microsoft 365' in desc_lower:
            if 'business basic' in desc_lower:
                return ("Microsoft 365 Business Basic", 1.0, "exact")
            elif 'business standard' in desc_lower:
                return ("Microsoft 365 Business Standard", 1.0, "exact")
            elif 'business premium' in desc_lower:
                return ("Microsoft 365 Business Premium", 1.0, "exact")
            elif ' e3' in desc_lower or 'e3 ' in desc_lower or desc_lower.endswith('e3'):
                return ("Microsoft 365 E3", 1.0, "exact")
            elif ' e5' in desc_lower or 'e5 ' in desc_lower or desc_lower.endswith('e5'):
                return ("Microsoft 365 E5", 1.0, "exact")
            elif ' f3' in desc_lower or 'f3 ' in desc_lower or desc_lower.endswith('f3'):
                return ("Microsoft 365 F3", 1.0, "exact")
            elif ' f1' in desc_lower or 'f1 ' in desc_lower or desc_lower.endswith('f1'):
                return ("Microsoft 365 F1", 1.0, "exact")
            elif 'copilot' in desc_lower:
                return ("Microsoft 365 Copilot", 1.0, "exact")
            elif 'apps for business' in desc_lower:
                return ("Microsoft 365 Apps for Business", 1.0, "exact")
            elif 'apps for enterprise' in desc_lower:
                return ("Microsoft 365 Apps for Enterprise", 1.0, "exact")
            elif 'audio conferencing' in desc_lower:
                return ("Microsoft 365 Audio Conferencing", 1.0, "exact")
            else:
                return (desc, 0.85, "m365_variant")

        # Office 365 grouping
        if 'office 365' in desc_lower and 'microsoft 365' not in desc_lower:
            if 'business basic' in desc_lower:
                return ("Office 365 Business Basic", 1.0, "exact")
            elif 'business standard' in desc_lower:
                return ("Office 365 Business Standard", 1.0, "exact")
            elif 'business premium' in desc_lower:
                return ("Office 365 Business Premium", 1.0, "exact")
            elif ' e1' in desc_lower or 'e1 ' in desc_lower or desc_lower.endswith('e1'):
                return ("Office 365 E1", 1.0, "exact")
            elif ' e3' in desc_lower or 'e3 ' in desc_lower or desc_lower.endswith('e3'):
                return ("Office 365 E3", 1.0, "exact")
            elif ' e5' in desc_lower or 'e5 ' in desc_lower or desc_lower.endswith('e5'):
                return ("Office 365 E5", 1.0, "exact")
            elif 'backup' in desc_lower:
                return ("Office 365 Backup", 1.0, "exact")
            else:
                return (desc, 0.85, "o365_variant")

        # Exchange Online grouping
        if 'exchange online' in desc_lower:
            if 'plan 1' in desc_lower or '(plan 1)' in desc_lower:
                return ("Exchange Online Plan 1", 1.0, "exact")
            elif 'plan 2' in desc_lower or '(plan 2)' in desc_lower:
                return ("Exchange Online Plan 2", 1.0, "exact")
            elif 'archiving' in desc_lower:
                return ("Exchange Online Archiving", 1.0, "exact")
            else:
                return (desc, 0.85, "exchange_variant")

        # Teams grouping
        if 'teams' in desc_lower and 'microsoft' in desc_lower:
            if 'phone standard' in desc_lower:
                return ("Microsoft Teams Phone Standard", 1.0, "exact")
            elif 'rooms pro' in desc_lower:
                return ("Microsoft Teams Rooms Pro", 1.0, "exact")
            elif 'premium' in desc_lower:
                return ("Microsoft Teams Premium", 1.0, "exact")
            elif 'enterprise' in desc_lower:
                return ("Microsoft Teams Enterprise", 1.0, "exact")
            else:
                return (desc, 0.85, "teams_variant")

        # Power Platform grouping
        if 'power bi' in desc_lower:
            if 'pro' in desc_lower:
                return ("Power BI Pro", 1.0, "exact")
            elif 'premium' in desc_lower:
                return ("Power BI Premium", 1.0, "exact")
            else:
                return (desc, 0.85, "powerbi_variant")

        if 'power automate' in desc_lower:
            if 'premium' in desc_lower:
                return ("Power Automate Premium", 1.0, "exact")
            elif 'per user' in desc_lower:
                return ("Power Automate Per User", 1.0, "exact")
            else:
                return (desc, 0.85, "powerautomate_variant")

        if 'power apps' in desc_lower:
            if 'premium' in desc_lower:
                return ("Power Apps Premium", 1.0, "exact")
            else:
                return (desc, 0.85, "powerapps_variant")

        # Dynamics grouping
        if 'dynamics 365' in desc_lower:
            if 'business central' in desc_lower:
                if 'essentials' in desc_lower:
                    return ("Dynamics 365 Business Central Essentials", 1.0, "exact")
                elif 'team members' in desc_lower:
                    return ("Dynamics 365 Business Central Team Members", 1.0, "exact")
                else:
                    return ("Dynamics 365 Business Central", 0.95, "dynamics_variant")
            elif 'customer service' in desc_lower:
                return ("Dynamics 365 Customer Service", 1.0, "exact")
            else:
                return (desc, 0.85, "dynamics_variant")

        # Azure/VM grouping
        if 'azure' in desc_lower:
            if 'virtual machine' in desc_lower or 'vm instance' in desc_lower or re.search(r'virtual machines [a-z]+v?\d+ series', desc_lower):
                # Extract VM series
                match = re.search(r'(bs|dsv?\d+|fsv?\d+|esv?\d+) series', desc_lower)
                if match:
                    series = match.group(1).upper()
                    return (f"Azure Virtual Machine - {series} Series", 0.95, "azure_vm")
                else:
                    return ("Azure Virtual Machines", 0.90, "azure_vm")
            elif 'azure plan' in desc_lower or 'azure subscription' in desc_lower:
                return ("Azure Plan", 1.0, "exact")
            elif 'active directory' in desc_lower or 'entra id' in desc_lower:
                if 'premium p1' in desc_lower or 'p1' in desc_lower:
                    return ("Microsoft Entra ID P1", 1.0, "exact")
                elif 'premium p2' in desc_lower or 'p2' in desc_lower:
                    return ("Microsoft Entra ID P2", 1.0, "exact")
                else:
                    return ("Microsoft Entra ID", 0.90, "entra_variant")
            else:
                return (desc, 0.80, "azure_variant")

        # Internet/Connectivity grouping
        if any(word in desc_lower for word in ['internet', 'broadband', 'fibre', 'fiber', 'nbn']):
            # Extract speed if possible
            speed_match = re.search(r'(\d+)\s*(mb|gb|mbps|gbps)', desc_lower)
            if speed_match:
                speed_num = int(speed_match.group(1))
                speed_unit = speed_match.group(2)
                if 'gb' in speed_unit:
                    speed_num *= 1000

                if speed_num >= 1000:
                    return ("Internet - 1000Mbps", 0.95, "internet_speed")
                elif speed_num >= 400:
                    return ("Internet - 400Mbps", 0.95, "internet_speed")
                elif speed_num >= 100:
                    return ("Internet - 100Mbps", 0.95, "internet_speed")
                else:
                    return (f"Internet - {speed_num}Mbps", 0.90, "internet_speed")
            else:
                return ("Internet Service", 0.85, "internet_generic")

        # Support Services grouping
        if 'support' in desc_lower:
            if 'user support' in desc_lower or 'desktop support' in desc_lower:
                return ("User Support", 0.95, "support_type")
            elif 'server support' in desc_lower:
                return ("Server Support", 0.95, "support_type")
            elif 'network support' in desc_lower:
                return ("Network Support", 0.95, "support_type")
            elif 'printer support' in desc_lower:
                return ("Printer Support", 0.95, "support_type")
            elif 'onsite' in desc_lower or 'on-site' in desc_lower:
                return ("Onsite Support", 0.95, "support_type")
            else:
                return ("Support Services", 0.80, "support_generic")

        # Telephony grouping
        if any(word in desc_lower for word in ['sip', '3cx', 'voip', 'pbx', 'phone']):
            if '3cx' in desc_lower:
                return ("3CX Phone System", 0.95, "telephony")
            elif 'sip' in desc_lower:
                return ("SIP Trunking", 0.95, "telephony")
            else:
                return ("Telephony Services", 0.85, "telephony")

        # If no pattern matched, keep original but flag for review
        return (desc, 0.70, "unmatched")


def main():
    """Process unique.xlsx with intelligent grouping"""

    # Load data
    input_file = '/Users/naythandawe/Library/CloudStorage/OneDrive-ORROPTYLTD/Documents/Claude/unique.xlsx'
    df = pd.read_excel(input_file)

    print(f"📂 Processing {len(df)} unique descriptions...\n")

    # Apply grouping
    grouper = IntelligentProductGrouper()

    results = []
    for desc in df['Shortened Description']:
        standardized, confidence, strategy = grouper.standardize_product(desc)
        results.append({
            'Shortened Description': desc,
            'Standardized Product': standardized,
            'Confidence Score': confidence,
            'Review Needed': 'Yes' if confidence < 0.75 else 'No',
            'Strategy': strategy
        })

    result_df = pd.DataFrame(results)

    # Output
    output_file = '/Users/naythandawe/Library/CloudStorage/OneDrive-ORROPTYLTD/Documents/Claude/unique_STANDARDIZED.xlsx'
    result_df[['Shortened Description', 'Standardized Product', 'Confidence Score', 'Review Needed']].to_excel(
        output_file, index=False, sheet_name='Standardized'
    )

    # Stats
    print(f"📊 Results:")
    print(f"   Input unique: {result_df['Shortened Description'].nunique()}")
    print(f"   Output unique: {result_df['Standardized Product'].nunique()}")
    print(f"   Variance reduction: {(1 - result_df['Standardized Product'].nunique() / result_df['Shortened Description'].nunique()):.1%}")
    print(f"\n   High confidence (≥75%): {(result_df['Review Needed'] == 'No').sum()} ({(result_df['Review Needed'] == 'No').sum()/len(result_df):.1%})")
    print(f"   Needs review: {(result_df['Review Needed'] == 'Yes').sum()} ({(result_df['Review Needed'] == 'Yes').sum()/len(result_df):.1%})")

    print(f"\n💾 Exported to: {output_file}")

    # Show grouping examples
    print(f"\n📋 Grouping Examples:")
    for base_product in result_df['Standardized Product'].value_counts().head(10).index:
        variants = result_df[result_df['Standardized Product'] == base_product]['Shortened Description'].tolist()
        print(f"\n   {base_product} ({len(variants)} variants):")
        for v in variants[:3]:
            print(f"      • {v}")
        if len(variants) > 3:
            print(f"      ... and {len(variants) - 3} more")


if __name__ == '__main__':
    main()

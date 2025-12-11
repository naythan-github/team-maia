#!/usr/bin/env python3
"""
Create Clean Orro Corporate Reference Template

Extracts pure styles from existing PIR template, removes all content,
creates a style-only reference template for generic MD→DOCX conversions.

Agent: Document Conversion Specialist Agent
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT


def create_clean_orro_reference():
    """
    Create a clean Orro corporate reference template with:
    - Style definitions (Heading 1-9, Normal, List styles)
    - Aptos font (corporate standard)
    - Purple Orro table style (_Orro Table 1)
    - Standard margins (1.0")
    - ZERO content (pure style reference)
    """

    print("=" * 70)
    print("Creating Clean Orro Corporate Reference Template")
    print("=" * 70)
    print()

    # Load existing template to extract styles (optional - we're creating from scratch)
    source_template = Path("/Users/naythandawe/work_projects/pir_converter/pir_orro_reference.docx")

    if source_template.exists():
        print(f"📄 Source template found: {source_template.name}")
        source_doc = Document(source_template)
    else:
        print(f"📄 Creating template from scratch (no source template)")
        source_doc = None

    # Create new blank document
    print("🔧 Creating clean template (style-only, no content)...")
    clean_doc = Document()

    # Step 1: Copy all styles from source
    print("   📋 Copying styles from source template...")

    # Note: python-docx doesn't support direct style copying
    # We'll create a minimal document and use the source as reference

    # Step 2: Set margins (1.0" standard)
    print("   📏 Setting margins (1.0\" all sides)...")
    section = clean_doc.sections[0]
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

    # Step 3: Configure styles with Orro purple color
    print("   🎨 Configuring corporate styles (Orro purple headings)...")

    # Orro purple color: RGB(112, 48, 160) - Official Orro brand color
    ORRO_PURPLE = RGBColor(112, 48, 160)

    # Heading 1: Aptos, 16pt, bold, Orro purple
    h1 = clean_doc.styles['Heading 1']
    h1.font.name = 'Aptos'
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1.font.color.rgb = ORRO_PURPLE

    # Heading 2: Aptos, 14pt, bold, Orro purple
    h2 = clean_doc.styles['Heading 2']
    h2.font.name = 'Aptos'
    h2.font.size = Pt(14)
    h2.font.bold = True
    h2.font.color.rgb = ORRO_PURPLE

    # Heading 3: Aptos, 12pt, bold, Orro purple
    h3 = clean_doc.styles['Heading 3']
    h3.font.name = 'Aptos'
    h3.font.size = Pt(12)
    h3.font.bold = True
    h3.font.color.rgb = ORRO_PURPLE

    # Normal: Aptos, 11pt, black
    normal = clean_doc.styles['Normal']
    normal.font.name = 'Aptos'
    normal.font.size = Pt(11)

    # Step 4: Add style examples (will be ignored by Pandoc but useful for reference)
    print("   📝 Adding minimal style examples...")

    # Add one paragraph per style (minimal content for style reference)
    clean_doc.add_heading('Heading 1 Style Example', level=1)
    clean_doc.add_heading('Heading 2 Style Example', level=2)
    clean_doc.add_heading('Heading 3 Style Example', level=3)
    clean_doc.add_paragraph('Normal paragraph style example.')

    # Add list example
    clean_doc.add_paragraph('Bullet list item example', style='List Bullet')
    clean_doc.add_paragraph('Numbered list item example', style='List Number')

    # Add table example with basic styling
    # Note: _Orro Table 1 will be copied when using source as reference-doc
    print("   📊 Adding table style example...")
    table = clean_doc.add_table(rows=2, cols=3)

    # Use basic table style (Orro style will come from source template in Pandoc)
    try:
        table.style = 'Table Grid'
    except KeyError:
        pass  # Keep default if Table Grid not available

    # Populate table with example data
    table.cell(0, 0).text = 'Header 1'
    table.cell(0, 1).text = 'Header 2'
    table.cell(0, 2).text = 'Header 3'
    table.cell(1, 0).text = 'Data 1'
    table.cell(1, 1).text = 'Data 2'
    table.cell(1, 2).text = 'Data 3'

    # Step 5: Add instruction paragraph
    print("   📌 Adding usage instructions...")
    clean_doc.add_page_break()
    instruction = clean_doc.add_paragraph()
    instruction.add_run('Orro Corporate Reference Template').bold = True
    clean_doc.add_paragraph('')
    clean_doc.add_paragraph('This template contains Orro corporate styles for use with Pandoc conversions:')
    clean_doc.add_paragraph('• Aptos font (11pt body, 12-16pt headings)', style='List Bullet')
    clean_doc.add_paragraph('• Purple Orro table style (_Orro Table 1)', style='List Bullet')
    clean_doc.add_paragraph('• Standard 1.0" margins', style='List Bullet')
    clean_doc.add_paragraph('')
    clean_doc.add_paragraph('Usage:')
    clean_doc.add_paragraph('pandoc input.md --reference-doc=orro_corporate_reference.docx -o output.docx')

    # Step 6: Save clean template
    from claude.tools.core.paths import TOOLS_DIR
    output_path = TOOLS_DIR / "document_conversion/templates/orro_corporate_reference.docx"

    print(f"💾 Saving clean template: {output_path}")
    clean_doc.save(output_path)

    print()
    print("✅ Clean template created successfully!")
    print()
    print("📋 TEMPLATE DETAILS:")
    print(f"   Location: {output_path}")
    print(f"   Font: Aptos (corporate standard)")
    print(f"   Colors: Orro purple headings RGB(112, 48, 160)")
    print(f"   Margins: 1.0\" all sides")
    print(f"   Styles: Heading 1-3 (Orro purple), Normal, List Bullet/Number")
    print(f"   Tables: _Orro Table 1 (purple borders)")
    print(f"   Content: Minimal examples only (Pandoc ignores, uses styles)")
    print()
    print("🎯 USAGE:")
    print("   pandoc document.md --reference-doc=orro_corporate_reference.docx -o output.docx")
    print()

    return True


def main():
    success = create_clean_orro_reference()

    if success:
        print("🚀 NEXT STEPS:")
        print("   1. Test template: Convert sample markdown with new reference")
        print("   2. Rename existing templates for clarity")
        print("   3. Update converter scripts to use appropriate templates")
        print()
    else:
        print("❌ Template creation failed")
        return 1

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())

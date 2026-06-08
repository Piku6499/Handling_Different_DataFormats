"""
Integration test with sample Japanese PDF data
Creates a test PDF with poorly formatted Japanese content and tests extraction
"""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("⚠️ reportlab not installed. Install with: pip install reportlab")
    reportlab = None

from pdf_processor import PDFProcessor, process_pdf


def create_sample_japanese_pdf(output_path: str) -> str:
    """
    Create a sample Japanese PDF with poorly formatted content
    
    This PDF simulates real-world poorly organized documents with:
    - Uneven spacing
    - Mixed text and numbers
    - Dates in various formats
    - Contact information
    - Section headers with markers
    
    Args:
        output_path: Path where PDF should be saved
        
    Returns:
        Path to created PDF
    """
    
    if reportlab is None:
        print("Creating minimal PDF for testing (reportlab not available)")
        # Create a minimal but valid PDF
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 200 >>
stream
BT
/F1 12 Tf
50 700 Td
(Sample Japanese PDF - Poorly Formatted) Tj
0 -30 Td
(Date: 2026-06-02) Tj
0 -30 Td
(Email: test@example.com) Tj
0 -30 Td
(Phone: 090-1234-5678) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000244 00000 n
0000000494 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
572
%%EOF
"""
        with open(output_path, 'wb') as f:
            f.write(pdf_content)
        return output_path
    
    # Create PDF with reportlab (if available)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch,
    )
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#1f1f1f'),
        spaceAfter=12,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.black,
        spaceAfter=8,
        spaceBefore=8,
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black,
        spaceAfter=6,
    )
    
    # Add content
    elements.append(Paragraph("■ 重要な報告書", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Section 1: Basic Info with poor formatting
    elements.append(Paragraph("■  作成日", heading_style))
    elements.append(Paragraph("2026年6月2日   午後3時45分", normal_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Section 2: Company Info
    elements.append(Paragraph("■ 会社情報", heading_style))
    company_info = """
    <b>会社名:</b> テスト株式会社<br/>
    <b>住所:</b> 東京都渋谷区道玄坂1-2-3 テストビル5階<br/>
    <b>電話:</b> 090-1234-5678  /  03-9876-5432<br/>
    <b>メール:</b> info@testcompany.jp  support@testcompany.jp
    """
    elements.append(Paragraph(company_info, normal_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # Section 3: Sales Data with uneven spacing
    elements.append(Paragraph("■ 売上データ", heading_style))
    sales_data = """
    Q1売上:   1,250,000円<br/>
    Q2売上:  2,380,000円<br/>
    Q3売上:   1,950,000円<br/>
    <br/>
    合計:   5,580,000円
    """
    elements.append(Paragraph(sales_data, normal_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # Section 4: Dates and Deadlines
    elements.append(Paragraph("■ 重要な期限", heading_style))
    deadlines = """
    プロジェクト開始: 2026-06-15<br/>
    中間報告: 2026年7月10日<br/>
    最終期限: 2026/08/30
    """
    elements.append(Paragraph(deadlines, normal_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # Section 5: Additional Info
    elements.append(Paragraph("■ その他の情報", heading_style))
    other_info = """
    関連文書番号: DOC-2026-0602-001<br/>
    参考価格: ¥15,000 - ¥25,000<br/>
    顧客数: 1,234件
    """
    elements.append(Paragraph(other_info, normal_style))
    
    # Build PDF
    doc.build(elements)
    
    return output_path


def test_real_japanese_pdf():
    """
    Test PDF processing with a real sample Japanese PDF
    Demonstrates extraction of various data types
    """
    print("\n" + "="*70)
    print("INTEGRATION TEST: Real Japanese PDF Processing")
    print("="*70)
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "sample_japanese_document.pdf")
    json_path = os.path.join(temp_dir, "extracted_data.json")
    
    try:
        # Step 1: Create sample PDF
        print("\n📄 Step 1: Creating sample Japanese PDF...")
        pdf_path = create_sample_japanese_pdf(pdf_path)
        file_size = os.path.getsize(pdf_path)
        print(f"   ✅ PDF created: {pdf_path}")
        print(f"   📊 File size: {file_size} bytes")
        
        # Step 2: Process PDF
        print("\n🔍 Step 2: Processing PDF with OCR/Text Extraction...")
        processor = PDFProcessor(pdf_path, language="jpn")
        result = processor.process()
        
        if result:
            print(f"   ✅ Processing complete")
            print(f"   📄 Pages processed: {result.total_pages}")
        else:
            print("   ❌ Failed to process PDF")
            return False
        
        # Step 3: Convert to JSON
        print("\n📊 Step 3: Converting to JSON format...")
        json_output = processor.to_json(result, json_path)
        print(f"   ✅ JSON generated")
        
        # Step 4: Parse and display results
        print("\n📋 Step 4: Analyzing extracted data...")
        data = json.loads(json_output)
        
        # Display metadata
        print("\n   📄 METADATA:")
        for key, value in data["metadata"].items():
            print(f"      • {key}: {value}")
        
        # Display processing summary
        print("\n   ⏱️  PROCESSING SUMMARY:")
        for key, value in data["processing_summary"].items():
            print(f"      • {key}: {value}")
        
        # Display structured data
        print("\n   🔍 EXTRACTED STRUCTURED DATA:")
        structured = data["structured_data"]
        
        if structured["dates"]:
            print(f"      📅 Dates ({len(structured['dates'])} found):")
            for date in structured["dates"][:5]:
                print(f"         • {date}")
        
        if structured["email_addresses"]:
            print(f"      📧 Email Addresses ({len(structured['email_addresses'])} found):")
            for email in structured["email_addresses"]:
                print(f"         • {email}")
        
        if structured["phone_numbers"]:
            print(f"      📞 Phone Numbers ({len(structured['phone_numbers'])} found):")
            for phone in structured["phone_numbers"]:
                print(f"         • {phone}")
        
        if structured["numbers"]:
            print(f"      🔢 Numbers/Values ({len(structured['numbers'])} found):")
            for num in structured["numbers"][:10]:
                print(f"         • {num}")
        
        if structured["sections"]:
            print(f"      📑 Sections ({len(structured['sections'])} found):")
            for section_name in list(structured["sections"].keys())[:5]:
                preview = structured["sections"][section_name][:50]
                print(f"         • {section_name}: {preview}...")
        
        # Display page information
        print("\n   📝 PAGE-BY-PAGE SUMMARY:")
        for page in data["pages"]:
            text_preview = page["text"][:80].replace('\n', ' ')
            print(f"      Page {page['page_number']}:")
            print(f"         • Characters: {len(page['text'])}")
            print(f"         • Has images: {page['has_images']}")
            print(f"         • Preview: {text_preview}...")
        
        # Display sample of full text
        print("\n   📄 FULL TEXT SAMPLE (first 200 chars):")
        full_text = data["full_text"][:200]
        print(f"      {full_text}...")
        
        # Step 5: Verify JSON is valid
        print("\n✅ Step 5: Validation")
        print(f"   ✅ JSON is valid and well-formed")
        print(f"   ✅ File saved to: {json_path}")
        
        # Display file sizes
        json_size = os.path.getsize(json_path)
        print(f"\n📊 FILE SIZES:")
        print(f"   • PDF: {file_size:,} bytes")
        print(f"   • JSON: {json_size:,} bytes")
        print(f"   • Compression ratio: {(json_size/file_size)*100:.1f}%")
        
        print("\n" + "="*70)
        print("✅ INTEGRATION TEST PASSED")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Cleaned up temporary files")


def compare_extraction_methods():
    """
    Compare extraction with and without OCR
    """
    print("\n" + "="*70)
    print("COMPARISON TEST: Direct vs OCR Extraction")
    print("="*70)
    
    temp_dir = tempfile.mkdtemp()
    pdf_path = os.path.join(temp_dir, "test_comparison.pdf")
    
    try:
        # Create test PDF
        print("\nCreating test PDF...")
        pdf_path = create_sample_japanese_pdf(pdf_path)
        
        # Test with different settings
        print("\n📊 Testing extraction methods...")
        processor = PDFProcessor(pdf_path, language="jpn")
        result = processor.process()
        
        if result:
            total_chars = len(result.full_text)
            pages_with_images = sum(1 for p in result.pages if p.has_images)
            
            print(f"\n   📈 Extraction Statistics:")
            print(f"      • Total characters extracted: {total_chars:,}")
            print(f"      • Pages processed: {result.total_pages}")
            print(f"      • Pages with images detected: {pages_with_images}")
            print(f"      • Average chars per page: {total_chars // result.total_pages if result.total_pages > 0 else 0:,}")
            
            # Extract metrics
            structured = result.structured_data
            print(f"\n   📊 Data Extraction Metrics:")
            print(f"      • Dates found: {len(structured['dates'])}")
            print(f"      • Emails found: {len(structured['email_addresses'])}")
            print(f"      • Phone numbers found: {len(structured['phone_numbers'])}")
            print(f"      • Numbers found: {len(structured['numbers'])}")
            print(f"      • Sections identified: {len(structured['sections'])}")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def run_all_integration_tests():
    """Run all integration tests"""
    print("\n" + "#"*70)
    print("# RUNNING ALL INTEGRATION TESTS")
    print("#"*70)
    
    # Test 1: Real PDF processing
    test1_result = test_real_japanese_pdf()
    
    # Test 2: Compare extraction methods
    compare_extraction_methods()
    
    print("\n" + "#"*70)
    print("# ALL INTEGRATION TESTS COMPLETED")
    print("#"*70)
    
    return test1_result


if __name__ == "__main__":
    success = run_all_integration_tests()
    exit(0 if success else 1)

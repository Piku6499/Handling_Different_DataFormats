"""
Example usage of PDF Processor for handling poorly formatted Japanese PDFs
"""

import json
from pdf_processor import process_pdf, PDFProcessor

# Example 1: Simple processing with default parameters
if __name__ == "__main__":
    # Process a PDF file
    pdf_path = "sample_japanese_document.pdf"
    output_json_path = "output.json"
    
    # Process with Japanese OCR
    json_result = process_pdf(
        pdf_path=pdf_path,
        output_json_path=output_json_path,
        language="jpn"  # Japanese language
    )
    
    # Parse and display results
    data = json.loads(json_result)
    
    print("=" * 60)
    print("PDF PROCESSING RESULTS")
    print("=" * 60)
    
    print("\n📄 METADATA:")
    for key, value in data["metadata"].items():
        print(f"  {key}: {value}")
    
    print("\n📊 PROCESSING SUMMARY:")
    for key, value in data["processing_summary"].items():
        print(f"  {key}: {value}")
    
    print("\n🔍 EXTRACTED STRUCTURED DATA:")
    structured = data["structured_data"]
    
    if structured["dates"]:
        print(f"  📅 Dates found: {structured['dates']}")
    
    if structured["email_addresses"]:
        print(f"  📧 Emails found: {structured['email_addresses']}")
    
    if structured["phone_numbers"]:
        print(f"  📞 Phone numbers found: {structured['phone_numbers']}")
    
    if structured["numbers"]:
        print(f"  🔢 Numbers found: {structured['numbers'][:5]}...")  # Show first 5
    
    if structured["sections"]:
        print(f"  📑 Sections identified: {list(structured['sections'].keys())}")
    
    print("\n📝 PAGE-BY-PAGE SUMMARY:")
    for page in data["pages"]:
        print(f"  Page {page['page_number']}: {len(page['text'])} characters, "
              f"Images detected: {page['has_images']}")
    
    print("\n✅ Full output saved to:", output_json_path)
    print("=" * 60)


# Example 2: Advanced usage with custom processing
def advanced_example():
    """
    Advanced example showing how to use PDFProcessor class directly
    for more control over the processing
    """
    pdf_file = "difficult_japanese_document.pdf"
    
    # Initialize processor
    processor = PDFProcessor(pdf_file, language="jpn")
    
    # Process the PDF
    result = processor.process()
    
    if result:
        # Access results
        print(f"Successfully processed {result.total_pages} pages")
        
        # Access individual pages
        for page in result.pages:
            print(f"Page {page.page_number}: {len(page.text)} chars, "
                  f"OCR confidence: {page.confidence}")
        
        # Get structured data
        structured = result.structured_data
        print(f"Found {len(structured['dates'])} dates")
        print(f"Found {len(structured['email_addresses'])} email addresses")
        
        # Convert to JSON with custom path
        json_output = processor.to_json(
            result, 
            output_path="advanced_output.json"
        )
        
        return json_output
    else:
        print("Failed to process PDF")
        return None


# Example 3: Batch processing multiple PDFs
def batch_processing_example():
    """Process multiple PDFs and combine results"""
    import os
    from pathlib import Path
    
    pdf_directory = "./japanese_pdfs"
    output_directory = "./processed_json"
    
    Path(output_directory).mkdir(exist_ok=True)
    
    results = []
    
    # Process all PDFs in directory
    for pdf_file in os.listdir(pdf_directory):
        if pdf_file.endswith('.pdf'):
            pdf_path = os.path.join(pdf_directory, pdf_file)
            output_path = os.path.join(output_directory, f"{pdf_file[:-4]}.json")
            
            print(f"Processing {pdf_file}...")
            
            json_output = process_pdf(pdf_path, output_path, language="jpn")
            results.append(json.loads(json_output))
    
    # Combine all results
    combined = {
        "total_files_processed": len(results),
        "processing_timestamp": results[0]["processing_summary"]["processing_timestamp"] if results else None,
        "files": results
    }
    
    # Save combined results
    with open(os.path.join(output_directory, "combined_results.json"), 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Batch processing complete. Processed {len(results)} files.")

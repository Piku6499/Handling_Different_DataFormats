# PDF Processing Solution for Poorly Formatted Documents

A comprehensive Python solution for processing poorly formatted, scanned, or unevenly spaced PDFs—particularly those in Japanese. This tool automatically handles various document formats, applies intelligent text extraction, and outputs structured JSON data.

## Problem It Solves

Many Japanese organizations deal with PDFs that are:
- **Scanned/Image-based** - No extractable text layer
- **Poorly formatted** - Inconsistent spacing and alignment
- **Unstructured** - Mixed content without clear sections
- **Low quality** - Faded or compressed images requiring OCR enhancement

## Features

✨ **Multi-Modal Text Extraction**
- Direct PDF text extraction for digital documents
- Optical Character Recognition (OCR) for scanned PDFs
- Automatic fallback to OCR when direct extraction fails

🖼️ **Image Preprocessing**
- Denoising with fast non-local means filtering
- Contrast enhancement using CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Automatic binarization for improved text recognition
- Deskewing support

🌐 **Multi-Language Support**
- Japanese (jpn) - optimized for Japanese characters
- English (eng)
- Combined support (jpn+eng)

📊 **Structured Data Extraction**
- Automatic date detection (both Japanese and ISO formats)
- Email and phone number extraction
- Numerical data identification
- Document section segmentation

📝 **Text Normalization**
- Unicode normalization (NFKC for Japanese)
- Whitespace cleaning and standardization
- Control character removal
- Line break preservation

📄 **JSON Output**
- Complete metadata
- Page-by-page text with confidence scores
- Structured extracted data
- Processing timestamps and file information

## Installation

### Prerequisites
- Python 3.8+
- Tesseract OCR engine (required for OCR functionality)

### Install Tesseract

**Windows:**
```bash
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
# Or use chocolatey:
choco install tesseract
```

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr libtesseract-dev
```

**Linux (Fedora/CentOS):**
```bash
sudo yum install tesseract
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from pdf_processor import process_pdf

# Simple one-liner
json_output = process_pdf(
    pdf_path="document.pdf",
    output_json_path="output.json",
    language="jpn"  # Japanese
)
```

### Command Line Usage

```bash
# Process PDF and save JSON
python pdf_processor.py input.pdf output.json jpn

# Process PDF and print JSON to console
python pdf_processor.py input.pdf
```

### Advanced Usage

```python
from pdf_processor import PDFProcessor
import json

# Initialize processor
processor = PDFProcessor("document.pdf", language="jpn")

# Process the document
result = processor.process()

if result:
    # Access structured data
    print(f"Extracted {len(result.pages)} pages")
    print(f"Found dates: {result.structured_data['dates']}")
    print(f"Found emails: {result.structured_data['email_addresses']}")
    
    # Save to JSON
    json_str = processor.to_json(result, "output.json")
    
    # Parse JSON
    data = json.loads(json_str)
```

### Batch Processing

```python
from pdf_processor import process_pdf
import os

pdf_directory = "./pdfs"
output_directory = "./json_outputs"
os.makedirs(output_directory, exist_ok=True)

for pdf_file in os.listdir(pdf_directory):
    if pdf_file.endswith('.pdf'):
        pdf_path = os.path.join(pdf_directory, pdf_file)
        output_path = os.path.join(output_directory, f"{pdf_file[:-4]}.json")
        process_pdf(pdf_path, output_path, language="jpn")
```

## Output Format

The JSON output contains:

```json
{
  "metadata": {
    "file_name": "document.pdf",
    "file_size_bytes": 524288,
    "total_pages": 5,
    "language": "jpn",
    "processing_completed_at": "2026-06-02T08:10:30.123456"
  },
  "processing_summary": {
    "total_pages": 5,
    "processing_timestamp": "2026-06-02T08:10:30.123456",
    "file_path": "/path/to/document.pdf"
  },
  "structured_data": {
    "dates": ["2026年6月2日", "2026-06-01"],
    "numbers": ["1000", "5000", "12345"],
    "email_addresses": ["user@example.com"],
    "phone_numbers": ["090-1234-5678"],
    "sections": {
      "Section Title": "Content here...",
      "Another Section": "More content..."
    }
  },
  "pages": [
    {
      "page_number": 1,
      "has_images": false,
      "confidence": 0.95,
      "text": "Extracted text from page 1..."
    }
  ],
  "full_text": "Complete text from entire document..."
}
```

## How It Works

### Text Extraction Pipeline

1. **Load PDF** - Open file using PyMuPDF
2. **Try Direct Extraction** - Attempt text extraction from PDF
3. **Fallback to OCR** - If text extraction fails/yields minimal content:
   - Convert page to image
   - Preprocess image (denoise, enhance contrast)
   - Apply Tesseract OCR with Japanese language model
4. **Normalize Text** - Clean and standardize extracted text
5. **Extract Structured Data** - Parse dates, emails, phone numbers, sections
6. **Generate JSON** - Format all results as structured JSON

### Key Libraries

| Library | Purpose |
|---------|---------|
| **PyMuPDF** | PDF loading and rendering |
| **Tesseract** | OCR engine for scanned PDFs |
| **Pillow** | Image processing |
| **OpenCV** | Image preprocessing (denoising, contrast) |
| **NumPy** | Numerical operations |

## Performance Tips

- **Batch Processing**: Process multiple PDFs simultaneously using multiprocessing
- **Resolution**: Increase zoom factor in `get_pixmap()` for low-quality PDFs
- **Language**: Use only required languages (e.g., "jpn" instead of "jpn+eng")
- **Memory**: For very large PDFs, process page-by-page instead of loading entire document

## Troubleshooting

### "Tesseract not found" Error
- Ensure Tesseract is installed and in system PATH
- Specify Tesseract path if needed: `pytesseract.pytesseract.pytesseract_cmd = r'/path/to/tesseract'`

### Poor OCR Quality
- Check image preprocessing settings
- Increase `get_pixmap()` zoom factor for better resolution
- Try different Tesseract PSM modes (0-13)

### Out of Memory
- Process PDFs in chunks
- Reduce image resolution (lower zoom factor)
- Use streaming approach for very large files

## Requirements

See `requirements.txt`:
- PyMuPDF 1.23.8
- pytesseract 0.3.10
- Pillow 10.1.0
- opencv-python 4.8.1.78
- numpy 1.24.3

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions welcome! Please submit issues and pull requests.

## Support

For issues, questions, or feature requests, please open a GitHub issue.

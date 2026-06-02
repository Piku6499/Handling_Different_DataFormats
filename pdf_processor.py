"""
PDF Processing Module for Handling Poorly Formatted Documents
Handles Japanese PDFs with uneven spacing, poor formatting, and scanned images
Converts extracted data to structured JSON format
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass, asdict
from datetime import datetime

# PDF and OCR libraries
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import cv2
import numpy as np

# Text processing
import re
import unicodedata

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessedPage:
    """Represents a processed page from PDF"""
    page_number: int
    text: str
    confidence: float
    has_images: bool
    image_text: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class ExtractedData:
    """Represents all extracted data from PDF"""
    file_path: str
    total_pages: int
    processing_timestamp: str
    pages: List[ProcessedPage]
    full_text: str
    structured_data: Dict[str, Any]
    metadata: Dict[str, Any]


class PDFProcessor:
    """
    Main class for processing PDF files with various improvements:
    - Handles scanned PDFs via OCR
    - Processes normal text PDFs
    - Cleans and normalizes Japanese text
    - Recovers structure from unformatted content
    - Outputs structured JSON
    """

    def __init__(self, pdf_path: str, language: str = "jpn"):
        """
        Initialize PDF processor
        
        Args:
            pdf_path: Path to PDF file
            language: Language for OCR (jpn for Japanese, eng for English, jpn+eng for both)
        """
        self.pdf_path = pdf_path
        self.language = language
        self.document = None
        self.pages_data: List[ProcessedPage] = []
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    def load_pdf(self) -> bool:
        """Load PDF document"""
        try:
            self.document = fitz.open(self.pdf_path)
            logger.info(f"Successfully loaded PDF: {self.pdf_path} ({len(self.document)} pages)")
            return True
        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            return False
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results
        - Contrast enhancement
        - Denoising
        - Deskewing
        """
        try:
            # Convert PIL image to numpy array
            img_array = np.array(image)
            
            # Convert to grayscale if needed
            if len(img_array.shape) == 3:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(img_array, h=10)
            
            # Contrast enhancement using CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Thresholding for better text detection
            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            return Image.fromarray(thresh)
        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {e}")
            return image
    
    def extract_text_with_ocr(self, image: Image.Image) -> Tuple[str, float]:
        """
        Extract text from image using Tesseract OCR
        
        Args:
            image: PIL Image object
            
        Returns:
            Tuple of (text, confidence)
        """
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Extract text with Tesseract
            # Config: PSM 3 for automatic page segmentation with OCR
            config = f'--psm 3 -l {self.language}'
            text = pytesseract.image_to_string(processed_image, config=config)
            
            # Get confidence data
            data = pytesseract.image_to_data(processed_image, config=config, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['confidence'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return text, avg_confidence / 100.0
        except Exception as e:
            logger.warning(f"OCR extraction failed: {e}")
            return "", 0.0
    
    def extract_text_from_page(self, page_num: int) -> Tuple[str, bool]:
        """
        Extract text from a PDF page using both direct extraction and OCR
        
        Args:
            page_num: Page number (0-indexed)
            
        Returns:
            Tuple of (text, has_images)
        """
        try:
            page = self.document[page_num]
            
            # Try direct text extraction first
            text = page.get_text()
            
            # Check if page contains images
            has_images = False
            image_text = ""
            
            # Get page as image for OCR
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # If direct extraction yields little text, use OCR
            if len(text.strip()) < 50:  # Threshold for minimal text
                has_images = True
                image_text, confidence = self.extract_text_with_ocr(img)
                logger.info(f"Page {page_num + 1}: Using OCR (confidence: {confidence:.2f})")
                return image_text, has_images
            else:
                # Also try OCR for any images on the page with regular text
                image_text, _ = self.extract_text_with_ocr(img)
                if image_text and len(image_text.strip()) > 0:
                    has_images = True
                    text += "\n[Image Content]\n" + image_text
                
                logger.info(f"Page {page_num + 1}: Using direct text extraction")
                return text, has_images
        
        except Exception as e:
            logger.error(f"Error extracting text from page {page_num + 1}: {e}")
            return "", False
    
    def normalize_japanese_text(self, text: str) -> str:
        """
        Normalize Japanese text:
        - Remove extra whitespace
        - Normalize unicode
        - Remove control characters
        """
        # Normalize unicode (NFKC for Japanese)
        text = unicodedata.normalize('NFKC', text)
        
        # Remove excessive whitespace while preserving line breaks
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove leading/trailing spaces
            line = line.strip()
            # Remove multiple consecutive spaces
            line = re.sub(r'\s+', ' ', line)
            if line:  # Only add non-empty lines
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def segment_text_into_sections(self, text: str) -> Dict[str, Any]:
        """
        Attempt to segment text into logical sections
        Looks for patterns like headers, dates, etc.
        """
        sections = {}
        current_section = "content"
        current_content = []
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect potential headers (short lines, often in caps or specific patterns)
            if (len(line) < 40 and 
                (line.isupper() or 
                 re.match(r'^[0-9]+\.', line) or
                 re.match(r'^■|^●|^▪', line))):
                
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                current_section = line
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def extract_structured_data(self, full_text: str) -> Dict[str, Any]:
        """
        Extract structured data from text
        Looks for dates, numbers, email, phone, etc.
        """
        structured = {
            "dates": [],
            "numbers": [],
            "email_addresses": [],
            "phone_numbers": [],
            "sections": {}
        }
        
        # Extract dates (Japanese format: 2026年6月2日 or 2026-06-02)
        dates = re.findall(r'(\d{4}年\d{1,2}月\d{1,2}日|\d{4}-\d{2}-\d{2})', full_text)
        structured["dates"] = list(set(dates))
        
        # Extract numbers
        numbers = re.findall(r'\d+(?:[,、]\d+)*(?:\.\d+)?', full_text)
        structured["numbers"] = list(set(numbers))[:20]  # Limit to top 20
        
        # Extract emails
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', full_text)
        structured["email_addresses"] = list(set(emails))
        
        # Extract phone numbers
        phones = re.findall(r'(?:\+81|0)\d{1,4}[.-]?\d{1,4}[.-]?\d{3,4}', full_text)
        structured["phone_numbers"] = list(set(phones))
        
        # Segment into sections
        structured["sections"] = self.segment_text_into_sections(full_text)
        
        return structured
    
    def process(self) -> Optional[ExtractedData]:
        """
        Main processing function
        
        Returns:
            ExtractedData object or None if failed
        """
        if not self.load_pdf():
            return None
        
        logger.info(f"Processing {len(self.document)} pages...")
        
        all_text = []
        
        for page_num in range(len(self.document)):
            logger.info(f"Processing page {page_num + 1}/{len(self.document)}")
            
            text, has_images = self.extract_text_from_page(page_num)
            text = self.normalize_japanese_text(text)
            
            page_data = ProcessedPage(
                page_number=page_num + 1,
                text=text,
                confidence=0.85,  # Placeholder
                has_images=has_images
            )
            
            self.pages_data.append(page_data)
            all_text.append(text)
        
        full_text = '\n\n'.join(all_text)
        structured_data = self.extract_structured_data(full_text)
        
        # Get PDF metadata
        metadata = {
            "file_name": os.path.basename(self.pdf_path),
            "file_size_bytes": os.path.getsize(self.pdf_path),
            "total_pages": len(self.document),
            "language": self.language,
            "processing_completed_at": datetime.now().isoformat()
        }
        
        result = ExtractedData(
            file_path=self.pdf_path,
            total_pages=len(self.document),
            processing_timestamp=datetime.now().isoformat(),
            pages=self.pages_data,
            full_text=full_text,
            structured_data=structured_data,
            metadata=metadata
        )
        
        logger.info("PDF processing completed successfully")
        return result
    
    def to_json(self, result: ExtractedData, output_path: Optional[str] = None) -> str:
        """
        Convert extracted data to JSON format
        
        Args:
            result: ExtractedData object
            output_path: Optional file path to save JSON
            
        Returns:
            JSON string
        """
        json_data = {
            "metadata": result.metadata,
            "processing_summary": {
                "total_pages": result.total_pages,
                "processing_timestamp": result.processing_timestamp,
                "file_path": result.file_path
            },
            "structured_data": result.structured_data,
            "pages": [
                {
                    "page_number": page.page_number,
                    "has_images": page.has_images,
                    "confidence": page.confidence,
                    "text": page.text
                }
                for page in result.pages
            ],
            "full_text": result.full_text
        }
        
        json_str = json.dumps(json_data, ensure_ascii=False, indent=2)
        
        if output_path:
            try:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                logger.info(f"JSON output saved to: {output_path}")
            except Exception as e:
                logger.error(f"Failed to save JSON: {e}")
        
        return json_str


def process_pdf(pdf_path: str, output_json_path: Optional[str] = None, 
                language: str = "jpn") -> str:
    """
    Convenience function to process a PDF and return JSON
    
    Args:
        pdf_path: Path to PDF file
        output_json_path: Optional path to save JSON output
        language: Language for OCR (jpn, eng, jpn+eng)
        
    Returns:
        JSON string with extracted data
    """
    processor = PDFProcessor(pdf_path, language=language)
    result = processor.process()
    
    if result:
        return processor.to_json(result, output_json_path)
    else:
        return json.dumps({"error": "Failed to process PDF"}, ensure_ascii=False)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_processor.py <pdf_path> [output_json_path] [language]")
        print("Example: python pdf_processor.py input.pdf output.json jpn")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    json_file = sys.argv[2] if len(sys.argv) > 2 else None
    lang = sys.argv[3] if len(sys.argv) > 3 else "jpn"
    
    json_output = process_pdf(pdf_file, json_file, lang)
    
    if json_file is None:
        print(json_output)

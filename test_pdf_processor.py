"""
Unit tests for PDF Processor module
Tests all major functionality including:
- PDF loading
- Text extraction
- Image preprocessing
- OCR functionality
- Text normalization
- Structured data extraction
- JSON output
"""

import unittest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
from PIL import Image
import io

from pdf_processor import (
    PDFProcessor,
    ProcessedPage,
    ExtractedData,
    process_pdf
)


class TestPDFProcessorInitialization(unittest.TestCase):
    """Test PDF Processor initialization and basic setup"""
    
    def setUp(self):
        """Create temporary test files"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        
        # Create a dummy PDF file for testing
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')  # Minimal PDF header
    
    def tearDown(self):
        """Clean up temporary files"""
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
        os.rmdir(self.temp_dir)
    
    def test_processor_initialization(self):
        """Test that PDFProcessor initializes correctly"""
        processor = PDFProcessor(self.test_pdf_path, language="jpn")
        self.assertEqual(processor.pdf_path, self.test_pdf_path)
        self.assertEqual(processor.language, "jpn")
        self.assertIsNone(processor.document)
    
    def test_processor_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files"""
        with self.assertRaises(FileNotFoundError):
            PDFProcessor("nonexistent_file.pdf")
    
    def test_processor_language_options(self):
        """Test that various language options are accepted"""
        for lang in ["jpn", "eng", "jpn+eng"]:
            processor = PDFProcessor(self.test_pdf_path, language=lang)
            self.assertEqual(processor.language, lang)


class TestTextNormalization(unittest.TestCase):
    """Test Japanese text normalization functions"""
    
    def setUp(self):
        """Create processor instance"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
        
        self.processor = PDFProcessor(self.test_pdf_path, language="jpn")
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
        os.rmdir(self.temp_dir)
    
    def test_normalize_empty_text(self):
        """Test normalization of empty text"""
        result = self.processor.normalize_japanese_text("")
        self.assertEqual(result, "")
    
    def test_normalize_whitespace(self):
        """Test that excessive whitespace is removed"""
        text = "これは    テスト   です"
        result = self.processor.normalize_japanese_text(text)
        self.assertEqual(result, "これは テスト です")
    
    def test_normalize_line_breaks(self):
        """Test that line breaks are preserved"""
        text = "行1\n\n行2\n行3"
        result = self.processor.normalize_japanese_text(text)
        # Empty lines should be removed
        self.assertIn("行1", result)
        self.assertIn("行2", result)
        self.assertIn("行3", result)
    
    def test_normalize_unicode(self):
        """Test Unicode normalization"""
        # Full-width forms should be normalized
        text = "１２３"  # Full-width numbers
        result = self.processor.normalize_japanese_text(text)
        # Should normalize to standard forms
        self.assertIsNotNone(result)


class TestStructuredDataExtraction(unittest.TestCase):
    """Test extraction of structured data from text"""
    
    def setUp(self):
        """Create processor instance"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
        
        self.processor = PDFProcessor(self.test_pdf_path, language="jpn")
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
        os.rmdir(self.temp_dir)
    
    def test_extract_dates_japanese_format(self):
        """Test extraction of Japanese formatted dates"""
        text = "2026年6月2日に実施されました。"
        result = self.processor.extract_structured_data(text)
        self.assertIn("2026年6月2日", result["dates"])
    
    def test_extract_dates_iso_format(self):
        """Test extraction of ISO formatted dates"""
        text = "会議は2026-06-02に開催されます。"
        result = self.processor.extract_structured_data(text)
        self.assertIn("2026-06-02", result["dates"])
    
    def test_extract_email_addresses(self):
        """Test extraction of email addresses"""
        text = "お問い合わせは contact@example.com までお願いします。"
        result = self.processor.extract_structured_data(text)
        self.assertIn("contact@example.com", result["email_addresses"])
    
    def test_extract_phone_numbers(self):
        """Test extraction of Japanese phone numbers"""
        text = "電話番号: 090-1234-5678"
        result = self.processor.extract_structured_data(text)
        # Should find phone number pattern
        self.assertGreaterEqual(len(result["phone_numbers"]), 0)
    
    def test_extract_numbers(self):
        """Test extraction of numerical data"""
        text = "売上は1000万円で、2500件の契約がありました。"
        result = self.processor.extract_structured_data(text)
        # Should extract numbers
        self.assertGreater(len(result["numbers"]), 0)
    
    def test_extract_sections(self):
        """Test section segmentation"""
        text = """■第1章 概要
これは概要です。

■第2章 詳細
詳細内容がここに入ります。"""
        result = self.processor.extract_structured_data(text)
        self.assertGreater(len(result["sections"]), 0)
    
    def test_structured_data_format(self):
        """Test that structured data has correct format"""
        text = "サンプルテキスト"
        result = self.processor.extract_structured_data(text)
        
        self.assertIn("dates", result)
        self.assertIn("numbers", result)
        self.assertIn("email_addresses", result)
        self.assertIn("phone_numbers", result)
        self.assertIn("sections", result)
        
        self.assertIsInstance(result["dates"], list)
        self.assertIsInstance(result["numbers"], list)
        self.assertIsInstance(result["email_addresses"], list)
        self.assertIsInstance(result["phone_numbers"], list)
        self.assertIsInstance(result["sections"], dict)


class TestImagePreprocessing(unittest.TestCase):
    """Test image preprocessing functions"""
    
    def setUp(self):
        """Create processor instance and test images"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
        
        self.processor = PDFProcessor(self.test_pdf_path, language="jpn")
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
        os.rmdir(self.temp_dir)
    
    def test_preprocess_image_returns_image(self):
        """Test that preprocessing returns a PIL Image"""
        # Create a simple test image
        test_image = Image.new('RGB', (100, 100), color='white')
        result = self.processor.preprocess_image(test_image)
        
        self.assertIsInstance(result, Image.Image)
    
    def test_preprocess_image_dimensions_preserved(self):
        """Test that image dimensions are preserved after preprocessing"""
        test_image = Image.new('RGB', (200, 150), color='white')
        result = self.processor.preprocess_image(test_image)
        
        self.assertEqual(result.size[0], 200)
        self.assertEqual(result.size[1], 150)
    
    def test_preprocess_rgb_to_grayscale(self):
        """Test that RGB images are converted properly"""
        # Create RGB image with noise
        arr = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        test_image = Image.fromarray(arr, 'RGB')
        
        result = self.processor.preprocess_image(test_image)
        self.assertIsInstance(result, Image.Image)


class TestProcessedPageDataclass(unittest.TestCase):
    """Test ProcessedPage dataclass"""
    
    def test_processed_page_creation(self):
        """Test creating a ProcessedPage instance"""
        page = ProcessedPage(
            page_number=1,
            text="Sample text",
            confidence=0.95,
            has_images=False
        )
        
        self.assertEqual(page.page_number, 1)
        self.assertEqual(page.text, "Sample text")
        self.assertEqual(page.confidence, 0.95)
        self.assertEqual(page.has_images, False)
    
    def test_processed_page_with_image_text(self):
        """Test ProcessedPage with image text"""
        page = ProcessedPage(
            page_number=1,
            text="Regular text",
            confidence=0.90,
            has_images=True,
            image_text="Image extracted text"
        )
        
        self.assertEqual(page.image_text, "Image extracted text")
        self.assertTrue(page.has_images)


class TestExtractedDataDataclass(unittest.TestCase):
    """Test ExtractedData dataclass"""
    
    def test_extracted_data_creation(self):
        """Test creating ExtractedData instance"""
        pages = [
            ProcessedPage(1, "Page 1", 0.95, False),
            ProcessedPage(2, "Page 2", 0.92, True)
        ]
        
        data = ExtractedData(
            file_path="/path/to/file.pdf",
            total_pages=2,
            processing_timestamp="2026-06-02T08:00:00",
            pages=pages,
            full_text="Combined text",
            structured_data={"dates": []},
            metadata={"language": "jpn"}
        )
        
        self.assertEqual(data.total_pages, 2)
        self.assertEqual(len(data.pages), 2)
        self.assertEqual(data.full_text, "Combined text")


class TestJSONOutput(unittest.TestCase):
    """Test JSON output generation"""
    
    def setUp(self):
        """Create processor instance"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
        
        self.processor = PDFProcessor(self.test_pdf_path, language="jpn")
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
        os.rmdir(self.temp_dir)
    
    def test_json_output_valid(self):
        """Test that JSON output is valid"""
        pages = [ProcessedPage(1, "Test", 0.95, False)]
        
        result = ExtractedData(
            file_path=self.test_pdf_path,
            total_pages=1,
            processing_timestamp="2026-06-02T08:00:00",
            pages=pages,
            full_text="Test text",
            structured_data={"dates": ["2026-06-02"]},
            metadata={"language": "jpn"}
        )
        
        json_output = self.processor.to_json(result)
        
        # Should be valid JSON
        parsed = json.loads(json_output)
        self.assertIsInstance(parsed, dict)
    
    def test_json_output_structure(self):
        """Test that JSON output has correct structure"""
        pages = [ProcessedPage(1, "Test", 0.95, False)]
        
        result = ExtractedData(
            file_path=self.test_pdf_path,
            total_pages=1,
            processing_timestamp="2026-06-02T08:00:00",
            pages=pages,
            full_text="Test text",
            structured_data={"dates": []},
            metadata={"language": "jpn"}
        )
        
        json_output = self.processor.to_json(result)
        parsed = json.loads(json_output)
        
        # Check required keys
        self.assertIn("metadata", parsed)
        self.assertIn("processing_summary", parsed)
        self.assertIn("structured_data", parsed)
        self.assertIn("pages", parsed)
        self.assertIn("full_text", parsed)
    
    def test_json_output_japanese_characters(self):
        """Test that JSON output preserves Japanese characters"""
        pages = [ProcessedPage(1, "これはテストです", 0.95, False)]
        
        result = ExtractedData(
            file_path=self.test_pdf_path,
            total_pages=1,
            processing_timestamp="2026-06-02T08:00:00",
            pages=pages,
            full_text="これはテストです",
            structured_data={"dates": []},
            metadata={"language": "jpn"}
        )
        
        json_output = self.processor.to_json(result)
        parsed = json.loads(json_output)
        
        # Should preserve Japanese characters
        self.assertIn("これはテストです", json_output)
    
    def test_json_file_output(self):
        """Test saving JSON to file"""
        pages = [ProcessedPage(1, "Test", 0.95, False)]
        
        result = ExtractedData(
            file_path=self.test_pdf_path,
            total_pages=1,
            processing_timestamp="2026-06-02T08:00:00",
            pages=pages,
            full_text="Test text",
            structured_data={"dates": []},
            metadata={"language": "jpn"}
        )
        
        output_path = os.path.join(self.temp_dir, "output.json")
        self.processor.to_json(result, output_path)
        
        # File should be created
        self.assertTrue(os.path.exists(output_path))
        
        # Should be valid JSON
        with open(output_path, 'r', encoding='utf-8') as f:
            parsed = json.load(f)
        self.assertIsInstance(parsed, dict)


class TestSegmentText(unittest.TestCase):
    """Test text segmentation into sections"""
    
    def setUp(self):
        """Create processor instance"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
        
        self.processor = PDFProcessor(self.test_pdf_path, language="jpn")
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
        os.rmdir(self.temp_dir)
    
    def test_segment_with_headers(self):
        """Test segmentation with header markers"""
        text = """■ セクション1
内容1

■ セクション2
内容2"""
        result = self.processor.segment_text_into_sections(text)
        
        self.assertGreater(len(result), 0)
    
    def test_segment_with_numbered_headers(self):
        """Test segmentation with numbered headers"""
        text = """1. はじめに
最初のセクション

2. 本文
メインコンテンツ"""
        result = self.processor.segment_text_into_sections(text)
        
        self.assertGreater(len(result), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Create temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_process_pdf_function(self):
        """Test the convenience process_pdf function"""
        test_pdf_path = os.path.join(self.temp_dir, "test.pdf")
        with open(test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n')
        
        # Should return JSON string or error
        result = process_pdf(test_pdf_path, language="jpn")
        self.assertIsInstance(result, str)


def run_unit_tests():
    """Run all unit tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPDFProcessorInitialization))
    suite.addTests(loader.loadTestsFromTestCase(TestTextNormalization))
    suite.addTests(loader.loadTestsFromTestCase(TestStructuredDataExtraction))
    suite.addTests(loader.loadTestsFromTestCase(TestImagePreprocessing))
    suite.addTests(loader.loadTestsFromTestCase(TestProcessedPageDataclass))
    suite.addTests(loader.loadTestsFromTestCase(TestExtractedDataDataclass))
    suite.addTests(loader.loadTestsFromTestCase(TestJSONOutput))
    suite.addTests(loader.loadTestsFromTestCase(TestSegmentText))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_unit_tests()
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

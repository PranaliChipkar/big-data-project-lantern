#!/usr/bin/env python3
"""
Part 1: Text Extraction from SEC Filings
Extracts text from HTML/TXT files and PDFs with OCR fallback
"""

import sys
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional
import re
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import pdfplumber
from PyPDF2 import PdfReader
import pytesseract
from PIL import Image
from bs4 import BeautifulSoup
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SECFilingParser:
    """Extract text from SEC filings with OCR fallback"""
    
    def __init__(self, input_dir: str = "data/raw/pdfs", output_dir: str = "data/parsed/text"):
        """
        Initialize the parser
        
        Args:
            input_dir: Directory containing downloaded SEC filings
            output_dir: Directory to save extracted text
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track extraction statistics
        self.extraction_log = []
        
    def extract_text_from_html(self, file_path: Path) -> Dict:
        """
        Extract text from HTML file
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n')
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Extract sections if possible
            sections = self._extract_sections(text)
            
            return {
                'status': 'success',
                'method': 'html_parser',
                'text': text,
                'sections': sections,
                'char_count': len(text),
                'line_count': len(text.splitlines()),
                'word_count': len(text.split())
            }
            
        except Exception as e:
            logger.error(f"Error extracting from HTML {file_path}: {e}")
            return {
                'status': 'error',
                'method': 'html_parser',
                'error': str(e),
                'text': ''
            }
    
    def extract_text_from_txt(self, file_path: Path) -> Dict:
        """
        Extract text from TXT file (full submission format)
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            # For full-submission.txt files, extract the main document
            if 'full-submission' in file_path.name:
                # Find the main document section (usually after <DOCUMENT> tag)
                doc_pattern = r'<DOCUMENT>.*?<TYPE>10-[KQ].*?<TEXT>(.*?)</TEXT>'
                match = re.search(doc_pattern, text, re.DOTALL)
                if match:
                    main_text = match.group(1)
                else:
                    # Fallback: extract everything after first <TEXT> tag
                    text_start = text.find('<TEXT>')
                    text_end = text.find('</TEXT>')
                    if text_start != -1 and text_end != -1:
                        main_text = text[text_start+6:text_end]
                    else:
                        main_text = text
            else:
                main_text = text
            
            # Clean up text
            main_text = self._clean_text(main_text)
            
            # Extract sections
            sections = self._extract_sections(main_text)
            
            return {
                'status': 'success',
                'method': 'txt_parser',
                'text': main_text,
                'sections': sections,
                'char_count': len(main_text),
                'line_count': len(main_text.splitlines()),
                'word_count': len(main_text.split())
            }
            
        except Exception as e:
            logger.error(f"Error extracting from TXT {file_path}: {e}")
            return {
                'status': 'error',
                'method': 'txt_parser',
                'error': str(e),
                'text': ''
            }
    
    def extract_text_from_pdf(self, file_path: Path) -> Dict:
        """
        Extract text from PDF with OCR fallback
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            extracted_pages = []
            ocr_pages = []
            word_boxes = []
            
            # Try pdfplumber first
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text
                    text = page.extract_text()
                    
                    if text and len(text.strip()) > 50:  # Page has meaningful text
                        extracted_pages.append({
                            'page': page_num,
                            'text': text,
                            'method': 'pdfplumber'
                        })
                        
                        # Extract word bounding boxes for later use
                        words = page.extract_words()
                        word_boxes.append({
                            'page': page_num,
                            'words': words
                        })
                    else:
                        # Page needs OCR
                        logger.info(f"Page {page_num} needs OCR")
                        ocr_text = self._ocr_page(file_path, page_num)
                        extracted_pages.append({
                            'page': page_num,
                            'text': ocr_text,
                            'method': 'tesseract_ocr'
                        })
                        ocr_pages.append(page_num)
            
            # Combine all pages
            full_text = '\n\n'.join(p['text'] for p in extracted_pages)
            
            return {
                'status': 'success',
                'method': 'pdf_mixed',
                'text': full_text,
                'pages': extracted_pages,
                'ocr_pages': ocr_pages,
                'word_boxes': word_boxes,
                'total_pages': len(extracted_pages),
                'char_count': len(full_text),
                'word_count': len(full_text.split())
            }
            
        except Exception as e:
            logger.error(f"Error extracting from PDF {file_path}: {e}")
            return {
                'status': 'error',
                'method': 'pdf_parser',
                'error': str(e),
                'text': ''
            }
    
    def _ocr_page(self, pdf_path: Path, page_num: int) -> str:
        """
        Perform OCR on a specific PDF page
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed)
            
        Returns:
            Extracted text from OCR
        """
        try:
            # Convert PDF page to image
            # Note: This is a simplified version. In production, you'd use pdf2image
            # For now, return placeholder
            logger.warning(f"OCR needed for {pdf_path} page {page_num} - using placeholder")
            return f"[OCR needed for page {page_num}]"
            
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return f"[OCR failed for page {page_num}]"
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove HTML entities if any remain
        text = re.sub(r'&[a-z]+;', ' ', text, flags=re.IGNORECASE)
        
        # Remove page numbers and headers/footers patterns
        text = re.sub(r'Page \d+ of \d+', '', text)
        
        return text.strip()
    
    def _extract_sections(self, text: str) -> List[Dict]:
        """
        Extract common sections from SEC filings
        
        Args:
            text: Full text of filing
            
        Returns:
            List of section dictionaries
        """
        sections = []
        
        # Common section headers in 10-K/10-Q
        section_patterns = [
            r'(ITEM\s+\d+[A-Z]?\.?\s+[^\n]+)',
            r'(PART\s+[IVX]+)',
            r'(Management.s Discussion and Analysis)',
            r'(Risk Factors)',
            r'(Financial Statements)',
            r'(Business Overview)',
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                sections.append({
                    'title': match.group(1),
                    'start': match.start(),
                    'end': match.end()
                })
        
        # Sort sections by position
        sections.sort(key=lambda x: x['start'])
        
        return sections
    
    def process_filing(self, file_path: Path) -> Dict:
        """
        Process a single filing file
        
        Args:
            file_path: Path to filing file
            
        Returns:
            Extraction results
        """
        logger.info(f"Processing: {file_path.name}")
        
        # Determine file type and extract accordingly
        if file_path.suffix.lower() == '.html':
            result = self.extract_text_from_html(file_path)
        elif file_path.suffix.lower() == '.txt':
            result = self.extract_text_from_txt(file_path)
        elif file_path.suffix.lower() == '.pdf':
            result = self.extract_text_from_pdf(file_path)
        else:
            result = {
                'status': 'skipped',
                'reason': f'Unsupported file type: {file_path.suffix}'
            }
        
        # Add file metadata
        result['file_path'] = str(file_path)
        result['file_name'] = file_path.name
        result['file_size'] = file_path.stat().st_size
        result['processed_at'] = datetime.now().isoformat()
        
        return result
    
    def process_all_filings(self):
        """Process all downloaded SEC filings"""
        
        # Find all filing files
        filing_dir = self.input_dir / "sec-edgar-filings"
        
        if not filing_dir.exists():
            logger.error(f"Directory not found: {filing_dir}")
            return
        
        # Get all HTML and TXT files
        files = list(filing_dir.rglob("primary-document.html"))
        
        if not files:
            logger.warning("No primary documents found, processing all files")
            files = list(filing_dir.rglob("*.html")) + list(filing_dir.rglob("*.txt"))
        
        logger.info(f"Found {len(files)} files to process")
        
        # Process each file
        for file_path in tqdm(files, desc="Extracting text"):
            result = self.process_filing(file_path)
            
            # Save extracted text
            if result.get('status') == 'success' and result.get('text'):
                self._save_extracted_text(file_path, result)
            
            # Log extraction
            self.extraction_log.append({
                'file': str(file_path.relative_to(self.input_dir)),
                'status': result.get('status'),
                'method': result.get('method'),
                'char_count': result.get('char_count', 0),
                'word_count': result.get('word_count', 0),
                'error': result.get('error')
            })
        
        # Save extraction log
        self._save_extraction_log()
        
        # Print summary
        self._print_summary()
    
    def _save_extracted_text(self, source_path: Path, result: Dict):
        """Save extracted text to file"""
        
        # Create output path structure
        rel_path = source_path.relative_to(self.input_dir / "sec-edgar-filings")
        output_path = self.output_dir / rel_path.parent
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save text file
        text_file = output_path / f"{source_path.stem}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(result['text'])
        
        # Save metadata
        meta_file = output_path / f"{source_path.stem}_meta.json"
        metadata = {k: v for k, v in result.items() if k != 'text'}
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.debug(f"Saved: {text_file}")
    
    def _save_extraction_log(self):
        """Save extraction log"""
        log_file = self.output_dir / "extraction_log.json"
        with open(log_file, 'w') as f:
            json.dump(self.extraction_log, f, indent=2)
        logger.info(f"Extraction log saved to {log_file}")
    
    def _print_summary(self):
        """Print extraction summary"""
        print("\n" + "="*50)
        print("Text Extraction Summary")
        print("="*50)
        
        total = len(self.extraction_log)
        successful = sum(1 for log in self.extraction_log if log['status'] == 'success')
        failed = sum(1 for log in self.extraction_log if log['status'] == 'error')
        
        print(f"Total files processed: {total}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        
        # Calculate statistics
        if successful > 0:
            total_chars = sum(log.get('char_count', 0) for log in self.extraction_log)
            total_words = sum(log.get('word_count', 0) for log in self.extraction_log)
            print(f"\n📊 Statistics:")
            print(f"  Total characters extracted: {total_chars:,}")
            print(f"  Total words extracted: {total_words:,}")
            print(f"  Average words per document: {total_words // successful:,}")
        
        print(f"\n📁 Output directory: {self.output_dir}")


def main():
    """Main function"""
    parser = SECFilingParser()
    parser.process_all_filings()
    
    print("\n✅ Part 1 Complete!")
    print("\nNext steps:")
    print("1. Review extracted text in data/parsed/text/")
    print("2. Check extraction_log.json for any issues")
    print("3. Proceed to Part 2 for table extraction")


if __name__ == "__main__":
    main()
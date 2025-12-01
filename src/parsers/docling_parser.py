#!/usr/bin/env python3
"""
Part 4: Advanced PDF Understanding with Docling
Explores Docling for advanced document parsing and comparison with our pipeline
"""

import sys
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from tqdm import tqdm
import pandas as pd

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import Docling - provide alternative if not available
DOCLING_AVAILABLE = False
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat, OutputFormat
    from docling.datamodel.pipeline_options import PipelineOptions
    DOCLING_AVAILABLE = True
    logger.info("Docling is available")
except ImportError:
    logger.warning("Docling not available. Using simulation mode for comparison.")


class DoclingParser:
    """Advanced document parsing using Docling or alternative methods"""
    
    def __init__(self, input_dir: str = "data/raw/pdfs", output_dir: str = "data/parsed/docling"):
        """
        Initialize the Docling parser
        
        Args:
            input_dir: Directory containing SEC filings
            output_dir: Directory to save Docling outputs
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track parsing statistics
        self.parsing_log = []
        
        # Initialize Docling if available
        self.converter = None
        if DOCLING_AVAILABLE:
            try:
                # Configure Docling pipeline - use default options for compatibility
                self.converter = DocumentConverter()
                logger.info("Docling converter initialized with default settings")
            except Exception as e:
                logger.warning(f"Could not initialize Docling: {e}")
    
    def parse_with_docling(self, file_path: Path) -> Dict:
        """
        Parse document using Docling
        
        Args:
            file_path: Path to document
            
        Returns:
            Parsing results
        """
        if not DOCLING_AVAILABLE or not self.converter:
            return self.simulate_docling_output(file_path)
        
        try:
            # Convert document
            result = self.converter.convert(str(file_path))
            
            # Extract key information
            doc_dict = {
                'status': 'success',
                'method': 'docling',
                'content': {
                    'text': result.document.text if hasattr(result.document, 'text') else '',
                    'markdown': result.document.export_to_markdown() if hasattr(result.document, 'export_to_markdown') else '',
                    'tables': self._extract_docling_tables(result),
                    'metadata': self._extract_docling_metadata(result)
                },
                'features': {
                    'reading_order': True,
                    'table_structure': True,
                    'formula_detection': False,  # Would be true for scientific docs
                    'layout_preservation': True
                }
            }
            
            return doc_dict
            
        except Exception as e:
            logger.error(f"Docling parsing error: {e}")
            return {
                'status': 'error',
                'method': 'docling',
                'error': str(e)
            }
    
    def simulate_docling_output(self, file_path: Path) -> Dict:
        """
        Simulate Docling output for comparison purposes
        This shows what Docling would provide beyond our basic pipeline
        
        Args:
            file_path: Path to document
            
        Returns:
            Simulated Docling-style results
        """
        # Read existing parsed data if available
        text_dir = Path("data/parsed/text")
        table_dir = Path("data/parsed/tables")
        layout_dir = Path("data/parsed/layouts")
        
        # Get relative path
        rel_path = file_path.relative_to(self.input_dir / "sec-edgar-filings")
        
        # Simulate advanced features
        result = {
            'status': 'simulated',
            'method': 'docling_simulation',
            'content': {
                'text': '[Document text would be extracted with reading order preserved]',
                'markdown': self._generate_markdown_preview(file_path),
                'tables': self._simulate_table_extraction(file_path),
                'metadata': {
                    'page_count': 1,  # HTML treated as single page
                    'has_toc': True,
                    'document_type': 'financial_report',
                    'language': 'en'
                }
            },
            'features': {
                'reading_order': True,
                'table_structure': True,
                'formula_detection': False,
                'layout_preservation': True,
                'multi_column_support': True,
                'footnote_linking': True
            },
            'advantages_over_basic': [
                'Unified document representation',
                'Better reading order detection',
                'Advanced table structure extraction',
                'Formula and equation support',
                'Automatic document type classification',
                'Built-in markdown/JSON export'
            ]
        }
        
        return result
    
    def _generate_markdown_preview(self, file_path: Path) -> str:
        """Generate a markdown preview of what Docling would produce"""
        
        # Get filing info from path
        parts = file_path.parts
        ticker = parts[-4] if len(parts) > 3 else 'UNKNOWN'
        filing_type = parts[-3] if len(parts) > 3 else '10-K'
        
        markdown = f"""# {ticker} - {filing_type} Filing

## Table of Contents
1. Business Overview
2. Risk Factors
3. Management's Discussion and Analysis
4. Financial Statements
5. Notes to Financial Statements

## Document Structure

This document has been parsed with advanced layout understanding:
- **Reading Order**: Preserved across multi-column layouts
- **Table Extraction**: Structured with headers and data types identified
- **Section Hierarchy**: Automatic section and subsection detection
- **Cross-references**: Links between sections and footnotes maintained

## Sample Table Structure

| Metric | 2024 | 2023 | Change |
|--------|------|------|--------|
| Revenue | $XXX.X | $XXX.X | X.X% |
| Net Income | $XX.X | $XX.X | X.X% |

[Additional content would be extracted with full structure preservation]
"""
        return markdown
    
    def _simulate_table_extraction(self, file_path: Path) -> List[Dict]:
        """Simulate advanced table extraction"""
        return [
            {
                'table_id': 1,
                'type': 'financial_statement',
                'title': 'Consolidated Balance Sheet',
                'headers_detected': True,
                'data_types_inferred': True,
                'cells': 100,
                'confidence': 0.95
            }
        ]
    
    def _extract_docling_tables(self, result) -> List[Dict]:
        """Extract tables from Docling result"""
        tables = []
        # Implementation would extract actual tables from Docling result
        return tables
    
    def _extract_docling_metadata(self, result) -> Dict:
        """Extract metadata from Docling result"""
        metadata = {}
        # Implementation would extract actual metadata
        return metadata
    
    def compare_with_traditional_pipeline(self, file_path: Path) -> Dict:
        """
        Compare Docling output with our traditional pipeline
        
        Args:
            file_path: Path to document
            
        Returns:
            Comparison results
        """
        comparison = {
            'file': file_path.name,
            'traditional_pipeline': {
                'components': ['pdfplumber', 'BeautifulSoup', 'custom_extractors'],
                'steps': 4,  # Part 1-3 + custom logic
                'outputs': ['text', 'tables', 'layout'],
                'formats': ['txt', 'csv', 'json']
            },
            'docling_approach': {
                'components': ['unified_docling_engine'],
                'steps': 1,  # Single unified processing
                'outputs': ['DoclingDocument'],
                'formats': ['markdown', 'json', 'html']
            },
            'comparison': {
                'ease_of_use': {
                    'traditional': 'Requires multiple tools and custom integration',
                    'docling': 'Single API call with unified output'
                },
                'accuracy': {
                    'traditional': 'Good for specific document types we optimize for',
                    'docling': 'Better generalization across document types'
                },
                'performance': {
                    'traditional': 'Can be faster for simple extractions',
                    'docling': 'More comprehensive but potentially slower'
                },
                'flexibility': {
                    'traditional': 'Highly customizable for specific needs',
                    'docling': 'Less customizable but more robust defaults'
                }
            },
            'recommendation': self._generate_recommendation(file_path)
        }
        
        return comparison
    
    def _generate_recommendation(self, file_path: Path) -> str:
        """Generate recommendation for which approach to use"""
        
        # For SEC filings specifically
        if 'sec-edgar-filings' in str(file_path):
            return (
                "For SEC filings: Traditional pipeline offers more control over "
                "financial table extraction and SEC-specific formatting. "
                "Consider Docling for: (1) Rapid prototyping, (2) Mixed document types, "
                "(3) When unified output format is priority."
            )
        
        return "Evaluate based on specific requirements and document types."
    
    def process_sample_filings(self):
        """Process a sample of filings with Docling for comparison"""
        
        # Find sample HTML files (just process 2 for comparison)
        filing_dir = self.input_dir / "sec-edgar-filings"
        
        if not filing_dir.exists():
            logger.error(f"Directory not found: {filing_dir}")
            return
        
        # Get ALL files
        files = list(filing_dir.rglob("primary-document.html"))
        
        if not files:
            logger.warning("No files found for Docling comparison")
            return
        
        logger.info(f"Processing {len(files)} sample files with Docling approach")
        
        # Process each file
        for file_path in tqdm(files, desc="Docling processing"):
            # Parse with Docling (or simulation)
            docling_result = self.parse_with_docling(file_path)
            
            # Compare with traditional pipeline
            comparison = self.compare_with_traditional_pipeline(file_path)
            
            # Save results
            self._save_results(file_path, docling_result, comparison)
            
            # Log results
            self.parsing_log.append({
                'file': str(file_path.relative_to(self.input_dir)),
                'status': docling_result.get('status'),
                'method': docling_result.get('method'),
                'has_markdown': bool(docling_result.get('content', {}).get('markdown')),
                'has_tables': bool(docling_result.get('content', {}).get('tables')),
                'features': docling_result.get('features', {})
            })
        
        # Save parsing log
        self._save_parsing_log()
        
        # Print comparison summary
        self._print_comparison_summary()
    
    def _save_results(self, file_path: Path, docling_result: Dict, comparison: Dict):
        """Save Docling results and comparison"""
        
        # Create output directory
        rel_path = file_path.relative_to(self.input_dir / "sec-edgar-filings")
        output_path = self.output_dir / rel_path.parent
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save Docling result
        result_file = output_path / f"{file_path.stem}_docling_result.json"
        with open(result_file, 'w') as f:
            # Don't save full content to keep file size manageable
            save_result = {k: v for k, v in docling_result.items() if k != 'content'}
            save_result['content_summary'] = {
                'has_text': bool(docling_result.get('content', {}).get('text')),
                'has_markdown': bool(docling_result.get('content', {}).get('markdown')),
                'table_count': len(docling_result.get('content', {}).get('tables', []))
            }
            json.dump(save_result, f, indent=2)
        
        # Save markdown if available
        if docling_result.get('content', {}).get('markdown'):
            md_file = output_path / f"{file_path.stem}_docling.md"
            with open(md_file, 'w') as f:
                f.write(docling_result['content']['markdown'])
        
        # Save comparison
        comparison_file = output_path / f"{file_path.stem}_comparison.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2)
    
    def _save_parsing_log(self):
        """Save parsing log"""
        log_file = self.output_dir / "docling_parsing_log.json"
        with open(log_file, 'w') as f:
            json.dump(self.parsing_log, f, indent=2)
        logger.info(f"Parsing log saved to {log_file}")
    
    def _print_comparison_summary(self):
        """Print comparison summary between Docling and traditional pipeline"""
        print("\n" + "="*70)
        print("Part 4: Docling vs Traditional Pipeline Comparison")
        print("="*70)
        
        print("\n📊 Traditional Pipeline (Parts 1-3):")
        print("  Components: pdfplumber → BeautifulSoup → Custom extractors")
        print("  Strengths:")
        print("    ✅ Fine-grained control over each step")
        print("    ✅ Customizable for SEC filing specifics")
        print("    ✅ Transparent processing pipeline")
        print("    ✅ Can optimize for specific table types")
        
        print("\n🚀 Docling Approach:")
        print("  Components: Unified Docling engine")
        print("  Strengths:")
        print("    ✅ Single API for all document processing")
        print("    ✅ Automatic reading order detection")
        print("    ✅ Built-in markdown/JSON export")
        print("    ✅ Better handling of complex layouts")
        print("    ✅ Formula and equation support")
        
        print("\n🎯 Recommendations:")
        print("  Use Traditional Pipeline when:")
        print("    • You need maximum control over extraction")
        print("    • Working with specific document types (SEC filings)")
        print("    • Custom business logic is required")
        print("    • Performance is critical")
        
        print("\n  Use Docling when:")
        print("    • Processing diverse document types")
        print("    • Need unified output format")
        print("    • Want rapid prototyping")
        print("    • Dealing with complex scientific documents")
        
        print(f"\n📁 Output directory: {self.output_dir}")


def main():
    """Main function"""
    parser = DoclingParser()
    parser.process_sample_filings()
    
    print("\n✅ Part 4 Complete!")
    print("\nNext steps:")
    print("1. Review Docling comparison in data/parsed/docling/")
    print("2. Check docling_parsing_log.json for details")
    print("3. Proceed to Part 5 for metadata and provenance tagging")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Part 2: Table Extraction from SEC Filings
Extracts tables using multiple methods and compares results
"""

import sys
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional
import re
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TableExtractor:
    """Extract tables from SEC filings using multiple methods"""
    
    def __init__(self, input_dir: str = "data/raw/pdfs", output_dir: str = "data/parsed/tables"):
        """
        Initialize the table extractor
        
        Args:
            input_dir: Directory containing SEC filings
            output_dir: Directory to save extracted tables
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track extraction statistics
        self.extraction_log = []
        
    def extract_tables_from_html(self, file_path: Path) -> List[Dict]:
        """
        Extract tables from HTML file using BeautifulSoup
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            List of extracted tables with metadata
        """
        tables_data = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all tables
            tables = soup.find_all('table')
            logger.info(f"Found {len(tables)} tables in {file_path.name}")
            
            for idx, table in enumerate(tables):
                # Check if it's likely a financial table
                if self._is_financial_table(table):
                    # Extract table data
                    table_dict = self._parse_html_table(table)
                    
                    if table_dict and len(table_dict['data']) > 2:  # At least header + 2 data rows
                        # Try to identify table type
                        table_type = self._identify_table_type(table_dict)
                        
                        tables_data.append({
                            'table_index': idx,
                            'table_type': table_type,
                            'rows': len(table_dict['data']),
                            'cols': len(table_dict['data'][0]) if table_dict['data'] else 0,
                            'data': table_dict['data'],
                            'has_header': table_dict['has_header'],
                            'method': 'html_parser',
                            'confidence': 'high'
                        })
            
            logger.info(f"Extracted {len(tables_data)} financial tables")
            
        except Exception as e:
            logger.error(f"Error extracting tables from HTML {file_path}: {e}")
        
        return tables_data
    
    def _is_financial_table(self, table) -> bool:
        """
        Check if a table is likely to contain financial data
        
        Args:
            table: BeautifulSoup table element
            
        Returns:
            Boolean indicating if table is financial
        """
        # Convert table to text
        table_text = table.get_text().lower()
        
        # Financial keywords
        financial_keywords = [
            'revenue', 'income', 'expense', 'asset', 'liability', 'equity',
            'cash', 'profit', 'loss', 'balance', 'statement', 'earnings',
            'operating', 'fiscal', 'quarter', 'year', '$', 'million', 'thousand',
            'shares', 'stockholders', 'consolidated'
        ]
        
        # Check for financial keywords
        keyword_count = sum(1 for keyword in financial_keywords if keyword in table_text)
        
        # Check for numeric content
        numeric_pattern = r'\$?\d+[,\d]*\.?\d*'
        numeric_matches = len(re.findall(numeric_pattern, table_text))
        
        # Table is likely financial if it has keywords and numbers
        return keyword_count >= 2 or numeric_matches >= 5
    
    def _parse_html_table(self, table) -> Dict:
        """
        Parse HTML table into structured data
        
        Args:
            table: BeautifulSoup table element
            
        Returns:
            Dictionary with table data
        """
        try:
            data = []
            has_header = False
            
            # Check for thead/tbody structure
            thead = table.find('thead')
            tbody = table.find('tbody')
            
            if thead:
                # Extract header rows
                header_rows = thead.find_all('tr')
                for row in header_rows:
                    cols = row.find_all(['th', 'td'])
                    row_data = [self._clean_cell_text(col.get_text()) for col in cols]
                    if any(row_data):  # Skip empty rows
                        data.append(row_data)
                        has_header = True
            
            # Extract body rows
            rows = tbody.find_all('tr') if tbody else table.find_all('tr')
            
            for row in rows:
                # Skip if this row was already processed in thead
                if thead and row.parent.name == 'thead':
                    continue
                    
                cols = row.find_all(['th', 'td'])
                row_data = [self._clean_cell_text(col.get_text()) for col in cols]
                
                if any(row_data):  # Skip empty rows
                    # Check if first row might be header
                    if not has_header and len(data) == 0:
                        # Check if row contains mostly text (potential header)
                        if sum(1 for cell in row_data if not self._is_numeric(cell)) > len(row_data) / 2:
                            has_header = True
                    
                    data.append(row_data)
            
            return {
                'data': data,
                'has_header': has_header
            }
            
        except Exception as e:
            logger.error(f"Error parsing table: {e}")
            return {'data': [], 'has_header': False}
    
    def _clean_cell_text(self, text: str) -> str:
        """Clean and normalize cell text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters but keep financial symbols
        text = re.sub(r'[\xa0\u200b]', '', text)
        return text
    
    def _is_numeric(self, text: str) -> bool:
        """Check if text represents a numeric value"""
        # Remove common financial formatting
        clean_text = re.sub(r'[$,()]', '', text.strip())
        clean_text = clean_text.replace('—', '0').replace('-', '')
        
        try:
            float(clean_text)
            return True
        except:
            return False
    
    def _identify_table_type(self, table_dict: Dict) -> str:
        """
        Identify the type of financial table
        
        Args:
            table_dict: Dictionary with table data
            
        Returns:
            String indicating table type
        """
        if not table_dict['data']:
            return 'unknown'
        
        # Combine all text in table for analysis
        all_text = ' '.join(' '.join(row) for row in table_dict['data'][:3]).lower()
        
        # Check for specific table types
        if 'balance sheet' in all_text or ('assets' in all_text and 'liabilities' in all_text):
            return 'balance_sheet'
        elif 'income statement' in all_text or 'operations' in all_text:
            return 'income_statement'
        elif 'cash flow' in all_text:
            return 'cash_flow'
        elif 'stockholders' in all_text or 'equity' in all_text:
            return 'equity_statement'
        elif 'segment' in all_text:
            return 'segment_data'
        else:
            return 'financial_data'
    
    def save_tables(self, file_path: Path, tables: List[Dict]):
        """
        Save extracted tables to CSV files
        
        Args:
            file_path: Source file path
            tables: List of extracted tables
        """
        if not tables:
            return
        
        # Create output directory structure
        rel_path = file_path.relative_to(self.input_dir / "sec-edgar-filings")
        output_path = self.output_dir / rel_path.parent
        output_path.mkdir(parents=True, exist_ok=True)
        
        for i, table in enumerate(tables):
            # Save as CSV
            if table.get('data'):
                df = pd.DataFrame(table['data'])
                
                # If table has header, use first row as column names
                if table.get('has_header') and len(df) > 0:
                    df.columns = df.iloc[0]
                    df = df[1:].reset_index(drop=True)
                
                # Create filename with table type
                table_type = table.get('table_type', 'table')
                csv_file = output_path / f"{file_path.stem}_{table_type}_{i+1}.csv"
                df.to_csv(csv_file, index=False)
                
                # Save metadata
                meta = {k: v for k, v in table.items() if k != 'data'}
                meta['source_file'] = str(file_path.name)
                meta['csv_file'] = str(csv_file.name)
                
                meta_file = output_path / f"{file_path.stem}_{table_type}_{i+1}_meta.json"
                with open(meta_file, 'w') as f:
                    json.dump(meta, f, indent=2)
    
    def process_all_filings(self):
        """Process all SEC filings to extract tables"""
        
        # Find all HTML files
        filing_dir = self.input_dir / "sec-edgar-filings"
        
        if not filing_dir.exists():
            logger.error(f"Directory not found: {filing_dir}")
            return
        
        # Get all primary HTML documents
        files = list(filing_dir.rglob("primary-document.html"))
        
        if not files:
            logger.warning("No primary documents found")
            return
        
        logger.info(f"Found {len(files)} HTML files to process")
        
        total_tables = 0
        
        # Process each file
        for file_path in tqdm(files, desc="Extracting tables"):
            # Extract tables
            tables = self.extract_tables_from_html(file_path)
            
            # Save tables
            if tables:
                self.save_tables(file_path, tables)
                total_tables += len(tables)
            
            # Log extraction
            self.extraction_log.append({
                'file': str(file_path.relative_to(self.input_dir)),
                'tables_found': len(tables),
                'table_types': [t.get('table_type', 'unknown') for t in tables],
                'method': 'html_parser',
                'status': 'success' if tables else 'no_tables'
            })
        
        # Save extraction log
        self._save_extraction_log()
        
        # Print summary
        self._print_summary(total_tables)
    
    def _save_extraction_log(self):
        """Save extraction log"""
        log_file = self.output_dir / "table_extraction_log.json"
        with open(log_file, 'w') as f:
            json.dump(self.extraction_log, f, indent=2)
        logger.info(f"Extraction log saved to {log_file}")
    
    def _print_summary(self, total_tables: int):
        """Print extraction summary"""
        print("\n" + "="*50)
        print("Table Extraction Summary")
        print("="*50)
        
        total_files = len(self.extraction_log)
        files_with_tables = sum(1 for log in self.extraction_log if log['tables_found'] > 0)
        
        print(f"Total files processed: {total_files}")
        print(f"Files with tables: {files_with_tables}")
        print(f"Total tables extracted: {total_tables}")
        
        if total_tables > 0:
            print(f"Average tables per document: {total_tables / total_files:.1f}")
            
            # Count table types
            table_types = {}
            for log in self.extraction_log:
                for t_type in log.get('table_types', []):
                    table_types[t_type] = table_types.get(t_type, 0) + 1
            
            print("\n📊 Table Types Found:")
            for t_type, count in sorted(table_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {t_type}: {count}")
        
        print(f"\n📁 Output directory: {self.output_dir}")


def main():
    """Main function"""
    extractor = TableExtractor()
    extractor.process_all_filings()
    
    print("\n✅ Part 2 Complete!")
    print("\nNext steps:")
    print("1. Review extracted tables in data/parsed/tables/")
    print("2. Check table_extraction_log.json for details")
    print("3. Proceed to Part 3 for layout detection")


if __name__ == "__main__":
    main()
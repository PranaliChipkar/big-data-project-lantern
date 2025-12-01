#!/usr/bin/env python3
"""
Part 5: Metadata & Provenance Tagging
Attaches provenance metadata to every extracted piece of text and table
Enables traceability in downstream QA and ensures answers can cite exact locations
"""

import sys
from pathlib import Path
import json
import jsonlines
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
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


class MetadataSchema:
    """Define the metadata schema for all extracted content"""
    
    @staticmethod
    def create_document_metadata(file_path: Path) -> Dict:
        """
        Create document-level metadata
        
        Args:
            file_path: Path to source document
            
        Returns:
            Document metadata dictionary
        """
        parts = file_path.parts
        
        # Extract filing information from path
        ticker = parts[-4] if len(parts) > 3 else 'unknown'
        filing_type = parts[-3] if len(parts) > 3 else 'unknown'
        filing_id = parts[-2] if len(parts) > 2 else 'unknown'
        
        # Generate unique document ID
        doc_id = hashlib.md5(str(file_path).encode()).hexdigest()[:12]
        
        return {
            'doc_id': doc_id,
            'ticker': ticker,
            'company': ticker,  # Could be enhanced with full company name
            'filing_type': filing_type,
            'filing_id': filing_id,
            'fiscal_period': MetadataSchema._extract_fiscal_period(filing_type),
            'source_file': file_path.name,
            'source_path': str(file_path),
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'processed_at': datetime.now().isoformat(),
            'schema_version': '1.0'
        }
    
    @staticmethod
    def _extract_fiscal_period(filing_type: str) -> str:
        """Extract fiscal period from filing type"""
        if '10-K' in filing_type:
            return 'annual'
        elif '10-Q' in filing_type:
            return 'quarterly'
        elif '8-K' in filing_type:
            return 'current'
        else:
            return 'unknown'
    
    @staticmethod
    def create_block_metadata(
        doc_metadata: Dict,
        block_type: str,
        block_content: Any,
        page: int = 1,
        section: Optional[str] = None,
        bbox: Optional[tuple] = None,
        block_index: int = 0
    ) -> Dict:
        """
        Create metadata for an individual content block
        
        Args:
            doc_metadata: Document-level metadata
            block_type: Type of block (text, table, figure, etc.)
            block_content: The actual content
            page: Page number
            section: Section identifier
            bbox: Bounding box coordinates
            block_index: Index of this block in document
            
        Returns:
            Block metadata dictionary
        """
        # Generate unique block ID
        block_id = f"{doc_metadata['doc_id']}_{block_type}_{block_index:04d}"
        
        # Calculate content statistics
        content_stats = MetadataSchema._calculate_content_stats(block_content)
        
        return {
            'block_id': block_id,
            'doc_id': doc_metadata['doc_id'],
            'company': doc_metadata['company'],
            'fiscal_year': MetadataSchema._extract_year(doc_metadata),
            'page': page,
            'section': section or 'unknown',
            'block_type': block_type,
            'block_index': block_index,
            'bbox': bbox,
            'content_stats': content_stats,
            'source_path': doc_metadata['source_path'],
            'extraction_method': 'automated',
            'confidence': 0.95,  # Could be dynamic based on extraction quality
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def _extract_year(doc_metadata: Dict) -> str:
        """Extract year from filing ID or default to current"""
        filing_id = doc_metadata.get('filing_id', '')
        # Filing IDs often contain year like "0000320193-24-000123"
        if '-' in filing_id:
            parts = filing_id.split('-')
            if len(parts) > 1:
                year_part = parts[1]
                if year_part.isdigit() and len(year_part) == 2:
                    return f"20{year_part}"
        return str(datetime.now().year)
    
    @staticmethod
    def _calculate_content_stats(content: Any) -> Dict:
        """Calculate statistics about the content"""
        stats = {
            'char_count': 0,
            'word_count': 0,
            'line_count': 0
        }
        
        if isinstance(content, str):
            stats['char_count'] = len(content)
            stats['word_count'] = len(content.split())
            stats['line_count'] = len(content.splitlines())
        elif isinstance(content, list):
            # For tables
            stats['row_count'] = len(content)
            stats['col_count'] = len(content[0]) if content else 0
        
        return stats


class MetadataTagger:
    """Add metadata and provenance to all extracted content"""
    
    def __init__(
        self,
        text_dir: str = "data/parsed/text",
        table_dir: str = "data/parsed/tables",
        layout_dir: str = "data/parsed/layouts",
        output_dir: str = "data/parsed/metadata"
    ):
        """
        Initialize the metadata tagger
        
        Args:
            text_dir: Directory with extracted text
            table_dir: Directory with extracted tables
            layout_dir: Directory with layout information
            output_dir: Directory to save metadata-enriched content
        """
        self.text_dir = Path(text_dir)
        self.table_dir = Path(table_dir)
        self.layout_dir = Path(layout_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track tagging statistics
        self.tagging_log = []
    
    def tag_text_content(self, source_file: Path) -> List[Dict]:
        """
        Tag extracted text with metadata
        
        Args:
            source_file: Original source file path
            
        Returns:
            List of tagged content blocks
        """
        tagged_blocks = []
        
        # Create document metadata
        doc_metadata = MetadataSchema.create_document_metadata(source_file)
        
        # Find corresponding text file
        rel_path = source_file.relative_to(Path("data/raw/pdfs/sec-edgar-filings"))
        text_file = self.text_dir / rel_path.parent / f"{source_file.stem}.txt"
        
        if text_file.exists():
            # Read extracted text
            with open(text_file, 'r', encoding='utf-8') as f:
                full_text = f.read()
            
            # Split into sections (simple approach - could be enhanced)
            sections = self._split_into_sections(full_text)
            
            block_index = 0
            for section_name, section_text in sections.items():
                # Create metadata for this section
                block_metadata = MetadataSchema.create_block_metadata(
                    doc_metadata=doc_metadata,
                    block_type='text',
                    block_content=section_text,
                    section=section_name,
                    block_index=block_index
                )
                
                # Combine metadata with content
                tagged_block = {
                    **block_metadata,
                    'text': section_text[:1000],  # Limit text for storage
                    'full_text_available': True
                }
                
                tagged_blocks.append(tagged_block)
                block_index += 1
        
        return tagged_blocks
    
    def tag_table_content(self, source_file: Path) -> List[Dict]:
        """
        Tag extracted tables with metadata
        
        Args:
            source_file: Original source file path
            
        Returns:
            List of tagged table blocks
        """
        tagged_tables = []
        
        # Create document metadata
        doc_metadata = MetadataSchema.create_document_metadata(source_file)
        
        # Find corresponding table files
        rel_path = source_file.relative_to(Path("data/raw/pdfs/sec-edgar-filings"))
        table_pattern = self.table_dir / rel_path.parent / f"{source_file.stem}_*.csv"
        
        table_files = list(Path(self.table_dir / rel_path.parent).glob(f"{source_file.stem}_*.csv"))
        
        for idx, table_file in enumerate(table_files):
            try:
                # Read table
                df = pd.read_csv(table_file)
                
                # Extract table type from filename
                table_type = self._extract_table_type(table_file.name)
                
                # Create metadata for this table
                block_metadata = MetadataSchema.create_block_metadata(
                    doc_metadata=doc_metadata,
                    block_type='table',
                    block_content=df.values.tolist(),
                    section=table_type,
                    block_index=idx
                )
                
                # Combine metadata with table info
                tagged_table = {
                    **block_metadata,
                    'table_file': str(table_file),
                    'table_type': table_type,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': df.columns.tolist()
                }
                
                tagged_tables.append(tagged_table)
                
            except Exception as e:
                logger.error(f"Error tagging table {table_file}: {e}")
        
        return tagged_tables
    
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """
        Split text into sections based on common patterns
        
        Args:
            text: Full document text
            
        Returns:
            Dictionary of section_name: section_text
        """
        sections = {}
        
        # Common section patterns in SEC filings
        section_patterns = [
            r'ITEM\s+\d+[A-Z]?\.',
            r'PART\s+[IVX]+',
            r'Management.s Discussion and Analysis',
            r'Financial Statements',
            r'Risk Factors'
        ]
        
        # For simplicity, just split by lines for now
        # In production, would use regex to find section boundaries
        lines = text.splitlines()
        current_section = "introduction"
        current_text = []
        
        for line in lines:
            # Check if this line is a section header
            is_header = False
            for pattern in ['ITEM', 'PART', 'Management', 'Financial', 'Risk']:
                if pattern in line.upper():
                    # Save previous section
                    if current_text:
                        sections[current_section] = '\n'.join(current_text)
                    # Start new section
                    current_section = line[:50].strip()
                    current_text = []
                    is_header = True
                    break
            
            if not is_header:
                current_text.append(line)
        
        # Save last section
        if current_text:
            sections[current_section] = '\n'.join(current_text)
        
        # If no sections found, return whole text as one section
        if not sections:
            sections['full_document'] = text
        
        return sections
    
    def _extract_table_type(self, filename: str) -> str:
        """Extract table type from filename"""
        # Filenames like "primary-document_balance_sheet_1.csv"
        parts = filename.replace('.csv', '').split('_')
        if len(parts) > 2:
            return '_'.join(parts[1:-1])
        return 'table'
    
    def create_jsonl_output(self, tagged_content: List[Dict], output_file: Path):
        """
        Create JSONL output file with all tagged content
        
        Args:
            tagged_content: List of tagged content blocks
            output_file: Path to output JSONL file
        """
        with jsonlines.open(output_file, mode='w') as writer:
            for block in tagged_content:
                writer.write(block)
        
        logger.info(f"Wrote {len(tagged_content)} blocks to {output_file}")
    
    def create_markdown_summary(self, source_file: Path, tagged_content: List[Dict]) -> str:
        """
        Create markdown summary with metadata
        
        Args:
            source_file: Source file path
            tagged_content: List of tagged content blocks
            
        Returns:
            Markdown string
        """
        # Get document metadata
        doc_meta = MetadataSchema.create_document_metadata(source_file)
        
        markdown = f"""# {doc_meta['ticker']} - {doc_meta['filing_type']} Filing

## Document Metadata
- **Document ID**: {doc_meta['doc_id']}
- **Company**: {doc_meta['company']}
- **Filing Type**: {doc_meta['filing_type']}
- **Filing ID**: {doc_meta['filing_id']}
- **Source**: {doc_meta['source_file']}
- **Processed**: {doc_meta['processed_at']}

## Content Summary
- **Total Blocks**: {len(tagged_content)}
- **Text Blocks**: {sum(1 for b in tagged_content if b.get('block_type') == 'text')}
- **Table Blocks**: {sum(1 for b in tagged_content if b.get('block_type') == 'table')}

## Sections Found
"""
        # List unique sections
        sections = set(b.get('section', 'unknown') for b in tagged_content)
        for section in sorted(sections):
            block_count = sum(1 for b in tagged_content if b.get('section') == section)
            markdown += f"- {section}: {block_count} blocks\n"
        
        markdown += """
## Provenance Tracking

Every extracted piece has:
- Unique block ID for reference
- Source document and location
- Extraction method and confidence
- Timestamp of extraction

This enables full traceability for downstream QA systems.
"""
        
        return markdown
    
    def process_all_documents(self):
        """Process all documents to add metadata and provenance"""
        
        # Find all source documents
        source_dir = Path("data/raw/pdfs/sec-edgar-filings")
        source_files = list(source_dir.rglob("primary-document.html"))
        
        if not source_files:
            logger.error("No source files found")
            return
        
        logger.info(f"Processing {len(source_files)} documents for metadata tagging")
        
        all_tagged_content = []
        
        for source_file in tqdm(source_files, desc="Adding metadata"):
            try:
                # Tag text content
                text_blocks = self.tag_text_content(source_file)
                
                # Tag table content
                table_blocks = self.tag_table_content(source_file)
                
                # Combine all blocks
                doc_blocks = text_blocks + table_blocks
                all_tagged_content.extend(doc_blocks)
                
                # Save per-document outputs
                rel_path = source_file.relative_to(source_dir)
                output_path = self.output_dir / rel_path.parent
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Save JSONL
                jsonl_file = output_path / f"{source_file.stem}_metadata.jsonl"
                self.create_jsonl_output(doc_blocks, jsonl_file)
                
                # Save Markdown summary
                markdown = self.create_markdown_summary(source_file, doc_blocks)
                md_file = output_path / f"{source_file.stem}_summary.md"
                with open(md_file, 'w') as f:
                    f.write(markdown)
                
                # Log statistics
                self.tagging_log.append({
                    'file': str(source_file.relative_to(source_dir)),
                    'text_blocks': len(text_blocks),
                    'table_blocks': len(table_blocks),
                    'total_blocks': len(doc_blocks),
                    'status': 'success'
                })
                
            except Exception as e:
                logger.error(f"Error processing {source_file}: {e}")
                self.tagging_log.append({
                    'file': str(source_file.relative_to(source_dir)),
                    'status': 'error',
                    'error': str(e)
                })
        
        # Save complete dataset
        self._save_complete_dataset(all_tagged_content)
        
        # Save tagging log
        self._save_tagging_log()
        
        # Print summary
        self._print_summary()
    
    def _save_complete_dataset(self, all_content: List[Dict]):
        """Save complete tagged dataset"""
        
        # Save as single JSONL file
        complete_file = self.output_dir / "complete_metadata_dataset.jsonl"
        self.create_jsonl_output(all_content, complete_file)
        
        # Save summary statistics
        stats = {
            'total_documents': len(set(b['doc_id'] for b in all_content)),
            'total_blocks': len(all_content),
            'total_text_blocks': sum(1 for b in all_content if b['block_type'] == 'text'),
            'total_table_blocks': sum(1 for b in all_content if b['block_type'] == 'table'),
            'companies': list(set(b['company'] for b in all_content)),
            'filing_types': list(set(b.get('filing_type', 'unknown') for b in all_content)),
            'created_at': datetime.now().isoformat()
        }
        
        stats_file = self.output_dir / "dataset_statistics.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def _save_tagging_log(self):
        """Save tagging log"""
        log_file = self.output_dir / "metadata_tagging_log.json"
        with open(log_file, 'w') as f:
            json.dump(self.tagging_log, f, indent=2)
        logger.info(f"Tagging log saved to {log_file}")
    
    def _print_summary(self):
        """Print tagging summary"""
        print("\n" + "="*50)
        print("Metadata & Provenance Tagging Summary")
        print("="*50)
        
        total_files = len(self.tagging_log)
        successful = sum(1 for log in self.tagging_log if log.get('status') == 'success')
        
        print(f"Documents processed: {total_files}")
        print(f"✅ Successful: {successful}")
        
        if successful > 0:
            total_blocks = sum(log.get('total_blocks', 0) for log in self.tagging_log)
            text_blocks = sum(log.get('text_blocks', 0) for log in self.tagging_log)
            table_blocks = sum(log.get('table_blocks', 0) for log in self.tagging_log)
            
            print(f"\n📊 Content Tagged:")
            print(f"  Total blocks: {total_blocks:,}")
            print(f"  Text blocks: {text_blocks:,}")
            print(f"  Table blocks: {table_blocks:,}")
            print(f"  Average blocks per document: {total_blocks // successful}")
            
            print(f"\n✨ Key Features:")
            print(f"  • Unique IDs for every block")
            print(f"  • Full provenance tracking")
            print(f"  • Section identification")
            print(f"  • Content statistics")
            print(f"  • JSONL format for streaming")
        
        print(f"\n📁 Output directory: {self.output_dir}")
        print(f"📄 Complete dataset: {self.output_dir}/complete_metadata_dataset.jsonl")


def main():
    """Main function"""
    tagger = MetadataTagger()
    tagger.process_all_documents()
    
    print("\n✅ Part 5 Complete!")
    print("\nNext steps:")
    print("1. Review metadata in data/parsed/metadata/")
    print("2. Check complete_metadata_dataset.jsonl for all tagged content")
    print("3. Review markdown summaries for each document")
    print("4. Proceed to Part 6 for storage format comparison")


if __name__ == "__main__":
    main()
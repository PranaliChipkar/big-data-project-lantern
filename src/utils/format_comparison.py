#!/usr/bin/env python3
"""
Part 6: Storage Format Comparison - Markdown vs JSON vs TXT
Compares different output formats to decide which best supports downstream retrieval
"""

import sys
from pathlib import Path
import json
import jsonlines
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
from tqdm import tqdm
import pandas as pd
from dataclasses import dataclass
import os

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FormatMetrics:
    """Metrics for evaluating storage formats"""
    file_size: int
    write_time: float
    read_time: float
    search_time: float
    human_readable: int  # Score 1-10
    machine_parsable: int  # Score 1-10
    preserves_structure: int  # Score 1-10
    supports_metadata: int  # Score 1-10
    compression_ratio: float


class FormatConverter:
    """Convert content to different storage formats"""
    
    def __init__(self, metadata_dir: str = "data/parsed/metadata"):
        """
        Initialize format converter
        
        Args:
            metadata_dir: Directory containing metadata-tagged content
        """
        self.metadata_dir = Path(metadata_dir)
        
    def load_sample_data(self) -> Dict:
        """Load sample data for conversion"""
        
        # Load from complete dataset
        complete_file = self.metadata_dir / "complete_metadata_dataset.jsonl"
        
        sample_data = {
            'blocks': [],
            'document_info': {},
            'tables': []
        }
        
        if complete_file.exists():
            with jsonlines.open(complete_file) as reader:
                for obj in reader:
                    sample_data['blocks'].append(obj)
                    
                    # Organize by type
                    if obj.get('block_type') == 'table':
                        sample_data['tables'].append(obj)
                    
                    # Extract document info
                    doc_id = obj.get('doc_id')
                    if doc_id and doc_id not in sample_data['document_info']:
                        sample_data['document_info'][doc_id] = {
                            'company': obj.get('company'),
                            'filing_type': obj.get('filing_type', 'unknown'),
                            'source_path': obj.get('source_path')
                        }
        
        return sample_data
    
    def convert_to_markdown(self, data: Dict) -> str:
        """
        Convert data to Markdown format
        
        Args:
            data: Sample data dictionary
            
        Returns:
            Markdown string
        """
        markdown = "# SEC Filings Dataset\n\n"
        
        # Document summary
        markdown += "## Documents\n\n"
        for doc_id, info in data['document_info'].items():
            markdown += f"### {info['company']} - {info['filing_type']}\n"
            markdown += f"- **Document ID**: {doc_id}\n"
            markdown += f"- **Source**: {info['source_path']}\n\n"
        
        # Sample content blocks
        markdown += "## Sample Content Blocks\n\n"
        for block in data['blocks'][:5]:  # First 5 blocks
            markdown += f"### Block: {block.get('block_id', 'unknown')}\n"
            markdown += f"- **Type**: {block.get('block_type')}\n"
            markdown += f"- **Section**: {block.get('section', 'unknown')}\n"
            markdown += f"- **Page**: {block.get('page', 1)}\n"
            
            if 'text' in block:
                markdown += f"\n{block['text'][:200]}...\n\n"
            
            markdown += "---\n\n"
        
        # Tables summary
        markdown += f"## Tables\n\n"
        markdown += f"Total tables: {len(data['tables'])}\n\n"
        
        for table in data['tables'][:3]:  # First 3 tables
            markdown += f"- {table.get('table_type', 'table')}: "
            markdown += f"{table.get('rows', 0)} rows × {table.get('columns', 0)} columns\n"
        
        return markdown
    
    def convert_to_json(self, data: Dict) -> str:
        """
        Convert data to JSON format
        
        Args:
            data: Sample data dictionary
            
        Returns:
            JSON string
        """
        # Structure data for JSON
        json_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total_blocks': len(data['blocks']),
                'total_documents': len(data['document_info']),
                'schema_version': '1.0'
            },
            'documents': data['document_info'],
            'content': {
                'text_blocks': [b for b in data['blocks'] if b.get('block_type') == 'text'][:5],
                'tables': data['tables'][:5]
            }
        }
        
        return json.dumps(json_data, indent=2)
    
    def convert_to_txt(self, data: Dict) -> str:
        """
        Convert data to plain text format
        
        Args:
            data: Sample data dictionary
            
        Returns:
            Plain text string
        """
        text = "SEC FILINGS DATASET\n"
        text += "=" * 50 + "\n\n"
        
        # Document list
        text += "DOCUMENTS:\n"
        for doc_id, info in data['document_info'].items():
            text += f"  - {info['company']} {info['filing_type']} (ID: {doc_id})\n"
        
        text += "\n" + "-" * 50 + "\n\n"
        
        # Sample content
        text += "SAMPLE CONTENT:\n\n"
        for block in data['blocks'][:5]:
            if 'text' in block:
                text += f"[{block.get('block_type')}] {block.get('section', 'unknown')}:\n"
                text += f"{block['text'][:300]}...\n\n"
        
        # Statistics
        text += "-" * 50 + "\n"
        text += f"STATISTICS:\n"
        text += f"  Total blocks: {len(data['blocks'])}\n"
        text += f"  Total tables: {len(data['tables'])}\n"
        text += f"  Documents: {len(data['document_info'])}\n"
        
        return text
    
    def convert_to_jsonl(self, data: Dict) -> str:
        """
        Convert data to JSONL format (newline-delimited JSON)
        
        Args:
            data: Sample data dictionary
            
        Returns:
            JSONL string
        """
        lines = []
        
        # Each block becomes a line
        for block in data['blocks'][:10]:  # First 10 blocks
            lines.append(json.dumps(block))
        
        return '\n'.join(lines)


class FormatEvaluator:
    """Evaluate different storage formats"""
    
    def __init__(self, output_dir: str = "data/parsed/format_comparison"):
        """
        Initialize format evaluator
        
        Args:
            output_dir: Directory to save format comparisons
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def evaluate_format(self, format_name: str, content: str, data: Dict) -> FormatMetrics:
        """
        Evaluate a storage format
        
        Args:
            format_name: Name of the format
            content: Content in this format
            data: Original data for comparison
            
        Returns:
            Format metrics
        """
        # Save to file
        file_path = self.output_dir / f"sample.{format_name}"
        
        # Measure write time
        start = time.time()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        write_time = time.time() - start
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Measure read time
        start = time.time()
        with open(file_path, 'r', encoding='utf-8') as f:
            _ = f.read()
        read_time = time.time() - start
        
        # Measure search time (simple substring search)
        search_term = "revenue"
        start = time.time()
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            occurrences = content.lower().count(search_term.lower())
        search_time = time.time() - start
        
        # Calculate compression ratio (compared to raw data size)
        raw_size = len(json.dumps(data))
        compression_ratio = raw_size / file_size if file_size > 0 else 1.0
        
        # Scoring (1-10 scale)
        scores = self._calculate_scores(format_name)
        
        return FormatMetrics(
            file_size=file_size,
            write_time=write_time,
            read_time=read_time,
            search_time=search_time,
            human_readable=scores['human_readable'],
            machine_parsable=scores['machine_parsable'],
            preserves_structure=scores['preserves_structure'],
            supports_metadata=scores['supports_metadata'],
            compression_ratio=compression_ratio
        )
    
    def _calculate_scores(self, format_name: str) -> Dict[str, int]:
        """Calculate qualitative scores for each format"""
        
        scores = {
            'md': {
                'human_readable': 9,
                'machine_parsable': 6,
                'preserves_structure': 8,
                'supports_metadata': 7
            },
            'json': {
                'human_readable': 5,
                'machine_parsable': 10,
                'preserves_structure': 10,
                'supports_metadata': 10
            },
            'txt': {
                'human_readable': 7,
                'machine_parsable': 3,
                'preserves_structure': 3,
                'supports_metadata': 2
            },
            'jsonl': {
                'human_readable': 4,
                'machine_parsable': 9,
                'preserves_structure': 8,
                'supports_metadata': 9
            }
        }
        
        return scores.get(format_name, {
            'human_readable': 5,
            'machine_parsable': 5,
            'preserves_structure': 5,
            'supports_metadata': 5
        })
    
    def create_comparison_report(self, metrics: Dict[str, FormatMetrics]) -> str:
        """
        Create comparison report
        
        Args:
            metrics: Dictionary of format_name -> FormatMetrics
            
        Returns:
            Report string
        """
        report = "# Storage Format Comparison Report\n\n"
        report += f"Generated: {datetime.now().isoformat()}\n\n"
        
        # Performance metrics table
        report += "## Performance Metrics\n\n"
        report += "| Format | File Size | Write Time | Read Time | Search Time | Compression |\n"
        report += "|--------|-----------|------------|-----------|-------------|-------------|\n"
        
        for fmt, m in metrics.items():
            report += f"| {fmt.upper()} | {m.file_size:,} bytes | {m.write_time:.4f}s | "
            report += f"{m.read_time:.4f}s | {m.search_time:.4f}s | {m.compression_ratio:.2f}x |\n"
        
        # Qualitative scores
        report += "\n## Qualitative Scores (1-10)\n\n"
        report += "| Format | Human Readable | Machine Parsable | Structure | Metadata |\n"
        report += "|--------|----------------|------------------|-----------|----------|\n"
        
        for fmt, m in metrics.items():
            report += f"| {fmt.upper()} | {m.human_readable} | {m.machine_parsable} | "
            report += f"{m.preserves_structure} | {m.supports_metadata} |\n"
        
        # Recommendations
        report += "\n## Recommendations\n\n"
        report += self._generate_recommendations(metrics)
        
        return report
    
    def _generate_recommendations(self, metrics: Dict[str, FormatMetrics]) -> str:
        """Generate format recommendations based on metrics"""
        
        rec = "### Use Cases by Format\n\n"
        
        rec += "**Markdown (.md)**\n"
        rec += "- ✅ Best for: Human review, documentation, reports\n"
        rec += "- ✅ Preserves document structure well\n"
        rec += "- ❌ Not ideal for: Machine processing, large-scale analysis\n\n"
        
        rec += "**JSON (.json)**\n"
        rec += "- ✅ Best for: APIs, full data preservation, complex queries\n"
        rec += "- ✅ Perfect structure and metadata preservation\n"
        rec += "- ❌ Not ideal for: Human reading, large files\n\n"
        
        rec += "**Plain Text (.txt)**\n"
        rec += "- ✅ Best for: Simple searches, legacy systems, minimal storage\n"
        rec += "- ✅ Universal compatibility\n"
        rec += "- ❌ Not ideal for: Structure preservation, metadata\n\n"
        
        rec += "**JSONL (.jsonl)**\n"
        rec += "- ✅ Best for: Streaming, large datasets, line-by-line processing\n"
        rec += "- ✅ Good balance of structure and efficiency\n"
        rec += "- ❌ Not ideal for: Human reading, nested structures\n\n"
        
        # Overall recommendation
        rec += "### Overall Recommendation\n\n"
        rec += "For this SEC filing dataset:\n"
        rec += "1. **Primary storage**: JSONL for efficient processing and streaming\n"
        rec += "2. **Human review**: Markdown summaries for key documents\n"
        rec += "3. **API/Integration**: JSON for structured access\n"
        rec += "4. **Search/Index**: Plain text for full-text search engines\n"
        
        return rec


def main():
    """Main function"""
    
    print("\n" + "="*50)
    print("Part 6: Storage Format Comparison")
    print("="*50)
    
    # Initialize components
    converter = FormatConverter()
    evaluator = FormatEvaluator()
    
    # Load sample data
    print("\n📚 Loading sample data...")
    sample_data = converter.load_sample_data()
    
    if not sample_data['blocks']:
        logger.error("No data found. Please run Part 5 first.")
        return
    
    print(f"  Loaded {len(sample_data['blocks'])} blocks from {len(sample_data['document_info'])} documents")
    
    # Convert to different formats
    print("\n🔄 Converting to different formats...")
    formats = {
        'md': converter.convert_to_markdown(sample_data),
        'json': converter.convert_to_json(sample_data),
        'txt': converter.convert_to_txt(sample_data),
        'jsonl': converter.convert_to_jsonl(sample_data)
    }
    
    # Evaluate each format
    print("\n📊 Evaluating formats...")
    metrics = {}
    
    for format_name, content in tqdm(formats.items(), desc="Evaluating"):
        metrics[format_name] = evaluator.evaluate_format(format_name, content, sample_data)
    
    # Create comparison report
    print("\n📝 Creating comparison report...")
    report = evaluator.create_comparison_report(metrics)
    
    # Save report
    report_file = evaluator.output_dir / "format_comparison_report.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Print summary
    print("\n" + "="*50)
    print("Format Comparison Results")
    print("="*50)
    
    print("\n📈 Performance Summary:")
    for fmt, m in metrics.items():
        print(f"\n{fmt.upper()} Format:")
        print(f"  • File size: {m.file_size:,} bytes")
        print(f"  • Human readable: {m.human_readable}/10")
        print(f"  • Machine parsable: {m.machine_parsable}/10")
        print(f"  • Structure preservation: {m.preserves_structure}/10")
    
    print("\n🎯 Recommendation for SEC Filings:")
    print("  1. Use JSONL for main storage (streaming, efficient)")
    print("  2. Generate Markdown for human review")
    print("  3. Keep JSON for API access")
    print("  4. Create TXT for search indexing")
    
    print(f"\n📁 Output directory: {evaluator.output_dir}")
    print(f"📄 Full report: {report_file}")
    
    print("\n✅ Part 6 Complete!")
    print("\nNext steps:")
    print("1. Review format samples in data/parsed/format_comparison/")
    print("2. Read the full comparison report")
    print("3. Proceed to Part 7 for Build vs Buy analysis")


if __name__ == "__main__":
    main()
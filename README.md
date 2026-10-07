# Project LANTERN - AI‑Powered PDF Parsing Pipeline

An advanced document parsing pipeline for automated extraction and analysis of SEC financial filings (10-K/10-Q documents).


## Project Overview

Project LANTERN automates the extraction and validation of financial data from SEC filings, replacing manual analysis with an intelligent parsing pipeline that achieves 92.1% accuracy while operating at 15x lower cost than commercial cloud services.

### Key Features
- **Text Extraction**: 255,007 words extracted with 98% accuracy
- **Table Detection**: 422 financial tables identified and parsed
- **Layout Analysis**: Document structure understanding with LayoutParser
- **XBRL Validation**: Cross-validation with official SEC structured data
- **Cost Efficiency**: 92% cheaper than AWS Textract/Google Document AI
- **Performance**: Processes 3.73 pages/second (3,200+ documents/day)
- **Reproducibility**: Full DVC pipeline for consistent results

## Pipeline Performance Metrics

| Metric | Value |
|--------|-------|
| **Extraction Quality** | 92.1/100 |
| **Processing Speed** | 3.73 pages/second |
| **Tables Extracted** | 422 |
| **Words Extracted** | 255,007 |
| **Cost per 1000 pages** | $1.00 |
| **Success Rate** | 94% |
| **XBRL Validation Accuracy** | 85% for key concepts |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  SEC EDGAR API  │────▶│  Text Extractor │────▶│    Metadata     │
│   Downloader    │     │  (pdfplumber)   │     │     Tagger      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Table Extractor │────▶│ Layout Detector │────▶│  XBRL Validator │
│   (Camelot)     │     │ (LayoutParser)  │     │   (python-xbrl) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │   DVC Pipeline       │
                    │  (Reproducibility)   │
                    └─────────────────────┘
```

## Installation

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/PranaliChipkar/big-data-project-lantern.git

```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install Tesseract OCR** (for OCR fallback)
```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

## Quick Start

### Run Complete Pipeline
```bash
# Run the entire pipeline with DVC
dvc repro

# Or run individual components
python src/download/edgar_downloader.py        # Download SEC filings
python src/parsers/pdf_parser.py               # Extract text
python src/parsers/table_extractor.py          # Extract tables
python src/parsers/layout_detector.py          # Detect layouts
python src/utils/metadata.py                   # Add metadata
```

### Run Evaluation & Validation
```bash
# Evaluate extraction quality
python src/evaluation/evaluation_metrics_final.py

# Benchmark performance
python src/benchmarking/performance_benchmark.py

# Validate against XBRL
python src/validation/xbrl_validation.py
```

### Run Tests
```bash
# Run regression tests
python tests/test_extraction_quality.py -v
```

## Project Structure

```
project-lantern/
├── src/
│   ├── download/           # SEC filing downloaders
│   ├── parsers/            # Text, table, layout parsers
│   ├── utils/              # Metadata, format conversion
│   ├── evaluation/         # Quality evaluation metrics
│   ├── benchmarking/       # Performance benchmarks
│   └── validation/         # XBRL validation
├── data/
│   ├── raw/               # Downloaded SEC filings
│   │   ├── pdfs/          # Original documents
│   │   └── xbrl/          # XBRL files
│   └── parsed/            # Processed outputs
│       ├── text/          # Extracted text
│       ├── tables/        # Extracted tables (CSV)
│       ├── layouts/       # Layout information
│       └── metadata/      # Tagged content
├── reports/               # Analysis reports
├── tests/                 # Test suites
├── config/               # Configuration files
├── dvc.yaml              # DVC pipeline definition
├── dvc.lock              # DVC pipeline lock file
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## DVC Pipeline Stages

The pipeline consists of 8 reproducible stages:

1. **download**: Fetch SEC filings from EDGAR
2. **parse_text**: Extract text using pdfplumber
3. **extract_tables**: Extract tables using Camelot
4. **detect_layout**: Analyze document structure
5. **docling_comparison**: Compare with Docling parser
6. **add_metadata**: Tag content with provenance
7. **format_comparison**: Compare storage formats
8. **build_vs_buy**: Analyze cost vs cloud services

Run any stage:
```bash
dvc repro <stage_name>
```

## Results Summary

### Phase 1: Design (Parts 0-4)
- Downloaded 8 SEC filings (AAPL, MSFT)
- Extracted 255,007 words of text
- Identified 422 financial tables
- Detected 19,517 layout blocks
- Compared with Docling advanced parser

### Phase 2: Representation & Staging (Parts 5-8)
- Tagged 1,266 content blocks with metadata
- Optimized storage format (JSONL selected)
- AWS Textract integration and cost analysis
- Created reproducible DVC pipeline

### Phase 3: Evaluation & Validation (Parts 9-11)
- Quality Score: 92.1/100
- Performance: 3.73 pages/second
- XBRL Validation: 85% accuracy on key financials

## Cost Comparison

| Service | Cost per 1000 Pages | Monthly (50K pages) |
|---------|-------------------|-------------------|
| **Our Pipeline** | $1.00 | $50 |
| AWS Textract | $15.00 | $750 |

**Savings: 92% lower cost than cloud services**

## Testing

Run the complete test suite:
```bash
pytest tests/ -v
```

Or run specific tests:
```bash
python tests/test_extraction_quality.py
```

All regression tests pass with:
- Minimum word extraction: 229,506 words
- Maximum WER: 0.024
- Minimum tables: 379
- Minimum F1 score: 0.70

## Configuration

Edit `config/params.yaml` to customize:
- Filing types to download
- OCR settings
- Table extraction methods
- Metadata schema version
- Output formats

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies installed
```bash
pip install -r requirements.txt
```

2. **Tesseract not found**: Install Tesseract OCR
```bash
brew install tesseract  # macOS
```

3. **Memory errors**: Reduce batch size in config
```yaml
parsing:
  batch_size: 10  # Reduce if memory issues
```

4. **DVC errors**: Initialize DVC
```bash
dvc init
```

## Documentation

- [Evaluation Report](reports/evaluation_report.md) - Quality metrics
- [Benchmark Report](reports/benchmark_report.md) - Performance analysis
- [XBRL Validation](reports/xbrl_validation_report.md) - Validation results


## License

Academic use only. Part of coursework for Big Data course.

## Achievements

- **92.1% Extraction Accuracy** - Industry-leading quality
- **15x Cost Reduction** - Compared to cloud services  
- **3,200 Documents/Day** - Production-ready throughput
- **Full Reproducibility** - DVC pipeline ensures consistency
- **XBRL Validation** - Verified against official SEC data

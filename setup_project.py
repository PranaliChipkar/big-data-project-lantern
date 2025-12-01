#!/usr/bin/env python3
"""
Setup script to initialize Project LANTERN directory structure
Run this to create all necessary directories and files
"""

import os
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_directory_structure():
    """Create the complete project directory structure"""
    
    # Define all directories
    directories = [
        # Source code
        "src",
        "src/download",
        "src/parsers", 
        "src/validation",
        "src/utils",
        
        # Data directories
        "data/raw/pdfs",
        "data/raw/xbrl",
        "data/parsed/text",
        "data/parsed/tables",
        "data/parsed/layouts",
        "data/parsed/metadata",
        "data/processed/markdown",
        "data/processed/json",
        "data/processed/txt",
        "data/ground_truth",
        
        # Other directories
        "notebooks",
        "reports",
        "tests",
        "config",
        "docs"
    ]
    
    # Create directories
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Add .gitkeep to keep empty directories in git
        gitkeep = Path(dir_path) / ".gitkeep"
        gitkeep.touch(exist_ok=True)
        
    logger.info("✓ Directory structure created")


def create_init_files():
    """Create __init__.py files for Python packages"""
    
    packages = [
        "src",
        "src/download",
        "src/parsers",
        "src/validation", 
        "src/utils",
        "tests",
        "config"
    ]
    
    for package in packages:
        init_file = Path(package) / "__init__.py"
        init_file.write_text('"""Package initialization"""')
        
    logger.info("✓ Python package files created")


def create_config_file():
    """Create initial configuration file"""
    
    config = {
        "project_name": "Project LANTERN",
        "version": "0.1.0",
        "sec_downloader": {
            "company_name": "YOUR_COMPANY_NAME",  # Update this
            "email": "your.email@example.com",     # Update this
            "user_agent_note": "IMPORTANT: Update company_name and email before running"
        },
        "parsing": {
            "ocr_enabled": True,
            "layout_detection_enabled": True,
            "table_extraction_methods": ["camelot_lattice", "camelot_stream", "pdfplumber"]
        },
        "output_formats": ["markdown", "json", "txt"],
        "evaluation": {
            "metrics": ["wer", "precision", "recall"],
            "benchmark_enabled": True
        }
    }
    
    config_file = Path("config") / "settings.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
        
    logger.info("✓ Configuration file created")


def create_sample_notebook():
    """Create a sample Jupyter notebook for exploration"""
    
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Project LANTERN - Data Exploration\n",
                          "\n",
                          "This notebook is for exploring SEC filings and testing parsing methods."]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["import sys\n",
                          "from pathlib import Path\n",
                          "sys.path.append(str(Path.cwd()))\n",
                          "\n",
                          "import pandas as pd\n",
                          "import pdfplumber\n",
                          "from src.download.edgar_downloader import SECFilingDownloader"]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["## 1. Load Downloaded Filings\n",
                          "\n", 
                          "First, let's check what filings we have downloaded."]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["# List downloaded PDFs\n",
                          "pdf_dir = Path('data/raw/pdfs')\n",
                          "pdf_files = list(pdf_dir.rglob('*.html')) + list(pdf_dir.rglob('*.txt'))\n",
                          "print(f'Found {len(pdf_files)} filing documents')\n",
                          "for f in pdf_files[:5]:\n",
                          "    print(f'  - {f.relative_to(pdf_dir)}')"]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.13.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }
    
    notebook_file = Path("notebooks") / "01_data_exploration.ipynb"
    with open(notebook_file, 'w') as f:
        json.dump(notebook_content, f, indent=2)
        
    logger.info("✓ Sample notebook created")


def create_dvc_config():
    """Create initial DVC configuration file"""
    
    dvc_yaml = """stages:
  download:
    cmd: python src/download/edgar_downloader.py
    deps:
      - src/download/edgar_downloader.py
    outs:
      - data/raw/pdfs
      - data/raw/xbrl
    
  parse_text:
    cmd: python src/parsers/pdf_parser.py
    deps:
      - src/parsers/pdf_parser.py
      - data/raw/pdfs
    outs:
      - data/parsed/text
    
  extract_tables:
    cmd: python src/parsers/table_extractor.py
    deps:
      - src/parsers/table_extractor.py
      - data/raw/pdfs
    outs:
      - data/parsed/tables
"""
    
    dvc_file = Path("dvc.yaml")
    dvc_file.write_text(dvc_yaml)
    
    logger.info("✓ DVC configuration created")


def main():
    """Run all setup tasks"""
    
    print("\n" + "="*50)
    print("Project LANTERN Setup")
    print("="*50 + "\n")
    
    # Create everything
    create_directory_structure()
    create_init_files()
    create_config_file()
    create_sample_notebook()
    create_dvc_config()
    
    print("\n" + "="*50)
    print("✅ Project structure created successfully!")
    print("="*50 + "\n")
    
    print("Next steps:")
    print("1. Update config/settings.json with your info")
    print("2. Edit src/download/edgar_downloader.py with your name and email")
    print("3. Run: python src/download/edgar_downloader.py")
    print("4. Start with Part 1: Text extraction")
    print("\nGood luck with Project LANTERN! 🚀")


if __name__ == "__main__":
    main()
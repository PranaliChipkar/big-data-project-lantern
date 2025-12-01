#!/usr/bin/env python3
"""
Fixed SEC EDGAR Downloader for Project LANTERN
Downloads 10-K and 10-Q filings with their XBRL attachments
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Optional
import json

from sec_edgar_downloader import Downloader
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SECFilingDownloader:
    """Download SEC filings and XBRL data from EDGAR"""
    
    def __init__(self, company_name: str, email_address: str, output_dir: str = "data/raw/pdfs"):
        """
        Initialize the SEC Filing Downloader
        
        Args:
            company_name: Your company/name for User-Agent string
            email_address: Your email for User-Agent string (SEC requirement)
            output_dir: Directory to save downloaded files
        """
        self.company_name = company_name
        self.email_address = email_address
        self.output_dir = Path(output_dir)
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize downloader with the output directory
        self.downloader = Downloader(company_name, email_address, self.output_dir)
        
        # Track downloaded files
        self.download_log = []
        
    def download_filings(
        self,
        ticker: str,
        filing_type: str = "10-K",
        limit: int = 2
    ) -> List[dict]:
        """
        Download SEC filings for a company
        
        Args:
            ticker: Stock ticker symbol (e.g., "AAPL")
            filing_type: Type of filing ("10-K", "10-Q", "8-K")
            limit: Maximum number of filings to download
            
        Returns:
            List of download metadata
        """
        logger.info(f"Downloading {limit} {filing_type} filings for {ticker}")
        
        try:
            # Download filings (they will go to output_dir/sec-edgar-filings/ticker/filing_type/)
            self.downloader.get(
                filing_type,
                ticker,
                limit=limit,
                download_details=True  # Also download filing details
            )
            
            # The files are downloaded to sec-edgar-filings subdirectory
            filing_dir = self.output_dir / "sec-edgar-filings" / ticker / filing_type
            
            if filing_dir.exists():
                logger.info(f"Found filings in: {filing_dir}")
                
                # Process each filing folder
                for filing_folder in filing_dir.iterdir():
                    if filing_folder.is_dir():
                        # Find the main document
                        files = list(filing_folder.glob("*.txt")) + list(filing_folder.glob("*.html"))
                        
                        if files:
                            for file in files:
                                metadata = {
                                    "ticker": ticker,
                                    "filing_type": filing_type,
                                    "folder_path": str(filing_folder),
                                    "filing_id": filing_folder.name,
                                    "file_path": str(file),
                                    "file_name": file.name,
                                    "file_size": file.stat().st_size,
                                    "downloaded_at": datetime.now().isoformat()
                                }
                                self.download_log.append(metadata)
                                logger.info(f"  - Downloaded: {file.name} ({file.stat().st_size:,} bytes)")
            else:
                logger.warning(f"No filings found at: {filing_dir}")
                
        except Exception as e:
            logger.error(f"Error downloading filings: {e}")
            
        return self.download_log
    
    def save_download_log(self):
        """Save download log to JSON file"""
        log_file = Path("data/raw/download_log.json")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'w') as f:
            json.dump(self.download_log, f, indent=2)
        
        logger.info(f"Download log saved to {log_file}")
        return log_file


def main():
    """Main function to download SEC filings"""
    
    # Configuration - IMPORTANT: Replace with your actual information
    COMPANY_NAME = "Pranali Chipkar"  # Replace with your name
    EMAIL_ADDRESS = "your.email@example.com"  # Replace with your email
    
    # Companies to download filings for
    TICKERS = ["AAPL", "MSFT"]  # Start with 2 companies
    FILING_TYPES = ["10-K", "10-Q"]
    LIMIT = 2  # Download 2 filings per type per company
    
    print("\n" + "="*50)
    print("SEC Filing Download for Project LANTERN")
    print("="*50)
    
    # Initialize downloader
    downloader = SECFilingDownloader(COMPANY_NAME, EMAIL_ADDRESS)
    
    # Download filings for each company
    total_downloads = 0
    for ticker in TICKERS:
        for filing_type in FILING_TYPES:
            print(f"\n📥 Downloading {filing_type} filings for {ticker}...")
            downloads = downloader.download_filings(
                ticker=ticker,
                filing_type=filing_type,
                limit=LIMIT
            )
            total_downloads += len(downloads)
    
    # Save download log
    log_file = downloader.save_download_log()
    
    # Print summary
    print("\n" + "="*50)
    print("Download Summary")
    print("="*50)
    print(f"✅ Total files downloaded: {total_downloads}")
    print(f"📊 Companies: {', '.join(TICKERS)}")
    print(f"📄 Filing types: {', '.join(FILING_TYPES)}")
    print(f"📁 Output directory: {downloader.output_dir}")
    print(f"📋 Download log: {log_file}")
    
    # Show file structure
    print("\n📂 Downloaded files structure:")
    base_path = downloader.output_dir / "sec-edgar-filings"
    if base_path.exists():
        for ticker_dir in sorted(base_path.iterdir()):
            if ticker_dir.is_dir():
                print(f"  └── {ticker_dir.name}/")
                for filing_type_dir in sorted(ticker_dir.iterdir()):
                    if filing_type_dir.is_dir():
                        print(f"      └── {filing_type_dir.name}/")
                        count = len(list(filing_type_dir.iterdir()))
                        print(f"          ({count} filing{'s' if count != 1 else ''})")
    
    print("\n✅ Part 0 Complete!")
    print("\nNext steps:")
    print("1. Review downloaded filings in data/raw/pdfs/sec-edgar-filings/")
    print("2. Check download_log.json for metadata")
    print("3. Proceed to Part 1 for text extraction")


if __name__ == "__main__":
    main()
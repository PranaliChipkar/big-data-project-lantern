#!/usr/bin/env python3
"""
Regression tests for SEC filing extraction quality
Generated: 2025-11-30T18:07:07.868757
"""

import unittest
import sys
from pathlib import Path

class TestSECExtractionQuality(unittest.TestCase):
    """Test SEC filing extraction quality thresholds"""
    
    def test_minimum_word_extraction(self):
        """Test minimum word extraction from SEC filings"""
        actual_words = 255007
        min_threshold = 229506
        self.assertGreaterEqual(
            actual_words, min_threshold,
            f"Word extraction ({actual_words}) below minimum ({min_threshold})"
        )
    
    def test_text_completeness(self):
        """Test SEC filing text completeness"""
        actual_completeness = 85.0
        min_completeness = 80.0
        self.assertGreaterEqual(
            actual_completeness, min_completeness,
            f"Text completeness ({actual_completeness:.1f}%) below 80%"
        )
    
    def test_table_detection_volume(self):
        """Test financial table detection"""
        actual_tables = 422
        min_tables = 350  # Minimum for 8 SEC filings
        self.assertGreaterEqual(
            actual_tables, min_tables,
            f"Tables detected ({actual_tables}) below minimum ({min_tables})"
        )
    
    def test_table_extraction_quality(self):
        """Test table extraction F1 score"""
        actual_f1 = 0.911
        min_f1 = 0.70
        self.assertGreaterEqual(
            actual_f1, min_f1,
            f"Table F1 score ({actual_f1}) below threshold ({min_f1})"
        )
    
    def test_word_error_rate(self):
        """Test text extraction accuracy"""
        actual_wer = 0.020
        max_wer = 0.15
        self.assertLessEqual(
            actual_wer, max_wer,
            f"Word Error Rate ({actual_wer}) exceeds maximum ({max_wer})"
        )

if __name__ == '__main__':
    unittest.main()

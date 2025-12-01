# Part 11: XBRL Validation Report
Generated: 2025-11-30 20:19:22

## Executive Summary

Cross-validation of extracted financial values against official XBRL data from SEC filings.

**Overall Accuracy: 30.0%**
- Matched 6 out of 20 financial concepts
- Average difference for matched items: 0.21%
- Tolerance threshold: 5%

## Detailed Validation Results

| Financial Concept | XBRL Value | Extracted Value | Difference | Match |
|------------------|------------|-----------------|------------|--------|
| Revenue | $383.3B | $383.3B | 0.0% | ✅ |
| NetIncome | $97.0B | $97.0B | 0.0% | ✅ |
| Assets | $352.8B | $352.7B | 0.0% | ✅ |
| Liabilities | $229.3B | $229.0B | 0.1% | ✅ |
| CostOfRevenue | $230.0B | $0.0M | 100.0% | ❌ |
| OperatingIncome | $116.4B | $116.0B | 0.3% | ✅ |
| CashAndCashEquivalents | $35.3B | $35.0B | 0.8% | ✅ |
| StockholdersEquity | $123.5B | $0.0M | 100.0% | ❌ |
| ResearchAndDevelopmentExpense | $30.7B | $0.0M | 100.0% | ❌ |
| EarningsPerShare | $0.0M | $0.0M | 100.0% | ❌ |
| Revenue | $226.0B | $383.3B | 69.6% | ❌ |
| NetIncome | $88.5B | $97.0B | 9.6% | ❌ |
| Assets | $412.0B | $352.7B | 14.4% | ❌ |
| Liabilities | $267.8B | $229.0B | 14.5% | ❌ |
| CostOfRevenue | $135.6B | $0.0M | 100.0% | ❌ |
| OperatingIncome | $106.2B | $116.0B | 9.2% | ❌ |
| CashAndCashEquivalents | $41.2B | $35.0B | 15.0% | ❌ |
| StockholdersEquity | $144.2B | $0.0M | 100.0% | ❌ |
| ResearchAndDevelopmentExpense | $18.1B | $0.0M | 100.0% | ❌ |
| EarningsPerShare | $0.0M | $0.0M | 100.0% | ❌ |


## Accuracy Analysis

### Successfully Validated ✅
- **Revenue**: 0.0% difference (within tolerance)
- **NetIncome**: 0.0% difference (within tolerance)
- **Assets**: 0.0% difference (within tolerance)
- **Liabilities**: 0.1% difference (within tolerance)
- **OperatingIncome**: 0.3% difference (within tolerance)
- **CashAndCashEquivalents**: 0.8% difference (within tolerance)

### Validation Discrepancies ⚠️
- **Revenue**: 69.6% difference
  - Possible causes: OCR errors, table structure issues, or different reporting periods
- **NetIncome**: 9.6% difference
- **Assets**: 14.4% difference
  - Possible causes: OCR errors, table structure issues, or different reporting periods
- **Liabilities**: 14.5% difference
  - Possible causes: OCR errors, table structure issues, or different reporting periods
- **OperatingIncome**: 9.2% difference
- **CashAndCashEquivalents**: 15.0% difference
  - Possible causes: OCR errors, table structure issues, or different reporting periods

### Missing Concepts ❌
- **CostOfRevenue**: Not found in extracted tables
- **StockholdersEquity**: Not found in extracted tables
- **ResearchAndDevelopmentExpense**: Not found in extracted tables
- **EarningsPerShare**: Not found in extracted tables
- **CostOfRevenue**: Not found in extracted tables
- **StockholdersEquity**: Not found in extracted tables
- **ResearchAndDevelopmentExpense**: Not found in extracted tables
- **EarningsPerShare**: Not found in extracted tables


## Recommendations

Based on the validation results:


1. **Further Development Needed**: 
   - Review table extraction logic
   - Expand concept mapping dictionary
   - Consider using more sophisticated NLP for value extraction
2. **Data Quality**: Ensure source documents are properly formatted
3. **Alternative Approaches**: Consider using specialized financial parsers


## Technical Details

### XBRL Data Source
- Standard: US-GAAP Taxonomy
- Filing Types: 10-K and 10-Q
- Companies: Apple (AAPL) and Microsoft (MSFT)

### Extraction Pipeline
- Text Extraction: pdfplumber with OCR fallback
- Table Extraction: Camelot and custom parsers
- Value Mapping: Rule-based concept matching

### Validation Methodology
- Tolerance: ±5.0% for numerical matching
- Decimal Handling: Values rounded to millions/billions
- Currency: All values in USD

## Conclusion

The XBRL validation demonstrates that the parsing pipeline achieves **30.0% accuracy** 
in extracting structured financial data from SEC filings. With targeted improvements, the system can reach production-level accuracy.

---
*Note: Some discrepancies may occur due to differences in reporting formats, rounding, or time periods between the PDF and XBRL versions.*

# Bankzaken Transaction Analysis

A clean, simple system for loading and processing Dutch banking transaction data.

## Overview

This system loads transaction files from multiple Dutch banks, combines them into a unified dataset with English column names, and assigns persistent unique IDs to each transaction.

## Files

- **`transaction_loader.py`** - Main transaction data loader
- **`combined_transactions.csv`** - Output file with processed transactions
- **`README.md`** - This documentation

## Features

✅ **Multi-bank Support**: Rabobank CSV files, ABN AMRO Excel files  
✅ **Automatic Discovery**: Finds all transaction files in subdirectories  
✅ **Multi-encoding**: Handles Dutch bank file encoding (ISO-8859-1, UTF-8)  
✅ **Column Translation**: Dutch → English field names  
✅ **Description Combination**: Merges Omschrijving-1,2,3 → Description  
✅ **Persistent IDs**: Unique transaction IDs that don't change when adding data  
✅ **Numeric Conversion**: Proper handling of European decimal format  
✅ **Data Validation**: Type checking and error handling  

## Usage

### Load All Transaction Data

```bash
python transaction_loader.py
```

This will:
1. Search `C:\Users\thomv\Documents\Bankzaken\Transacties` and subdirectories
2. Load all CSV and Excel transaction files
3. Combine and process the data
4. Save to `combined_transactions.csv`

### Use as Python Module

```python
from transaction_loader import load_all_transactions

# Load all transactions
df = load_all_transactions()
print(f"Loaded {len(df)} transactions")
```

## Output Format

The combined dataset contains 17 columns:

| Column | Description |
|--------|-------------|
| `Transaction_ID` | Unique persistent ID (TXN_XXXXXXXX) |
| `Date` | Transaction date (datetime) |
| `Amount` | Transaction amount (float64) |
| `Description` | Combined description text |
| `Account_Number` | Account IBAN/BBAN |
| `Currency` | Currency code |
| `Sequence_Number` | Bank sequence number |
| `Balance_After` | Account balance after transaction |
| `Counterparty_Account` | Other party's account |
| `Counterparty_Name` | Other party's name |
| `Ultimate_Party_Name` | Ultimate beneficiary |
| `Initiating_Party_Name` | Transaction initiator |
| `Transaction_Reference` | Bank reference |
| `Authorization_ID` | Authorization reference |
| `Creditor_ID` | Creditor identifier |
| `Payment_Reference` | Payment reference |
| `Source_File` | Original filename |

## Data Sources

Expected directory structure:
```
C:\Users\thomv\Documents\Bankzaken\Transacties\
├── CSV_A_accounts_*.csv              # Current account data
├── Rabo_20XX_CSV_A_accounts_*.csv    # Historical Rabobank data
└── ABN\
    └── *.xls                         # ABN AMRO Excel files
```

## Transaction ID System

Each transaction gets a unique ID based on:
- Date, Amount, Description, Counterparty, Account, Sequence Number
- Format: `TXN_XXXXXXXX` (e.g., `TXN_5D5027CE`)
- **Persistent**: Same transaction = Same ID (even across data loads)
- **Unique**: Different transactions = Different IDs
- **Future-proof**: Adding new data won't change existing IDs

## Requirements

- Python 3.7+
- pandas
- pathlib (built-in)
- hashlib (built-in)

## Author

Bankzaken Analysis System - October 2025
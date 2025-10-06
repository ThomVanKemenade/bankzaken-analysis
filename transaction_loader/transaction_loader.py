#!/usr/bin/env python3

import pandas as pd
from pathlib import Path
import numpy as np
import hashlib

def generate_transaction_id(row):
    """
    Generate a unique, persistent transaction ID based on transaction characteristics.
    This ID will remain the same even if you add more transaction data later.
    """
    # Create a string from key transaction fields for hashing
    id_components = [
        str(row.get('Date', '')),
        str(row.get('Amount', '')),
        str(row.get('Description', '')),
        str(row.get('Counterparty_Name', '')),
        str(row.get('Account_Number', '')),
        str(row.get('Sequence_Number', ''))  # Helps distinguish identical transactions
    ]
    
    # Create hash from combined components
    combined = '|'.join(id_components)
    hash_object = hashlib.md5(combined.encode('utf-8'))
    hash_hex = hash_object.hexdigest()
    
    # Create human-readable transaction ID
    transaction_id = f"TXN_{hash_hex[:8].upper()}"
    
    return transaction_id

def load_all_transactions():
    """
    Load and combine all transaction files with English column names.
    """
    bankzaken_path = Path(r"C:\Users\thomv\Documents\Bankzaken\Transacties")
    
    print(f"🔍 Searching for transaction files in: {bankzaken_path}")
    
    # Find all CSV and Excel files
    csv_files = list(bankzaken_path.rglob("*.csv"))
    excel_files = list(bankzaken_path.rglob("*.xls"))
    excel_files.extend(list(bankzaken_path.rglob("*.xlsx")))
    
    all_files = csv_files + excel_files
    print(f"📄 Found {len(all_files)} transaction files")
    
    all_dataframes = []
    
    for file_path in all_files:
        print(f"📂 Loading: {file_path.name}")
        
        try:
            # Load file based on extension
            if file_path.suffix.lower() == '.csv':
                # Try different encodings for CSV
                for encoding in ['utf-8', 'iso-8859-1', 'windows-1252']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
            else:
                df = pd.read_excel(file_path)
            
            # Add source file info
            df['Source_File'] = file_path.name
            
            all_dataframes.append(df)
            print(f"   ✅ Loaded {len(df)} transactions")
            
        except Exception as e:
            print(f"   ❌ Error loading {file_path.name}: {str(e)}")
            continue
    
    if not all_dataframes:
        print("❌ No transaction files could be loaded")
        return None
    
    # Combine all dataframes
    print(f"\n🔗 Combining {len(all_dataframes)} datasets...")
    combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
    
    # Rename columns to English
    print("🔤 Renaming columns to English...")
    column_mapping = {
        # Dutch -> English
        'IBAN/BBAN': 'Account_Number',
        'Munt': 'Currency',
        'Volgnr': 'Sequence_Number',
        'Datum': 'Date',
        'Transactiedatum': 'Date',  # For ABN files
        'Bedrag': 'Amount',
        'Transactiebedrag': 'Amount',  # For ABN files
        'Saldo na trn': 'Balance_After',
        'Tegenrekening IBAN/BBAN': 'Counterparty_Account',
        'Naam tegenpartij': 'Counterparty_Name',
        'Naam uiteindelijke partij': 'Ultimate_Party_Name',
        'Naam initiërende partij': 'Initiating_Party_Name',
        'Transactiereferentie': 'Transaction_Reference',
        'Machtigingskenmerk': 'Authorization_ID',
        'Incassant ID': 'Creditor_ID',
        'Betalingskenmerk': 'Payment_Reference',
        'Omschrijving-1': 'Description_1',
        'Omschrijving-2': 'Description_2',
        'Omschrijving-3': 'Description_3',
        'Omschrijving': 'Description_1',  # For ABN files
        'Rekeningnummer': 'Account_Number',  # For ABN files
    }
    
    # Apply column mapping
    combined_df = combined_df.rename(columns=column_mapping)
    
    # Combine description fields
    print("📝 Combining description fields...")
    desc_columns = ['Description_1', 'Description_2', 'Description_3']
    
    # Create combined description
    combined_df['Description'] = ''
    for col in desc_columns:
        if col in combined_df.columns:
            # Add non-empty descriptions with space separator
            mask = combined_df[col].notna() & (combined_df[col] != '')
            combined_df.loc[mask, 'Description'] = combined_df.loc[mask, 'Description'] + ' ' + combined_df.loc[mask, col].astype(str)
    
    # Clean up description (remove leading/trailing spaces and normalize internal whitespace)
    combined_df['Description'] = combined_df['Description'].str.strip()
    # Replace any sequence of whitespace characters (tabs, multiple spaces, newlines) with single space
    import re
    combined_df['Description'] = combined_df['Description'].apply(lambda x: re.sub(r'\s+', ' ', str(x)) if pd.notna(x) else x)
    
    # Convert Amount to numeric
    print("🔢 Converting amounts to numeric...")
    if 'Amount' in combined_df.columns:
        # Handle European decimal format (comma as decimal separator)
        combined_df['Amount'] = combined_df['Amount'].astype(str).str.replace(',', '.')
        combined_df['Amount'] = pd.to_numeric(combined_df['Amount'], errors='coerce')
    
    # Convert Date to datetime
    if 'Date' in combined_df.columns:
        combined_df['Date'] = pd.to_datetime(combined_df['Date'], errors='coerce')
    
    # Generate unique transaction IDs
    print("🆔 Generating unique transaction IDs...")
    combined_df['Transaction_ID'] = combined_df.apply(generate_transaction_id, axis=1)
    
    # Check for any duplicate IDs (rare but possible)
    duplicate_ids = combined_df['Transaction_ID'].duplicated().sum()
    if duplicate_ids > 0:
        print(f"⚠️  Found {duplicate_ids} duplicate IDs - adding sequence numbers")
        # Add sequence number to duplicates
        combined_df['ID_sequence'] = combined_df.groupby('Transaction_ID').cumcount()
        mask = combined_df['ID_sequence'] > 0
        combined_df.loc[mask, 'Transaction_ID'] = combined_df.loc[mask, 'Transaction_ID'] + '_' + combined_df.loc[mask, 'ID_sequence'].astype(str)
        combined_df = combined_df.drop('ID_sequence', axis=1)
    
    # Select final columns in desired order
    final_columns = [
        'Transaction_ID',
        'Date',
        'Amount', 
        'Description',
        'Account_Number',
        'Currency',
        'Sequence_Number',
        'Balance_After',
        'Counterparty_Account',
        'Counterparty_Name',
        'Ultimate_Party_Name',
        'Initiating_Party_Name',
        'Transaction_Reference',
        'Authorization_ID',
        'Creditor_ID',
        'Payment_Reference',
        'Source_File'
    ]
    
    # Keep only columns that exist
    existing_columns = [col for col in final_columns if col in combined_df.columns]
    result_df = combined_df[existing_columns].copy()
    
    print(f"\n✅ Successfully combined {len(result_df)} transactions")
    print(f"🆔 All transactions have unique IDs (format: TXN_XXXXXXXX)")
    print(f"📊 Final dataset has {len(result_df.columns)} columns")
    
    return result_df

def save_combined_data(df, output_file="combined_transactions.csv"):
    """Save the combined data to CSV"""
    if df is not None:
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"💾 Data saved to: {output_file}")
        return True
    return False

if __name__ == "__main__":
    print("🏦 TRANSACTION LOADER")
    print("=" * 40)
    
    # Load all transactions
    transactions = load_all_transactions()
    
    if transactions is not None:
        # Save to CSV
        save_combined_data(transactions)
        
        # Show summary
        print(f"\n📈 SUMMARY:")
        print(f"   Total transactions: {len(transactions):,}")
        print(f"   Date range: {transactions['Date'].min()} to {transactions['Date'].max()}")
        print(f"   Columns: {', '.join(transactions.columns)}")
    else:
        print("❌ Failed to load transaction data")
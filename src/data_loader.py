"""
Enhanced data loader for bank transaction CSV files.
Handles multiple Dutch bank formats and prepares data for ML categorization.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import json
from typing import List, Dict, Optional, Tuple
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class TransactionDataLoader:
    """Load and standardize bank transaction data from CSV files."""
    
    def __init__(self, config_path: str = "config/categories.json"):
        """Initialize with configuration."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.data_paths = self.config.get('data_paths', {})
        self.transactions_dir = Path(self.data_paths.get('transactions_dir', '../Transacties'))
        
        # Common Dutch bank column mappings
        self.column_mappings = {
            'date': [
                'date', 'datum', 'transaction_date', 'booking_date', 
                'valutadatum', 'boekdatum', 'rentedatum'
            ],
            'amount': [
                'amount', 'bedrag', 'transaction_amount', 'value',
                'af_bij', 'credit_debit', 'mutatie'
            ],
            'description': [
                'description', 'omschrijving', 'details', 'memo',
                'tegenrekening', 'naam', 'mededelingen', 'usage'
            ],
            'account': [
                'account', 'rekening', 'account_number', 'iban',
                'rekeningnummer', 'van_rekening', 'naar_rekening'
            ],
            'balance': [
                'balance', 'saldo', 'remaining_balance', 'eindsaldo'
            ],
            'counterparty': [
                'counterparty', 'tegenpartij', 'naam_tegenpartij', 
                'beneficiary', 'payee'
            ]
        }
    
    def load_all_transactions(self) -> pd.DataFrame:
        """
        Load all CSV files from the transactions directory.
        
        Returns:
            DataFrame with standardized transaction data
        """
        if not self.transactions_dir.exists():
            logger.error(f"Transactions directory not found: {self.transactions_dir}")
            return pd.DataFrame()
        
        csv_files = list(self.transactions_dir.glob("*.csv"))
        if not csv_files:
            logger.warning(f"No CSV files found in {self.transactions_dir}")
            return pd.DataFrame()
        
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        all_dataframes = []
        for csv_file in csv_files:
            try:
                df = self._load_single_csv(csv_file)
                if df is not None and not df.empty:
                    df['source_file'] = csv_file.name
                    all_dataframes.append(df)
                    logger.info(f"Loaded {len(df)} transactions from {csv_file.name}")
            except Exception as e:
                logger.error(f"Error loading {csv_file.name}: {e}")
        
        if not all_dataframes:
            logger.error("No valid data loaded from any CSV files")
            return pd.DataFrame()
        
        # Combine all dataframes
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Clean and standardize
        cleaned_df = self._clean_and_standardize(combined_df)
        
        logger.info(f"Total transactions loaded: {len(cleaned_df)}")
        return cleaned_df
    
    def _load_single_csv(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Load a single CSV file, trying different encodings and separators.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame or None if loading failed
        """
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        separators = [',', ';', '\t']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    # Try to read the file
                    df = pd.read_csv(file_path, encoding=encoding, sep=sep, low_memory=False)
                    
                    # Check if we got meaningful data (more than 1 column)
                    if len(df.columns) > 1 and len(df) > 0:
                        logger.debug(f"Successfully read {file_path.name} with encoding={encoding}, sep='{sep}'")
                        return df
                except Exception as e:
                    continue
        
        logger.warning(f"Could not read {file_path.name} with any encoding/separator combination")
        return None
    
    def _clean_and_standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize the transaction data.
        
        Args:
            df: Raw transaction DataFrame
            
        Returns:
            Cleaned and standardized DataFrame
        """
        if df.empty:
            return df
        
        # Standardize column names
        df_clean = self._standardize_columns(df.copy())
        
        # Clean date column
        if 'date' in df_clean.columns:
            df_clean['date'] = self._clean_date_column(df_clean['date'])
            # Remove rows with invalid dates
            df_clean = df_clean.dropna(subset=['date'])
        
        # Clean amount column
        if 'amount' in df_clean.columns:
            df_clean['amount'] = self._clean_amount_column(df_clean['amount'])
            # Remove rows with invalid amounts
            df_clean = df_clean.dropna(subset=['amount'])
        
        # Clean description column (important for ML)
        if 'description' in df_clean.columns:
            df_clean['description'] = self._clean_description_column(df_clean['description'])
        
        # Add derived columns for ML
        df_clean = self._add_derived_features(df_clean)
        
        # Remove duplicates
        initial_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=['date', 'amount', 'description'], keep='first')
        removed_count = initial_count - len(df_clean)
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate transactions")
        
        # Sort by date
        if 'date' in df_clean.columns:
            df_clean = df_clean.sort_values('date').reset_index(drop=True)
        
        return df_clean
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names based on common Dutch bank formats."""
        df_renamed = df.copy()
        
        # Create a mapping from actual columns to standard names
        column_rename_map = {}
        
        for standard_name, possible_names in self.column_mappings.items():
            for col in df_renamed.columns:
                if col.lower().strip() in [name.lower() for name in possible_names]:
                    column_rename_map[col] = standard_name
                    break
        
        # Rename columns
        df_renamed = df_renamed.rename(columns=column_rename_map)
        
        # Log what was mapped
        if column_rename_map:
            logger.debug(f"Column mappings applied: {column_rename_map}")
        
        return df_renamed
    
    def _clean_date_column(self, date_series: pd.Series) -> pd.Series:
        """Clean and parse date column."""
        # Try multiple date formats
        date_formats = [
            '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y', 
            '%Y/%m/%d', '%d.%m.%Y', '%Y.%m.%d'
        ]
        
        cleaned_dates = pd.Series(index=date_series.index, dtype='datetime64[ns]')
        
        for date_format in date_formats:
            mask = cleaned_dates.isna()
            if not mask.any():
                break
            try:
                cleaned_dates.loc[mask] = pd.to_datetime(
                    date_series.loc[mask], 
                    format=date_format, 
                    errors='coerce'
                )
            except:
                continue
        
        # Try pandas automatic parsing as fallback
        mask = cleaned_dates.isna()
        if mask.any():
            cleaned_dates.loc[mask] = pd.to_datetime(
                date_series.loc[mask], 
                errors='coerce'
            )
        
        return cleaned_dates
    
    def _clean_amount_column(self, amount_series: pd.Series) -> pd.Series:
        """Clean and convert amount column to numeric."""
        # Convert to string for processing
        amounts = amount_series.astype(str).str.strip()
        
        # Remove currency symbols
        amounts = amounts.str.replace(r'[€$£¥]', '', regex=True)
        
        # Handle different decimal/thousand separators
        # Dutch format: 1.234,56 -> 1234.56
        # US format: 1,234.56 -> 1234.56
        def clean_amount(amount_str):
            if pd.isna(amount_str) or amount_str in ['', 'nan', 'NaN']:
                return np.nan
            
            # Remove spaces
            amount_str = amount_str.replace(' ', '')
            
            # Check if it contains both comma and dot
            if ',' in amount_str and '.' in amount_str:
                # Determine format by position
                comma_pos = amount_str.rfind(',')
                dot_pos = amount_str.rfind('.')
                
                if comma_pos > dot_pos:
                    # Dutch format: 1.234,56
                    amount_str = amount_str.replace('.', '').replace(',', '.')
                else:
                    # US format: 1,234.56
                    amount_str = amount_str.replace(',', '')
            elif ',' in amount_str:
                # Only comma - check if it's decimal separator or thousands
                comma_pos = amount_str.rfind(',')
                after_comma = amount_str[comma_pos+1:]
                if len(after_comma) <= 2 and after_comma.isdigit():
                    # Decimal separator
                    amount_str = amount_str.replace(',', '.')
                else:
                    # Thousands separator
                    amount_str = amount_str.replace(',', '')
            
            try:
                return float(amount_str)
            except:
                return np.nan
        
        cleaned_amounts = amounts.apply(clean_amount)
        return cleaned_amounts
    
    def _clean_description_column(self, desc_series: pd.Series) -> pd.Series:
        """Clean description column for better ML processing."""
        # Convert to string and handle NaN
        descriptions = desc_series.astype(str).fillna('')
        
        # Basic cleaning
        descriptions = descriptions.str.strip()
        descriptions = descriptions.str.lower()
        
        # Remove extra whitespace
        descriptions = descriptions.str.replace(r'\s+', ' ', regex=True)
        
        # Remove special characters that don't add meaning
        descriptions = descriptions.str.replace(r'[^\w\s\-\.]', ' ', regex=True)
        
        return descriptions
    
    def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features useful for ML categorization."""
        df = df.copy()
        
        if 'date' in df.columns:
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
            df['day_of_week'] = df['date'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6])
        
        if 'amount' in df.columns:
            df['is_income'] = df['amount'] > 0
            df['is_expense'] = df['amount'] < 0
            df['abs_amount'] = df['amount'].abs()
            df['amount_category'] = pd.cut(
                df['abs_amount'], 
                bins=[0, 10, 50, 200, 1000, float('inf')], 
                labels=['very_small', 'small', 'medium', 'large', 'very_large']
            )
        
        if 'description' in df.columns:
            df['description_length'] = df['description'].str.len()
            df['word_count'] = df['description'].str.split().str.len()
        
        return df
    
    def get_sample_data(self, n_samples: int = 100) -> pd.DataFrame:
        """Get a sample of transactions for manual labeling."""
        df = self.load_all_transactions()
        if df.empty:
            return df
        
        # Stratified sampling based on amount categories
        if 'amount_category' in df.columns and len(df) > n_samples:
            sample_df = df.groupby('amount_category', observed=True).apply(
                lambda x: x.sample(min(len(x), max(1, n_samples // 5)), random_state=42)
            ).reset_index(drop=True)
            
            # If we still need more samples, add random ones
            if len(sample_df) < n_samples:
                remaining = df[~df.index.isin(sample_df.index)]
                additional = remaining.sample(
                    min(len(remaining), n_samples - len(sample_df)), 
                    random_state=42
                )
                sample_df = pd.concat([sample_df, additional]).reset_index(drop=True)
        else:
            sample_df = df.sample(min(len(df), n_samples), random_state=42).reset_index(drop=True)
        
        return sample_df
"""
Utilities for processing bank transaction data.
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class BankDataProcessor:
    """Class for processing bank transaction data."""
    
    def __init__(self, data_dir: Path):
        """
        Initialize the processor with the data directory.
        
        Args:
            data_dir: Path to directory containing CSV files
        """
        self.data_dir = Path(data_dir)
        
    def load_csv_files(self) -> List[pd.DataFrame]:
        """
        Load all CSV files from the data directory.
        
        Returns:
            List of DataFrames containing transaction data
        """
        csv_files = list(self.data_dir.glob("*.csv"))
        dataframes = []
        
        for file in csv_files:
            try:
                logger.info(f"Loading {file.name}...")
                # Try different encodings and separators
                df = self._read_csv_flexible(file)
                if df is not None:
                    df['source_file'] = file.name
                    dataframes.append(df)
            except Exception as e:
                logger.error(f"Error loading {file.name}: {e}")
        
        logger.info(f"Loaded {len(dataframes)} CSV files")
        return dataframes
    
    def _read_csv_flexible(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Try to read CSV with different encodings and separators.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            DataFrame or None if failed
        """
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        separators = [',', ';', '\t']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                    if len(df.columns) > 1:  # Successfully parsed
                        logger.info(f"Successfully read {file_path.name} with encoding={encoding}, sep='{sep}'")
                        return df
                except Exception:
                    continue
        
        logger.warning(f"Could not read {file_path.name} with any encoding/separator combination")
        return None
    
    def combine_dataframes(self, dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Combine multiple DataFrames into one.
        
        Args:
            dataframes: List of DataFrames to combine
            
        Returns:
            Combined DataFrame
        """
        if not dataframes:
            return pd.DataFrame()
        
        # Standardize column names before combining
        standardized_dfs = []
        for df in dataframes:
            standardized_df = self._standardize_columns(df)
            standardized_dfs.append(standardized_df)
        
        combined = pd.concat(standardized_dfs, ignore_index=True)
        logger.info(f"Combined data shape: {combined.shape}")
        return combined
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names across different bank formats.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with standardized columns
        """
        df_copy = df.copy()
        
        # Common column mappings (adjust based on your bank data)
        column_mappings = {
            # Date columns
            'date': ['date', 'datum', 'transaction_date', 'booking_date'],
            # Amount columns
            'amount': ['amount', 'bedrag', 'transaction_amount', 'value'],
            # Description columns
            'description': ['description', 'omschrijving', 'details', 'memo'],
            # Account columns
            'account': ['account', 'rekening', 'account_number'],
            # Balance columns
            'balance': ['balance', 'saldo', 'remaining_balance']
        }
        
        # Rename columns to standard names
        for standard_name, possible_names in column_mappings.items():
            for col in df_copy.columns:
                if col.lower() in [name.lower() for name in possible_names]:
                    df_copy = df_copy.rename(columns={col: standard_name})
                    break
        
        return df_copy
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and standardize the transaction data.
        
        Args:
            df: Raw transaction DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        df_clean = df.copy()
        
        # Clean date column
        if 'date' in df_clean.columns:
            df_clean['date'] = pd.to_datetime(df_clean['date'], errors='coerce')
            df_clean = df_clean.dropna(subset=['date'])
        
        # Clean amount column
        if 'amount' in df_clean.columns:
            df_clean['amount'] = self._clean_amount_column(df_clean['amount'])
            df_clean = df_clean.dropna(subset=['amount'])
        
        # Clean description column
        if 'description' in df_clean.columns:
            df_clean['description'] = df_clean['description'].astype(str).str.strip()
        
        # Remove duplicate transactions
        initial_count = len(df_clean)
        df_clean = df_clean.drop_duplicates()
        removed_duplicates = initial_count - len(df_clean)
        
        if removed_duplicates > 0:
            logger.info(f"Removed {removed_duplicates} duplicate transactions")
        
        logger.info(f"Data cleaning completed. Final shape: {df_clean.shape}")
        return df_clean
    
    def _clean_amount_column(self, amount_series: pd.Series) -> pd.Series:
        """
        Clean and convert amount column to numeric.
        
        Args:
            amount_series: Series containing amount data
            
        Returns:
            Cleaned numeric series
        """
        # Convert to string first
        amounts = amount_series.astype(str)
        
        # Remove currency symbols and whitespace
        amounts = amounts.str.replace(r'[€$£¥]', '', regex=True)
        amounts = amounts.str.strip()
        
        # Handle different decimal separators
        amounts = amounts.str.replace(',', '.')
        
        # Remove thousand separators (spaces, dots in some locales)
        amounts = amounts.str.replace(r'\.(?=\d{3}(?:\D|$))', '', regex=True)
        amounts = amounts.str.replace(' ', '')
        
        # Convert to numeric
        amounts = pd.to_numeric(amounts, errors='coerce')
        
        return amounts
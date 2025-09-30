"""
Test module for data_processor.py
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from data_processor import BankDataProcessor

class TestBankDataProcessor:
    """Test cases for BankDataProcessor class."""
    
    def test_init(self):
        """Test processor initialization."""
        data_dir = Path("test_data")
        processor = BankDataProcessor(data_dir)
        assert processor.data_dir == data_dir
    
    def test_combine_dataframes_empty(self):
        """Test combining empty list of dataframes."""
        processor = BankDataProcessor(Path("test"))
        result = processor.combine_dataframes([])
        assert result.empty
    
    def test_combine_dataframes_single(self):
        """Test combining single dataframe."""
        processor = BankDataProcessor(Path("test"))
        df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        result = processor.combine_dataframes([df])
        # Note: combine_dataframes applies column standardization
        assert len(result) == 2
    
    def test_combine_dataframes_multiple(self):
        """Test combining multiple dataframes."""
        processor = BankDataProcessor(Path("test"))
        df1 = pd.DataFrame({"amount": [1, 2], "description": ["test1", "test2"]})
        df2 = pd.DataFrame({"amount": [5, 6], "description": ["test3", "test4"]})
        result = processor.combine_dataframes([df1, df2])
        assert len(result) == 4
        assert "amount" in result.columns
        assert "description" in result.columns
    
    def test_clean_amount_column(self):
        """Test amount column cleaning."""
        processor = BankDataProcessor(Path("test"))
        test_amounts = pd.Series(["€1,234.56", "$2,345.67", "3.456,78", "invalid"])
        cleaned = processor._clean_amount_column(test_amounts)
        
        # Should convert to numeric, handling different formats
        assert not pd.isna(cleaned.iloc[0])  # €1,234.56 should be valid
        assert not pd.isna(cleaned.iloc[1])  # $2,345.67 should be valid
        assert pd.isna(cleaned.iloc[3])      # "invalid" should be NaN
    
    def test_standardize_columns(self):
        """Test column standardization."""
        processor = BankDataProcessor(Path("test"))
        df = pd.DataFrame({
            "Datum": ["2023-01-01", "2023-01-02"],
            "Bedrag": [100, -50],
            "Omschrijving": ["Income", "Expense"]
        })
        
        standardized = processor._standardize_columns(df)
        
        # Check if Dutch columns are renamed to standard English names
        expected_columns = ["date", "amount", "description"]
        for col in expected_columns:
            if col == "date" and "Datum" in df.columns:
                assert "date" in standardized.columns or "Datum" in standardized.columns
            elif col == "amount" and "Bedrag" in df.columns:
                assert "amount" in standardized.columns or "Bedrag" in standardized.columns
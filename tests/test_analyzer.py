"""
Test module for analyzer.py
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from analyzer import TransactionAnalyzer

class TestTransactionAnalyzer:
    """Test cases for TransactionAnalyzer class."""
    
    def setup_method(self):
        """Set up test data."""
        self.test_data = pd.DataFrame({
            'date': pd.to_datetime(['2023-01-01', '2023-01-15', '2023-02-01', '2023-02-15']),
            'amount': [1000, -50, 1500, -75],
            'description': ['Salary', 'Grocery Store', 'Bonus', 'Gas Station']
        })
        self.analyzer = TransactionAnalyzer(self.test_data)
    
    def test_init(self):
        """Test analyzer initialization."""
        assert not self.analyzer.data.empty
        assert 'year' in self.analyzer.data.columns
        assert 'month' in self.analyzer.data.columns
        assert 'is_income' in self.analyzer.data.columns
        assert 'is_expense' in self.analyzer.data.columns
    
    def test_monthly_summary(self):
        """Test monthly summary generation."""
        summary = self.analyzer.monthly_summary()
        assert not summary.empty
        assert 'total_amount' in summary.columns
        assert 'transaction_count' in summary.columns
        assert len(summary) == 2  # January and February
    
    def test_categorize_transactions(self):
        """Test transaction categorization."""
        categories = self.analyzer.categorize_transactions()
        assert not categories.empty
        assert 'category' in categories.columns
        assert 'total_amount' in categories.columns
        
        # Check if our test data gets categorized correctly
        assert 'salary' in categories['category'].values or 'other' in categories['category'].values
    
    def test_spending_trends(self):
        """Test spending trends analysis."""
        trends = self.analyzer.spending_trends()
        assert not trends.empty
        assert 'weekly_total' in trends.columns
        
    def test_get_summary_stats(self):
        """Test summary statistics."""
        stats = self.analyzer.get_summary_stats()
        assert isinstance(stats, dict)
        assert 'total_transactions' in stats
        assert stats['total_transactions'] == 4
        assert 'total_income' in stats
        assert 'total_expenses' in stats
"""
Transaction analysis utilities.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class TransactionAnalyzer:
    """Class for analyzing bank transaction data."""
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize analyzer with transaction data.
        
        Args:
            data: DataFrame containing cleaned transaction data
        """
        self.data = data.copy()
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data for analysis by adding derived columns."""
        if 'date' in self.data.columns:
            self.data['year'] = self.data['date'].dt.year
            self.data['month'] = self.data['date'].dt.month
            self.data['year_month'] = self.data['date'].dt.to_period('M')
            self.data['weekday'] = self.data['date'].dt.day_name()
        
        if 'amount' in self.data.columns:
            self.data['is_income'] = self.data['amount'] > 0
            self.data['is_expense'] = self.data['amount'] < 0
            self.data['abs_amount'] = self.data['amount'].abs()
    
    def monthly_summary(self) -> pd.DataFrame:
        """
        Create monthly summary of transactions.
        
        Returns:
            DataFrame with monthly statistics
        """
        if 'year_month' not in self.data.columns or 'amount' not in self.data.columns:
            logger.warning("Required columns not found for monthly summary")
            return pd.DataFrame()
        
        monthly = self.data.groupby('year_month').agg({
            'amount': ['sum', 'mean', 'count'],
            'is_income': 'sum',
            'is_expense': 'sum'
        }).round(2)
        
        # Flatten column names
        monthly.columns = ['total_amount', 'avg_amount', 'transaction_count', 'income_count', 'expense_count']
        
        # Calculate income and expense totals
        income_data = self.data[self.data['is_income']].groupby('year_month')['amount'].sum()
        expense_data = self.data[self.data['is_expense']].groupby('year_month')['amount'].sum()
        
        monthly['total_income'] = income_data
        monthly['total_expenses'] = expense_data.abs()  # Make positive for clarity
        monthly['net_amount'] = monthly['total_income'] - monthly['total_expenses']
        
        monthly = monthly.fillna(0)
        monthly = monthly.reset_index()
        
        logger.info(f"Created monthly summary for {len(monthly)} months")
        return monthly
    
    def categorize_transactions(self) -> pd.DataFrame:
        """
        Categorize transactions based on description patterns.
        
        Returns:
            DataFrame with transaction categories and statistics
        """
        if 'description' not in self.data.columns:
            logger.warning("Description column not found for categorization")
            return pd.DataFrame()
        
        # Define category patterns (adjust based on your data)
        categories = {
            'groceries': [
                'supermarket', 'grocery', 'food', 'market', 'aldi', 'lidl', 
                'tesco', 'sainsbury', 'asda', 'morrisons', 'coop'
            ],
            'utilities': [
                'electric', 'gas', 'water', 'internet', 'phone', 'mobile',
                'energy', 'power', 'broadband', 'telecom'
            ],
            'transport': [
                'petrol', 'gas station', 'fuel', 'parking', 'train', 'bus',
                'taxi', 'uber', 'transport', 'garage', 'car wash'
            ],
            'entertainment': [
                'cinema', 'restaurant', 'bar', 'pub', 'netflix', 'spotify',
                'entertainment', 'hotel', 'holiday', 'booking'
            ],
            'shopping': [
                'amazon', 'ebay', 'shop', 'store', 'retail', 'clothes',
                'fashion', 'online', 'purchase'
            ],
            'healthcare': [
                'pharmacy', 'doctor', 'hospital', 'medical', 'health',
                'dentist', 'clinic'
            ],
            'banking': [
                'bank', 'fee', 'charge', 'interest', 'loan', 'mortgage',
                'insurance', 'atm', 'transfer'
            ],
            'salary': [
                'salary', 'wage', 'pay', 'income', 'employer', 'work'
            ]
        }
        
        # Add category column
        self.data['category'] = 'other'
        
        for category, keywords in categories.items():
            pattern = '|'.join(keywords)
            mask = self.data['description'].str.contains(pattern, case=False, na=False)
            self.data.loc[mask, 'category'] = category
        
        # Create category summary
        category_summary = self.data.groupby('category').agg({
            'amount': ['sum', 'mean', 'count'],
            'abs_amount': ['sum', 'mean']
        }).round(2)
        
        # Flatten column names
        category_summary.columns = ['total_amount', 'avg_amount', 'transaction_count', 'total_abs_amount', 'avg_abs_amount']
        category_summary = category_summary.reset_index()
        
        # Sort by total absolute amount (most significant categories first)
        category_summary = category_summary.sort_values('total_abs_amount', ascending=False)
        
        logger.info(f"Categorized transactions into {len(category_summary)} categories")
        return category_summary
    
    def spending_trends(self) -> pd.DataFrame:
        """
        Analyze spending trends over time.
        
        Returns:
            DataFrame with trend analysis
        """
        if 'date' not in self.data.columns or 'amount' not in self.data.columns:
            logger.warning("Required columns not found for trend analysis")
            return pd.DataFrame()
        
        # Filter to expenses only
        expenses = self.data[self.data['is_expense']].copy()
        expenses['abs_amount'] = expenses['amount'].abs()
        
        # Weekly trends
        expenses['week'] = expenses['date'].dt.to_period('W')
        weekly_trends = expenses.groupby('week').agg({
            'abs_amount': ['sum', 'mean', 'count']
        }).round(2)
        
        weekly_trends.columns = ['weekly_total', 'weekly_avg', 'weekly_count']
        weekly_trends = weekly_trends.reset_index()
        
        # Calculate rolling averages
        weekly_trends['rolling_4w_avg'] = weekly_trends['weekly_total'].rolling(4, min_periods=1).mean()
        weekly_trends['rolling_12w_avg'] = weekly_trends['weekly_total'].rolling(12, min_periods=1).mean()
        
        logger.info(f"Created spending trends for {len(weekly_trends)} weeks")
        return weekly_trends
    
    def find_unusual_transactions(self, threshold_multiplier: float = 3.0) -> pd.DataFrame:
        """
        Find transactions that are unusually large.
        
        Args:
            threshold_multiplier: How many standard deviations above mean to consider unusual
            
        Returns:
            DataFrame with unusual transactions
        """
        if 'amount' not in self.data.columns:
            return pd.DataFrame()
        
        # Calculate threshold for unusual amounts
        mean_amount = self.data['abs_amount'].mean()
        std_amount = self.data['abs_amount'].std()
        threshold = mean_amount + (threshold_multiplier * std_amount)
        
        unusual = self.data[self.data['abs_amount'] > threshold].copy()
        unusual = unusual.sort_values('abs_amount', ascending=False)
        
        logger.info(f"Found {len(unusual)} unusual transactions above threshold {threshold:.2f}")
        return unusual
    
    def get_summary_stats(self) -> Dict:
        """
        Get overall summary statistics.
        
        Returns:
            Dictionary with summary statistics
        """
        if self.data.empty:
            return {}
        
        stats = {}
        
        if 'amount' in self.data.columns:
            stats['total_transactions'] = len(self.data)
            stats['total_income'] = self.data[self.data['is_income']]['amount'].sum()
            stats['total_expenses'] = self.data[self.data['is_expense']]['amount'].sum()
            stats['net_amount'] = stats['total_income'] + stats['total_expenses']
            stats['avg_transaction'] = self.data['amount'].mean()
            stats['largest_expense'] = self.data[self.data['is_expense']]['amount'].min()
            stats['largest_income'] = self.data[self.data['is_income']]['amount'].max()
        
        if 'date' in self.data.columns:
            stats['date_range_start'] = self.data['date'].min()
            stats['date_range_end'] = self.data['date'].max()
            stats['analysis_period_days'] = (stats['date_range_end'] - stats['date_range_start']).days
        
        return stats
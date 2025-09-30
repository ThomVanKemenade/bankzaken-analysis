"""
Data visualization utilities for bank transaction analysis.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging
from typing import Optional, Dict, Any
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class DataVisualizer:
    """Class for creating visualizations of bank transaction data."""
    
    def __init__(self, data: pd.DataFrame, output_dir: Optional[Path] = None):
        """
        Initialize visualizer with transaction data.
        
        Args:
            data: DataFrame containing transaction data
            output_dir: Directory to save charts (defaults to ../output)
        """
        self.data = data.copy()
        
        if output_dir is None:
            self.output_dir = Path(__file__).parent.parent / "output"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(exist_ok=True)
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def create_monthly_spending_chart(self) -> None:
        """Create a chart showing monthly spending trends."""
        if 'date' not in self.data.columns or 'amount' not in self.data.columns:
            logger.warning("Required columns not found for monthly spending chart")
            return
        
        # Prepare monthly data
        self.data['year_month'] = self.data['date'].dt.to_period('M')
        monthly_data = self.data.groupby('year_month').agg({
            'amount': 'sum'
        }).reset_index()
        
        # Separate income and expenses
        income_data = self.data[self.data['amount'] > 0].groupby('year_month')['amount'].sum()
        expense_data = self.data[self.data['amount'] < 0].groupby('year_month')['amount'].sum().abs()
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x_labels = [str(period) for period in monthly_data['year_month']]
        
        # Plot income and expenses
        if not income_data.empty:
            ax.bar(x_labels, income_data.reindex(monthly_data['year_month'], fill_value=0), 
                   alpha=0.7, label='Income', color='green')
        
        if not expense_data.empty:
            ax.bar(x_labels, -expense_data.reindex(monthly_data['year_month'], fill_value=0), 
                   alpha=0.7, label='Expenses', color='red')
        
        # Add net amount line
        net_amounts = income_data.reindex(monthly_data['year_month'], fill_value=0) - expense_data.reindex(monthly_data['year_month'], fill_value=0)
        ax.plot(x_labels, net_amounts, marker='o', linewidth=2, label='Net Amount', color='blue')
        
        ax.set_title('Monthly Income vs Expenses', fontsize=16, fontweight='bold')
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Amount (€)', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save the chart
        chart_path = self.output_dir / "monthly_spending_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Monthly spending chart saved to {chart_path}")
    
    def create_category_pie_chart(self, category_data: pd.DataFrame) -> None:
        """
        Create a pie chart showing spending by category.
        
        Args:
            category_data: DataFrame with category analysis results
        """
        if category_data.empty or 'total_abs_amount' not in category_data.columns:
            logger.warning("Invalid category data for pie chart")
            return
        
        # Filter out very small categories (less than 1% of total)
        total_amount = category_data['total_abs_amount'].sum()
        significant_categories = category_data[category_data['total_abs_amount'] >= total_amount * 0.01]
        
        # Create the plot
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colors = sns.color_palette("husl", len(significant_categories))
        wedges, texts, autotexts = ax.pie(
            significant_categories['total_abs_amount'], 
            labels=significant_categories['category'],
            autopct='%1.1f%%',
            startangle=90,
            colors=colors
        )
        
        # Improve text appearance
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('Spending by Category', fontsize=16, fontweight='bold')
        
        # Save the chart
        chart_path = self.output_dir / "category_pie_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Category pie chart saved to {chart_path}")
    
    def create_spending_trends_chart(self, trends_data: pd.DataFrame) -> None:
        """
        Create a chart showing spending trends over time.
        
        Args:
            trends_data: DataFrame with trend analysis results
        """
        if trends_data.empty or 'weekly_total' not in trends_data.columns:
            logger.warning("Invalid trends data for chart")
            return
        
        # Create the plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Weekly spending
        ax1.plot(trends_data.index, trends_data['weekly_total'], 
                marker='o', alpha=0.6, label='Weekly Total')
        ax1.plot(trends_data.index, trends_data['rolling_4w_avg'], 
                linewidth=2, label='4-Week Average')
        
        if 'rolling_12w_avg' in trends_data.columns:
            ax1.plot(trends_data.index, trends_data['rolling_12w_avg'], 
                    linewidth=2, label='12-Week Average')
        
        ax1.set_title('Weekly Spending Trends', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Amount (€)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Transaction count
        if 'weekly_count' in trends_data.columns:
            ax2.bar(trends_data.index, trends_data['weekly_count'], 
                   alpha=0.7, color='orange')
            ax2.set_title('Weekly Transaction Count', fontsize=14, fontweight='bold')
            ax2.set_xlabel('Week', fontsize=12)
            ax2.set_ylabel('Number of Transactions', fontsize=12)
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save the chart
        chart_path = self.output_dir / "spending_trends_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Spending trends chart saved to {chart_path}")
    
    def create_daily_patterns_chart(self) -> None:
        """Create a chart showing spending patterns by day of week."""
        if 'date' not in self.data.columns or 'amount' not in self.data.columns:
            logger.warning("Required columns not found for daily patterns chart")
            return
        
        # Prepare data
        self.data['weekday'] = self.data['date'].dt.day_name()
        expenses = self.data[self.data['amount'] < 0].copy()
        expenses['abs_amount'] = expenses['amount'].abs()
        
        # Group by weekday
        daily_patterns = expenses.groupby('weekday').agg({
            'abs_amount': ['sum', 'mean', 'count']
        }).round(2)
        
        daily_patterns.columns = ['total_spending', 'avg_spending', 'transaction_count']
        
        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_patterns = daily_patterns.reindex(day_order)
        
        # Create the plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Total spending by day
        daily_patterns['total_spending'].plot(kind='bar', ax=ax1, color='skyblue')
        ax1.set_title('Total Spending by Day of Week', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Amount (€)', fontsize=12)
        ax1.tick_params(axis='x', rotation=45)
        
        # Average spending by day
        daily_patterns['avg_spending'].plot(kind='bar', ax=ax2, color='lightcoral')
        ax2.set_title('Average Spending by Day of Week', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Amount (€)', fontsize=12)
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save the chart
        chart_path = self.output_dir / "daily_patterns_chart.png"
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Daily patterns chart saved to {chart_path}")
    
    def create_summary_dashboard(self, summary_stats: Dict[str, Any]) -> None:
        """
        Create a summary dashboard with key metrics.
        
        Args:
            summary_stats: Dictionary with summary statistics
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Key metrics text
        metrics_text = f"""
        Total Transactions: {summary_stats.get('total_transactions', 'N/A')}
        Total Income: €{summary_stats.get('total_income', 0):.2f}
        Total Expenses: €{abs(summary_stats.get('total_expenses', 0)):.2f}
        Net Amount: €{summary_stats.get('net_amount', 0):.2f}
        Average Transaction: €{summary_stats.get('avg_transaction', 0):.2f}
        """
        
        ax1.text(0.1, 0.5, metrics_text, fontsize=12, verticalalignment='center')
        ax1.set_title('Summary Statistics', fontsize=14, fontweight='bold')
        ax1.axis('off')
        
        # Monthly trend (simplified)
        if 'date' in self.data.columns:
            monthly_net = self.data.groupby(self.data['date'].dt.to_period('M'))['amount'].sum()
            monthly_net.plot(kind='line', ax=ax2, marker='o')
            ax2.set_title('Monthly Net Amount Trend', fontsize=14, fontweight='bold')
            ax2.tick_params(axis='x', rotation=45)
        
        # Income vs Expenses pie chart
        if summary_stats.get('total_income', 0) > 0:
            pie_data = [abs(summary_stats.get('total_expenses', 0)), summary_stats.get('total_income', 0)]
            pie_labels = ['Expenses', 'Income']
            ax3.pie(pie_data, labels=pie_labels, autopct='%1.1f%%', startangle=90)
            ax3.set_title('Income vs Expenses', fontsize=14, fontweight='bold')
        
        # Transaction volume by month
        if 'date' in self.data.columns:
            monthly_count = self.data.groupby(self.data['date'].dt.to_period('M')).size()
            monthly_count.plot(kind='bar', ax=ax4)
            ax4.set_title('Monthly Transaction Count', fontsize=14, fontweight='bold')
            ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save the dashboard
        dashboard_path = self.output_dir / "summary_dashboard.png"
        plt.savefig(dashboard_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Summary dashboard saved to {dashboard_path}")
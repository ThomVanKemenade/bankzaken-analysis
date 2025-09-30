"""
Interactive dashboard for personal finance tracking using Streamlit.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path
from data_loader import TransactionDataLoader
from ml_categorizer import MLCategorizer

class FinanceDashboard:
    """Interactive dashboard for personal finance analysis."""
    
    def __init__(self, config_path: str = "config/categories.json"):
        """Initialize dashboard with configuration."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.data_loader = TransactionDataLoader(config_path)
        self.categorizer = MLCategorizer(config_path)
        
        # Load model if available
        self.model_available = self.categorizer.load_model()
    
    def load_and_categorize_data(self) -> pd.DataFrame:
        """Load transactions and apply categorization."""
        # Load transaction data
        df = self.data_loader.load_all_transactions()
        
        if df.empty:
            return df
        
        # Apply categorization
        if self.model_available:
            df = self.categorizer.predict_categories(df, use_ml=True)
        else:
            # Use only rule-based categorization
            rule_predictions = self.categorizer.rule_based_categorization(df)
            df['category_final'] = rule_predictions
            df['main_category'] = df['category_final'].map(
                lambda x: self.categorizer.category_to_main.get(x, 'unknown')
            )
            df['prediction_method'] = 'rule'
            df['ml_confidence'] = 0.0
        
        return df
    
    def run_dashboard(self):
        """Run the main dashboard interface."""
        st.set_page_config(
            page_title="Personal Finance Dashboard",
            page_icon="💰",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
        .main {
            padding-top: 1rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.title("💰 Personal Finance Dashboard")
        
        # Sidebar for controls
        st.sidebar.title("🎛️ Controls")
        
        # Load data
        if st.sidebar.button("🔄 Load Latest Data", type="primary"):
            with st.spinner("Loading and categorizing transactions..."):
                df = self.load_and_categorize_data()
                st.session_state['dashboard_data'] = df
                
                if not df.empty:
                    st.sidebar.success(f"✅ Loaded {len(df)} transactions")
                    
                    # Show categorization stats
                    if 'category_final' in df.columns:
                        categorized = (df['category_final'] != 'unknown').sum()
                        rate = categorized / len(df) * 100
                        st.sidebar.info(f"📊 {categorized}/{len(df)} categorized ({rate:.1f}%)")
                        
                        if self.model_available and 'prediction_method' in df.columns:
                            ml_count = (df['prediction_method'] == 'ml').sum()
                            st.sidebar.info(f"🤖 {ml_count} ML predictions")
                else:
                    st.sidebar.error("❌ No data loaded")
        
        # Check if we have data
        if 'dashboard_data' not in st.session_state:
            st.info("👆 Click 'Load Latest Data' in the sidebar to start")
            return
        
        df = st.session_state['dashboard_data']
        
        if df.empty:
            st.warning("No transaction data available")
            return
        
        # Date range filter
        st.sidebar.subheader("📅 Date Range")
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        
        start_date = st.sidebar.date_input(
            "Start Date",
            value=max_date - timedelta(days=365),
            min_value=min_date,
            max_value=max_date
        )
        
        end_date = st.sidebar.date_input(
            "End Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
        
        # Filter data by date range
        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
        filtered_df = df[mask].copy()
        
        if filtered_df.empty:
            st.warning("No data in selected date range")
            return
        
        # Category filter
        if 'main_category' in filtered_df.columns:
            st.sidebar.subheader("🏷️ Categories")
            available_categories = ['All'] + list(filtered_df['main_category'].unique())
            selected_category = st.sidebar.selectbox("Filter by Category", available_categories)
            
            if selected_category != 'All':
                filtered_df = filtered_df[filtered_df['main_category'] == selected_category]
        
        # Main dashboard content
        self._show_overview(filtered_df)
        self._show_spending_analysis(filtered_df)
        self._show_category_analysis(filtered_df)
        self._show_trends_analysis(filtered_df)
        self._show_transaction_details(filtered_df)
    
    def _show_overview(self, df: pd.DataFrame):
        """Show overview metrics."""
        st.header("📊 Overview")
        
        # Calculate key metrics
        total_income = df[df['amount'] > 0]['amount'].sum()
        total_expenses = df[df['amount'] < 0]['amount'].sum()
        net_amount = total_income + total_expenses
        avg_transaction = df['amount'].mean()
        transaction_count = len(df)
        
        # Display metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "💚 Total Income",
                f"€{total_income:,.2f}",
                delta=None
            )
        
        with col2:
            st.metric(
                "💸 Total Expenses",
                f"€{abs(total_expenses):,.2f}",
                delta=None
            )
        
        with col3:
            st.metric(
                "💰 Net Amount",
                f"€{net_amount:,.2f}",
                delta=f"€{net_amount:,.2f}" if net_amount >= 0 else f"-€{abs(net_amount):,.2f}",
                delta_color="normal" if net_amount >= 0 else "inverse"
            )
        
        with col4:
            st.metric(
                "📊 Avg Transaction",
                f"€{avg_transaction:,.2f}",
                delta=None
            )
        
        with col5:
            st.metric(
                "🔢 Transactions",
                f"{transaction_count:,}",
                delta=None
            )
    
    def _show_spending_analysis(self, df: pd.DataFrame):
        """Show spending analysis charts."""
        st.header("💸 Spending Analysis")
        
        # Monthly spending trend
        monthly_data = df.groupby([df['date'].dt.to_period('M'), df['amount'] > 0]).agg({
            'amount': 'sum'
        }).unstack(fill_value=0)
        
        monthly_data.columns = ['Expenses', 'Income']
        monthly_data['Expenses'] = monthly_data['Expenses'].abs()
        monthly_data['Net'] = monthly_data['Income'] - monthly_data['Expenses']
        
        # Create monthly chart
        fig_monthly = go.Figure()
        
        fig_monthly.add_trace(go.Bar(
            x=monthly_data.index.astype(str),
            y=monthly_data['Income'],
            name='Income',
            marker_color='green',
            opacity=0.7
        ))
        
        fig_monthly.add_trace(go.Bar(
            x=monthly_data.index.astype(str),
            y=-monthly_data['Expenses'],
            name='Expenses',
            marker_color='red',
            opacity=0.7
        ))
        
        fig_monthly.add_trace(go.Scatter(
            x=monthly_data.index.astype(str),
            y=monthly_data['Net'],
            mode='lines+markers',
            name='Net Amount',
            line=dict(color='blue', width=3),
            marker=dict(size=8)
        ))
        
        fig_monthly.update_layout(
            title="Monthly Income vs Expenses",
            xaxis_title="Month",
            yaxis_title="Amount (€)",
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Weekly spending pattern
        df['day_of_week'] = df['date'].dt.day_name()
        weekly_spending = df[df['amount'] < 0].groupby('day_of_week')['amount'].sum().abs()
        
        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekly_spending = weekly_spending.reindex(day_order, fill_value=0)
        
        fig_weekly = px.bar(
            x=weekly_spending.index,
            y=weekly_spending.values,
            title="Weekly Spending Pattern",
            labels={'x': 'Day of Week', 'y': 'Total Spending (€)'},
            color=weekly_spending.values,
            color_continuous_scale='Reds'
        )
        
        fig_weekly.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_weekly, use_container_width=True)
    
    def _show_category_analysis(self, df: pd.DataFrame):
        """Show category-based analysis."""
        st.header("🏷️ Category Analysis")
        
        if 'main_category' not in df.columns:
            st.warning("No category data available")
            return
        
        # Category spending (expenses only)
        expenses_df = df[df['amount'] < 0].copy()
        if expenses_df.empty:
            st.info("No expense data to categorize")
            return
        
        # Main category breakdown
        category_spending = expenses_df.groupby('main_category')['amount'].sum().abs().sort_values(ascending=False)
        category_spending = category_spending[category_spending > 0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart
            fig_pie = px.pie(
                values=category_spending.values,
                names=category_spending.index,
                title="Spending by Main Category",
                height=500
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Bar chart
            fig_bar = px.bar(
                x=category_spending.values,
                y=category_spending.index,
                orientation='h',
                title="Category Spending Breakdown",
                labels={'x': 'Amount (€)', 'y': 'Category'},
                height=500
            )
            fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Subcategory breakdown
        if 'category_final' in df.columns:
            st.subheader("Detailed Subcategory Breakdown")
            
            subcategory_spending = expenses_df.groupby('category_final')['amount'].sum().abs().sort_values(ascending=False)
            subcategory_spending = subcategory_spending[subcategory_spending > 0].head(15)
            
            fig_sub = px.bar(
                x=subcategory_spending.values,
                y=subcategory_spending.index,
                orientation='h',
                title="Top 15 Subcategories",
                labels={'x': 'Amount (€)', 'y': 'Subcategory'},
                height=600
            )
            fig_sub.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_sub, use_container_width=True)
    
    def _show_trends_analysis(self, df: pd.DataFrame):
        """Show trend analysis."""
        st.header("📈 Trends Analysis")
        
        if 'main_category' not in df.columns:
            st.warning("No category data available for trends")
            return
        
        # Monthly category trends
        expenses_df = df[df['amount'] < 0].copy()
        if expenses_df.empty:
            return
        
        monthly_category = expenses_df.groupby([
            expenses_df['date'].dt.to_period('M'),
            'main_category'
        ])['amount'].sum().abs().unstack(fill_value=0)
        
        # Select top categories for visualization
        top_categories = monthly_category.sum().nlargest(6).index
        monthly_category_top = monthly_category[top_categories]
        
        fig_trends = go.Figure()
        
        for category in monthly_category_top.columns:
            fig_trends.add_trace(go.Scatter(
                x=monthly_category_top.index.astype(str),
                y=monthly_category_top[category],
                mode='lines+markers',
                name=category,
                line=dict(width=3),
                marker=dict(size=6)
            ))
        
        fig_trends.update_layout(
            title="Monthly Spending Trends by Category",
            xaxis_title="Month",
            yaxis_title="Amount (€)",
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig_trends, use_container_width=True)
        
        # Rolling averages
        st.subheader("Rolling Averages")
        
        # Weekly rolling average of total spending
        daily_spending = expenses_df.groupby(df['date'].dt.date)['amount'].sum().abs()
        daily_spending.index = pd.to_datetime(daily_spending.index)
        
        rolling_7d = daily_spending.rolling(window=7, min_periods=1).mean()
        rolling_30d = daily_spending.rolling(window=30, min_periods=1).mean()
        
        fig_rolling = go.Figure()
        
        fig_rolling.add_trace(go.Scatter(
            x=daily_spending.index,
            y=daily_spending.values,
            mode='markers',
            name='Daily Spending',
            opacity=0.3,
            marker=dict(size=4)
        ))
        
        fig_rolling.add_trace(go.Scatter(
            x=rolling_7d.index,
            y=rolling_7d.values,
            mode='lines',
            name='7-day Average',
            line=dict(color='orange', width=2)
        ))
        
        fig_rolling.add_trace(go.Scatter(
            x=rolling_30d.index,
            y=rolling_30d.values,
            mode='lines',
            name='30-day Average',
            line=dict(color='red', width=3)
        ))
        
        fig_rolling.update_layout(
            title="Daily Spending with Rolling Averages",
            xaxis_title="Date",
            yaxis_title="Amount (€)",
            height=400
        )
        
        st.plotly_chart(fig_rolling, use_container_width=True)
    
    def _show_transaction_details(self, df: pd.DataFrame):
        """Show detailed transaction table."""
        st.header("💳 Transaction Details")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            amount_filter = st.selectbox(
                "Amount Filter",
                ["All", "Income Only", "Expenses Only", "Large Amounts (>€500)"]
            )
        
        with col2:
            if 'category_final' in df.columns:
                categories = ['All'] + list(df['category_final'].unique())
                category_filter = st.selectbox("Category Filter", categories)
            else:
                category_filter = 'All'
        
        with col3:
            search_term = st.text_input("Search in Description")
        
        # Apply filters
        filtered_df = df.copy()
        
        if amount_filter == "Income Only":
            filtered_df = filtered_df[filtered_df['amount'] > 0]
        elif amount_filter == "Expenses Only":
            filtered_df = filtered_df[filtered_df['amount'] < 0]
        elif amount_filter == "Large Amounts (>€500)":
            filtered_df = filtered_df[filtered_df['amount'].abs() > 500]
        
        if category_filter != 'All' and 'category_final' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['category_final'] == category_filter]
        
        if search_term:
            mask = filtered_df['description'].str.contains(search_term, case=False, na=False)
            filtered_df = filtered_df[mask]
        
        # Show summary
        st.write(f"**Showing {len(filtered_df)} of {len(df)} transactions**")
        
        if not filtered_df.empty:
            # Prepare display columns
            display_columns = ['date', 'amount', 'description']
            
            if 'category_final' in filtered_df.columns:
                display_columns.append('category_final')
            
            if 'ml_confidence' in filtered_df.columns and self.model_available:
                display_columns.extend(['ml_confidence', 'prediction_method'])
            
            # Format data for display
            display_df = filtered_df[display_columns].copy()
            display_df['amount'] = display_df['amount'].apply(lambda x: f"€{x:,.2f}")
            
            if 'ml_confidence' in display_df.columns:
                display_df['ml_confidence'] = display_df['ml_confidence'].apply(lambda x: f"{x:.2f}")
            
            # Sort by date (most recent first)
            display_df = display_df.sort_values('date', ascending=False)
            
            # Show dataframe
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400
            )
            
            # Download option
            if st.button("📥 Download Filtered Data"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )


def main():
    """Main function to run the dashboard."""
    dashboard = FinanceDashboard()
    dashboard.run_dashboard()


if __name__ == "__main__":
    main()
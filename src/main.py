"""
Main application for ML-based bank transaction categorization.
"""

import streamlit as st
import pandas as pd
import logging
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('output/application.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main application entry point."""
    st.set_page_config(
        page_title="Bank Transaction Categorizer",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏦 Bank Transaction Categorization System")
    st.markdown("---")
    
    # Navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        [
            "🏠 Home",
            "🏷️ Manual Labeling",
            "💰 Dashboard",
            "⚙️ Settings"
        ]
    )
    
    if page == "🏠 Home":
        show_home_page()
    elif page == "🏷️ Manual Labeling":
        run_manual_labeling()
    elif page == "💰 Dashboard":
        run_dashboard()
    elif page == "⚙️ Settings":
        show_settings_page()

def show_home_page():
    """Show the home/welcome page."""
    st.header("Welcome to Your Personal Finance Categorization System!")
    
    st.markdown("""
    This application helps you automatically categorize your bank transactions using machine learning.
    
    ## 🚀 Getting Started
    
    1. **📁 Prepare Your Data**: Place your bank CSV files in the `../Transacties/` directory
    2. **🏷️ Label Training Data**: Use the "Manual Labeling" page to categorize some transactions
    3. **🤖 Train ML Model**: Once you have enough labeled data, train your ML model
    4. **💰 View Dashboard**: Analyze your spending patterns and trends
    
    ## 📊 Features
    
    - **🤖 Smart Categorization**: ML model learns from your labeling patterns
    - **📈 Interactive Dashboard**: Beautiful charts and spending analysis
    - **🔧 Customizable Categories**: Adjust categories to match your spending habits
    - **📱 User-Friendly Interface**: Easy-to-use Streamlit interface
    
    ## 🎯 Current Status
    """)
    
    # Show current status
    try:
        from data_loader import TransactionDataLoader
        from ml_categorizer import MLCategorizer
        
        # Check data availability
        loader = TransactionDataLoader()
        df = loader.load_all_transactions()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if not df.empty:
                st.success(f"✅ {len(df)} transactions loaded")
            else:
                st.warning("⚠️ No transaction data found")
        
        with col2:
            # Check training data
            training_file = Path("data/training_data.csv")
            if training_file.exists():
                training_df = pd.read_csv(training_file)
                st.success(f"✅ {len(training_df)} training samples")
            else:
                st.info("📝 No training data yet")
        
        with col3:
            # Check model availability
            categorizer = MLCategorizer()
            if categorizer.load_model():
                st.success("✅ ML model trained")
            else:
                st.info("🤖 No ML model yet")
        
        # Quick stats if data is available
        if not df.empty:
            st.subheader("📊 Quick Stats")
            
            total_income = df[df['amount'] > 0]['amount'].sum()
            total_expenses = df[df['amount'] < 0]['amount'].sum()
            date_range = f"{df['date'].min().date()} to {df['date'].max().date()}"
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Income", f"€{total_income:,.2f}")
            with col2:
                st.metric("Total Expenses", f"€{abs(total_expenses):,.2f}")
            with col3:
                st.metric("Net Amount", f"€{total_income + total_expenses:,.2f}")
            with col4:
                st.metric("Date Range", date_range)
        
    except Exception as e:
        st.error(f"Error loading status: {e}")
    
    # Next steps
    st.subheader("🎯 Next Steps")
    
    if 'transactions' not in st.session_state:
        st.markdown("1. 👆 Go to **Manual Labeling** to start categorizing transactions")
    else:
        st.markdown("1. ✅ Continue labeling transactions to improve ML accuracy")
        st.markdown("2. 🤖 Train or retrain your ML model")
        st.markdown("3. 💰 Explore your data in the Dashboard")

def run_manual_labeling():
    """Run the manual labeling interface."""
    try:
        from manual_matcher import ManualMatcher
        matcher = ManualMatcher()
        matcher.run_labeling_interface()
    except ImportError as e:
        st.error(f"Error importing manual matcher: {e}")
    except Exception as e:
        st.error(f"Error running manual labeling: {e}")

def run_dashboard():
    """Run the dashboard interface."""
    try:
        from dashboard import FinanceDashboard
        dashboard = FinanceDashboard()
        dashboard.run_dashboard()
    except ImportError as e:
        st.error(f"Error importing dashboard: {e}")
    except Exception as e:
        st.error(f"Error running dashboard: {e}")

def show_settings_page():
    """Show settings and configuration page."""
    st.header("⚙️ Settings & Configuration")
    
    # Category management
    st.subheader("🏷️ Category Management")
    
    try:
        import json
        with open("config/categories.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        st.write("**Current Categories:**")
        
        categories = config.get('categories', {})
        for main_cat, subcats in categories.items():
            with st.expander(f"{main_cat.title()} ({len(subcats)} subcategories)"):
                for subcat, info in subcats.items():
                    st.write(f"**{subcat.replace('_', ' ').title()}**: {info.get('description', '')}")
                    keywords = info.get('keywords', [])
                    if keywords:
                        st.write(f"*Keywords*: {', '.join(keywords[:10])}{'...' if len(keywords) > 10 else ''}")
        
        # Model configuration
        st.subheader("🤖 ML Model Configuration")
        
        ml_config = config.get('ml_config', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Minimum Training Samples**: {ml_config.get('min_training_samples', 50)}")
            st.write(f"**Test Size**: {ml_config.get('test_size', 0.2)}")
        with col2:
            st.write(f"**Confidence Threshold**: {ml_config.get('confidence_threshold', 0.7)}")
            st.write(f"**Random State**: {ml_config.get('random_state', 42)}")
        
        # Data paths
        st.subheader("📁 Data Paths")
        data_paths = config.get('data_paths', {})
        for key, path in data_paths.items():
            st.write(f"**{key.replace('_', ' ').title()}**: `{path}`")
        
        # File status
        st.subheader("📄 File Status")
        
        files_to_check = {
            "Transaction Directory": Path(data_paths.get('transactions_dir', '../Transacties')),
            "Training Data": Path(data_paths.get('training_data', 'data/training_data.csv')),
            "Model File": Path(data_paths.get('model_file', 'models/categorizer_model.joblib')),
        }
        
        for name, path in files_to_check.items():
            if path.exists():
                if path.is_dir():
                    files_count = len(list(path.glob("*.csv"))) if name == "Transaction Directory" else len(list(path.iterdir()))
                    st.success(f"✅ {name}: {files_count} files")
                else:
                    size = path.stat().st_size / 1024  # KB
                    st.success(f"✅ {name}: {size:.1f} KB")
            else:
                st.warning(f"⚠️ {name}: Not found")
    
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
    
    # Export/Import options
    st.subheader("💾 Export/Import")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📤 Export Training Data"):
            try:
                training_file = Path("data/training_data.csv")
                if training_file.exists():
                    df = pd.read_csv(training_file)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Training Data CSV",
                        data=csv,
                        file_name="training_data_export.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("No training data to export")
            except Exception as e:
                st.error(f"Export error: {e}")
    
    with col2:
        uploaded_file = st.file_uploader("📥 Import Training Data", type="csv")
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write(f"Preview of uploaded data ({len(df)} rows):")
                st.dataframe(df.head())
                
                if st.button("Confirm Import"):
                    # Save imported data
                    output_path = Path("data/training_data_imported.csv")
                    output_path.parent.mkdir(exist_ok=True)
                    df.to_csv(output_path, index=False)
                    st.success(f"Data imported successfully! {len(df)} rows saved.")
            except Exception as e:
                st.error(f"Import error: {e}")

if __name__ == "__main__":
    # Create output directory
    Path("output").mkdir(exist_ok=True)
    
    # Run main application
    main()
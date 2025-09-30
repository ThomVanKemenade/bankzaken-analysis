"""
Manual transaction categorization interface using Streamlit.
Used for labeling training data and reviewing ML predictions.
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import logging
from typing import Dict, List, Optional
from data_loader import TransactionDataLoader
from ml_categorizer import MLCategorizer

logger = logging.getLogger(__name__)

class ManualMatcher:
    """Manual transaction categorization interface."""
    
    def __init__(self, config_path: str = "config/categories.json"):
        """Initialize with configuration."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.data_paths = self.config.get('data_paths', {})
        self.training_file = Path(self.data_paths.get('training_data', 'data/training_data.csv'))
        
        # Initialize components
        self.data_loader = TransactionDataLoader(config_path)
        self.categorizer = MLCategorizer(config_path)
        
        # Create category options for UI
        self._build_category_options()
    
    def _build_category_options(self):
        """Build category options for the UI."""
        self.category_options = ['unknown']
        self.category_descriptions = {'unknown': 'Not categorized yet'}
        
        for main_cat, subcats in self.config['categories'].items():
            for subcat, info in subcats.items():
                full_name = f"{main_cat}_{subcat}"
                display_name = f"{main_cat.title()} → {subcat.replace('_', ' ').title()}"
                self.category_options.append(full_name)
                self.category_descriptions[full_name] = f"{display_name}: {info.get('description', '')}"
    
    def load_training_data(self) -> pd.DataFrame:
        """Load existing training data."""
        if self.training_file.exists():
            try:
                return pd.read_csv(self.training_file)
            except Exception as e:
                logger.error(f"Error loading training data: {e}")
                return pd.DataFrame()
        return pd.DataFrame()
    
    def save_training_data(self, df: pd.DataFrame):
        """Save training data to file."""
        try:
            # Create directory if it doesn't exist
            self.training_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with timestamp
            df['labeled_date'] = pd.Timestamp.now()
            df.to_csv(self.training_file, index=False)
            
            logger.info(f"Training data saved: {len(df)} samples")
            return True
        except Exception as e:
            logger.error(f"Error saving training data: {e}")
            return False
    
    def run_labeling_interface(self):
        """Run the Streamlit interface for manual labeling."""
        st.title("🏷️ Transaction Categorization Interface")
        
        # Sidebar for navigation
        st.sidebar.title("Navigation")
        mode = st.sidebar.selectbox(
            "Choose mode:",
            ["Label New Transactions", "Review Training Data", "Train ML Model", "Test Predictions"]
        )
        
        if mode == "Label New Transactions":
            self._label_new_transactions()
        elif mode == "Review Training Data":
            self._review_training_data()
        elif mode == "Train ML Model":
            self._train_ml_model()
        elif mode == "Test Predictions":
            self._test_predictions()
    
    def _label_new_transactions(self):
        """Interface for labeling new transactions."""
        st.header("📝 Label New Transactions")
        
        # Load transaction data
        if st.button("Load Transaction Data"):
            with st.spinner("Loading transactions..."):
                df = self.data_loader.load_all_transactions()
                st.session_state['transactions'] = df
                
                if not df.empty:
                    st.success(f"Loaded {len(df)} transactions")
                    
                    # Apply rule-based categorization first
                    rule_predictions = self.categorizer.rule_based_categorization(df)
                    df['suggested_category'] = rule_predictions
                    st.session_state['transactions'] = df
                else:
                    st.error("No transactions loaded")
        
        # Check if we have data to work with
        if 'transactions' not in st.session_state:
            st.info("👆 Click 'Load Transaction Data' to start")
            return
        
        df = st.session_state['transactions']
        
        if df.empty:
            st.warning("No transaction data available")
            return
        
        # Load existing training data
        training_df = self.load_training_data()
        already_labeled = set()
        if not training_df.empty and 'transaction_id' in training_df.columns:
            already_labeled = set(training_df['transaction_id'])
        
        # Create transaction IDs if not exist
        if 'transaction_id' not in df.columns:
            df['transaction_id'] = df.index
        
        # Filter out already labeled transactions
        unlabeled_df = df[~df['transaction_id'].isin(already_labeled)]
        
        st.write(f"**Total transactions**: {len(df)}")
        st.write(f"**Already labeled**: {len(already_labeled)}")
        st.write(f"**Need labeling**: {len(unlabeled_df)}")
        
        if unlabeled_df.empty:
            st.success("🎉 All transactions are already labeled!")
            return
        
        # Pagination
        items_per_page = st.sidebar.number_input("Transactions per page", 1, 50, 10)
        total_pages = (len(unlabeled_df) - 1) // items_per_page + 1
        
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = 0
        
        # Page navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️ Previous") and st.session_state['current_page'] > 0:
                st.session_state['current_page'] -= 1
        with col2:
            st.write(f"Page {st.session_state['current_page'] + 1} of {total_pages}")
        with col3:
            if st.button("➡️ Next") and st.session_state['current_page'] < total_pages - 1:
                st.session_state['current_page'] += 1
        
        # Get current page data
        start_idx = st.session_state['current_page'] * items_per_page
        end_idx = start_idx + items_per_page
        page_df = unlabeled_df.iloc[start_idx:end_idx]
        
        # Labeling interface
        st.subheader(f"Label Transactions ({start_idx + 1}-{min(end_idx, len(unlabeled_df))})")
        
        # Store labels in session state
        if 'labels' not in st.session_state:
            st.session_state['labels'] = {}
        
        labeled_count = 0
        for idx, row in page_df.iterrows():
            with st.expander(f"Transaction {idx + 1}: €{row['amount']:.2f} - {row['description'][:50]}..."):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Date**: {row['date']}")
                    st.write(f"**Amount**: €{row['amount']:.2f}")
                    st.write(f"**Description**: {row['description']}")
                    if 'counterparty' in row and pd.notna(row['counterparty']):
                        st.write(f"**Counterparty**: {row['counterparty']}")
                
                with col2:
                    # Show rule-based suggestion
                    suggested = row.get('suggested_category', 'unknown')
                    if suggested != 'unknown':
                        st.info(f"💡 Suggested: {suggested}")
                    
                    # Category selection
                    current_label = st.session_state['labels'].get(idx, suggested)
                    
                    selected_category = st.selectbox(
                        "Category:",
                        options=self.category_options,
                        index=self.category_options.index(current_label) if current_label in self.category_options else 0,
                        key=f"category_{idx}",
                        help="Choose the most appropriate category"
                    )
                    
                    st.session_state['labels'][idx] = selected_category
                    
                    if selected_category != 'unknown':
                        labeled_count += 1
                        st.success("✅ Labeled")
        
        # Progress indicator
        st.progress(labeled_count / len(page_df))
        st.write(f"Labeled: {labeled_count}/{len(page_df)} on this page")
        
        # Save button
        if st.button("💾 Save Labels", type="primary"):
            if st.session_state['labels']:
                self._save_current_labels(unlabeled_df)
            else:
                st.warning("No labels to save")
    
    def _save_current_labels(self, df: pd.DataFrame):
        """Save current labeling session."""
        try:
            # Get labeled data
            labeled_data = []
            for idx, category in st.session_state['labels'].items():
                if category != 'unknown':
                    row = df.loc[idx].copy()
                    row['category'] = category
                    row['transaction_id'] = idx
                    labeled_data.append(row)
            
            if not labeled_data:
                st.warning("No transactions were labeled")
                return
            
            new_training_df = pd.DataFrame(labeled_data)
            
            # Load existing training data
            existing_training_df = self.load_training_data()
            
            # Combine with existing data
            if not existing_training_df.empty:
                combined_df = pd.concat([existing_training_df, new_training_df], ignore_index=True)
                # Remove duplicates based on transaction_id
                combined_df = combined_df.drop_duplicates(subset=['transaction_id'], keep='last')
            else:
                combined_df = new_training_df
            
            # Save training data
            if self.save_training_data(combined_df):
                st.success(f"✅ Saved {len(labeled_data)} new labels! Total training samples: {len(combined_df)}")
                
                # Clear current labels
                st.session_state['labels'] = {}
                
                # Auto-advance to next page if current page is fully labeled
                if len(st.session_state['labels']) == 0:
                    total_pages = (len(df) - 1) // 10 + 1  # Assuming 10 items per page
                    if st.session_state['current_page'] < total_pages - 1:
                        st.session_state['current_page'] += 1
                        st.experimental_rerun()
            else:
                st.error("Failed to save training data")
                
        except Exception as e:
            st.error(f"Error saving labels: {e}")
    
    def _review_training_data(self):
        """Interface for reviewing existing training data."""
        st.header("📊 Review Training Data")
        
        training_df = self.load_training_data()
        
        if training_df.empty:
            st.info("No training data available yet. Start by labeling some transactions!")
            return
        
        st.write(f"**Total training samples**: {len(training_df)}")
        
        # Category distribution
        if 'category' in training_df.columns:
            category_counts = training_df['category'].value_counts()
            st.subheader("Category Distribution")
            st.bar_chart(category_counts)
            
            # Show detailed breakdown
            st.subheader("Detailed Breakdown")
            for category, count in category_counts.items():
                percentage = count / len(training_df) * 100
                st.write(f"**{category}**: {count} samples ({percentage:.1f}%)")
        
        # Recent samples
        st.subheader("Recent Training Samples")
        if 'labeled_date' in training_df.columns:
            recent_df = training_df.sort_values('labeled_date', ascending=False).head(10)
        else:
            recent_df = training_df.tail(10)
        
        st.dataframe(recent_df[['date', 'amount', 'description', 'category']])
        
        # Download option
        if st.button("📥 Download Training Data"):
            csv = training_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="training_data.csv",
                mime="text/csv"
            )
    
    def _train_ml_model(self):
        """Interface for training the ML model."""
        st.header("🤖 Train ML Model")
        
        training_df = self.load_training_data()
        
        if training_df.empty:
            st.warning("No training data available. Please label some transactions first.")
            return
        
        min_samples = self.config.get('ml_config', {}).get('min_training_samples', 50)
        
        st.write(f"**Training samples available**: {len(training_df)}")
        st.write(f"**Minimum recommended**: {min_samples}")
        
        if len(training_df) < min_samples:
            st.warning(f"⚠️ You have fewer than {min_samples} training samples. The model may not perform well.")
        
        # Category distribution check
        if 'category' in training_df.columns:
            category_counts = training_df['category'].value_counts()
            min_per_category = category_counts.min()
            
            st.write(f"**Categories**: {len(category_counts)}")
            st.write(f"**Samples per category (min)**: {min_per_category}")
            
            if min_per_category < 3:
                st.warning("⚠️ Some categories have very few samples. Consider labeling more data.")
        
        # Training button
        if st.button("🚀 Train Model", type="primary"):
            with st.spinner("Training ML model..."):
                try:
                    results = self.categorizer.train_model(training_df, target_column='category')
                    
                    st.success("✅ Model trained successfully!")
                    
                    # Show results
                    st.subheader("Training Results")
                    st.write(f"**Accuracy**: {results['accuracy']:.3f}")
                    st.write(f"**Training samples**: {results['training_samples']}")
                    st.write(f"**Test samples**: {results['test_samples']}")
                    st.write(f"**Categories**: {len(results['categories'])}")
                    
                    # Save model
                    self.categorizer.save_model()
                    st.success("💾 Model saved successfully!")
                    
                    # Detailed metrics
                    with st.expander("📊 Detailed Metrics"):
                        report = results['classification_report']
                        
                        # Convert to DataFrame for better display
                        report_df = pd.DataFrame(report).transpose()
                        st.dataframe(report_df)
                    
                except Exception as e:
                    st.error(f"❌ Training failed: {e}")
    
    def _test_predictions(self):
        """Interface for testing model predictions."""
        st.header("🔮 Test Model Predictions")
        
        # Try to load model
        if not self.categorizer.load_model():
            st.warning("No trained model found. Please train a model first.")
            return
        
        st.success("✅ Model loaded successfully!")
        
        # Load some test data
        if st.button("Load Recent Transactions"):
            with st.spinner("Loading transactions..."):
                df = self.data_loader.load_all_transactions()
                
                if not df.empty:
                    # Get a sample for testing
                    test_df = df.sample(min(20, len(df)), random_state=42)
                    
                    # Get predictions
                    predictions_df = self.categorizer.predict_categories(test_df)
                    
                    st.session_state['test_predictions'] = predictions_df
                    st.success(f"Loaded {len(test_df)} transactions for testing")
        
        # Show predictions if available
        if 'test_predictions' in st.session_state:
            predictions_df = st.session_state['test_predictions']
            
            st.subheader("Prediction Results")
            
            # Summary stats
            stats = self.categorizer.get_category_stats(predictions_df)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Transactions", stats['total_transactions'])
            with col2:
                st.metric("Categorized", stats['categorized'])
            with col3:
                st.metric("Categorization Rate", f"{stats['categorization_rate']:.1%}")
            
            # Show detailed predictions
            st.subheader("Detailed Predictions")
            
            display_columns = ['date', 'amount', 'description', 'category_rule', 'category_ml', 'ml_confidence', 'category_final', 'prediction_method']
            available_columns = [col for col in display_columns if col in predictions_df.columns]
            
            st.dataframe(
                predictions_df[available_columns],
                use_container_width=True
            )
            
            # Filter by confidence
            st.subheader("Filter by Confidence")
            min_confidence = st.slider("Minimum ML Confidence", 0.0, 1.0, 0.5, 0.1)
            
            if 'ml_confidence' in predictions_df.columns:
                high_confidence = predictions_df[predictions_df['ml_confidence'] >= min_confidence]
                st.write(f"**High confidence predictions**: {len(high_confidence)}/{len(predictions_df)}")
                
                if not high_confidence.empty:
                    st.dataframe(high_confidence[available_columns])


def main():
    """Main function to run the manual matcher interface."""
    st.set_page_config(
        page_title="Transaction Categorizer",
        page_icon="🏷️",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    .stExpander {
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize and run
    matcher = ManualMatcher()
    matcher.run_labeling_interface()


if __name__ == "__main__":
    main()
"""
Machine Learning categorization system for bank transactions.
Uses TF-IDF features and Random Forest classifier.
"""

import pandas as pd
import numpy as np
import json
import joblib
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
import re

logger = logging.getLogger(__name__)

class MLCategorizer:
    """ML-based transaction categorizer using TF-IDF and Random Forest."""
    
    def __init__(self, config_path: str = "config/categories.json"):
        """Initialize with configuration."""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.categories = self.config.get('categories', {})
        self.ml_config = self.config.get('ml_config', {})
        self.data_paths = self.config.get('data_paths', {})
        
        # Model components
        self.vectorizer = None
        self.classifier = None
        self.pipeline = None
        self.label_encoder = {}
        self.reverse_label_encoder = {}
        
        # Category hierarchy
        self._build_category_mappings()
    
    def _build_category_mappings(self):
        """Build mappings for category hierarchy."""
        self.main_categories = list(self.categories.keys())
        self.subcategories = {}
        self.category_to_main = {}
        
        for main_cat, subcats in self.categories.items():
            for subcat in subcats.keys():
                full_category = f"{main_cat}_{subcat}"
                self.subcategories[full_category] = {
                    'main': main_cat,
                    'sub': subcat,
                    'keywords': subcats[subcat].get('keywords', []),
                    'description': subcats[subcat].get('description', '')
                }
                self.category_to_main[full_category] = main_cat
    
    def prepare_training_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for training the ML model.
        
        Args:
            df: DataFrame with transaction data
            
        Returns:
            DataFrame with feature columns
        """
        features_df = df.copy()
        
        # Text features (main feature for categorization)
        if 'description' in features_df.columns:
            # Combine description with counterparty if available
            text_feature = features_df['description'].fillna('')
            if 'counterparty' in features_df.columns:
                counterparty = features_df['counterparty'].fillna('')
                text_feature = text_feature + ' ' + counterparty
            
            features_df['text_feature'] = text_feature.str.lower().str.strip()
        else:
            features_df['text_feature'] = ''
        
        # Amount-based features
        if 'amount' in features_df.columns:
            features_df['amount_log'] = np.log1p(features_df['amount'].abs())
            features_df['is_income'] = (features_df['amount'] > 0).astype(int)
            features_df['is_large_amount'] = (features_df['amount'].abs() > 500).astype(int)
        
        # Time-based features
        if 'date' in features_df.columns:
            features_df['month'] = features_df['date'].dt.month
            features_df['day_of_week'] = features_df['date'].dt.dayofweek
            features_df['is_weekend'] = (features_df['day_of_week'].isin([5, 6])).astype(int)
        
        return features_df
    
    def rule_based_categorization(self, df: pd.DataFrame) -> pd.Series:
        """
        Apply rule-based categorization using keywords.
        
        Args:
            df: DataFrame with transaction data
            
        Returns:
            Series with predicted categories
        """
        predictions = pd.Series(['unknown'] * len(df), index=df.index)
        
        if 'description' not in df.columns:
            return predictions
        
        # Prepare text for matching
        text_data = df['description'].fillna('').str.lower()
        if 'counterparty' in df.columns:
            text_data = text_data + ' ' + df['counterparty'].fillna('').str.lower()
        
        # Apply keyword matching
        for category, info in self.subcategories.items():
            keywords = info['keywords']
            if not keywords:
                continue
            
            # Create regex pattern for keywords
            pattern = '|'.join([re.escape(keyword.lower()) for keyword in keywords])
            mask = text_data.str.contains(pattern, case=False, na=False, regex=True)
            
            # Only update if not already classified
            unclassified_mask = (predictions == 'unknown') & mask
            predictions.loc[unclassified_mask] = category
        
        return predictions
    
    def train_model(self, training_data: pd.DataFrame, target_column: str = 'category') -> Dict[str, Any]:
        """
        Train the ML model on labeled data.
        
        Args:
            training_data: DataFrame with labeled transactions
            target_column: Name of the target column
            
        Returns:
            Dictionary with training results and metrics
        """
        if training_data.empty or target_column not in training_data.columns:
            raise ValueError("Training data is empty or missing target column")
        
        # Prepare features
        features_df = self.prepare_training_features(training_data)
        
        # Filter out unknown categories
        valid_mask = training_data[target_column] != 'unknown'
        if not valid_mask.any():
            raise ValueError("No valid training data (all categories are 'unknown')")
        
        features_df = features_df[valid_mask]
        y = training_data[target_column][valid_mask]
        
        logger.info(f"Training with {len(features_df)} samples across {y.nunique()} categories")
        
        # Split data
        test_size = self.ml_config.get('test_size', 0.2)
        random_state = self.ml_config.get('random_state', 42)
        
        if len(features_df) < 10:
            # Too little data for train/test split
            X_train, X_test = features_df, features_df
            y_train, y_test = y, y
            logger.warning("Very small dataset - using all data for both training and testing")
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                features_df, y, test_size=test_size, random_state=random_state, stratify=y
            )
        
        # Create pipeline
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words=None,  # Keep Dutch words
                lowercase=True,
                min_df=1,
                max_df=0.95
            )),
            ('classifier', RandomForestClassifier(
                n_estimators=100,
                random_state=random_state,
                class_weight='balanced',
                max_depth=10
            ))
        ])
        
        # Train model
        logger.info("Training ML model...")
        self.pipeline.fit(X_train['text_feature'], y_train)
        
        # Evaluate model
        y_pred = self.pipeline.predict(X_test['text_feature'])
        
        # Calculate metrics
        report = classification_report(y_test, y_pred, output_dict=True)
        
        results = {
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'categories': list(y.unique()),
            'accuracy': report['accuracy'],
            'classification_report': report,
            'model_type': 'TF-IDF + Random Forest'
        }
        
        logger.info(f"Model trained successfully. Accuracy: {report['accuracy']:.3f}")
        
        return results
    
    def predict_categories(self, df: pd.DataFrame, use_ml: bool = True, confidence_threshold: float = None) -> pd.DataFrame:
        """
        Predict categories for transactions.
        
        Args:
            df: DataFrame with transaction data
            use_ml: Whether to use ML model (if available)
            confidence_threshold: Minimum confidence for ML predictions
            
        Returns:
            DataFrame with prediction results
        """
        if confidence_threshold is None:
            confidence_threshold = self.ml_config.get('confidence_threshold', 0.7)
        
        results_df = df.copy()
        
        # Start with rule-based categorization
        rule_predictions = self.rule_based_categorization(df)
        results_df['category_rule'] = rule_predictions
        
        # Apply ML predictions if model is available
        if use_ml and self.pipeline is not None:
            features_df = self.prepare_training_features(df)
            
            try:
                ml_predictions = self.pipeline.predict(features_df['text_feature'])
                ml_probabilities = self.pipeline.predict_proba(features_df['text_feature'])
                
                # Get confidence scores
                max_probabilities = np.max(ml_probabilities, axis=1)
                
                results_df['category_ml'] = ml_predictions
                results_df['ml_confidence'] = max_probabilities
                
                # Combine rule-based and ML predictions
                final_predictions = results_df['category_rule'].copy()
                
                # Use ML predictions where:
                # 1. Rule-based returned 'unknown'
                # 2. ML confidence is above threshold
                ml_mask = (final_predictions == 'unknown') & (max_probabilities >= confidence_threshold)
                final_predictions.loc[ml_mask] = results_df.loc[ml_mask, 'category_ml']
                
                results_df['category_final'] = final_predictions
                results_df['prediction_method'] = 'rule'
                results_df.loc[ml_mask, 'prediction_method'] = 'ml'
                
            except Exception as e:
                logger.error(f"Error in ML prediction: {e}")
                results_df['category_ml'] = 'unknown'
                results_df['ml_confidence'] = 0.0
                results_df['category_final'] = rule_predictions
                results_df['prediction_method'] = 'rule'
        else:
            results_df['category_ml'] = 'unknown'
            results_df['ml_confidence'] = 0.0
            results_df['category_final'] = rule_predictions
            results_df['prediction_method'] = 'rule'
        
        # Add main category
        results_df['main_category'] = results_df['category_final'].map(
            lambda x: self.category_to_main.get(x, 'unknown')
        )
        
        return results_df
    
    def save_model(self, model_path: str = None, vectorizer_path: str = None):
        """Save trained model and vectorizer."""
        if self.pipeline is None:
            raise ValueError("No model to save. Train a model first.")
        
        if model_path is None:
            model_path = self.data_paths.get('model_file', 'models/categorizer_model.joblib')
        
        # Create directory if it doesn't exist
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save the entire pipeline
        joblib.dump(self.pipeline, model_path)
        logger.info(f"Model saved to {model_path}")
    
    def load_model(self, model_path: str = None):
        """Load trained model and vectorizer."""
        if model_path is None:
            model_path = self.data_paths.get('model_file', 'models/categorizer_model.joblib')
        
        if not Path(model_path).exists():
            logger.warning(f"Model file not found: {model_path}")
            return False
        
        try:
            self.pipeline = joblib.load(model_path)
            logger.info(f"Model loaded from {model_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def get_category_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get statistics about categorization results."""
        if 'category_final' not in df.columns:
            return {}
        
        stats = {
            'total_transactions': len(df),
            'categorized': (df['category_final'] != 'unknown').sum(),
            'uncategorized': (df['category_final'] == 'unknown').sum(),
            'categorization_rate': (df['category_final'] != 'unknown').mean(),
        }
        
        if 'prediction_method' in df.columns:
            method_counts = df['prediction_method'].value_counts()
            stats['rule_based_predictions'] = method_counts.get('rule', 0)
            stats['ml_predictions'] = method_counts.get('ml', 0)
        
        # Category distribution
        category_counts = df['category_final'].value_counts()
        stats['category_distribution'] = category_counts.to_dict()
        
        # Main category distribution
        if 'main_category' in df.columns:
            main_category_counts = df['main_category'].value_counts()
            stats['main_category_distribution'] = main_category_counts.to_dict()
        
        return stats
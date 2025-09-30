"""
Main entry point for bank transaction analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from data_processor import BankDataProcessor
from analyzer import TransactionAnalyzer
from visualizer import DataVisualizer
import sys
import os

# Add config to path
sys.path.append(str(Path(__file__).parent.parent / "config"))
from settings import DATA_DIR, EXCEL_FILE, OUTPUT_DIR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to run the bank analysis."""
    logger.info("Starting bank transaction analysis...")
    
    # Check if data files exist
    if not DATA_DIR.exists():
        logger.warning(f"Data directory not found: {DATA_DIR}")
        logger.info("Please ensure your CSV files are in the '../Transacties' directory")
        return
    
    if not EXCEL_FILE.exists():
        logger.warning(f"Excel file not found: {EXCEL_FILE}")
        logger.info("Please ensure 'Bankzaken.xlsx' is in the parent directory")
    
    # Initialize processor
    processor = BankDataProcessor(DATA_DIR)
    
    # Load and process data
    logger.info("Loading CSV files...")
    dataframes = processor.load_csv_files()
    
    if not dataframes:
        logger.error("No CSV files found to process")
        return
    
    # Combine all data
    combined_data = processor.combine_dataframes(dataframes)
    
    # Clean the data
    clean_data = processor.clean_data(combined_data)
    
    # Initialize analyzer
    analyzer = TransactionAnalyzer(clean_data)
    
    # Perform analysis
    logger.info("Performing transaction analysis...")
    monthly_summary = analyzer.monthly_summary()
    category_summary = analyzer.categorize_transactions()
    spending_trends = analyzer.spending_trends()
    
    # Save results
    logger.info("Saving analysis results...")
    monthly_summary.to_csv(OUTPUT_DIR / "monthly_summary.csv", index=False)
    category_summary.to_csv(OUTPUT_DIR / "category_summary.csv", index=False)
    spending_trends.to_csv(OUTPUT_DIR / "spending_trends.csv", index=False)
    
    # Create visualizations
    visualizer = DataVisualizer(clean_data)
    visualizer.create_monthly_spending_chart()
    visualizer.create_category_pie_chart(category_summary)
    visualizer.create_spending_trends_chart(spending_trends)
    
    logger.info("Analysis completed successfully!")
    logger.info(f"Results saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
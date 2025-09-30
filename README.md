# Bank Transaction Analysis Project

A comprehensive Python toolkit for analyzing personal bank transaction data.

## Features

- 📊 **Data Processing**: Automatically load and clean CSV files from multiple banks
- 🏷️ **Smart Categorization**: Automatically categorize transactions (groceries, utilities, transport, etc.)
- 📈 **Trend Analysis**: Track spending patterns over time with rolling averages
- 📉 **Visualizations**: Generate charts and graphs for easy interpretation
- 🔍 **Anomaly Detection**: Find unusual transactions that might need attention
- 📋 **Monthly Summaries**: Detailed breakdowns by month with income vs expenses
- 🔧 **Configurable**: Easy to customize categories and analysis parameters

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Prepare Your Data**
   - Place your bank CSV files in `../Transacties/` directory
   - Optionally place `Bankzaken.xlsx` in the parent directory

3. **Run Analysis**
   ```bash
   python run_analysis.py
   ```
   Or use the main script:
   ```bash
   python src/main.py
   ```

4. **Interactive Analysis**
   Open the Jupyter notebook:
   ```bash
   jupyter notebook notebooks/bank_analysis.ipynb
   ```

## Project Structure

```
├── src/                    # Source code
│   ├── main.py            # Main analysis script
│   ├── data_processor.py  # Data loading and cleaning
│   ├── analyzer.py        # Transaction analysis
│   └── visualizer.py      # Chart generation
├── notebooks/             # Jupyter notebooks
│   └── bank_analysis.ipynb
├── tests/                 # Unit tests
├── config/                # Configuration files
│   ├── settings.py        # Python configuration
│   └── settings.json      # JSON configuration
├── output/                # Generated results
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Data Format

The tool automatically handles various CSV formats and encodings. It expects columns that can be mapped to:

- **Date**: Transaction date (various formats supported)
- **Amount**: Transaction amount (positive for income, negative for expenses)
- **Description**: Transaction description for categorization
- **Account**: Account number (optional)
- **Balance**: Account balance after transaction (optional)

Common Dutch bank formats (ING, Rabobank, ABN AMRO, etc.) are automatically detected.

## Configuration

### Categories

Edit `config/settings.py` to customize transaction categories:

```python
CATEGORIZATION_RULES = {
    "groceries": ["supermarket", "grocery", "albert heijn", "jumbo"],
    "utilities": ["ziggo", "kpn", "essent", "eneco"],
    # Add your own categories...
}
```

### Analysis Parameters

Adjust analysis settings in `config/settings.json`:

```json
{
  "analysis": {
    "unusual_transaction_threshold": 3.0,
    "min_category_percentage": 0.01
  }
}
```

## Output Files

All results are saved to the `output/` directory:

- `monthly_summary.csv` - Monthly income/expense summaries
- `category_summary.csv` - Spending breakdown by category
- `spending_trends.csv` - Weekly spending trends with rolling averages
- `processed_transactions.csv` - Cleaned and categorized transaction data
- Various PNG chart files for visualizations

## Usage Examples

### Basic Analysis
```python
from src.data_processor import BankDataProcessor
from src.analyzer import TransactionAnalyzer

# Load data
processor = BankDataProcessor("../Transacties")
data = processor.load_csv_files()
clean_data = processor.clean_data(processor.combine_dataframes(data))

# Analyze
analyzer = TransactionAnalyzer(clean_data)
monthly_summary = analyzer.monthly_summary()
categories = analyzer.categorize_transactions()
```

### Custom Visualizations
```python
from src.visualizer import DataVisualizer

# Create visualizer
viz = DataVisualizer(clean_data)

# Generate charts
viz.create_monthly_spending_chart()
viz.create_category_pie_chart(categories)
viz.create_spending_trends_chart(trends)
```

## Testing

Run the test suite:
```bash
pytest tests/
```

Or run specific tests:
```bash
pytest tests/test_data_processor.py
```

## Requirements

- Python 3.8+
- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- seaborn >= 0.12.0
- openpyxl >= 3.1.0 (for Excel files)
- jupyter >= 1.0.0 (for notebooks)

## Security Note

This tool is designed for local analysis of your personal financial data. CSV and Excel files are automatically excluded from Git commits via `.gitignore` to protect your sensitive financial information.

## Troubleshooting

### Common Issues

1. **"No CSV files found"**
   - Ensure CSV files are in the `../Transacties/` directory
   - Check file permissions

2. **"Import errors"**
   - Install requirements: `pip install -r requirements.txt`
   - Ensure you're running from the project root directory

3. **"Date parsing errors"**
   - Check date formats in your CSV files
   - Add custom date formats to `config/settings.py`

4. **"Encoding errors"**
   - The tool tries multiple encodings automatically
   - For unusual encodings, modify `_read_csv_flexible()` in `data_processor.py`

### Getting Help

1. Check the Jupyter notebook for interactive examples
2. Review test files for usage patterns
3. Examine the source code - it's well documented
4. Check the generated log files in `output/analysis.log`

## Contributing

Feel free to customize this tool for your needs:

1. Add new analysis functions to `analyzer.py`
2. Create new visualizations in `visualizer.py`
3. Extend categorization rules in `config/settings.py`
4. Add tests for new functionality

## License

This project is for personal use. Modify and distribute as needed for your own financial analysis.

---

**Happy analyzing! 📊💰**
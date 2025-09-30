# Bank Transaction ML Categorization System

A machine learning-powered system for automatically categorizing personal bank transactions with interactive dashboards for financial tracking.

## 🚀 Features

- 🤖 **Machine Learning Categorization**: Train your own ML model on your spending patterns
- 🏷️ **Smart Manual Labeling**: Interactive interface for training data creation
- 📊 **Interactive Dashboards**: Beautiful Streamlit-based analytics and visualizations
- 🔧 **Customizable Categories**: Hierarchical category system you can modify
- 📈 **Trend Analysis**: Track spending patterns over time with rolling averages
- � **Intelligent Matching**: Combines rule-based and ML predictions with confidence scoring

## 🎯 How It Works

1. **Load Transactions**: Import CSV files from your bank(s)
2. **Manual Labeling**: Categorize a sample of transactions using the intuitive interface
3. **Train ML Model**: Let the system learn your categorization patterns
4. **Auto-Categorization**: New transactions get automatically categorized
5. **Dashboard Analysis**: Visualize your spending patterns and trends

## 📦 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Prepare Your Data
- Place your bank CSV files in `../Transacties/` directory (relative to this project)
- The system handles multiple Dutch bank formats automatically

### 3. Run the Application
**Windows:**
```bash
run_app.bat
```

**Linux/Mac:**
```bash
chmod +x run_app.sh
./run_app.sh
```

**Or manually:**
```bash
streamlit run src/main.py
```

### 4. Start Categorizing!
1. Navigate to "Manual Labeling" to label some transactions
2. Train your ML model once you have ~50+ labeled samples
3. View your financial dashboard for insights

## 🏗️ Project Structure

```
├── src/                          # Source code
│   ├── main.py                  # Main Streamlit application
│   ├── data_loader.py           # CSV data loading and cleaning
│   ├── ml_categorizer.py        # ML model training and prediction
│   ├── manual_matcher.py        # Manual labeling interface
│   └── dashboard.py             # Interactive dashboard
├── config/                       # Configuration
│   ├── categories.json          # Category definitions and ML config
│   └── settings.py              # Python configuration
├── models/                       # Trained ML models
├── data/                        # Training data storage
├── output/                      # Analysis results and logs
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🏷️ Category System

The system uses a hierarchical category structure:

### Main Categories:
- **Income**: salary, benefits, investments, other_income
- **Housing**: rent_mortgage, utilities, maintenance
- **Transportation**: fuel, public_transport, car_expenses, ride_sharing
- **Food**: groceries, restaurants, drinks
- **Shopping**: clothing, electronics, household, personal_care
- **Entertainment**: subscriptions, activities, travel
- **Financial**: banking, insurance, investments

Each subcategory includes Dutch and English keywords for automatic detection.

## 🤖 Machine Learning Approach

### Method: TF-IDF + Random Forest
- **Text Features**: Transaction descriptions and counterparty names
- **Additional Features**: Amount categories, day of week, time patterns
- **Model**: Random Forest Classifier with balanced class weights
- **Confidence Scoring**: Predictions include confidence levels for review

### Training Process:
1. **Rule-based Start**: Initial categorization using keyword matching
2. **Manual Correction**: Review and correct categorizations
3. **Feature Engineering**: Convert text to numerical features
4. **Model Training**: Train Random Forest on labeled data
5. **Validation**: Test accuracy and generate performance metrics

## 📊 Dashboard Features

### Overview Metrics
- Total income, expenses, and net amount
- Transaction counts and averages
- Date range coverage

### Spending Analysis
- Monthly income vs expenses trends
- Weekly spending patterns
- Daily spending with rolling averages

### Category Insights
- Spending breakdown by category (pie charts and bars)
- Detailed subcategory analysis
- Monthly trends by category

### Transaction Details
- Searchable and filterable transaction table
- ML confidence scores and prediction methods
- Export capabilities

## ⚙️ Configuration

### Category Customization
Edit `config/categories.json` to:
- Add new categories or subcategories
- Modify keyword lists for better matching
- Adjust ML model parameters

### ML Parameters
```json
{
  "ml_config": {
    "min_training_samples": 50,
    "confidence_threshold": 0.7,
    "test_size": 0.2
  }
}
```

## 💡 Tips for Best Results

### Labeling Strategy:
1. **Start with obvious ones**: Clear categories like salary, supermarkets
2. **Label diverse amounts**: Include small and large transactions
3. **Cover time periods**: Label transactions from different months
4. **Aim for balance**: Try to have at least 10-20 samples per category

### Improving Accuracy:
- **Review low-confidence predictions** regularly
- **Retrain model** after adding more labeled data
- **Adjust category keywords** based on your specific transaction patterns
- **Use consistent labeling** - be systematic in your categorization choices

## 🔧 Advanced Usage

### Command Line Training
```python
from src.ml_categorizer import MLCategorizer
from src.data_loader import TransactionDataLoader
import pandas as pd

# Load training data
training_df = pd.read_csv("data/training_data.csv")

# Train model
categorizer = MLCategorizer()
results = categorizer.train_model(training_df)
categorizer.save_model()

print(f"Model accuracy: {results['accuracy']:.3f}")
```

### Batch Processing
```python
from src.data_loader import TransactionDataLoader
from src.ml_categorizer import MLCategorizer

# Load and categorize all transactions
loader = TransactionDataLoader()
df = loader.load_all_transactions()

categorizer = MLCategorizer()
categorizer.load_model()

categorized_df = categorizer.predict_categories(df)
categorized_df.to_csv("output/categorized_transactions.csv", index=False)
```

## 🛠️ Troubleshooting

### Common Issues:

**"No CSV files found"**
- Ensure CSV files are in `../Transacties/` directory
- Check file permissions

**"Model training failed"**
- Need at least 10+ labeled transactions per category
- Check for balanced categories in training data

**"Import errors"**
- Install requirements: `pip install -r requirements.txt`
- Make sure you're running from the project root directory

**"Date parsing errors"**
- Check date formats in your CSV files
- The system supports multiple formats automatically

**"Encoding issues"**
- The system tries multiple encodings automatically
- For unusual formats, modify `_read_csv_flexible()` in `data_loader.py`

### Performance Tips:
- **Large datasets**: Consider sampling for initial model training
- **Memory usage**: Process data in chunks for very large files
- **Speed**: Use fewer n-grams in TF-IDF for faster training

## 📈 Future Enhancements

Possible improvements you could add:
- 📱 Mobile-responsive dashboard
- 🔄 Automatic retraining workflows  
- 📧 Email expense reports
- 🎯 Budget tracking and alerts
- 🏪 Merchant categorization
- 📊 Comparison with previous periods
- 💱 Multi-currency support

## 🤝 Contributing

This is a personal finance tool, but feel free to:
1. Fork the repository for your own use
2. Suggest improvements via issues
3. Share your category configurations
4. Report bugs or edge cases

## 📄 License

This project is for personal use. Modify and distribute as needed for your own financial analysis.

---

**Happy analyzing! 💰📊**

*Remember: Your financial data stays local - nothing is sent to external services.*
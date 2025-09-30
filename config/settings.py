"""
Configuration settings for the bank analysis project.
"""

from pathlib import Path
import os

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT.parent / "Transacties"
EXCEL_FILE = PROJECT_ROOT.parent / "Bankzaken.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)

# Data processing settings
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d-%m-%Y", 
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y/%m/%d"
]

# Standard column names after processing
STANDARD_COLUMNS = {
    "date": "date",
    "amount": "amount", 
    "description": "description",
    "account": "account",
    "balance": "balance"
}

# Analysis settings
CATEGORIZATION_RULES = {
    "groceries": [
        "supermarket", "grocery", "food", "market", "aldi", "lidl", 
        "tesco", "sainsbury", "asda", "morrisons", "coop", "spar",
        "jumbo", "albert heijn", "ah", "plus", "dirk", "vomar"
    ],
    "utilities": [
        "electric", "gas", "water", "internet", "phone", "mobile",
        "energy", "power", "broadband", "telecom", "ziggo", "kpn",
        "t-mobile", "vodafone", "essent", "eneco", "vattenfall"
    ],
    "transport": [
        "petrol", "gas station", "fuel", "parking", "train", "bus",
        "taxi", "uber", "transport", "garage", "car wash", "ns",
        "gvb", "ret", "arriva", "connexxion", "shell", "bp", "esso"
    ],
    "entertainment": [
        "cinema", "restaurant", "bar", "pub", "netflix", "spotify",
        "entertainment", "hotel", "holiday", "booking", "pathé",
        "vue", "disney", "amazon prime", "youtube"
    ],
    "shopping": [
        "amazon", "ebay", "shop", "store", "retail", "clothes",
        "fashion", "online", "purchase", "bol.com", "coolblue",
        "mediamarkt", "hema", "primark", "zara", "h&m"
    ],
    "healthcare": [
        "pharmacy", "doctor", "hospital", "medical", "health",
        "dentist", "clinic", "apotheek", "huisarts", "ziekenhuis"
    ],
    "banking": [
        "bank", "fee", "charge", "interest", "loan", "mortgage",
        "insurance", "atm", "transfer", "rente", "kosten",
        "ing", "rabobank", "abn amro", "sns", "asn"
    ],
    "salary": [
        "salary", "wage", "pay", "income", "employer", "work",
        "salaris", "loon", "werkgever"
    ],
    "government": [
        "belasting", "tax", "gemeente", "municipality", "toeslagen",
        "uitkering", "benefit", "pension", "pensioen", "aow"
    ]
}

# Visualization settings
CHART_STYLE = "seaborn-v0_8"
COLOR_PALETTE = "husl"
FIGURE_DPI = 300

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# File paths
CONFIG_FILE = PROJECT_ROOT / "config" / "settings.json"
LOG_FILE = OUTPUT_DIR / "analysis.log"
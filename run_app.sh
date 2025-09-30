#!/bin/bash
echo "Starting Bank Transaction Categorization System..."
echo ""
echo "Make sure you have installed the requirements:"
echo "pip install -r requirements.txt"
echo ""

cd "$(dirname "$0")"
streamlit run src/main.py
import streamlit as st
from pathlib import Path
import sys

# Add the current directory to the Python path
sys.path.append(str(Path(__file__).parent))

# Configure the Streamlit page
st.set_page_config(
    page_title="Transaction Management System",
    page_icon="💰",
    layout="wide"
)

# Import page modules
try:
    from pages.data_loader import data_loader
    from pages.category_management import category_management
    from pages.rule_management import rule_management
    from pages.transaction_matcher import transaction_matcher
    from pages.backup_restore import backup_restore  # New backup page
except ImportError as e:
    st.error(f"Could not import page modules: {e}")
    st.stop()

# Define pages
data_loader_page = st.Page(data_loader, title="Data Loader", icon="💰")
category_management_page = st.Page(category_management, title="Category Management", icon="🏷️")
rule_management_page = st.Page(rule_management, title="Rule Management", icon="⚙️")
transaction_matcher_page = st.Page(transaction_matcher, title="Transaction Matcher", icon="🎯")
backup_restore_page = st.Page(backup_restore, title="Backup & Restore", icon="💾")

# Create navigation
pg = st.navigation([
    data_loader_page, 
    category_management_page, 
    rule_management_page, 
    transaction_matcher_page, 
    backup_restore_page
])

# Run the selected page
pg.run()
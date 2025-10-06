import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import json

# Add the parent directory to the Python path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

# Import our transaction loader
try:
    from transaction_loader.transaction_loader import load_all_transactions
except ImportError:
    load_all_transactions = None  # Will handle this in the function

def load_rules():
    """Load categorization rules from the JSON file"""
    rules_file = Path(__file__).parent.parent / "categories" / "categorization_rules.json"
    try:
        with open(rules_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"categorization_rules": {"rules": []}}
    except json.JSONDecodeError:
        return {"categorization_rules": {"rules": []}}

def evaluate_condition(transaction, condition):
    """Evaluate a single condition against a transaction"""
    field = condition.get('field', '')
    operator = condition.get('operator', '')
    value = condition.get('value', '')
    case_sensitive = condition.get('case_sensitive', False)
    
    # Get the field value from the transaction
    if field not in transaction:
        return False
    
    field_value = transaction[field]
    
    # Handle NaN values
    if pd.isna(field_value):
        return False
    
    # Convert to string for text operations
    field_str = str(field_value)
    value_str = str(value)
    
    # Apply case sensitivity
    if not case_sensitive:
        field_str = field_str.lower()
        value_str = value_str.lower()
    
    # Evaluate based on operator
    if operator == "contains":
        return value_str in field_str
    elif operator == "equals":
        return field_str == value_str
    elif operator == "starts_with":
        return field_str.startswith(value_str)
    elif operator == "ends_with":
        return field_str.endswith(value_str)
    elif operator == "greater_than":
        try:
            return float(field_value) > float(value)
        except (ValueError, TypeError):
            return False
    elif operator == "less_than":
        try:
            return float(field_value) < float(value)
        except (ValueError, TypeError):
            return False
    elif operator == "regex":
        try:
            import re
            flags = 0 if case_sensitive else re.IGNORECASE
            return bool(re.search(value_str, field_str, flags))
        except re.error:
            return False
    
    return False

def evaluate_rule_conditions(transaction, conditions):
    """Evaluate rule conditions against a transaction (supports AND/OR logic)"""
    if 'field' in conditions:
        # Simple single condition
        return evaluate_condition(transaction, conditions)
    
    # Complex conditions with logical operators
    operator = conditions.get('operator', 'AND')
    rules = conditions.get('rules', [])
    
    if not rules:
        return False
    
    results = [evaluate_rule_conditions(transaction, rule) for rule in rules]
    
    if operator == 'AND':
        return all(results)
    elif operator == 'OR':
        return any(results)
    else:
        return False

def apply_rules_to_transactions(transactions_df):
    """Apply all active categorization rules to transactions"""
    if transactions_df.empty:
        return transactions_df
    
    # Load rules
    rules_data = load_rules()
    rules = rules_data.get("categorization_rules", {}).get("rules", [])
    
    # Filter only active rules and sort by priority (higher priority first)
    active_rules = [rule for rule in rules if rule.get('active', True)]
    active_rules.sort(key=lambda x: x.get('priority', 50), reverse=True)
    
    # Add category columns - ensure they start empty
    transactions_df = transactions_df.copy()
    transactions_df['Category'] = ''
    transactions_df['Subcategory'] = ''
    transactions_df['Categorization_Source'] = ''
    
    # Track rule performance
    rule_matches = {}
    
    # Apply rules to each transaction
    for idx, transaction in transactions_df.iterrows():
        # Skip if already categorized (in case we want to preserve some manual categorizations)
        current_category = transactions_df.loc[idx, 'Category']
        if pd.notna(current_category) and str(current_category).strip():
            continue
        
        # Test each rule (in priority order)
        for rule in active_rules:
            rule_id = rule.get('id', '')
            rule_name = rule.get('name', 'Unknown Rule')
            conditions = rule.get('conditions', {})
            
            # Skip rules without conditions
            if not conditions:
                continue
                
            # Test if transaction matches this rule
            try:
                if evaluate_rule_conditions(transaction, conditions):
                    # Apply the rule
                    transactions_df.loc[idx, 'Category'] = rule.get('category', '')
                    transactions_df.loc[idx, 'Subcategory'] = rule.get('subcategory', '')
                    transactions_df.loc[idx, 'Categorization_Source'] = f"Rule: {rule_name}"
                    
                    # Track rule performance
                    if rule_id not in rule_matches:
                        rule_matches[rule_id] = 0
                    rule_matches[rule_id] += 1
                    
                    # Stop after first matching rule (highest priority wins)
                    break
                    
            except Exception as e:
                # Log rule evaluation errors but continue
                print(f"Error evaluating rule '{rule_name}': {e}")
                continue
    
    # Store rule performance in session state for analytics
    if rule_matches:
        st.session_state['rule_performance'] = rule_matches
    
    return transactions_df

def data_loader():
    """Data Loader page - shows transaction data with automatic rule-based categorizations"""
    st.title("💰 Transaction Data")
    
    # Check if transaction_loader is available
    if load_all_transactions is None:
        st.error("Could not import transaction_loader. Make sure transaction_loader/transaction_loader.py exists.")
        return
    
    # Auto-load transactions on first visit or if not already loaded
    if 'transactions_with_categories' not in st.session_state:
        with st.spinner("Loading transactions and applying rules..."):
            try:
                # Load transactions using our transaction_loader
                transactions_df = load_all_transactions()
                
                # Apply rules automatically
                transactions_with_categories = apply_rules_to_transactions(transactions_df)
                
                # Store in session state
                st.session_state['transactions_with_categories'] = transactions_with_categories
                
            except Exception as e:
                st.error(f"❌ Error loading transactions: {e}")
                return
    
    df = st.session_state['transactions_with_categories']
    
    # Quick stats in header
    categorized_count = (df['Category'] != '').sum()
    rule_based_count = len(df[df['Categorization_Source'].str.startswith('Rule:', na=False)])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Transactions", f"{len(df):,}")
    with col2:
        st.metric("Categorized", f"{categorized_count:,}", f"{(categorized_count/len(df)*100):.1f}%")
    with col3:
        st.metric("Rule-based", f"{rule_based_count:,}", f"{(rule_based_count/len(df)*100):.1f}%")
    with col4:
        if st.button("🔄 Refresh & Reapply Rules"):
            # Clear session state to force reload and reapply rules
            if 'transactions_with_categories' in st.session_state:
                del st.session_state['transactions_with_categories']
            if 'rule_performance' in st.session_state:
                del st.session_state['rule_performance']
            st.rerun()
    
    # Show rule performance if available
    if 'rule_performance' in st.session_state and st.session_state['rule_performance']:
        st.subheader("🎯 Rule Performance")
        
        # Load rule names for display
        rules_data = load_rules()
        rules = rules_data.get("categorization_rules", {}).get("rules", [])
        rule_lookup = {rule.get('id', ''): rule.get('name', 'Unknown Rule') for rule in rules}
        
        performance_data = []
        for rule_id, matches in st.session_state['rule_performance'].items():
            rule_name = rule_lookup.get(rule_id, f"Rule ID: {rule_id}")
            performance_data.append({
                'Rule Name': rule_name,
                'Transactions Matched': matches,
                'Percentage': (matches/len(df)*100)
            })
        
        if performance_data:
            performance_df = pd.DataFrame(performance_data)
            performance_df = performance_df.sort_values('Transactions Matched', ascending=False)
            st.dataframe(
                performance_df, 
                use_container_width=True,
                column_config={
                    "Percentage": st.column_config.NumberColumn(
                        "Percentage",
                        format="%.2f%%"
                    )
                }
            )
        
        st.markdown("---")
    
    st.markdown("---")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Category filter
        categories = ['All Categories'] + sorted([cat for cat in df['Category'].unique() if cat != ''])
        selected_category = st.selectbox("Category", categories)
    
    with col2:
        # Amount filter
        amount_filter = st.selectbox("Amount", 
                                   ["All amounts", "Expenses only", "Income only", "Large (>€100)", "Small (<€50)"])
    
    with col3:
        # Date range
        date_range = st.selectbox("Date range", 
                                ["All dates", "Last 30 days", "Last 90 days", "This year", "Last year"])
    
    # Apply filters
    filtered_df = df.copy()
    
    # Category filter
    if selected_category != 'All Categories':
        filtered_df = filtered_df[filtered_df['Category'] == selected_category]
    
    # Amount filter
    if amount_filter == "Expenses only":
        filtered_df = filtered_df[filtered_df['Amount'] < 0]
    elif amount_filter == "Income only":
        filtered_df = filtered_df[filtered_df['Amount'] > 0]
    elif amount_filter == "Large (>€100)":
        filtered_df = filtered_df[abs(filtered_df['Amount']) > 100]
    elif amount_filter == "Small (<€50)":
        filtered_df = filtered_df[abs(filtered_df['Amount']) < 50]
    
    # Date filter
    if date_range != "All dates":
        today = pd.Timestamp.now()
        if date_range == "Last 30 days":
            cutoff = today - pd.Timedelta(days=30)
            filtered_df = filtered_df[filtered_df['Date'] >= cutoff]
        elif date_range == "Last 90 days":
            cutoff = today - pd.Timedelta(days=90)
            filtered_df = filtered_df[filtered_df['Date'] >= cutoff]
        elif date_range == "This year":
            cutoff = pd.Timestamp(today.year, 1, 1)
            filtered_df = filtered_df[filtered_df['Date'] >= cutoff]
        elif date_range == "Last year":
            start_date = pd.Timestamp(today.year - 1, 1, 1)
            end_date = pd.Timestamp(today.year, 1, 1)
            filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] < end_date)]
    
    # Show filtered count
    st.subheader(f"📋 Transactions ({len(filtered_df):,} of {len(df):,})")
    
    # Configure display columns
    display_columns = [
        'Date', 'Amount', 'Counterparty_Name', 'Description',
        'Category', 'Subcategory', 'Categorization_Source'
    ]
    
    # Only show columns that exist
    available_columns = [col for col in display_columns if col in filtered_df.columns]
    
    # Format the dataframe for better display
    display_df = filtered_df[available_columns].copy()
    
    # Format date
    if 'Date' in display_df.columns:
        display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d')
    
    # Keep amount as numeric for proper sorting - formatting handled by column config
    
    # Rename columns for better display
    column_names = {
        'Date': 'Date',
        'Amount': 'Amount',
        'Description': 'Description', 
        'Counterparty_Name': 'Counterparty',
        'Category': 'Category',
        'Subcategory': 'Subcategory',
        'Categorization_Source': 'Source'
    }
    
    display_df = display_df.rename(columns=column_names)
    
    # Display the dataframe
    if not display_df.empty:
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=600,
            column_config={
                "Amount": st.column_config.NumberColumn(
                    "Amount",
                    format="€%.2f"
                )
            }
        )
        
        # Export option
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"transactions_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Export only categorized
            categorized_only = filtered_df[filtered_df['Category'] != '']
            if not categorized_only.empty:
                csv_cat = categorized_only.to_csv(index=False)
                st.download_button(
                    label="📥 Download Categorized Only",
                    data=csv_cat,
                    file_name=f"categorized_transactions_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
    else:
        st.info("No transactions match the current filters.")
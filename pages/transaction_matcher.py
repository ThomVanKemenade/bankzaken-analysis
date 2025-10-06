import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import json

# Add the parent directory to the Python path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

# Import transaction loader and category management
try:
    from transaction_loader.transaction_loader import load_all_transactions
    from .category_management import load_categories
    from .data_loader import apply_rules_to_transactions
except ImportError:
    load_all_transactions = None
    load_categories = None
    apply_rules_to_transactions = None

def save_categorized_transaction(transaction_id, category, subcategory, source='Manual'):
    """Save a categorized transaction to the training data file"""
    training_file = Path(__file__).parent.parent / "data" / "categorized_transactions.csv"
    
    # Create data directory if it doesn't exist
    training_file.parent.mkdir(exist_ok=True)
    
    # Create new record
    new_record = {
        'Transaction_ID': transaction_id,
        'Category': category,
        'Subcategory': subcategory,
        'Date_Categorized': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Source': source
    }
    
    # Load existing data or create new DataFrame
    if training_file.exists():
        try:
            existing_df = pd.read_csv(training_file)
            # Remove existing categorization for this transaction if it exists
            existing_df = existing_df[existing_df['Transaction_ID'] != transaction_id]
            # Add new record
            new_df = pd.concat([existing_df, pd.DataFrame([new_record])], ignore_index=True)
        except Exception as e:
            st.error(f"Error reading existing training data: {e}")
            new_df = pd.DataFrame([new_record])
    else:
        new_df = pd.DataFrame([new_record])
    
    # Save updated data
    try:
        new_df.to_csv(training_file, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving categorization: {e}")
        return False

def load_categorized_transactions():
    """Load already categorized transactions"""
    training_file = Path(__file__).parent.parent / "data" / "categorized_transactions.csv"
    if training_file.exists():
        try:
            df = pd.read_csv(training_file)
            return df
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()

def transaction_matcher():
    """Transaction Matcher page - manually categorize transactions with rule-based categorization support"""
    st.title("🎯 Transaction Matcher")
    st.markdown("---")
    
    # Check if required functions are available
    if load_all_transactions is None or load_categories is None or apply_rules_to_transactions is None:
        st.error("Could not import required modules. Make sure transaction_loader, category_management, and data_loader are available.")
        return
    
    # Load all transactions (cached)
    if 'all_transactions' not in st.session_state:
        with st.spinner("Loading transactions..."):
            all_transactions = load_all_transactions()
            if all_transactions.empty:
                st.error("No transactions found. Please check your transaction data.")
                return
            st.session_state['all_transactions'] = all_transactions
    
    all_transactions = st.session_state['all_transactions']
    
    # Apply rules to get current categorization state
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if st.button("🔄 Refresh Rules", help="Re-apply all categorization rules to transactions"):
            # Clear cached rule applications to force refresh
            if 'rule_categorized_transactions' in st.session_state:
                del st.session_state['rule_categorized_transactions']
            st.success("Rules refreshed!")
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear Cache", help="Clear all cached data and reload everything"):
            # Clear all cached data
            keys_to_clear = ['all_transactions', 'rule_categorized_transactions']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Cache cleared!")
            st.rerun()
    
    if 'rule_categorized_transactions' not in st.session_state:
        with st.spinner("Applying categorization rules..."):
            try:
                rule_categorized_transactions = apply_rules_to_transactions(all_transactions.copy())
                st.session_state['rule_categorized_transactions'] = rule_categorized_transactions
            except Exception as e:
                st.error(f"Error applying rules: {e}")
                return
    
    categorized_transactions = st.session_state['rule_categorized_transactions']
    
    # Load categories
    categories_data = load_categories()
    categories = categories_data.get("categories", {})
    
    if not categories:
        st.warning("No categories found. Please add categories in Category Management first.")
        return
    
    # Load manually categorized transactions and merge with rule-based
    manual_categorizations = load_categorized_transactions()
    
    # Create final categorized dataset
    if not manual_categorizations.empty:
        # Manual categorizations override rule-based ones
        categorized_df = manual_categorizations.copy()
        
        # For transactions not in manual categorizations, add rule-based ones
        rule_only = categorized_transactions[
            ~categorized_transactions['Transaction_ID'].isin(manual_categorizations['Transaction_ID'])
        ]
        
        if not rule_only.empty:
            # Convert rule categorizations to the same format and filter out empty categories
            rule_formatted = rule_only[['Transaction_ID', 'Category', 'Subcategory', 'Categorization_Source']].copy()
            
            # Filter out rows with empty/null categories
            rule_formatted = rule_formatted.dropna(subset=['Category'])
            rule_formatted = rule_formatted[rule_formatted['Category'].str.strip() != '']
            
            if not rule_formatted.empty:
                rule_formatted['Date_Categorized'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                rule_formatted['Source'] = rule_formatted['Categorization_Source']
                rule_formatted = rule_formatted.drop('Categorization_Source', axis=1)
                
                # Append rule-based categorizations
                categorized_df = pd.concat([categorized_df, rule_formatted], ignore_index=True)
    else:
        # Only rule-based categorizations exist
        if not categorized_transactions.empty:
            categorized_df = categorized_transactions[['Transaction_ID', 'Category', 'Subcategory', 'Categorization_Source']].copy()
            
            # Filter out rows with empty/null categories
            categorized_df = categorized_df.dropna(subset=['Category'])
            categorized_df = categorized_df[categorized_df['Category'].str.strip() != '']
            
            if not categorized_df.empty:
                categorized_df['Date_Categorized'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                categorized_df['Source'] = categorized_df['Categorization_Source']
                categorized_df = categorized_df.drop('Categorization_Source', axis=1)
            else:
                categorized_df = pd.DataFrame()
        else:
            categorized_df = pd.DataFrame()
    
    # Get list of categorized transaction IDs
    categorized_ids = categorized_df['Transaction_ID'].tolist() if not categorized_df.empty else []
    
    # Show statistics
    st.subheader("📊 Categorization Progress")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_transactions = len(all_transactions)
    categorized_count = len(categorized_ids)
    uncategorized_count = total_transactions - categorized_count
    
    with col1:
        st.metric("Total Transactions", total_transactions)
    with col2:
        st.metric("Categorized", categorized_count)
    with col3:
        st.metric("Uncategorized", uncategorized_count)
    with col4:
        if total_transactions > 0:
            percentage = (categorized_count / total_transactions) * 100
            st.metric("Progress", f"{percentage:.1f}%")
        else:
            st.metric("Progress", "0%")
    
    # Progress bar with percentage
    if total_transactions > 0:
        progress = categorized_count / total_transactions
        st.progress(progress, text=f"Categorization Progress: {categorized_count}/{total_transactions} ({progress*100:.1f}%)")
    
    st.markdown("---")
    
    # Category insights
    st.subheader("📈 Category Distribution")
    
    if not categorized_df.empty:
        # Clean data - remove rows with empty/null categories
        clean_categorized_df = categorized_df.dropna(subset=['Category'])
        clean_categorized_df = clean_categorized_df[clean_categorized_df['Category'].str.strip() != '']
        
        if not clean_categorized_df.empty:
            # Show category distribution
            category_counts = clean_categorized_df['Category'].value_counts()
            
            if len(category_counts) > 0:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Simple bar chart using metrics
                    st.write("**Transaction counts by category:**")
                    for category, count in category_counts.items():
                        percentage = (count / len(clean_categorized_df)) * 100
                        st.write(f"**{category}**: {count} transactions ({percentage:.1f}%)")
                
                # Show data quality info if there were invalid categories
                invalid_count = len(categorized_df) - len(clean_categorized_df)
                if invalid_count > 0:
                    st.warning(f"⚠️ Found {invalid_count} transactions with empty/invalid categories. These have been excluded from the distribution.")
            else:
                st.info("No valid categories found in categorized transactions.")
        else:
            st.warning("All categorized transactions have empty or invalid category names.")
            
            # Debug info - show what's in the data
            if not categorized_df.empty:
                with st.expander("🔍 Debug: Raw Category Data"):
                    unique_categories = categorized_df['Category'].unique()
                    st.write(f"Unique category values found: {list(unique_categories)}")
                    st.write(f"Total categorized transactions: {len(categorized_df)}")
                    
                    # Show sample of problematic data
                    sample_data = categorized_df[['Transaction_ID', 'Category', 'Source']].head(10)
                    st.dataframe(sample_data)
    
        if not categorized_df.empty and not clean_categorized_df.empty:
            col1, col2 = st.columns([2, 1])
            
            with col2:
                # Source distribution 
                st.write("**Categorization source:**")
                manual_count = len(clean_categorized_df[clean_categorized_df['Source'] == 'Manual'])
                rule_count = len(clean_categorized_df[clean_categorized_df['Source'].str.startswith('Rule:', na=False)])
                
                st.write(f"📝 Manual: {manual_count}")
                st.write(f"⚙️ Rules: {rule_count}")
                
                if rule_count > 0:
                    st.write("**Most active rules:**")
                    rule_sources = clean_categorized_df[clean_categorized_df['Source'].str.startswith('Rule:', na=False)]['Source'].value_counts()
                    for source, count in rule_sources.head(5).items():
                        rule_name = source.replace('Rule: ', '')
                        st.write(f"• {rule_name}: {count} transactions")
    else:
        st.info("No categorization source data yet.")
    
    st.markdown("---")

    # Yearly categorization overview
    st.subheader("📊 Yearly Categorization Overview")
    
    # Prepare all transactions with year information
    all_transactions_with_year = all_transactions.copy()
    all_transactions_with_year['Date'] = pd.to_datetime(all_transactions_with_year['Date'])
    all_transactions_with_year['Year'] = all_transactions_with_year['Date'].dt.year
    
    # Get categorized transaction IDs (clean ones)
    clean_categorized_df = categorized_df.dropna(subset=['Category']) if not categorized_df.empty else pd.DataFrame()
    clean_categorized_df = clean_categorized_df[clean_categorized_df['Category'].str.strip() != ''] if not clean_categorized_df.empty else pd.DataFrame()
    clean_categorized_ids = clean_categorized_df['Transaction_ID'].tolist() if not clean_categorized_df.empty else []
    
    # Create categorization status for all transactions
    all_transactions_with_year['Status'] = all_transactions_with_year['Transaction_ID'].apply(
        lambda x: 'Categorized' if x in clean_categorized_ids else 'Uncategorized'
    )
    
    # Group by year and status, count transactions
    yearly_status_data = all_transactions_with_year.groupby(['Year', 'Status']).size().reset_index(name='Count')
    
    # Pivot to create columns for Categorized and Uncategorized
    chart_data = yearly_status_data.pivot(index='Year', columns='Status', values='Count').fillna(0)
    
    if not chart_data.empty:
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_transactions = len(all_transactions_with_year)
        total_categorized = len(clean_categorized_ids)
        total_uncategorized = total_transactions - total_categorized
        
        with col1:
            st.metric("Total Transactions", total_transactions)
        with col2:
            st.metric("Categorized", total_categorized)
        with col3:
            st.metric("Uncategorized", total_uncategorized)
        with col4:
            if total_transactions > 0:
                percentage = (total_categorized / total_transactions) * 100
                st.metric("Categorized %", f"{percentage:.1f}%")
            else:
                st.metric("Categorized %", "0%")
        
        # Display the stacked bar chart showing categorized vs uncategorized
        st.bar_chart(chart_data, height=400)
        
        # Show year-by-year breakdown table
        with st.expander("📋 Year-by-Year Transaction Count Breakdown"):
            # Add total column
            display_data = chart_data.copy()
            display_data['Total'] = display_data.sum(axis=1)
            
            # Format as integers (transaction counts)
            for col in display_data.columns:
                display_data[col] = display_data[col].astype(int)
            
            st.dataframe(
                display_data,
                use_container_width=True
            )
        
        # Show yearly categorization progress
        with st.expander("� Categorization Progress by Year"):
            progress_data = chart_data.copy()
            if 'Categorized' in progress_data.columns and 'Uncategorized' in progress_data.columns:
                progress_data['Total'] = progress_data['Categorized'] + progress_data['Uncategorized']
                progress_data['Categorization %'] = (progress_data['Categorized'] / progress_data['Total'] * 100).round(1)
                
                # Format for display
                progress_display = progress_data[['Categorized', 'Uncategorized', 'Total', 'Categorization %']].copy()
                for col in ['Categorized', 'Uncategorized', 'Total']:
                    progress_display[col] = progress_display[col].astype(int)
                progress_display['Categorization %'] = progress_display['Categorization %'].apply(lambda x: f"{x}%")
                
                st.dataframe(
                    progress_display,
                    use_container_width=True
                )
            else:
                st.info("Not enough data to show categorization progress.")
    else:
        st.info("No transactions available to analyze.")
    
    st.markdown("---")
    
    # Debug section for troubleshooting
    with st.expander("🔧 Debug Tools - Find Specific Transaction"):
        st.write("**Search for a specific transaction by description:**")
        search_description = st.text_input("Enter part of the transaction description:", 
                                         placeholder="e.g., 'Kosten Rabo BasisPakket'")
        
        if search_description and len(search_description) > 3:
            # Search in original transactions
            matching_original = all_transactions[
                all_transactions['Description'].str.contains(search_description, case=False, na=False)
            ]
            
            # Search in categorized transactions
            matching_categorized = categorized_transactions[
                categorized_transactions['Description'].str.contains(search_description, case=False, na=False)
            ]
            
            st.write(f"**Found {len(matching_original)} matching transactions in original data:**")
            if not matching_original.empty:
                for idx, row in matching_original.iterrows():
                    st.write(f"- **ID:** {row['Transaction_ID']}")
                    st.write(f"  **Description:** {row['Description']}")
                    st.write(f"  **Amount:** €{row['Amount']:.2f}")
                    st.write(f"  **Date:** {row['Date']}")
                    if 'Counterparty_Name' in row and pd.notna(row['Counterparty_Name']):
                        st.write(f"  **Counterparty:** {row['Counterparty_Name']}")
                    st.write("---")
            
            st.write(f"**Categorization status for these transactions:**")
            if not matching_categorized.empty:
                for idx, row in matching_categorized.iterrows():
                    category = row.get('Category', 'Not categorized')
                    subcategory = row.get('Subcategory', 'Not categorized')
                    source = row.get('Categorization_Source', 'Unknown')
                    
                    st.write(f"- **ID:** {row['Transaction_ID']}")
                    st.write(f"  **Category:** {category}")
                    st.write(f"  **Subcategory:** {subcategory}")
                    st.write(f"  **Source:** {source}")
                    st.write("---")
            else:
                st.warning("No categorization found for these transactions in the rule-categorized data.")
                
            # Check manual categorizations
            manual_categorizations = load_categorized_transactions()
            if not manual_categorizations.empty:
                matching_manual = manual_categorizations[
                    manual_categorizations['Transaction_ID'].isin(matching_original['Transaction_ID'])
                ]
                if not matching_manual.empty:
                    st.write("**Manual categorizations found:**")
                    for idx, row in matching_manual.iterrows():
                        st.write(f"- **ID:** {row['Transaction_ID']}")
                        st.write(f"  **Category:** {row['Category']}")
                        st.write(f"  **Subcategory:** {row['Subcategory']}")
                        st.write(f"  **Source:** {row['Source']}")
                        st.write("---")

    # Show categorization interface
    categorized_transactions_subset = categorized_df[['Transaction_ID', 'Category', 'Source']].copy() if not categorized_df.empty else pd.DataFrame()
    
    if not categories:
        st.error("No categories available. Please configure categories first.")
    else:
        show_transaction_matcher(all_transactions, categorized_transactions_subset, categorized_ids, categories)


def show_transaction_matcher(all_transactions, categorized_df, categorized_ids, categories):
    """Show the actual transaction categorization interface"""
    st.subheader("🎯 Transaction Categorization Interface")
    
    # Filter to uncategorized transactions
    uncategorized_transactions = all_transactions[~all_transactions['Transaction_ID'].isin(categorized_ids)]
    
    # Filter options
    st.subheader("📋 Filter Options")
    col1, col2 = st.columns(2)
    
    with col1:
        show_mode = st.selectbox("Show transactions:", 
                                ["Uncategorized only", "All transactions", "Categorized only"])
    
    with col2:
        amount_filter = st.selectbox("Amount filter:", 
                                   ["All amounts", "Expenses only", "Income only", "Large amounts (>€100)", "Small amounts (<€50)"])
    
    # Apply filters
    if show_mode == "Uncategorized only":
        filtered_transactions = uncategorized_transactions
    elif show_mode == "Categorized only":
        filtered_transactions = all_transactions[all_transactions['Transaction_ID'].isin(categorized_ids)]
    else:
        filtered_transactions = all_transactions
    
    # Amount filters
    if amount_filter == "Expenses only":
        filtered_transactions = filtered_transactions[filtered_transactions['Amount'] < 0]
    elif amount_filter == "Income only":
        filtered_transactions = filtered_transactions[filtered_transactions['Amount'] > 0]
    elif amount_filter == "Large amounts (>€100)":
        filtered_transactions = filtered_transactions[abs(filtered_transactions['Amount']) > 100]
    elif amount_filter == "Small amounts (<€50)":
        filtered_transactions = filtered_transactions[abs(filtered_transactions['Amount']) < 50]
    
    if filtered_transactions.empty:
        st.info("🎉 No transactions match your filter criteria. Try adjusting the filters or you're all done!")
        return
    
    # Reset to first transaction if current index is out of bounds
    if 'current_transaction_index' not in st.session_state:
        st.session_state.current_transaction_index = 0
    
    if st.session_state.current_transaction_index >= len(filtered_transactions):
        st.session_state.current_transaction_index = 0
    
    # Get current transaction
    current_index = st.session_state.current_transaction_index
    total_transactions = len(filtered_transactions)
    current_transaction = filtered_transactions.iloc[current_index]
    transaction_id = current_transaction['Transaction_ID']
    
    # Navigation and progress header
    st.markdown("---")
    
    # Progress indicator
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Previous", disabled=(current_index == 0)):
            st.session_state.current_transaction_index = max(0, current_index - 1)
            st.rerun()
    
    with col2:
        progress = (current_index + 1) / total_transactions
        st.progress(progress, text=f"Transaction {current_index + 1} of {total_transactions}")
        st.write(f"**Transaction ID:** {transaction_id}")
    
    with col3:
        if st.button("Next ➡️", disabled=(current_index == total_transactions - 1)):
            st.session_state.current_transaction_index = min(total_transactions - 1, current_index + 1)
            st.rerun()
    
    st.markdown("---")
    
    # Check if already categorized
    current_categorization = None
    if not categorized_df.empty:
        existing = categorized_df[categorized_df['Transaction_ID'] == transaction_id]
        if not existing.empty:
            current_categorization = existing.iloc[0]
    
    # Show current transaction details in a prominent card
    with st.container():
        if current_categorization is not None:
            st.success(f"✅ **Already categorized as:** {current_categorization['Category']} → {current_categorization.get('Subcategory', 'N/A')} (by {current_categorization['Source']})")
        
        # Transaction details card
        st.subheader("💳 Transaction Details")
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Main transaction info
            st.markdown(f"""
            **� Date:** {current_transaction['Date']}  
            **💰 Amount:** €{current_transaction['Amount']:.2f}  
            **📝 Description:** {current_transaction['Description']}
            """)
            
            if pd.notna(current_transaction.get('Counterparty_Name')):
                st.markdown(f"**🏢 Counterparty:** {current_transaction['Counterparty_Name']}")
            
            if pd.notna(current_transaction.get('Reference')):
                st.markdown(f"**🔗 Reference:** {current_transaction['Reference']}")
        
        with col2:
            # Categorization section
            st.subheader("📂 Categorization")
            
            if current_categorization is None:
                # Show categorization form - handle category/subcategory selection outside form for reactivity
                
                # Category selection (outside form for reactivity)
                selected_category = st.selectbox(
                    "Select Category", 
                    [""] + list(categories.keys()),
                    key=f"cat_{transaction_id}",
                    help="Choose the main category for this transaction"
                )
                
                # Subcategory selection (outside form for reactivity)
                subcategory_options = [""]
                if selected_category and selected_category in categories:
                    subcategories = categories[selected_category].get("subcategories", {})
                    subcategory_options.extend(list(subcategories.keys()))
                
                selected_subcategory = st.selectbox(
                    "Select Subcategory",
                    subcategory_options,
                    key=f"subcat_{transaction_id}",
                    help="Choose the specific subcategory"
                )
                
                # Show current selection
                if selected_category:
                    if selected_subcategory:
                        st.info(f"**Selected:** {selected_category} → {selected_subcategory}")
                    else:
                        st.warning(f"**Selected:** {selected_category} → (Please select subcategory)")
                
                # Form for submission only
                with st.form(f"categorize_{transaction_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        submitted = st.form_submit_button("💾 Save Category", type="primary", use_container_width=True)
                    
                    with col2:
                        skip = st.form_submit_button("⏭️ Skip", use_container_width=True)
                    
                    if submitted and selected_category and selected_subcategory:
                        if save_categorized_transaction(transaction_id, selected_category, selected_subcategory):
                            st.success(f"✅ Categorized as {selected_category} → {selected_subcategory}")
                            # Auto-advance to next transaction
                            if current_index < total_transactions - 1:
                                st.session_state.current_transaction_index += 1
                            st.rerun()
                        else:
                            st.error("❌ Failed to save categorization")
                    elif submitted:
                        st.error("⚠️ Please select both category and subcategory")
                    
                    if skip:
                        # Move to next transaction without categorizing
                        if current_index < total_transactions - 1:
                            st.session_state.current_transaction_index += 1
                            st.rerun()
                        else:
                            st.info("📋 Reached the end of transactions")
            else:
                # Show existing categorization and option to change
                st.info(f"**Current Category:** {current_categorization['Category']}")
                st.info(f"**Current Subcategory:** {current_categorization.get('Subcategory', 'N/A')}")
                st.info(f"**Source:** {current_categorization['Source']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Re-categorize", key=f"recat_{transaction_id}", use_container_width=True):
                        # Remove existing categorization to allow re-categorization
                        training_file = Path(__file__).parent.parent / "data" / "categorized_transactions.csv"
                        if training_file.exists():
                            try:
                                existing_df = pd.read_csv(training_file)
                                updated_df = existing_df[existing_df['Transaction_ID'] != transaction_id]
                                updated_df.to_csv(training_file, index=False)
                                st.success("✅ Categorization removed")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error removing categorization: {e}")
                
                with col2:
                    if st.button("⏭️ Next Transaction", key=f"next_{transaction_id}", use_container_width=True):
                        if current_index < total_transactions - 1:
                            st.session_state.current_transaction_index += 1
                            st.rerun()
                        else:
                            st.info("📋 Reached the end of transactions")
    
    # Quick navigation
    st.markdown("---")
    st.subheader("🔢 Quick Navigation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⏮️ First Transaction"):
            st.session_state.current_transaction_index = 0
            st.rerun()
    
    with col2:
        # Jump to specific transaction
        jump_to = st.number_input(
            "Jump to transaction #", 
            min_value=1, 
            max_value=total_transactions, 
            value=current_index + 1,
            key="jump_to_transaction"
        )
        if st.button("🎯 Go"):
            st.session_state.current_transaction_index = jump_to - 1
            st.rerun()
    
    with col3:
        if st.button("⏭️ Last Transaction"):
            st.session_state.current_transaction_index = total_transactions - 1
            st.rerun()
    
    # Keyboard shortcuts info
    with st.expander("⌨️ Keyboard Shortcuts & Tips"):
        st.markdown("""
        **Navigation Tips:**
        - Use the Previous/Next buttons to navigate through transactions
        - The progress bar shows your current position
        - After categorizing, you'll automatically advance to the next transaction
        - Use Quick Navigation to jump to specific transactions
        
        **Categorization Tips:**
        - Select both category and subcategory before saving
        - Use "Skip" to move to the next transaction without categorizing
        - You can re-categorize any transaction later
        - Filter options help you focus on specific types of transactions
        """)
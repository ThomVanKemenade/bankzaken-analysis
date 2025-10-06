import streamlit as st
import pandas as pd
import json
import datetime
import re
from pathlib import Path

def rule_management():
    st.title("⚙️ Rule Management")
    st.markdown("Create and manage rules to automatically categorize your transactions.")
    
    # Load rules data
    def load_rules():
        try:
            rules_file = Path(__file__).parent.parent / "categories" / "categorization_rules.json"
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"categorization_rules": {"rules": []}}
        except Exception as e:
            st.error(f"Error loading rules: {e}")
            return {"categorization_rules": {"rules": []}}
    
    def save_rules(rules_data):
        try:
            rules_file = Path(__file__).parent.parent / "categories" / "categorization_rules.json"
            rules_file.parent.mkdir(parents=True, exist_ok=True)
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Error saving rules: {e}")
            return False
    
    # Load transaction data for rule testing
    def load_all_transactions():
        try:
            import sys
            from pathlib import Path
            sys.path.append(str(Path(__file__).parent.parent))
            from transaction_loader.transaction_loader import load_all_transactions as load_transactions
            return load_transactions()
        except ImportError:
            try:
                data_file = Path(__file__).parent.parent / "combined_transactions.csv"
                if data_file.exists():
                    return pd.read_csv(data_file)
                else:
                    return pd.DataFrame()
            except Exception:
                return pd.DataFrame()
    
    def evaluate_condition(transaction, condition):
        """Evaluate a single condition against a transaction"""
        import pandas as pd
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
        if operator == 'contains':
            return value_str in field_str
        elif operator == 'equals':
            return field_str == value_str
        elif operator == 'starts_with':
            return field_str.startswith(value_str)
        elif operator == 'ends_with':
            return field_str.endswith(value_str)
        elif operator == 'regex':
            try:
                flags = 0 if case_sensitive else re.IGNORECASE
                return bool(re.search(value_str, field_str, flags))
            except re.error:
                return False
        elif operator == 'greater_than':
            try:
                return float(field_value) > float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'less_than':
            try:
                return float(field_value) < float(value)
            except (ValueError, TypeError):
                return False
        elif operator == 'between':
            try:
                if isinstance(value, list) and len(value) == 2:
                    val = float(field_value)
                    return float(value[0]) <= val <= float(value[1])
            except (ValueError, TypeError):
                return False
        elif operator == 'in':
            # Check if field value is in a list of values
            if isinstance(value, list):
                # Handle case sensitivity for list matching
                if not case_sensitive:
                    return field_str.lower() in [str(v).lower() for v in value]
                else:
                    return field_str in [str(v) for v in value]
            else:
                # Single value, behave like equals
                return field_str == value_str
        
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

    def test_rule_against_transactions(conditions, transactions, max_results=10):
        """Test rule conditions against transactions and return matches"""
        import pandas as pd
        matching_transactions = []
        
        for _, transaction in transactions.iterrows():
            if evaluate_rule_conditions(transaction, conditions):
                matching_transactions.append(transaction)
                if len(matching_transactions) >= max_results:
                    break
        
        return pd.DataFrame(matching_transactions)

    def format_condition_display(condition):
        """Format a condition for display"""
        field = condition.get('field', '')
        operator = condition.get('operator', '')
        value = condition.get('value', '')
        case_sensitive = condition.get('case_sensitive', False)
        
        # Format value for display
        if isinstance(value, list):
            value_str = f"[{', '.join(map(str, value))}]"
        else:
            value_str = str(value)
        
        case_str = "" if case_sensitive else " (case insensitive)"
        return f"{field} {operator} '{value_str}'{case_str}"

    # Load data
    rules_data = load_rules()
    rules = rules_data.get("categorization_rules", {}).get("rules", [])
    
    # Available fields for rule conditions
    available_fields = [
        "Date", "Amount", "Description", "Counterparty_Name", 
        "Account_Number", "Transaction_Type", "Reference", 
        "Balance_After", "Currency"
    ]
    
    # Load all transactions for rule preview (not just samples)
    all_transactions = load_all_transactions()
    
    # Tab-based navigation
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View & Edit Rules", "➕ Add Rule", "📊 Rule History", "📖 Rule Guide"])
    
    with tab1:
        st.subheader("📋 Rule Overview & Management")
        
        if not rules:
            st.info("No rules found. Create your first rule using the 'Add Rule' tab.")
            st.markdown("### Quick Start")
            st.markdown("""
            1. 📝 **Add a new rule** - Click the 'Add Rule' tab
            2. 🎯 **Set conditions** - Define when the rule should apply
            3. 🏷️ **Choose category** - Select where transactions should be categorized
            4. ⚡ **Test & activate** - Preview matches and activate your rule
            """)
        else:
            # Statistics
            total_rules = len(rules)
            active_rules = len([r for r in rules if r.get("active", True)])
            inactive_rules = total_rules - active_rules
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rules", total_rules)
            with col2:
                st.metric("Active Rules", active_rules)
            with col3:
                st.metric("Inactive Rules", inactive_rules)
        
            st.markdown("---")
            
            # Rules table with inline editing
            st.subheader("Rules Overview")
            
            # Sort rules by priority (highest first)
            sorted_rules = sorted(rules, key=lambda x: x.get("priority", 0), reverse=True)
            
            for i, rule in enumerate(sorted_rules):
                rule_id = rule.get("id", f"rule_{i}")
                name = rule.get("name", "Unnamed Rule")
                description = rule.get("description", "No description")
                category = rule.get("category", "")
                subcategory = rule.get("subcategory", "")
                priority = rule.get("priority", 0)
                is_active = rule.get("active", True)
                
                # Create rule card
                status_icon = "✅" if is_active else "❌"
                priority_color = "🔴" if priority >= 90 else "🟡" if priority >= 70 else "🟢"
                
                with st.expander(f"{status_icon} {priority_color} **{name}** → {category} → {subcategory}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Rule details
                        st.write(f"**Description:** {description}")
                        st.write(f"**Priority:** {priority}")
                        st.write(f"**Status:** {'✅ Active' if is_active else '❌ Inactive'}")
                        
                        # Show conditions
                        conditions = rule.get("conditions", {})
                        if conditions:
                            st.write("**Conditions:**")
                            if 'field' in conditions:
                                # Single condition
                                condition_text = format_condition_display(conditions)
                                st.code(condition_text, language="text")
                            else:
                                # Multiple conditions
                                logic_op = conditions.get("operator", "AND")
                                st.write(f"*Logic: {logic_op}*")
                                for j, cond in enumerate(conditions.get("rules", [])):
                                    condition_text = format_condition_display(cond)
                                    st.code(f"{j+1}. {condition_text}", language="text")
                    
                    with col2:
                        # Action buttons
                        col_edit, col_delete = st.columns(2)
                        
                        with col_edit:
                            if st.button("✏️ Edit", key=f"edit_{rule_id}", help="Edit this rule"):
                                st.session_state['edit_rule_id'] = rule_id
                                st.session_state['edit_rule_data'] = rule.copy()
                                # Initialize edit conditions
                                rule_conditions = rule.get('conditions', {})
                                if 'field' in rule_conditions:
                                    st.session_state.edit_rule_conditions = [rule_conditions]
                                else:
                                    st.session_state.edit_rule_conditions = rule_conditions.get('rules', [])
                                st.rerun()
                        
                        with col_delete:
                            if st.button("🗑️ Delete", key=f"delete_{rule_id}", help="Delete this rule"):
                                # Confirm deletion
                                if st.session_state.get(f'confirm_delete_{rule_id}', False):
                                    # Actually delete the rule
                                    rules_data["categorization_rules"]["rules"] = [r for r in rules if r.get("id") != rule_id]
                                    if save_rules(rules_data):
                                        st.success(f"Rule '{name}' deleted successfully!")
                                        st.session_state[f'confirm_delete_{rule_id}'] = False
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete rule")
                                else:
                                    st.session_state[f'confirm_delete_{rule_id}'] = True
                                    st.warning("⚠️ Click 'Delete' again to confirm deletion.")
                                    st.rerun()
            
            # Edit section (appears when a rule is selected for editing)
            if 'edit_rule_id' in st.session_state and 'edit_rule_data' in st.session_state:
                st.markdown("---")
                st.subheader("✏️ Edit Rule")
                
                edit_rule_data = st.session_state['edit_rule_data']
                
                # Back button
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("← Back"):
                        # Clear edit session state
                        for key in ['edit_rule_id', 'edit_rule_data', 'edit_rule_conditions', 'edit_logic_operator']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                
                with col2:
                    st.info(f"💡 **Editing rule:** {edit_rule_data.get('name', 'Unknown Rule')}")
                
                # Initialize edit conditions in session state if not exists
                if 'edit_rule_conditions' not in st.session_state:
                    rule_conditions = edit_rule_data.get('conditions', {})
                    if 'field' in rule_conditions:
                        st.session_state.edit_rule_conditions = [rule_conditions]
                    else:
                        st.session_state.edit_rule_conditions = rule_conditions.get('rules', [])
                
                # Condition builder for editing
                st.subheader("Rule Conditions")
                
                with st.container():
                    st.markdown("**Add/Modify Conditions:**")
                    
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                    with col1:
                        condition_field = st.selectbox("Field", available_fields, key="edit_condition_field")
                    with col2:
                        condition_operator = st.selectbox("Operator", 
                            ["contains", "equals", "starts_with", "ends_with", "greater_than", "less_than", "regex", "in"],
                            key="edit_condition_operator")
                    with col3:
                        if condition_operator == "in":
                            condition_value = st.text_area("Values (one per line)", key="edit_condition_value", help="Enter multiple values, one per line")
                        else:
                            condition_value = st.text_input("Value", key="edit_condition_value")
                    with col4:
                        case_sensitive = st.checkbox("Case sensitive", key="edit_condition_case")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("➕ Add Condition", type="secondary", key="edit_add_condition"):
                            if condition_field and condition_value:
                                # Handle 'in' operator specially
                                if condition_operator == "in":
                                    # Split by lines and clean up
                                    value_list = [v.strip() for v in condition_value.split('\n') if v.strip()]
                                    if value_list:
                                        new_condition = {
                                            "field": condition_field,
                                            "operator": condition_operator,
                                            "value": value_list,
                                            "case_sensitive": case_sensitive
                                        }
                                    else:
                                        st.error("Please provide at least one value for 'in' operator")
                                        st.stop()
                                else:
                                    new_condition = {
                                        "field": condition_field,
                                        "operator": condition_operator,
                                        "value": condition_value,
                                        "case_sensitive": case_sensitive
                                    }
                                st.session_state.edit_rule_conditions.append(new_condition)
                                st.rerun()
                            else:
                                st.error("Please fill in field and value")
                    
                    with col2:
                        if st.button("🗑️ Clear All Conditions", key="edit_clear_conditions"):
                            st.session_state.edit_rule_conditions = []
                            st.rerun()
                
                # Display current conditions for editing
                if st.session_state.edit_rule_conditions:
                    st.markdown("**Current Conditions:**")
                    
                    # Logic operator selection
                    existing_logic = "AND"
                    if 'operator' in edit_rule_data.get('conditions', {}):
                        existing_logic = edit_rule_data['conditions']['operator']
                    
                    logic_operator = st.radio("Logic between conditions:", ["AND", "OR"], 
                                            index=0 if existing_logic == "AND" else 1, 
                                            horizontal=True, key="edit_logic_operator")
                    
                    # Display conditions with remove option
                    conditions_to_remove = []
                    for j, condition in enumerate(st.session_state.edit_rule_conditions):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            condition_text = format_condition_display(condition)
                            st.code(condition_text, language="text")
                        with col2:
                            if st.checkbox("Remove", key=f"edit_remove_condition_{j}", help="Check to remove this condition"):
                                conditions_to_remove.append(j)
                    
                    # Remove conditions if any are marked
                    if conditions_to_remove:
                        for j in reversed(conditions_to_remove):
                            st.session_state.edit_rule_conditions.pop(j)
                        st.rerun()
                    
                    # Build final conditions for preview
                    if len(st.session_state.edit_rule_conditions) == 1:
                        final_conditions = st.session_state.edit_rule_conditions[0]
                    else:
                        final_conditions = {
                            "operator": logic_operator,
                            "rules": st.session_state.edit_rule_conditions
                        }
                    
                    # Rule preview
                    if not all_transactions.empty:
                        st.markdown("**🔍 Rule Preview - Matching Transactions:**")
                        
                        # Get matches
                        all_matching = test_rule_against_transactions(final_conditions, all_transactions, max_results=10000)
                        total_matches = len(all_matching)
                        
                        preview_limit = st.slider("Preview limit", min_value=5, max_value=100, value=20, step=5, key="edit_rule_preview_limit")
                        matching_transactions = test_rule_against_transactions(final_conditions, all_transactions, max_results=preview_limit)
                        
                        if not matching_transactions.empty:
                            if total_matches > preview_limit:
                                st.success(f"✅ Found **{total_matches}** total matching transactions (showing first {preview_limit}):")
                            else:
                                st.success(f"✅ Found **{total_matches}** matching transactions:")
                            
                            display_columns = ['Date', 'Amount', 'Description', 'Counterparty_Name']
                            available_columns = [col for col in display_columns if col in matching_transactions.columns]
                            
                            if available_columns:
                                st.dataframe(
                                    matching_transactions[available_columns], 
                                    use_container_width=True,
                                    column_config={
                                        "Amount": st.column_config.NumberColumn(
                                            "Amount",
                                            format="€%.2f"
                                        )
                                    }
                                )
                            else:
                                st.dataframe(
                                    matching_transactions, 
                                    use_container_width=True,
                                    column_config={
                                        "Amount": st.column_config.NumberColumn(
                                            "Amount",
                                            format="€%.2f"
                                        )
                                    }
                                )
                        else:
                            st.warning("⚠️ No transactions match this rule")
                else:
                    st.info("Add conditions above to build your rule")
                
                # Category/Subcategory selection for editing
                st.markdown("**Category Selection:**")
                
                try:
                    from .category_management import load_categories
                    categories_data = load_categories()
                    categories = categories_data.get("categories", {})
                    category_names = list(categories.keys())
                except Exception as e:
                    st.error(f"Error loading categories: {e}")
                    category_names = []
                
                if category_names:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        existing_category = edit_rule_data.get('category', '')
                        category_index = category_names.index(existing_category) if existing_category in category_names else 0
                        selected_category = st.selectbox("Category *", category_names, index=category_index, key="edit_rule_category")
                    
                    with col2:
                        if selected_category and selected_category in categories:
                            subcategories = list(categories[selected_category].get("subcategories", {}).keys())
                            if subcategories:
                                existing_subcategory = edit_rule_data.get('subcategory', '')
                                subcategory_index = subcategories.index(existing_subcategory) if existing_subcategory in subcategories else 0
                                selected_subcategory = st.selectbox("Subcategory *", subcategories, index=subcategory_index, key="edit_rule_subcategory")
                            else:
                                st.warning(f"No subcategories found for '{selected_category}'.")
                                selected_subcategory = None
                        else:
                            selected_subcategory = None
                else:
                    st.warning("No categories found. Please create categories first.")
                    selected_category = None
                    selected_subcategory = None
                
                # Edit form
                with st.form("edit_rule_form"):
                    st.markdown("**Rule Details:**")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        rule_name = st.text_input("Rule Name *", value=edit_rule_data.get('name', ''))
                        priority = st.number_input("Priority", min_value=1, max_value=100, value=edit_rule_data.get('priority', 50))
                    
                    with col2:
                        if selected_category:
                            st.info(f"**Selected Category:** {selected_category}")
                            if selected_subcategory:
                                st.info(f"**Selected Subcategory:** {selected_subcategory}")
                        
                        is_active = st.checkbox("Active", value=edit_rule_data.get('active', True))
                    
                    description = st.text_area("Description", value=edit_rule_data.get('description', ''))
                    
                    # Submit buttons
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        submitted = st.form_submit_button("💾 Save Changes")
                    with col2:
                        cancel = st.form_submit_button("❌ Cancel")
                    with col3:
                        reset = st.form_submit_button("🔄 Reset")
                    
                    if cancel:
                        for key in ['edit_rule_id', 'edit_rule_data', 'edit_rule_conditions', 'edit_logic_operator']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                    
                    if reset:
                        rule_conditions = edit_rule_data.get('conditions', {})
                        if 'field' in rule_conditions:
                            st.session_state.edit_rule_conditions = [rule_conditions]
                        else:
                            st.session_state.edit_rule_conditions = rule_conditions.get('rules', [])
                        st.rerun()
                    
                    if submitted:
                        logic_operator = st.session_state.get('edit_logic_operator', 'AND')
                        rule_id = edit_rule_data.get('id', '')
                        
                        if not all([rule_name, selected_category, selected_subcategory]):
                            st.error("Please fill in all required fields.")
                        elif not st.session_state.edit_rule_conditions:
                            st.error("Please add at least one condition.")
                        else:
                            # Build conditions
                            if len(st.session_state.edit_rule_conditions) == 1:
                                rule_conditions = st.session_state.edit_rule_conditions[0]
                            else:
                                rule_conditions = {
                                    "operator": logic_operator,
                                    "rules": st.session_state.edit_rule_conditions
                                }
                            
                            # Update rule
                            import datetime as dt
                            updated_rule = {
                                "id": rule_id,
                                "name": rule_name,
                                "description": description,
                                "category": selected_category,
                                "subcategory": selected_subcategory,
                                "priority": priority,
                                "active": is_active,
                                "conditions": rule_conditions,
                                "created_at": edit_rule_data.get("created_at", dt.datetime.now().isoformat()),
                                "created_by": edit_rule_data.get("created_by", "user"),
                                "last_modified_at": dt.datetime.now().isoformat(),
                                "last_modified_by": "user"
                            }
                            
                            # Find and update the rule
                            rule_found = False
                            for i, r in enumerate(rules):
                                if r.get("id") == rule_id:
                                    rules[i] = updated_rule
                                    rule_found = True
                                    break
                            
                            if rule_found:
                                rules_data["categorization_rules"]["rules"] = rules
                                if save_rules(rules_data):
                                    st.success(f"Rule '{rule_name}' updated successfully!")
                                    # Clear edit session state
                                    for key in ['edit_rule_id', 'edit_rule_data', 'edit_rule_conditions', 'edit_logic_operator']:
                                        if key in st.session_state:
                                            del st.session_state[key]
                                    st.rerun()
                                else:
                                    st.error("Failed to save updated rule.")
                            else:
                                st.error(f"Could not find rule with ID '{rule_id}'.")

    with tab2:
        # Add Rule Tab
        st.subheader("➕ Add New Rule")
        st.info("💡 **Tip:** Start with the Rule Guide if you're new to creating rules!")
        
        # Initialize conditions in session state
        if 'new_rule_conditions' not in st.session_state:
            st.session_state.new_rule_conditions = []
        
        # Condition builder section
        st.subheader("Rule Conditions")
        
        with st.container():
            st.markdown("**Add Conditions:**")
            
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                condition_field = st.selectbox("Field", available_fields, key="new_condition_field")
            with col2:
                condition_operator = st.selectbox("Operator", 
                    ["contains", "equals", "starts_with", "ends_with", "greater_than", "less_than", "regex", "in"],
                    key="new_condition_operator")
            with col3:
                if condition_operator == "in":
                    condition_value = st.text_area("Values (one per line)", key="new_condition_value", help="Enter multiple values, one per line")
                else:
                    condition_value = st.text_input("Value", key="new_condition_value")
            with col4:
                case_sensitive = st.checkbox("Case sensitive", key="new_condition_case")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("➕ Add Condition", type="secondary", key="new_add_condition"):
                    if condition_field and condition_value:
                        # Handle 'in' operator specially
                        if condition_operator == "in":
                            # Split by lines and clean up
                            value_list = [v.strip() for v in condition_value.split('\n') if v.strip()]
                            if value_list:
                                new_condition = {
                                    "field": condition_field,
                                    "operator": condition_operator,
                                    "value": value_list,
                                    "case_sensitive": case_sensitive
                                }
                            else:
                                st.error("Please provide at least one value for 'in' operator")
                                st.stop()
                        else:
                            new_condition = {
                                "field": condition_field,
                                "operator": condition_operator,
                                "value": condition_value,
                                "case_sensitive": case_sensitive
                            }
                        st.session_state.new_rule_conditions.append(new_condition)
                        st.rerun()
                    else:
                        st.error("Please fill in field and value")
            
            with col2:
                if st.button("🗑️ Clear All Conditions", key="new_clear_conditions"):
                    st.session_state.new_rule_conditions = []
                    st.rerun()
        
        # Display current conditions
        if st.session_state.new_rule_conditions:
            st.markdown("**Current Conditions:**")
            
            # Logic operator selection
            logic_operator = st.radio("Logic between conditions:", ["AND", "OR"], 
                                    index=0, horizontal=True, key="new_logic_operator")
            
            # Display conditions with remove option
            conditions_to_remove = []
            for i, condition in enumerate(st.session_state.new_rule_conditions):
                col1, col2 = st.columns([4, 1])
                with col1:
                    condition_text = format_condition_display(condition)
                    st.code(condition_text, language="text")
                with col2:
                    if st.checkbox("Remove", key=f"new_remove_condition_{i}", help="Check to remove this condition"):
                        conditions_to_remove.append(i)
            
            # Remove conditions if any are marked
            if conditions_to_remove:
                for i in reversed(conditions_to_remove):
                    st.session_state.new_rule_conditions.pop(i)
                st.rerun()
            
            # Build final conditions for preview
            if len(st.session_state.new_rule_conditions) == 1:
                final_conditions = st.session_state.new_rule_conditions[0]
            else:
                final_conditions = {
                    "operator": logic_operator,
                    "rules": st.session_state.new_rule_conditions
                }
            
            # Real-time rule preview
            if not all_transactions.empty:
                st.markdown("**🔍 Rule Preview - Matching Transactions:**")
                
                # Get total count first
                all_matching = test_rule_against_transactions(final_conditions, all_transactions, max_results=10000)
                total_matches = len(all_matching)
                
                # Show preview with configurable limit
                preview_limit = st.slider("Preview limit", min_value=5, max_value=100, value=20, step=5, key="new_rule_preview_limit")
                matching_transactions = test_rule_against_transactions(final_conditions, all_transactions, max_results=preview_limit)
                
                if not matching_transactions.empty:
                    if total_matches > preview_limit:
                        st.success(f"✅ Found **{total_matches}** total matching transactions (showing first {preview_limit}):")
                    else:
                        st.success(f"✅ Found **{total_matches}** matching transactions:")
                    
                    # Display matching transactions
                    display_columns = ['Date', 'Amount', 'Description', 'Counterparty_Name']
                    available_columns = [col for col in display_columns if col in matching_transactions.columns]
                    
                    if available_columns:
                        st.dataframe(
                            matching_transactions[available_columns], 
                            use_container_width=True,
                            column_config={
                                "Amount": st.column_config.NumberColumn(
                                    "Amount",
                                    format="€%.2f"
                                )
                            }
                        )
                    else:
                        st.dataframe(
                            matching_transactions, 
                            use_container_width=True,
                            column_config={
                                "Amount": st.column_config.NumberColumn(
                                    "Amount",
                                    format="€%.2f"
                                )
                            }
                        )
                else:
                    st.warning("⚠️ No transactions match this rule")
            else:
                st.warning("⚠️ No transaction data available for preview. Please ensure your transaction data is loaded in combined_transactions.csv.")
        else:
            st.info("Add conditions above to build your rule")
        
        st.markdown("---")
        
        # Category/Subcategory selection
        st.markdown("**Category Selection:**")
        
        # Load categories for dropdown
        try:
            from .category_management import load_categories
            categories_data = load_categories()
            categories = categories_data.get("categories", {})
            category_names = list(categories.keys())
        except Exception as e:
            st.error(f"Error loading categories: {e}")
            category_names = []
        
        if category_names:
            col1, col2 = st.columns(2)
            
            with col1:
                selected_category = st.selectbox("Category *", category_names, key="new_rule_category")
            
            with col2:
                if selected_category and selected_category in categories:
                    subcategories = list(categories[selected_category].get("subcategories", {}).keys())
                    if subcategories:
                        selected_subcategory = st.selectbox("Subcategory *", subcategories, key="new_rule_subcategory")
                    else:
                        st.warning(f"No subcategories found for '{selected_category}'. Please add subcategories first.")
                        selected_subcategory = None
                else:
                    selected_subcategory = None
        else:
            st.warning("No categories found. Please create categories first.")
            selected_category = None
            selected_subcategory = None
        
        # Rule creation form
        with st.form("new_rule_form"):
            st.markdown("**Rule Details:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                rule_name = st.text_input("Rule Name *", help="Give your rule a descriptive name")
                priority = st.number_input("Priority", min_value=1, max_value=100, value=50,
                                         help="Higher priority rules are applied first (1-100)")
            
            with col2:
                # Display selected category/subcategory
                if selected_category:
                    st.info(f"**Selected Category:** {selected_category}")
                    if selected_subcategory:
                        st.info(f"**Selected Subcategory:** {selected_subcategory}")
                    else:
                        st.error("Please select a subcategory above.")
                else:
                    st.error("Please select a category and subcategory above.")
                
                is_active = st.checkbox("Active", value=True, help="Active rules are applied to transactions")
            
            description = st.text_area("Description", help="Describe what this rule does")
            
            # Submit button
            submitted = st.form_submit_button("💾 Create Rule", type="primary")
            
            if submitted:
                # Get the current logic operator
                logic_operator = st.session_state.get('new_logic_operator', 'AND')
                
                # Validation
                if not all([rule_name, selected_category, selected_subcategory]):
                    st.error("Please fill in all required fields (marked with *) and select both category and subcategory above.")
                elif not st.session_state.new_rule_conditions:
                    st.error("Please add at least one condition to your rule.")
                else:
                    # Build conditions from session state
                    if len(st.session_state.new_rule_conditions) == 1:
                        rule_conditions = st.session_state.new_rule_conditions[0]
                    else:
                        rule_conditions = {
                            "operator": logic_operator,
                            "rules": st.session_state.new_rule_conditions
                        }
                    
                    # Generate unique rule ID
                    import uuid
                    import datetime as dt
                    rule_id = f"{rule_name.lower().replace(' ', '_')}_{str(uuid.uuid4())[:8]}"
                    
                    # Create new rule
                    new_rule = {
                        "id": rule_id,
                        "name": rule_name,
                        "description": description,
                        "category": selected_category,
                        "subcategory": selected_subcategory,
                        "priority": priority,
                        "active": is_active,
                        "conditions": rule_conditions,
                        "created_at": dt.datetime.now().isoformat(),
                        "created_by": "user"
                    }
                    
                    # Add to rules list
                    rules.append(new_rule)
                    rules_data["categorization_rules"]["rules"] = rules
                    
                    # Save the rules
                    if save_rules(rules_data):
                        st.success(f"Rule '{rule_name}' created successfully!")
                        # Clear the session state for new rule creation
                        st.session_state.new_rule_conditions = []
                        st.rerun()
                    else:
                        st.error("Failed to save the new rule.")

    with tab3:
        # Rule History Tab
        st.subheader("📊 Rule History & Analytics")
        
        if not rules:
            st.info("No rules found. Create some rules first to see their history here.")
        else:
            # Sort rules by creation date (newest first)
            rules_with_dates = []
            for rule in rules:
                rule_copy = rule.copy()
                # Handle rules that might not have creation timestamps (legacy rules)
                if 'created_at' not in rule_copy:
                    rule_copy['created_at'] = "Unknown"
                    rule_copy['created_by'] = "Unknown"
                rules_with_dates.append(rule_copy)
            
            # Try to sort by creation date, fallback to name if no date
            try:
                sorted_rules = sorted(rules_with_dates, 
                                    key=lambda x: x.get('created_at', '0000-01-01T00:00:00'), 
                                    reverse=True)
            except:
                sorted_rules = sorted(rules_with_dates, key=lambda x: x.get('name', ''))
            
            # Overview statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Rules", len(rules))
            
            with col2:
                active_count = sum(1 for r in rules if r.get('active', True))
                st.metric("Active Rules", active_count)
            
            with col3:
                # Count rules created in last 7 days
                recent_count = 0
                seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
                for rule in rules:
                    created_at = rule.get('created_at')
                    if created_at and created_at != "Unknown":
                        try:
                            rule_date = datetime.datetime.fromisoformat(created_at)
                            if rule_date > seven_days_ago:
                                recent_count += 1
                        except:
                            pass
                st.metric("Created This Week", recent_count)
            
            st.markdown("---")
            
            # Charts and Analytics
            st.subheader("📈 Rule Analytics")
            
            # Quick insights box
            with st.container():
                st.markdown("**📊 Quick Insights**")
                insight_col1, insight_col2, insight_col3, insight_col4 = st.columns(4)
                
                with insight_col1:
                    avg_priority = sum(r.get('priority', 50) for r in rules) / len(rules) if rules else 0
                    st.metric("Average Priority", f"{avg_priority:.1f}")
                
                with insight_col2:
                    unique_categories = len(set(r.get('category', 'Unknown') for r in rules))
                    st.metric("Categories Used", unique_categories)
                
                with insight_col3:
                    # Most common category
                    category_counts = {}
                    for rule in rules:
                        category = rule.get('category', 'Unknown')
                        category_counts[category] = category_counts.get(category, 0) + 1
                    
                    most_common = max(category_counts.items(), key=lambda x: x[1]) if category_counts else ("None", 0)
                    st.metric("Most Used Category", most_common[0][:15] + "..." if len(most_common[0]) > 15 else most_common[0])
                
                with insight_col4:
                    activation_rate = (active_count / len(rules) * 100) if rules else 0
                    st.metric("Activation Rate", f"{activation_rate:.0f}%")
            
            st.markdown("---")
            
            # Prepare data for charts
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # Rules by Category Chart
                st.markdown("**Rules by Category**")
                category_counts = {}
                for rule in rules:
                    category = rule.get('category', 'Unknown')
                    category_counts[category] = category_counts.get(category, 0) + 1
                
                if category_counts:
                    # Create DataFrame for chart
                    import pandas as pd
                    chart_data = pd.DataFrame(
                        list(category_counts.items()),
                        columns=['Category', 'Count']
                    )
                    st.bar_chart(chart_data.set_index('Category'))
                else:
                    st.info("No category data available")
            
            with chart_col2:
                # Rules by Priority Range Chart
                st.markdown("**Rules by Priority Range**")
                priority_ranges = {
                    "90-100 (Very High)": 0,
                    "70-89 (High)": 0,
                    "50-69 (Medium)": 0,
                    "30-49 (Low)": 0,
                    "1-29 (Very Low)": 0
                }
                
                for rule in rules:
                    priority = rule.get('priority', 50)
                    if priority >= 90:
                        priority_ranges["90-100 (Very High)"] += 1
                    elif priority >= 70:
                        priority_ranges["70-89 (High)"] += 1
                    elif priority >= 50:
                        priority_ranges["50-69 (Medium)"] += 1
                    elif priority >= 30:
                        priority_ranges["30-49 (Low)"] += 1
                    else:
                        priority_ranges["1-29 (Very Low)"] += 1
                
                # Create DataFrame for chart
                priority_data = pd.DataFrame(
                    list(priority_ranges.items()),
                    columns=['Priority Range', 'Count']
                )
                st.bar_chart(priority_data.set_index('Priority Range'))
            
            # Rules Creation Timeline
            st.markdown("**📅 Rule Creation Timeline**")
            
            # Prepare timeline data
            timeline_data = {}
            for rule in rules:
                created_at = rule.get('created_at', 'Unknown')
                if created_at != 'Unknown':
                    try:
                        created_date = datetime.datetime.fromisoformat(created_at)
                        date_key = created_date.strftime('%Y-%m-%d')
                        timeline_data[date_key] = timeline_data.get(date_key, 0) + 1
                    except:
                        pass
            
            if timeline_data:
                # Sort by date
                sorted_timeline = dict(sorted(timeline_data.items()))
                timeline_df = pd.DataFrame(
                    list(sorted_timeline.items()),
                    columns=['Date', 'Rules Created']
                )
                timeline_df['Date'] = pd.to_datetime(timeline_df['Date'])
                timeline_df = timeline_df.set_index('Date')
                st.line_chart(timeline_df)
            else:
                st.info("No creation date data available for timeline")
            
            # Active vs Inactive Pie Chart
            col_pie1, col_pie2 = st.columns(2)
            
            with col_pie1:
                st.markdown("**Active vs Inactive Rules**")
                active_count = sum(1 for r in rules if r.get('active', True))
                inactive_count = len(rules) - active_count
                
                if active_count > 0 or inactive_count > 0:
                    # Using plotly for pie chart if available
                    try:
                        import plotly.express as px
                        import plotly.graph_objects as go
                        pie_data = pd.DataFrame({
                            'Status': ['Active', 'Inactive'],
                            'Count': [active_count, inactive_count]
                        })
                        fig = px.pie(pie_data, values='Count', names='Status', 
                                   color_discrete_map={'Active': '#00CC88', 'Inactive': '#FF6B6B'},
                                   title="Rule Status Distribution")
                        fig.update_layout(height=350, showlegend=True)
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
                    except ImportError:
                        # Fallback to simple bar chart if plotly not available
                        status_data = pd.DataFrame({
                            'Status': ['Active', 'Inactive'],
                            'Count': [active_count, inactive_count]
                        })
                        st.bar_chart(status_data.set_index('Status'))
                else:
                    st.info("No rules to display")
            
            with col_pie2:
                st.markdown("**Top Categories by Rule Count**")
                if category_counts:
                    # Sort categories by count and show top 5
                    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    try:
                        import plotly.express as px
                        top_cat_data = pd.DataFrame(sorted_categories, columns=['Category', 'Count'])
                        fig = px.pie(top_cat_data, values='Count', names='Category',
                                   title="Top Categories by Rule Count")
                        fig.update_layout(height=350, showlegend=True)
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
                    except ImportError:
                        # Fallback to bar chart
                        top_cat_df = pd.DataFrame(sorted_categories, columns=['Category', 'Count'])
                        st.bar_chart(top_cat_df.set_index('Category'))
                else:
                    st.info("No category data available")
            
            st.markdown("---")
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox(
                    "Filter by Status:",
                    ["All", "Active Only", "Inactive Only"],
                    key="history_status_filter"
                )
            
            with col2:
                sort_option = st.selectbox(
                    "Sort by:",
                    ["Creation Date (Newest)", "Creation Date (Oldest)", "Name A-Z", "Priority High-Low"],
                    key="history_sort_option"
                )
            
            # Apply filters
            filtered_rules = sorted_rules.copy()
            
            if status_filter == "Active Only":
                filtered_rules = [r for r in filtered_rules if r.get('active', True)]
            elif status_filter == "Inactive Only":
                filtered_rules = [r for r in filtered_rules if not r.get('active', True)]
            
            # Apply sorting
            if sort_option == "Creation Date (Oldest)":
                try:
                    filtered_rules = sorted(filtered_rules, 
                                          key=lambda x: x.get('created_at', '9999-12-31T23:59:59'), 
                                          reverse=False)
                except:
                    pass
            elif sort_option == "Name A-Z":
                filtered_rules = sorted(filtered_rules, key=lambda x: x.get('name', '').lower())
            elif sort_option == "Priority High-Low":
                filtered_rules = sorted(filtered_rules, key=lambda x: x.get('priority', 0), reverse=True)
            
            st.subheader(f"Rule History ({len(filtered_rules)} rules)")
            
            if not filtered_rules:
                st.info("No rules match the current filters.")
            else:
                # Display rules in a table format
                for i, rule in enumerate(filtered_rules):
                    rule_id = rule.get("id", f"rule_{i}")
                    name = rule.get("name", "Unnamed Rule")
                    description = rule.get("description", "No description")
                    category = rule.get("category", "")
                    subcategory = rule.get("subcategory", "")
                    priority = rule.get("priority", 0)
                    is_active = rule.get("active", True)
                    created_at = rule.get("created_at", "Unknown")
                    created_by = rule.get("created_by", "Unknown")
                    last_modified = rule.get("last_modified_at", "Not modified")
                    
                    # Format creation date
                    if created_at != "Unknown":
                        try:
                            created_date = datetime.datetime.fromisoformat(created_at)
                            formatted_date = created_date.strftime("%Y-%m-%d %H:%M")
                            time_ago = datetime.datetime.now() - created_date
                            if time_ago.days > 0:
                                time_ago_str = f"{time_ago.days} days ago"
                            elif time_ago.seconds > 3600:
                                hours = time_ago.seconds // 3600
                                time_ago_str = f"{hours} hours ago"
                            else:
                                minutes = time_ago.seconds // 60
                                time_ago_str = f"{minutes} minutes ago"
                        except:
                            formatted_date = created_at
                            time_ago_str = "Unknown"
                    else:
                        formatted_date = "Unknown"
                        time_ago_str = "Unknown"
                    
                    # Format last modified date
                    if last_modified != "Not modified":
                        try:
                            modified_date = datetime.datetime.fromisoformat(last_modified)
                            formatted_modified = modified_date.strftime("%Y-%m-%d %H:%M")
                        except:
                            formatted_modified = last_modified
                    else:
                        formatted_modified = "Not modified"
                    
                    # Create rule card
                    status_icon = "✅" if is_active else "❌"
                    priority_color = "🔴" if priority >= 90 else "🟡" if priority >= 70 else "🟢"
                    
                    with st.expander(f"{status_icon} {priority_color} 💰 **{name}** (Created: {time_ago_str}) → {category} → {subcategory}"):
                        col1, col2 = st.columns([2, 2])
                        
                        with col1:
                            st.write(f"**Rule Details:**")
                            st.write(f"• **Name:** {name}")
                            st.write(f"• **ID:** `{rule_id}`")
                            st.write(f"• **Description:** {description}")
                            st.write(f"• **Category:** {category} → {subcategory}")
                            st.write(f"• **Priority:** {priority}")
                            st.write(f"• **Status:** {'✅ Active' if is_active else '❌ Inactive'}")
                        
                        with col2:
                            st.write(f"**Timeline:**")
                            st.write(f"• **Created:** {formatted_date}")
                            st.write(f"• **Created by:** {created_by}")
                            st.write(f"• **Last modified:** {formatted_modified}")
                            
                            # Show conditions
                            conditions = rule.get("conditions", {})
                            if conditions:
                                st.write("**Conditions:**")
                                if 'field' in conditions:
                                    # Single condition
                                    condition_text = format_condition_display(conditions)
                                    st.code(condition_text, language="text")
                                else:
                                    # Multiple conditions  
                                    logic_op = conditions.get("operator", "AND")
                                    st.write(f"*Logic: {logic_op}*")
                                    for j, cond in enumerate(conditions.get("rules", [])):
                                        condition_text = format_condition_display(cond)
                                        st.code(f"{j+1}. {condition_text}", language="text")

    with tab4:
        # Rule Guide Tab
        st.subheader("📖 Rule Creation Guide")
        
        st.markdown("""
        Welcome to the Rule Management Guide! This guide will help you create effective categorization rules.
        """)
        
        # Quick start section
        with st.expander("🚀 Quick Start", expanded=True):
            st.markdown("""
            ### Creating Your First Rule
            
            1. **Go to the 'Add Rule' tab**
            2. **Add conditions** - Define when the rule should apply (e.g., "Counterparty_Name contains 'ALBERT HEIJN'")
            3. **Choose category** - Select where transactions should be categorized (e.g., "Food & Dining → Groceries")
            4. **Set priority** - Higher numbers = higher priority (1-100)
            5. **Test the rule** - See which transactions match your conditions
            6. **Save & activate** - Your rule is now ready to categorize transactions!
            """)
        
        # Field guide
        with st.expander("📋 Available Fields"):
            st.markdown("**Transaction Fields You Can Use:**")
            for field in available_fields:
                st.write(f"• **`{field}`** - {get_field_description(field)}")
        
        # Operator guide
        with st.expander("🔧 Operators Guide"):
            st.markdown("**Available Operators:**")
            st.markdown("• **`contains`** - Field contains the value (e.g., 'ALBERT' in 'ALBERT HEIJN')")
            st.markdown("• **`equals`** - Field exactly matches the value")
            st.markdown("• **`starts_with`** - Field starts with the value")
            st.markdown("• **`ends_with`** - Field ends with the value")
            st.markdown("• **`greater_than`** - Field value is greater than the specified number")
            st.markdown("• **`less_than`** - Field value is less than the specified number")
            st.markdown("• **`regex`** - Field matches a regular expression pattern")
            st.markdown("• **`in`** - Field value is in a list of values (enter one value per line)")
        
        # Examples section
        with st.expander("💡 Rule Examples"):
            st.markdown("""
            ### Common Rule Patterns
            
            **Grocery Stores:**
            - Field: `Counterparty_Name` 
            - Operator: `contains`
            - Value: `ALBERT HEIJN`
            - Category: Food & Dining → Groceries
            
            **Rent Payments:**
            - Field: `Counterparty_Name`
            - Operator: `equals` 
            - Value: `John Smith Landlord`
            - Category: Housing & Utilities → Rent
            
            **Multiple Coffee Shops (using 'in' operator):**
            - Field: `Counterparty_Name`
            - Operator: `in`
            - Values: 
              ```
              Starbucks
              Costa Coffee  
              Cafe Nero
              ```
            - Category: Food & Dining → Restaurants
            
            **Large Transactions:**
            - Field: `Amount`
            - Operator: `greater_than`
            - Value: `1000`
            - Category: Financial Services → Investments
            """)
        
        # Best practices
        with st.expander("✨ Best Practices"):
            st.markdown("""
            ### Rule Creation Tips
            
            **🎯 Priority Guidelines:**
            - **90-100**: Very specific rules (exact counterparty names)
            - **70-89**: Moderately specific rules (contains specific keywords)
            - **50-69**: General rules (broader patterns)
            - **1-49**: Catch-all rules (very general patterns)
            
            **⚖️ Logic Operators:**
            - **AND**: All conditions must be true (more restrictive)
            - **OR**: Any condition can be true (more inclusive)
            
            **🔍 Testing Rules:**
            - Always preview your rule before saving
            - Check that it matches the expected transactions
            - Avoid overly broad rules that catch unintended transactions
            
            **📈 Performance Tips:**
            - Use specific counterparty names when possible
            - Avoid regex unless necessary (slower performance)
            - Higher priority rules are checked first
            """)
        
        # Troubleshooting
        with st.expander("🛠️ Troubleshooting"):
            st.markdown("""
            ### Common Issues & Solutions
            
            **Rule not matching transactions:**
            - Check spelling and case sensitivity
            - Verify the field contains the expected data
            - Try using 'contains' instead of 'equals'
            
            **Rule matching too many transactions:**
            - Add more specific conditions
            - Use AND logic instead of OR
            - Increase specificity of values
            
            **Rule conflicts:**
            - Check rule priorities (higher priority wins)
            - Ensure rule conditions don't overlap unintentionally
            - Test rules individually
            """)

def get_field_description(field):
    """Get description for a field"""
    descriptions = {
        "Date": "Transaction date",
        "Amount": "Transaction amount (positive for income, negative for expenses)",
        "Description": "Transaction description from bank",
        "Counterparty_Name": "Name of the other party in the transaction",
        "Account_Number": "Your account number",
        "Transaction_Type": "Type of transaction (e.g., payment, transfer)",
        "Reference": "Transaction reference or memo",
        "Balance_After": "Account balance after this transaction",
        "Currency": "Currency of the transaction"
    }
    return descriptions.get(field, "Transaction field")
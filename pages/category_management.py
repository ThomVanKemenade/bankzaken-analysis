import streamlit as st
import json
from pathlib import Path

def load_categories():
    """Load categories from the JSON file"""
    categories_file = Path(__file__).parent.parent / "categories" / "categories.json"
    try:
        with open(categories_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Categories file not found: {categories_file}")
        return {"categories": {}}
    except json.JSONDecodeError:
        st.error("Invalid JSON in categories file")
        return {"categories": {}}

def save_categories(categories_data):
    """Save categories to the JSON file"""
    categories_file = Path(__file__).parent.parent / "categories" / "categories.json"
    try:
        with open(categories_file, 'w', encoding='utf-8') as f:
            json.dump(categories_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving categories: {e}")
        return False

def category_management():
    """Category Management page - manage categories, subcategories, and labels"""
    st.title("🏷️ Category Management")
    st.markdown("---")
    
    # Load categories
    categories_data = load_categories()
    categories = categories_data.get("categories", {})
    
    # Main tab navigation
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View Categories", "➕ Add Category", "🏷️ Add Subcategory", "✏️ Manage Categories"])
    
    # View All Categories Tab
    with tab1:
        st.subheader("📋 Category Overview")
        
        if not categories:
            st.info("No categories defined yet. Use the other tabs to add categories.")
            return
        
        # Statistics
        total_categories = len(categories)
        total_subcategories = sum(len(cat.get("subcategories", {})) for cat in categories.values())
        active_categories = sum(1 for cat in categories.values() if cat.get('active', True))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Categories", total_categories)
        with col2:
            st.metric("Active Categories", active_categories)
        with col3:
            st.metric("Total Subcategories", total_subcategories)
        
        st.markdown("---")
        
        # Display categories in a more organized way
        for cat_name, cat_data in categories.items():
            status_icon = "✅" if cat_data.get('active', True) else "❌"
            
            with st.expander(f"{status_icon} **{cat_name}** ({len(cat_data.get('subcategories', {}))} subcategories)"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Description:** {cat_data.get('description', 'No description')}")
                    st.write(f"**Status:** {'Active' if cat_data.get('active', True) else 'Inactive'}")
                    
                    subcategories = cat_data.get("subcategories", {})
                    if subcategories:
                        st.write("**Subcategories:**")
                        for subcat_name, subcat_data in subcategories.items():
                            subcat_status = "✅" if subcat_data.get('active', True) else "❌"
                            st.write(f"  {subcat_status} **{subcat_name}**")
                            st.write(f"      *{subcat_data.get('description', 'No description')}*")
                    else:
                        st.write("*No subcategories defined*")
                
                with col2:
                    st.write("**Quick Actions:**")
                    
                    # Edit category button
                    if st.button(f"✏️ Edit", key=f"quick_edit_cat_{cat_name}", help="Edit this category"):
                        st.session_state['edit_category'] = cat_name
                        st.session_state['manage_action'] = "edit_category"
                        st.rerun()
                    
                    # Manage subcategories button
                    if st.button(f"🏷️ Subcategories", key=f"manage_subcat_{cat_name}", help="Manage subcategories"):
                        st.session_state['manage_category'] = cat_name
                        st.session_state['manage_action'] = "manage_subcategories"
                        st.rerun()
    
    # Add Category Tab
    with tab2:
        st.subheader("➕ Add New Category")
        st.info("💡 **Tip:** Choose descriptive names and add subcategories to organize your transactions better!")
        
        with st.form("add_category_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_cat_name = st.text_input("Category Name *", help="Enter a unique category name")
                new_cat_description = st.text_area("Description", help="Describe what this category covers")
            
            with col2:
                new_cat_active = st.checkbox("Active", value=True, help="Active categories are available for rule creation")
                
                # Preview existing categories
                if categories:
                    st.write("**Existing Categories:**")
                    for cat_name in list(categories.keys())[:5]:
                        st.write(f"• {cat_name}")
                    if len(categories) > 5:
                        st.write(f"... and {len(categories) - 5} more")
            
            submitted = st.form_submit_button("Add Category", type="primary")
            
            if submitted:
                if not new_cat_name:
                    st.error("Please provide a category name.")
                elif new_cat_name in categories:
                    st.error(f"Category '{new_cat_name}' already exists. Please choose a different name.")
                else:
                    categories[new_cat_name] = {
                        "description": new_cat_description,
                        "active": new_cat_active,
                        "subcategories": {}
                    }
                    
                    if save_categories(categories_data):
                        st.success(f"✅ Category '{new_cat_name}' added successfully!")
                        st.info(f"💡 Next step: Add subcategories to '{new_cat_name}' using the 'Add Subcategory' tab.")
                        st.rerun()
                    else:
                        st.error("Failed to save the new category.")
    
    # Add Subcategory Tab
    with tab3:
        st.subheader("🏷️ Add New Subcategory")
        
        if not categories:
            st.info("No categories available. Please add some categories first using the 'Add Category' tab.")
        else:
            # Category selection
            category_names = list(categories.keys())
            selected_category = st.selectbox("Select Category", [""] + category_names, key="add_subcat_category_select")
            
            if selected_category:
                category = categories[selected_category]
                subcategories = category.get("subcategories", {})
                
                st.info(f"Adding subcategory to: **{selected_category}**")
                
                with st.form("add_new_subcategory"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_subcat_name = st.text_input("Subcategory Name *")
                        new_subcat_description = st.text_area("Description")
                    
                    with col2:
                        new_subcat_active = st.checkbox("Active", value=True)
                        
                        # Show existing subcategories
                        if subcategories:
                            st.write("**Existing Subcategories:**")
                            for existing_name in list(subcategories.keys())[:5]:
                                st.write(f"• {existing_name}")
                            if len(subcategories) > 5:
                                st.write(f"... and {len(subcategories) - 5} more")
                    
                    add_subcat_submitted = st.form_submit_button("➕ Add Subcategory", type="primary")
                    
                    if add_subcat_submitted:
                        if not new_subcat_name:
                            st.error("Please provide a subcategory name.")
                        elif new_subcat_name in subcategories:
                            st.error(f"Subcategory '{new_subcat_name}' already exists in this category.")
                        else:
                            if "subcategories" not in categories[selected_category]:
                                categories[selected_category]["subcategories"] = {}
                            
                            categories[selected_category]["subcategories"][new_subcat_name] = {
                                "description": new_subcat_description,
                                "active": new_subcat_active
                            }
                            
                            if save_categories(categories_data):
                                st.success(f"✅ Subcategory '{new_subcat_name}' added successfully to '{selected_category}'!")
                                st.rerun()
                            else:
                                st.error("Failed to save the new subcategory.")
            else:
                st.info("👆 Please select a category from the dropdown above.")
    
    # Manage Categories Tab  
    with tab4:
        st.subheader("✏️ Manage Categories & Subcategories")
        
        if not categories:
            st.info("No categories available. Please add some categories first using the 'Add Category' tab.")
        else:
            # Category selection
            category_names = list(categories.keys())
            selected_category = st.selectbox("Select Category to Manage", [""] + category_names, key="manage_category_select")
            
            if selected_category:
                category = categories[selected_category]
                
                st.markdown(f"### Managing: **{selected_category}**")
                
                # Sub-tabs for category and subcategory management
                subtab1, subtab2 = st.tabs(["🏷️ Category Details", "📂 Subcategories"])
                
                with subtab1:
                    # Edit category form
                    with st.form("edit_category_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            updated_name = st.text_input("Category Name", value=selected_category)
                            updated_description = st.text_area("Description", value=category.get("description", ""))
                        
                        with col2:
                            updated_active = st.checkbox("Active", value=category.get("active", True))
                            
                            # Show category stats
                            subcat_count = len(category.get("subcategories", {}))
                            st.info(f"**Current subcategories:** {subcat_count}")
                            
                            if subcat_count > 0:
                                active_subcat = sum(1 for sub in category.get("subcategories", {}).values() if sub.get('active', True))
                                st.info(f"**Active subcategories:** {active_subcat}")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            update_submitted = st.form_submit_button("💾 Update Category", type="primary")
                        with col2:
                            rename_submitted = st.form_submit_button("🔄 Rename Category")
                        with col3:
                            delete_submitted = st.form_submit_button("🗑️ Delete Category", type="secondary")
                        
                        if update_submitted:
                            categories[selected_category]["description"] = updated_description
                            categories[selected_category]["active"] = updated_active
                            
                            if save_categories(categories_data):
                                st.success(f"✅ Category '{selected_category}' updated successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to update the category.")
                        
                        if rename_submitted:
                            if updated_name and updated_name != selected_category:
                                if updated_name not in categories:
                                    # Rename the category
                                    categories[updated_name] = categories.pop(selected_category)
                                    categories[updated_name]["description"] = updated_description
                                    categories[updated_name]["active"] = updated_active
                                    
                                    if save_categories(categories_data):
                                        st.success(f"✅ Category renamed from '{selected_category}' to '{updated_name}'!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to rename the category.")
                                else:
                                    st.error(f"Category name '{updated_name}' already exists.")
                            else:
                                st.error("Please provide a new, unique category name.")
                        
                        if delete_submitted:
                            # Confirm deletion
                            if st.session_state.get(f"confirm_delete_{selected_category}", False):
                                del categories[selected_category]
                                if save_categories(categories_data):
                                    st.success(f"✅ Category '{selected_category}' deleted successfully!")
                                    if f"confirm_delete_{selected_category}" in st.session_state:
                                        del st.session_state[f"confirm_delete_{selected_category}"]
                                    st.rerun()
                                else:
                                    st.error("Failed to delete the category.")
                            else:
                                st.session_state[f"confirm_delete_{selected_category}"] = True
                                st.warning(f"⚠️ Click 'Delete Category' again to confirm deletion of '{selected_category}' and all its subcategories!")
                                st.rerun()
                
                with subtab2:
                    # Subcategory management
                    subcategories = category.get("subcategories", {})
                    
                    st.write(f"**Subcategories for {selected_category}:**")
                    
                    # Tabs for different subcategory actions
                    subcat_tab1, subcat_tab2, subcat_tab3 = st.tabs(["📋 View & Edit", "🗑️ Bulk Actions", "📊 Statistics"])
                    
                    with subcat_tab1:
                        if subcategories:
                            st.write(f"**Found {len(subcategories)} subcategories:**")
                            
                            for subcat_name, subcat_data in subcategories.items():
                                status_icon = "✅" if subcat_data.get('active', True) else "❌"
                                
                                with st.expander(f"{status_icon} **{subcat_name}**"):
                                    with st.form(f"edit_subcat_{subcat_name}"):
                                        col1, col2 = st.columns([2, 1])
                                        
                                        with col1:
                                            new_subcat_name = st.text_input("Subcategory Name", value=subcat_name, key=f"name_{subcat_name}")
                                            new_subcat_description = st.text_area("Description", value=subcat_data.get("description", ""), key=f"desc_{subcat_name}")
                                        
                                        with col2:
                                            new_subcat_active = st.checkbox("Active", value=subcat_data.get("active", True), key=f"active_{subcat_name}")
                                        
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            update_subcat = st.form_submit_button("💾 Update", key=f"update_{subcat_name}")
                                        with col2:
                                            rename_subcat = st.form_submit_button("🔄 Rename", key=f"rename_{subcat_name}")
                                        with col3:
                                            delete_subcat = st.form_submit_button("🗑️ Delete", key=f"delete_{subcat_name}")
                                        
                                        if update_subcat:
                                            categories[selected_category]["subcategories"][subcat_name]["description"] = new_subcat_description
                                            categories[selected_category]["subcategories"][subcat_name]["active"] = new_subcat_active
                                            
                                            if save_categories(categories_data):
                                                st.success(f"✅ Subcategory '{subcat_name}' updated!")
                                                st.rerun()
                                        
                                        if rename_subcat:
                                            if new_subcat_name and new_subcat_name != subcat_name:
                                                if new_subcat_name not in subcategories:
                                                    # Rename subcategory
                                                    categories[selected_category]["subcategories"][new_subcat_name] = categories[selected_category]["subcategories"].pop(subcat_name)
                                                    categories[selected_category]["subcategories"][new_subcat_name]["description"] = new_subcat_description
                                                    categories[selected_category]["subcategories"][new_subcat_name]["active"] = new_subcat_active
                                                    
                                                    if save_categories(categories_data):
                                                        st.success(f"✅ Subcategory renamed from '{subcat_name}' to '{new_subcat_name}'!")
                                                        st.rerun()
                                                else:
                                                    st.error(f"Subcategory '{new_subcat_name}' already exists in this category.")
                                        
                                        if delete_subcat:
                                            confirm_key = f"confirm_delete_subcat_{subcat_name}"
                                            if st.session_state.get(confirm_key, False):
                                                del categories[selected_category]["subcategories"][subcat_name]
                                                if save_categories(categories_data):
                                                    st.success(f"✅ Subcategory '{subcat_name}' deleted!")
                                                    if confirm_key in st.session_state:
                                                        del st.session_state[confirm_key]
                                                    st.rerun()
                                            else:
                                                st.session_state[confirm_key] = True
                                                st.warning(f"⚠️ Click 'Delete' again to confirm deletion of '{subcat_name}'!")
                                                st.rerun()
                        else:
                            st.info(f"No subcategories found for '{selected_category}'. Add some using the 'Add Subcategory' tab.")
                    
                    with subcat_tab2:
                        st.write("**Bulk Actions:**")
                        
                        if subcategories:
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                if st.button("✅ Activate All", key=f"activate_all_{selected_category}"):
                                    for subcat_name in subcategories:
                                        categories[selected_category]["subcategories"][subcat_name]["active"] = True
                                    if save_categories(categories_data):
                                        st.success("All subcategories activated!")
                                        st.rerun()
                            
                            with col2:
                                if st.button("❌ Deactivate All", key=f"deactivate_all_{selected_category}"):
                                    for subcat_name in subcategories:
                                        categories[selected_category]["subcategories"][subcat_name]["active"] = False
                                    if save_categories(categories_data):
                                        st.success("All subcategories deactivated!")
                                        st.rerun()
                            
                            with col3:
                                if st.button("🗑️ Delete All Inactive", key=f"delete_inactive_{selected_category}"):
                                    inactive_subcats = [name for name, data in subcategories.items() if not data.get('active', True)]
                                    if inactive_subcats:
                                        confirm_key = f"confirm_bulk_delete_inactive_{selected_category}"
                                        if st.session_state.get(confirm_key, False):
                                            for subcat_name in inactive_subcats:
                                                del categories[selected_category]["subcategories"][subcat_name]
                                            if save_categories(categories_data):
                                                st.success(f"Deleted {len(inactive_subcats)} inactive subcategories!")
                                                if confirm_key in st.session_state:
                                                    del st.session_state[confirm_key]
                                                st.rerun()
                                        else:
                                            st.session_state[confirm_key] = True
                                            st.warning(f"⚠️ Click again to confirm deletion of {len(inactive_subcats)} inactive subcategories!")
                                            st.rerun()
                                    else:
                                        st.info("No inactive subcategories to delete.")
                        else:
                            st.info("No subcategories available for bulk actions.")
                    
                    with subcat_tab3:
                        if subcategories:
                            total_subcats = len(subcategories)
                            active_subcats = sum(1 for sub in subcategories.values() if sub.get('active', True))
                            inactive_subcats = total_subcats - active_subcats
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Subcategories", total_subcats)
                            with col2:
                                st.metric("Active", active_subcats)
                            with col3:
                                st.metric("Inactive", inactive_subcats)
                            
                            # Show distribution
                            if total_subcats > 0:
                                st.write("**Status Distribution:**")
                                st.progress(active_subcats / total_subcats, text=f"Active: {active_subcats}/{total_subcats} ({(active_subcats/total_subcats)*100:.1f}%)")
                        else:
                            st.info("No statistics available - no subcategories defined.")
            else:
                st.info("👆 Please select a category from the dropdown above.")
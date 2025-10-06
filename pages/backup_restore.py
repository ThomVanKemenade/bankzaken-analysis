import streamlit as st
import pandas as pd
import json
import datetime
import zipfile
import tempfile
from pathlib import Path


def backup_restore():
    """Backup and Restore System"""
    st.title("💾 Backup & Restore System")
    
    # Load current data for stats
    try:
        rules_file = Path(__file__).parent.parent / "categories" / "categorization_rules.json"
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        rules = rules_data.get("categorization_rules", {}).get("rules", [])
    except:
        rules = []
    
    try:
        categories_file = Path(__file__).parent.parent / "categories" / "categories.json"
        with open(categories_file, 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
    except:
        categories_data = {}
    
    # Create backup function
    def create_backup():
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(__file__).parent.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            backup_filename = f"bankzaken_backup_{timestamp}.zip"
            backup_path = backup_dir / backup_filename
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup rules
                rules_file = Path(__file__).parent.parent / "categories" / "categorization_rules.json"
                if rules_file.exists():
                    zipf.write(rules_file, "categorization_rules.json")
                
                # Backup categories
                categories_file = Path(__file__).parent.parent / "categories" / "categories.json"
                if categories_file.exists():
                    zipf.write(categories_file, "categories.json")
                
                # Backup transaction data if it exists
                transaction_file = Path(__file__).parent.parent / "combined_transactions.csv"
                if transaction_file.exists():
                    zipf.write(transaction_file, "combined_transactions.csv")
                
                # Create backup manifest
                manifest = {
                    "backup_date": datetime.datetime.now().isoformat(),
                    "app_version": "1.0",
                    "files_included": [],
                    "rules_count": len(rules),
                    "categories_count": len(categories_data.get("categories", {}))
                }
                
                # Add files to manifest
                for file_info in zipf.filelist:
                    manifest["files_included"].append(file_info.filename)
                
                # Write manifest to zip
                manifest_json = json.dumps(manifest, indent=2)
                zipf.writestr("backup_manifest.json", manifest_json)
            
            return backup_path, manifest
        except Exception as e:
            st.error(f"Backup failed: {e}")
            return None, None
    
    # Backup section
    st.markdown("### 📤 Create Backup")
    st.info("💡 Regular backups protect your rules, categories, and transaction data from accidental loss.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**What will be backed up:**")
        st.write("• ⚙️ All categorization rules")
        st.write("• 🏷️ Category structure")
        st.write("• 💰 Transaction data (if available)")
        st.write("• 📋 Backup manifest with metadata")
    
    with col2:
        if st.button("🔄 Create Backup Now", type="primary"):
            with st.spinner("Creating backup..."):
                backup_path, manifest = create_backup()
                
                if backup_path and manifest:
                    st.success(f"✅ Backup created successfully!")
                    st.write(f"**File:** `{backup_path.name}`")
                    st.write(f"**Size:** {backup_path.stat().st_size / 1024:.1f} KB")
                    st.write(f"**Rules:** {manifest['rules_count']}")
                    st.write(f"**Categories:** {manifest['categories_count']}")
                    
                    # Provide download link
                    with open(backup_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Backup",
                            data=f.read(),
                            file_name=backup_path.name,
                            mime="application/zip"
                        )
    
    st.markdown("---")
    
    # Restore section
    st.markdown("### 📥 Restore from Backup")
    st.warning("⚠️ **Warning:** Restoring will replace your current rules and categories. Create a backup first!")
    
    uploaded_backup = st.file_uploader(
        "Upload backup file",
        type=["zip"],
        help="Select a backup file created by this system"
    )
    
    if uploaded_backup:
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_file:
                tmp_file.write(uploaded_backup.read())
                tmp_path = tmp_file.name
            
            # Read backup manifest
            with zipfile.ZipFile(tmp_path, 'r') as zipf:
                if "backup_manifest.json" in zipf.namelist():
                    manifest_data = json.loads(zipf.read("backup_manifest.json"))
                    
                    st.markdown("**📋 Backup Information:**")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        backup_date = manifest_data.get("backup_date", "Unknown")
                        if backup_date != "Unknown":
                            date_obj = datetime.datetime.fromisoformat(backup_date)
                            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
                            st.write(f"**Date:** {formatted_date}")
                        else:
                            st.write(f"**Date:** {backup_date}")
                        
                        st.write(f"**Rules:** {manifest_data.get('rules_count', 'Unknown')}")
                        st.write(f"**Categories:** {manifest_data.get('categories_count', 'Unknown')}")
                    
                    with col2:
                        st.write(f"**App Version:** {manifest_data.get('app_version', 'Unknown')}")
                        st.write("**Files in backup:**")
                        for file in manifest_data.get("files_included", []):
                            st.write(f"• {file}")
                    
                    # Confirm restore
                    if st.button("🔄 Restore from Backup", type="secondary"):
                        if st.session_state.get("confirm_restore", False):
                            try:
                                # Perform restore
                                with zipfile.ZipFile(tmp_path, 'r') as zipf:
                                    # Restore rules
                                    if "categorization_rules.json" in zipf.namelist():
                                        rules_content = zipf.read("categorization_rules.json")
                                        rules_file = Path(__file__).parent.parent / "categories" / "categorization_rules.json"
                                        with open(rules_file, 'wb') as f:
                                            f.write(rules_content)
                                    
                                    # Restore categories
                                    if "categories.json" in zipf.namelist():
                                        categories_content = zipf.read("categories.json")
                                        categories_file = Path(__file__).parent.parent / "categories" / "categories.json"
                                        with open(categories_file, 'wb') as f:
                                            f.write(categories_content)
                                
                                st.success("✅ Backup restored successfully!")
                                st.info("🔄 Please refresh the page to see the restored data.")
                                st.session_state["confirm_restore"] = False
                                
                            except Exception as e:
                                st.error(f"Restore failed: {e}")
                        else:
                            st.warning("⚠️ Click 'Confirm Restore' below to proceed.")
                            if st.button("Confirm Restore", type="primary"):
                                st.session_state["confirm_restore"] = True
                                st.rerun()
                
        except Exception as e:
            st.error(f"Error reading backup file: {e}")
    
    st.markdown("---")
    
    # Current system status
    st.markdown("### 📊 Current System Status")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Rules", len([r for r in rules if r.get("active", True)]))
    
    with col2:
        st.metric("Total Categories", len(categories_data.get("categories", {})))
    
    with col3:
        # Check if transaction data exists
        transaction_file = Path(__file__).parent.parent / "combined_transactions.csv"
        if transaction_file.exists():
            st.metric("Transaction Data", "Available")
        else:
            st.metric("Transaction Data", "Not Found")
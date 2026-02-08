# Version: v1.2.1
# Description: Bookmark Gallery with non-destructive Config.json update
# Changes: Optimized update_config_url to preserve complex JSON structures

import streamlit as st
import json
import os

# --- CONFIGURATION ---
DB_FILE = "Gems_bookmark.json"
CONFIG_FILE = "config.json"

def load_json(file_path):
    """Load data from a JSON file safely."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error reading {file_path}: {e}")
        return None

def save_json(file_path, data):
    """Save data to a JSON file with indentation."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving {file_path}: {e}")
        return False

def update_config_url(new_url):
    """Update only the 'url' key in config.json while preserving other fields."""
    if not os.path.exists(CONFIG_FILE):
        st.warning(f"Warning: '{CONFIG_FILE}' not found in root directory. Please ensure the file exists.")
        return False
    
    config_content = load_json(CONFIG_FILE)
    
    if config_content is dict or isinstance(config_content, dict):
        # Update only the URL field
        config_content["url"] = new_url
        return save_json(CONFIG_FILE, config_content)
    else:
        st.error(f"Failed to parse '{CONFIG_FILE}'. Please check if the JSON format is valid.")
        return False

def main():
    st.set_page_config(page_title="Gems Bookmark Gallery", layout="wide")

    # --- SESSION STATE INITIALIZATION ---
    if "edit_index" not in st.session_state:
        st.session_state.edit_index = None

    # --- UI HEADER ---
    st.title("Gems Bookmark Gallery")
    st.markdown("### Version: v1.2.1")

    # --- INPUT/EDIT SECTION ---
    bookmarks = load_json(DB_FILE)
    if bookmarks is None:
        bookmarks = []
    
    is_edit_mode = st.session_state.edit_index is not None
    default_name = ""
    default_url = ""
    default_desc = ""

    if is_edit_mode:
        idx = st.session_state.edit_index
        if 0 <= idx < len(bookmarks):
            default_name = bookmarks[idx]["name"]
            default_url = bookmarks[idx]["url"]
            default_desc = bookmarks[idx]["description"]

    with st.expander("Bookmark Editor", expanded=True):
        st.subheader("Edit/Update Bookmark" if is_edit_mode else "Add New Bookmark")
        
        col_name, col_url = st.columns(2)
        with col_name:
            name = st.text_input("Bookmark Name", value=default_name, placeholder="e.g. Gemini App")
        with col_url:
            url = st.text_input("URL", value=default_url, placeholder="https://gemini.google.com/app")
        
        description = st.text_area("Description", value=default_desc, placeholder="Describe this bookmark...")
        
        btn_col1, btn_col2 = st.columns([1, 5])
        with btn_col1:
            if is_edit_mode:
                if st.button("Update Bookmark", type="primary"):
                    if name and url:
                        bookmarks[st.session_state.edit_index] = {
                            "name": name,
                            "url": url,
                            "description": description
                        }
                        save_json(DB_FILE, bookmarks)
                        st.session_state.edit_index = None
                        st.success("Bookmark updated!")
                        st.rerun()
                    else:
                        st.error("Name and URL are required.")
            else:
                if st.button("Save Bookmark", type="primary"):
                    if name and url:
                        new_bookmark = {"name": name, "url": url, "description": description}
                        bookmarks.append(new_bookmark)
                        save_json(DB_FILE, bookmarks)
                        st.success("Bookmark saved!")
                        st.rerun()
                    else:
                        st.error("Name and URL are required.")

        with btn_col2:
            if is_edit_mode:
                if st.button("Cancel Edit"):
                    st.session_state.edit_index = None
                    st.rerun()

    st.divider()

    # --- GALLERY DISPLAY SECTION ---
    st.subheader("My Collection")

    if not bookmarks:
        st.info("No bookmarks found. Add your first one above!")
    else:
        # Create a grid layout (3 columns)
        cols = st.columns(3)
        for index, bookmark in enumerate(bookmarks):
            with cols[index % 3]:
                with st.container(border=True):
                    st.markdown(f"### {bookmark['name']}")
                    st.write(bookmark['description'] if bookmark['description'] else "No description.")
                    
                    # Apply URL to config.json
                    if st.button(f"Apply to Config", key=f"apply_{index}", width='stretch', type="secondary"):
                        if update_config_url(bookmark['url']):
                            st.toast(f"Config updated with: {bookmark['url']}", icon="🚀")
                    
                    st.write("---")
                    # Management buttons
                    edit_col, del_col = st.columns(2)
                    with edit_col:
                        if st.button(f"Edit", key=f"edit_btn_{index}", width='stretch'):
                            st.session_state.edit_index = index
                            st.rerun()
                    with del_col:
                        if st.button(f"Delete", key=f"del_btn_{index}", width='stretch'):
                            bookmarks.pop(index)
                            save_json(DB_FILE, bookmarks)
                            if st.session_state.edit_index == index:
                                st.session_state.edit_index = None
                            st.rerun()

if __name__ == "__main__":
    main()
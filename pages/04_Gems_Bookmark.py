# Version: v1.3.2
# Description: Bookmark Gallery with optimized Edit-Fetch synchronization.
# Changes: Fixed data display priority so Auto-Fetched data shows up during Editing.

import streamlit as st
import json
import os
import time

# --- CONFIGURATION ---
DB_FILE = "Gems_bookmark.json"
CONFIG_FILE = "config.json"
TASK_FILE = "task.json"
SCRAPED_FILE = "scraped_info.json"

def load_json(file_path):
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error reading {file_path}: {e}")
        return None

def save_json(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving {file_path}: {e}")
        return False

def update_config_url(new_url):
    if not os.path.exists(CONFIG_FILE): return False
    config_content = load_json(CONFIG_FILE)
    if isinstance(config_content, dict):
        config_content["url"] = new_url
        return save_json(CONFIG_FILE, config_content)
    return False

def trigger_watcher_fetch(url):
    update_config_url(url)
    task = {"action": "scrape_gem_info"}
    save_json(TASK_FILE, task)
    if os.path.exists(SCRAPED_FILE):
        os.remove(SCRAPED_FILE)

def main():
    st.set_page_config(page_title="Gems Bookmark Gallery", layout="wide")

    # Initialize session states
    if "edit_index" not in st.session_state: st.session_state.edit_index = None
    if "temp_name" not in st.session_state: st.session_state.temp_name = ""
    if "temp_desc" not in st.session_state: st.session_state.temp_desc = ""

    st.title("Gems Bookmark Gallery")
    st.markdown("### Version: v1.3.2")

    bookmarks = load_json(DB_FILE) or []
    is_edit_mode = st.session_state.edit_index is not None

    # --- EDITOR SECTION ---
    with st.expander("Bookmark Editor", expanded=True):
        st.subheader("Edit Bookmark" if is_edit_mode else "Add New Bookmark")
        
        # URL Input
        default_url = bookmarks[st.session_state.edit_index]["url"] if is_edit_mode else ""
        url = st.text_input("URL", value=default_url, placeholder="https://gemini.google.com/app/gems/...")
        
        # Auto-Fetch Button
        if st.button("🔍 Auto-Fetch via Engine", width='stretch'):
            if url:
                trigger_watcher_fetch(url)
                with st.status("Engine is scraping Gem info...", expanded=True) as status:
                    found = False
                    for _ in range(25):
                        time.sleep(1)
                        if os.path.exists(SCRAPED_FILE):
                            res = load_json(SCRAPED_FILE)
                            if res:
                                # Update session state with new data
                                st.session_state.temp_name = res.get("name", "")
                                st.session_state.temp_desc = res.get("description", "")
                                found = True
                                break
                    if found:
                        status.update(label="Fetch Successful!", state="complete")
                        st.rerun()
                    else:
                        status.update(label="Fetch Failed.", state="error")
            else:
                st.error("Please enter a URL first.")

        # Display Logic: Priority -> Temp Data > Existing Bookmark Data > Empty
        if is_edit_mode:
            display_name = st.session_state.temp_name if st.session_state.temp_name else bookmarks[st.session_state.edit_index]["name"]
            display_desc = st.session_state.temp_desc if st.session_state.temp_desc else bookmarks[st.session_state.edit_index]["description"]
        else:
            display_name = st.session_state.temp_name
            display_desc = st.session_state.temp_desc

        col_name, _ = st.columns([1, 1])
        with col_name:
            name = st.text_input("Bookmark Name", value=display_name)
        
        description = st.text_area("Description", value=display_desc)
        
        # Action Buttons
        btn_col1, btn_col2 = st.columns([1, 5])
        with btn_col1:
            if st.button("Save", type="primary", width='stretch'):
                new_entry = {"name": name, "url": url, "description": description}
                if is_edit_mode:
                    bookmarks[st.session_state.edit_index] = new_entry
                else:
                    bookmarks.append(new_entry)
                
                if save_json(DB_FILE, bookmarks):
                    # Clear states after save
                    st.session_state.edit_index = None
                    st.session_state.temp_name = ""
                    st.session_state.temp_desc = ""
                    st.rerun()
        with btn_col2:
            if is_edit_mode and st.button("Cancel"):
                st.session_state.edit_index = None
                st.session_state.temp_name = ""
                st.session_state.temp_desc = ""
                st.rerun()

    st.divider()
    # --- GALLERY SECTION ---
    if not bookmarks:
        st.info("No bookmarks.")
    else:
        cols = st.columns(3)
        for index, b in enumerate(bookmarks):
            with cols[index % 3]:
                with st.container(border=True):
                    st.markdown(f"### {b['name']}")
                    st.write(b['description'] or "No description.")
                    if st.button(f"Apply to Config", key=f"app_{index}", width='stretch'):
                        if update_config_url(b['url']): st.toast("Config updated!")
                    st.write("---")
                    e_col, d_col = st.columns(2)
                    with e_col:
                        if st.button(f"Edit", key=f"ed_{index}", width='stretch'):
                            # Reset temp data when starting a fresh edit
                            st.session_state.temp_name = ""
                            st.session_state.temp_desc = ""
                            st.session_state.edit_index = index
                            st.rerun()
                    with d_col:
                        if st.button(f"Delete", key=f"de_{index}", width='stretch'):
                            bookmarks.pop(index)
                            save_json(DB_FILE, bookmarks)
                            st.rerun()

if __name__ == "__main__":
    main()
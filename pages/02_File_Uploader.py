# Version: 1.2.4
# Description: Fixed UnicodeDecodeError by adding UTF-8 encoding to all file operations.
# Ensures compatibility with special characters in config.json.

import streamlit as st
import json
import os
from PIL import Image

# --- CONFIGURATION ---
CONFIG_FILE = "config.json"
UPLOAD_DIR = "temp_uploads"

def init_config():
    """
    Validates config.json existence with UTF-8 encoding.
    Stops execution if file is missing.
    """
    if not os.path.exists(CONFIG_FILE):
        st.error(f"Critical Error: '{CONFIG_FILE}' not found. Program halted.")
        st.stop()
    
    try:
        # Added encoding='utf-8' to prevent UnicodeDecodeError
        with open(CONFIG_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        st.error(f"Error: '{CONFIG_FILE}' contains invalid JSON.")
        st.stop()
    except UnicodeDecodeError:
        st.error(f"Encoding Error: Failed to read '{CONFIG_FILE}'. Ensure it is UTF-8 encoded.")
        st.stop()

    if "upload_task" not in data:
        data["upload_task"] = []
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    
    return data

def save_config(file_paths):
    """Safely updates upload_task while preserving other keys with UTF-8 encoding."""
    if not os.path.exists(CONFIG_FILE):
        return

    try:
        with open(CONFIG_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        data = {}

    data["upload_task"] = file_paths
    
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def clear_all_files():
    """Removes all files and performs a FULL rerun to reset media cache."""
    for file_info in st.session_state.get('uploaded_files_info', []):
        path = file_info['path']
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
    
    st.session_state.uploaded_files_info = []
    save_config([])
    st.rerun()

def delete_single_file(index):
    """Deletes a single file and refreshes the fragment."""
    file_to_remove = st.session_state.uploaded_files_info.pop(index)
    path = file_to_remove['path']
    if os.path.exists(path):
        os.remove(path)
    
    current_paths = [f['path'] for f in st.session_state.uploaded_files_info]
    save_config(current_paths)

@st.fragment
def file_preview_grid():
    """Fragmented gallery for efficient local UI updates."""
    if not st.session_state.uploaded_files_info:
        st.info("No files in the current task.")
        return

    st.subheader(f"Gallery ({len(st.session_state.uploaded_files_info)})")
    
    if st.button("🗑️ Clear All Files", key="clear_all_btn", width='stretch', type="primary"):
        clear_all_files()
    
    st.divider()

    cols = st.columns(5)
    for idx, file_data in enumerate(st.session_state.uploaded_files_info):
        with cols[idx % 5]:
            with st.container(border=True):
                if "image" in file_data['type']:
                    try:
                        img = Image.open(file_data['path'])
                        st.image(img, width='stretch')
                    except Exception:
                        st.error("Preview Error")
                else:
                    st.info("📄 Document")
                
                st.caption(file_data['name'], help=file_data['path'])
                
                if st.button("Remove", key=f"del_{idx}", width='stretch', type="secondary"):
                    delete_single_file(idx)
                    st.rerun(scope="fragment")

def main():
    st.set_page_config(page_title="Secure Gallery v1.2.4", layout="wide")
    st.title("File Management & Preview")

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    config_data = init_config()

    if "uploaded_files_info" not in st.session_state:
        initial_list = []
        for path in config_data.get("upload_task", []):
            if os.path.exists(path):
                initial_list.append({
                    "name": os.path.basename(path),
                    "path": path,
                    "type": "image" if path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')) else "file"
                })
        st.session_state.uploaded_files_info = initial_list

    # --- SIDEBAR ---
    st.sidebar.header("Uploader")
    uploaded_files = st.sidebar.file_uploader(
        "Upload files", 
        accept_multiple_files=True,
        key="uploader"
    )

    if uploaded_files:
        current_paths = [f['path'] for f in st.session_state.uploaded_files_info]
        added = False
        for uploaded_file in uploaded_files:
            file_path = os.path.abspath(os.path.join(UPLOAD_DIR, uploaded_file.name))
            if file_path not in current_paths:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.session_state.uploaded_files_info.append({
                    "name": uploaded_file.name,
                    "path": file_path,
                    "type": uploaded_file.type
                })
                current_paths.append(file_path)
                added = True
        
        if added:
            save_config(current_paths)
            st.rerun()

    file_preview_grid()

if __name__ == "__main__":
    main()
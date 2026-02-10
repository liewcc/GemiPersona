# Version: 1.3.2
# Add explanation
# Description: Finalized startup logic. Ensures 'temp_uploads' is created non-destructively 
# at the very beginning of execution without affecting existing files.

import streamlit as st
import json
import os
import subprocess
import platform
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

    # Store normalized absolute paths in config for consistency
    data["upload_task"] = [os.path.abspath(p) for p in file_paths]
    
    with open(CONFIG_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def open_folder(path):
    """Opens the local file explorer at the specified path (Cross-platform)."""
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        st.sidebar.error("Folder does not exist yet.")
        return

    try:
        current_os = platform.system()
        if current_os == "Windows":
            os.startfile(abs_path)
        elif current_os == "Darwin":  # macOS
            subprocess.Popen(["open", abs_path])
        else:  # Linux
            subprocess.Popen(["xdg-open", abs_path])
    except Exception as e:
        st.sidebar.error(f"Failed to open folder: {e}")

def clear_unused_buffer():
    """Removes physical files that are NOT listed in the config task."""
    config_data = init_config()
    task_paths = [os.path.abspath(p) for p in config_data.get("upload_task", [])]
    
    removed_count = 0
    if os.path.exists(UPLOAD_DIR):
        for file_name in os.listdir(UPLOAD_DIR):
            file_path = os.path.abspath(os.path.join(UPLOAD_DIR, file_name))
            if os.path.isfile(file_path) and file_path not in task_paths:
                try:
                    os.remove(file_path)
                    removed_count += 1
                except Exception:
                    pass
    
    st.sidebar.success(f"Buffer Cleared: Removed {removed_count} unlisted files.")
    st.rerun()

def clear_all_files():
    """Removes all files with path normalization and error feedback."""
    failed_deletions = []
    
    for file_info in st.session_state.get('uploaded_files_info', []):
        abs_path = os.path.abspath(file_info['path'])
        
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception as e:
                failed_deletions.append(f"{file_info['name']} (Reason: {str(e)})")
    
    if failed_deletions:
        st.sidebar.error("Failed to delete some files from disk.")
    else:
        st.session_state.uploaded_files_info = []
        save_config([])
        st.rerun()

def delete_single_file(index):
    """Deletes a single file with error handling."""
    file_to_remove = st.session_state.uploaded_files_info[index]
    abs_path = os.path.abspath(file_to_remove['path'])
    
    try:
        if os.path.exists(abs_path):
            os.remove(abs_path)
        st.session_state.uploaded_files_info.pop(index)
        current_paths = [f['path'] for f in st.session_state.uploaded_files_info]
        save_config(current_paths)
    except Exception as e:
        st.error(f"Could not delete file: {e}")

@st.fragment
def file_preview_grid(task_list):
    """Fragmented gallery showing all files as cards with Task Icon."""
    if not st.session_state.uploaded_files_info:
        st.info("The upload folder is empty.")
        return

    st.subheader(f"Album View ({len(st.session_state.uploaded_files_info)} items)")
    
    if st.button("🗑️ Clear All Files (including delete upload file lists)", key="clear_all_btn", width='stretch', type="primary"):
        clear_all_files()
    
    st.divider()

    cols = st.columns(5)
    normalized_task_list = [os.path.abspath(p) for p in task_list]

    for idx, file_data in enumerate(st.session_state.uploaded_files_info):
        file_abs_path = os.path.abspath(file_data['path'])
        is_task_file = file_abs_path in normalized_task_list
        task_icon = " 🔖" if is_task_file else ""

        with cols[idx % 5]:
            with st.container(border=True):
                if "image" in file_data['type']:
                    try:
                        img = Image.open(file_data['path'])
                        st.image(img, width='stretch')
                    except Exception:
                        st.error("Corrupted Image")
                else:
                    ext = os.path.splitext(file_data['name'])[1].upper() or "FILE"
                    st.markdown(
                        f"""
                        <div style="height:100px; display:flex; align-items:center; justify-content:center; 
                        background-color:#f0f2f6; border-radius:10px; margin-bottom:10px;">
                            <span style="font-size:24px; font-weight:bold; color:#5f6368;">{ext}</span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                
                st.caption(f"{file_data['name']}{task_icon}", help=file_data['path'])
                
                if st.button("Remove", key=f"del_{idx}", width='stretch', type="secondary"):
                    delete_single_file(idx)
                    st.rerun(scope="fragment")

def main():
    # --- FIRST THING: INITIALIZE ENVIRONMENT ---
    # Create directory if it doesn't exist (Non-destructive)
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    st.set_page_config(page_title="Secure Gallery v1.3.1", layout="wide")
    st.title("File Management & Preview")

    config_data = init_config()
    current_task_list = config_data.get("upload_task", [])

    # Real-time scan of temp_uploads folder to ensure UI matches Disk
    synced_list = []
    disk_files = sorted(os.listdir(UPLOAD_DIR)) 
    
    for file_name in disk_files:
        abs_path = os.path.abspath(os.path.join(UPLOAD_DIR, file_name))
        if os.path.isfile(abs_path):
            is_img = file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))
            synced_list.append({
                "name": file_name,
                "path": abs_path,
                "type": "image" if is_img else "application/octet-stream"
            })
    
    st.session_state.uploaded_files_info = synced_list

    # --- SIDEBAR ---
    st.sidebar.header("Uploader")
    uploaded_files = st.sidebar.file_uploader(
        "Upload files", 
        accept_multiple_files=True,
        key="uploader"
    )

    if uploaded_files:
        current_paths = [os.path.abspath(f['path']) for f in st.session_state.uploaded_files_info]
        added = False
        for uploaded_file in uploaded_files:
            file_path = os.path.abspath(os.path.join(UPLOAD_DIR, uploaded_file.name))
            if file_path not in current_paths:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                if file_path not in [os.path.abspath(p) for p in current_task_list]:
                    current_task_list.append(file_path)
                added = True
        
        if added:
            save_config(current_task_list)
            st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("System Tools")
    
    if st.sidebar.button("📂 Open Temp Folder", width='stretch'):
        open_folder(UPLOAD_DIR)
        
    if st.sidebar.button("🧹 Clear Unused Buffer", width='stretch'):
        clear_unused_buffer()

    # Pass current task list to the fragment to render icons
    file_preview_grid(current_task_list)

if __name__ == "__main__":
    main()
import streamlit as st
import subprocess
import json
import os
import glob
import psutil
import time
from PIL import Image

# --- 1. CONFIGURATION & VERSIONING ---
# Version V26.1.7: Fixed all actions to upload_test/redo; logic now scans last 3 log lines.
APP_VERSION = "V26.1.7"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(ROOT_DIR, "watcher_engine")
DEFAULT_OUTPUT_DIR = os.path.join(ROOT_DIR, "browser_outputs")
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")
TASK_FILE = os.path.join(ROOT_DIR, "task.json")
LOG_FILE = os.path.join(ROOT_DIR, "engine.log")
TEMP_UPLOAD_DIR = os.path.join(ROOT_DIR, "temp_uploads")

if not os.path.exists(TEMP_UPLOAD_DIR):
    os.makedirs(TEMP_UPLOAD_DIR)

st.set_page_config(page_title=f"GemiPersona Pro {APP_VERSION}", layout="wide")

# --- 2. CONFIGURATION LOGIC ---
def load_config_from_disk():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None

def save_config_to_disk(updated_data):
    current_disk_cfg = load_config_from_disk() or st.session_state.config
    current_disk_cfg.update(updated_data)
    current_disk_cfg.pop('send_loop', None) 
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_disk_cfg, f, indent=4, ensure_ascii=False)
    st.session_state.config = current_disk_cfg

def initialize_config():
    default_cfg = {
        "engine_version": "Unknown", 
        "url": "https://gemini.google.com/app",
        "headless": True,
        "save_dir": DEFAULT_OUTPUT_DIR,
        "name_prefix": "",
        "name_padding": 2,
        "name_start": 1,
        "last_prompt": "",
        "upload_task": [],
        "show_debug_console": True,
        "selectors": {"textbox": 'div[role="textbox"]', "send_btn": 'button[aria-label*="Send"]', "img_list": "img"}
    }
    disk_cfg = load_config_from_disk()
    if disk_cfg:
        for key, value in disk_cfg.items():
            default_cfg[key] = value
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_cfg, f, indent=4, ensure_ascii=False)
        return default_cfg
    else:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_cfg, f, indent=4, ensure_ascii=False)
        return default_cfg

if 'config' not in st.session_state:
    st.session_state.config = initialize_config()
if 'loop_active' not in st.session_state:
    st.session_state.loop_active = False
if 'last_processed_log_line' not in st.session_state:
    st.session_state.last_processed_log_line = ""

# --- 3. SYSTEM STATUS & UTILS ---
def get_engine_info():
    for proc in psutil.process_iter(['cmdline']):
        try:
            cmd = " ".join(proc.info.get('cmdline') or []).lower()
            if "watcher.py" in cmd: return True, proc.pid
        except: continue
    return False, None

def wait_for_browser_ready(timeout=20):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if ">>> Browser Ready" in content:
                        return True
            except: pass
        time.sleep(0.5)
    return False

# --- 4. SIDEBAR LAYOUT ---
with st.sidebar:
    st.caption(f"🚀 App: {APP_VERSION} | ⚙️ Engine: {st.session_state.config.get('engine_version', 'Unknown')}")

    def auto_save_config():
        updates = {
            "url": st.session_state.url_input,
            "save_dir": st.session_state.storage_input,
            "name_prefix": st.session_state.prefix_input,
            "name_padding": st.session_state.padding_input,
            "name_start": st.session_state.start_input
        }
        save_config_to_disk(updates)

    @st.fragment(run_every="2s")
    def render_config_inputs():
        disk_data = load_config_from_disk()
        if disk_data:
            mapping = {
                "url_input": "url", "storage_input": "save_dir", "prefix_input": "name_prefix",
                "padding_input": "name_padding", "start_input": "name_start"
            }
            for widget_key, disk_key in mapping.items():
                new_val = disk_data.get(disk_key)
                if widget_key in st.session_state and st.session_state[widget_key] != new_val:
                    st.session_state[widget_key] = new_val
                elif widget_key not in st.session_state:
                    st.session_state[widget_key] = new_val

        st.text_input("Target URL", key="url_input", on_change=auto_save_config)
        st.text_input("Storage Path", key="storage_input", on_change=auto_save_config)
        
        target_path = st.session_state.config.get('save_dir', "")
        if st.button("📂 Open Folder", width='stretch'):
            if target_path and os.path.exists(target_path):
                os.startfile(os.path.normpath(target_path))
            else:
                st.toast("Invalid Path")

        st.divider()
        st.markdown("**File Naming Rules**")
        st.text_input("Name Prefix", key="prefix_input", on_change=auto_save_config)
        n_col1, n_col2 = st.columns(2)
        n_col1.number_input("Padding", min_value=1, max_value=10, key="padding_input", on_change=auto_save_config)
        n_col2.number_input("Start No.", min_value=0, key="start_input", on_change=auto_save_config)

    render_config_inputs()
    st.divider()

    is_alive, eng_pid = get_engine_info()
    VENV_PYTHON = os.path.normpath(os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe"))
    WATCHER_SCRIPT = os.path.normpath(os.path.join(ROOT_DIR, "watcher_engine", "watcher.py"))

    if not is_alive:
        if st.button("🔥 Fire up Browser (Headless)", width='stretch', type="primary"):
            subprocess.Popen([VENV_PYTHON, WATCHER_SCRIPT], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
            with open(TASK_FILE, 'w', encoding='utf-8') as f:
                json.dump({"action": "launch_headless", "timestamp": time.time()}, f)
            
            with st.spinner("Waiting for Browser Ready..."):
                if wait_for_browser_ready(timeout=25):
                    with open(TASK_FILE, 'w', encoding='utf-8') as f:
                        json.dump({"action": "check_signin", "timestamp": time.time()}, f)
                    st.toast("Browser Ready & Check-signin Sent")
                else:
                    st.error("Browser launch timeout.")
            st.rerun()
    else:
        if st.button("🛑 Shutdown System", width='stretch'):
            with open(TASK_FILE, 'w', encoding='utf-8') as f:
                json.dump({"action": "close_browser", "timestamp": time.time()}, f)
            time.sleep(1.5)
            for proc in psutil.process_iter(['cmdline']):
                try:
                    cmd = " ".join(proc.info.get('cmdline') or []).lower()
                    if "watcher.py" in cmd: proc.terminate()
                except: continue
            st.session_state.loop_active = False
            st.rerun()

    @st.fragment(run_every="2s")
    def render_sidebar_status():
        st.subheader("📡 System Status")
        active, _ = get_engine_info()
        if active: st.success("Engine: Online")
        else: st.error("Engine: Offline")
        if st.session_state.loop_active: st.warning("🔄 Loop: ACTIVE")
        else: st.info("⏹️ Loop: Idle")
    render_sidebar_status()

# --- 5. MAIN PANEL ---

@st.fragment(run_every="2s")
def render_live_status():
    log_path = os.path.join(ROOT_DIR, "engine.log")
    if os.path.exists(log_path) and st.session_state.loop_active:
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                if not lines: return
                
                # Logic: Scan last 3 lines for status signals to prevent missing trigger
                target_lines = lines[-3:]
                for line in reversed(target_lines):
                    clean_line = line.strip()
                    is_success = "[SUCCESS]" in clean_line
                    is_fail = "[FAIL]" in clean_line
                    
                    if (is_success or is_fail) and clean_line != st.session_state.last_processed_log_line:
                        disk_cfg = load_config_from_disk()
                        # Always re-trigger with upload_test_redo
                        with open(TASK_FILE, "w", encoding="utf-8") as tf:
                            json.dump({
                                "action": "upload_test_redo",
                                "subject": disk_cfg.get('last_prompt', ""),
                                "timestamp": time.time()
                            }, tf, ensure_ascii=False)
                        st.session_state.last_processed_log_line = clean_line
                        st.toast(f"Looping: upload_test_redo triggered")
                        break
        except: pass

    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    if "error" in last_line.lower() or "[FAIL]" in last_line: st.error(last_line)
                    elif "[SUCCESS]" in last_line: st.success(last_line)
                    else: st.info(last_line)
        except: pass

render_live_status()

input_prompt = st.text_area(
    "Prompt Input", 
    value=st.session_state.config.get('last_prompt', ""), 
    height=120, 
    label_visibility="collapsed"
)

if input_prompt != st.session_state.config.get('last_prompt', ""):
    save_config_to_disk({'last_prompt': input_prompt})

uploaded_files = st.file_uploader(
    "Upload", 
    type=["png", "jpg", "jpeg", "webp"], 
    accept_multiple_files=True, 
    label_visibility="collapsed"
)

if uploaded_files:
    current_tasks = st.session_state.config.get("upload_task", [])
    added = False
    for f in uploaded_files:
        t_path = os.path.join(TEMP_UPLOAD_DIR, f.name)
        with open(t_path, "wb") as buf:
            buf.write(f.getbuffer())
        if t_path not in current_tasks:
            current_tasks.append(t_path)
            added = True
    if added:
        save_config_to_disk({"upload_task": current_tasks})
        st.rerun()

task_list = st.session_state.config.get("upload_task", [])
if task_list:
    cols_per_row = 10
    for i in range(0, len(task_list), cols_per_row):
        batch = task_list[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for j, img_path in enumerate(batch):
            with cols[j]:
                if os.path.exists(img_path):
                    st.image(img_path, width='stretch')
                    st.caption(os.path.basename(img_path))
                    if st.button("X", key=f"del_{i+j}", width='stretch'):
                        task_list.remove(img_path)
                        save_config_to_disk({"upload_task": task_list})
                        st.rerun()
                else:
                    st.caption("Missing")
                    if st.button("C", key=f"clr_{i+j}", width='stretch'):
                        task_list.remove(img_path)
                        save_config_to_disk({"upload_task": task_list})
                        st.rerun()

btn_col1, btn_col2 = st.columns(2)

with btn_col1:
    once_disabled = not is_alive or st.session_state.loop_active
    if st.button("🚀 Send Once", disabled=once_disabled, width='stretch'):
        # Action locked to upload_test
        save_config_to_disk({'last_prompt': input_prompt})
        task_payload = {
            "action": "upload_test", 
            "subject": input_prompt, 
            "timestamp": time.time(), 
            "attachments": task_list
        }
        with open(TASK_FILE, "w", encoding="utf-8") as f:
            json.dump(task_payload, f, ensure_ascii=False)
        st.toast("Sent: upload_test")

with btn_col2:
    loop_label = "Stop Loop" if st.session_state.loop_active else "Start Loop"
    if st.button(loop_label, disabled=not is_alive, width='stretch', type="secondary" if st.session_state.loop_active else "primary"):
        if not st.session_state.loop_active:
            # First shot locked to upload_test
            log_path = os.path.join(ROOT_DIR, "engine.log")
            if os.path.exists(log_path):
                try:
                    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        st.session_state.last_processed_log_line = lines[-1].strip() if lines else ""
                except: pass
            
            save_config_to_disk({'last_prompt': input_prompt})
            task_payload = {
                "action": "upload_test", 
                "subject": input_prompt, 
                "timestamp": time.time(), 
                "attachments": task_list
            }
            with open(TASK_FILE, "w", encoding="utf-8") as f:
                json.dump(task_payload, f, ensure_ascii=False)
            st.session_state.loop_active = True
            st.rerun()
        else:
            st.session_state.loop_active = False
            st.rerun()

@st.fragment(run_every="5s")
def render_gallery():
    target_path = st.session_state.config.get('save_dir', DEFAULT_OUTPUT_DIR)
    if os.path.exists(target_path):
        files = glob.glob(os.path.join(target_path, "*.png"))
        files.sort(key=os.path.getmtime, reverse=True)
        if files:
            grid = st.columns(4)
            for i, fpath in enumerate(files):
                with grid[i % 4]:
                    has_meta = False
                    try:
                        with Image.open(fpath) as img:
                            if "Prompt" in img.info: has_meta = True
                    except: pass
                    st.image(fpath, width='stretch')
                    st.caption(f"{os.path.basename(fpath)}{' 📝' if has_meta else ''}")
render_gallery()
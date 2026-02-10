import streamlit as st
import psutil
import os
import time
import json
import subprocess

# --- CONFIG & PATHS ---
# Updated to V1.4.4: Added list detection for upload_task and width='stretch'
DIAG_PAGE_VERSION = "V1.4.4" 
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCHER_SCRIPT = os.path.normpath(os.path.join(ROOT_DIR, "watcher_engine", "watcher.py"))
VENV_PYTHON = os.path.normpath(os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe"))
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")
TASK_FILE = os.path.join(ROOT_DIR, "task.json")
LOG_FILE = os.path.join(ROOT_DIR, "engine.log")

st.set_page_config(page_title=f"Diagnosis {DIAG_PAGE_VERSION}", layout="wide")

# --- UTILS ---
def get_mem_info(pid):
    """Get process memory usage"""
    try: 
        process = psutil.Process(pid)
        return f"{process.memory_info().rss / (1024 * 1024):.1f} MB"
    except: return "N/A"

def get_engine_pid():
    """Scan for running Watcher Engine process"""
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = " ".join(proc.info.get('cmdline') or []).lower()
            if "watcher.py" in cmdline:
                return proc.info['pid']
        except: continue
    return None

def kill_safe():
    """Safely terminate all related processes"""
    ui_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.pid == ui_pid: continue
            cmd = " ".join(proc.info.get('cmdline') or []).lower()
            name = proc.info['name'].lower()
            if "watcher.py" in cmd or any(k in name for k in ['chrome', 'playwright']):
                proc.kill()
        except: continue
    time.sleep(0.5)

def send_task(action_name):
    """Dispatch instruction to task.json"""
    with open(TASK_FILE, 'w', encoding='utf-8') as f:
        json.dump({"action": action_name, "timestamp": time.time()}, f)

def save_config_field(field_name, value):
    """Update specific field in config.json and notify user"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        cfg[field_name] = value
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        st.toast(f"Config updated: {field_name}")
    except Exception as e:
        st.error(f"Save failed: {e}")

# --- SIDEBAR UI ---
config = {}
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except: pass

with st.sidebar:
    v_col1, v_col2 = st.columns(2)
    v_col1.caption(f"🚀 App: V20.0")
    v_col2.caption(f"⚙️ Engine: {config.get('engine_version', 'Unknown')}")
    st.caption(f"🛡️ Diagnosis: {DIAG_PAGE_VERSION}")
    
    eng_pid = get_engine_pid()
    if eng_pid:
        if st.button("🛑 STOP ENGINE", type="secondary", width='stretch'):
            kill_safe(); st.rerun()
    else:
        if st.button("🚀 START ENGINE (Silent)", width='stretch'):
            kill_safe()
            subprocess.Popen([VENV_PYTHON, WATCHER_SCRIPT], creationflags=subprocess.CREATE_NO_WINDOW)
            st.rerun()

    st.divider()
    # Browser launch controls
    if st.button("🔍 Launch Browser (Visual)", type="secondary", width='stretch', disabled=not eng_pid):
        send_task("launch")
        st.toast("Visual launch command sent.")
    if st.button("🌑 Launch Browser (Headless)", width='stretch', disabled=not eng_pid):
        send_task("launch_headless")
        st.toast("Headless launch command sent.")

    # Termination controls
    if st.button("💀 KILL ALL TARGETS", width='stretch'):
        kill_safe(); st.rerun()
    if st.button("❌ Close Browser (Graceful)", width='stretch', disabled=not eng_pid):
        send_task("close_browser")
        st.toast("Close command sent.")

    st.divider()
    # ----- Core Test Buttons -----
  
    if st.button("👤 Check Sign-in Status", width='stretch', disabled=not eng_pid):
        send_task("check_signin")
        st.toast("Checking...")

    if st.button("📤 Upload Files Test", width='stretch', disabled=not eng_pid):
        send_task("upload_test")
        st.toast("Testing upload logic...")

    if st.button("📤 Upload Files Redo Test", width='stretch', disabled=not eng_pid):
        send_task("upload_test_redo")
        st.toast("Testing redo after upload files...")
 
    if st.button("🧇 Sand Box", width='stretch', disabled=not eng_pid):
        send_task("sand_box")
        st.toast("For general testing...") 
    
    st.divider()
    
# ----- Text Box Input Section (V1.4.5 Improved Empty Handling) -----
    # Logic: Saves on Enter for text_input, Ctrl+Enter for text_area
    
    # Check if upload_task is a list and extract the first item, 
    # and ensure empty lists/values display as an empty string instead of []
    raw_path = config.get("upload_task", "")
    if isinstance(raw_path, list):
        display_path = raw_path[0] if len(raw_path) > 0 else ""
    else:
        display_path = raw_path if raw_path else ""

    upload_path = st.text_input(
        "File Path to Upload (Press Enter)", 
        value=display_path,
        key="path_input_val",
        on_change=lambda: save_config_field("upload_task", st.session_state.path_input_val),
        width='stretch'
    )

    new_prompt = st.text_area(
        "Edit Last Prompt (Press Ctrl+Enter)", 
        value=config.get("last_prompt", ""), 
        height=120,
        key="prompt_input_val",
        on_change=lambda: save_config_field("last_prompt", st.session_state.prompt_input_val),
        width='stretch'
    )

# --- MAIN PANEL ---
@st.fragment(run_every="2s")
def render_status():
    ui_pid, curr_pid = os.getpid(), get_engine_pid()
    
    col_left, col_right = st.columns([40, 60])

    with col_left:
        st.subheader("Process Snapshot")
        status_text = f"Snapshot Time: {time.strftime('%H:%M:%S')}\n"
        status_text += "========================================\n\n"
        status_text += f"[ ENVIRONMENT (VENV) ]\n >> Status: {'READY' if os.path.exists(VENV_PYTHON) else 'MISSING'}\n >> Path: {VENV_PYTHON}\n\n"
        status_text += f"[ SYSTEM UI (STREAMLIT) ]\n >> PID: {ui_pid} | MEM: {get_mem_info(ui_pid)}\n\n"
        status_text += f"[ LOCAL WATCHER ENGINE ]\n >> PID: {curr_pid if curr_pid else 'OFFLINE'} | MEM: {get_mem_info(curr_pid) if curr_pid else 'N/A'}\n\n"
        
        status_text += "[ BROWSER PROCESSES ]\n"
        found = False
        for proc in psutil.process_iter(['pid', 'cmdline']):
            try:
                cmd = " ".join(proc.info.get('cmdline') or []).lower()
                if "chrome" in cmd and "gemini_user_data" in cmd:
                    status_text += f" >> PID: {proc.pid} | MEM: {get_mem_info(proc.pid)}\n"
                    found = True
            except: continue
        if not found: status_text += " >> STATUS: NO ACTIVE BROWSER\n"
        
        st.code(status_text + "\n========================================", language="text")

    with col_right:
        log_col_title, log_col_btn = st.columns([3, 1])
        with log_col_title:
            st.subheader("Engine Live Logs")
        with log_col_btn:
            if st.button("🗑️ Clear", width='stretch'):
                if os.path.exists(LOG_FILE):
                    try:
                        with open(LOG_FILE, 'w', encoding='utf-8') as f:
                            f.write(f"--- Log cleared at {time.strftime('%H:%M:%S')} ---\n")
                        st.toast("Logs cleared!")
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Clear failed: {e}")

        log_display = "Waiting for engine output...\n"
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    log_display += "".join(lines[-25:])
            except: 
                log_display += " >> Syncing log file..."
        st.code(log_display , language="text")

render_status()
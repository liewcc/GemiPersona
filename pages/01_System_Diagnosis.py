import streamlit as st
import psutil
import os
import time
import json
import subprocess

# --- CONFIG & PATHS ---
# Incremented to V1.4.1 to reflect button additions [cite: 1]
DIAG_PAGE_VERSION = "V1.4.1" 
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
    # Display engine version from config.json
    v_col2.caption(f"⚙️ Engine: {config.get('engine_version', 'Unknown')}")
    st.caption(f"🛡️ Diagnosis: {DIAG_PAGE_VERSION}")
    
    eng_pid = get_engine_pid()
    if eng_pid:
        if st.button("🛑 STOP ENGINE", type="secondary", use_container_width=True):
            kill_safe(); st.rerun()
    else:
        if st.button("🚀 START ENGINE (Silent)", use_container_width=True):
            kill_safe()
            subprocess.Popen([VENV_PYTHON, WATCHER_SCRIPT], creationflags=subprocess.CREATE_NO_WINDOW)
            st.rerun()

    st.divider()
    # Browser launch controls
    if st.button("🔍 Launch Browser (Visual)", type="secondary", use_container_width=True, disabled=not eng_pid):
        send_task("launch")
        st.toast("Visual launch command sent.")
    if st.button("🌑 Launch Browser (Headless)", use_container_width=True, disabled=not eng_pid):
        send_task("launch_headless")
        st.toast("Headless launch command sent.")

    # Termination controls
    if st.button("💀 KILL ALL TARGETS", use_container_width=True):
        kill_safe(); st.rerun()
    if st.button("❌ Close Browser (Graceful)", use_container_width=True, disabled=not eng_pid):
        send_task("close_browser")
        st.toast("Close command sent.")

    st.divider()
    # Core Test Buttons
    if st.button("🧇 Sand Box", use_container_width=True, disabled=not eng_pid):
        send_task("sand_box")
        st.toast("For general testing...")
    
    if st.button("👤 Check Sign-in Status", use_container_width=True, disabled=not eng_pid):
        send_task("check_signin")
        st.toast("Checking...")

    if st.button("🍌 Prompt Test (Image Gen)", type="secondary", use_container_width=True, disabled=not eng_pid):
        send_task("prompt_test")
        st.toast("Image Gen & Download Started")

    if st.button("🔄 Redo Loop Test", use_container_width=True, disabled=not eng_pid):
        send_task("redo_loop")
        st.toast("Triggering redo loop...")

    if st.button("📤 Upload Files Test", use_container_width=True, disabled=not eng_pid):
        send_task("upload_test")
        st.toast("Testing upload logic...")

    if st.button("📤 Upload Files Redo Test", use_container_width=True, disabled=not eng_pid):
        send_task("upload_test_redo")
        st.toast("Testing redo after upload files...")
    
    st.divider()

    # 从 config 中获取路径，如果没有则为空字符串
    current_path = config.get("upload_file_path", "")
    upload_path = st.text_input("File Path to Upload", value=current_path)

    if upload_path != current_path:
        config["upload_file_path"] = upload_path
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        st.success("Upload path updated!")

    # 新增：Text Box 放置在 File Path 下方
    current_prompt = config.get("last_prompt", "")
    new_prompt = st.text_area("Edit Last Prompt", value=current_prompt, height=120)

    # 如果 Prompt 发生变化，实时保存到 config.json
    if new_prompt != current_prompt:
        config["last_prompt"] = new_prompt
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

# --- MAIN PANEL (40/60 比例修复纯净版) ---
@st.fragment(run_every="2s")
def render_status():
    ui_pid, curr_pid = os.getpid(), get_engine_pid()
    
    # 设定主列比例：Snapshot(40%) | Logs(60%)
    col_left, col_right = st.columns([40, 60])

    with col_left:
        st.subheader("Process Snapshot")
        # 定义 status_text 变量
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
        # 顶部标题与清空按钮布局
        log_col_title, log_col_btn = st.columns([3, 1])
        with log_col_title:
            st.subheader("Engine Live Logs")
        with log_col_btn:
            if st.button("🗑️ Clear", use_container_width=True):
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
                    # 取最后 25 行并拼接成字符串
                    log_display += "".join(lines[-25:])
            except: 
                log_display += " >> Syncing log file..."
        st.code(log_display , language="text")

render_status()
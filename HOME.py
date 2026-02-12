import streamlit as st
import subprocess
import json
import os
import glob
import psutil
import time
from PIL import Image
from datetime import datetime

# --- 1. CONFIGURATION & VERSIONING ---
# Version V26.2.12: 
# - Logic Update: Changed 'Decline' calculation from subtraction formula to keyword detection.
# - Keyword: Increments image_decline if "Declined" is found in the log.
# - UI: Maintained English interface and 'stretch' width compliance.
APP_VERSION = "V26.2.12"
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ENGINE_DIR = os.path.join(ROOT_DIR, "watcher_engine")
DEFAULT_OUTPUT_DIR = os.path.join(ROOT_DIR, "browser_outputs")
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")
TASK_FILE = os.path.join(ROOT_DIR, "task.json")
LOG_FILE = os.path.join(ROOT_DIR, "engine.log")
COUNTER_FILE = os.path.join(ROOT_DIR, "counter.json")
TEMP_UPLOAD_DIR = os.path.join(ROOT_DIR, "temp_uploads")

if not os.path.exists(TEMP_UPLOAD_DIR):
    os.makedirs(TEMP_UPLOAD_DIR)

st.set_page_config(page_title=f"GemiPersona Pro {APP_VERSION}", layout="wide")

# --- 2. JSON DATA PERSISTENCE ---
def load_json_file(file_path, default_val):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return default_val

def save_json_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

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
        "loop_count": 0,
        "count_until_switch": False,
        "count_until": 0,
        "selectors": {"textbox": 'div[role=\"textbox\"]', "send_btn": 'button[aria-label*=\"Send\"]', "img_list": "img"}
    }
    disk_cfg = load_json_file(CONFIG_FILE, default_cfg)
    
    changed = False
    for k, v in default_cfg.items():
        if k not in disk_cfg:
            disk_cfg[k] = v
            changed = True
            
    if changed:
        save_json_file(CONFIG_FILE, disk_cfg)
    return disk_cfg

def get_counter():
    return load_json_file(COUNTER_FILE, {"total_count": 0, "image_save": 0, "image_decline": 0, "fail_count": 0, "line_offset": 0})

def update_counter(total, saved, decline, fail, offset):
    data = {
        "total_count": total, "image_save": saved, "image_decline": decline, "fail_count": fail, "line_offset": offset
    }
    save_json_file(COUNTER_FILE, data)
    return data

if 'config' not in st.session_state:
    st.session_state.config = initialize_config()
if 'loop_active' not in st.session_state:
    st.session_state.loop_active = False
if 'is_first_run' not in st.session_state:
    st.session_state.is_first_run = True
if 'last_processed_log_line' not in st.session_state:
    st.session_state.last_processed_log_line = ""

# --- 3. SYSTEM UTILS ---
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
                    if ">>> Browser Ready" in f.read(): return True
            except: pass
        time.sleep(0.5)
    return False

# --- 4. SIDEBAR ---
with st.sidebar:
    st.caption(f"🚀 App: {APP_VERSION} | ⚙️ Engine: {st.session_state.config.get('engine_version', 'Unknown')}")
    
    @st.fragment(run_every="2s")
    def render_counter_metrics():
        cnt = get_counter()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", cnt['total_count'])
        c2.metric("Saved", cnt['image_save'])
        c3.metric("Decline", cnt['image_decline'])
        c4.metric("Reset", cnt.get('fail_count', 0))
    
    render_counter_metrics()

    @st.fragment(run_every="2s")
    def render_sidebar_status():
        active, _ = get_engine_info()
        if active: st.success("Engine: Online")
        else: st.error("Engine: Offline")
        if st.session_state.loop_active: st.warning("🔄 Loop: ACTIVE")
        else: st.info("⏹️ Loop: Idle")
        
        if active:
            if st.button("🛑 Shutdown Browser", width='stretch'):
                save_json_file(TASK_FILE, {"action": "close_browser", "timestamp": time.time()})
                time.sleep(1.5)
                for proc in psutil.process_iter(['cmdline']):
                    try:
                        if "watcher.py" in " ".join(proc.info.get('cmdline') or []).lower(): proc.terminate()
                    except: continue
                st.session_state.loop_active = False
                st.rerun()
        else:
            VENV_PYTHON = os.path.normpath(os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe"))
            WATCHER_SCRIPT = os.path.normpath(os.path.join(ROOT_DIR, "watcher_engine", "watcher.py"))
            if st.button("🔥 Fire up Browser (Headless)", width='stretch', type="primary"):
                subprocess.Popen([VENV_PYTHON, WATCHER_SCRIPT], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                if os.path.exists(LOG_FILE): os.remove(LOG_FILE)
                save_json_file(TASK_FILE, {"action": "launch_headless", "timestamp": time.time()})
                wait_for_browser_ready(25)
                st.rerun()
    
    render_sidebar_status()
    st.divider()

    def update_loop_count():
        try:
            new_val = int(st.session_state.loop_count_input)
        except ValueError:
            new_val = 0
        current_cfg = load_json_file(CONFIG_FILE, st.session_state.config)
        current_cfg["loop_count"] = new_val
        save_json_file(CONFIG_FILE, current_cfg)
        st.session_state.config = current_cfg

    st.text_input("Loop Limit", 
                  value=str(st.session_state.config.get("loop_count", 0)), 
                  key="loop_count_input", 
                  on_change=update_loop_count,
                  disabled=st.session_state.loop_active)
    
    def update_count_until_settings():
        current_cfg = load_json_file(CONFIG_FILE, st.session_state.config)
        try:
            current_cfg["count_until"] = int(st.session_state.count_until_input)
        except ValueError:
            current_cfg["count_until"] = 0
        current_cfg["count_until_switch"] = st.session_state.count_until_switch_input
        save_json_file(CONFIG_FILE, current_cfg)
        st.session_state.config = current_cfg

    st.text_input("Count Until (Saved)", 
                  value=str(st.session_state.config.get("count_until", 0)),
                  key="count_until_input",
                  on_change=update_count_until_settings,
                  disabled=st.session_state.loop_active)

    st.toggle("Stop after Saved", 
              value=st.session_state.config.get("count_until_switch", False),
              key="count_until_switch_input",
              on_change=update_count_until_settings,
              help="If enabled, the loop will stop only when 'Saved' count matches target. Ignores Loop Limit.",
              disabled=st.session_state.loop_active)

    st.divider()

    def auto_save_config():
        new_path = st.session_state.storage_input
        updates = {
            "url": st.session_state.url_input,
            "save_dir": new_path,
            "name_prefix": st.session_state.prefix_input,
            "name_padding": st.session_state.padding_input,
            "name_start": st.session_state.start_input
        }
        current_cfg = load_json_file(CONFIG_FILE, st.session_state.config)
        current_cfg.update(updates)
        save_json_file(CONFIG_FILE, current_cfg)
        st.session_state.config = current_cfg

    @st.fragment(run_every="2s")
    def render_config_inputs():
        disk_data = load_json_file(CONFIG_FILE, st.session_state.config)
        mapping = {"url_input": "url", "storage_input": "save_dir", "prefix_input": "name_prefix", "padding_input": "name_padding", "start_input": "name_start"}
        for widget_key, disk_key in mapping.items():
            if widget_key not in st.session_state or st.session_state[widget_key] != disk_data.get(disk_key):
                st.session_state[widget_key] = disk_data.get(disk_key)
        
        st.text_input("Target URL", key="url_input", on_change=auto_save_config)
        st.text_input("Storage Path", key="storage_input", on_change=auto_save_config)
        
        if st.button("📂 Open Picture Folder", width='stretch'):
            if st.session_state.storage_input and os.path.exists(st.session_state.storage_input):
                os.startfile(os.path.normpath(st.session_state.storage_input))
        
        if st.button("🏠 Open Repository Folder", width='stretch'):
            os.startfile(os.path.normpath(ROOT_DIR))

        st.link_button("🌐 Visit GitHub Repo", "https://github.com/liewcc/GemiPersona", width='stretch')
        st.divider()
        st.markdown("**File Naming Rules**")
        st.text_input("Name Prefix", key="prefix_input", on_change=auto_save_config)
        n_col1, n_col2 = st.columns(2)
        n_col1.number_input("Padding", min_value=1, max_value=10, key="padding_input", on_change=auto_save_config)
        n_col2.number_input("Start No.", min_value=0, key="start_input", on_change=auto_save_config)

    render_config_inputs()
    st.divider()

# --- 5. LOG PROCESSING & LIVE MONITORING ---

@st.fragment(run_every="2s")
def render_live_status():
    cnt = get_counter() 
    config = st.session_state.config
    limit = config.get("loop_count", 0)
    count_until_active = config.get("count_until_switch", False)
    count_until_target = config.get("count_until", 0)
    
    if st.session_state.loop_active:
        if count_until_active and count_until_target > 0:
            if cnt['image_save'] >= count_until_target:
                st.toast(f"Reached {count_until_target} saved images. Stopping...", icon="✅")
                st.session_state.loop_active = False
                st.rerun()
                return
        elif limit > 0 and cnt['total_count'] >= limit:
            st.toast(f"Loop Limit {limit} reached. Stopping...", icon="🛑")
            st.session_state.loop_active = False
            st.rerun()
            return

    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                all_lines = f.readlines()
                if not all_lines: return
                
                offset = cnt.get("line_offset", 0)
                new_lines = all_lines[offset:]
                
                cur_total = cnt['total_count']
                cur_saved = cnt['image_save']
                cur_decline = cnt['image_decline']
                cur_fail = cnt.get('fail_count', 0)
                
                processed_count = 0
                for line in new_lines:
                    clean_line = line.strip()
                    if not clean_line: continue
                    processed_count += 1
                    
                    if st.session_state.loop_active:
                        if "Executing Action:" in clean_line:
                            cur_total += 1
                    
                    # Track Saved images keyword
                    if "Saved:" in clean_line:
                        cur_saved += 1
                    
                    # NEW: Track Declined images keyword
                    if "Declined" in clean_line:
                        cur_decline += 1
                
                if processed_count > 0:
                    update_counter(cur_total, cur_saved, cur_decline, cur_fail, offset + processed_count)

                last_line = all_lines[-1].strip()
                if "[END]" in last_line and last_line != st.session_state.last_processed_log_line:
                    st.session_state.loop_active = False
                    st.session_state.last_processed_log_line = last_line
                    st.rerun()
                    return

                if st.session_state.loop_active and ("[SUCCESS]" in last_line or "[FAIL]" in last_line) and last_line != st.session_state.last_processed_log_line:
                    disk_cfg = load_json_file(CONFIG_FILE, {})
                    task_list = disk_cfg.get("upload_task", [])
                    
                    if "[RESET_REQUIRED]" in last_line:
                        cur_fail += 1
                        update_counter(cur_total, cur_saved, cur_decline, cur_fail, offset + processed_count)
                        save_json_file(TASK_FILE, {"action": "upload_test", "subject": disk_cfg.get('last_prompt', ""), "timestamp": time.time(), "attachments": task_list})
                    else:
                        save_json_file(TASK_FILE, {"action": "upload_test_redo", "subject": disk_cfg.get('last_prompt', ""), "timestamp": time.time()})
                    
                    st.session_state.last_processed_log_line = last_line

                if "error" in last_line.lower() or "[FAIL]" in last_line: st.error(last_line)
                elif "[SUCCESS]" in last_line: st.success(last_line)
                elif "[END]" in last_line: st.warning(last_line)
                else: st.info(last_line)
        except Exception: pass

render_live_status()

# --- 6. MAIN UI ---
input_prompt = st.text_area("Prompt Input", value=st.session_state.config.get('last_prompt', ""), height=120, label_visibility="collapsed")
if input_prompt != st.session_state.config.get('last_prompt', ""):
    cfg = load_json_file(CONFIG_FILE, st.session_state.config); cfg['last_prompt'] = input_prompt
    save_json_file(CONFIG_FILE, cfg); st.session_state.config = cfg

uploaded_files = st.file_uploader("Upload", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, label_visibility="collapsed")
if uploaded_files:
    current_tasks = st.session_state.config.get("upload_task", [])
    for f in uploaded_files:
        t_path = os.path.join(TEMP_UPLOAD_DIR, f.name)
        with open(t_path, "wb") as buf: buf.write(f.getbuffer())
        if t_path not in current_tasks: current_tasks.append(t_path)
    cfg = load_json_file(CONFIG_FILE, st.session_state.config); cfg["upload_task"] = current_tasks
    save_json_file(CONFIG_FILE, cfg); st.session_state.config = cfg; st.rerun()

task_list = st.session_state.config.get("upload_task", [])
if task_list:
    cols = st.columns(10)
    for i, img_path in enumerate(task_list):
        with cols[i % 10]:
            if os.path.exists(img_path):
                st.image(img_path, width='stretch')
                if st.button("X", key=f"del_{i}", width='stretch'):
                    task_list.remove(img_path); cfg = load_json_file(CONFIG_FILE, st.session_state.config)
                    cfg["upload_task"] = task_list; save_json_file(CONFIG_FILE, cfg); st.rerun()

btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    if st.button("🚀 Send Once", disabled=not get_engine_info()[0] or st.session_state.loop_active, width='stretch'):
        save_json_file(TASK_FILE, {"action": "upload_test", "subject": input_prompt, "timestamp": time.time(), "attachments": task_list})

with btn_col2:
    is_active = st.session_state.loop_active
    if st.button("Stop Loop" if is_active else "Start Loop", disabled=not get_engine_info()[0], width='stretch', type="secondary" if is_active else "primary"):
        if not is_active:
            start_off = 0
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    if lines: start_off = len(lines)
            update_counter(0, 0, 0, 0, start_off); st.session_state.is_first_run = True 
            save_json_file(TASK_FILE, {"action": "upload_test", "subject": input_prompt, "timestamp": time.time(), "attachments": task_list})
            st.session_state.loop_active = True
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
                    if st.button(f"🔍 {os.path.basename(fpath)}{' 📝' if has_meta else ''}", key=f"gal_btn_{i}", width='stretch'):
                        os.startfile(os.path.normpath(fpath))

render_gallery()
# watcher_engine/watcher.py
# Version: V2.8.1
# Description: Adaptive Viewport Logic with Dynamic URL Sync and Redo Protection.
# UI and Comments: English only.

import os
import asyncio
import logging
import sys
import json
import time
import importlib
from playwright.async_api import async_playwright

# --- CONFIG ---
ENGINE_VERSION = "V2.8.1" 
WATCHER_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(WATCHER_DIR)
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")
TASK_FILE = os.path.join(ROOT_DIR, "task.json")
LOG_FILE = os.path.join(ROOT_DIR, "engine.log")
USER_DATA_DIR = os.path.join(WATCHER_DIR, "gemini_user_data")
STATE_FILE = os.path.join(WATCHER_DIR, "state.json")
DEFAULT_URL = "https://gemini.google.com/app"

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8', mode='w'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def safe_sync_version():
    """Sync ENGINE_VERSION to config.json."""
    if not os.path.exists(CONFIG_FILE): return
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data["engine_version"] = ENGINE_VERSION
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"🔄 Version Check: Engine synchronized to {ENGINE_VERSION}")
    except Exception as e:
        logger.error(f"Version sync failed: {e}")

class GemiWatcher:
    def __init__(self):
        self.browser_context = None
        self.page = None
        self.playwright = None
        self.is_headless = False
        self.last_action_url = None # Tracks the URL used in the last non-redo action

    def get_config_url(self):
        """Fetch the latest URL from config.json with fallback logic."""
        if not os.path.exists(CONFIG_FILE):
            return DEFAULT_URL
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            url = data.get("url")
            return url if url and url.strip() else DEFAULT_URL
        except Exception as e:
            logger.error(f"Error reading config URL: {e}")
            return DEFAULT_URL

    async def apply_hardcore_stealth(self, page):
        """Manual JS injection for anti-detection."""
        try:
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => False});
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            """)
            logger.info("🛡️ Hardcore Stealth injected.")
        except Exception as e:
            logger.error(f"⚠️ Manual stealth failed: {e}")

    async def inject_session_state(self):
        """Inject saved session state from state.json."""
        if not os.path.exists(STATE_FILE):
            logger.warning("⚠️ No state.json for injection.")
            return
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
            if 'cookies' in state:
                await self.browser_context.add_cookies(state['cookies'])
                logger.info(f"🔑 Injected {len(state['cookies'])} cookies.")
        except Exception as e:
            logger.error(f"❌ Injection failed: {e}")

    async def save_session_state(self):
        """Safely export current state."""
        if self.browser_context and not self.is_headless:
            try:
                await self.browser_context.storage_state(path=STATE_FILE)
                logger.info(f"💾 Session state saved: {STATE_FILE}")
            except Exception as e:
                logger.error(f"⚠️ Save state failed: {e}")

    async def launch_browser(self, headless=False):
        if self.browser_context: return
        self.is_headless = headless
        
        logger.info(f">>> Launching Browser (Headless={headless})...")
        try:
            self.playwright = await async_playwright().start()
            real_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            
            target_viewport = {'width': 2560, 'height': 1440} if headless else None
            
            self.browser_context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=headless,
                user_agent=real_ua,
                viewport=target_viewport, 
                ignore_default_args=["--enable-automation", "--use-mock-keychain"],
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
            )
            
            if headless:
                await self.inject_session_state()

            self.page = await self.browser_context.new_page()
            await self.apply_hardcore_stealth(self.page)
            
            # Initial Navigation
            target_url = self.get_config_url()
            logger.info(f"Navigating to {target_url}...")
            await self.page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
            self.last_action_url = target_url
            
            try:
                await self.page.wait_for_selector('[role="textbox"]', timeout=15000)
                logger.info("✅ Gemini UI detected and ready.")
            except:
                logger.warning("⚠️ Textbox not found yet, page might still be loading.")

            if not headless:
                await self.save_session_state()

            logger.info(f">>> Browser Ready. Mode: {'Headless (2560x1440)' if headless else 'Headed (Auto-Maximized)'}")
        except Exception as e:
            logger.error(f"❌ Launch failed: {e}")

    async def dispatch_action(self, action_name):
        """Action loader with URL sync and redo-protection logic."""
        try:
            current_config_url = self.get_config_url()
            is_redo_action = "redo" in action_name.lower()

            # URL Synchronization Logic
            if is_redo_action:
                logger.info(f"🔄 Redo action '{action_name}' detected. Keeping current page URL.")
            else:
                if self.last_action_url != current_config_url:
                    logger.info(f"🌐 URL Change detected: {self.last_action_url} -> {current_config_url}")
                    await self.page.goto(current_config_url, wait_until="domcontentloaded", timeout=45000)
                    self.last_action_url = current_config_url
                else:
                    logger.info(f"✅ URL remains unchanged: {current_config_url}")

            # Module Execution
            module_name = f"watcher_engine.actions_lib.{action_name}"
            module = importlib.import_module(module_name)
            importlib.reload(module)
            logger.info(f"🚀 Executing Action: {action_name}")
            
            await module.run(self.page, logger, CONFIG_FILE)
            
            if not self.is_headless:
                await self.save_session_state()
        except Exception as e:
            logger.error(f"Action '{action_name}' error: {e}")

    async def run(self):
        safe_sync_version()
        logger.info(f"Watcher Engine {ENGINE_VERSION} Active. Listening for tasks...")
        
        while True:
            if os.path.exists(TASK_FILE):
                try:
                    await asyncio.sleep(0.3)
                    with open(TASK_FILE, 'r', encoding='utf-8') as f:
                        task = json.load(f)
                    action = task.get("action")
                    
                    if action == "launch": await self.launch_browser(headless=False)
                    elif action == "launch_headless": await self.launch_browser(headless=True)
                    elif action == "close_browser":
                        if self.browser_context:
                            await self.save_session_state()
                            await self.browser_context.close()
                            await self.playwright.stop()
                            self.page = None; self.browser_context = None
                            self.last_action_url = None
                        logger.info("Browser closed.")
                    elif action:
                        if self.page: await self.dispatch_action(action)
                        else: logger.error(f"Action '{action}' ignored: Browser inactive.")
                    
                    if os.path.exists(TASK_FILE): os.remove(TASK_FILE)
                except Exception as e:
                    logger.error(f"Main loop error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    watcher = GemiWatcher()
    try:
        asyncio.run(watcher.run())
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
    except Exception as e:
        logger.critical(f"System Crash: {e}")
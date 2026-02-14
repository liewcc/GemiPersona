import asyncio
import os
import json
import re
from playwright.async_api import TimeoutError

# Version: V5.4.3 (Post-Log Signal Injection)
# Update: Added a secondary explicit log entry for [RESET_REQUIRED] after any exception 
#         to ensure it's the final line, bypassing Playwright's multi-line debug logs.
# Update: Maintained English comments and UI per user instructions.

async def start_new_chat(page, logger, config_path):
    """
    Navigates to the target URL and waits for the interaction textbox.
    """
    try:
        if not os.path.exists(config_path):
            logger.error("Config missing.")
            logger.error("[FAIL] [RESET_REQUIRED]")
            return False
            
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        
        target_url = cfg.get("url")
        logger.info(f">> Navigating to: {target_url}")
        
        await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        
        try:
            selectors = ['[role="textbox"]', '[contenteditable="true"]', 'textarea[aria-label="Prompt"]']
            combined_selector = ", ".join(selectors)
            await page.wait_for_selector(combined_selector, timeout=30000)
            logger.info(">> [SIGNAL] Textbox detected.")
            return True
        except TimeoutError:
            logger.error(f"UI Timeout at {page.url}")
            logger.error("[FAIL] [RESET_REQUIRED]")
            return False

    except Exception as e:
        logger.error(f"Navigation crash: {e}")
        logger.error("[FAIL] [RESET_REQUIRED]")
        return False

async def handle_file_upload(page, logger, upload_tasks):
    """
    Handles file upload tasks. Injects a final reset line after any error log.
    """
    if not upload_tasks: return True
    for file_path in upload_tasks:
        if not os.path.exists(file_path): 
            logger.warning(f">> File not found: {file_path}")
            continue
            
        abs_path = os.path.abspath(file_path)
        file_name = os.path.basename(file_path)
        try:
            async with page.expect_file_chooser(timeout=30000) as fc_info:
                logger.info(f">> Preparing to upload: {file_name}")
                await page.evaluate('''() => {
                    const gemsIcon = document.querySelector('mat-icon[data-mat-icon-name="add_2"]') || 
                                   document.querySelector('mat-icon[fonticon="add"]');
                    if (gemsIcon) { gemsIcon.closest('button').click(); }
                }''')
                await asyncio.sleep(2.0)
                await page.evaluate('''() => {
                    const opt = Array.from(document.querySelectorAll('.menu-text, span'))
                                     .find(i => i.innerText.toLowerCase().includes("upload files"));
                    if (opt) opt.click();
                }''')
                file_chooser = await fc_info.value
                await file_chooser.set_files(abs_path)
            logger.info(f">> [SUCCESS] {file_name} uploaded.")
            await asyncio.sleep(4.0)
        except Exception as e:
            # First, print the messy Playwright error with all the '==== logs ===='
            logger.error(f"Upload error: {e}")
            # Second, print the clean signal so it's the absolute last line in the log file
            logger.error("[FAIL] [RESET_REQUIRED]")
            return False
    return True

async def check_response_status(page, logger=None):
    """
    Monitors Gemini's response status.
    """
    config_path = "config.json"
    declined_kws = ["违反", "规范", "点子", "协助你将想法化为现实"] 
    quota_kws = ["quota exceeded", "daily limit", "reached your limit"]
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                declined_kws.extend(cfg.get("declined_msg", []))
                quota_kws.extend(cfg.get("quota_exceeded_msg", []))
        except Exception as e:
            if logger: logger.error(f">> [ERROR] Config load failed: {e}")

    eval_data = {"declined": declined_kws, "quota": quota_kws}

    data = await page.evaluate('''(args) => {
        const bodyTextLower = document.body.innerText.toLowerCase();
        const isGenerating = bodyTextLower.includes("nano banana") || !!document.querySelector('mat-progress-bar');
        if (isGenerating) return { status: "generating", text: "..." };

        const responses = Array.from(document.querySelectorAll('model-response'));
        if (responses.length === 0) return { status: "waiting", text: "" };
        
        const lastResp = responses[responses.length - 1];
        const literalText = lastResp.innerText.trim(); 
        const lowerText = literalText.toLowerCase();

        for (const kw of args.quota) {
            if (lowerText.includes(kw.toLowerCase())) return { status: "quota_exceeded", text: literalText };
        }
        for (const kw of args.declined) {
            if (lowerText.includes(kw.toLowerCase())) return { status: "refused", text: literalText };
        }
        if (!!lastResp.querySelector('img')) return { status: "success", text: literalText };

        return (literalText.length > 0) ? { status: "waiting", text: literalText } : { status: "waiting", text: "" };
    }''', eval_data)

    if logger and data['text']:
        flat_text = data['text'].replace('\n', ' ').replace('\r', ' ')
        clean_text = " ".join(flat_text.split())
        msg = f"Gemini says: \"{clean_text}\""
        if data['status'] == "refused": logger.warning(f">> [DETECTION] Blocked. {msg}")
        elif data['status'] == "quota_exceeded": logger.error(f">> [DETECTION] Quota Limit. {msg}")
        elif data['status'] == "success": logger.info(f">> [DETECTION] Success. {msg}")
        elif data['status'] == "waiting" and data['text']: logger.info(f">> [DETECTION] {msg}")

    return data['status']

async def ensure_tool_selected(page, logger, tool_keyword="create image"):
    """
    Ensures a specific UI tool is selected.
    """
    try:
        visible = await page.evaluate(f'''(kw) => {{
            const btn = Array.from(document.querySelectorAll('button, span'))
                             .find(i => i.innerText.toLowerCase().includes(kw));
            if (btn) {{ btn.click(); return true; }}
            return false;
        }}''', tool_keyword)
        if visible: logger.info(f">> Tool selected: {tool_keyword}")
        return visible
    except Exception: return False
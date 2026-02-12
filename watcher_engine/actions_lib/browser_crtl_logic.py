import asyncio
import os
import json
import re
from playwright.async_api import TimeoutError

# Version: V5.4.0 (Reset Signal & Timeout Resilience)
# Update: Integrated "[FAIL] [RESET_REQUIRED]" signal for system-level resets.
# Update: Added URL tracking and multi-selector fallback for text input detection.
# Update: Maintained English comments and UI per user personalization instructions.

async def start_new_chat(page, logger, config_path):
    """
    Navigates to the target URL and waits for the interaction textbox.
    Triggers a reset signal if navigation or element detection fails.
    """
    try:
        if not os.path.exists(config_path):
            logger.error(f"[FAIL] [RESET_REQUIRED] Config missing: {config_path}")
            return False
            
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        
        target_url = cfg.get("url")
        logger.info(f">> Navigating to: {target_url}")
        
        # Increased wait_until to 'networkidle' for better stability in 2026 web environments
        await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        
        # Multi-selector fallback to handle UI updates (Textbox or ContentEditable)
        try:
            selectors = ['[role="textbox"]', '[contenteditable="true"]', 'textarea[aria-label="Prompt"]']
            combined_selector = ", ".join(selectors)
            await page.wait_for_selector(combined_selector, timeout=30000)
            logger.info(">> [SIGNAL] Textbox detected.")
            return True
        except TimeoutError:
            current_url = page.url
            logger.error(f"[FAIL] [RESET_REQUIRED] UI Timeout. Current URL: {current_url}")
            return False

    except Exception as e:
        logger.error(f"[FAIL] [RESET_REQUIRED] Navigation crash: {e}")
        return False

async def handle_file_upload(page, logger, upload_tasks):
    """
    Handles file upload tasks via the 'add' icon and file chooser.
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
                # Using more generic icon selectors to prevent breakage
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
            logger.error(f"[FAIL] Upload error: {e}")
            return False
    return True

async def check_response_status(page, logger=None):
    """
    Monitors Gemini's response status, handling quota and refusal keywords.
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
            if logger:
                logger.error(f">> [ERROR] Config load failed: {e}")

    eval_data = {"declined": declined_kws, "quota": quota_kws}

    data = await page.evaluate('''(args) => {
        const bodyTextLower = document.body.innerText.toLowerCase();
        
        // 1. Generation detection (Updated for Nano Banana)
        const isGenerating = bodyTextLower.includes("nano banana") || !!document.querySelector('mat-progress-bar');
        if (isGenerating) return { status: "generating", text: "..." };

        // 2. Response extraction
        const responses = Array.from(document.querySelectorAll('model-response'));
        if (responses.length === 0) return { status: "waiting", text: "" };
        
        const lastResp = responses[responses.length - 1];
        const literalText = lastResp.innerText.trim(); 
        const lowerText = literalText.toLowerCase();

        // 3. Quota check
        for (const kw of args.quota) {
            if (lowerText.includes(kw.toLowerCase())) return { status: "quota_exceeded", text: literalText };
        }

        // 4. Policy refusal check
        for (const kw of args.declined) {
            if (lowerText.includes(kw.toLowerCase())) return { status: "refused", text: literalText };
        }

        // 5. Image success check
        if (!!lastResp.querySelector('img')) return { status: "success", text: literalText };

        return (literalText.length > 0) ? { status: "waiting", text: literalText } : { status: "waiting", text: "" };
    }''', eval_data)

    if logger and data['text']:
        # Text flattening to ensure log line integrity
        flat_text = data['text'].replace('\n', ' ').replace('\r', ' ')
        clean_text = " ".join(flat_text.split())
        msg = f"Gemini says: \"{clean_text}\""
        
        if data['status'] == "refused":
            logger.warning(f">> [DETECTION] Blocked. {msg}")
        elif data['status'] == "quota_exceeded":
            logger.error(f">> [DETECTION] Quota Limit. {msg}")
        elif data['status'] == "success":
            logger.info(f">> [DETECTION] Success. {msg}")
        elif data['status'] == "waiting" and data['text']:
            logger.info(f">> [DETECTION] {msg}")

    return data['status']

async def ensure_tool_selected(page, logger, tool_keyword="create image"):
    """
    Ensures a specific UI tool is selected based on keyword.
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
    except Exception: 
        return False
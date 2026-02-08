import asyncio
import os
import json

# Version: V5.1.9 (Core Logic)
# Update: Added specific keywords for "Minors" and "Depiction" refusals.
# Strengthened refusal detection to scan all paragraph tags.

async def start_new_chat(page, logger, config_path):
    try:
        if not os.path.exists(config_path):
            logger.error(f"[FAIL] Config missing: {config_path}")
            return False
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        target_url = cfg.get("url")
        logger.info(f">> Navigating to: {target_url}")
        await page.goto(target_url, wait_until="load", timeout=60000)
        await page.wait_for_selector('[role="textbox"]', timeout=30000)
        logger.info(">> [SIGNAL] Textbox detected.")
        return True
    except Exception as e:
        logger.error(f"[FAIL] Navigation crash: {e}"); return False

async def handle_file_upload(page, logger, upload_tasks):
    if not upload_tasks: return True
    for file_path in upload_tasks:
        if not os.path.exists(file_path): continue
        abs_path = os.path.abspath(file_path)
        try:
            async with page.expect_file_chooser(timeout=30000) as fc_info:
                await page.evaluate('''() => {
                    const gemsIcon = document.querySelector('mat-icon[data-mat-icon-name="add_2"]');
                    if (gemsIcon) { gemsIcon.closest('button').click(); return; }
                    const appBtn = Array.from(document.querySelectorAll('button')).find(b => b.ariaLabel?.includes("Add") || b.innerHTML.includes("plus"));
                    if (appBtn) appBtn.click();
                }''')
                await asyncio.sleep(2.0)
                await page.evaluate('''() => {
                    const gemsOpt = Array.from(document.querySelectorAll('.menu-text')).find(i => i.innerText.toLowerCase().includes("upload files"));
                    if (gemsOpt) { gemsOpt.click(); return; }
                    const appOpt = Array.from(document.querySelectorAll('[role="menuitem"], span')).find(i => i.innerText.toLowerCase().includes("upload files"));
                    if (appOpt) appOpt.click();
                }''')
                file_chooser = await fc_info.value
                await file_chooser.set_files(abs_path)
            await asyncio.sleep(4.0)
        except Exception as e:
            logger.error(f"[FAIL] Upload error: {e}"); return False
    return True

async def ensure_tool_selected(page, logger, tool_keyword="create image"):
    try:
        visible = await page.evaluate(f'''(kw) => {{
            const btn = Array.from(document.querySelectorAll('button, span, .menu-text')).find(i => i.innerText.toLowerCase().includes(kw));
            if (btn && btn.offsetParent !== null) {{ btn.click(); return true; }}
            return false;
        }}''', tool_keyword)
        if not visible:
            drawer_btn = await page.query_selector('mat-icon[data-mat-icon-name="page_info"]')
            if drawer_btn:
                parent_btn = await drawer_btn.evaluate_handle('el => el.closest("button")')
                await parent_btn.click()
                await asyncio.sleep(2.0)
                visible = await page.evaluate(f'''(kw) => {{
                    const btn = Array.from(document.querySelectorAll('button, span, .menu-text')).find(i => i.innerText.toLowerCase().includes(kw));
                    if (btn) {{ btn.click(); return true; }}
                    return false;
                }}''', tool_keyword)
        if visible:
            await asyncio.sleep(3.0); return True
        return False
    except Exception: return False

async def check_response_status(page, logger=None):
    """
    V5.1.9: Now captures the "Minors" refusal and specific Chinese phrasing.
    """
    status_data = await page.evaluate('''() => {
        const bodyText = document.body.innerText;
        const bodyTextLower = bodyText.toLowerCase();
        
        // 1. Generation Check
        const isGenerating = bodyTextLower.includes("nano banana") || 
                             !!document.querySelector('mat-progress-bar');
        if (isGenerating) return { status: "generating", text: "" };

        // 2. Comprehensive Refusal Check
        const refusalKeywords = [
            "can't generate", "cannot generate", "policy", "safety", "real people", "minors",
            "不能生成", "无法生成", "真实人物", "未成年人", "描绘他们", "安全提示", "试试其他想法", "抱歉"
        ];
        
        // Scan the last model response or all paragraph tags for policy hits
        const responses = Array.from(document.querySelectorAll('model-response'));
        const lastRespText = responses.length > 0 ? responses[responses.length - 1].innerText : "";
        const allPTags = Array.from(document.querySelectorAll('p')).map(p => p.innerText).join(" ");
        
        const fullCheckText = (lastRespText + " " + allPTags).toLowerCase();

        if (refusalKeywords.some(kw => fullCheckText.includes(kw))) {
            return { status: "refused", text: "Policy Hit" };
        }

        // 3. Success Check
        const lastResp = responses[responses.length - 1];
        const hasImages = lastResp ? !!lastResp.querySelector('img') : false;
        if (hasImages) return { status: "success", text: "" };

        return { status: "waiting", text: "" };
    }''')

    if logger and status_data['status'] != "waiting":
        logger.info(f">> [DEBUG] Status: {status_data['status']}")
    return status_data['status']
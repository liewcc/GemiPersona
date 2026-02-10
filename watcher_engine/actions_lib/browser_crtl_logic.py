import asyncio
import os
import json
import re

# Version: V5.2.18 (Log Formatting & Text Flattening)
# Update: Implemented text flattening for Gemini's response to prevent log line breaking.
# Update: Maintained English comments and UI per user personalization instructions.

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
        file_name = os.path.basename(file_path)
        try:
            async with page.expect_file_chooser(timeout=30000) as fc_info:
                logger.info(f">> Preparing to upload: {file_name}")
                await page.evaluate('''() => {
                    const gemsIcon = document.querySelector('mat-icon[data-mat-icon-name="add_2"]');
                    if (gemsIcon) { gemsIcon.closest('button').click(); }
                }''')
                await asyncio.sleep(2.0)
                await page.evaluate('''() => {
                    const opt = Array.from(document.querySelectorAll('.menu-text, span')).find(i => i.innerText.toLowerCase().includes("upload files"));
                    if (opt) opt.click();
                }''')
                file_chooser = await fc_info.value
                await file_chooser.set_files(abs_path)
            logger.info(f">> [SUCCESS] {file_name} uploaded.")
            await asyncio.sleep(4.0)
        except Exception as e:
            logger.error(f"[FAIL] Upload error: {e}"); return False
    return True
#--------------------------------------------------------------------------

async def check_response_status(page, logger=None):
    """
    V5.3.1: Aligned quota detection logic with refusal detection.
    Both now use initial default lists and .extend() from config.json for consistency.
    """
    config_path = "config.json"
    # Initialized both with default triggers to ensure baseline detection
    declined_kws = ["违反", "规范", "点子", "协助你将想法化为现实"] 
    quota_kws = ["quota exceeded", "daily limit", "reached your limit"]
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                # Now both use .extend() to merge rather than overwrite
                declined_kws.extend(cfg.get("declined_msg", []))
                quota_kws.extend(cfg.get("quota_exceeded_msg", []))
        except Exception as e:
            if logger:
                logger.error(f">> [ERROR] Failed to load keywords from config: {e}")

    eval_data = {"declined": declined_kws, "quota": quota_kws}

    data = await page.evaluate('''(args) => {
        const bodyTextLower = document.body.innerText.toLowerCase();
        
        // 1. Check if still generating
        const isGenerating = bodyTextLower.includes("nano banana") || !!document.querySelector('mat-progress-bar');
        if (isGenerating) return { status: "generating", text: "..." };

        // 2. Get the latest response block
        const responses = Array.from(document.querySelectorAll('model-response'));
        if (responses.length === 0) return { status: "waiting", text: "" };
        
        const lastResp = responses[responses.length - 1];
        const literalText = lastResp.innerText.trim(); 
        const lowerText = literalText.toLowerCase();

        // 3. Quota detection (Using aligned logic)
        for (const kw of args.quota) {
            if (lowerText.includes(kw.toLowerCase())) return { status: "quota_exceeded", text: literalText };
        }

        // 4. Refusal detection (Policy)
        for (const kw of args.declined) {
            if (lowerText.includes(kw.toLowerCase())) return { status: "refused", text: literalText };
        }

        // 5. Success detection (Images)
        if (!!lastResp.querySelector('img')) return { status: "success", text: literalText };

        // 6. Final Fallback
        if (literalText.length > 0) {
            return { status: "waiting", text: literalText };
        }

        return { status: "waiting", text: "" };
    }''', eval_data)

    if logger and data['text']:
        # Flattening text to prevent log line breaking
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
    
#--------------------------------------------------------------
# Global logging for text updates
# Global logging for text updates
    if logger and data['text']:
        # # 将原始信息追加到根目录下的 output.txt，并强制刷新缓冲区确保立即看到内容
        # with open("output.txt", "a", encoding="utf-8") as f:
            # f.write(data['text'] + "\n" + "="*30 + "\n")
            # f.flush()  # Ensure content is written to disk immediately

        # 强化清洗逻辑：先手动替换硬换行，再用 split 拍平，彻底解决 engine.log 分段问题
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
    try:
        visible = await page.evaluate(f'''(kw) => {{
            const btn = Array.from(document.querySelectorAll('button, span')).find(i => i.innerText.toLowerCase().includes(kw));
            if (btn) {{ btn.click(); return true; }}
            return false;
        }}''', tool_keyword)
        if visible: logger.info(f">> Tool selected: {tool_keyword}")
        return visible
    except: return False
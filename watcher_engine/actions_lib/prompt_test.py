import asyncio
import os
import json
import sys
from PIL import Image, PngImagePlugin

# --- PATH ADAPTATION ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    import browser_crtl_logic as bcl
except ImportError:
    from . import browser_crtl_logic as bcl

# --- VERSIONING ---
# Version: V5.1.8
# Update: Aligned with Logic Core V5.1.8. Strictly using [FAIL]/[SUCCESS].

async def run(page, logger, config_path):
    logger.info(">>> [STATUS] Running Prompt_Test V5.1.8")

    try:
        # 1. Initialize
        if not await bcl.start_new_chat(page, logger, config_path):
            return False
            
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        
        # 2. Tool Selection
        if not await bcl.ensure_tool_selected(page, logger, "create image"):
            logger.warning(">> Tool selection could not be confirmed.")
        
        # 3. Prompt Injection
        prompt_text = cfg.get("last_prompt", "").strip()
        logger.info(">> Injecting prompt...")
        await page.wait_for_selector('[role="textbox"]', state="visible")
        await page.evaluate('''(text) => {
            const tb = document.querySelector('[role="textbox"]');
            tb.focus();
            const dt = new DataTransfer();
            dt.setData('text/plain', text);
            tb.dispatchEvent(new ClipboardEvent('paste', { clipboardData: dt, bubbles: true }));
            if (tb.innerText.trim().length === 0) document.execCommand('insertText', false, text);
        }''', prompt_text)
        
        # Verification
        content_check = await page.evaluate('() => document.querySelector(\'[role="textbox"]\').innerText.trim()')
        if not content_check:
            await page.keyboard.type(prompt_text)

        await asyncio.sleep(0.5)
        await page.keyboard.press("Enter")
        logger.info(">> [SIGNAL] Prompt submitted. Monitoring...")

        # 4. Monitoring
        status = "waiting"
        for _ in range(60):
            status = await bcl.check_response_status(page)
            if status == "refused":
                logger.warning("[FAIL] Policy Refusal detected.")
                break
            elif status == "success":
                logger.info(">> [SIGNAL] Success. Processing images...")
                break
            await asyncio.sleep(2)

        if status == "refused": return False
        if status == "waiting":
            logger.error("[FAIL] Timeout: No result signal.")
            return False

        # 5. Download
        last_response = await page.query_selector('model-response:last-of-type')
        imgs = await last_response.query_selector_all('img') if last_response else []
        dl_count = 0
        start_idx = cfg.get("name_start", 1)
        save_dir = cfg.get("save_dir", "browser_outputs")

        for img in imgs:
            box = await img.bounding_box()
            if box and box['width'] > 150:
                try:
                    await img.click(force=True); await asyncio.sleep(3)
                    async with page.expect_download(timeout=15000) as dl_info:
                        await page.evaluate('''() => {
                            const btn = Array.from(document.querySelectorAll('button')).find(b => (b.ariaLabel?.includes("Download") || b.innerText.includes("Download")) && b.offsetParent !== null);
                            if (btn) btn.click();
                        }''')
                        download = await dl_info.value
                        save_name = f"{cfg.get('name_prefix','')}{str(start_idx).zfill(cfg.get('name_padding',2))}.png"
                        temp_path = await download.path()
                        with Image.open(temp_path) as pil_img:
                            meta = PngImagePlugin.PngInfo()
                            meta.add_text("Prompt", prompt_text)
                            pil_img.save(os.path.join(save_dir, save_name), "PNG", pnginfo=meta)
                        logger.info(f">> Saved: {save_name}")
                        start_idx += 1; dl_count += 1
                    await page.keyboard.press("Escape"); await asyncio.sleep(1.0)
                except Exception: await page.keyboard.press("Escape")

        # Sync Config
        cfg["name_start"] = start_idx
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
            
        logger.info(f"[SUCCESS] Prompt_Test task finished. Downloaded: {dl_count}")
        return True

    except Exception as e:
        logger.error(f"[FAIL] Prompt_Test crash: {e}")
        return False
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

# Version: V5.1.14
# Update: Refactored MONITORING LOOP to pass logger every turn, ensuring immediate capture of refusal text.

async def run(page, logger, config_path):
    logger.info(">>> [STATUS] Running Upload_Test V5.1.14")

    try:
        # --- [STEP 0: Load Config] ---
        if not os.path.exists(config_path):
            logger.error("[FAIL] Config missing.")
            return False
            
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        save_dir = cfg.get("save_dir", "browser_outputs")
        prompt_text = cfg.get("last_prompt", "AI generated art")
        start_idx = cfg.get("name_start", 1)
        prefix = cfg.get("name_prefix", "")
        padding = cfg.get("name_padding", 2)        

        if not await bcl.start_new_chat(page, logger, config_path): return False
        with open(config_path, "r", encoding="utf-8") as f: cfg = json.load(f)
        if not await bcl.handle_file_upload(page, logger, cfg.get("upload_task", [])): return False
        await bcl.ensure_tool_selected(page, logger, "create image")
        
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
        
        await asyncio.sleep(0.5)
        await page.keyboard.press("Enter")
        logger.info(">> [SIGNAL] Prompt submitted. Monitoring loop started.")

        # --- MONITORING LOOP ---
        status = "waiting"
        for i in range(20):
            # Always pass logger to ensure check_response_status can print text the moment it appears
            status = await bcl.check_response_status(page, logger)
            
            if status == "refused":
                logger.error("[FAIL] Declined to generate.")
                return False
            elif status == "quota_exceeded":
                logger.error("[END] Quota Limit detected.")
                return False
            elif status == "success":
                logger.info(">> [SIGNAL] Images detected. Starting download...")
                break
                
            # Heartbeat info every 10 seconds if still waiting
            if i % 5 == 0 and status in ["waiting", "generating"]:
                logger.info(f">> [MONITOR] Status: {status} (Attempt {i+1}/60)")
                
            await asyncio.sleep(2)
        # --- END MONITORING LOOP ---

        if status != "success":
            logger.error("[FAIL] [RESET_REQUIRED] Timeout or Image failure: No image signal detected.")
            return False

        # --- DOWNLOAD PROCESS ---
        last_response = await page.query_selector('model-response:last-of-type')
        imgs = await last_response.query_selector_all('img') if last_response else []
        dl_count = 0

        for img in imgs:
            box = await img.bounding_box()
            if box and box['width'] > 150:
                try:
                    await img.evaluate('(el) => el.click()')
                    await asyncio.sleep(3)
                    async with page.expect_download(timeout=15000) as dl_info:
                        await page.evaluate('''() => {
                            const btn = Array.from(document.querySelectorAll('button'))
                                             .find(b => (b.ariaLabel?.includes("Download") || b.innerText.includes("Download")) && b.offsetParent !== null);
                            if (btn) btn.click();
                        }''')
                        download = await dl_info.value
                        temp_path = await download.path()

                        # Atomic collision check for filename
                        while True:
                            save_name = f"{prefix}{str(start_idx).zfill(padding)}.png"
                            final_path = os.path.join(save_dir, save_name)
                            if not os.path.exists(final_path): break
                            start_idx += 1

                        with Image.open(temp_path) as pil_img:
                            meta = PngImagePlugin.PngInfo()
                            meta.add_text("Prompt", prompt_text)
                            pil_img.save(final_path, "PNG", pnginfo=meta)
                        
                        logger.info(f">> Saved: {save_name}")
                        start_idx += 1
                        dl_count += 1
                    
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(1.0)
                except Exception as e:
                    logger.error(f">> Download failed: {e}")
                    await page.keyboard.press("Escape")

        # Sync back to config
        cfg["name_start"] = start_idx
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
            
        logger.info(f"[SUCCESS] Upload task finished. Downloaded: {dl_count}")
        return True

    except Exception as e:
        logger.error(f"[FAIL] V5.1.14 Crash: {e}")
        return False
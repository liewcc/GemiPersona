import asyncio
import os
import json
import sys
import time
from PIL import Image, PngImagePlugin

# --- PATH ADAPTATION ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    import browser_crtl_logic as bcl
except ImportError:
    from . import browser_crtl_logic as bcl

# Version: V5.1.14 (Redo Specialized)
# Update: Refactored MONITORING LOOP to pass logger every turn to catch refusal text instantly.

async def run(page, logger, config_path):
    logger.info(">>> [STATUS] Running Upload_Test_Redo V5.1.14")

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

        # --- [STEP 1: Trigger Redo Menu] ---
        menu_triggered = await page.evaluate('''async () => {
            const findTrigger = () => {
                return document.querySelector('button[aria-label*="Regenerate"]') || 
                       document.querySelector('mat-icon[data-mat-icon-name="refresh"]')?.closest('button') ||
                       document.querySelector('button .google-symbols[fonticon="refresh"]')?.closest('button');
            };
            const trigger = findTrigger();
            if (trigger) {
                trigger.scrollIntoView({behavior: "smooth", block: "center"});
                trigger.click();
                return true;
            }
            return false;
        }''')

        if not menu_triggered:
            logger.error("[FAIL] Redo menu trigger not found.")
            return False
            
        await asyncio.sleep(1.5)

        # --- [STEP 2: Click 'Try again'] ---
        redo_clicked = await page.evaluate('''async () => {
            const overlay = document.querySelector('.cdk-overlay-pane');
            if (!overlay) return false;
            const items = Array.from(overlay.querySelectorAll('button[role="menuitem"], .mat-mdc-menu-item'));
            const btn = items.find(b => b.innerText.toLowerCase().includes("try again"));
            if (btn) { btn.click(); return true; }
            return false;
        }''')

        if not redo_clicked:
            logger.error("[FAIL] 'Try again' button not found in overlay.")
            return False
        
        logger.info(">> Redo triggered successfully. Monitoring response...")

        # --- MONITORING LOOP ---
        status = "waiting"
        for i in range(15):
            # Pass logger every 2 seconds to ensure no message is missed due to loop frequency
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
                
            if i % 5 == 0 and status in ["waiting", "generating"]:
                logger.info(f">> [MONITOR] Status: {status} (Attempt {i+1}/60)")
                
            await asyncio.sleep(2)
        # --- END MONITORING LOOP ---

        if status != "success":
            logger.error("[FAIL] Timeout: Redo action failed to produce images.")
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
            
        logger.info(f"[SUCCESS] Redo task finished. Downloaded: {dl_count}")
        return True

    except Exception as e:
        logger.error(f"[FAIL] Redo crash: {e}")
        return False
import asyncio
import os
import json
import logging
import time
from PIL import Image, PngImagePlugin

# --- VERSIONING ---
# Version: V1.1.0 (Correction)
# Logic: Scroll -> Redo/TryAgain -> Wait for New Imgs -> Download -> Finish.

async def run(page, logger, config_path):
    logger.info(">>> [STATUS] Upload_test V1.1.0 (Continuous Loop) started.")
    
    try:
        # --- [STEP 0: Load Config] ---
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        save_dir = cfg.get("save_dir", "GemiPersona_outputs")
        prompt_text = cfg.get("last_prompt", "AI generated art")
        
        # --- [STEP 1: Scroll Down to Focus] ---
        logger.info(">>> [STEP 1] Scrolling down to find Redo...")
        # 寻找当前页面已有的图片作为滚动焦点
        existing_imgs = await page.query_selector_all('img')
        if existing_imgs:
            box = await existing_imgs[-1].bounding_box()
            if box:
                await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                for _ in range(3):
                    await page.mouse.wheel(0, 500)
                    await asyncio.sleep(0.5)

        # --- [STEP 2: Trigger Redo & Try Again] ---
        logger.info(">>> [STEP 2] Attempting to click Redo/Try Again...")
        triggered = await page.evaluate('''async () => {
            const findBtn = (sel) => document.querySelector(sel);
            const findByText = (txt) => Array.from(document.querySelectorAll('button'))
                                            .find(b => b.innerText.toLowerCase().includes(txt));
            
            let redoBtn = findBtn('regenerate-button button') || 
                          findBtn('button[aria-label="Redo"]') ||
                          document.querySelector('mat-icon[data-mat-icon-name="refresh"]')?.closest('button');

            if (redoBtn) {
                redoBtn.scrollIntoView({behavior: "smooth", block: "center"});
                redoBtn.click();
                await new Promise(r => setTimeout(r, 2000));
                
                let tryAgain = findByText("try again");
                if (tryAgain) { tryAgain.click(); return "REDO_WITH_TRY_AGAIN"; }
                return "REDO_CLICKED";
            }
            return "NOT_FOUND";
        }''')
        
        if triggered == "NOT_FOUND":
            logger.error(">>> [ERROR] Redo button not found after scrolling.")
            return False
        logger.info(f">>> [STEP 2] Result: {triggered}")

        # --- [STEP 3: Wait for New Images] ---
        # --- [STEP 3: 增强型动态侦察与拒绝识别 (V2.1.0)] ---
        
        logger.info(">> [STEP 3] Monitoring engine status (Refusal detection enabled)...")
        
        max_wait = 120 
        start_time = time.time()
        engine_detected = False
        refusal_detected = False

        while (time.time() - start_time) < max_wait:
            # 强化版 JS 侦察：同时返回生成状态、是否有拒绝文案、是否有图片生成
            status_report = await page.evaluate('''() => {
                const bodyText = document.body.innerText.toLowerCase();
                
                // 1. 进度条检测 (nano banana)
                const isGenerating = bodyText.includes("nano banana") || 
                                     !!document.querySelector('mat-progress-bar') ||
                                     !!document.querySelector('.generating-progress');
                
                // 2. 拒绝生成文案检测
                const refusalKeywords = ["can't help", "safety", "policy", "unable", "sorry", "against our guidelines"];
                const hasRefusalText = refusalKeywords.some(kw => bodyText.includes(kw));
                
                // 3. 检查最后一个回复框内是否已经渲染了图片
                const lastResponse = document.querySelector('model-response:last-of-type');
                const hasImages = lastResponse ? !!lastResponse.querySelector('img') : false;

                // 4. 自动滚动保持视野 (Container-Aware Scrolling)
                const findScrollable = () => {
                    const elements = document.querySelectorAll('main, div[role="main"], .conversation-container, [class*="chat-history"]');
                    for (let el of elements) {
                        if (el.scrollHeight > el.clientHeight) return el;
                    }
                    return null;
                };
                const container = findScrollable();
                if (isGenerating && container) {
                    container.scrollTop = container.scrollHeight;
                }

                return { isGenerating, hasRefusalText, hasImages };
            }''')

            is_gen = status_report['isGenerating']
            has_refusal = status_report['hasRefusalText']
            has_img = status_report['hasImages']

            if is_gen:
                if not engine_detected:
                    logger.info(">> Engine 'nano banana' active. Generation in progress...")
                    engine_detected = True
            else:
                # 如果引擎不再运行（进度条消失）
                if engine_detected:
                    # 场景 A: 进度条跑完，且有图片 -> 成功
                    if has_img:
                        logger.info(">> Engine finished. Images detected.")
                        break
                    # 场景 B: 进度条跑完，没图片但有拒绝词 -> 被拒
                    elif has_refusal:
                        logger.warning(">>> [REFUSAL] Gemini refused to generate images (Safety/Policy).")
                        refusal_detected = True
                        break
                    # 场景 C: 进度条消失，既没图片也没拒绝词 -> 可能是加载故障
                    else:
                        logger.error(">> Engine stopped. No images or refusal text found.")
                        break
                else:
                    # 还没开始生成时的等待期，定期同步滚动
                    if int(time.time() - start_time) % 8 == 0:
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            
            await asyncio.sleep(2.0)

        # 判定结果处理
        if refusal_detected:
            logger.error(">> [FAIL] Task Aborted: Gemini Refusal detected.")
            # 可选：在此处将失败状态写回 config.json 或发送特定通知
            return False 

        # Final stabilization scroll (仅在成功时执行)
        logger.info(">> Step 3 complete. Stabilizing view for Step 4.")
        await page.evaluate('''() => {
            const container = document.querySelector('main') || document.body;
            container.scrollTop = container.scrollHeight;
            window.scrollTo(0, document.body.scrollHeight);
        }''')
        await asyncio.sleep(3.0)
        
        # --- [STEP 4: Download New Images] ---
        # --- [STEP 4: Download New Images (V2.1.6 增强版)] ---
        
        logger.info(">>> [STEP 4] Starting download cycle...")
        start_idx = cfg.get("name_start", 1)
        prefix = cfg.get("name_prefix", "")
        padding = cfg.get("name_padding", 2)
        dl_count = 0
        processed_srcs = set() # Track processed images to prevent duplicates
        
        # 1. 确保页面滚动到最底部，并预留时间给 UI 渲染
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(2)

        # 2. 获取图片列表（增加筛选：过滤掉过小的图标）
        imgs = await page.query_selector_all('img')
        valid_imgs = []
        for img in imgs:
            box = await img.bounding_box()
            if box and box['width'] > 250:
                valid_imgs.append(img)
        
        # 只处理最后生成的 4 张
        new_imgs = valid_imgs[-4:] if len(valid_imgs) >= 4 else valid_imgs
        logger.info(f">> Found {len(new_imgs)} target images to download.")
        
        for img in new_imgs:
            try:
                # 3. 核心修复：更强力的滚动，确保元素在视口中心
                await img.evaluate('el => el.scrollIntoView({behavior: "instant", block: "center"})')
                await asyncio.sleep(1)
                
                # 使用 force=True 绕过遮挡检测，或者直接在 JS 中触发点击
                await img.click(force=True) 
                logger.info(f">>> [INFO] Expanded preview for Image {start_idx}")
                await asyncio.sleep(3) 
                
                # 4. 执行下载
                async with page.expect_download(timeout=10000) as dl_info:
                    # 使用更精准的选择器定位下载按钮
                    download_triggered = await page.evaluate('''() => {
                        const b = Array.from(document.querySelectorAll('button'))
                                     .find(x => x.ariaLabel?.includes("Download") || 
                                               x.title?.includes("Download") ||
                                               x.innerText.includes("Download"));
                        if(b) { b.click(); return true; }
                        return false;
                    }''')
                    
                    if not download_triggered:
                        raise Exception("Download button not found in preview.")

                    download = await dl_info.value
                    save_name = f"{prefix}{str(start_idx).zfill(padding)}.png"
                    save_path = os.path.join(save_dir, save_name)
                    
                    temp_path = await download.path()
                    # Save with Metadata
                    with Image.open(temp_path) as pil_img:
                        meta = PngImagePlugin.PngInfo()
                        meta.add_text("Prompt", prompt_text)
                        pil_img.save(save_path, "PNG", pnginfo=meta)
                    
                    logger.info(f">> [SUCCESS] Saved: {save_name}")
                    start_idx += 1
                    dl_count += 1
                
                # 6. 安全关闭预览
                await page.keyboard.press("Escape")
                await asyncio.sleep(1.5)

            except Exception as e:
                logger.warning(f">>> [WARNING] Image {start_idx} skip: {e}")
                # 即使出错也尝试按一次 Escape 确保不会卡在预览界面
                await page.keyboard.press("Escape")
                await asyncio.sleep(1)

        # --- [STEP 5: Sync Config] ---
        
        cfg["name_start"] = start_idx
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        
        logger.info(">> [SUCCESS] Upload_test continuous loop finished.")
        return True

    except Exception as e:
        logger.error(f">>> [CRASH] Upload_test V1.1.0: {e}")
        return False
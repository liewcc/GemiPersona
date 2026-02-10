# watcher_engine/actions_lib/scrape_gem_info.py
# Version: V1.2.5
# Description: Ultra-fast polling scraper for Gemini Gems.
# Changes: Removed 'networkidle' to prevent hanging; added active polling for Angular content.

import asyncio
import json
import os

async def run(page, logger, config_path):
    logger.info("🚀 Action: Starting Ultra-fast Gem Scrape (V1.2.5)...")
    RESULT_FILE = "scraped_info.json"
    
    try:
        # 1. READ URL
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        target_url = cfg.get("url")
        if not target_url:
            logger.error("❌ Target URL missing.")
            return False

        # 2. NAVIGATE (Fast Mode)
        logger.info(f"🌐 Navigating to: {target_url}")
        # Use 'domcontentloaded' instead of 'networkidle' to avoid hanging
        await page.goto(target_url, wait_until="domcontentloaded", timeout=60000)

        # 3. ACTIVE POLLING FOR CONTENT
        logger.info("⏳ Polling for Gem content...")
        scraped_data = {"name": "", "description": ""}
        
        # Poll for 20 seconds
        for i in range(40): 
            scraped_data = await page.evaluate('''() => {
                const clean = (t) => t ? t.trim().replace(/\\n/g, ' ') : "";
                
                // Try to find Name
                const nameContainer = document.querySelector('.bot-name-container');
                let name = "";
                if (nameContainer) {
                    const temp = nameContainer.cloneNode(true);
                    const badge = temp.querySelector('bot-experiment-badge, .bot-name-container-animation-box');
                    if (badge) badge.remove();
                    name = clean(temp.innerText);
                }

                // Try to find Description
                const descContainer = document.querySelector('.bot-description');
                let description = "";
                if (descContainer) {
                    description = clean(descContainer.innerText);
                }

                return { name, description };
            }''')

            # If we got at least the name, we can stop early
            if scraped_data["name"] and scraped_data["name"] != "Gemini":
                logger.info(f"🎯 Content found at poll {i+1}")
                break
            
            await asyncio.sleep(0.5)

        # 4. FINAL CHECK & FALLBACK
        if not scraped_data["name"]:
            scraped_data["name"] = (await page.title()).replace(" - Gemini", "").trim()
        
        if not scraped_data["name"] or scraped_data["name"] == "Gemini":
            scraped_data["name"] = "New Gem (Fetch Failed)"

        # 5. SAVE RESULT
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(scraped_data, f, indent=4, ensure_ascii=False)
            
        logger.info(f"✨ Scrape result: {scraped_data['name']}")
        return True

    except Exception as e:
        logger.error(f"❌ Scrape failed with error: {e}")
        return False
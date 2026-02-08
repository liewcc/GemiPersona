import asyncio
import os
import json
import logging
import time
from PIL import Image, PngImagePlugin

async def run(page, logger, config_path):

    logger.info("Executing Action: Sand Box")
    try:
        # Gemini 的 New Chat 按钮通常包含特定的 aria-label 或 text
        # 选择器建议使用通用性较强的方式
        new_chat_button = page.locator('button:has-text("New chat"), [aria-label="New chat"]')
        
        if await new_chat_button.is_visible():
            await new_chat_button.click()
            logger.info(">>> 'New Chat' clicked successfully.")
            # 给页面一点响应时间
            await asyncio.sleep(2) 
        else:
            logger.warning(">>> 'New Chat' button not visible. Trying to open menu first...")
            # 如果是移动端或窗口过小，可能需要先点开左侧菜单 (Hamburger menu)
            menu_button = page.locator('[aria-label="Main menu"], [aria-label="Expand menu"]')
            if await menu_button.is_visible():
                await menu_button.click()
                await asyncio.sleep(1)
                await new_chat_button.click()
                logger.info(">>> 'New Chat' clicked after opening menu.")



    except Exception as e:
        logger.error(f"Action Error (check_signin): {e}")
        return "ERROR"
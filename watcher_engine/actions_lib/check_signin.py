# watcher_engine/actions_lib/check_signin.py
# Version: V1.3.0
# Description: Sign-in check with User Name detection and auto-screenshot.

import asyncio
import os
import re

async def run(page, logger, config_path):
    logger.info("Executing Action: Sign In Status Check & User Discovery")
    try:
        # 1. Extended wait for Headless stability
        await page.wait_for_timeout(200)
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except:
            logger.info("Network idle timeout, checking elements...")

        # 2. Selectors
        # Standard Google account button usually contains the name in aria-label
        user_avatar = page.locator('a[href*="accounts.google.com/SignOut"], button[aria-label*="Google Account"]').first
        signin_button = page.locator('a[href*="accounts.google.com/ServiceLogin"], button:has-text("Sign in")').first

        is_logged_in = await user_avatar.is_visible()
        is_not_logged_in = await signin_button.is_visible()

        if is_logged_in:
            # --- User Name Detection Logic ---
            user_name = "Unknown User"
            aria_label = await user_avatar.get_attribute("aria-label")
            
            if aria_label:
                # Regex to extract name from "Google Account: Name (email@gmail.com)"
                match = re.search(r"Google Account:\s*(.*?)\s*\(", aria_label)
                if match:
                    user_name = match.group(1)
                else:
                    # Fallback for different label formats
                    user_name = aria_label.replace("Google Account:", "").strip()

            logger.info(f"✅ Status: Logged In. User: {user_name}")
            return True

        elif is_not_logged_in:
            debug_img = "headless_signin_detected.png"
            await page.screenshot(path=debug_img, full_page=True)
            logger.warning(f"❌ Status: Not Logged In. Screenshot saved to {debug_img}")
            return False
            
        else:
            # 3. Fallback: Secondary sidebar check
            chat_list = page.locator('div[data-test-id="conversations-list"]').first
            if await chat_list.is_visible():
                logger.info("✅ Status: Logged In (Detected via sidebar, Name: Unknown).")
                return True
            
            # Save screenshot for unknown state
            debug_img = "headless_unknown_state.png"
            await page.screenshot(path=debug_img, full_page=True)
            logger.warning(f"❌ Status: Unknown. Screenshot saved to {debug_img}")
            return False
            
    except Exception as e:
        logger.error(f"Action Error (check_signin): {e}")
        return "ERROR"
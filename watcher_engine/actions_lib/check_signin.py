# watcher_engine/actions_lib/check_signin.py
# Version: V1.2.1
# Description: Sign-in check with auto-screenshot for headless debugging.

import asyncio
import os

async def run(page, logger, config_path):
    logger.info("Executing Action: Sign In Status Check (Debug Mode)")
    try:
        # 1. Extended wait for Headless stability
        await page.wait_for_timeout(3000)
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except:
            logger.info("Network idle timeout, checking elements...")

        # 2. Selectors with .first to avoid strict mode violation
        user_avatar = page.locator('a[href*="accounts.google.com/SignOut"], button[aria-label*="Google Account"]').first
        signin_button = page.locator('a[href*="accounts.google.com/ServiceLogin"], button:has-text("Sign in")').first

        is_logged_in = await user_avatar.is_visible()
        is_not_logged_in = await signin_button.is_visible()

        if is_logged_in:
            logger.info("✅ Status: Logged In.")
            return True
        elif is_not_logged_in:
            # 3. Save evidence if sign-in button is seen
            debug_img = "headless_signin_detected.png"
            await page.screenshot(path=debug_img, full_page=True)
            logger.warning(f"❌ Status: Not Logged In. Screenshot saved to {debug_img}")
            return False
        else:
            # 4. Fallback: Secondary sidebar check
            chat_list = page.locator('div[data-test-id="conversations-list"]').first
            if await chat_list.is_visible():
                logger.info("✅ Status: Logged In (Detected via sidebar).")
                return True
            
            # Save screenshot for unknown state
            debug_img = "headless_unknown_state.png"
            await page.screenshot(path=debug_img, full_page=True)
            logger.warning(f"❌ Status: Unknown. Screenshot saved to {debug_img}")
            return False
            
    except Exception as e:
        logger.error(f"Action Error (check_signin): {e}")
        return "ERROR"
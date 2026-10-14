import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

ARTIFACTS_DIR = Path(r"C:\Users\user\.gemini\antigravity\brain\0f0387c8-fb6d-4b0d-825a-964da86c5a8e")
PROJECT_ROOT = Path(r"d:\Mysite1")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Desktop viewport standard 1280x768 (as on user laptop in screenshot)
        page = await browser.new_page(viewport={"width": 1280, "height": 768})

        # Serve locally via file:// or http://
        url = (PROJECT_ROOT / "pages" / "contacts.html").as_uri()
        print(f"Navigating to {url}")
        await page.goto(url, wait_until="networkidle")

        # Scroll to ticket booking section
        booking_section = page.locator("#ticket-booking")
        await booking_section.scroll_into_view_if_needed()
        await page.wait_for_timeout(1000)

        # 1. Screenshot booking form with currency pills, payment tabs, and disclaimer
        form_shot_path = ARTIFACTS_DIR / "verified_checkout_ui_fixed.png"
        await booking_section.screenshot(path=str(form_shot_path))
        print(f"Saved checkout UI screenshot to {form_shot_path}")

        # 2. Test Currency Switcher clicks
        curr_usd = page.locator('.currency-btn[data-curr="USD"]')
        if await curr_usd.count() > 0:
            await curr_usd.click()
            await page.wait_for_timeout(300)

        curr_tjs = page.locator('.currency-btn[data-curr="TJS"]')
        if await curr_tjs.count() > 0:
            await curr_tjs.click()
            await page.wait_for_timeout(300)

        # 3. Fill form and submit to trigger modal
        await page.locator("#ticketBuyerName").fill("Усмони Умар")
        await page.locator("#ticketBuyerEmail").fill("umar@example.com")
        await page.locator("#ticketBuyerPhone").fill("+992 92 777 88 99")

        # Submit
        submit_btn = page.locator('button[type="submit"][form="ticketBookingForm"]')
        await submit_btn.click()

        # Wait for modal active
        modal = page.locator("#ticketModal")
        await page.wait_for_selector("#ticketModal.active", timeout=5000)
        await page.wait_for_timeout(1000)

        # 4. Screenshot the full browser viewport showing the modal perfectly centered & fitting
        modal_full_path = ARTIFACTS_DIR / "verified_modal_full_screen.png"
        await page.screenshot(path=str(modal_full_path))
        print(f"Saved full screen modal screenshot to {modal_full_path}")

        # 5. Screenshot just the ticket pass card
        pass_card = page.locator(".ticket-pass")
        pass_shot_path = ARTIFACTS_DIR / "verified_ticket_pass_card.png"
        await pass_card.screenshot(path=str(pass_shot_path))
        print(f"Saved pass card screenshot to {pass_shot_path}")

        await browser.close()
        print("Visual verification complete!")

if __name__ == "__main__":
    asyncio.run(main())

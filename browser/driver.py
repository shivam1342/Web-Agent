"""
Browser driver using Playwright for web automation.
"""

from playwright.sync_api import sync_playwright


class BrowserDriver:
    """Manages browser interactions with Playwright"""
    
    def __init__(self, headless: bool = False):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()

    def open(self, url: str):
        """Navigate to URL"""
        self.page.goto(url)
        self.page.wait_for_load_state("domcontentloaded")

    def get_page_state(self):
        """Get current page state"""
        return {
            "url": self.page.url,
            "title": self.page.title(),
            "buttons": self._get_buttons(),
            "links": self._get_links(),
            "errors": self._get_errors(),
        }
    
    def get_page(self):
        """Return the Playwright page object"""
        return self.page

    def click_button(self, text: str) -> bool:
        """Click button by text"""
        try:
            self.page.get_by_role("button", name=text).first.click()
            self.page.wait_for_timeout(1500)
            return True
        except Exception:
            return False

    def click_link(self, text: str) -> bool:
        """Click link by text"""
        try:
            self.page.get_by_role("link", name=text).first.click()
            self.page.wait_for_timeout(1500)
            return True
        except Exception:
            return False

    def close(self):
        """Close browser"""
        self.browser.close()
        self.playwright.stop()

    # ---------- helpers ----------

    def _get_buttons(self):
        """Extract all button text"""
        return [
            b.inner_text().strip()
            for b in self.page.locator("button").all()
            if b.inner_text().strip()
        ]

    def _get_links(self):
        """Extract all link text"""
        return [
            a.inner_text().strip()
            for a in self.page.locator("a").all()
            if a.inner_text().strip()
        ][:20]  # Limit to first 20 to avoid overwhelming

    def _get_errors(self):
        """Detect error keywords on page"""
        keywords = ["error", "invalid", "failed"]
        try:
            body_text = self.page.inner_text("body").lower()
            return [k for k in keywords if k in body_text]
        except:
            return []

import logging
from typing import Set, Dict, Any
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Page

"""
Utilities For Downloading Files From URLs
"""

logger = logging.getLogger(__name__)

class BrowserNavigator:
    def __init__(self, config: Dict[str, Any]):
        self.headless = config.get("headless", False)
        self.timeout = config.get("timeout", 5000)
        self.wait_until = config.get("wait_until", "networkidle")
        self.max_links_to_follow = config.get("max_links_to_follow", 5)
        self.resource_urls = set()

    def _handle_response(self, response):
        """
        Handle response event by collecting the URL
        """
        self.resource_urls.add(response.url)

    async def extract_base_url(self, url: str) -> str:
        """
        Extract the base URL from a full URL
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    async def navigate_site(self, target_url: str) -> Set[str]:
        """
        Navigate the website and collect resource URLS
        """
        self.resource_urls = set()

        # Launch Playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            page.on("response", self._handle_response)

            logger.info(f"🌐 Navigating to {target_url}")
            await page.goto(target_url, wait_until=self.wait_until)
            await page.wait_for_timeout(self.timeout)

            await self._interact_with_page(page, target_url)

            await browser.close()

            logger.info(f"📥 Found {len(self.resource_urls)} resources")
            return self.resource_urls
        
    async def _interact_with_page(self, page: Page, target_url: str) -> None:
        """
        Interact with the page to trigger loading of additional resources
        """
        try:
            buttons = await page.query_selector_all("button")
            for button in buttons[:3]:
                try:
                    await button.click()
                    await page.wait_for_timeout(1000)
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Error interacting with buttons: {e}")

        try:
            links = await page.query_selector_all("a")
            base_url = await self.extract_base_url(target_url)
            
            for link in links[:self.max_links_to_follow]:
                try:
                    href = await link.get_attribute("href")
                    if href and href.startswith("#/"):
                        logger.info(f"🔍 Navigating to: {href}")
                        await page.goto(f"{base_url}/{href.lstrip('#/')}", wait_until=self.wait_until)
                        await page.wait_for_timeout(1000)
                except Exception as e:
                    logger.debug(f"Error navigating to link: {e}")
        except Exception as e:
            logger.debug(f"Error finding links: {e}")


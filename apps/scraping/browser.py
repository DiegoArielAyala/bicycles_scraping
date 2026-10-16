import asyncio
import logging
import random

from playwright.async_api import async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth

from apps.scraping.constants import CHROME_USER_AGENT
from core.exceptions import CloudflareChallengeError

logger = logging.getLogger(__name__)


class BrowserSession():
    CLOUDFLARE_MARKER = "cdn-cgi/challenge-platform"
    LISTING_READY_SELECTOR = "li.item.product.product-item, article.product-miniature"
    CLOUDFLARE_WAIT_MS = 45000
    CLOUDFLARE_RETRY_DELAY_RANGE = (15, 25)
    PAGES_PER_SESSION = 2


    def __init__(self):
        self.pages_in_session = 0
        self.context = None
        self.page = None
        self.browser = None
        self.playwright = None
    

    async def __aenter__(self):
        logger.info({"event": "enter_browser_session"})
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"]
        )

        self.context, self.page = await self.open_session()

        return self
    

    async def __aexit__(self, exc_type, exc_value, traceback):
        logger.info({"event": "exit_browser_session"})
        try:
            await self.close_session()
        finally:
            try:
                if self.browser:
                    await self.browser.close()
            finally:
                if self.playwright:
                    await self.playwright.stop()


    async def fetch_html(self, url):
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        html = await self.page.content()

        if self.CLOUDFLARE_MARKER in html:
            logger.warning({"event": "cloudflare_challenge_detected", "url": url})
            html = await self.wait_for_cloudflare_clear()
        
        return html
        

    async def get_html(self, url, page_number):
        if self.pages_in_session >= self.PAGES_PER_SESSION:
            logger.info({"event": "rotate_browser_session", "next_page": page_number})
            await self.close_session()
            self.context, self.page = await self.open_session()
            self.pages_in_session = 0
        try:
            html = await self.fetch_html(url)

        except CloudflareChallengeError:
            logger.warning({"event": "cloudflare_rotate_session", "url": url, "page": page_number})

            await asyncio.sleep(random.uniform(*self.CLOUDFLARE_RETRY_DELAY_RANGE))

            await self.close_session()
            self.context, self.page = await self.open_session()
            self.pages_in_session = 0

            html = await self.fetch_html(url)
        
        self.pages_in_session+=1
        return html
    

    async def open_session(self):
        self.context = await self.browser.new_context(
            user_agent=CHROME_USER_AGENT,
            viewport={"width": 1366, "height": 768},
            locale="es-ES",
        )
        stealth = Stealth()
        await stealth.apply_stealth_async(self.context)
        self.page = await self.context.new_page()

        return self.context, self.page


    async def close_session(self):
        try:
            if self.page:
                await self.page.close()
        finally:
            if self.context:
                await self.context.close()


    async def wait_for_cloudflare_clear(self):
        try:
            await self.page.wait_for_function(
                """() => {
                    const html = document.documentElement.innerHTML;
                    const challengeGone = !html.includes('cdn-cgi/challenge-platform');
                    const hasListing = !!document.querySelector(
                        'li.item.product.product-item, article.product-miniature'
                    );
                    return challengeGone || hasListing;
                }""",
                timeout=self.CLOUDFLARE_WAIT_MS,
            )
        except PlaywrightTimeoutError:
            logger.error({"event": "cloudflare_challenge_timeout"})
            raise CloudflareChallengeError("Cloudflare challenge did not clear")
            
        html = await self.page.content()
        has_listing = await self.page.query_selector(self.LISTING_READY_SELECTOR)
        if self.CLOUDFLARE_MARKER in html and not has_listing:
            raise CloudflareChallengeError("Cloudflare challenge still present")

        logger.info({"event": "cloudflare_challenge_cleared"})
        return html



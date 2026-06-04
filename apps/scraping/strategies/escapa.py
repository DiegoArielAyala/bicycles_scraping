import asyncio
import random

from bs4 import BeautifulSoup

from apps.scraping.strategies.base import ScrapingStrategy

class EscapaStrategy(ScrapingStrategy):
    BASE_URL = "https://www.biciescapa.com/es/"
    SEARCH_ENDPOINT = "https://www.biciescapa.com/es/bicicletas/?en-stock=1&page={}"

    def _extract_price(self, product_element):
        price_span = product_element.find("span", class_= "price current-price-discount") or product_element.find("span", class_= "price")
        
        return price_span.text if price_span else None
    
    def _extract_reference(self, product_element):
        bicycle_reference = product_element.get("data-id-product")

        return bicycle_reference if bicycle_reference else None
    
    def _extract_name(self, product_element):
        name_tag = product_element.find("h3", class_="h3-product-title")
        
        return name_tag.text.strip() if name_tag else None
    
    def _extract_img(self, product_element):
        img_tag = product_element.find("img")

        return img_tag.get("src") if img_tag else None
    
    def get_product_elements_html(self, soup):
        product_elements_html = soup.find_all("article", class_="product-miniature js-product-miniature mb-3")
        
        return product_elements_html
    
    async def bicycle_exists(self, page, reference):
        url = self.BASE_URL
        await page.goto(url)
        try:
            await page.click("button#onetrust-accept-btn-handler", timeout=3000)
        except:
            pass

        await page.fill("input[name='s']", str(reference))
        await asyncio.sleep(random.uniform(3, 6))
        await page.wait_for_selector("div.dfd-card-flag", timeout=5000)

        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        div = soup.find("div", class_="dfd-card-flag", attrs={"data-availability":"out-of-stock"})
    
        if div.text.strip() == "Agotado" or "Prueba de nuevo con otra búsqueda…" in soup.text:
            return False
        else:
            return True
        
    def get_list_url(self, counter):
        return self.SEARCH_ENDPOINT.format(counter)
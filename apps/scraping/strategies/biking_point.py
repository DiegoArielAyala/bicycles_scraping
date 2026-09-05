import re
import logging

from apps.scraping.strategies.base import ScrapingStrategy
from core.utils import is_last_product

""" Error de import circular - chat envio de emails gratis"""

logger = logging.getLogger(__name__)

class BikingPointStrategy(ScrapingStrategy):
    BASE_URL = "https://www.bikingpoint.es/es/bicicletas.html/?p={}"
    SEARCH_ENDPOINT = "https://www.bikingpoint.es/es/catalogsearch/result/?q={}"

    def _extract_price(self, product_element):
        prices = product_element.find_all("span", class_="price")
        return prices[0].text if prices else None
    
    def _extract_reference(self, product_element):
        img_tag = product_element.find("img")
        
        if not img_tag:
            return None
        
        data_src = img_tag.get("data-src")
        if not data_src:
            return None
        
        match = re.search(r"/(\d+)_([^/]+)\.jpg", data_src)
        
        return match.group(1) if match else None

    def _extract_name(self, product_element):
        name_tag = product_element.find("strong", class_="product-item-name")
        
        return name_tag.text.strip() if name_tag else None
    
    def _extract_img(self, product_element):
        img_tag = product_element.find("img", class_="product-image-photo") or product_element.find("img")
        if not img_tag:
            return None
        return img_tag.get("data-src") or img_tag.get("src")

    def get_product_elements_html(self, soup):
        if is_last_product(soup):
            logger.info({"event": "is_last_product", "web": "biking_point"})
            return []
        
        product_elements_html = soup.find_all("li", class_="item product product-item")
        
        return product_elements_html
    
    async def bicycle_exists(self, page, reference):
        url = self.SEARCH_ENDPOINT
        await page.goto(url.format(reference))
        content = await page.content()
        if "La búsqueda no ha devuelto ningún resultado." in content:
            return False
        else:
            return True
        
    def get_list_url(self, counter):
        return self.BASE_URL.format(counter)
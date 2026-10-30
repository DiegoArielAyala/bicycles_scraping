import logging

from apps.scraping.strategies.base import ScrapingStrategy

logger = logging.getLogger(__name__)

class EscapaStrategy(ScrapingStrategy):
    BASE_URL = "https://www.biciescapa.com/es/"
    SEARCH_ENDPOINT = "https://www.biciescapa.com/es/bicicletas/?page={}"

    def _extract_price(self, product_element):
        price_span = product_element.find("span", class_= "price current-price-discount") or product_element.find("span", class_= "price")
        
        return price_span.text if price_span else None
    
    def _extract_reference(self, product_element):
        bicycle_reference = str(product_element.get("data-id-product"))

        return bicycle_reference if bicycle_reference else None
     
    def _extract_name(self, product_element):
        name_tag = product_element.find("h3", class_="h3-product-title")
        
        return name_tag.text.strip() if name_tag else None
    
    def _extract_img(self, product_element):
        img_tag = product_element.find("img")

        return img_tag.get("data-src") or img_tag.get("src") if img_tag else None
    
    def get_product_elements_html(self, soup):
        product_elements_html = soup.find_all("article", class_="product-miniature js-product-miniature mb-3")
        
        return product_elements_html
    
    def get_list_url(self, counter):
        return self.SEARCH_ENDPOINT.format(counter)

    async def check_href(self, page, href):
        await page.goto(href)
        logger.debug({"event": "url_not_equal_to_href", "url": page.url, "href": href})
        return href == page.url

    def is_last_page(soup):
        return "No hay productos bajo esta categoría." in soup.text
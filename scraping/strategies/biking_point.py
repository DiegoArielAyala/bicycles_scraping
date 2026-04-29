import re

from ..exceptions import PriceNotFoundError, ReferenceNotFoundError, NameNotFoundError, ImgNotFoundError

from .base import ScrapingStrategy

class BikingPointStrategy(ScrapingStrategy):
    def get_name(self, product_element):
        return 

    def _extract_price(self, product_element, bicycle_reference):
        prices = product_element.find_all("span", class_="price")
        if not prices:
            raise PriceNotFoundError({"event": "price_not_found", "web": "biking_point", "reference": bicycle_reference})
        price_text = prices[0].text
        return price_text
    
    def _extract_reference(self, product_element):
        img_tag = product_element.find("img")
        
        if img_tag is None:
            raise ReferenceNotFoundError("img_tag not found")
        
        data_src = img_tag.get("data-src")
        if not data_src:
            raise ReferenceNotFoundError("data_src missing")
        
        match = re.search(r"/(\d+)_([^/]+)\.jpg", data_src)
        if not match:
            raise ReferenceNotFoundError("regex not match")
        
        return match.group(1)

    def _extract_name(self, product_element, bicycle_reference):
        name_tag = product_element.find("strong", class_="product-item-name")

        if not name_tag:
            raise NameNotFoundError(f"Name not found for reference {bicycle_reference}")
        
        return name_tag.text.strip()
    
    def _extract_img(self, product_element, bicycle_reference):
        img_tag = product_element.find("img")

        if not img_tag:
            raise ImgNotFoundError(f"Img not found for reference {bicycle_reference}")
        
        return img_tag.get("src")
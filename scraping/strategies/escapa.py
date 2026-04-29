from .base import ScrapingStrategy
from ..exceptions import PriceNotFoundError, ReferenceNotFoundError, NameNotFoundError, ImgNotFoundError

class EscapaStrategy(ScrapingStrategy):
    def _extract_price(self, product_element, bicycle_reference):
        price_span = product_element.find("span", class_= "price current-price-discount") or product_element.find("span", class_= "price")
        if not price_span:
            raise PriceNotFoundError({"event": "price_not_found", "web": "escapa", "reference": bicycle_reference})
        price_text = price_span.text
        
        return price_text
    
    def _extract_reference(self, product_element):
        bicycle_reference = product_element.get("data-id-product")
        if bicycle_reference is None:
            raise ReferenceNotFoundError("bicycle_reference not found")
        return bicycle_reference
    
    def _extract_name(self, product_element, bicycle_reference):
        name_tag = product_element.find("h3", class_="h3-product-title")

        if not name_tag:
            raise NameNotFoundError(f"Name not found for reference {bicycle_reference}")
        
        return name_tag.text.strip()
    
    def _extract_img(self, product_element, bicycle_reference):
        img_tag = product_element.find("img")

        if not img_tag:
            raise ImgNotFoundError(f"Img not found for reference {bicycle_reference}")

        return img_tag.get("src")
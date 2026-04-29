from .base import ScrapingStrategy
from ..exceptions import PriceNotFoundError, ReferenceNotFound

class EscapaStrategy(ScrapingStrategy):
    def get_name(self, product_element):
        return 
    
    def _extract_price(self, product_element, bicycle_reference):
        price_span = product_element.find("span", class_= "price current-price-discount") or product_element.find("span", class_= "price")
        if not price_span:
            raise PriceNotFoundError({"event": "price_not_found", "web": "escapa", "reference": bicycle_reference})
        price_text = price_span.text
        
        return price_text
    
    def _extract_reference(self, product_element):
        bicycle_reference = product_element.get("data-id-product")
        if bicycle_reference is None:
            raise ReferenceNotFound("bicycle_reference not found")
        return bicycle_reference
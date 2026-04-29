import logging

from ..exceptions import PriceNotFoundError

logger = logging.getLogger(__name__)

class ScrapingStrategy():
    def get_price(self, product_element, bicycle_reference):
        price_text = self._extract_price(product_element, bicycle_reference)
        return self.clean_price(price_text, bicycle_reference)

    def _extract_price(self, product_element, bicycle_reference):
        raise NotImplementedError
    
    def clean_price(self, price_text, bicycle_reference):
        cleaned_price = (
            price_text
            .replace("\xa0", "")
            .replace("€", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )
        
        if not cleaned_price:
            raise PriceNotFoundError(f"Price text is empty after cleaning for reference {bicycle_reference}")

        return cleaned_price

    def get_reference(self, product_element):
        bicycle_reference = self._extract_reference(product_element)
        logger.debug(f"Bicycle reference: {bicycle_reference}")
        return bicycle_reference

    def _extract_reference(self, product_element):
        raise NotImplementedError

    def get_product_info(self, product_element, bicycle_reference):
        bicycle_name = "Bicycle"
        bicycle_img = None

        bicycle_name = self._extract_name(product_element, bicycle_reference)
        bicycle_img = self._extract_img(product_element, bicycle_reference)

        logger.debug({"event": "product_info_extracted", "strategy": self.__class__.__name__, "reference": bicycle_reference, "name": bicycle_name, "img": bicycle_img
        })

        return bicycle_name, bicycle_img

    def _extract_name(self, product_element, bicycle_reference):
        raise NotImplementedError
    
    def _extract_img(self, product_element, bicycle_reference):
        raise NotImplementedError
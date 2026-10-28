import logging

from abc import ABC, abstractmethod
from bs4 import Tag
from decimal import Decimal
from typing import Optional, Tuple

from core.exceptions import PriceNotFoundError


logger = logging.getLogger(__name__)

class ScrapingStrategy(ABC):
    BASE_URL = None
    SEARCH_ENDPOINT = None

    def get_price(self, product_element: Tag) -> Optional[Decimal]:
        raw_price = self._extract_price(product_element)
        if raw_price is None:
            raise PriceNotFoundError
        return Decimal(self.clean_price(raw_price))
  
    def get_product_info(self, product_element: Tag) -> Tuple[str, Optional[str]]:
        bicycle_name = self._extract_name(product_element)
        bicycle_img = self._extract_img(product_element)
        
        return bicycle_name or "Bicycle", bicycle_img

    def get_reference(self, product_element: Tag) -> Optional[str]:
        return self._extract_reference(product_element)

    @abstractmethod
    def get_product_elements_html(self, soup):
        pass
    
    @abstractmethod
    def _extract_price(self, product_element: Tag) -> Optional[str]:
        pass

    @abstractmethod
    def _extract_name(self, product_element: Tag) -> Optional[str]:
        pass

    @abstractmethod
    def _extract_img(self, product_element: Tag) -> Optional[str]:
        pass

    @abstractmethod
    def _extract_reference(self, product_element: Tag) -> Optional[str]:
        pass

    @abstractmethod
    def get_list_url(self, counter: int) -> str:
        pass

    def get_end_of_catalog_text(self) -> Optional[str]:
        return None

    def clean_price(self, price_text):
        return (
            price_text
            .replace("\xa0", "")
            .replace("€", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )


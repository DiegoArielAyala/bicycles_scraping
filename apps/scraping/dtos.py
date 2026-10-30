from bs4.element import Tag
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class ScrapedPrices:
    reference: str
    current_price: Decimal
    product_element: Tag

@dataclass
class ScrapedBycicles:
    reference: str
    current_price: Decimal
    name: str
    web: str
    url: str
    last_seen_at: date
    is_active: bool
    img: str | None = None
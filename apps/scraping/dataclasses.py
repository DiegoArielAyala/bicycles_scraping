from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from xxlimited import Str

@dataclass
class ScrapedProduct:
    reference: str
    current_price: Decimal
    name: str
    web: str
    url: str
    last_seen_at: date
    img: str | None = None
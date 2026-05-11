from pydantic import field_validator, BaseModel 
from typing import Optional

class BicycleDTO(BaseModel):
    name: str
    price: float
    img: Optional[str]
    url: str    
    reference: str
    web: str

    @field_validator("price", mode="before")
    @classmethod
    def clean_price(cls, value):
        if value is None:
            return None
        
        return float(
            value
            .replace("\xa0", "")
            .replace("€", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
            )
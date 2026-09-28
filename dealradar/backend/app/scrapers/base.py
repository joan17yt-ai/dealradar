from dataclasses import dataclass
from typing import Optional

@dataclass
class ScrapedProduct:
    title: str
    price_cop: float
    original_price_cop: Optional[float]
    discount_percentage: int
    store: str
    product_url: str
    image_url: Optional[str]
    is_available: bool = True

class BaseScraper:
    def __init__(self, store_name: str):
        self.store_name = store_name

    async def search(self, query: str, limit: int = 5) -> list[ScrapedProduct]:
        raise NotImplementedError

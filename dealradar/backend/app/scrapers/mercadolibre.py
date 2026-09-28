import httpx
from typing import List
from app.scrapers.base import BaseScraper, ScrapedProduct

class MercadoLibreScraper(BaseScraper):
    def __init__(self):
        super().__init__("Mercado Libre")
        self.base_url = "https://api.mercadolibre.com/sites/MCO/search"

    async def search(self, query: str, limit: int = 5) -> List[ScrapedProduct]:
        products = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {"q": query, "limit": limit}
                headers = {"User-Agent": "DealRadar/1.0 (Android Price Tracker)"}
                response = await client.get(self.base_url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    for item in results:
                        price = float(item.get("price", 0))
                        original_price = item.get("original_price")
                        original_price = float(original_price) if original_price else price
                        discount = 0
                        if original_price > price and original_price > 0:
                            discount = int(round(((original_price - price) / original_price) * 100))

                        products.append(
                            ScrapedProduct(
                                title=item.get("title", ""),
                                price_cop=price,
                                original_price_cop=original_price,
                                discount_percentage=discount,
                                store=self.store_name,
                                product_url=item.get("permalink", ""),
                                image_url=item.get("thumbnail", ""),
                                is_available=True
                            )
                        )
        except Exception as e:
            print(f"[MercadoLibreScraper Error] {e}")
        return products

import httpx
from typing import List
from app.scrapers.base import BaseScraper, ScrapedProduct

class ExitoScraper(BaseScraper):
    def __init__(self):
        super().__init__("Éxito")
        self.api_url = "https://www.exito.com/api/catalog_system/pub/products/search"

    async def search(self, query: str, limit: int = 5) -> List[ScrapedProduct]:
        products = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json"
                }
                params = {"ft": query}
                response = await client.get(self.api_url, params=params, headers=headers)
                if response.status_code == 200:
                    items = response.json()
                    count = 0
                    for item in items:
                        if count >= limit:
                            break
                        items_sku = item.get("items", [])
                        if not items_sku:
                            continue
                        sellers = items_sku[0].get("sellers", [])
                        if not sellers:
                            continue
                        comm_offer = sellers[0].get("commertialOffer", {})
                        price = float(comm_offer.get("Price", 0))
                        list_price = float(comm_offer.get("ListPrice", price))
                        discount = 0
                        if list_price > price and list_price > 0:
                            discount = int(round(((list_price - price) / list_price) * 100))

                        images = items_sku[0].get("images", [])
                        img_url = images[0].get("imageUrl") if images else None

                        if price > 0:
                            products.append(
                                ScrapedProduct(
                                    title=item.get("productName", ""),
                                    price_cop=price,
                                    original_price_cop=list_price,
                                    discount_percentage=discount,
                                    store=self.store_name,
                                    product_url=item.get("link", ""),
                                    image_url=img_url,
                                    is_available=comm_offer.get("AvailableQuantity", 0) > 0
                                )
                            )
                            count += 1
        except Exception as e:
            print(f"[ExitoScraper Error] {e}")
        return products

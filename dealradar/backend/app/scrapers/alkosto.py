import httpx
from typing import List
from app.scrapers.base import BaseScraper, ScrapedProduct

class AlkostoScraper(BaseScraper):
    def __init__(self):
        super().__init__("Alkosto")
        self.api_url = "https://www.alkosto.com/rest/v2/alkosto/products/search"

    async def search(self, query: str, limit: int = 5) -> List[ScrapedProduct]:
        products = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json"
                }
                params = {
                    "query": query,
                    "pageSize": limit,
                    "fields": "FULL"
                }
                response = await client.get(self.api_url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    raw_products = data.get("products", [])
                    for p in raw_products:
                        price_obj = p.get("price", {})
                        price = float(price_obj.get("value", 0))
                        was_price_obj = p.get("wasPrice", {})
                        was_price = float(was_price_obj.get("value", price)) if was_price_obj else price
                        discount = 0
                        if was_price > price and was_price > 0:
                            discount = int(round(((was_price - price) / was_price) * 100))

                        url_path = p.get("url", "")
                        full_url = f"https://www.alkosto.com{url_path}" if url_path.startswith("/") else url_path

                        images = p.get("images", [])
                        img_url = images[0].get("url") if images else None
                        if img_url and img_url.startswith("/"):
                            img_url = f"https://www.alkosto.com{img_url}"

                        if price > 0:
                            products.append(
                                ScrapedProduct(
                                    title=p.get("name", query),
                                    price_cop=price,
                                    original_price_cop=was_price,
                                    discount_percentage=discount,
                                    store=self.store_name,
                                    product_url=full_url,
                                    image_url=img_url,
                                    is_available=True
                                )
                            )
        except Exception as e:
            print(f"[AlkostoScraper Error] {e}")
        return products

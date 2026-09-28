import httpx
from bs4 import BeautifulSoup
from typing import List
from app.scrapers.base import BaseScraper, ScrapedProduct

class AmazonScraper(BaseScraper):
    def __init__(self):
        super().__init__("Amazon")
        self.search_url = "https://www.amazon.com/s"
        # Tasa aproximada de conversión USD -> COP para envíos a Colombia
        self.usd_to_cop = 4150.0

    async def search(self, query: str, limit: int = 5) -> List[ScrapedProduct]:
        products = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8"
                }
                params = {"k": query}
                response = await client.get(self.search_url, params=params, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    items = soup.select("div[data-component-type='s-search-result']")
                    count = 0
                    for item in items:
                        if count >= limit:
                            break
                        title_el = item.select_one("h2 a span")
                        link_el = item.select_one("h2 a")
                        price_whole = item.select_one(".a-price-whole")
                        price_fraction = item.select_one(".a-price-fraction")
                        img_el = item.select_one(".s-image")

                        if title_el and link_el and price_whole:
                            title = title_el.text.strip()
                            link = "https://www.amazon.com" + link_el.get("href", "")
                            cents = price_fraction.text.strip() if price_fraction else "00"
                            price_str = price_whole.text.replace(".", "").replace(",", "").strip() + "." + cents
                            price_usd = float(price_str)
                            price_cop = round(price_usd * self.usd_to_cop)

                            img_url = img_el.get("src") if img_el else None

                            products.append(
                                ScrapedProduct(
                                    title=title,
                                    price_cop=price_cop,
                                    original_price_cop=price_cop,
                                    discount_percentage=0,
                                    store=self.store_name,
                                    product_url=link,
                                    image_url=img_url,
                                    is_available=True
                                )
                            )
                            count += 1
        except Exception as e:
            print(f"[AmazonScraper Error] {e}")
        return products

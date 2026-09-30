import urllib.parse
import httpx
from bs4 import BeautifulSoup
from typing import List
from app.scrapers.base import BaseScraper, ScrapedProduct

class MercadoLibreScraper(BaseScraper):
    def __init__(self):
        super().__init__("Mercado Libre")

    async def search(self, query: str, limit: int = 5) -> List[ScrapedProduct]:
        products = []
        encoded_query = urllib.parse.quote(query.strip())
        
        # 1. Intentar scraping HTML de listado oficial (más permisivo que la API)
        html_url = f"https://listado.mercadolibre.com.co/{encoded_query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-CO,es;q=0.9,en;q=0.8"
        }

        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.get(html_url, headers=headers)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Selectores modernos de Mercado Libre
                    items = soup.select(".ui-search-layout__item, .poly-card, .ui-search-result")
                    for item in items[:limit]:
                        title_el = item.select_one(".ui-search-item__title, .poly-component__title, h2")
                        link_el = item.select_one("a.ui-search-link, a.poly-component__title, a")
                        price_el = item.select_one(".andes-money-amount__fraction")
                        img_el = item.select_one("img.ui-search-result-image__element, img.poly-component__picture, img")

                        if title_el and price_el and link_el:
                            title = title_el.text.strip()
                            link = link_el.get("href", html_url)
                            price_text = price_el.text.replace(".", "").replace(",", "").strip()
                            price = float(price_text) if price_text.isdigit() else 0.0
                            img_url = img_el.get("src") or img_el.get("data-src") if img_el else None

                            if price > 0:
                                products.append(
                                    ScrapedProduct(
                                        title=title,
                                        price_cop=price,
                                        original_price_cop=price,
                                        discount_percentage=0,
                                        store=self.store_name,
                                        product_url=link,
                                        image_url=img_url,
                                        is_available=True
                                    )
                                )
        except Exception as e:
            print(f"[MercadoLibre HTML Error] {e}")

        # 2. Fallback a la API pública si HTML no devolvió nada
        if not products:
            try:
                api_url = f"https://api.mercadolibre.com/sites/MCO/search?q={encoded_query}&limit={limit}"
                async with httpx.AsyncClient(timeout=6.0) as client:
                    api_resp = await client.get(api_url, headers={"User-Agent": "Mozilla/5.0"})
                    if api_resp.status_code == 200:
                        data = api_resp.json()
                        for item in data.get("results", []):
                            price = float(item.get("price", 0))
                            if price > 0:
                                products.append(
                                    ScrapedProduct(
                                        title=item.get("title", query),
                                        price_cop=price,
                                        original_price_cop=float(item.get("original_price") or price),
                                        discount_percentage=0,
                                        store=self.store_name,
                                        product_url=item.get("permalink", html_url),
                                        image_url=item.get("thumbnail", ""),
                                        is_available=True
                                    )
                                )
            except Exception as e:
                print(f"[MercadoLibre API Error] {e}")

        return products

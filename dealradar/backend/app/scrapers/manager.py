import asyncio
from typing import List
from app.scrapers.base import ScrapedProduct
from app.scrapers.mercadolibre import MercadoLibreScraper
from app.scrapers.alkosto import AlkostoScraper
from app.scrapers.exito import ExitoScraper
from app.scrapers.amazon import AmazonScraper

class ScraperManager:
    def __init__(self):
        self.scrapers = [
            MercadoLibreScraper(),
            AlkostoScraper(),
            ExitoScraper(),
            AmazonScraper()
        ]

    async def search_all_stores(self, query: str, limit_per_store: int = 4) -> List[ScrapedProduct]:
        tasks = [scraper.search(query, limit=limit_per_store) for scraper in self.scrapers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_products: List[ScrapedProduct] = []
        for r in results:
            if isinstance(r, list):
                all_products.extend(r)

        # Ordenar por precio ascendente
        all_products.sort(key=lambda p: p.price_cop)
        return all_products

scraper_manager = ScraperManager()

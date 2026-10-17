"""Base Connector Abstract Class and Extracted Item Definition"""

from abc import ABC, abstractmethod
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class ScrapedItem(BaseModel):
    title: str
    current_price: Decimal
    original_price: Optional[Decimal] = None
    currency: str = "BRL"
    url: str
    external_id: Optional[str] = None
    store_slug: str
    image_url: Optional[str] = None
    seller_name: Optional[str] = None
    in_stock: bool = True
    rating: Optional[Decimal] = None
    reviews_count: int = 0
    raw_payload: dict = Field(default_factory=dict)


class BaseConnector(ABC):
    def __init__(self, site_slug: str, base_url: str):
        self.site_slug = site_slug
        self.base_url = base_url

    @abstractmethod
    async def search(self, query: str, limit: int = 20) -> list[ScrapedItem]:
        """Executa busca textual no site de compras."""
        pass

    @abstractmethod
    async def fetch_product_details(self, url: str) -> Optional[ScrapedItem]:
        """Extrai os dados e preço atual a partir de uma URL direta de produto."""
        pass

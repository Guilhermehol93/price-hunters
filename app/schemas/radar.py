from pydantic import BaseModel, Field, field_validator


class RadarSearchRequest(BaseModel):
    category: str = Field(min_length=1, max_length=150)
    query: str = Field(min_length=2, max_length=200)
    sites: list[str] = Field(min_length=1, max_length=8)
    min_discount_pct: float = Field(ge=0, le=100)
    use_market_history: bool = True

    @field_validator("sites")
    @classmethod
    def normalize_sites(cls, sites: list[str]) -> list[str]:
        normalized = []
        for value in sites:
            value = value.strip()
            if value and value not in normalized:
                normalized.append(value)
        if not normalized:
            raise ValueError("Informe pelo menos um site para pesquisar.")
        return normalized


class RadarCategoryResponse(BaseModel):
    categories: list[str]

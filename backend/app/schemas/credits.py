from pydantic import BaseModel


class CreditCategoryItem(BaseModel):
    type: str
    current: float
    required: float
    is_reached: bool
    gap: float


class CreditSummaryData(BaseModel):
    details: list[CreditCategoryItem]
    yearly_total: float
    total: float
    total_required: float
    per_type_required: float = 0.5
    is_total_reached: bool
    total_gap: float

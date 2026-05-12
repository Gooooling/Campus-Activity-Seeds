from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    content: str | None = Field(None, max_length=500, description="评价内容")


class ReviewData(BaseModel):
    id: int
    rating: int
    content: str | None
    reviewer_name: str
    created_at: datetime


class ReviewListItem(BaseModel):
    id: int
    rating: int
    content: str | None
    reviewer_name: str
    created_at: datetime

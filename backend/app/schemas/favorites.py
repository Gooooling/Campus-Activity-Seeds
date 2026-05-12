from pydantic import BaseModel, Field


class FavoriteToggleRequest(BaseModel):
    activity_id: int = Field(..., gt=0, description="活动ID")


class FavoriteToggleData(BaseModel):
    is_favorited: bool

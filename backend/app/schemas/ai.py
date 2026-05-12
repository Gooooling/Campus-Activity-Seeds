from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ParsedField(BaseModel):
    value: str | int | float | None = None
    confidence: Literal["high", "medium", "low"] = "low"


class ParseActivityRequest(BaseModel):
    article_text: str | None = Field(default=None, min_length=1)
    group_message: str | None = Field(default=None, min_length=1)

    @field_validator("article_text", "group_message")
    @classmethod
    def strip_whitespace(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip() or None
        return v

    @field_validator("article_text")
    @classmethod
    def check_at_least_one(cls, v: str | None, info) -> str | None:
        data = info.data
        other = data.get("group_message")
        if v is None and other is None:
            raise ValueError("article_text 和 group_message 至少填写一个")
        return v


class ParseActivityData(BaseModel):
    title: ParsedField
    activity_type: ParsedField
    start_time: ParsedField
    end_time: ParsedField
    location: ParsedField
    credit_type: ParsedField
    credit_value: ParsedField
    registration_deadline: ParsedField
    max_participants: ParsedField
    description: ParsedField


class CreditAdvicePriorityItem(BaseModel):
    type: str
    gap: float


class CreditAdviceActivityItem(BaseModel):
    id: int
    title: str
    credit_type: str
    credit_value: float | None
    registration_deadline: str
    location: str
    cover_image_url: str | None = None
    match_reason: str


class CreditAdviceData(BaseModel):
    total_gap: float
    priority_list: list[CreditAdvicePriorityItem]
    recommended_activities: list[CreditAdviceActivityItem]
    summary: str

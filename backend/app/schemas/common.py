from typing import Any

from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ResponseBase(BaseModel):
    code: int = 200
    message: str = "ok"
    data: Any = None


class PaginatedData(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]


def success(data: Any = None, message: str = "ok", code: int = 200) -> dict:
    return {"code": code, "message": message, "data": data}


def error(message: str, code: int = 400, data: Any = None) -> JSONResponse:
    return JSONResponse(status_code=code, content={"code": code, "message": message, "data": data})

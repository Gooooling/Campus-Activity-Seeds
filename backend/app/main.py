from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import settings
from app.config import settings
from app.database import async_session
from app.models.models import College
from app.routers.auth import router as auth_router
from app.routers.activities import router as activities_router
from app.routers.participations import router as participations_router
from app.routers.favorites import router as favorites_router
from app.routers.reviews import router as reviews_router
from app.routers.credits import router as credits_router
from app.routers.users import router as users_router
from app.routers.upload import router as upload_router
from app.routers.ai import router as ai_router
from app.routers.notifications import router as notifications_router
from app.routers.admin import router as admin_router
from app.routers.home import router as home_router
from app.routers.config import router as config_router
from app.routers.owners import router as owners_router
from app.routers.system_config import public_router as system_config_public_router
from app.scheduler import setup_scheduler

COLLEGE_SEED = [
    "基础医学院",
    "第一临床医学院",
    "第二临床医学院（全科医学院）",
    "医学技术学院",
    "护理学院",
    "药学院",
    "公共卫生学院",
    "妇儿医学院",
    "海洋与热带医学学院",
    "人文与管理学院",
    "生物医学工程学院(未来技术学院）",
    "外国语学院",
]


async def seed_colleges():
    async with async_session() as db:
        result = await db.execute(select(College))
        existing = result.scalars().all()
        if len(existing) < 12:
            existing_names = {c.name for c in existing}
            for name in COLLEGE_SEED:
                if name not in existing_names:
                    db.add(College(name=name))
            await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_colleges()
    scheduler = setup_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="校园活动信息港 V2",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChineseQueryMiddleware:
    """修复中文查询参数编码问题：确保 query_string 中的中文字符被正确 percent-encode。"""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] in ("http", "websocket"):
            qs = scope.get("query_string", b"")
            if qs:
                try:
                    qs.decode("ascii")
                except UnicodeDecodeError:
                    # 含非 ASCII 字符，重新 percent-encode
                    text = qs.decode("utf-8", errors="replace")
                    encoded = quote(text, safe="=&+%,:/;-._~!$'()*@")
                    scope["query_string"] = encoded.encode("ascii")
        await self.app(scope, receive, send)


app.add_middleware(ChineseQueryMiddleware)

app.include_router(auth_router)
app.include_router(activities_router)
app.include_router(participations_router)
app.include_router(favorites_router)
app.include_router(reviews_router)
app.include_router(credits_router)
app.include_router(users_router)
app.include_router(upload_router)
app.include_router(ai_router)
app.include_router(notifications_router)
app.include_router(admin_router)
app.include_router(config_router)
app.include_router(home_router)
app.include_router(owners_router)
app.include_router(system_config_public_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误", "data": None},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}

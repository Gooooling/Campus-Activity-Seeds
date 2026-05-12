from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    JWT_PRIVATE_KEY: str
    JWT_PUBLIC_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "Ed25519"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENAI_BASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str 

    UPLOAD_MAX_SIZE_MB: int = 10

    # CORS 来源，逗号分隔
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"

    # 允许的图片 MIME 类型，逗号分隔
    ALLOWED_MIME_TYPES: str = "image/jpeg,image/png,image/gif,image/webp,image/bmp"

    # 上传类型→子目录映射，JSON 格式
    TYPE_TO_SUBDIR: str = '{"activity_image":"activities","qrcode":"qrcodes","avatar":"avatars"}'

    # 通知清理保留天数
    NOTIFICATION_CLEANUP_DAYS: int = 15

    # 通知轮询间隔（前端用，毫秒）
    NOTIFICATION_POLL_INTERVAL: int = 600_000

    @property
    def DATABASE_URL_ASYNC(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

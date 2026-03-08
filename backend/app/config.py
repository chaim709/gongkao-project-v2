from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "公考管理系统 V2"
    APP_VERSION: str = "1.0.1"
    DEBUG: bool = False

    # 数据库配置
    DATABASE_URL: str = ""

    # JWT 配置
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120  # 2小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS 配置
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # AI 配置
    ANTHROPIC_API_KEY: str = ""
    AI_MODEL: str = "claude-sonnet-4-20250514"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    if not s.DATABASE_URL:
        raise ValueError("DATABASE_URL 环境变量未配置")
    if not s.SECRET_KEY:
        raise ValueError("SECRET_KEY 环境变量未配置")
    return s


settings = get_settings()

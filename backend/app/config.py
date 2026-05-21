from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    frontend_port: int = 5173

    database_url: str = "sqlite+aiosqlite:///./data/blog.db"

    claude_code_path: str = "claude"

    tistory_blog_url: str = ""

    obsidian_vault_path: str = ""

    sisyphus_dir: str = ".sisyphus"

    log_level: str = "INFO"

    stage_timeout: int = 600

    @property
    def sisyphus_path(self) -> Path:
        return Path(self.sisyphus_dir)

    @property
    def data_dir(self) -> Path:
        return Path("data")


settings = Settings()

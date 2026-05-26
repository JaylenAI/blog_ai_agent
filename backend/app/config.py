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

    oracle_threshold_chars: int = 10000
    slop_can_do_threshold: int = 5
    slop_emphasis_threshold: int = 3
    slop_superlatives_threshold: int = 2
    sentence_length_min: int = 15
    sentence_length_max: int = 80
    keyword_density_min: float = 0.005
    keyword_density_max: float = 0.025
    burstiness_min_std: float = 8.0

    image_generation_enabled: bool = True
    image_generation_timeout: int = 120
    max_images_per_article: int = 4
    image_allowed_tools: str = "Write,Bash"

    @property
    def sisyphus_path(self) -> Path:
        return Path(self.sisyphus_dir)

    @property
    def data_dir(self) -> Path:
        return Path("data")


settings = Settings()

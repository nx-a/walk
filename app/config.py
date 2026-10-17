import os
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql://shelter:shelter@localhost:5433/walks"
    )
    pool_min: int = int(os.getenv("DB_POOL_MIN", "1"))
    pool_max: int = int(os.getenv("DB_POOL_MAX", "10"))
    schema_path: Path = BASE_DIR / "app" / "schema.sql"
    static_dir: Path = BASE_DIR / "static"


settings = Settings()

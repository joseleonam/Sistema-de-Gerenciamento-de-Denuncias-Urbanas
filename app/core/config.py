"""
Configurações centrais da aplicação.
Carrega variáveis do arquivo .env e expõe Settings para uso global.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Banco de dados
    DATABASE_URL: str = "sqlite+aiosqlite:///./denuncias_urbanas.db"

    # Aplicação
    APP_NAME: str = "Sistema de Gerenciamento de Denúncias Urbanas"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,gif,pdf"

    @property
    def upload_path(self) -> Path:
        """Retorna o Path da pasta de uploads, criando-a se necessário."""
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()

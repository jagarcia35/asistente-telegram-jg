"""La configuración (del .env en tu equipo, o del panel Environment en Render) y el modelo.

En cualquier archivo:

    from config import modelo, settings
"""

from pathlib import Path
from typing import Literal

import pydantic_ai
from pydantic import SecretStr
from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_settings import BaseSettings, SettingsConfigDict

pydantic_ai.BANNER_ENABLED = False  # sin el aviso de Logfire en cada ejecución

RAIZ = Path(__file__).resolve().parent  # la carpeta del proyecto
DATOS = RAIZ / "datos"  # gastos.csv y documentos/*.pdf


class Settings(BaseSettings):
    """pydantic-settings lee el .env (o las variables de Render) y valida cada una con su tipo."""

    # extra="ignore": si tu .env trae otras variables, no pasa nada
    model_config = SettingsConfigDict(env_file=RAIZ / ".env", extra="ignore")

    modo: Literal["gemini", "local"] = "gemini"  # gemini = la nube · local = Ollama (no funciona en Render)
    gemini_api_key_local: SecretStr  # obligatoria; SecretStr no se imprime por accidente
    gemini_model: str = "gemini-3.5-flash-lite"
    ollama_model: str = "gemma4:e2b"
    telegram_token: SecretStr = SecretStr("")  # el token de @BotFather
    telegram_permitidos: str = ""  # números de chat separados por coma; vacío = nadie

    api_tokens: SecretStr = SecretStr("")  # extra opcional (API.md): tokens de la API separados por coma; vacío = nadie

    @property
    def permitidos(self) -> set[str]:
        return {c.strip() for c in self.telegram_permitidos.split(",") if c.strip()}

    @property
    def tokens(self) -> set[str]:
        return {t.strip() for t in self.api_tokens.get_secret_value().split(",") if t.strip()}


def crear_modelo(settings: Settings) -> Model:
    """El modelo de lenguaje, según el MODO."""
    if settings.modo == "local":
        # Ollama expone una API compatible con la de OpenAI en el puerto 11434
        provider = OllamaProvider(base_url="http://localhost:11434/v1")
        return OpenAIChatModel(settings.ollama_model, provider=provider)

    provider = GoogleProvider(api_key=settings.gemini_api_key_local.get_secret_value())
    return GoogleModel(settings.gemini_model, provider=provider)


settings = Settings()
modelo = crear_modelo(settings)

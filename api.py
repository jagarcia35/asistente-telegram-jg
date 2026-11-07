"""Extra opcional: tu asistente como API HTTP (instrucciones en API.md).

En tu equipo:  uv run uvicorn api:app --reload   →   http://127.0.0.1:8000/docs
En Render, es un segundo servicio del mismo repo, con otro Start Command.
"""

import secrets

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from asistente import responder
from config import settings

app = FastAPI(title="Mi asistente")


def autenticar(credenciales: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False))) -> None:
    """Como TELEGRAM_PERMITIDOS: sin un token de API_TOKENS no se llama al modelo (ni se gasta tu cuota)."""
    token = credenciales.credentials if credenciales else ""
    # compare_digest compara sin dar pistas por el tiempo que tarda
    if not any(secrets.compare_digest(token, valido) for valido in settings.tokens):
        raise HTTPException(401, "Token inválido")


class Pedido(BaseModel):
    """Lo que manda el cliente. Pydantic lo valida: un mensaje vacío o enorme da 422 sin llamar al modelo."""

    mensaje: str = Field(min_length=1, max_length=2000)


class Respuesta(BaseModel):
    texto: str


@app.post("/chat", dependencies=[Depends(autenticar)])
async def chat(pedido: Pedido) -> Respuesta:
    return Respuesta(texto=await responder(pedido.mensaje))  # el mismo responder que usa el bot

"""El agente: modelo + instrucciones + capabilities. Sin memoria: cada mensaje empieza de cero.

Pruébalo en la terminal, sin Telegram:  uv run asistente.py
"""

import asyncio

from pydantic_ai import Agent

from capacidades import apis, consulta, documentos, registro
from config import modelo

asistente = Agent(
    modelo,
    # ← Cambia esto por tu caso: para quién es, qué hace y qué NO hace.
    instructions=(
        "Eres el asistente personal de Alex: economía, clima, sus gastos y sus documentos. "
        "Responde en español, breve y en texto plano (sin Markdown)."
    ),
    capabilities=[apis, consulta, registro, documentos],  # ← aquí enchufas tus capabilities
)


async def responder(mensaje: str) -> str:
    """Lo único que necesita el bot: un mensaje entra, una respuesta sale."""
    resultado = await asistente.run(mensaje)  # await: mientras espera al modelo, el bot atiende a otros
    return resultado.output


async def main() -> None:
    while (mensaje := input("tú> ").strip()) not in {"", "salir"}:
        print("asistente>", await responder(mensaje))


if __name__ == "__main__":
    asyncio.run(main())  # un solo asyncio.run: todo lo async vive dentro

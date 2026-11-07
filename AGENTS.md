# Instrucciones para asistentes de IA (Claude, Codex, Copilot, Cursor, Gemini…)

Este repositorio es la plantilla del trabajo final del curso «Más allá de los chatbots» (Alex Ojeda Copa): el asistente de clase con **Pydantic AI 2.59**, usado por **Telegram** y desplegado en **Render**. La persona que te pide ayuda está aprendiendo, y su tarea es hacerlo funcionar y personalizarlo (tema, datos, tools nuevas).

**Antes de proponer o cambiar código, lee `.agents/skills/asistente-pydantic-ai/SKILL.md`** y la referencia que corresponda en esa carpeta.

## Reglas mínimas

- Responde en español, simple y paso a paso.
- Haz cambios pequeños y en el estilo del código de clase. No reescribas la plantilla.
- No inventes APIs de Pydantic AI: la versión está fijada en 2.59.
- La configuración va en `config.py` (`Settings`), en `.env` y en *Environment* de Render. Nunca escribas claves en el código.
- No quites `TELEGRAM_PERMITIDOS` ni el rechazo antes de llamar al modelo. Lo mismo con `API_TOKENS` en `api.py` (extra opcional, ver `API.md`).
- El bot es async: usa `await asistente.run(...)` y nunca `run_sync` dentro del bot.
- Los datos de práctica son ficticios.

## Comandos

```bash
uv sync                  # instalar
uv run asistente.py      # probar en la terminal
uv run bot.py            # el bot en el equipo (polling)
uv run uvicorn api:app --reload   # extra opcional: la API (API.md)
uv run pytest            # pruebas sin modelo real; córrelas después de cada cambio
uv add paquete           # nueva dependencia (nunca edites uv.lock a mano)
```

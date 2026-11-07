---
name: asistente-pydantic-ai
description: Guía del curso «Más allá de los chatbots» (Alex Ojeda Copa) para personalizar, ampliar, depurar y desplegar este asistente con Pydantic AI 2.59. Cubre lo visto en clase. S1, agentes, salida tipada, tools y capabilities con APIs públicas y SQLite. S2, búsqueda web y RAG con PDFs y citas. S3, MCP. S4, flujos con Pydantic Graph. S5, async/await, bot de Telegram y Render. Úsalo siempre que trabajes en este repositorio, por ejemplo para cambiar las instrucciones o los datos, agregar una tool, una API, una capability, un buscador, un servidor MCP o un flujo, desplegar en Render o entender un error.
---

# Asistente con Pydantic AI (curso «Más allá de los chatbots»)

Este repositorio es la plantilla del trabajo final: el asistente que se armó en clase, sesión por sesión, ahora como **bot de Telegram** desplegado en **Render**. La tarea de quien lo usa es **hacerlo funcionar y personalizarlo**: cambiar el tema, los datos o las instrucciones, y agregar cosas.

Quien te pide ayuda está aprendiendo, así que:
- Explica en español, simple y paso a paso. Di **en qué archivo y dónde** va cada cambio.
- Haz cambios pequeños sobre la plantilla, con el mismo estilo que el código de clase. No la reescribas ni añadas frameworks que el curso no usó.
- Si aparece un concepto nuevo (async, decoradores, tipos), explícalo antes con una analogía y el error que sale si se hace mal.

## Reglas de oro

1. **Pydantic AI está fijado en 2.59** (`pyproject.toml`). No inventes APIs. Si dudas de que algo exista, compruébalo con `uv run python -c "from pydantic_ai import X"`.
2. **La configuración sale de `config.py`** (`from config import modelo, settings`). Una variable nueva se declara como campo de `Settings` y va en `.env`, en `.env.example` sin valor y en *Environment* de Render.
3. **Las tools no inventan.** Devuelven solo lo útil y con `fuente`. Si no hay dato, devuelven `{"error": "…"}` para que el modelo lo diga.
4. **Los secretos nunca van en el código**: van en `.env` (ignorado por git) y en *Environment* de Render. Si una clave se filtra, se revoca.
5. **El bot es async:** dentro de `async def`, usa `await asistente.run(...)`. Hay un solo `asyncio.run` por programa, y nunca `run_sync` dentro del bot.
6. **No quites `TELEGRAM_PERMITIDOS`** ni el rechazo antes de llamar al modelo: sin eso, cualquiera gasta tu cuota.
7. **SQL siempre con `?`**, nunca armado con lo que manda el modelo. La lectura se abre en modo `?mode=ro`.
8. **Los datos de práctica son ficticios.**
9. **Prueba sin gastar cuota:** `uv run pytest` usa modelos falsos. Al agregar una tool, agrega su prueba.

## Mapa del repositorio

| Archivo | Qué tiene |
|---|---|
| `config.py` | `Settings` (lee `.env` o las variables de Render) y el `modelo` (Gemini u Ollama) |
| `capacidades.py` | `apis` (Banco Mundial y clima, S1), `consulta` y `registro` (gastos en SQLite, S1), `documentos` (RAG con PDFs, S2). **Aquí van las tuyas** |
| `asistente.py` | El `Agent`: instrucciones, lista de capabilities y `responder(mensaje)`. Sin memoria: cada mensaje empieza de cero |
| `bot.py` | Telegram: `/start`, la lista de permitidos, *polling* en el equipo y webhook en Render |
| `api.py` | **Extra opcional, no visto en clase:** el mismo `responder` como API HTTP con FastAPI y `API_TOKENS` (pasos en `API.md`) |
| `datos/` | `gastos.csv` (la base `gastos.db` se crea sola) y `documentos/*.pdf` |
| `tests/` | Pruebas sin modelo real |

## Receta: agregar una capability

1. En `capacidades.py`:

```python
recetas = Capability(
    id="recetas",
    description="Recetas bolivianas y sus ingredientes",
    instructions="Usa ingredientes para hablar de recetas. Si no la tienes, dilo.",
)

@recetas.tool_plain
def ingredientes(plato: str) -> list[str] | dict:
    """Ingredientes de un plato boliviano: silpancho, api o sopa de maní."""
    datos = {"silpancho": ["carne", "pan molido", "arroz", "papa", "huevo"]}
    return datos.get(plato.lower(), {"error": f"No tengo la receta de {plato}"})
```

2. En `asistente.py`: `from capacidades import ..., recetas` y agrégala a `capabilities=[...]`.
3. Prueba la tool sola (`print(ingredientes("silpancho"))`) y luego con el agente: `uv run asistente.py`.
4. `git add`, `git commit` y `git push`: Render vuelve a desplegar solo.

El docstring y los tipos son **el contrato**, lo único que el modelo ve de la tool. Usa `Literal[...]` para los valores cerrados y `Args:` en el docstring para explicar cada parámetro.

## Qué referencia leer

| Necesitas… | Lee |
|---|---|
| Repasar qué es un LLM, uv, los tipos o pydantic-settings | [referencias/s0-ia-y-python.md](referencias/s0-ia-y-python.md) |
| Agente, salida tipada, tools, capabilities, APIs o SQLite | [referencias/s1-agentes-y-tools.md](referencias/s1-agentes-y-tools.md) |
| Buscar en la web o en documentos propios (RAG con citas) | [referencias/s2-conocimiento.md](referencias/s2-conocimiento.md) |
| Usar o crear un servidor MCP | [referencias/s3-mcp.md](referencias/s3-mcp.md) |
| Un flujo de varios pasos: cadena o router (Pydantic Graph) | [referencias/s4-flujos-con-grafos.md](referencias/s4-flujos-con-grafos.md) |
| `async`/`await`, el bot, Render o los secretos | [referencias/s5-async-y-despliegue.md](referencias/s5-async-y-despliegue.md) |
| Un mensaje de error | [referencias/errores.md](referencias/errores.md) |

## Comandos

```bash
uv sync                  # instala (la primera vez y tras cambiar dependencias)
uv run asistente.py      # conversa en la terminal («salir» para terminar)
uv run bot.py            # el bot en tu equipo (polling)
uv run pytest            # pruebas sin modelo real
uv add paquete           # nueva dependencia (actualiza pyproject.toml y uv.lock)
```

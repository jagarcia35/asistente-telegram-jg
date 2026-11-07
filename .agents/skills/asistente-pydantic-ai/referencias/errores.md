# Errores frecuentes: qué ves y qué hacer

Busca aquí una parte del texto del error.

## Configuración y modelo

| Ves | Causa | Arreglo |
|---|---|---|
| `ValidationError … gemini_api_key_local Field required` | No hay `GEMINI_API_KEY_LOCAL` en `.env` ni en *Environment* | Crea la clave en aistudio.google.com/apikey y ponla |
| `Falta TELEGRAM_TOKEN` | No hay token | Créalo con @BotFather y ponlo en `.env` o en Render |
| `429 … RESOURCE_EXHAUSTED` / `exceeded your current quota` | Se acabó la cuota diaria gratis de ese modelo | Espera a mañana o cambia `GEMINI_MODEL` (por ejemplo, `gemini-3.1-flash-lite`) |
| `429 … spending cap` | La clave es de un proyecto de Google **con facturación** | Crea la clave en un proyecto sin facturación |
| `429` solo al buscar en la web | `WebSearch(local=False)` usa el buscador de Google, que no es gratis | `WebSearch(native=False, local=True)` o Tavily |
| Una variable de `.env` «no se aplica» | Una variable del entorno (la terminal o VS Code) gana a la del `.env` | Abre una terminal nueva o borra la variable del entorno |

## async / await

| Ves | Causa | Arreglo |
|---|---|---|
| `AttributeError: 'coroutine' object has no attribute 'output'` | `r = asistente.run(...)` sin `await` | `r = await asistente.run(...)`, o `run_sync` fuera de async |
| `RuntimeWarning: coroutine '…' was never awaited` | Llamaste a una función `async` sin `await` | Ponle `await` delante |
| `SyntaxError: 'await' outside function` | `await` suelto en un script | Mételo en `async def main()` y llama `asyncio.run(main())` |
| `RuntimeError: asyncio.run() cannot be called from a running event loop` | `asyncio.run` dentro de algo async o en un notebook | Usa `await` directo |
| `RuntimeError: This event loop is already running` | `run_sync` dentro de `async def`, del bot o de un notebook | Cambia a `await asistente.run(...)` |
| `… bound to a different event loop` / `Event loop is closed` | Dos `asyncio.run` (o `run_sync` y luego `asyncio.run`) en el mismo programa | Un solo `asyncio.run(main())` |

## Tools

| Ves | Causa | Arreglo |
|---|---|---|
| El modelo inventa una cifra o una cita | La tool no devuelve `fuente`, o las instrucciones no dicen «no inventes» | Devuelve la fuente y pide decir «no lo encuentro» |
| El modelo no usa tu tool | Docstring vago o la capability no está en `capabilities=[...]` | Docstring claro con `Args:`, y enchúfala en `asistente.py` |
| `UnexpectedModelBehavior: Exceeded maximum retries` | La salida no cumple el `output_type`, o la tool falla siempre | Simplifica el tipo, aclara el docstring; para clasificar, `NativeOutput(...)` |
| `sqlite3.OperationalError: no such table` | `gastos.db` se creó vacía o con otra tabla | Bórrala: se vuelve a crear desde el CSV |
| La búsqueda en documentos no encuentra en español | Embeddings por defecto de Chroma (en inglés) | `gemini-embedding-001` (ya está en `capacidades.py`) |
| `ModuleNotFoundError: No module named …` | Falta la dependencia | `uv add paquete` (y para un extra: `uv add "pydantic-ai-slim[google,openai,EXTRA]==2.59.0"`) |

## MCP y grafos

| Ves | Causa | Arreglo |
|---|---|---|
| `MCP(local="servidor.py")` falla | `local=` solo acepta URL o un transporte | `MCP(local=StdioTransport(command=sys.executable, args=["servidor.py"]))` |
| `421 Misdirected Request` | El servidor HTTP escucha en `127.0.0.1` | `host="0.0.0.0"` |
| «Error executing tool» sin detalle | `ValueError` en una tool MCP | `raise ToolError("mensaje útil")` |
| `TypeError: object … can't be used in 'await' expression` | Un paso de grafo con `def` | `async def` |
| `'StepContext' object has no attribute …` | Usaste el parámetro como si fuera el valor | El valor está en `ctx.inputs` |
| `GraphValidationError` en `build()` | Una rama sin camino a `g.end_node` | Conecta cada rama al final |

## Telegram y Render

| Ves | Causa | Arreglo |
|---|---|---|
| El bot contesta «No autorizado. Tu chat es N» | Tu chat no está en `TELEGRAM_PERMITIDOS` | Añade N (separa con comas) y reinicia, o guarda la variable en Render |
| El bot contesta «Algo falló…» | El modelo o una tool falló | Mira la terminal o los *Logs* de Render: ahí está el error |
| El bot de Render dejó de responder después de probar en tu equipo | El *polling* local borró el webhook | Render: *Manual Deploy → Restart service* |
| `telegram.error.Conflict: terminated by other getUpdates request` | Dos bots en *polling* con el mismo token | Deja uno solo corriendo |
| El primer mensaje tarda un minuto | Render Free se durmió | Es normal |
| Desaparecieron los gastos registrados | El disco de Render Free se borra al dormirse o al redesplegar | Es un límite conocido |
| El build falla por `uv.lock` (`--locked`) | Cambiaste `pyproject.toml` sin `uv lock` | `uv lock`, commit y push (mejor: `uv add paquete`) |
| *No open ports detected* | El servicio no escucha en `$PORT` | El Start Command debe ser `uv run --no-sync bot.py` |
| Asteriscos `**` en los mensajes | El modelo escribió Markdown | Las instrucciones piden texto plano; refuérzalo |

## Windows

| Ves | Causa | Arreglo |
|---|---|---|
| `UnicodeEncodeError … cp1252` | Consola en cp1252 | Usa Git Bash, o `sys.stdout.reconfigure(encoding="utf-8")` |
| `UnicodeDecodeError` al leer un archivo | Se abrió sin codificación | `open(..., encoding="utf-8")` |

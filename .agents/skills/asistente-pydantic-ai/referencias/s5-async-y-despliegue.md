# S5 · async/await y despliegue (Telegram + Render)

## async/await: el mesero que no se queda esperando

Un mesero **sin async** toma el pedido de la mesa 1, va a la cocina y **espera** el plato antes de atender a la mesa 2. Un mesero **con async** deja el pedido en cocina y, **mientras se cocina**, atiende la mesa 2. Esperar al modelo (1 a 5 s) es como esperar a la cocina: el bot puede atender a otras personas mientras tanto.

| Palabra | Qué significa |
|---|---|
| `async def f()` | «Esta función puede esperar sin bloquear». Llamarla **no** la ejecuta: devuelve una corrutina |
| `await f()` | «Ejecútala y espera su resultado sin bloquear a los demás». Solo vale **dentro** de un `async def` |
| `asyncio.run(main())` | Arranca el bucle de eventos (la cocina). **Uno solo** por programa, al final del script |

```python
async def pedido(mesa):
    await asyncio.sleep(1)                      # como esperar al modelo
    return mesa

await asyncio.gather(pedido("ana"), pedido("beto"), pedido("carla"))   # a la vez: ≈ 1 s, no 3
```

**¿`await` o `run_sync`? Mira dónde estás.**

| Dónde estás | Usa |
|---|---|
| Dentro de `async def` (el bot, una tool async, un paso de grafo) | `await asistente.run(...)` |
| En una celda de notebook | `await asistente.run(...)` (el notebook ya tiene un bucle) |
| En un script normal, fuera de todo `async def` | `asistente.run_sync(...)` o un solo `asyncio.run(main())` |

Las tools normales (`def`, con `httpx.get`) también sirven dentro del bot: Pydantic AI las corre aparte para no bloquear.

## El núcleo: un agente es una función

`asistente.py` expone `responder(mensaje) -> str`. El bot (o la terminal) solo llama a esa función, así que puedes cambiar el canal sin tocar al agente. El asistente **no tiene memoria**: cada mensaje empieza de cero.

## Telegram

1. En Telegram, abre **@BotFather** y escribe `/newbot`. Dale un nombre y un usuario que termine en `bot`. El **token** que te da (`123456:ABC…`) va en `TELEGRAM_TOKEN`. Quien tenga el token controla el bot. Si se filtra, invalídalo con `/revoke` en @BotFather.
2. Ejecuta `uv run bot.py` y escríbele `/start`: te responde con tu **número de chat**. Ponlo en `TELEGRAM_PERMITIDOS` (separa varios con comas) y reinicia el bot.
3. **¿Quién puede escribirle?** Cualquiera que encuentre su `@usuario`: los bots son públicos. Pero `bot.py` solo **responde** a la lista y rechaza al resto **antes** de llamar al modelo.

| | Polling (tu equipo) | Webhook (Render) |
|---|---|---|
| Cómo llegan los mensajes | El bot pregunta a Telegram cada poco | Telegram hace un POST a `https://tu-app.onrender.com/telegram` |
| URL pública | No necesita | Render la pone en `RENDER_EXTERNAL_URL` |
| Seguridad extra | — | Un `secret_token` derivado del token: solo Telegram lo conoce |

**No uses el mismo token en los dos a la vez.** Al arrancar, el *polling* **borra el webhook** y el bot de Render deja de recibir mensajes. Para recuperarlo, en Render usa *Manual Deploy → Restart service*. Para ver a dónde apunta el webhook, abre `https://api.telegram.org/bot<TOKEN>/getWebhookInfo` en tu navegador (no compartas esa URL).

## Render (plan Free), a mano

*New → Web Service → GitHub →* tu repositorio:

| Campo | Valor |
|---|---|
| Language | Python 3 |
| Branch | `main` |
| Build Command | `uv sync --locked --no-dev` |
| Start Command | `uv run --no-sync bot.py` |
| Instance Type | **Free** |
| Environment | `GEMINI_API_KEY_LOCAL`, `TELEGRAM_TOKEN`, `TELEGRAM_PERMITIDOS` |

- Render instala uv solo, porque hay un `uv.lock`, y usa Python 3.14 por el archivo `.python-version`.
- Cada `git push` a `main` vuelve a desplegar. Cambiar una variable en *Environment* también.
- En *Logs* debe aparecer `Webhook en https://….onrender.com/telegram`.

**Límites del plan Free:**
- **Se duerme** tras 15 minutos sin uso. El primer mensaje tarda alrededor de un minuto.
- **El disco es efímero.** Al reiniciar, redesplegar o dormirse, `gastos.db` vuelve a crearse desde `gastos.csv` y se pierden los gastos registrados.
- 512 MB de RAM: alcanza con Gemini; Ollama (`MODO=local`) no cabe.
- La cuota de Gemini gratis es **diaria**: si los Logs muestran un 429, espera o cambia `GEMINI_MODEL`.

## Secretos

| Dónde | Cómo |
|---|---|
| Tu equipo | `.env` (copia de `.env.example`), ignorado por `.gitignore` |
| GitHub | **Nunca** `.env`, claves ni tokens: lo subido queda en el historial |
| Render | Panel *Environment* |

Antes de subir, `git status` no debe mostrar `.env`, y `git grep -nE "AIza[0-9A-Za-z_-]{30}"` no debe encontrar nada.

## Extra no visto en clase: la API (`api.py`)

Opcional: el trabajo final es el bot. Los pasos están en `API.md`, en la raíz.

- `POST /chat` con `{"mensaje": "…"}` devuelve `{"texto": "…"}`, usando el mismo `await responder(mensaje)` que el bot.
- **Autenticación:** `Authorization: Bearer <token>`, con los tokens en `API_TOKENS` (separados por coma, uno por persona; vacío = nadie). Sin token válido responde 401 **antes** de llamar al modelo, igual que `TELEGRAM_PERMITIDOS`. Nunca reutilices el token de Telegram.
- **En tu equipo:** `uv run uvicorn api:app --reload` y `http://127.0.0.1:8000/docs` (botón *Authorize*).
- **En Render:** un **segundo** Web Service del mismo repositorio, con el mismo Build y Start `uv run --no-sync uvicorn api:app --host 0.0.0.0 --port $PORT`. Variables: `GEMINI_API_KEY_LOCAL` y `API_TOKENS`. Un servicio escucha en un solo puerto, y el del bot ya lo usa el webhook: por eso son dos servicios.
- **En las pruebas:** `httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app))` con `await` (ver `tests/`). Con `TestClient` y un modelo real, la app corre en otro event loop y el cliente del modelo falla.

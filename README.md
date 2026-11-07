# Mi asistente

Plantilla del trabajo final del curso **«Más allá de los chatbots»** de Alex Ojeda Copa. Es el asistente que armamos en clase con [Pydantic AI](https://pydantic.dev/docs/ai/), convertido en un **bot de Telegram** desplegado gratis en **Render**.

| Ya trae | Sesión | Dónde |
|---|---|---|
| Tools de lectura con APIs públicas (inflación del Banco Mundial, clima de Open Meteo) | S1 | `capacidades.py` → `apis` |
| Mi contador: gastos en SQLite, una tool que lee y otra que escribe | S1 | `capacidades.py` → `consulta` y `registro` |
| RAG: buscar en PDFs y citar la fuente | S2 | `capacidades.py` → `documentos` |
| El agente y su núcleo async: `responder(mensaje)` | S5 | `asistente.py` |
| El bot de Telegram con lista de permitidos: *polling* en tu equipo y webhook en Render | S5 | `bot.py` |

El asistente **no tiene memoria**: cada mensaje empieza de cero.

Lo que tienes que hacer y cómo se califica está en **[TRABAJO_FINAL.md](TRABAJO_FINAL.md)**.

---

## 0 · Lo que necesitas

| Qué | Para qué | Dónde |
|---|---|---|
| **uv** y **git** | Instalar y ejecutar; subir tu código | Los instalaste en la S0. En Windows, usa **Git Bash** |
| Una cuenta de **GitHub** | Guardar tu código; Render lo lee de ahí | [github.com](https://github.com) |
| Una clave de **Gemini** (gratis) | El modelo y los embeddings | [aistudio.google.com/apikey](https://aistudio.google.com/apikey), en un proyecto **sin facturación** |
| **Telegram** | Crear y usar el bot | [telegram.org](https://telegram.org) |
| Una cuenta de **Render** (gratis, sin tarjeta) | Publicar el bot en internet | [render.com](https://render.com): entra con *GitHub* |

## 1 · Tu copia de la plantilla

1. Arriba en esta página, pulsa **Use this template → Create a new repository**.
2. Ponle un nombre, por ejemplo `mi-asistente`. Puede ser **privado**.
3. Clónalo y entra en la carpeta:

```bash
git clone https://github.com/TU-USUARIO/mi-asistente.git
cd mi-asistente
```

## 2 · En tu equipo

```bash
cp .env.example .env     # y escribe tu GEMINI_API_KEY_LOCAL en .env (nunca subas .env)
uv sync                  # instala Python 3.14 y las dependencias en .venv/
uv run asistente.py      # conversa en la terminal; «salir» para terminar
```

Prueba estas preguntas:
- «¿Qué temperatura hace en Cochabamba?»
- «¿Cuál fue la inflación de Bolivia en 2023?»
- «¿Cuánto gasté en transporte?» y luego «Registra 35 Bs de almuerzo hoy».
- «Se me cayó la laptop, ¿la cubre la garantía?»: busca en los PDFs y cita `[garantia_laptop-1]`.

Para comprobar el código sin gastar cuota del modelo, corre `uv run pytest`.

## 3 · Tu bot de Telegram

**3.1 · Crea el bot**
1. En Telegram, busca **@BotFather** (con la marca azul de verificado) y pulsa *Iniciar*.
2. Escribe `/newbot`.
3. Escribe el **nombre** que verá la gente, por ejemplo «Asistente de Ana».
4. Escribe el **usuario**, que tiene que terminar en `bot`, por ejemplo `asistente_de_ana_bot`.
5. BotFather te da un **token** como `7812345678:AAH…`. Cópialo en `.env`: `TELEGRAM_TOKEN=7812345678:AAH…`

El token es la llave del bot: quien lo tenga lo controla. No lo compartas ni lo subas. Si se filtra, escribe `/revoke` en @BotFather para invalidarlo.

**3.2 · Arráncalo y averigua tu número de chat**

```bash
uv run bot.py
```

Abre tu bot en Telegram (el enlace `t.me/…_bot` que te dio BotFather) y pulsa **Iniciar** o escribe `/start`. Te responde «Tu número de chat es 123456789…».

**3.3 · Autorízate**
1. Detén el bot con Ctrl+C.
2. Pon ese número en `.env`: `TELEGRAM_PERMITIDOS=123456789`. Para varias personas, sepáralas con comas: `TELEGRAM_PERMITIDOS=123456789,987654321`.
   > **No es tu número de teléfono.** Es el número que te dio `/start`: sin `+`, sin código de país y sin espacios.
3. Ejecuta otra vez `uv run bot.py` y escríbele.

> **¿Cualquiera puede escribirle a mi bot?** Cualquiera que encuentre su usuario puede *escribirle*: en Telegram no hay bots privados. Pero el bot solo *responde* a los números de `TELEGRAM_PERMITIDOS`. Al resto le contesta «No autorizado» **sin llamar al modelo**, así que no gastan tu cuota. Si la lista está vacía, no le responde a nadie.

En tu equipo, el bot funciona por ***polling***: le pregunta a Telegram cada poco si hay mensajes. Si apagas la computadora, se apaga el bot. Para que esté siempre disponible, súbelo a Render.

## 4 · Despliegue en Render (paso a paso, a mano)

**4.1 · Sube tu código a GitHub**

```bash
git status               # .env NO debe aparecer en la lista
git add .
git commit -m "Mi asistente"
git push
```

**4.2 · Crea el servicio**
1. Entra a [dashboard.render.com](https://dashboard.render.com) con tu cuenta de GitHub.
2. Pulsa **+ New → Web Service**.
3. En *Source Code*, elige **GitHub**. La primera vez, pulsa *Configure GitHub* (o *Connect GitHub*) y dale acceso a tu repositorio.
4. Elige tu repositorio y completa:

| Campo | Valor |
|---|---|
| **Name** | `mi-asistente-ana`. Será parte de la URL: `https://mi-asistente-ana.onrender.com` |
| **Language** | `Python 3` |
| **Branch** | `main` |
| **Region** | La que quieras, por ejemplo *Virginia (US East)* |
| **Root Directory** | (vacío) |
| **Build Command** | `uv sync --locked --no-dev` |
| **Start Command** | `uv run --no-sync bot.py` |
| **Instance Type** | **Free** |

5. En **Environment Variables**, pulsa *Add Environment Variable* y agrega:

| Key | Value |
|---|---|
| `GEMINI_API_KEY_LOCAL` | Tu clave de Gemini |
| `TELEGRAM_TOKEN` | El token de BotFather |
| `TELEGRAM_PERMITIDOS` | Tu número de chat y el del docente, separados por coma |

6. Pulsa **Deploy Web Service**. La primera vez tarda unos minutos.

**4.3 · Comprueba que funciona**
1. En **Logs** debe aparecer `Webhook en https://mi-asistente-ana.onrender.com/telegram` y luego *Your service is live 🎉*.
2. **Detén el bot de tu equipo** (Ctrl+C), si seguía corriendo.
3. Escríbele en Telegram: ahora responde desde Render, aunque tu computadora esté apagada.

En Render, el mismo `bot.py` funciona con **webhook**: Telegram envía cada mensaje a tu URL. El código se da cuenta solo, porque Render define `RENDER_EXTERNAL_URL`. Además, Telegram firma cada aviso con un secreto que sale de tu token, así que nadie más puede hacerse pasar por Telegram.

**4.4 · Actualizar**
- Cada `git push` a `main` vuelve a desplegar solo.
- Si cambias una variable en **Environment** y la guardas, también se vuelve a desplegar.

> **Atajo opcional:** en lugar de los pasos 2 a 6 de 4.2, puedes usar **+ New → Blueprint**. Elige tu repositorio y rellena las variables que te pide: Render lee `render.yaml`, que tiene la misma configuración.

### Límites del plan Free

| Límite | Qué significa |
|---|---|
| **Se duerme** tras 15 minutos sin mensajes | El primer mensaje tarda alrededor de un minuto en responder; los siguientes son rápidos |
| **El disco es efímero** | Al dormirse o redesplegar, `gastos.db` vuelve a crearse desde `gastos.csv`: los gastos registrados se pierden |
| 512 MB de memoria | Alcanza con Gemini; Ollama no cabe |
| La cuota de Gemini gratis es **diaria** | Si el bot dice «Algo falló», mira los *Logs*: un `429` es cuota. Espera o cambia `GEMINI_MODEL` |

## 5 · Hazlo tuyo

- **Instrucciones** (`asistente.py`): para quién es, qué hace y qué no.
- **Datos** (`datos/`): tu propio `gastos.csv` (o la tabla que quieras) y tus PDFs, ficticios.
- **Tools y capabilities** (`capacidades.py`): agrega las tuyas y enchúfalas en `asistente.py`, en `capabilities=[...]`. Ideas:
  - otra API pública;
  - búsqueda web (S2);
  - un servidor MCP (S3);
  - un flujo con un grafo (S4).
- **Dependencias:** `uv add nombre-paquete`, nunca a mano. Luego haz commit de `pyproject.toml` y `uv.lock`.

> **Extra opcional:** si además quieres usar tu asistente como API HTTP, sigue [API.md](API.md). No hace falta para el trabajo final.

## 6 · Pide ayuda a una IA

Este repositorio trae un **skill** con lo que vimos en el curso: reglas, recetas con el código de clase y una tabla de errores reales. Está en [`.agents/skills/asistente-pydantic-ai/`](.agents/skills/asistente-pydantic-ai/SKILL.md).

| Herramienta | Cómo lo usa |
|---|---|
| **Claude Code** | Solo: lee `CLAUDE.md` y el skill. Pídele, por ejemplo: «agrega una capability con la API de tipos de cambio» |
| **Codex**, **Cursor**, **GitHub Copilot**, **Gemini CLI** | Leen `AGENTS.md`, que les dice dónde está el skill |
| **ChatGPT**, **Claude.ai**, **Gemini** (en la web) | Adjunta `SKILL.md` y la referencia que necesites (por ejemplo, `referencias/errores.md`), y pega tu código y el error completo |

La IA te ayuda, pero el código es tuyo: entiende cada cambio antes de aceptarlo, y nunca le pegues tus claves ni tokens.

## 7 · Problemas frecuentes

| Ves | Qué hacer |
|---|---|
| `ValidationError … gemini_api_key_local` o `Falta TELEGRAM_TOKEN` | Ponlas en `.env` (equipo) o en *Environment* (Render) |
| El bot responde «No autorizado. Tu chat es N» | Agrega N a `TELEGRAM_PERMITIDOS` y reinicia el bot (en Render, guarda la variable) |
| El bot responde «Algo falló…» | Mira la terminal o los *Logs* de Render: ahí está el error real (un `429` es cuota) |
| El bot de Render dejó de responder **después de probar en tu equipo** | Al arrancar, el *polling* local borra el webhook. En Render: **Manual Deploy → Restart service** |
| `Conflict: terminated by other getUpdates request` | Hay dos bots en *polling* con el mismo token: deja uno solo |
| El build de Render falla por `uv.lock` | Cambiaste dependencias sin `uv lock`: corre `uv lock`, commit y push |
| Más errores (async, MCP, grafos) | [`referencias/errores.md`](.agents/skills/asistente-pydantic-ai/referencias/errores.md) |

## Archivos

```
├── config.py           la configuración (.env o Render) y el modelo
├── capacidades.py      apis, consulta, registro y documentos  ← aquí van las tuyas
├── asistente.py        el agente y responder(mensaje)
├── bot.py              Telegram: /start, permitidos, polling o webhook
├── api.py              extra opcional: la API HTTP (ver API.md)
├── datos/              gastos.csv y documentos/*.pdf (ficticios)
├── tests/              pruebas sin modelo real
├── pyproject.toml      dependencias (uv.lock las fija)
├── .python-version     Python 3.14 (lo leen uv y Render)
├── .env.example        las variables, sin valores
├── render.yaml         atajo para Render (Blueprint)
├── TRABAJO_FINAL.md    qué se entrega y cómo se califica
├── API.md              extra opcional: el asistente como API
├── AGENTS.md, CLAUDE.md  instrucciones para asistentes de IA
└── .agents/skills/     el skill del curso
```

---

Autor: **Alex Ojeda Copa**. Código bajo licencia [MIT](LICENSE).

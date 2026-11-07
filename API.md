# Extra opcional: tu asistente como API

**No hace falta para el trabajo final.** Lo principal es el bot de Telegram del [README](README.md). Haz esto solo si quieres que, además, otros programas usen tu asistente: un script, otra app, n8n o una página con su propio servidor.

La API es el archivo `api.py`. Recibe un mensaje por HTTP y devuelve la respuesta del **mismo** `responder(mensaje)` que usa el bot. Si cambias una tool en `capacidades.py`, la toman los dos.

```
POST /chat   Authorization: Bearer <tu token>   {"mensaje": "¿Cuánto gasté en transporte?"}
         →   {"texto": "En transporte gastaste 67 bolivianos en total."}
```

## 1 · Crea tu token

Igual que el bot solo responde a los números de `TELEGRAM_PERMITIDOS`, la API solo responde a quien mande un token de `API_TOKENS`. Sin token, contesta `401` **sin llamar al modelo**, así que nadie gasta tu cuota. Si la lista está vacía, no entra nadie.

1. Genera un token:
   ```bash
   uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. Ponlo en `.env`:
   ```
   API_TOKENS=el-token-que-salió
   ```
   Para varias personas, genera un token para cada una y sepáralos con comas. Si uno se filtra, borras solo ese.

> **No reutilices el token de Telegram.** Ese token es la llave del bot: quien lo tenga puede leer sus mensajes y hacerse pasar por él. Cada cosa lleva su propia llave.

## 2 · Pruébala en tu equipo

```bash
uv run uvicorn api:app --reload
```

- Abre **http://127.0.0.1:8000/docs**: FastAPI arma una página para probarla. Pulsa **Authorize**, pega tu token y luego, en `POST /chat`, *Try it out*.
- O desde la terminal:
  ```bash
  curl -X POST http://127.0.0.1:8000/chat \
    -H "Authorization: Bearer el-token-que-salió" \
    -H "Content-Type: application/json" \
    -d '{"mensaje": "¿Cuánto gasté en transporte?"}'
  ```

| Respuesta | Qué significa |
|---|---|
| `200` y `{"texto": …}` | Funciona |
| `401 Token inválido` | Falta el token, está mal o `API_TOKENS` está vacío |
| `422` | El pedido no cumple el contrato: falta `mensaje`, está vacío o pasa de 2000 caracteres |
| `500` | Falló el modelo o una tool: el error está en la terminal (un `429` es cuota) |

## 3 · Publícala en Render

Es un **segundo servicio** del mismo repositorio. El servicio del bot no se toca.

1. En [dashboard.render.com](https://dashboard.render.com): **+ New → Web Service** y elige el mismo repositorio.
2. Completa los campos como los del bot, salvo el nombre y el **Start Command**:

| Campo | Valor |
|---|---|
| **Name** | `mi-asistente-ana-api`. Será parte de la URL |
| **Build Command** | `uv sync --locked --no-dev`, el mismo |
| **Start Command** | `uv run --no-sync uvicorn api:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | **Free** |

3. En **Environment Variables**:

| Key | Value |
|---|---|
| `GEMINI_API_KEY_LOCAL` | Tu clave de Gemini |
| `API_TOKENS` | Tu token o tus tokens |

4. Pulsa **Deploy Web Service** y pruébala como en el paso 2, con `https://mi-asistente-ana-api.onrender.com` en lugar de `http://127.0.0.1:8000`.

Cada `git push` vuelve a desplegar los dos servicios. Los límites del plan Free son los mismos que los del bot: se duerme a los 15 minutos, el disco es efímero y las 750 horas gratis al mes se reparten entre tus servicios (alcanzan, porque se duermen).

## Cuidado

- El token sirve cuando la API la llama **un programa**. Si haces una página web que llama a la API **desde el navegador**, cualquiera puede ver el token en las herramientas de desarrollo. Para eso hace falta un login o un servidor intermedio.
- Nunca escribas un token en el código ni lo subas a GitHub: va en `.env` y en *Environment*.
- `uv run pytest` incluye dos pruebas de la API: sin token válido no se llama al modelo, y con token responde.

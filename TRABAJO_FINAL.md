# Trabajo final

**Entrega: jueves 5 de noviembre de 2026.**

## Qué haces

1. **Haz funcionar el asistente de clase como bot de Telegram en Render**, con esta plantilla. Ya trae lo que vimos: APIs públicas, el contador de gastos en SQLite y la búsqueda en documentos con citas.
2. **Hazlo tuyo.** Ajusta a tus preferencias:
   - el tema y las instrucciones (para quién es y qué hace);
   - tus datos: otro CSV, otros PDFs;
   - una API nueva, otra tool u otra capability;
   - lo que vimos en las otras sesiones: búsqueda web (S2), un servidor MCP (S3), un flujo con un grafo (S4).

## Qué entregas (por el canal que indique el docente)

- [ ] El **usuario de tu bot** (`@…_bot`). Antes, pídele al docente su número de chat y agrégalo a `TELEGRAM_PERMITIDOS` en Render.
- [ ] El **enlace a tu repositorio**. Puede ser privado si compartes el acceso con el docente. En su README escribe tres o cuatro líneas: qué cambiaste o agregaste y dos o tres preguntas para probarlo.

## Cómo se califica

**Solo el funcionamiento.** 

1. responde en Telegram desde Render;
2. devuelve respuestas adecuadas
3. lo personalizaste

## Antes de entregar

- [ ] El bot responde **hoy** en Render. Si se durmió, el primer mensaje tarda alrededor de un minuto, y eso es normal.
- [ ] Un chat que no está en la lista recibe «No autorizado».
- [ ] `uv run pytest` pasa.
- [ ] `.env` no está en el repositorio y `git grep -nE "AIza[0-9A-Za-z_-]{30}"` no encuentra nada.

## Si la nube falla

Si Render, Telegram o la cuota del modelo te bloquean, avisa **antes del 5 de noviembre**. Entrega una grabación corta de la pantalla con el bot funcionando en tu equipo (`uv run bot.py`) y el error que te dio la nube.

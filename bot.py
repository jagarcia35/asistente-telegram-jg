"""Tu asistente en Telegram.

En tu equipo:  uv run bot.py   (polling: el bot le pregunta a Telegram cada poco si hay mensajes)
En Render, el mismo archivo usa un webhook (Telegram avisa a tu URL cuando llega un mensaje):
se da cuenta solo porque Render define RENDER_EXTERNAL_URL.
"""

import hashlib
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from asistente import responder
from config import settings

TOKEN = settings.telegram_token.get_secret_value()


async def inicio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start: lo primero que manda Telegram. Dice el número de chat para añadirlo a la lista."""
    chat = str(update.effective_chat.id)
    if chat in settings.permitidos:
        await update.message.reply_text("¡Hola! Ya puedes escribirme.")
    else:
        await update.message.reply_text(f"Tu número de chat es {chat}. Pídele al dueño del bot que lo añada.")


async def mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = str(update.effective_chat.id)
    if chat not in settings.permitidos:  # se rechaza ANTES de llamar al modelo (y de gastar tu cuota)
        print(f"Chat no autorizado: {chat}", flush=True)
        await update.message.reply_text(f"No autorizado. Tu chat es {chat}: pídele al dueño que lo añada.")
        return
    try:
        respuesta = await responder(update.message.text)
    except Exception as error:  # cuota agotada (429), una API caída…: se avisa en vez de quedarse callado
        print("Error:", repr(error)[:300], flush=True)  # el detalle, en la terminal o en los Logs de Render
        respuesta = "Algo falló (el modelo o una herramienta). Intenta de nuevo en un minuto."
    await update.message.reply_text(respuesta[:4000])  # Telegram no acepta más de 4096 caracteres


def main() -> None:
    if not TOKEN:
        raise SystemExit("Falta TELEGRAM_TOKEN: créalo con @BotFather y ponlo en .env (o en Environment, en Render).")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", inicio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensaje))

    permitidos = sorted(settings.permitidos) or "nadie"
    url = os.getenv("RENDER_EXTERNAL_URL")  # solo existe en Render
    if url:
        print(f"Webhook en {url}/telegram · permitidos: {permitidos}", flush=True)
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.getenv("PORT", "10000")),  # Render dice en qué puerto escuchar
            url_path="telegram",
            webhook_url=f"{url}/telegram",
            # Telegram manda este secreto en cada aviso: así nadie más puede hacerse pasar por Telegram.
            # Sale de tu token, que solo tú tienes.
            secret_token=hashlib.sha256(TOKEN.encode()).hexdigest()[:32],
        )
    else:
        print(f"Bot en marcha (polling) · permitidos: {permitidos}. Ctrl+C para parar.", flush=True)
        app.run_polling()  # ojo: esto BORRA el webhook de Render (ver README, «Problemas frecuentes»)


if __name__ == "__main__":
    main()

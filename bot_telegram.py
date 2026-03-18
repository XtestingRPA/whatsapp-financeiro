from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from telegram_bridge import TelegramFinanceBridge


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_CHAT_IDS_RAW = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").strip()

bridge = TelegramFinanceBridge()


def get_allowed_chat_ids() -> set[int]:
    if not ALLOWED_CHAT_IDS_RAW:
        return set()

    result: set[int] = set()
    for item in ALLOWED_CHAT_IDS_RAW.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            result.add(int(item))
        except ValueError:
            logger.warning("Chat ID inválido ignorado: %s", item)
    return result


ALLOWED_CHAT_IDS = get_allowed_chat_ids()


def is_chat_allowed(chat_id: int) -> bool:
    if not ALLOWED_CHAT_IDS:
        return True
    return chat_id in ALLOWED_CHAT_IDS


async def send_bridge_response(update: Update, context: ContextTypes.DEFAULT_TYPE, response) -> None:
    if update.effective_chat is None:
        return

    chat_id = update.effective_chat.id

    if response.text:
        await context.bot.send_message(chat_id=chat_id, text=response.text)

    for file_path in response.file_paths:
        if not file_path.exists():
            await context.bot.send_message(chat_id=chat_id, text="Arquivo gerado não encontrado para envio.")
            continue

        with file_path.open("rb") as f:
            await context.bot.send_document(chat_id=chat_id, document=f)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return

    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    response = bridge.handle_text("/start", chat_id=chat_id)
    await send_bridge_response(update, context, response)


async def ajuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return

    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    response = bridge.handle_text("/ajuda", chat_id=chat_id)
    await send_bridge_response(update, context, response)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None or update.effective_message is None:
        return

    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    text = update.effective_message.text or ""
    if not text.strip():
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        response = bridge.handle_text(text, chat_id=chat_id)
        await send_bridge_response(update, context, response)
    except Exception as exc:
        logger.exception("Erro ao processar mensagem do Telegram")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Erro interno ao processar a mensagem: {exc}"
        )


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "Defina a variável de ambiente TELEGRAM_BOT_TOKEN antes de executar o bot."
        )

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ajuda", ajuda_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    logger.info("Bot do Telegram iniciado em long polling.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
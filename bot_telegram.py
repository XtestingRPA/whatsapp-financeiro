from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
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


def build_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📊 Resumo mês", callback_data="quick:resumo_mes"),
            InlineKeyboardButton("📁 Últimos", callback_data="quick:listar_ultimos"),
        ],
        [
            InlineKeyboardButton("🏷️ Categorias", callback_data="quick:listar_categorias"),
            InlineKeyboardButton("📑 Relatório mês", callback_data="quick:relatorio_mes"),
        ],
        [
            InlineKeyboardButton("📤 Resumo PDF", callback_data="quick:exportar_resumo_pdf"),
            InlineKeyboardButton("📘 Ajuda", callback_data="quick:ajuda"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def send_core_response(chat_id: int, context: ContextTypes.DEFAULT_TYPE, response) -> None:
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
    await send_core_response(chat_id, context, response)

    await context.bot.send_message(
        chat_id=chat_id,
        text="Escolha uma ação rápida:",
        reply_markup=build_main_menu(),
    )


async def ajuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return

    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    response = bridge.handle_text("ajuda", chat_id=chat_id)
    await send_core_response(chat_id, context, response)


async def comandos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return

    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    text = (
        "🤖 Comandos principais do bot\n\n"
        "/start - iniciar bot\n"
        "/ajuda - ajuda geral\n"
        "/comandos - lista de comandos\n"
        "/resumo - resumo do mês atual\n"
        "/ultimos - listar últimos lançamentos\n"
        "/categorias - listar categorias\n"
        "/relatorio - relatório do mês atual\n\n"
        "Você também pode mandar frases livres como:\n"
        "• Paguei 35 de gasolina hoje\n"
        "• Resumo março\n"
        "• Exportar resumo pdf\n"
        "• Relatorio últimos 30 dias"
    )
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=build_main_menu())


async def resumo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    response = bridge.handle_text("resumo este mês", chat_id=chat_id)
    await send_core_response(chat_id, context, response)


async def ultimos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    response = bridge.handle_text("listar ultimos", chat_id=chat_id)
    await send_core_response(chat_id, context, response)


async def categorias_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    response = bridge.handle_text("listar categorias", chat_id=chat_id)
    await send_core_response(chat_id, context, response)


async def relatorio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    response = bridge.handle_text("relatorio este mês", chat_id=chat_id)
    await send_core_response(chat_id, context, response)


async def quick_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.callback_query is None or update.effective_chat is None:
        return

    query = update.callback_query
    chat_id = update.effective_chat.id

    if not is_chat_allowed(chat_id):
        await query.answer()
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    data = query.data or ""
    await query.answer()

    mapping = {
        "quick:resumo_mes": "resumo este mês",
        "quick:listar_ultimos": "listar ultimos",
        "quick:listar_categorias": "listar categorias",
        "quick:relatorio_mes": "relatorio este mês",
        "quick:exportar_resumo_pdf": "exportar resumo pdf",
        "quick:ajuda": "ajuda",
    }

    text = mapping.get(data)
    if not text:
        await context.bot.send_message(chat_id=chat_id, text="Ação rápida não reconhecida.")
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    response = bridge.handle_text(text, chat_id=chat_id)
    await send_core_response(chat_id, context, response)


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
        await send_core_response(chat_id, context, response)
    except Exception as exc:
        logger.exception("Erro ao processar mensagem do Telegram")
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Erro interno ao processar a mensagem: {exc}"
        )


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Defina TELEGRAM_BOT_TOKEN antes de executar o bot.")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("ajuda", ajuda_command))
    app.add_handler(CommandHandler("comandos", comandos_command))
    app.add_handler(CommandHandler("resumo", resumo_command))
    app.add_handler(CommandHandler("ultimos", ultimos_command))
    app.add_handler(CommandHandler("categorias", categorias_command))
    app.add_handler(CommandHandler("relatorio", relatorio_command))

    app.add_handler(CallbackQueryHandler(quick_action_handler, pattern=r"^quick:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    logger.info("Bot do Telegram iniciado em long polling.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
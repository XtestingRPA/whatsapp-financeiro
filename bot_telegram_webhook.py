from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
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
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").strip()
WEBHOOK_SECRET_PATH = os.getenv("WEBHOOK_SECRET_PATH", "telegram").strip()

bridge = TelegramFinanceBridge()
telegram_app: Application | None = None


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


# =========================================================
# MENUS
# =========================================================
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


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


def build_summary_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📤 PDF", callback_data="post:summary_pdf"),
            InlineKeyboardButton("📄 XML", callback_data="post:summary_xml"),
        ],
        [
            InlineKeyboardButton("📑 Relatório", callback_data="post:summary_to_report"),
            InlineKeyboardButton("📁 Últimos", callback_data="post:listar_ultimos"),
        ],
        [
            InlineKeyboardButton("🏷️ Categorias", callback_data="post:listar_categorias"),
            InlineKeyboardButton("📘 Ajuda", callback_data="post:ajuda"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_report_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📤 PDF", callback_data="post:report_pdf"),
            InlineKeyboardButton("📄 XML", callback_data="post:report_xml"),
        ],
        [
            InlineKeyboardButton("📊 Resumo mês", callback_data="post:resumo_mes"),
            InlineKeyboardButton("📁 Últimos", callback_data="post:listar_ultimos"),
        ],
        [
            InlineKeyboardButton("🏷️ Categorias", callback_data="post:listar_categorias"),
            InlineKeyboardButton("📘 Ajuda", callback_data="post:ajuda"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_list_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📊 Resumo mês", callback_data="post:resumo_mes"),
            InlineKeyboardButton("📑 Relatório mês", callback_data="post:relatorio_mes"),
        ],
        [
            InlineKeyboardButton("📤 Resumo PDF", callback_data="post:summary_pdf"),
            InlineKeyboardButton("🏷️ Categorias", callback_data="post:listar_categorias"),
        ],
        [
            InlineKeyboardButton("📘 Ajuda", callback_data="post:ajuda"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_categories_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("📊 Resumo mês", callback_data="post:resumo_mes"),
            InlineKeyboardButton("📁 Últimos", callback_data="post:listar_ultimos"),
        ],
        [
            InlineKeyboardButton("📘 Ajuda categorias", callback_data="post:ajuda_categorias"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_email_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("⚙️ Ver config email", callback_data="post:email_config"),
            InlineKeyboardButton("📘 Ajuda email", callback_data="post:ajuda_email"),
        ],
        [
            InlineKeyboardButton("📊 Resumo mês", callback_data="post:resumo_mes"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def choose_reply_markup(source_text: str, response_text: str) -> InlineKeyboardMarkup | None:
    src = (source_text or "").strip().lower()
    resp = (response_text or "").strip().lower()

    if src in {"/start", "/comandos", "/ajuda"}:
        return None

    if src.startswith("/resumo") or "resumo " in src or resp.startswith("📊 resumo".lower()):
        return build_summary_menu()

    if src.startswith("/relatorio") or src.startswith("/relatório") or "relatorio" in src or "relatório" in src or resp.startswith("📑 relatório".lower()):
        return build_report_menu()

    if src.startswith("/ultimos") or src.startswith("listar ") or src == "listar ultimos" or resp.startswith("📋 lançamentos".lower()) or resp.startswith("📁 últimos lançamentos".lower()):
        return build_list_menu()

    if src.startswith("/categorias") or src == "listar categorias" or resp.startswith("🏷️ categorias".lower()):
        return build_categories_menu()

    if "email" in src or "smtp" in resp:
        return build_email_menu()

    return None


async def send_core_response(chat_id: int, context: ContextTypes.DEFAULT_TYPE, response, source_text: str = "") -> None:
    reply_markup = choose_reply_markup(source_text, response.text)

    if response.text:
        await context.bot.send_message(chat_id=chat_id, text=response.text, reply_markup=reply_markup)

    for file_path in response.file_paths:
        if not file_path.exists():
            await context.bot.send_message(chat_id=chat_id, text="Arquivo gerado não encontrado para envio.")
            continue

        with file_path.open("rb") as f:
            await context.bot.send_document(chat_id=chat_id, document=f)


# =========================================================
# HANDLERS
# =========================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return

    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    response = bridge.handle_text("/start", chat_id=chat_id)
    await send_core_response(chat_id, context, response, source_text="/start")
    await context.bot.send_message(chat_id=chat_id, text="Escolha uma ação rápida:", reply_markup=build_main_menu())


async def ajuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    response = bridge.handle_text("ajuda", chat_id=chat_id)
    await send_core_response(chat_id, context, response, source_text="/ajuda")


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
        "/relatorio - relatório do mês atual\n"
        "/emailconfig - ver configuração de email\n"
        "/id - mostrar seu chat_id\n\n"
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

    source = "resumo este mês"
    response = bridge.handle_text(source, chat_id=chat_id)
    await send_core_response(chat_id, context, response, source_text=source)


async def ultimos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    source = "listar ultimos"
    response = bridge.handle_text(source, chat_id=chat_id)
    await send_core_response(chat_id, context, response, source_text=source)


async def categorias_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    source = "listar categorias"
    response = bridge.handle_text(source, chat_id=chat_id)
    await send_core_response(chat_id, context, response, source_text=source)


async def relatorio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    source = "relatorio este mês"
    response = bridge.handle_text(source, chat_id=chat_id)
    await send_core_response(chat_id, context, response, source_text=source)


async def emailconfig_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    if not is_chat_allowed(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="Acesso não autorizado.")
        return

    text = (
        "⚙️ Configuração de email\n\n"
        "Defina estas variáveis de ambiente:\n\n"
        "SMTP_HOST\nSMTP_PORT\nSMTP_USER\nSMTP_PASS\nSMTP_FROM\n\n"
        "Exemplo:\n"
        "SMTP_HOST=smtp.gmail.com\n"
        "SMTP_PORT=587\n"
        "SMTP_USER=seu_email@gmail.com\n"
        "SMTP_PASS=sua_app_password\n"
        "SMTP_FROM=seu_email@gmail.com\n\n"
        "Depois use:\n"
        "enviar resumo pdf para email@dominio.com"
    )
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=build_email_menu())


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=f"Seu chat_id: {chat_id}")


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
    await send_core_response(chat_id, context, response, source_text=text)


async def post_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        "post:summary_pdf": "exportar resumo pdf",
        "post:summary_xml": "exportar resumo xml",
        "post:report_pdf": "exportar relatorio pdf",
        "post:report_xml": "exportar relatorio xml",
        "post:summary_to_report": "relatorio este mês",
        "post:resumo_mes": "resumo este mês",
        "post:relatorio_mes": "relatorio este mês",
        "post:listar_ultimos": "listar ultimos",
        "post:listar_categorias": "listar categorias",
        "post:ajuda": "ajuda",
        "post:ajuda_categorias": "ajuda categorias",
        "post:ajuda_email": "ajuda email",
        "post:email_config": "__EMAIL_CONFIG__",
    }

    text = mapping.get(data)
    if not text:
        await context.bot.send_message(chat_id=chat_id, text="Ação não reconhecida.")
        return

    if text == "__EMAIL_CONFIG__":
        await emailconfig_command(update, context)
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    response = bridge.handle_text(text, chat_id=chat_id)
    await send_core_response(chat_id, context, response, source_text=text)


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
        await send_core_response(chat_id, context, response, source_text=text)
    except Exception as exc:
        logger.exception("Erro ao processar mensagem do Telegram")
        await context.bot.send_message(chat_id=chat_id, text=f"Erro interno ao processar a mensagem: {exc}")


# =========================================================
# FASTAPI + WEBHOOK
# =========================================================
def build_application() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Defina TELEGRAM_BOT_TOKEN antes de executar.")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("ajuda", ajuda_command))
    application.add_handler(CommandHandler("comandos", comandos_command))
    application.add_handler(CommandHandler("resumo", resumo_command))
    application.add_handler(CommandHandler("ultimos", ultimos_command))
    application.add_handler(CommandHandler("categorias", categorias_command))
    application.add_handler(CommandHandler("relatorio", relatorio_command))
    application.add_handler(CommandHandler("emailconfig", emailconfig_command))
    application.add_handler(CommandHandler("id", id_command))

    application.add_handler(CallbackQueryHandler(quick_action_handler, pattern=r"^quick:"))
    application.add_handler(CallbackQueryHandler(post_action_handler, pattern=r"^post:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    return application


@asynccontextmanager
async def lifespan(app: FastAPI):
    global telegram_app

    telegram_app = build_application()
    await telegram_app.initialize()
    await telegram_app.start()

    if not RENDER_EXTERNAL_URL:
        raise RuntimeError("Defina RENDER_EXTERNAL_URL com a URL pública do Render.")

    webhook_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/webhook/{WEBHOOK_SECRET_PATH}"
    await telegram_app.bot.set_webhook(url=webhook_url)
    logger.info("Webhook configurado em %s", webhook_url)

    yield

    if telegram_app:
        await telegram_app.bot.delete_webhook(drop_pending_updates=False)
        await telegram_app.stop()
        await telegram_app.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def healthcheck():
    return {"status": "ok", "service": "telegram-bot-webhook"}


@app.post("/webhook/{secret_path}")
async def telegram_webhook(secret_path: str, request: Request):
    if secret_path != WEBHOOK_SECRET_PATH:
        return Response(status_code=403)

    if telegram_app is None:
        return Response(status_code=503)

    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return Response(status_code=200)
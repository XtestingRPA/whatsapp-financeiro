from __future__ import annotations

from finance_core import FinanceCore, CoreResponse, UserContext


class TelegramFinanceBridge:
    def __init__(self) -> None:
        self.core = FinanceCore()

    def build_user_context(self, chat_id: int | None = None) -> UserContext:
        chat = str(chat_id) if chat_id is not None else "telegram_default_chat"
        return UserContext(
            canal="telegram",
            usuario_id=chat,
            chat_id=chat,
        )

    def handle_text(self, text: str, chat_id: int | None = None) -> CoreResponse:
        user = self.build_user_context(chat_id)
        normalized = text.strip().lower()

        if normalized in {"/start", "start"}:
            return CoreResponse(
                text=(
                    "💰 FinancesXTG iniciado no Telegram.\n\n"
                    "Seus dados ficam separados por chat.\n\n"
                    "Exemplos:\n"
                    "• Paguei 35 de gasolina hoje\n"
                    "• Resumo março\n"
                    "• Listar transferencias\n"
                    "• Relatorio últimos 30 dias\n"
                    "• Exportar resumo pdf\n"
                    "• Ajuda\n"
                )
            )

        if normalized in {"/ajuda", "ajuda"}:
            return self.core.process_message("ajuda", user=user)

        return self.core.process_message(text, user=user)
from __future__ import annotations

from finance_core import FinanceCore, CoreResponse


class TelegramFinanceBridge:
    def __init__(self) -> None:
        self.core = FinanceCore()

    def handle_text(self, text: str, chat_id: int | None = None) -> CoreResponse:
        normalized = text.strip().lower()

        if normalized in {"/start", "start"}:
            return CoreResponse(
                text=(
                    "💰 WhatsApp Financeiro no Telegram iniciado.\n\n"
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
            return self.core.process_message("ajuda")

        return self.core.process_message(text)
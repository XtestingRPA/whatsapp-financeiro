from __future__ import annotations

import os
import base64
from pathlib import Path

import resend


class ResendEmailProvider:
    def __init__(self) -> None:
        self.api_key = os.getenv("RESEND_API_KEY", "").strip()
        self.from_email = os.getenv("RESEND_FROM_EMAIL", "").strip()

        if not self.api_key:
            raise RuntimeError("RESEND_API_KEY não configurada.")

        if not self.from_email:
            raise RuntimeError("RESEND_FROM_EMAIL não configurado.")

        resend.api_key = self.api_key

    def send_email_with_attachment(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        attachment_path: str | Path,
    ) -> dict:
        attachment_path = Path(attachment_path)

        if not attachment_path.exists():
            raise RuntimeError(f"Arquivo não encontrado: {attachment_path.name}")

        with attachment_path.open("rb") as f:
            raw_bytes = f.read()

        encoded_content = base64.b64encode(raw_bytes).decode("utf-8")

        params: resend.Emails.SendParams = {
            "from": self.from_email,
            "to": [to_email],
            "subject": subject,
            "text": body_text,
            "attachments": [
                {
                    "filename": attachment_path.name,
                    "content": encoded_content,
                }
            ],
        }

        return resend.Emails.send(params)
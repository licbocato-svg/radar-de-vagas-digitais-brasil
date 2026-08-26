"""Configuração carregada de variáveis de ambiente, sem segredos no código."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Configurações do processo e do Telegram."""

    data_dir: Path = Path("data")
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_thread_id: str | None = None
    timezone: str = "America/Sao_Paulo"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        """Cria as configurações sem exibir ou validar valores secretos."""

        return cls(
            data_dir=Path(os.getenv("RADAR_DATA_DIR", "data")),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID") or None,
            telegram_thread_id=os.getenv("TELEGRAM_THREAD_ID") or None,
            timezone=os.getenv("RADAR_TIMEZONE", "America/Sao_Paulo"),
            log_level=os.getenv("RADAR_LOG_LEVEL", "INFO").upper(),
        )

    def require_telegram(self) -> tuple[str, str, int | None]:
        """Valida e converte a configuração necessária para o Telegram."""

        missing = [
            name
            for name, value in (
                ("TELEGRAM_BOT_TOKEN", self.telegram_bot_token),
                ("TELEGRAM_CHAT_ID", self.telegram_chat_id),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                "Telegram não configurado. Secret(s) ausente(s): "
                + ", ".join(missing)
            )

        thread_id: int | None = None
        if self.telegram_thread_id:
            try:
                thread_id = int(self.telegram_thread_id)
            except ValueError as error:
                raise RuntimeError(
                    "TELEGRAM_THREAD_ID deve ser um número inteiro."
                ) from error
            if thread_id <= 0:
                raise RuntimeError("TELEGRAM_THREAD_ID deve ser maior que zero.")

        return self.telegram_bot_token, self.telegram_chat_id, thread_id
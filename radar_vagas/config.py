"""Configuração carregada de variáveis de ambiente, sem segredos no código."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Configurações do processo e pontos reservados para o Telegram."""

    data_dir: Path = Path("data")
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    timezone: str = "America/Sao_Paulo"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        """Cria as configurações sem exibir ou validar valores secretos."""

        return cls(
            data_dir=Path(os.getenv("RADAR_DATA_DIR", "data")),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID") or None,
            timezone=os.getenv("RADAR_TIMEZONE", "America/Sao_Paulo"),
            log_level=os.getenv("RADAR_LOG_LEVEL", "INFO").upper(),
        )

    def require_telegram(self) -> tuple[str, str]:
        """Valida a configuração quando o publicador do Telegram for ativado."""

        if not self.telegram_bot_token or not self.telegram_chat_id:
            raise RuntimeError(
                "Telegram não configurado: defina TELEGRAM_BOT_TOKEN e "
                "TELEGRAM_CHAT_ID por meio dos segredos do ambiente."
            )
        return self.telegram_bot_token, self.telegram_chat_id
"""Cliente mínimo da API oficial do Telegram e formatação de mensagens."""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol

from radar_vagas.config import Settings
from radar_vagas.core.models import JobOpportunity
from radar_vagas.core.roles import matched_roles


@dataclass(frozen=True, slots=True)
class TelegramConfig:
    """Valores já validados, lidos dos Secrets pelo processo."""

    bot_token: str
    chat_id: str
    thread_id: int | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> "TelegramConfig":
        token, chat_id, thread_id = settings.require_telegram()
        return cls(token, chat_id, thread_id)


class TelegramApiError(RuntimeError):
    """Erro sanitizado da API, sem incluir token ou URL autenticada."""


class TelegramPublisher(Protocol):
    """Interface para publicar uma oportunidade no Telegram."""

    async def publish(self, job: JobOpportunity) -> None:
        """Publica uma oportunidade já filtrada."""
        ...


class TelegramBotClient:
    """Cliente sem dependências externas para os métodos usados pelo Radar."""

    api_base_url = "https://api.telegram.org"

    def __init__(
        self,
        config: TelegramConfig,
        *,
        timeout_seconds: float = 15.0,
        urlopen: Callable[..., Any] = urllib.request.urlopen,
    ) -> None:
        self.config = config
        self.timeout_seconds = timeout_seconds
        self._urlopen = urlopen

    async def get_me(self) -> Mapping[str, Any]:
        """Verifica o token com getMe; não envia mensagem."""

        return await asyncio.to_thread(self._request, "getMe", {})

    async def send_message(self, text: str) -> Mapping[str, Any]:
        """Envia texto somente quando chamado explicitamente pelo operador."""

        payload: dict[str, str | int | bool] = {
            "chat_id": self.config.chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        if self.config.thread_id is not None:
            payload["message_thread_id"] = self.config.thread_id
        return await asyncio.to_thread(self._request, "sendMessage", payload)

    async def publish(self, job: JobOpportunity) -> None:
        """Implementa o contrato de publicação futura de vagas."""

        await self.send_message(format_job_message(job))

    def _request(
        self, method: str, payload: Mapping[str, str | int | bool]
    ) -> Mapping[str, Any]:
        endpoint = f"{self.api_base_url}/bot{self.config.bot_token}/{method}"
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8") if payload else None,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with self._urlopen(request, timeout=self.timeout_seconds) as response:
                raw_body = response.read()
        except urllib.error.HTTPError as error:
            raise TelegramApiError(
                f"Telegram respondeu com HTTP {error.code}."
            ) from error
        except urllib.error.URLError as error:
            raise TelegramApiError(
                "Não foi possível alcançar a API oficial do Telegram."
            ) from error

        try:
            body = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise TelegramApiError("A resposta do Telegram não é um JSON válido.") from error

        if not isinstance(body, dict) or body.get("ok") is not True:
            description = body.get("description") if isinstance(body, dict) else None
            detail = f" Detalhe: {description}" if description else ""
            raise TelegramApiError(f"A API do Telegram rejeitou a operação.{detail}")

        result = body.get("result")
        return result if isinstance(result, dict) else {}


def format_job_message(job: JobOpportunity) -> str:
    """Formata uma vaga para envio, sem fazer qualquer chamada externa."""

    roles = ", ".join(matched_roles(job)) or "Vaga digital"
    lines = [f"{job.title} — {roles}"]
    if job.company:
        lines.append(f"Empresa: {job.company}")
    if job.location_text:
        lines.append(f"Localização: {job.location_text}")
    lines.append(f"Fonte: {job.source}")
    lines.append(job.url)
    return "\n".join(lines)


TEST_MESSAGE = (
    "Radar de Vagas Digitais Brasil: mensagem de teste enviada com sucesso. "
    "Nenhuma vaga foi publicada."
)
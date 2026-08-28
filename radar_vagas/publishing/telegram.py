"""Cliente da API oficial do Telegram."""

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
    chat_id: str | None = None
    thread_id: int | None = None

    @classmethod
    def from_settings(
        cls,
        settings: Settings,
    ) -> "TelegramConfig":
        token, chat_id, thread_id = settings.require_telegram()
        return cls(token, chat_id, thread_id)


class TelegramApiError(RuntimeError):
    """Erro sanitizado da API do Telegram."""


class TelegramPublisher(Protocol):

    async def publish(
        self,
        job: JobOpportunity,
    ) -> None:
        ...


class TelegramBotClient:
    """Cliente sem dependências externas para a API do Telegram."""

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

    async def get_me(
        self,
    ) -> Mapping[str, Any]:

        result = await asyncio.to_thread(
            self._request,
            "getMe",
            {},
        )

        if not isinstance(result, dict):
            raise TelegramApiError(
                "A resposta de getMe não contém um objeto válido."
            )

        return result

    async def get_updates(
        self,
        *,
        offset: int | None = None,
        poll_timeout_seconds: int = 0,
    ) -> tuple[Mapping[str, Any], ...]:
        """Obtém mensagens e eventos de entrada de membros."""

        payload: dict[str, Any] = {
            "timeout": max(
                0,
                poll_timeout_seconds,
            ),
            "allowed_updates": [
                "message",
                "chat_member",
            ],
        }

        if offset is not None:
            payload["offset"] = offset

        result = await asyncio.to_thread(
            self._request,
            "getUpdates",
            payload,
            max_http_timeout_seconds=max(
                15.0,
                poll_timeout_seconds + 5,
            ),
        )

        if not isinstance(result, list):
            raise TelegramApiError(
                "A resposta de getUpdates não contém uma lista válida."
            )

        return tuple(
            item
            for item in result
            if isinstance(item, dict)
        )

    async def send_message(
        self,
        text: str,
    ) -> Mapping[str, Any]:

        return await self._send_message(
            text=text,
        )

    async def send_message_with_buttons(
        self,
        text: str,
        buttons: list[list[dict[str, str]]],
    ) -> Mapping[str, Any]:

        return await self._send_message(
            text=text,
            reply_markup={
                "inline_keyboard": buttons,
            },
        )

    async def _send_message(
        self,
        *,
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> Mapping[str, Any]:

        if not self.config.chat_id:
            raise TelegramApiError(
                "TELEGRAM_CHAT_ID ainda não foi configurado."
            )

        payload: dict[str, Any] = {
            "chat_id": self.config.chat_id,
            "text": text,

            # Permite usar *texto* para negrito
            # nas mensagens enviadas ao Telegram.
            "parse_mode": "Markdown",

            "disable_web_page_preview": True,
        }

        if self.config.thread_id is not None:
            payload["message_thread_id"] = (
                self.config.thread_id
            )

        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        result = await asyncio.to_thread(
            self._request,
            "sendMessage",
            payload,
        )

        if not isinstance(result, dict):
            raise TelegramApiError(
                "A resposta de sendMessage não contém um objeto válido."
            )

        return result

    async def publish(
        self,
        job: JobOpportunity,
    ) -> None:

        await self.send_message(
            format_job_message(job)
        )

    def _request(
        self,
        method: str,
        payload: Mapping[str, Any],
        *,
        max_http_timeout_seconds: float | None = None,
    ) -> Any:

        endpoint = (
            f"{self.api_base_url}"
            f"/bot{self.config.bot_token}"
            f"/{method}"
        )

        request = urllib.request.Request(
            endpoint,
            data=(
                json.dumps(payload)
                .encode("utf-8")
                if payload
                else None
            ),
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        try:

            with self._urlopen(
                request,
                timeout=(
                    max_http_timeout_seconds
                    or self.timeout_seconds
                ),
            ) as response:

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

            body = json.loads(
                raw_body.decode("utf-8")
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as error:

            raise TelegramApiError(
                "A resposta do Telegram não é um JSON válido."
            ) from error

        if (
            not isinstance(body, dict)
            or body.get("ok") is not True
        ):

            description = (
                body.get("description")
                if isinstance(body, dict)
                else None
            )

            detail = (
                f" Detalhe: {description}"
                if description
                else ""
            )

            raise TelegramApiError(
                "A API do Telegram rejeitou a operação."
                + detail
            )

        return body.get("result")

    async def discover_forum_topic(
        self,
        *,
        topic_name: str = "Vagas & Oportunidades",
        wait_seconds: int = 120,
        poll_timeout_seconds: int = 30,
    ) -> "TopicDestination | None":

        pending = await self.get_updates(
            poll_timeout_seconds=0
        )

        offset = _next_offset(
            pending
        )

        loop = asyncio.get_running_loop()

        deadline = (
            loop.time()
            + max(
                1,
                wait_seconds,
            )
        )

        while loop.time() < deadline:

            remaining = max(
                1,
                int(
                    deadline
                    - loop.time()
                ),
            )

            updates = await self.get_updates(
                offset=offset,
                poll_timeout_seconds=min(
                    poll_timeout_seconds,
                    remaining,
                ),
            )

            offset = _next_offset(
                updates,
                fallback=offset,
            )

            for update in updates:

                destination = (
                    _destination_from_update(
                        update,
                        topic_name,
                    )
                )

                if destination is not None:
                    return destination

        return None


@dataclass(frozen=True, slots=True)
class TopicDestination:
    chat_id: str
    message_thread_id: int
    topic_name: str


def _next_offset(
    updates: tuple[
        Mapping[str, Any],
        ...,
    ],
    *,
    fallback: int | None = None,
) -> int | None:

    update_ids = [
        int(update["update_id"])
        for update in updates
        if isinstance(
            update.get("update_id"),
            int,
        )
    ]

    return max(
        update_ids,
        default=(
            fallback - 1
            if fallback is not None
            else -1
        ),
    ) + 1


def _destination_from_update(
    update: Mapping[str, Any],
    expected_topic_name: str,
) -> TopicDestination | None:

    message = update.get(
        "message"
    )

    if not isinstance(
        message,
        dict,
    ):
        return None

    thread_id = message.get(
        "message_thread_id"
    )

    chat = message.get(
        "chat"
    )

    if not isinstance(
        thread_id,
        int,
    ):
        return None

    if not isinstance(
        chat,
        dict,
    ):
        return None

    chat_id = chat.get(
        "id"
    )

    if not isinstance(
        chat_id,
        (int, str),
    ):
        return None

    created_topic = message.get(
        "forum_topic_created"
    )

    api_topic_name = (
        created_topic.get("name")
        if (
            isinstance(
                created_topic,
                dict,
            )
            and isinstance(
                created_topic.get("name"),
                str,
            )
        )
        else None
    )

    if (
        api_topic_name
        and api_topic_name.casefold()
        != expected_topic_name.casefold()
    ):
        return None

    return TopicDestination(
        chat_id=str(chat_id),
        message_thread_id=thread_id,
        topic_name=(
            api_topic_name
            or expected_topic_name
        ),
    )


def format_job_message(
    job: JobOpportunity,
) -> str:

    roles = (
        ", ".join(
            matched_roles(job)
        )
        or "Vaga digital"
    )

    lines = [
        f"{job.title} — {roles}"
    ]

    if job.company:
        lines.append(
            f"Empresa: {job.company}"
        )

    if job.location_text:
        lines.append(
            f"Localização: {job.location_text}"
        )

    lines.append(
        f"Fonte: {job.source}"
    )

    lines.append(
        job.url
    )

    return "\n".join(
        lines
    )


TEST_MESSAGE = (
    "Radar de Vagas Digitais Brasil: "
    "mensagem de teste enviada com sucesso. "
    "Nenhuma vaga foi publicada."
)

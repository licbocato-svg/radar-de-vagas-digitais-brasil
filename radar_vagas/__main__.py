"""CLI segura para validar a estrutura antes das integrações."""

from __future__ import annotations

import argparse
import asyncio

from radar_vagas.collectors.lever import LeverCollector
from radar_vagas.config import Settings
from radar_vagas.core.pipeline import JobPipeline
from radar_vagas.publishing.telegram import (
    TEST_MESSAGE,
    TelegramApiError,
    TelegramBotClient,
    TelegramConfig,
)
from radar_vagas.storage.seen_jobs import JsonSeenJobStore


async def _run() -> int:
    settings = Settings.from_env()
    store = JsonSeenJobStore(settings.data_dir / "seen_jobs.json")
    result = await JobPipeline(
    (LeverCollector(
        (
            "https://jobs.lever.co/scaleai",
            "https://jobs.lever.co/labelbox",
        )
    ),),
    store,
).run()
    print("Radar de Vagas Digitais Brasil")
    print(f"Vagas coletadas: {result.collected_count}")
    print(f"Correspondências de cargo: {result.role_matches_count}")
    print(f"Elegíveis para o Brasil: {result.brazil_eligible_count}")
    print(f"Vagas novas: {len(result.unique_jobs)}")
    print("Nenhuma plataforma externa está conectada nesta versão.")
    return 0


async def _check_telegram() -> int:
    try:
        client = TelegramBotClient(TelegramConfig.from_settings(Settings.from_env()))
        bot = await client.get_me()
    except (RuntimeError, TelegramApiError) as error:
        print(f"Falha na verificação do Telegram: {error}")
        return 1

    username = bot.get("username")
    if username:
        print(f"Conexão com o bot confirmada (@{username}).")
    else:
        print("Conexão com o bot confirmada.")
    print("Nenhuma mensagem foi enviada.")
    return 0


async def _send_telegram_test() -> int:
    try:
        client = TelegramBotClient(TelegramConfig.from_settings(Settings.from_env()))
        await client.get_me()
        await client.send_message(TEST_MESSAGE)
    except (RuntimeError, TelegramApiError) as error:
        print(f"Falha no teste do Telegram: {error}")
        return 1

    print("Mensagem de teste enviada ao destino configurado.")
    return 0


async def _discover_telegram_topic(topic_name: str, wait_seconds: int) -> int:
    try:
        client = TelegramBotClient(TelegramConfig.from_settings(Settings.from_env()))
        destination = await client.discover_forum_topic(
            topic_name=topic_name,
            wait_seconds=wait_seconds,
        )
    except (RuntimeError, TelegramApiError) as error:
        print(f"Falha na descoberta do tópico: {error}")
        return 1

    if destination is None:
        print(
            f"Nenhuma mensagem de tópico foi recebida nos últimos {wait_seconds} "
            "segundos."
        )
        return 1

    print("Destino descoberto a partir da mensagem recebida:")
    print(f"TELEGRAM_CHAT_ID={destination.chat_id}")
    print(f"TELEGRAM_THREAD_ID={destination.message_thread_id}")
    print(f"Tópico identificado: {destination.topic_name}")
    print("Nenhuma mensagem foi enviada.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Executa o pipeline inicial do Radar sem integrações externas."
    )
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "--check-telegram",
        action="store_true",
        help="valida o bot com getMe, sem enviar mensagens",
    )
    actions.add_argument(
        "--send-test",
        action="store_true",
        help="envia a mensagem de teste (exige --confirm-send-test)",
    )
    actions.add_argument(
        "--discover-telegram-topic",
        action="store_true",
        help="aguarda uma mensagem para descobrir chat_id e thread_id",
    )
    parser.add_argument(
        "--topic-name",
        default="Vagas & Oportunidades",
        help="nome esperado do tópico de fórum",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=120,
        help="tempo máximo de espera pela mensagem (padrão: 120)",
    )
    parser.add_argument(
        "--confirm-send-test",
        action="store_true",
        help="confirma explicitamente o envio da mensagem de teste",
    )
    arguments = parser.parse_args()
    if arguments.confirm_send_test and not arguments.send_test:
        parser.error("--confirm-send-test só pode ser usado com --send-test")
    if arguments.send_test and not arguments.confirm_send_test:
        parser.error("--send-test exige --confirm-send-test")
    if arguments.wait_seconds <= 0:
        parser.error("--wait-seconds deve ser maior que zero")
    if arguments.check_telegram:
        return asyncio.run(_check_telegram())
    if arguments.send_test:
        return asyncio.run(_send_telegram_test())
    if arguments.discover_telegram_topic:
        return asyncio.run(
            _discover_telegram_topic(arguments.topic_name, arguments.wait_seconds)
        )
    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())

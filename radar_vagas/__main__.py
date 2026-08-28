"""CLI do Radar de Vagas e do publicador de Materiais e Conteúdos."""

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


MATERIALS = {
    "home-office": [
        """💻 Quer começar a trabalhar de casa, mas ainda se sente perdida sobre por onde começar?

O Guia Home Office Internacional para Iniciantes foi criado para quem quer conhecer melhor as possibilidades de trabalho remoto e as oportunidades internacionais.

👉 Conheça o guia:
https://pay.kiwify.com.br/NVpp2kM""",

        """🌎 Trabalhar online para empresas internacionais pode parecer complicado no início.

Por isso, reunimos em um único guia informações para ajudar quem está dando os primeiros passos no universo do home office internacional.

📘 Conheça o Guia Home Office Internacional para Iniciantes:
https://pay.kiwify.com.br/NVpp2kM""",
    ],
    "formula-hol": [
        """🚀 Quer aprender um caminho mais completo para trabalhar de casa?

A Fórmula HOL é o treinamento para quem quer entender melhor as oportunidades de home office e construir uma nova possibilidade de renda trabalhando online.

👉 Conheça a Fórmula HOL:
https://lp.quebreiodespertador.com/formula-hol""",

        """💡 Muitas pessoas querem trabalhar de casa, mas não sabem quais caminhos seguir.

A Fórmula HOL reúne conhecimentos e estratégias para quem quer buscar oportunidades e desenvolver sua trajetória no home office.

🔗 Conheça o treinamento:
https://lp.quebreiodespertador.com/formula-hol""",
    ],
    "avaliador-mapas": [
        """🗺️ Você tem curiosidade sobre o trabalho de Avaliador de Mapas?

Essa é uma área que desperta muitas dúvidas: o que faz, onde encontrar oportunidades e como entender os processos.

📘 Para quem quer conhecer melhor esse universo:
https://pay.kiwify.com.br/5valD5Y""",

        """📍 Google Maps, localização e avaliação de resultados podem fazer parte de projetos de Avaliação de Mapas.

Se você quer entender melhor como funciona essa área, temos um material específico sobre o assunto.

👉 Conheça o Guia Avaliador de Mapas:
https://pay.kiwify.com.br/5valD5Y""",
    ],
    "avaliador-digital": [
        """🤖 O trabalho de Avaliador Digital tem despertado cada vez mais interesse entre quem busca oportunidades online.

Mas antes de procurar vagas, é importante entender como funciona esse universo.

📘 Conheça o Guia Completo de Formação de Avaliador Digital:
https://pay.kiwify.com.br/7JDByUZ""",

        """📱 Já ouviu falar em Avaliador Digital, mas ainda não sabe exatamente como essa área funciona?

Preparamos um guia para ajudar quem quer conhecer os conceitos, oportunidades e caminhos desse mercado.

👉 Conheça o Guia Avaliador Digital:
https://pay.kiwify.com.br/7JDByUZ""",
    ],
}


async def _run() -> int:
    settings = Settings.from_env()
    store = JsonSeenJobStore(settings.data_dir / "seen_jobs.json")

    result = await JobPipeline(
        (
            LeverCollector(
                (
                    "tryjeeves",
                    "weloglobal",
                )
            ),
        ),
        store,
    ).run()

    print("Radar de Vagas Digitais Brasil")
    print(f"Vagas coletadas: {result.collected_count}")
    print(f"Correspondências de cargo: {result.role_matches_count}")
    print(f"Elegíveis para o Brasil: {result.brazil_eligible_count}")
    print(f"Vagas novas: {len(result.unique_jobs)}")

    if not result.unique_jobs:
        print("Nenhuma vaga nova para publicar no Telegram.")
        return 0

    try:
        client = TelegramBotClient(TelegramConfig.from_settings(settings))
        await client.get_me()

        for job in result.unique_jobs:
            await client.publish(job)

    except (RuntimeError, TelegramApiError) as error:
        print(f"Falha ao publicar vagas no Telegram: {error}")
        return 1

    print(f"Vagas publicadas no Telegram: {len(result.unique_jobs)}")
    return 0


async def _check_telegram() -> int:
    try:
        client = TelegramBotClient(
            TelegramConfig.from_settings(Settings.from_env())
        )
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
        client = TelegramBotClient(
            TelegramConfig.from_settings(Settings.from_env())
        )
        await client.get_me()
        await client.send_message(TEST_MESSAGE)
    except (RuntimeError, TelegramApiError) as error:
        print(f"Falha no teste do Telegram: {error}")
        return 1

    print("Mensagem de teste enviada ao destino configurado.")
    return 0


async def _send_material(material: str, variation: int) -> int:
    messages = MATERIALS[material]
    message = messages[variation % len(messages)]

    try:
        client = TelegramBotClient(
            TelegramConfig.from_settings(Settings.from_env())
        )
        await client.get_me()
        await client.send_message(message)
    except (RuntimeError, TelegramApiError) as error:
        print(f"Falha ao publicar material no Telegram: {error}")
        return 1

    print(f"Material publicado com sucesso: {material}")
    return 0


async def _discover_telegram_topic(
    topic_name: str,
    wait_seconds: int,
) -> int:
    try:
        client = TelegramBotClient(
            TelegramConfig.from_settings(Settings.from_env())
        )
        destination = await client.discover_forum_topic(
            topic_name=topic_name,
            wait_seconds=wait_seconds,
        )
    except (RuntimeError, TelegramApiError) as error:
        print(f"Falha na descoberta do tópico: {error}")
        return 1

    if destination is None:
        print(
            f"Nenhuma mensagem de tópico foi recebida nos últimos "
            f"{wait_seconds} segundos."
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
        description="Executa o Radar de Vagas e o publicador de materiais."
    )

    actions = parser.add_mutually_exclusive_group()

    actions.add_argument(
        "--check-telegram",
        action="store_true",
        help="valida o bot sem enviar mensagens",
    )

    actions.add_argument(
        "--send-test",
        action="store_true",
        help="envia a mensagem de teste",
    )

    actions.add_argument(
        "--discover-telegram-topic",
        action="store_true",
        help="aguarda uma mensagem para descobrir chat_id e thread_id",
    )

    actions.add_argument(
        "--send-material",
        choices=MATERIALS.keys(),
        help="publica um dos materiais no Telegram",
    )

    parser.add_argument(
        "--variation",
        type=int,
        default=0,
        help="define a variação da mensagem do material",
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
        help="tempo máximo de espera pela mensagem",
    )

    parser.add_argument(
        "--confirm-send-test",
        action="store_true",
        help="confirma explicitamente o envio da mensagem de teste",
    )

    arguments = parser.parse_args()

    if arguments.confirm_send_test and not arguments.send_test:
        parser.error(
            "--confirm-send-test só pode ser usado com --send-test"
        )

    if arguments.send_test and not arguments.confirm_send_test:
        parser.error(
            "--send-test exige --confirm-send-test"
        )

    if arguments.wait_seconds <= 0:
        parser.error(
            "--wait-seconds deve ser maior que zero"
        )

    if arguments.check_telegram:
        return asyncio.run(_check_telegram())

    if arguments.send_test:
        return asyncio.run(_send_telegram_test())

    if arguments.discover_telegram_topic:
        return asyncio.run(
            _discover_telegram_topic(
                arguments.topic_name,
                arguments.wait_seconds,
            )
        )

    if arguments.send_material:
        return asyncio.run(
            _send_material(
                arguments.send_material,
                arguments.variation,
            )
        )

    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())

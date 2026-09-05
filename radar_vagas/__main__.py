"""CLI do Radar de Vagas e do publicador de Materiais e Conteúdos."""

from __future__ import annotations

import argparse
import asyncio
from html import escape

from radar_vagas.collectors.greenhouse import GreenhouseCollector
from radar_vagas.collectors.lever import LeverCollector
from radar_vagas.config import Settings
from radar_vagas.core.models import JobOpportunity
from radar_vagas.core.pipeline import JobPipeline
from radar_vagas.core.roles import matched_roles
from radar_vagas.publishing.telegram import (
    TEST_MESSAGE,
    TelegramApiError,
    TelegramBotClient,
    TelegramConfig,
)
from radar_vagas.storage.seen_jobs import (
    JsonSeenJobStore,
    job_fingerprint,
)


# ============================================================
# MATERIAIS
# ============================================================

MATERIALS = {
    "home-office": [
        """💻 Quer começar a trabalhar de casa, mas ainda se sente perdida sobre por onde começar?

O Guia Home Office Internacional para Iniciantes foi criado para quem quer conhecer melhor as possibilidades de trabalho remoto e as oportunidades internacionais.

👉 <b>CONHEÇA O GUIA:</b>""",

        """🌎 Trabalhar online para empresas internacionais pode parecer complicado no início.

Por isso, reunimos em um único guia informações para ajudar quem está dando os primeiros passos no universo do home office internacional.

📘 <b>CONHEÇA O GUIA HOME OFFICE INTERNACIONAL:</b>""",
    ],

    "formula-hol": [
        """🚀 Quer aprender um caminho mais completo para trabalhar de casa?

A Fórmula HOL é o treinamento para quem quer entender melhor as oportunidades de home office e construir uma nova possibilidade de renda trabalhando online.

👉 <b>CONHEÇA A FÓRMULA HOL:</b>""",

        """💡 Muitas pessoas querem trabalhar de casa, mas não sabem quais caminhos seguir.

A Fórmula HOL reúne conhecimentos e estratégias para quem quer buscar oportunidades e desenvolver sua trajetória no home office.

🔗 <b>CONHEÇA O TREINAMENTO:</b>""",
    ],

    "avaliador-mapas": [
        """🗺️ Você tem curiosidade sobre o trabalho de Avaliador de Mapas?

Essa é uma área que desperta muitas dúvidas: o que faz, onde encontrar oportunidades e como entender os processos.

📘 <b>CONHEÇA O GUIA:</b>""",

        """📍 Google Maps, localização e avaliação de resultados podem fazer parte de projetos de Avaliação de Mapas.

Se você quer entender melhor como funciona essa área, temos um material específico sobre o assunto.

👉 <b>CONHEÇA O GUIA AVALIADOR DE MAPAS:</b>""",
    ],

    "avaliador-digital": [
        """🤖 O trabalho de Avaliador Digital tem despertado cada vez mais interesse entre quem busca oportunidades online.

Mas antes de procurar vagas, é importante entender como funciona esse universo.

📘 <b>CONHEÇA O GUIA COMPLETO DE FORMAÇÃO DE AVALIADOR DIGITAL:</b>""",

        """📱 Já ouviu falar em Avaliador Digital, mas ainda não sabe exatamente como essa área funciona?

Preparamos um guia para ajudar quem quer conhecer os conceitos, oportunidades e caminhos desse mercado.

👉 <b>CONHEÇA O GUIA AVALIADOR DIGITAL:</b>""",
    ],
}


# ============================================================
# LINKS DOS MATERIAIS
# ============================================================

MATERIAL_URLS = {
    "home-office": "https://pay.kiwify.com.br/NVpp2kM",
    "formula-hol": "https://lp.quebreiodespertador.com/formula-hol",
    "avaliador-mapas": "https://pay.kiwify.com.br/5valD5Y",
    "avaliador-digital": "https://pay.kiwify.com.br/7JDByUZ",
}


# ============================================================
# FORMATAÇÃO DA VAGA
# ============================================================

def format_job_message_html(
    job: JobOpportunity,
) -> str:
    """Monta a mensagem da vaga usando HTML seguro."""

    title = escape(str(job.title))

    try:
        roles = ", ".join(
            str(role)
            for role in matched_roles(job)
        )
    except Exception:
        roles = ""

    if not roles:
        roles = "Vaga digital"

    roles = escape(roles)

    company = (
        escape(str(job.company))
        if job.company
        else None
    )

    location = (
        escape(str(job.location_text))
        if job.location_text
        else None
    )

    source = escape(str(job.source))

    lines = [
        f"<b>📢 {title}</b>",
        "",
        f"💼 <b>Área:</b> {roles}",
    ]

    if company:
        lines.append(
            f"🏢 <b>Empresa:</b> {company}"
        )

    if location:
        lines.append(
            f"📍 <b>Localização:</b> {location}"
        )

    lines.append(
        f"🔎 <b>Fonte:</b> {source}"
    )

    lines.append("")
    lines.append(
        "👇 <b>ACESSE A OPORTUNIDADE:</b>"
    )

    return "\n".join(lines)


# ============================================================
# RADAR DE VAGAS
# ============================================================

async def _run() -> int:

    settings = Settings.from_env()

    store = JsonSeenJobStore(
        settings.data_dir / "seen_jobs.json"
    )

    # ========================================================
    # COLETORES
    # ========================================================

    collectors = (
        # ----------------------------------------------------
        # LEVER
        # ----------------------------------------------------

        LeverCollector(
            (
                "tryjeeves",
                "weloglobal",
            )
        ),

        # ----------------------------------------------------
        # GREENHOUSE
        # ----------------------------------------------------

        GreenhouseCollector(
            (
                "appen",
                "telusinternational",
                "welocalize",
            )
        ),
    )

    print("=" * 60)
    print("RADAR DE VAGAS DIGITAIS BRASIL")
    print("=" * 60)
    print("Execução iniciada.")
    print()

    result = await JobPipeline(
        collectors,
        store,
    ).run()

    print(
        f"Vagas coletadas: "
        f"{result.collected_count}"
    )

    print(
        f"Correspondências de cargo: "
        f"{result.role_matches_count}"
    )

    print(
        f"Elegíveis para o Brasil: "
        f"{result.brazil_eligible_count}"
    )

    print(
        f"Vagas novas disponíveis: "
        f"{len(result.unique_jobs)}"
    )

    if not result.unique_jobs:

        print()
        print(
            "Nenhuma vaga nova para publicar "
            "no Telegram."
        )

        return 0

    # ========================================================
    # PUBLICA UMA VAGA POR EXECUÇÃO
    #
    # Como o GitHub Actions roda de hora em hora,
    # cada execução pode publicar uma vaga diferente.
    # ========================================================

    job = result.unique_jobs[0]

    print()
    print(
        "Vaga selecionada para esta execução:"
    )
    print(
        f"  {job.title}"
    )

    if job.company:
        print(
            f"  Empresa: {job.company}"
        )

    if job.location_text:
        print(
            f"  Localização: {job.location_text}"
        )

    print(
        f"  Fonte: {job.source}"
    )

    try:

        client = TelegramBotClient(
            TelegramConfig.from_settings(
                settings
            )
        )

        await client.get_me()

        message = format_job_message_html(
            job
        )

        buttons = [
            [
                {
                    "text": (
                        "🔎 VER VAGA E "
                        "SE CANDIDATAR"
                    ),
                    "url": str(job.url),
                }
            ]
        ]

        # ----------------------------------------------------
        # ENVIA A VAGA
        # ----------------------------------------------------

        await client.send_message_with_buttons(
            message,
            buttons,
            parse_mode="HTML",
        )

        # ----------------------------------------------------
        # SOMENTE DEPOIS DO ENVIO BEM-SUCEDIDO
        # REGISTRA A VAGA COMO PUBLICADA
        # ----------------------------------------------------

        fingerprint = job_fingerprint(job)

        store.remember_many(
            [fingerprint]
        )

        print()
        print(
            f"Vaga publicada com botão: "
            f"{job.title}"
        )

        print(
            "Vaga registrada no histórico "
            "de publicadas."
        )

    except (
        RuntimeError,
        TelegramApiError,
    ) as error:

        print(
            "Falha ao publicar vagas "
            f"no Telegram: {error}"
        )

        return 1

    print()
    print(
        "Vagas publicadas no Telegram: 1"
    )

    return 0


# ============================================================
# VERIFICAR TELEGRAM
# ============================================================

async def _check_telegram() -> int:

    try:

        client = TelegramBotClient(
            TelegramConfig.from_settings(
                Settings.from_env()
            )
        )

        bot = await client.get_me()

    except (
        RuntimeError,
        TelegramApiError,
    ) as error:

        print(
            f"Falha na verificação "
            f"do Telegram: {error}"
        )

        return 1

    username = bot.get("username")

    if username:

        print(
            f"Conexão com o bot confirmada "
            f"(@{username})."
        )

    else:

        print(
            "Conexão com o bot confirmada."
        )

    print(
        "Nenhuma mensagem foi enviada."
    )

    return 0


# ============================================================
# TESTE DO TELEGRAM
# ============================================================

async def _send_telegram_test() -> int:

    try:

        client = TelegramBotClient(
            TelegramConfig.from_settings(
                Settings.from_env()
            )
        )

        await client.get_me()

        await client.send_message(
            TEST_MESSAGE
        )

    except (
        RuntimeError,
        TelegramApiError,
    ) as error:

        print(
            f"Falha no teste do Telegram: "
            f"{error}"
        )

        return 1

    print(
        "Mensagem de teste enviada "
        "ao destino configurado."
    )

    return 0


# ============================================================
# PUBLICAR MATERIAL
# ============================================================

async def _send_material(
    material: str,
    variation: int,
) -> int:

    messages = MATERIALS[material]

    message = messages[
        variation % len(messages)
    ]

    url = MATERIAL_URLS[material]

    buttons = [
        [
            {
                "text": "🔗 ACESSAR MATERIAL",
                "url": url,
            }
        ]
    ]

    try:

        client = TelegramBotClient(
            TelegramConfig.from_settings(
                Settings.from_env()
            )
        )

        await client.get_me()

        await client.send_message_with_buttons(
            message,
            buttons,
            parse_mode="HTML",
        )

    except (
        RuntimeError,
        TelegramApiError,
    ) as error:

        print(
            "Falha ao publicar material "
            f"no Telegram: {error}"
        )

        return 1

    print(
        "Material publicado com sucesso: "
        f"{material}"
    )

    return 0


# ============================================================
# DESCOBRIR TÓPICO DO TELEGRAM
# ============================================================

async def _discover_telegram_topic(
    topic_name: str,
    wait_seconds: int,
) -> int:

    try:

        client = TelegramBotClient(
            TelegramConfig.from_settings(
                Settings.from_env()
            )
        )

        destination = (
            await client.discover_forum_topic(
                topic_name=topic_name,
                wait_seconds=wait_seconds,
            )
        )

    except (
        RuntimeError,
        TelegramApiError,
    ) as error:

        print(
            f"Falha na descoberta do tópico: "
            f"{error}"
        )

        return 1

    if destination is None:

        print(
            "Nenhuma mensagem de tópico "
            f"foi recebida nos últimos "
            f"{wait_seconds} segundos."
        )

        return 1

    print(
        "Destino descoberto a partir "
        "da mensagem recebida:"
    )

    print(
        f"TELEGRAM_CHAT_ID="
        f"{destination.chat_id}"
    )

    print(
        f"TELEGRAM_THREAD_ID="
        f"{destination.message_thread_id}"
    )

    print(
        f"Tópico identificado: "
        f"{destination.topic_name}"
    )

    print(
        "Nenhuma mensagem foi enviada."
    )

    return 0


# ============================================================
# CLI
# ============================================================

def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Executa o Radar de Vagas "
            "e o publicador de materiais."
        )
    )

    actions = (
        parser
        .add_mutually_exclusive_group()
    )

    actions.add_argument(
        "--check-telegram",
        action="store_true",
        help=(
            "valida o bot sem "
            "enviar mensagens"
        ),
    )

    actions.add_argument(
        "--send-test",
        action="store_true",
        help=(
            "envia a mensagem "
            "de teste"
        ),
    )

    actions.add_argument(
        "--discover-telegram-topic",
        action="store_true",
        help=(
            "aguarda uma mensagem "
            "para descobrir chat_id "
            "e thread_id"
        ),
    )

    actions.add_argument(
        "--send-material",
        choices=MATERIALS.keys(),
        help=(
            "publica um dos materiais "
            "no Telegram"
        ),
    )

    parser.add_argument(
        "--variation",
        type=int,
        default=0,
        help=(
            "define a variação da "
            "mensagem do material"
        ),
    )

    parser.add_argument(
        "--topic-name",
        default="Vagas & Oportunidades",
        help=(
            "nome esperado do tópico "
            "de fórum"
        ),
    )

    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=120,
        help=(
            "tempo máximo de espera "
            "pela mensagem"
        ),
    )

    parser.add_argument(
        "--confirm-send-test",
        action="store_true",
        help=(
            "confirma explicitamente "
            "o envio da mensagem de teste"
        ),
    )

    arguments = parser.parse_args()

    if (
        arguments.confirm_send_test
        and not arguments.send_test
    ):

        parser.error(
            "--confirm-send-test só pode "
            "ser usado com --send-test"
        )

    if (
        arguments.send_test
        and not arguments.confirm_send_test
    ):

        parser.error(
            "--send-test exige "
            "--confirm-send-test"
        )

    if arguments.wait_seconds <= 0:

        parser.error(
            "--wait-seconds deve ser "
            "maior que zero"
        )

    if arguments.check_telegram:

        return asyncio.run(
            _check_telegram()
        )

    if arguments.send_test:

        return asyncio.run(
            _send_telegram_test()
        )

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

    return asyncio.run(
        _run()
    )


# ============================================================
# INICIALIZAÇÃO
# ============================================================

if __name__ == "__main__":

    raise SystemExit(
        main()
    )

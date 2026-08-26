"""CLI segura para validar a estrutura antes das integrações."""

from __future__ import annotations

import argparse
import asyncio

from radar_vagas.collectors.empty import EmptyCollector
from radar_vagas.config import Settings
from radar_vagas.core.pipeline import JobPipeline
from radar_vagas.storage.seen_jobs import JsonSeenJobStore


async def _run() -> int:
    settings = Settings.from_env()
    store = JsonSeenJobStore(settings.data_dir / "seen_jobs.json")
    result = await JobPipeline((EmptyCollector(),), store).run()
    print("Radar de Vagas Digitais Brasil")
    print(f"Vagas coletadas: {result.collected_count}")
    print(f"Correspondências de cargo: {result.role_matches_count}")
    print(f"Elegíveis para o Brasil: {result.brazil_eligible_count}")
    print(f"Vagas novas: {len(result.unique_jobs)}")
    print("Nenhuma plataforma externa está conectada nesta versão.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Executa o pipeline inicial do Radar sem integrações externas."
    )
    parser.parse_args()
    return asyncio.run(_run())


if __name__ == "__main__":
    raise SystemExit(main())
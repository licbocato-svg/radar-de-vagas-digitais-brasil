"""Orquestração do fluxo de coleta, filtragem e deduplicação."""

from __future__ import annotations

from dataclasses import dataclass

from radar_vagas.collectors.base import JobCollector
from radar_vagas.core.eligibility import eligible_for_brazil
from radar_vagas.core.models import JobOpportunity
from radar_vagas.core.roles import matches_target_role
from radar_vagas.storage.seen_jobs import (
    SeenJobStore,
    job_fingerprint,
)


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Resumo verificável de uma execução do pipeline."""

    collected_count: int
    role_matches_count: int
    brazil_eligible_count: int
    unique_jobs: tuple[JobOpportunity, ...]


class JobPipeline:
    """Executa coletores e aplica regras comuns a todas as fontes."""

    def __init__(
        self,
        collectors: tuple[JobCollector, ...],
        seen_store: SeenJobStore,
    ) -> None:
        self.collectors = collectors
        self.seen_store = seen_store

    async def run(self) -> PipelineResult:

        collected: list[JobOpportunity] = []

        # ========================================================
        # 1. COLETA
        # ========================================================

        for collector in self.collectors:
            try:
                jobs = await collector.collect()

                print(
                    f"[COLETOR] {collector.name}: "
                    f"{len(jobs)} vagas coletadas"
                )

                collected.extend(jobs)

            except Exception as error:
                print(
                    f"[ERRO] Falha no coletor "
                    f"{collector.name}: {error}"
                )

        # ========================================================
        # 2. FILTRO POR CARGO
        # ========================================================

        role_matches = [
            job
            for job in collected
            if matches_target_role(job)
        ]

        # ========================================================
        # 3. FILTRO DE ELEGIBILIDADE PARA O BRASIL
        # ========================================================

        brazil_eligible = [
            job
            for job in role_matches
            if eligible_for_brazil(job)
        ]

        # ========================================================
        # 4. DEDUPLICAÇÃO
        # ========================================================

        unique_jobs: list[JobOpportunity] = []

        batch_fingerprints: set[str] = set()

        for job in brazil_eligible:

            fingerprint = job_fingerprint(job)

            # ----------------------------------------------------
            # DUPLICADA DENTRO DA MESMA EXECUÇÃO
            # ----------------------------------------------------

            if fingerprint in batch_fingerprints:

                print(
                    "[DUPLICADA NA EXECUÇÃO] "
                    f"{job.title} | "
                    f"{job.company}"
                )

                continue

            # ----------------------------------------------------
            # JÁ PUBLICADA EM EXECUÇÃO ANTERIOR
            # ----------------------------------------------------

            if self.seen_store.contains(fingerprint):

                print(
                    "[JÁ PUBLICADA] "
                    f"{job.title} | "
                    f"{job.company}"
                )

                print(
                    f"  URL: {job.url}"
                )

                print(
                    f"  Fonte: {job.source}"
                )

                print(
                    f"  ID: {job.external_id or 'sem ID'}"
                )

                continue

            # ----------------------------------------------------
            # NOVA VAGA
            # ----------------------------------------------------

            batch_fingerprints.add(fingerprint)

            unique_jobs.append(job)

            print(
                "[NOVA VAGA] "
                f"{job.title} | "
                f"{job.company}"
            )

            print(
                f"  URL: {job.url}"
            )

            print(
                f"  Fonte: {job.source}"
            )

            print(
                f"  ID: {job.external_id or 'sem ID'}"
            )

        # ========================================================
        # RESULTADO
        # ========================================================

        return PipelineResult(
            collected_count=len(collected),
            role_matches_count=len(role_matches),
            brazil_eligible_count=len(brazil_eligible),
            unique_jobs=tuple(unique_jobs),
        )

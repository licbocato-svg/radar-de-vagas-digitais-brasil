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
    legacy_job_fingerprint,
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

        for collector in self.collectors:
            try:
                jobs = await collector.collect()

                print(
                    f"[COLETOR] "
                    f"{getattr(collector, 'name', collector.__class__.__name__)}: "
                    f"{len(jobs)} vagas coletadas"
                )

                collected.extend(jobs)

            except Exception as error:
                print(
                    f"[ERRO COLETOR] "
                    f"{getattr(collector, 'name', collector.__class__.__name__)}: "
                    f"{error}"
                )

        role_matches = [
            job
            for job in collected
            if matches_target_role(job)
        ]

        brazil_eligible = [
            job
            for job in role_matches
            if eligible_for_brazil(job)
        ]

        unique_jobs: list[JobOpportunity] = []

        batch_fingerprints: set[str] = set()

        for job in brazil_eligible:

            current_fingerprint = job_fingerprint(job)
            legacy_fingerprint = legacy_job_fingerprint(job)

            # ====================================================
            # BLOQUEIA DUPLICAÇÃO NA MESMA EXECUÇÃO
            # ====================================================

            if (
                current_fingerprint in batch_fingerprints
                or legacy_fingerprint in batch_fingerprints
            ):
                continue

            # ====================================================
            # BLOQUEIA VAGA PUBLICADA NO HISTÓRICO ATUAL
            # ====================================================

            if self.seen_store.contains(
                current_fingerprint
            ):
                print(
                    f"[JÁ PUBLICADA] {job.title} | {job.company}"
                )
                print(f"  URL: {job.url}")
                print(f"  Fonte: {job.source}")
                print(
                    f"  ID: {job.external_id or 'sem ID'}"
                )
                continue

            # ====================================================
            # BLOQUEIA VAGA PUBLICADA COM O SISTEMA ANTIGO
            # ====================================================

            if self.seen_store.contains(
                legacy_fingerprint
            ):
                print(
                    f"[JÁ PUBLICADA - HISTÓRICO ANTIGO] "
                    f"{job.title} | {job.company}"
                )
                print(f"  URL: {job.url}")
                print(f"  Fonte: {job.source}")
                print(
                    f"  ID: {job.external_id or 'sem ID'}"
                )
                continue

            # ====================================================
            # NOVA VAGA
            # ====================================================

            print(
                f"[NOVA VAGA] {job.title} | {job.company}"
            )
            print(f"  URL: {job.url}")
            print(f"  Fonte: {job.source}")
            print(
                f"  ID: {job.external_id or 'sem ID'}"
            )

            batch_fingerprints.add(
                current_fingerprint
            )

            batch_fingerprints.add(
                legacy_fingerprint
            )

            unique_jobs.append(job)

        return PipelineResult(
            collected_count=len(collected),
            role_matches_count=len(role_matches),
            brazil_eligible_count=len(brazil_eligible),
            unique_jobs=tuple(unique_jobs),
        )

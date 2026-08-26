"""Orquestração do fluxo de coleta, filtragem e deduplicação."""

from __future__ import annotations

from dataclasses import dataclass

from radar_vagas.collectors.base import JobCollector
from radar_vagas.core.eligibility import eligible_for_brazil
from radar_vagas.core.models import JobOpportunity
from radar_vagas.core.roles import matches_target_role
from radar_vagas.storage.seen_jobs import SeenJobStore, job_fingerprint


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
            collected.extend(await collector.collect())

        role_matches = [job for job in collected if matches_target_role(job)]
        brazil_eligible = [job for job in role_matches if eligible_for_brazil(job)]

        unique_jobs: list[JobOpportunity] = []
        batch_fingerprints: set[str] = set()
        for job in brazil_eligible:
            fingerprint = job_fingerprint(job)
            if fingerprint in batch_fingerprints or self.seen_store.contains(fingerprint):
                continue
            batch_fingerprints.add(fingerprint)
            unique_jobs.append(job)

        self.seen_store.remember_many(batch_fingerprints)
        return PipelineResult(
            collected_count=len(collected),
            role_matches_count=len(role_matches),
            brazil_eligible_count=len(brazil_eligible),
            unique_jobs=tuple(unique_jobs),
        )
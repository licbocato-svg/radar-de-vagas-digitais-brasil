from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from radar_vagas.collectors.base import JobCollector
from radar_vagas.core.eligibility import eligible_for_brazil
from radar_vagas.core.models import JobOpportunity
from radar_vagas.core.pipeline import JobPipeline
from radar_vagas.core.roles import matched_roles, matches_target_role
from radar_vagas.storage.seen_jobs import JsonSeenJobStore


def make_job(**changes: object) -> JobOpportunity:
    values: dict[str, object] = {
        "source": "fonte-teste",
        "title": "Avaliador de Mapas",
        "url": "https://example.com/jobs/mapas",
        "company": "Empresa Teste",
        "location_text": "Brasil - remoto",
        "remote": True,
    }
    values.update(changes)
    return JobOpportunity(**values)


class SingleJobCollector(JobCollector):
    name = "test"

    def __init__(self, jobs: tuple[JobOpportunity, ...]) -> None:
        self.jobs = jobs

    async def collect(self) -> tuple[JobOpportunity, ...]:
        return self.jobs


class FilteringTests(unittest.TestCase):
    def test_matches_accented_portuguese_role(self) -> None:
        job = make_job(title="Avaliador de Mídias Sociais")
        self.assertTrue(matches_target_role(job))
        self.assertEqual(matched_roles(job), ("Avaliador de Mídias Sociais",))

    def test_matches_english_alias_in_description(self) -> None:
        job = make_job(title="Remote contractor", description="Search Quality Rater")
        self.assertTrue(matches_target_role(job))

    def test_rejects_unrelated_role(self) -> None:
        self.assertFalse(matches_target_role(make_job(title="Backend Developer")))

    def test_accepts_brazil_and_global_locations(self) -> None:
        self.assertTrue(eligible_for_brazil(make_job(location_text="São Paulo, Brasil")))
        self.assertTrue(eligible_for_brazil(make_job(location_text="Worldwide remote")))

    def test_rejects_unknown_and_excluded_locations(self) -> None:
        self.assertFalse(eligible_for_brazil(make_job(location_text="Remote")))
        self.assertFalse(eligible_for_brazil(make_job(location_text="US only")))

    def test_pipeline_returns_only_role_and_brazil_matches(self) -> None:
        jobs = (
            make_job(),
            make_job(
                title="Backend Developer",
                url="https://example.com/jobs/backend",
            ),
            make_job(
                title="Online Data Analyst",
                url="https://example.com/jobs/us",
                location_text="US only",
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            store = JsonSeenJobStore(Path(directory) / "seen.json")
            result = asyncio.run(
                JobPipeline((SingleJobCollector(jobs),), store).run()
            )

        self.assertEqual(result.collected_count, 3)
        self.assertEqual(result.role_matches_count, 2)
        self.assertEqual(result.brazil_eligible_count, 1)
        self.assertEqual(len(result.unique_jobs), 1)
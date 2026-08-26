from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from radar_vagas.core.models import JobOpportunity
from radar_vagas.storage.seen_jobs import (
    JsonSeenJobStore,
    canonicalize_url,
    job_fingerprint,
)


class DeduplicationTests(unittest.TestCase):
    def test_canonical_url_ignores_tracking_parameters(self) -> None:
        first = "https://example.com/vaga/?utm_source=newsletter"
        second = "https://EXAMPLE.COM/vaga"
        self.assertEqual(canonicalize_url(first), canonicalize_url(second))

    def test_store_persists_fingerprints_between_instances(self) -> None:
        job = JobOpportunity(
            source="fonte",
            title="Internet Assessor",
            url="https://example.com/job/1",
        )
        fingerprint = job_fingerprint(job)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "seen.json"
            JsonSeenJobStore(path).remember_many((fingerprint,))
            reloaded = JsonSeenJobStore(path)
            self.assertTrue(reloaded.contains(fingerprint))

    def test_content_fingerprint_is_available_without_url(self) -> None:
        job = JobOpportunity(
            source="fonte",
            title="Avaliador de IA",
            company="Empresa",
            location_text="Brasil",
            url="",
        )
        self.assertEqual(len(job_fingerprint(job)), 64)
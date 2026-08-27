"""Coletor de vagas públicas usando a API do Lever."""

from __future__ import annotations

from urllib.parse import quote
from urllib.request import urlopen
import json

from radar_vagas.collectors.base import JobCollector
from radar_vagas.core.models import JobOpportunity


class LeverCollector(JobCollector):
    """Coleta vagas públicas de empresas que utilizam o Lever."""

    def __init__(self, sites: tuple[str, ...]) -> None:
        self.sites = sites

    async def collect(self) -> list[JobOpportunity]:
        jobs: list[JobOpportunity] = []

        for site in self.sites:
            jobs.extend(self._collect_site(site))

        return jobs

    def _collect_site(self, site: str) -> list[JobOpportunity]:
        url = (
            "https://api.lever.co/v0/postings/"
            f"{quote(site, safe='')}?mode=json"
        )

        try:
            with urlopen(url, timeout=20) as response:
                postings = json.load(response)
        except Exception:
            return []

        jobs: list[JobOpportunity] = []

        for posting in postings:
            categories = posting.get("categories", {})

            jobs.append(
                JobOpportunity(
                    title=posting.get("text", ""),
                    company=site,
                    location_text=categories.get("location", ""),
                    source="lever",
                    url=posting.get("hostedUrl", ""),
                    external_id=posting.get("id", ""),
                    description=posting.get("descriptionPlain", ""),
                    metadata={
                        "team": categories.get("team", ""),
                        "commitment": categories.get("commitment", ""),
                    },
                )
            )

        return jobs

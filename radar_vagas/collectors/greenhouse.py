"""Coletor de vagas públicas de empresas que utilizam Greenhouse."""

from __future__ import annotations

import json
from urllib.request import Request, urlopen

from radar_vagas.collectors.base import JobCollector
from radar_vagas.core.models import JobOpportunity


class GreenhouseCollector(JobCollector):
    """Coleta vagas públicas através da API do Greenhouse."""

    name = "greenhouse"

    def __init__(self, boards: tuple[str, ...]) -> None:
        self.boards = boards

    async def collect(self) -> list[JobOpportunity]:
        jobs: list[JobOpportunity] = []

        for board in self.boards:
            jobs.extend(self._collect_board(board))

        return jobs

    def _collect_board(self, board: str) -> list[JobOpportunity]:
        url = (
            "https://boards-api.greenhouse.io/v1/boards/"
            f"{board}/jobs?content=true"
        )

        request = Request(
            url,
            headers={
                "User-Agent": "RadarVagas/1.0",
                "Accept": "application/json",
            },
        )

        try:
            with urlopen(request, timeout=20) as response:
                data = json.load(response)
        except Exception:
            return []

        postings = data.get("jobs", [])

        if not isinstance(postings, list):
            return []

        jobs: list[JobOpportunity] = []

        for posting in postings:
            if not isinstance(posting, dict):
                continue

            title = str(
                posting.get("title") or ""
            ).strip()

            url = str(
                posting.get("absolute_url") or ""
            ).strip()

            if not title or not url:
                continue

            location = ""

            location_data = posting.get("location")

            if isinstance(location_data, dict):
                location = str(
                    location_data.get("name") or ""
                ).strip()

            company = board.replace("-", " ").title()

            metadata: dict[str, str] = {
                "department": "",
                "team": "",
            }

            departments = posting.get("departments")

            if isinstance(departments, list):
                names: list[str] = []

                for department in departments:
                    if isinstance(department, dict):
                        name = str(
                            department.get("name") or ""
                        ).strip()

                        if name:
                            names.append(name)

                if names:
                    metadata["department"] = ", ".join(names)

            jobs.append(
                JobOpportunity(
                    source="greenhouse",
                    title=title,
                    url=url,
                    company=company,
                    description=str(
                        posting.get("content") or ""
                    ),
                    location_text=location,
                    remote=True,
                    external_id=str(
                        posting.get("id") or ""
                    ),
                    metadata=metadata,
                )
            )

        return jobs

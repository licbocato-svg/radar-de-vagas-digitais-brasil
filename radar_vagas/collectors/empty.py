"""Coletor vazio usado enquanto fontes externas não foram conectadas."""

from __future__ import annotations

from collections.abc import Sequence

from radar_vagas.collectors.base import JobCollector
from radar_vagas.core.models import JobOpportunity


class EmptyCollector(JobCollector):
    """Mantém a CLI executável sem realizar chamadas de rede."""

    name = "empty"

    async def collect(self) -> Sequence[JobOpportunity]:
        return ()
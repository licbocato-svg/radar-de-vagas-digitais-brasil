"""Contrato comum para futuros coletores."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from radar_vagas.core.models import JobOpportunity


class JobCollector(ABC):
    """Cada plataforma externa deve devolver oportunidades normalizadas."""

    name: str

    @abstractmethod
    async def collect(self) -> Sequence[JobOpportunity]:
        """Coleta vagas da fonte sem aplicar regras globais."""

        raise NotImplementedError
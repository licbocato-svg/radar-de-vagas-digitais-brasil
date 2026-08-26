"""Modelos centrais do domínio de vagas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping


@dataclass(frozen=True, slots=True)
class JobOpportunity:
    """Representa uma vaga normalizada por qualquer coletor."""

    source: str
    title: str
    url: str
    company: str = ""
    description: str = ""
    location_text: str = ""
    eligible_countries: tuple[str, ...] = ()
    remote: bool = True
    external_id: str | None = None
    published_at: datetime | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)
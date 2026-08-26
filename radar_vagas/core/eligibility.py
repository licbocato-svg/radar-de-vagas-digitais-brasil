"""Regras conservadoras para elegibilidade de residentes no Brasil."""

from __future__ import annotations

from radar_vagas.core.models import JobOpportunity
from radar_vagas.core.roles import normalize_text


BRAZIL_MARKERS = frozenset(
    {
        "br",
        "brazil",
        "brasil",
        "brasile",
        "brazilian",
        "portuguese brazil",
    }
)
GLOBAL_MARKERS = frozenset(
    {
        "worldwide",
        "global",
        "anywhere",
        "work from anywhere",
        "all countries",
        "international",
    }
)
EXCLUSION_MARKERS = frozenset(
    {
        "us only",
        "usa only",
        "united states only",
        "canada only",
        "uk only",
        "europe only",
    }
)


def _contains_marker(value: str, markers: frozenset[str]) -> bool:
    normalized = normalize_text(value)
    return any(normalize_text(marker) in normalized for marker in markers)


def eligible_for_brazil(job: JobOpportunity) -> bool:
    """Aplica uma decisão explícita; informação desconhecida não é aprovada."""

    country_text = " ".join(job.eligible_countries)
    combined_location = " ".join((country_text, job.location_text))

    if _contains_marker(combined_location, EXCLUSION_MARKERS):
        return False
    if _contains_marker(combined_location, BRAZIL_MARKERS):
        return True
    if _contains_marker(combined_location, GLOBAL_MARKERS):
        return True

    # Vaga remota sem país ou região declarada continua inconclusiva.
    return False
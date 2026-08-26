"""Correspondência dos cargos monitorados pelo Radar."""

from __future__ import annotations

import re
import unicodedata

from radar_vagas.core.models import JobOpportunity


TARGET_ROLES: tuple[str, ...] = (
    "Avaliador de Mapas",
    "Online Data Analyst",
    "Avaliador de Conteúdo",
    "Avaliador de Anúncios",
    "Avaliador de Mídias Sociais",
    "Search Quality Rater",
    "Internet Assessor",
    "Avaliador de IA",
)

ROLE_ALIASES: dict[str, tuple[str, ...]] = {
    "Avaliador de Mapas": ("map evaluator", "maps evaluator", "map quality"),
    "Online Data Analyst": ("online data analyst", "data analyst online"),
    "Avaliador de Conteúdo": ("content evaluator", "content reviewer"),
    "Avaliador de Anúncios": ("ads evaluator", "ad evaluator", "ads assessor"),
    "Avaliador de Mídias Sociais": (
        "social media evaluator",
        "social media assessor",
    ),
    "Search Quality Rater": ("search quality rater", "search evaluator"),
    "Internet Assessor": ("internet assessor",),
    "Avaliador de IA": ("ai evaluator", "ai trainer", "ai rater"),
}


def normalize_text(value: str) -> str:
    """Normaliza acentos, caixa e pontuação para comparações consistentes."""

    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()


def matched_roles(job: JobOpportunity) -> tuple[str, ...]:
    """Retorna os cargos monitorados encontrados na oportunidade."""

    searchable_text = normalize_text(
        " ".join((job.title, job.description, *job.metadata.values()))
    )
    matches: list[str] = []

    for role in TARGET_ROLES:
        terms = (role, *ROLE_ALIASES.get(role, ()))
        if any(normalize_text(term) in searchable_text for term in terms):
            matches.append(role)

    return tuple(matches)


def matches_target_role(job: JobOpportunity) -> bool:
    """Indica se a vaga está relacionada a algum cargo monitorado."""

    return bool(matched_roles(job))
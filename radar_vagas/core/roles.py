
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
    "Treinador de IA",
    "Anotador de Dados",
    "Anotador de Dados de Robótica",
    "Coletor de Dados",
    "Coletor de Vídeos",
    "Gravador de Vídeos",
    "Data Collector",
    "Data Annotator",
    "Robotics Data Annotator",
    "Robot Trainer",
    "AI Trainer",
    "Video Data Collector",
    "Video Recorder",
    "Data Contributor",
    "Egocentric Video Data Contributor",
    "Robotics Data Contributor",
)

ROLE_ALIASES: dict[str, tuple[str, ...]] = {
    "Avaliador de Mapas": (
        "map evaluator", "maps evaluator", "map quality",
    ),
    "Online Data Analyst": (
        "online data analyst", "data analyst online",
    ),
    "Avaliador de Conteúdo": (
        "content evaluator", "content reviewer",
    ),
    "Avaliador de Anúncios": (
        "ads evaluator", "ad evaluator", "ads assessor",
    ),
    "Avaliador de Mídias Sociais": (
        "social media evaluator", "social media assessor",
    ),
    "Search Quality Rater": (
        "search quality rater", "search evaluator",
    ),
    "Internet Assessor": ("internet assessor",),
    "Avaliador de IA": (
        "ai evaluator", "ai trainer", "ai rater",
    ),
    "Treinador de IA": (
        "ai trainer", "ai training", "train ai models",
    ),
    "Anotador de Dados": (
        "data annotator", "data annotation",
        "labeling data", "data labeling",
    ),
    "Anotador de Dados de Robótica": (
        "robotics data annotator", "robotics annotation",
        "robot data annotation",
    ),
    "Coletor de Dados": (
        "data collector", "data collection", "data contributor",
    ),
    "Coletor de Vídeos": (
        "video data collector", "video data collection",
        "video contributor",
    ),
    "Gravador de Vídeos": (
        "video recorder", "at-home video recorder",
        "video recording",
    ),
    "Data Collector": ("data collector", "data collection"),
    "Data Annotator": ("data annotator", "data annotation"),
    "Robotics Data Annotator": (
        "robotics data annotator", "robotics data annotation",
    ),
    "Robot Trainer": ("robot trainer", "robot training"),
    "AI Trainer": ("ai trainer", "ai training"),
    "Video Data Collector": (
        "video data collector", "video data collection",
    ),
    "Video Recorder": ("video recorder", "video recording"),
    "Data Contributor": ("data contributor", "data collection"),
    "Egocentric Video Data Contributor": (
        "egocentric video", "egocentric data collection",
    ),
    "Robotics Data Contributor": (
        "robotics data contributor", "robotics data collection",
    ),
}


def normalize_text(value: str) -> str:
    """Normaliza acentos, caixa e pontuação para comparações consistentes."""

    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
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
        if any(
            normalize_text(term) in searchable_text
            for term in terms
        ):
            matches.append(role)

    return tuple(matches)


def matches_target_role(job: JobOpportunity) -> bool:
    """Indica se a vaga está relacionada a algum cargo monitorado."""

    return bool(matched_roles(job))

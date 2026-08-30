"""Regras de elegibilidade para oportunidades que podem ser exercidas por residentes no Brasil."""

from __future__ import annotations

from radar_vagas.core.models import JobOpportunity
from radar_vagas.core.roles import normalize_text


# ============================================================
# INDICADORES DE CONTRATAÇÃO DIRETA NO BRASIL
# ============================================================

BRAZIL_MARKERS = frozenset(
    {
        "br",
        "brazil",
        "brasil",
        "brasile",
        "brazilian",
        "portuguese brazil",
        "portuguese (brazil)",
        "pt-br",
        "pt br",
        "sao paulo",
        "são paulo",
        "rio de janeiro",
        "minas gerais",
        "parana",
        "paraná",
        "curitiba",
        "recife",
        "salvador",
        "brasilia",
        "brasília",
    }
)


# ============================================================
# INDICADORES DE CONTRATAÇÃO INTERNACIONAL
# ============================================================

GLOBAL_MARKERS = frozenset(
    {
        "worldwide",
        "global",
        "anywhere",
        "work from anywhere",
        "work-from-anywhere",
        "all countries",
        "international",
        "internationally",
        "global remote",
        "remote worldwide",
    }
)


# ============================================================
# REGIÕES QUE PODEM INCLUIR O BRASIL
# ============================================================

BRAZIL_COMPATIBLE_REGIONS = frozenset(
    {
        "latin america",
        "latam",
        "south america",
        "south american",
        "americas",
        "america",
        "the americas",
        "central and south america",
        "central america and south america",
        "latin america and the caribbean",
        "latam region",
        "latin america region",
        "south america region",
    }
)


# ============================================================
# INDICADORES DE TRABALHO REMOTO
# ============================================================

REMOTE_MARKERS = frozenset(
    {
        "remote",
        "fully remote",
        "100% remote",
        "remote work",
        "work remotely",
        "work from home",
        "home office",
        "distributed",
    }
)


# ============================================================
# RESTRIÇÕES GEOGRÁFICAS EXPLÍCITAS
# ============================================================

EXCLUSION_MARKERS = frozenset(
    {
        "us only",
        "usa only",
        "u.s. only",
        "u.s.a. only",
        "united states only",
        "united states residents only",
        "us residents only",
        "usa residents only",
        "canada only",
        "canada residents only",
        "uk only",
        "uk residents only",
        "united kingdom only",
        "europe only",
        "european union only",
        "eu only",
        "australia only",
        "new zealand only",
        "asia only",
    }
)


def _contains_marker(
    value: str,
    markers: frozenset[str],
) -> bool:
    """Verifica se algum marcador aparece no texto normalizado."""

    normalized = normalize_text(
        value
    )

    return any(
        normalize_text(marker)
        in normalized
        for marker in markers
    )


def _job_text(
    job: JobOpportunity,
) -> str:
    """Combina as informações geográficas disponíveis na vaga."""

    parts = [
        job.location_text,
        *job.eligible_countries,
    ]

    return " ".join(
        str(part)
        for part in parts
        if part
    )


def eligible_for_brazil(
    job: JobOpportunity,
) -> bool:
    """
    Decide se uma oportunidade pode ser publicada
    para pessoas que estão no Brasil.

    A prioridade é:

    1. Restrições explícitas → rejeita.
    2. Brasil → aceita.
    3. Região compatível com Brasil → aceita.
    4. Contratação global/internacional → aceita.
    5. Remote sem região → permanece inconclusiva.
    """

    location_text = _job_text(
        job
    )

    # --------------------------------------------------------
    # 1. RESTRIÇÃO EXPLÍCITA
    # --------------------------------------------------------

    if _contains_marker(
        location_text,
        EXCLUSION_MARKERS,
    ):
        return False

    # --------------------------------------------------------
    # 2. BRASIL
    # --------------------------------------------------------

    if _contains_marker(
        location_text,
        BRAZIL_MARKERS,
    ):
        return True

    # --------------------------------------------------------
    # 3. AMÉRICA LATINA / AMÉRICA DO SUL
    # --------------------------------------------------------

    if _contains_marker(
        location_text,
        BRAZIL_COMPATIBLE_REGIONS,
    ):
        return True

    # --------------------------------------------------------
    # 4. GLOBAL / INTERNACIONAL
    # --------------------------------------------------------

    if _contains_marker(
        location_text,
        GLOBAL_MARKERS,
    ):
        return True

    # --------------------------------------------------------
    # 5. REMOTO SEM REGIÃO DEFINIDA
    # --------------------------------------------------------
    #
    # "Remote" sozinho não garante que brasileiros
    # possam se candidatar.
    #
    # Por isso, continuamos conservadores aqui.
    # --------------------------------------------------------

    if _contains_marker(
        location_text,
        REMOTE_MARKERS,
    ):
        return False

    # --------------------------------------------------------
    # 6. INFORMAÇÃO INSUFICIENTE
    # --------------------------------------------------------

    return False

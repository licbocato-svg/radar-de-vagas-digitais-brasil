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
        "brazil remote",
        "remote brazil",
        "remote - brazil",
        "remote – brazil",
        "remote, brazil",
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
        "all locations",
        "international",
        "internationally",
        "global remote",
        "remote worldwide",
        "remote global",
        "remote anywhere",
        "worldwide remote",
        "work anywhere",
    }
)


# ============================================================
# REGIÕES QUE PODEM INCLUIR O BRASIL
# ============================================================

BRAZIL_COMPATIBLE_REGIONS = frozenset(
    {
        "latin america",
        "latin-america",
        "latam",
        "latam region",
        "latin america region",
        "south america",
        "south-america",
        "south american",
        "americas",
        "the americas",
        "america",
        "central and south america",
        "central america and south america",
        "latin america and the caribbean",
        "latin america & caribbean",
        "latam region",
        "americas region",
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
        "remote position",
        "remote role",
        "remote job",
        "remote opportunity",
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
        "australia residents only",
        "new zealand only",
        "new zealand residents only",
        "asia only",
        "asia residents only",
    }
)


def _contains_marker(
    value: str,
    markers: frozenset[str],
) -> bool:
    """Verifica se algum marcador aparece no texto normalizado."""

    normalized = normalize_text(value)

    return any(
        normalize_text(marker) in normalized
        for marker in markers
    )


def _job_text(
    job: JobOpportunity,
) -> str:
    """Combina todas as informações geográficas disponíveis na vaga."""

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

    Ordem de decisão:

    1. Restrição geográfica explícita -> rejeita.
    2. Brasil -> aceita.
    3. América Latina / América do Sul / Américas -> aceita.
    4. Global / internacional -> aceita.
    5. Remote sem região -> aceita somente quando
       a própria vaga não apresenta uma restrição.
    6. Informação insuficiente -> rejeita.
    """

    location_text = _job_text(job)

    normalized_location = normalize_text(
        location_text
    )

    # --------------------------------------------------------
    # 1. RESTRIÇÕES EXPLÍCITAS
    # --------------------------------------------------------

    if _contains_marker(
        normalized_location,
        EXCLUSION_MARKERS,
    ):
        return False

    # --------------------------------------------------------
    # 2. BRASIL
    # --------------------------------------------------------

    if _contains_marker(
        normalized_location,
        BRAZIL_MARKERS,
    ):
        return True

    # --------------------------------------------------------
    # 3. AMÉRICA LATINA / AMÉRICA DO SUL / AMÉRICAS
    # --------------------------------------------------------

    if _contains_marker(
        normalized_location,
        BRAZIL_COMPATIBLE_REGIONS,
    ):
        return True

    # --------------------------------------------------------
    # 4. GLOBAL / INTERNACIONAL
    # --------------------------------------------------------

    if _contains_marker(
        normalized_location,
        GLOBAL_MARKERS,
    ):
        return True

    # --------------------------------------------------------
    # 5. REMOTO SEM RESTRIÇÃO GEOGRÁFICA
    # --------------------------------------------------------
    #
    # Se a fonte informa que a vaga é remota, mas não
    # apresenta uma restrição geográfica, consideramos
    # potencialmente elegível para brasileiros.
    #
    # A existência de uma restrição explícita já foi
    # verificada acima.
    # --------------------------------------------------------

    if _contains_marker(
        normalized_location,
        REMOTE_MARKERS,
    ):
        return True

    # --------------------------------------------------------
    # 6. INFORMAÇÃO INSUFICIENTE
    # --------------------------------------------------------

    return False

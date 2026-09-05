"""Fingerprints e armazenamento local para evitar vagas duplicadas."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from radar_vagas.core.models import JobOpportunity
from radar_vagas.core.roles import normalize_text


class SeenJobStore(Protocol):
    """Interface para armazenamento de vagas já publicadas."""

    def contains(self, fingerprint: str) -> bool:
        ...

    def remember_many(
        self,
        fingerprints: Iterable[str],
    ) -> None:
        ...


def canonicalize_url(url: str) -> str:
    """
    Normaliza a URL da vaga.

    Remove parâmetros comuns de rastreamento para que
    pequenas alterações na URL não criem uma nova vaga.
    """

    parsed = urlsplit(url.strip())

    query = [
        (key, value)
        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        )
        if not key.casefold().startswith("utm_")
        and key.casefold()
        not in {
            "ref",
            "source",
        }
    ]

    path = parsed.path.rstrip("/") or "/"

    return urlunsplit(
        (
            parsed.scheme.casefold(),
            parsed.netloc.casefold(),
            path,
            urlencode(query),
            "",
        )
    )


def job_fingerprint(job: JobOpportunity) -> str:
    """
    Gera uma identidade estável para a vaga.

    PRIORIDADE:

    1. URL da vaga
    2. ID da vaga na fonte
    3. Conteúdo básico da vaga

    A URL é usada primeiro porque é a identificação mais
    estável para oportunidades publicadas em páginas de vagas.
    """

    # ========================================================
    # 1. URL DA VAGA
    # ========================================================

    if job.url and job.url.strip():
        identity = (
            "url:"
            + canonicalize_url(job.url)
        )

    # ========================================================
    # 2. ID DA FONTE
    # ========================================================

    elif job.external_id:
        identity = (
            "source-id:"
            + normalize_text(job.source)
            + ":"
            + job.external_id.strip()
        )

    # ========================================================
    # 3. ÚLTIMO RECURSO
    # ========================================================

    else:
        identity = "|".join(
            (
                normalize_text(job.source),
                normalize_text(job.title),
                normalize_text(job.company),
                normalize_text(job.location_text),
            )
        )

        identity = "content:" + identity

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()


class JsonSeenJobStore:
    """Armazena fingerprints em JSON com escrita atômica."""

    def __init__(
        self,
        path: Path,
    ) -> None:
        self.path = path
        self._fingerprints = self._load()

    def _load(self) -> set[str]:
        if not self.path.exists():
            return set()

        with self.path.open(
            "r",
            encoding="utf-8",
        ) as file:
            payload = json.load(file)

        if (
            not isinstance(payload, list)
            or not all(
                isinstance(item, str)
                for item in payload
            )
        ):
            raise ValueError(
                "Formato inválido no armazenamento "
                f"de vagas: {self.path}"
            )

        return set(payload)

    def contains(
        self,
        fingerprint: str,
    ) -> bool:
        return fingerprint in self._fingerprints

    def remember_many(
        self,
        fingerprints: Iterable[str],
    ) -> None:

        new_fingerprints = (
            set(fingerprints)
            - self._fingerprints
        )

        if not new_fingerprints:
            return

        self._fingerprints.update(
            new_fingerprints
        )

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        descriptor, temporary_path = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            dir=self.path.parent,
            text=True,
        )

        try:
            with os.fdopen(
                descriptor,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    sorted(
                        self._fingerprints
                    ),
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

                file.write("\n")

            os.replace(
                temporary_path,
                self.path,
            )

        except Exception:
            os.unlink(
                temporary_path
            )
            raise

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
    """Interface para trocar o JSON por outro armazenamento no futuro."""

    def contains(self, fingerprint: str) -> bool:
        ...

    def remember_many(self, fingerprints: Iterable[str]) -> None:
        ...


def canonicalize_url(url: str) -> str:
    """Remove ruído comum de tracking antes de gerar o fingerprint."""

    parsed = urlsplit(url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_") and key.casefold() not in {"ref", "source"}
    ]
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit(
        (parsed.scheme.casefold(), parsed.netloc.casefold(), path, urlencode(query), "")
    )


def job_fingerprint(job: JobOpportunity) -> str:
    """Gera uma identidade estável por URL ou pelo conteúdo normalizado."""

    if job.url.strip():
        identity = f"url:{canonicalize_url(job.url)}"
    elif job.external_id:
        identity = f"source-id:{normalize_text(job.source)}:{job.external_id.strip()}"
    else:
        identity = "|".join(
            (
                normalize_text(job.source),
                normalize_text(job.title),
                normalize_text(job.company),
                normalize_text(job.location_text),
            )
        )
        identity = f"content:{identity}"

    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


class JsonSeenJobStore:
    """Armazena fingerprints em JSON com escrita atômica e formato legível."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._fingerprints = self._load()

    def _load(self) -> set[str]:
        if not self.path.exists():
            return set()
        with self.path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if not isinstance(payload, list) or not all(
            isinstance(item, str) for item in payload
        ):
            raise ValueError(f"Formato inválido no armazenamento de vagas: {self.path}")
        return set(payload)

    def contains(self, fingerprint: str) -> bool:
        return fingerprint in self._fingerprints

    def remember_many(self, fingerprints: Iterable[str]) -> None:
        new_fingerprints = set(fingerprints) - self._fingerprints
        if not new_fingerprints:
            return

        self._fingerprints.update(new_fingerprints)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_path = tempfile.mkstemp(
            prefix=f".{self.path.name}.",
            dir=self.path.parent,
            text=True,
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                json.dump(sorted(self._fingerprints), file, ensure_ascii=False, indent=2)
                file.write("\n")
            os.replace(temporary_path, self.path)
        except Exception:
            os.unlink(temporary_path)
            raise
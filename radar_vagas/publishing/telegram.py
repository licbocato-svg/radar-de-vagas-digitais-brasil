"""Contrato e formatação para uma futura publicação no Telegram."""

from __future__ import annotations

from typing import Protocol

from radar_vagas.core.models import JobOpportunity
from radar_vagas.core.roles import matched_roles


class TelegramPublisher(Protocol):
    """Interface para um cliente oficial do Telegram, ainda não conectado."""

    async def publish(self, job: JobOpportunity) -> None:
        """Publica uma oportunidade já filtrada."""
        ...


def format_job_message(job: JobOpportunity) -> str:
    """Formata uma vaga sem fazer qualquer chamada externa."""

    roles = ", ".join(matched_roles(job)) or "Vaga digital"
    lines = [f"{job.title} — {roles}"]
    if job.company:
        lines.append(f"Empresa: {job.company}")
    if job.location_text:
        lines.append(f"Localização: {job.location_text}")
    lines.append(f"Fonte: {job.source}")
    lines.append(job.url)
    return "\n".join(lines)
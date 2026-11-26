"""
BiofilmAI Backend — In-memory storage for demo analyses.

In a production deployment this would be replaced with a database
(PostgreSQL, MongoDB, etc.).  For the research prototype, in-memory
storage is sufficient.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Optional

from models import AnalysisResponse, AnalysisSummary


class AnalysisStorage:
    """Thread-safe in-memory store for analysis results."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._analyses: dict[str, AnalysisResponse] = {}

    def save(self, analysis: AnalysisResponse) -> None:
        with self._lock:
            self._analyses[analysis.analysis_id] = analysis

    def get(self, analysis_id: str) -> Optional[AnalysisResponse]:
        with self._lock:
            return self._analyses.get(analysis_id)

    def list_all(self) -> list[AnalysisSummary]:
        with self._lock:
            summaries = []
            for a in sorted(
                self._analyses.values(),
                key=lambda x: x.created_at,
                reverse=True,
            ):
                summaries.append(
                    AnalysisSummary(
                        analysis_id=a.analysis_id,
                        sample_id=a.sample_id,
                        sample_type=a.sample_type,
                        created_at=a.created_at,
                        modalities=list(a.modalities.keys()),
                        prediction=a.prediction,
                        status=a.status,
                        demo_mode=a.demo_mode,
                    )
                )
            return summaries

    def count(self) -> int:
        with self._lock:
            return len(self._analyses)


# Global singleton
storage = AnalysisStorage()
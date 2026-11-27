"""
BiofilmAI Backend — Analysis storage.

Analyses are kept in memory and saved to analyses.json next to this file, so
History and the Dashboard survive a backend restart. The file is loaded at
start-up and rewritten (atomically) after every new analysis.

Set BIOFILM_STORAGE_FILE to use a different file. In a production deployment
this would be replaced with a database (PostgreSQL, etc.).
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Optional

from models import AnalysisResponse, AnalysisSummary

logger = logging.getLogger(__name__)

STORAGE_FILE = Path(os.getenv("BIOFILM_STORAGE_FILE", Path(__file__).resolve().parent / "analyses.json"))


class AnalysisStorage:
    """Thread-safe store for analysis results, persisted to a JSON file."""

    def __init__(self, path: Path = STORAGE_FILE) -> None:
        self._lock = threading.Lock()
        self._path = path
        self._analyses: dict[str, AnalysisResponse] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.is_file():
            return
        try:
            for item in json.loads(self._path.read_text(encoding="utf-8")):
                analysis = AnalysisResponse.model_validate(item)
                self._analyses[analysis.analysis_id] = analysis
            logger.info("Loaded %d saved analyses from %s", len(self._analyses), self._path)
        except Exception as exc:
            logger.error("Could not read %s (%s); starting with empty history.", self._path, exc)

    def _write(self) -> None:
        data = [a.model_dump(by_alias=True) for a in self._analyses.values()]
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data), encoding="utf-8")
        os.replace(tmp, self._path)

    def save(self, analysis: AnalysisResponse) -> None:
        with self._lock:
            self._analyses[analysis.analysis_id] = analysis
            try:
                self._write()
            except OSError as exc:
                logger.error("Could not save analyses to %s: %s", self._path, exc)

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

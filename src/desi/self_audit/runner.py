"""SelfAuditRunner — orchestrator over Aufgaben 1–7."""
from __future__ import annotations

import pathlib
from datetime import datetime, timezone

from .contradictions import find_contradictions
from .corpus import DEFAULT_DOC_ROOTS, index_corpus
from .drift import find_drift
from .extractor import extract_claims_from_text
from .replayer import replay_claims
from .report import SelfAuditReport, build_audit_report


_DEFAULT_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


class SelfAuditRunner:
    def __init__(
        self,
        *,
        repo_root: pathlib.Path | None = None,
        doc_roots: tuple[str, ...] = DEFAULT_DOC_ROOTS,
        artifact_root: pathlib.Path | None = None,
    ) -> None:
        self._repo_root = repo_root or _DEFAULT_REPO_ROOT
        self._doc_roots = doc_roots
        self._artifact_root = (
            artifact_root or (self._repo_root / "artifacts")
        )

    def run(self) -> SelfAuditReport:
        started_at = datetime.now(timezone.utc)
        documents = index_corpus(
            self._repo_root, roots=self._doc_roots,
        )
        # Extract claims per document.
        all_claims = []
        for doc in documents:
            text = (self._repo_root / doc.path).read_text(
                encoding="utf-8",
            )
            all_claims.extend(extract_claims_from_text(
                doc_id=doc.doc_id, doc_path=doc.path, text=text,
            ))
        all_claims = tuple(all_claims)
        replayed = replay_claims(
            all_claims, artifact_root=self._artifact_root,
        )
        contradictions = find_contradictions(all_claims)
        drift = find_drift(all_claims)
        finished_at = datetime.now(timezone.utc)
        return build_audit_report(
            documents=documents,
            replayed_claims=replayed,
            contradictions=contradictions,
            drift_findings=drift,
            started_at=started_at,
            finished_at=finished_at,
        )


__all__ = ["SelfAuditRunner"]

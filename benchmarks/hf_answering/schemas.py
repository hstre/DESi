"""Schemas for the HF answering benchmark layer (PERIPHERAL).

Plain dataclasses for QA examples, model answers, and evaluation results. No
DESi core types are imported here — this layer sits entirely on the periphery.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class QAExample:
    """One boolean-QA example with ground truth."""
    id: str
    question: str
    passage: str
    gold: bool


@dataclass(frozen=True)
class ModelAnswer:
    """One model answer — raw text plus the parsed boolean (or None if
    unparseable). ONE deterministic call; no retries, no repair."""
    id: str
    raw_text: str
    parsed: bool | None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    error: str | None = None


@dataclass(frozen=True)
class Confusion:
    """Confusion matrix with 'positive' = True."""
    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class EvalResult:
    model: str
    n: int
    answered: int
    unparsed: int
    errors: int
    accuracy: float | None
    confusion: Confusion
    elapsed_s: float
    est_cost_usd: float | None

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        d["confusion"] = self.confusion.to_dict()
        return d


@dataclass
class RunRecord:
    """The full peripheral run record: benchmark scoring + DESi-core metrics
    recorded alongside (DESi is NOT the answer generator)."""
    dataset: str
    split: str
    model: str
    backend: str
    prompt: str
    examples: int
    blocked_reason: str | None
    eval: EvalResult | None
    desi_core: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset": self.dataset, "split": self.split, "model": self.model,
            "backend": self.backend, "prompt": self.prompt,
            "examples": self.examples, "blocked_reason": self.blocked_reason,
            "eval": self.eval.to_dict() if self.eval else None,
            "desi_core": self.desi_core,
        }


__all__ = ["Confusion", "EvalResult", "ModelAnswer", "QAExample", "RunRecord"]

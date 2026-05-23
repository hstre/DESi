"""Aufgaben 1 + 4 — closed signal taxonomy + per-chain extractor.

Eleven signals per chain, exactly as the directive enumerates.
All values come from the existing v1.2 ``PremiseExtractor`` — no
new regex, no new buckets, no LLM. ``paraphrase_instability``
is deliberately scored against a punctuation-perturbation
re-extraction so the metric is meaningful even though the
extractor is otherwise deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..logic.premises import PremiseExtractor, PremiseKind


class SignalName(str, Enum):
    PREMISE_COUNT              = "premise_count"
    ATOMIC_RATIO               = "atomic_ratio"
    PARTICULAR_RATIO           = "particular_ratio"
    UNIVERSAL_RATIO            = "universal_ratio"
    UNSUPPORTED_FORM_RATIO     = "unsupported_form_ratio"
    EXTRACTION_DROP_RATE       = "extraction_drop_rate"
    PREMISE_TOKEN_COUNT        = "premise_token_count"
    CONCLUSION_TOKEN_COUNT     = "conclusion_token_count"
    PREMISE_CONCLUSION_OVERLAP = "premise_conclusion_overlap"
    COMPRESSION_RATIO          = "compression_ratio"
    PARAPHRASE_INSTABILITY     = "paraphrase_instability"


SIGNAL_ORDER: tuple[str, ...] = tuple(s.value for s in SignalName)


_STOPWORDS: frozenset[str] = frozenset({
    "the", "a", "an", "this", "that", "these", "those",
    "is", "are", "was", "were", "be", "been", "being",
    "of", "in", "on", "at", "to", "for", "with", "and", "or",
    "as", "by", "from", "than", "then",
    "therefore", "thus", "so", "hence",
    "if", "while", "when", "where",
    "not", "no", "yes", "all", "some", "any",
})


def _tokens(text: str) -> list[str]:
    s = " " + text.lower() + " "
    for ch in ",.:;!?'\"":
        s = s.replace(ch, " ")
    return [
        t for t in s.split()
        if t not in _STOPWORDS and len(t) >= 3
    ]


def _sentence_count(text: str) -> int:
    parts = [p.strip() for p in text.replace("Therefore ", "").split(".")]
    return sum(1 for p in parts if p)


@dataclass(frozen=True)
class ExtractionSignals:
    chain_id: str
    premise_count: float
    premise_kind_sequence: tuple[str, ...]
    atomic_ratio: float
    particular_ratio: float
    universal_ratio: float
    unsupported_form_ratio: float
    extraction_drop_rate: float
    premise_token_count: float
    conclusion_token_count: float
    premise_conclusion_overlap: float
    compression_ratio: float
    paraphrase_instability: float

    def feature_tuple(self) -> tuple[float, ...]:
        return (
            self.premise_count,
            self.atomic_ratio,
            self.particular_ratio,
            self.universal_ratio,
            self.unsupported_form_ratio,
            self.extraction_drop_rate,
            self.premise_token_count,
            self.conclusion_token_count,
            self.premise_conclusion_overlap,
            self.compression_ratio,
            self.paraphrase_instability,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "premise_count": self.premise_count,
            "premise_kind_sequence":
                list(self.premise_kind_sequence),
            "atomic_ratio": self.atomic_ratio,
            "particular_ratio": self.particular_ratio,
            "universal_ratio": self.universal_ratio,
            "unsupported_form_ratio": self.unsupported_form_ratio,
            "extraction_drop_rate": self.extraction_drop_rate,
            "premise_token_count": self.premise_token_count,
            "conclusion_token_count": self.conclusion_token_count,
            "premise_conclusion_overlap":
                self.premise_conclusion_overlap,
            "compression_ratio": self.compression_ratio,
            "paraphrase_instability": self.paraphrase_instability,
        }


def _perturb(text: str) -> str:
    """Punctuation-perturbation: insert a comma before
    'Therefore' so the extractor's sentence boundary heuristic
    sees a different split. Used by paraphrase_instability."""
    if "Therefore" in text and ", Therefore" not in text:
        return text.replace("Therefore", ", Therefore")
    return text + "."


def extract_signals(
    chain_id: str, text: str,
    *, extractor: PremiseExtractor | None = None,
) -> ExtractionSignals:
    extractor = extractor or PremiseExtractor()
    result = extractor.extract(text)
    premises = result.premises
    conclusion = result.conclusion

    premise_count = float(len(premises))
    sent_count = _sentence_count(text)
    drop_rate = (
        max(0.0, (sent_count - len(premises) - (1 if conclusion else 0)))
        / max(1, sent_count)
    )

    kinds = [p.kind.value for p in premises]
    atomic = sum(1 for k in kinds if k == PremiseKind.ATOMIC.value)
    particular = sum(
        1 for k in kinds if k == PremiseKind.PARTICULAR.value
    )
    universal = sum(
        1 for k in kinds if k == PremiseKind.UNIVERSAL.value
    )
    unsupported = sum(
        1 for k in kinds
        if k not in (
            PremiseKind.ATOMIC.value,
            PremiseKind.PARTICULAR.value,
            PremiseKind.UNIVERSAL.value,
        )
    )
    denom = max(1, len(kinds))

    premise_tokens = sum(len(_tokens(p.text)) for p in premises)
    conclusion_tokens = (
        len(_tokens(conclusion.text)) if conclusion else 0
    )
    input_tokens = len(_tokens(text)) or 1
    compression = (
        (premise_tokens + conclusion_tokens) / input_tokens
    )

    # premise_conclusion_overlap: Jaccard between premise tokens
    # (union) and conclusion tokens.
    premise_token_set = set()
    for p in premises:
        premise_token_set.update(_tokens(p.text))
    conclusion_token_set = (
        set(_tokens(conclusion.text)) if conclusion else set()
    )
    if premise_token_set or conclusion_token_set:
        inter = premise_token_set & conclusion_token_set
        union = premise_token_set | conclusion_token_set
        overlap = len(inter) / len(union) if union else 0.0
    else:
        overlap = 0.0

    # Paraphrase instability: re-extract on a punctuation
    # perturbation and count kind changes.
    perturbed = extractor.extract(_perturb(text))
    p_kinds = [p.kind.value for p in perturbed.premises]
    if not kinds and not p_kinds:
        instability = 0.0
    elif len(kinds) != len(p_kinds):
        instability = 1.0
    else:
        diffs = sum(1 for a, b in zip(kinds, p_kinds) if a != b)
        instability = diffs / max(1, len(kinds))

    return ExtractionSignals(
        chain_id=chain_id,
        premise_count=premise_count,
        premise_kind_sequence=tuple(kinds),
        atomic_ratio=round(atomic / denom, 6),
        particular_ratio=round(particular / denom, 6),
        universal_ratio=round(universal / denom, 6),
        unsupported_form_ratio=round(unsupported / denom, 6),
        extraction_drop_rate=round(drop_rate, 6),
        premise_token_count=float(premise_tokens),
        conclusion_token_count=float(conclusion_tokens),
        premise_conclusion_overlap=round(overlap, 6),
        compression_ratio=round(compression, 6),
        paraphrase_instability=round(instability, 6),
    )


__all__ = [
    "ExtractionSignals",
    "SIGNAL_ORDER",
    "SignalName",
    "extract_signals",
]

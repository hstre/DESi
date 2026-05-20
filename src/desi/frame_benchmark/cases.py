"""40 hand-written frame-benchmark cases — Aufgabe 8.

Five cases per category × eight categories = 40 total. Every
case carries an author-supplied frame label and a closed set of
expected allowed/blocked pipelines. The benchmark grades
:class:`FrameDetector` + :func:`check_compatibility` against the
labels — never against itself.
"""
from __future__ import annotations

from ..frames import FrameKind, allowed_pipelines, blocked_pipelines
from ..memory.claim import ClaimState
from .case import FrameBenchmarkCase, FrameCategory


def _case(
    case_id: str, category: FrameCategory, text: str,
    expected_frame: FrameKind, expected_state: ClaimState,
) -> FrameBenchmarkCase:
    return FrameBenchmarkCase(
        case_id=case_id, category=category, text=text,
        expected_frame=expected_frame,
        expected_state=expected_state,
        expected_allowed_pipeline=allowed_pipelines(expected_frame),
        expected_blocked_pipeline=blocked_pipelines(expected_frame),
    )


# Category A — thermodynamic explicitly framed
A_CASES = (
    _case("FA_01", FrameCategory.A_THERMO_VS_INFO,
          "Frame: thermodynamic. Entropy of an isolated system never decreases.",
          FrameKind.THERMODYNAMIC, ClaimState.FRAME_DECLARED),
    _case("FA_02", FrameCategory.A_THERMO_VS_INFO,
          "Frame: thermodynamic. Heat flows from hot to cold reservoirs.",
          FrameKind.THERMODYNAMIC, ClaimState.FRAME_DECLARED),
    _case("FA_03", FrameCategory.A_THERMO_VS_INFO,
          "Frame: information-theoretic. The Shannon entropy of a fair coin is 1 bit.",
          FrameKind.INFORMATION_THEORETIC, ClaimState.FRAME_DECLARED),
    _case("FA_04", FrameCategory.A_THERMO_VS_INFO,
          "Frame: information-theoretic. Mutual information is symmetric.",
          FrameKind.INFORMATION_THEORETIC, ClaimState.FRAME_DECLARED),
    _case("FA_05", FrameCategory.A_THERMO_VS_INFO,
          "Frame: thermodynamic. Temperature has units of kelvin.",
          FrameKind.THERMODYNAMIC, ClaimState.FRAME_DECLARED),
)

# Category B — metaphorical vs literal
B_CASES = (
    _case("FB_01", FrameCategory.B_METAPHOR_VS_LITERAL,
          "The market is nervous, like a herd of deer.",
          FrameKind.METAPHORICAL, ClaimState.FRAME_DECLARED),
    _case("FB_02", FrameCategory.B_METAPHOR_VS_LITERAL,
          "Frame: metaphorical. Time flies when you are having fun.",
          FrameKind.METAPHORICAL, ClaimState.FRAME_DECLARED),
    _case("FB_03", FrameCategory.B_METAPHOR_VS_LITERAL,
          "He spoke as if he were the king of his domain.",
          FrameKind.METAPHORICAL, ClaimState.FRAME_DECLARED),
    _case("FB_04", FrameCategory.B_METAPHOR_VS_LITERAL,
          "Loosely speaking, the algorithm runs in linear time.",
          FrameKind.METAPHORICAL, ClaimState.FRAME_DECLARED),
    _case("FB_05", FrameCategory.B_METAPHOR_VS_LITERAL,
          "In a sense, every particle is everywhere at once.",
          FrameKind.METAPHORICAL, ClaimState.FRAME_DECLARED),
)

# Category C — ontological distinguishability
C_CASES = (
    _case("FC_01", FrameCategory.C_ONTOLOGICAL_DISTINGUISHABILITY,
          "Frame: ontological distinguishability. Two electrons in the same state are indistinguishable.",
          FrameKind.ONTOLOGICAL_DISTINGUISHABILITY,
          ClaimState.FRAME_DECLARED),
    _case("FC_02", FrameCategory.C_ONTOLOGICAL_DISTINGUISHABILITY,
          "The morning star and the evening star refer to the same object.",
          FrameKind.ONTOLOGICAL_DISTINGUISHABILITY,
          ClaimState.FRAME_DECLARED),
    _case("FC_03", FrameCategory.C_ONTOLOGICAL_DISTINGUISHABILITY,
          "These two atoms are numerically identical in this experiment.",
          FrameKind.ONTOLOGICAL_DISTINGUISHABILITY,
          ClaimState.FRAME_DECLARED),
    _case("FC_04", FrameCategory.C_ONTOLOGICAL_DISTINGUISHABILITY,
          "The identity of the witness was preserved by the protocol.",
          FrameKind.ONTOLOGICAL_DISTINGUISHABILITY,
          ClaimState.FRAME_DECLARED),
    _case("FC_05", FrameCategory.C_ONTOLOGICAL_DISTINGUISHABILITY,
          "An ontological commitment to natural kinds entails distinguishable referents.",
          FrameKind.ONTOLOGICAL_DISTINGUISHABILITY,
          ClaimState.FRAME_DECLARED),
)

# Category D — authority speech
D_CASES = (
    _case("FD_01", FrameCategory.D_AUTHORITY_SPEECH,
          "Professor Smith says the result holds.",
          FrameKind.AUTHORITY_SPEECH, ClaimState.FRAME_DECLARED),
    _case("FD_02", FrameCategory.D_AUTHORITY_SPEECH,
          "The committee claimed the verdict was unanimous.",
          FrameKind.AUTHORITY_SPEECH, ClaimState.FRAME_DECLARED),
    _case("FD_03", FrameCategory.D_AUTHORITY_SPEECH,
          "According to the report the experiment succeeded.",
          FrameKind.AUTHORITY_SPEECH, ClaimState.FRAME_DECLARED),
    _case("FD_04", FrameCategory.D_AUTHORITY_SPEECH,
          "The vendor states the device passes all tests.",
          FrameKind.AUTHORITY_SPEECH, ClaimState.FRAME_DECLARED),
    _case("FD_05", FrameCategory.D_AUTHORITY_SPEECH,
          "Dr Lin published proof that the conjecture holds.",
          FrameKind.AUTHORITY_SPEECH, ClaimState.FRAME_DECLARED),
)

# Category E — tool-computable
E_CASES = (
    _case("FE_01", FrameCategory.E_TOOL_COMPUTABLE,
          "What is 2 + 2 ?",
          FrameKind.TOOL_COMPUTABLE, ClaimState.FRAME_DECLARED),
    _case("FE_02", FrameCategory.E_TOOL_COMPUTABLE,
          "Calculate 17 * 23.",
          FrameKind.TOOL_COMPUTABLE, ClaimState.FRAME_DECLARED),
    _case("FE_03", FrameCategory.E_TOOL_COMPUTABLE,
          "How many days from 2020-01-01 to 2020-12-31 ?",
          FrameKind.TOOL_COMPUTABLE, ClaimState.FRAME_DECLARED),
    _case("FE_04", FrameCategory.E_TOOL_COMPUTABLE,
          "Compute the sum 1 + 2 + 3 + 4 + 5.",
          FrameKind.TOOL_COMPUTABLE, ClaimState.FRAME_DECLARED),
    _case("FE_05", FrameCategory.E_TOOL_COMPUTABLE,
          "Is 144 = 12 * 12 ?",
          FrameKind.TOOL_COMPUTABLE, ClaimState.FRAME_DECLARED),
)

# Category F — formal logic
F_CASES = (
    _case("FF_01", FrameCategory.F_FORMAL_LOGIC,
          "Frame: formal logic. Modus ponens preserves truth.",
          FrameKind.FORMAL_LOGIC, ClaimState.FRAME_DECLARED),
    _case("FF_02", FrameCategory.F_FORMAL_LOGIC,
          "Frame: formal logic. A syllogism with two universal premises closes deductively.",
          FrameKind.FORMAL_LOGIC, ClaimState.FRAME_DECLARED),
    _case("FF_03", FrameCategory.F_FORMAL_LOGIC,
          "Frame: formal logic. Every x is at least one y.",
          FrameKind.FORMAL_LOGIC, ClaimState.FRAME_DECLARED),
    _case("FF_04", FrameCategory.F_FORMAL_LOGIC,
          "Frame: formal logic. From A->B and B->C we derive A->C.",
          FrameKind.FORMAL_LOGIC, ClaimState.FRAME_DECLARED),
    _case("FF_05", FrameCategory.F_FORMAL_LOGIC,
          "Frame: formal logic. P and not-P entails any proposition.",
          FrameKind.FORMAL_LOGIC, ClaimState.FRAME_DECLARED),
)

# Category G — empirical causal
G_CASES = (
    _case("FG_01", FrameCategory.G_EMPIRICAL_CAUSAL,
          "Heavy rainfall causes localised flooding.",
          FrameKind.EMPIRICAL_CAUSAL, ClaimState.FRAME_DECLARED),
    _case("FG_02", FrameCategory.G_EMPIRICAL_CAUSAL,
          "Power outages led to data loss in the cluster.",
          FrameKind.EMPIRICAL_CAUSAL, ClaimState.FRAME_DECLARED),
    _case("FG_03", FrameCategory.G_EMPIRICAL_CAUSAL,
          "Inflation rose because of supply-chain disruptions.",
          FrameKind.EMPIRICAL_CAUSAL, ClaimState.FRAME_DECLARED),
    _case("FG_04", FrameCategory.G_EMPIRICAL_CAUSAL,
          "Delayed shipments results in stockouts at retailers.",
          FrameKind.EMPIRICAL_CAUSAL, ClaimState.FRAME_DECLARED),
    _case("FG_05", FrameCategory.G_EMPIRICAL_CAUSAL,
          "Crop failure was due to prolonged drought conditions.",
          FrameKind.EMPIRICAL_CAUSAL, ClaimState.FRAME_DECLARED),
)

# Category H — undeclared or conflict
H_CASES = (
    _case("FH_01", FrameCategory.H_UNDECLARED_OR_CONFLICT,
          "Entropy increases in any closed system over time.",
          FrameKind.FRAME_UNDECLARED, ClaimState.FRAME_CONFLICT),
    _case("FH_02", FrameCategory.H_UNDECLARED_OR_CONFLICT,
          "The fox jumped over the lazy dog.",
          FrameKind.FRAME_UNDECLARED, ClaimState.FRAME_UNDECLARED),
    _case("FH_03", FrameCategory.H_UNDECLARED_OR_CONFLICT,
          "Quality is hard to define.",
          FrameKind.FRAME_UNDECLARED, ClaimState.FRAME_UNDECLARED),
    _case("FH_04", FrameCategory.H_UNDECLARED_OR_CONFLICT,
          "Mutual information about heat suggests new entropy bounds.",
          FrameKind.FRAME_UNDECLARED, ClaimState.FRAME_CONFLICT),
    _case("FH_05", FrameCategory.H_UNDECLARED_OR_CONFLICT,
          "A unique experience.",
          FrameKind.FRAME_UNDECLARED, ClaimState.FRAME_UNDECLARED),
)


ALL_FRAME_CASES: tuple[FrameBenchmarkCase, ...] = (
    A_CASES + B_CASES + C_CASES + D_CASES
    + E_CASES + F_CASES + G_CASES + H_CASES
)


def cases_by_category(
    category: FrameCategory,
) -> tuple[FrameBenchmarkCase, ...]:
    return tuple(c for c in ALL_FRAME_CASES if c.category is category)


__all__ = [
    "ALL_FRAME_CASES",
    "A_CASES", "B_CASES", "C_CASES", "D_CASES",
    "E_CASES", "F_CASES", "G_CASES", "H_CASES",
    "cases_by_category",
]

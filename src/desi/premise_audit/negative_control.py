"""Aufgabe 7 — synthetic negative-control bank for the
extractor signal audit.

Fifty chains across five shapes:

* ``syntactically_clean_but_logically_false`` — perfectly
  formed premises/conclusion, factually wrong outcome. Should
  NOT be flagged on extraction signals (signals are about
  form, not truth).
* ``logically_valid_but_linguistically_chaotic`` — valid causal
  reasoning expressed with shifting tenses, sub-clauses, mixed
  punctuation. Should be flagged on extraction_drop_rate or
  paraphrase_instability.
* ``paraphrase_drift`` — three near-identical claims with
  small word changes that the extractor should treat
  identically. Should NOT be flagged.
* ``premise_loss`` — chain whose premises are run-on
  sentences the extractor cannot split; flagged on
  premise_count or extraction_drop_rate.
* ``conclusion_inflation`` — long, multi-clause conclusion;
  flagged on conclusion_token_count.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NCShape(str, Enum):
    CLEAN_BUT_FALSE          = "syntactically_clean_but_logically_false"
    VALID_BUT_CHAOTIC        = "logically_valid_but_linguistically_chaotic"
    PARAPHRASE_DRIFT         = "paraphrase_drift"
    PREMISE_LOSS             = "premise_loss"
    CONCLUSION_INFLATION     = "conclusion_inflation"


@dataclass(frozen=True)
class NCChain:
    case_id: str
    text: str
    shape: NCShape
    expected_anomalous: bool


def _nc(case_id: str, text: str, shape: NCShape,
        anomalous: bool) -> NCChain:
    return NCChain(case_id=case_id, text=text, shape=shape,
                   expected_anomalous=anomalous)


_CLEAN_BUT_FALSE = tuple(
    _nc(f"CBF{i:02d}", t, NCShape.CLEAN_BUT_FALSE, False)
    for i, t in enumerate((
        "The bread rose. The oven heated. "
        "Therefore the loaf came out raw.",
        "The bell rang. The children arrived. "
        "Therefore class was cancelled.",
        "Rain fell overnight. Roads stayed dry. "
        "Therefore the desert flooded.",
        "The kettle boiled. Steam appeared. "
        "Therefore the tea remained cold.",
        "Pollen drifted onto stigma. The ovary swelled. "
        "Therefore the flower withered before bloom.",
        "The sail filled with wind. The hull leaned over. "
        "Therefore the yacht sank at the dock.",
        "The kiln heated to cone six. The glaze melted. "
        "Therefore the bowl shattered into dust.",
        "The athlete sprinted to the line. Sweat ran down. "
        "Therefore she came in last by far.",
        "The painter mixed indigo and white. "
        "The brush flowed across canvas. "
        "Therefore the painting turned out black.",
        "The library stamped the date. The patron left. "
        "Therefore the loan record disappeared.",
    ), start=1)
)


_VALID_BUT_CHAOTIC = tuple(
    _nc(f"VBC{i:02d}", t, NCShape.VALID_BUT_CHAOTIC, True)
    for i, t in enumerate((
        "Heat — flowed — into the room; steam (visible) gathered "
        "near the window. Therefore the air became hot, said the cook.",
        "Birds, having migrated, settled in southern fields—where "
        "they fed, then nested. Therefore offspring eventually arrived.",
        "Snow! Cold! Wind!! Frost crept across the panes. "
        "Therefore the morning broke icy: very, very icy.",
        "The runner—exhausted, dehydrated, still resolute—pushed on. "
        "Hours passed; nightfall came. Therefore she finished, "
        "barely, by midnight.",
        "Smoke (curling, blue, ash-grey) rose; the alarm wailed; "
        "evacuation began. Therefore the building, fortunately, "
        "emptied in time.",
        "Stars: thousands of them; constellations, planets, dust. "
        "The astronomer traced them all. Therefore the chart "
        "filled out, slowly, by dawn.",
        "Strings—taut, polished—were tuned, tested, then released. "
        "Music followed. Therefore the recital, despite jitters, "
        "ended in applause.",
        "Pollen blew across the orchard (everywhere, ceaselessly); "
        "fruit set; harvest neared. Therefore the cellars filled, "
        "as expected, by autumn's end.",
        "The dam (built, tested, certified) held back floodwaters. "
        "Reservoirs filled. Therefore drinking water, in plain terms, "
        "stayed plentiful.",
        "The kiln blazed; clay hardened; glaze melted, smoothed, set. "
        "Therefore the vessel, lifted from the heat, gleamed.",
    ), start=1)
)


_PARAPHRASE_DRIFT = tuple(
    _nc(f"PFD{i:02d}", t, NCShape.PARAPHRASE_DRIFT, False)
    for i, t in enumerate((
        "The kettle whistled. Steam filled the room. "
        "Therefore the tea was ready.",
        "The kettle whistled loudly. Steam filled the room. "
        "Therefore the tea was ready.",
        "The kettle whistled. Steam filled the small room. "
        "Therefore the tea was ready.",
        "The kettle whistled. Steam quickly filled the room. "
        "Therefore the tea was ready.",
        "The kettle whistled. Steam filled the room. "
        "Therefore the tea was finally ready.",
        "Bees fanned the hive. The colony cooled. "
        "Therefore midsummer passed safely.",
        "Bees gently fanned the hive. The colony cooled. "
        "Therefore midsummer passed safely.",
        "Bees fanned the busy hive. The colony cooled. "
        "Therefore midsummer passed safely.",
        "Bees fanned the hive. The colony cooled quickly. "
        "Therefore midsummer passed safely.",
        "Bees fanned the hive. The colony cooled. "
        "Therefore the long midsummer passed safely.",
    ), start=1)
)


_PREMISE_LOSS = tuple(
    _nc(f"PML{i:02d}", t, NCShape.PREMISE_LOSS, True)
    for i, t in enumerate((
        # Comma-joined run-on premises — the extractor cannot
        # split on commas so they collapse into one ATOMIC
        # premise, dropping chain structure.
        "The kettle whistled, steam filled the room, tea brewed. "
        "Therefore breakfast was served.",
        "Bees fanned the hive, honey thickened in the comb, workers "
        "sealed the cells. Therefore the colony cooled.",
        "Pollen drifted onto the stigma, the ovary swelled, the "
        "tulip set seed. Therefore the harvest neared.",
        "The dam broke, water rushed through the valley, crops were "
        "destroyed. Therefore the village evacuated.",
        "The kiln reached cone six, glaze melted across the surface, "
        "the vessel cooled. Therefore the pot fired.",
        "The runner crossed the line, sweat ran down her brow, the "
        "crowd cheered. Therefore the race ended.",
        "Smoke rose from the kitchen, flames spread through the "
        "curtains, alarms wailed. Therefore evacuation began.",
        "The painter mixed cobalt, pigment thinned with oil, the "
        "brush flowed smoothly. Therefore the canvas filled.",
        "The flute played in tune, the cellist drew her bow, the "
        "conductor signalled. Therefore the symphony began.",
        "The library opened at nine, patrons arrived in numbers, "
        "the bell chimed. Therefore reading began.",
    ), start=1)
)


_CONCLUSION_INFLATION = tuple(
    _nc(f"CCI{i:02d}", t, NCShape.CONCLUSION_INFLATION, True)
    for i, t in enumerate((
        "The kettle whistled. Steam appeared. "
        "Therefore the tea, brewed carefully over many minutes by a "
        "patient hand, was poured into the heirloom cup that "
        "belonged to her late grandmother.",
        "The bell rang. Children entered. "
        "Therefore the morning class, with its many subjects, "
        "complicated lessons, and varied discussions, began on time "
        "despite the rain that had threatened all morning.",
        "Bees fanned the hive. Honey thickened. "
        "Therefore the apiary, long managed by three generations of "
        "beekeepers in the village near the river, produced its "
        "annual harvest in record-breaking quantity.",
        "Pollen drifted. The ovary swelled. "
        "Therefore the tulip, planted last autumn by the gardener "
        "after careful selection of soil and depth, eventually "
        "bloomed into the brightest scarlet seen in years.",
        "The sail filled. The hull leaned. "
        "Therefore the racing yacht, with its experienced crew of "
        "five sailors from three different harbours, crossed the "
        "finish line ahead of the entire competing fleet of twelve.",
        "Smoke rose. The alarm wailed. "
        "Therefore the office building, where forty-seven workers "
        "had been seated at their morning meeting, evacuated within "
        "the legally mandated three minutes without injury or loss.",
        "The dam broke. The valley flooded. "
        "Therefore the downstream town, whose residents had been "
        "warned three days earlier by the regional emergency office, "
        "abandoned the lower district in time to avoid casualties.",
        "Wind blew across the field. Snow drifted. "
        "Therefore the winter crop, sowed late by the new farmer "
        "who had taken over the land after the previous owner's "
        "retirement, suffered substantial damage that year.",
        "The musician tuned the strings. The orchestra played. "
        "Therefore the symphony, conducted by the visiting maestro "
        "from a city across two oceans, received standing ovations "
        "from the entire audience for nearly seven minutes.",
        "The painter mixed cobalt. The brush flowed. "
        "Therefore the portrait, of the elderly judge in her "
        "ceremonial robes painted entirely from a single afternoon "
        "sitting, became the gallery's most acclaimed work that year.",
    ), start=1)
)


ALL_NC_CHAINS: tuple[NCChain, ...] = (
    _CLEAN_BUT_FALSE
    + _VALID_BUT_CHAOTIC
    + _PARAPHRASE_DRIFT
    + _PREMISE_LOSS
    + _CONCLUSION_INFLATION
)


__all__ = ["ALL_NC_CHAINS", "NCChain", "NCShape"]

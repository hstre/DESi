"""Aufgabe 4 — synthetic naturalness negative-control bank.

Sixty chains across four shapes:

* ``natural_but_false`` — natural-sounding causal flow whose
  conclusion is factually wrong (should *not* be flagged on
  naturalness alone — the manifold is about distribution, not
  truth).
* ``valid_but_sparse`` — short, terse causal chains with few
  markers (should be accepted: naturally sparse).
* ``over_explained_but_true`` — true conclusions with stacked
  authority / metaphor / quantifier markers (should be flagged
  as *over-explained* even though true).
* ``weird_marker_free`` — non-sequiturs with no markers (should
  be flagged because the *distribution* is anomalous even
  without lexical evidence).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NCShape(str, Enum):
    NATURAL_BUT_FALSE       = "natural_but_false"
    VALID_BUT_SPARSE        = "valid_but_sparse"
    OVER_EXPLAINED_BUT_TRUE = "over_explained_but_true"
    WEIRD_MARKER_FREE       = "weird_marker_free"


@dataclass(frozen=True)
class NCChain:
    case_id: str
    text: str
    shape: NCShape
    expected_natural: bool

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "case_id": self.case_id, "text": self.text,
            "shape": self.shape.value,
            "expected_natural": self.expected_natural,
        }


def _nc(case_id: str, text: str, shape: NCShape,
        natural: bool) -> NCChain:
    return NCChain(case_id=case_id, text=text, shape=shape,
                   expected_natural=natural)


_NATURAL_BUT_FALSE: tuple[NCChain, ...] = (
    _nc("NBF01",
        "Snow fell on the rooftop. Icicles formed at the eaves. "
        "Water dripped onto the porch. Therefore the porch grew warmer.",
        NCShape.NATURAL_BUT_FALSE, True),
    _nc("NBF02",
        "Bees fanned the hive. Honey thickened in the comb. "
        "Workers sealed each cell. Therefore the colony lost its queen.",
        NCShape.NATURAL_BUT_FALSE, True),
    _nc("NBF03",
        "The athlete sprinted around the track. Sweat ran down her brow. "
        "She crossed the finish line first. Therefore she finished last.",
        NCShape.NATURAL_BUT_FALSE, True),
    _nc("NBF04",
        "The seedling pushed through the soil. Leaves unfurled in light. "
        "Roots reached for water. Therefore the plant withered.",
        NCShape.NATURAL_BUT_FALSE, True),
    _nc("NBF05",
        "Wind filled the sail steadily. The hull cut through swell. "
        "The crew trimmed the lines. Therefore the boat sank.",
        NCShape.NATURAL_BUT_FALSE, True),
    _nc("NBF06",
        "The orchard bloomed in spring. Bees pollinated each flower. "
        "Fruit set on the branches. Therefore the harvest failed.",
        NCShape.NATURAL_BUT_FALSE, True),
    _nc("NBF07",
        "The bread proofed overnight. The oven heated to baking "
        "temperature. The loaf rose in the tin. Therefore the bread "
        "stayed raw.",
        NCShape.NATURAL_BUT_FALSE, True),
    _nc("NBF08",
        "Rivers swelled with rain. The dam held back the flow. "
        "Reservoirs filled to capacity. Therefore the city ran dry.",
        NCShape.NATURAL_BUT_FALSE, True),
    _nc("NBF09",
        "Light entered the lens. The sensor captured photons. "
        "The image developed on screen. Therefore the picture was blank.",
        NCShape.NATURAL_BUT_FALSE, True),
    _nc("NBF10",
        "The kiln reached firing temperature. Glaze melted onto clay. "
        "The vessel cooled overnight. Therefore the bowl shattered.",
        NCShape.NATURAL_BUT_FALSE, True),
    _nc("NBF11",
        "The actor rehearsed nightly. The lines became second nature. "
        "Opening night arrived. Therefore the actor forgot every line.",
        NCShape.NATURAL_BUT_FALSE, True),
    _nc("NBF12",
        "Threads were dyed in indigo. The loom shuttled back and forth. "
        "A pattern emerged in the weave. Therefore the cloth turned "
        "white.",
        NCShape.NATURAL_BUT_FALSE, True),
)


_VALID_BUT_SPARSE: tuple[NCChain, ...] = (
    _nc("VBS01",
        "The bell rang. The children entered. "
        "Therefore class began.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS02",
        "Smoke rose from the kitchen. The cook turned the heat down. "
        "Therefore the pan cooled.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS03",
        "The clock struck noon. The shop opened. "
        "Therefore customers walked in.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS04",
        "The shutter clicked. Light entered the camera. "
        "Therefore the film captured the scene.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS05",
        "Frost coated the windows. The driver scraped the glass. "
        "Therefore the view cleared.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS06",
        "The whistle blew. The runners sprinted forward. "
        "Therefore the race began.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS07",
        "The gate creaked open. The dog raced through. "
        "Therefore the garden lost a flower bed.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS08",
        "The pot simmered slowly. The flavours deepened. "
        "Therefore dinner tasted rich.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS09",
        "A spark ignited dry grass. Flames spread across the meadow. "
        "Therefore the field charred.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS10",
        "The conductor raised the baton. The orchestra played the "
        "opening note. Therefore the symphony began.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS11",
        "Snow piled on the roof. The beams groaned. "
        "Therefore tiles fell to the street.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS12",
        "The painter mixed turpentine into oil. The pigment thinned. "
        "Therefore the brush flowed smoothly.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS13",
        "The horse galloped down the lane. Hooves stirred the dust. "
        "The rider shouted. Therefore the gate opened.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS14",
        "The shopkeeper unlocked the door. A bell jingled overhead. "
        "Light flooded the aisle. Therefore the morning trade began.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS15",
        "The phone rang in the office. The clerk answered. "
        "A message was relayed. Therefore the order was confirmed.",
        NCShape.VALID_BUT_SPARSE, True),
    _nc("VBS16",
        "The pencil snapped under pressure. Lead scattered on the desk. "
        "Therefore the sketch was abandoned.",
        NCShape.VALID_BUT_SPARSE, True),
)


_OVER_EXPLAINED_BUT_TRUE: tuple[NCChain, ...] = (
    _nc("OET01",
        "Loosely speaking, every kettle whistles when steam pressure "
        "rises. The minister stated water boiled at one hundred "
        "degrees. The expert wrote that thermodynamics is invariant. "
        "Therefore the tea brewed.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
    _nc("OET02",
        "All seedlings need water universally. The botanist noted "
        "every plant requires sunlight. The expert argued sunlight is "
        "a metaphor. Therefore the garden bloomed.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
    _nc("OET03",
        "Every dough rises consistently. The baker wrote that yeast "
        "is invariably needed. According to tradition, bread is a "
        "staple. Therefore the loaf baked golden.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
    _nc("OET04",
        "All wires conduct universally. The engineer felt the circuit "
        "is a system. The technician stated current flows always. "
        "Therefore the bulb lit.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
    _nc("OET05",
        "Every chord vibrates throughout. The cellist argued music is "
        "a metaphor. The conductor wrote pitch is invariant. "
        "Therefore the orchestra tuned.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
    _nc("OET06",
        "Some chemicals react universally. The chemist noted reactions "
        "are constant. The lab director stated catalysts always act. "
        "Therefore the experiment succeeded.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
    _nc("OET07",
        "All bridges hold loads consistently. The architect wrote that "
        "steel is a material. The engineer argued tension is invariant. "
        "Therefore the bridge stood.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
    _nc("OET08",
        "Every pollinator works universally. The botanist suggested "
        "flowers are a temptation. The minister announced bees are "
        "vital. Therefore the orchard fruited.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
    _nc("OET09",
        "Loosely speaking, all clocks tick universally. The watchmaker "
        "wrote time is a river. The historian argued seconds invariably "
        "follow. Therefore the hour struck.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
    _nc("OET10",
        "Every recipe requires salt consistently. The chef stated salt "
        "is a foundation. The expert wrote that seasoning is invariably "
        "necessary. Therefore the dish tasted right.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
    _nc("OET11",
        "All compasses point universally. The navigator wrote magnetism "
        "is a constant. The captain felt north is always reliable. "
        "Therefore the ship reached harbour.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
    _nc("OET12",
        "Every brushstroke matters consistently. The painter argued "
        "art is a discipline. The critic noted colour is invariant. "
        "Therefore the canvas filled.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
    _nc("OET13",
        "Loosely speaking, every wave breaks always. The surfer wrote "
        "the ocean is a teacher. The expert argued tides are invariant. "
        "Therefore the surfer rode home.",
        NCShape.OVER_EXPLAINED_BUT_TRUE, False),
)


_WEIRD_MARKER_FREE: tuple[NCChain, ...] = (
    _nc("WMF01",
        "The kettle whistled softly. A bell rang at noon. "
        "Therefore the harbour lights flickered at midnight.",
        NCShape.WEIRD_MARKER_FREE, False),
    _nc("WMF02",
        "Tulips opened in the garden. The clock chimed twice. "
        "Therefore the freight train rumbled through the valley.",
        NCShape.WEIRD_MARKER_FREE, False),
    _nc("WMF03",
        "The painter prepped the canvas. Bees fanned the hive. "
        "Therefore the violinist tuned for an encore.",
        NCShape.WEIRD_MARKER_FREE, False),
    _nc("WMF04",
        "Honey dripped from the comb. A pebble skipped across the "
        "pond. Therefore the bookkeeper closed the ledger.",
        NCShape.WEIRD_MARKER_FREE, False),
    _nc("WMF05",
        "The photograph developed slowly. Wind rattled the shutters. "
        "Therefore the navigator marked the chart.",
        NCShape.WEIRD_MARKER_FREE, False),
    _nc("WMF06",
        "A cellist tuned the strings. A baker kneaded dough. "
        "Therefore the astronomer recorded a transit.",
        NCShape.WEIRD_MARKER_FREE, False),
    _nc("WMF07",
        "The library stamped a date. A potter wedged clay. "
        "Therefore the rower crossed the finish line.",
        NCShape.WEIRD_MARKER_FREE, False),
    _nc("WMF08",
        "Pollen drifted onto a stigma. A potter glazed a bowl. "
        "Therefore the photographer flashed the studio.",
        NCShape.WEIRD_MARKER_FREE, False),
    _nc("WMF09",
        "Sails caught a breeze. A cheese ripened in the cave. "
        "Therefore the conductor finished the rehearsal.",
        NCShape.WEIRD_MARKER_FREE, False),
    _nc("WMF10",
        "The comet entered the inner system. A weaver threaded the "
        "loom. Therefore the chef poured the broth.",
        NCShape.WEIRD_MARKER_FREE, False),
    _nc("WMF11",
        "An origami crane took shape. A baker proofed the boule. "
        "Therefore the auditor signed off on the books.",
        NCShape.WEIRD_MARKER_FREE, False),
    _nc("WMF12",
        "The bonsai sprouted a new leaf. The cobbler stitched the "
        "shoe. Therefore the carpenter sanded the bench.",
        NCShape.WEIRD_MARKER_FREE, False),
    _nc("WMF13",
        "A blacksmith hammered an iron rod. A poet drafted a stanza. "
        "Therefore the engineer recalibrated the lens.",
        NCShape.WEIRD_MARKER_FREE, False),
)


ALL_NC_CHAINS: tuple[NCChain, ...] = (
    _NATURAL_BUT_FALSE
    + _VALID_BUT_SPARSE
    + _OVER_EXPLAINED_BUT_TRUE
    + _WEIRD_MARKER_FREE
)


__all__ = [
    "ALL_NC_CHAINS",
    "NCChain",
    "NCShape",
]

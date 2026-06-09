"""Deterministic tools for the DESi router catalogue.

Each tool is a pure function ``str -> result`` that parses a constrained pattern
and raises on anything it cannot handle — an honest boundary: an unparseable
query is a language problem the router would hand back to a model, not something
the tool guesses at.
"""
from desi_router.tools.datemath import solve_date
from desi_router.tools.retrieval import make_keyword_search
from desi_router.tools.units import convert_units

__all__ = ["solve_date", "convert_units", "make_keyword_search"]

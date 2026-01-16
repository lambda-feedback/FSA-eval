"""FSA Correction Module

Compares student FSAs against expected FSAs.

Exports:
- analyze_fsa_correction: Main pipeline (FSA vs FSA -> Result)
- check_minimality: Check if FSA is minimal
"""

from .correction import (
    analyze_fsa_correction,
    check_minimality,
)

__all__ = [
    "analyze_fsa_correction",
    "check_minimality",
]

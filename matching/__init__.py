"""
Modul: KI-Matching und Fristverwaltung
Ermöglicht den KI-gestützten Abgleich von Projekten mit Förderprogrammen.
"""

from .project_matcher import ProjectMatcher
from .deadline_engine import DeadlineEngine

__all__ = ["ProjectMatcher", "DeadlineEngine"]

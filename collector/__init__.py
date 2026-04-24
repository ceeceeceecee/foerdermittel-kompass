"""
Modul: Förderprogramm-Sammler
Ermöglicht das automatisierte Erfassen von Förderprogrammen aus verschiedenen Quellen.
"""

from .program_collector import ProgramCollector
from .source_parsers import RSSParser, HTMLParser, CSVParser, Foerderprogramm

__all__ = ["ProgramCollector", "RSSParser", "HTMLParser", "CSVParser", "Foerderprogramm"]

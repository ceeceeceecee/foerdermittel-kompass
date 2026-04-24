"""
Förderprogramm-Sammler
Zentrale Klasse zum Erfassen, Normalisieren und Deduplizieren von Förderprogrammen
aus verschiedenen Quellen (RSS, HTML, CSV).
"""

import logging
import time
from typing import Optional

import yaml

from .source_parsers import RSSParser, HTMLParser, CSVParser, Foerderprogramm

logger = logging.getLogger(__name__)


class ProgramCollector:
    """
    Sammelt Förderprogramme aus konfigurierten Quellen und bereitet sie auf.
    """

    # Mindestverzögerung zwischen Anfragen in Sekunden (Rate-Limiting)
    MINDEST_VERZOEGERUNG = 2.0

    def __init__(self, konfig_pfad: str = "config/sources.yaml"):
        """
        Initialisiert den Sammler.

        Parameter:
            konfig_pfad: Pfad zur YAML-Quellkonfiguration
        """
        self.konfig_pfad = konfig_pfad
        self.rss_parser = RSSParser()
        self.html_parser = HTMLParser()
        self.csv_parser = CSVParser()
        self.programme: list[Foerderprogramm] = []
        self.hash_index: dict[str, Foerderprogramm] = {}

    def lade_konfiguration(self) -> dict:
        """Lädt die Quellkonfiguration aus der YAML-Datei."""
        try:
            with open(self.konfig_pfad, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning("Quellkonfiguration nicht gefunden: %s", self.konfig_pfad)
            return {"quellen": []}

    def fetch_sources(self) -> list[Foerderprogramm]:
        """
        Ruft alle konfigurierten Quellen ab und sammelt Förderprogramme.

        Rückgabe:
            Liste der gefundenen Förderprogramme
        """
        konfig = self.lade_konfiguration()
        quellen = konfig.get("quellen", [])
        alle_programme = []

        for quelle in quellen:
            quelltyp = quelle.get("typ", "").lower()
            url_oder_pfad = quelle.get("url", quelle.get("datei", ""))

            if not url_oder_pfad:
                logger.warning("Quelle ohne URL/Datei übersprungen")
                continue

            logger.info("Rufe Quelle ab: %s (%s)", url_oder_pfad, quelltyp)

            try:
                if quelltyp == "rss":
                    programme = self.rss_parser.parse(url_oder_pfad)
                elif quelltyp == "html":
                    selektoren = quelle.get("selektoren", {})
                    programme = self.html_parser.parse(url_oder_pfad, selektoren)
                elif quelltyp == "csv":
                    programme = self.csv_parser.parse(url_oder_pfad)
                else:
                    logger.warning("Unbekannter Quelltyp: %s", quelltyp)
                    continue

                logger.info("%d Programme aus %s geladen", len(programme), url_oder_pfad)
                alle_programme.extend(programme)
            except Exception as e:
                logger.error("Fehler beim Abruf von %s: %s", url_oder_pfad, e)

            # Rate-Limiting
            time.sleep(self.MINDEST_VERZOEGERUNG)

        return alle_programme

    def parse_programs(self) -> list[Foerderprogramm]:
        """
        Kombiniert Abruf, Normalisierung und Deduplizierung.

        Rückgabe:
            Bereinigte Liste eindeutiger Förderprogramme
        """
        rohe_programme = self.fetch_sources()
        normalisiert = self.normalize_fields(rohe_programme)
        einzigartig = self.deduplicate(normalisiert)
        self.programme = einzigartig
        logger.info("Sammlung abgeschlossen: %d eindeutige Programme", len(einzigartig))
        return einzigartig

    def normalize_fields(self, programme: list[Foerderprogramm]) -> list[Foerderprogramm]:
        """
        Normalisiert die Felder aller Programme (Fristformat, Fördersatz etc.).

        Parameter:
            programme: Liste der zu normalisierenden Programme

        Rückgabe:
            Normalisierte Programme
        """
        for prog in programme:
            # Fördersatz normalisieren
            prog.quote = self._normalisiere_quote(prog.quote)
            # Frist normalisieren
            prog.frist = self._normalisiere_frist(prog.frist)
            # Bundesland normalisieren
            prog.bundesland = self._normalisiere_bundesland(prog.bundesland)
            # Themenfeld normalisieren
            prog.themenfeld = self._normalisiere_themenfeld(prog.themenfeld)

        return programme

    def _normalisiere_quote(self, quote: str) -> str:
        """Normalisiert den Fördersatz."""
        if not quote:
            return ""
        quote = quote.strip()
        # Prozentzeichen entfernen und formatieren
        quote = quote.replace("%", "").strip()
        try:
            wert = float(quote)
            if wert <= 1:
                return f"{int(wert * 100)}%"
            return f"{int(wert)}%"
        except ValueError:
            return quote if quote else ""

    def _normalisiere_frist(self, frist: str) -> str:
        """Normalisiert das Fristdatum."""
        if not frist:
            return ""
        frist = frist.strip()
        # Verschiedene Formate versuchen
        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%y", "%Y/%m/%d"):
            try:
                from datetime import datetime
                datum = datetime.strptime(frist, fmt)
                return datum.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return frist

    def _normalisiere_bundesland(self, bundesland: str) -> str:
        """Normalisiert die Bundesland-Angabe."""
        if not bundesland:
            return "Alle"
        bundesland = bundesland.strip()
        abkuerzungen = {
            "BW": "Baden-Württemberg", "BY": "Bayern", "BE": "Berlin",
            "BB": "Brandenburg", "HB": "Bremen", "HH": "Hamburg",
            "HE": "Hessen", "MV": "Mecklenburg-Vorpommern", "NI": "Niedersachsen",
            "NW": "Nordrhein-Westfalen", "RP": "Rheinland-Pfalz", "SL": "Saarland",
            "SN": "Sachsen", "ST": "Sachsen-Anhalt", "SH": "Schleswig-Holstein",
            "TH": "Thüringen",
        }
        return abkuerzungen.get(bundesland.upper(), bundesland)

    def _normalisiere_themenfeld(self, themenfeld: str) -> str:
        """Normalisiert das Themenfeld."""
        if not themenfeld:
            return ""
        # Erster Buchstabe gross
        return themenfeld.strip().capitalize()

    def deduplicate(self, programme: list[Foerderprogramm]) -> list[Foerderprogramm]:
        """
        Entfernt doppelte Programme basierend auf einem Inhalts-Hash.

        Parameter:
            programme: Liste der zu prüfenden Programme

        Rückgabe:
            Liste ohne Duplikate (erstes Vorkommen bleibt erhalten)
        """
        einzigartig = []
        gesehene_hash = set()

        for prog in programme:
            h = prog.inhalts_hash()
            if h not in gesehene_hash:
                gesehene_hash.add(h)
                einzigartig.append(prog)
            else:
                logger.debug("Duplikat entfernt: %s", prog.titel)

        return einzigartig

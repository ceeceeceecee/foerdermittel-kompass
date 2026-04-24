"""
Parser für verschiedene Fördermittel-Quellen.
Unterstützt RSS-Feeds, HTML-Seiten und CSV-Importe.
"""

import csv
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests


@dataclass
class Foerderprogramm:
    """Datenstruktur für ein Förderprogramm."""
    titel: str = ""
    traeger: str = ""
    bundesland: str = ""
    themenfeld: str = ""
    frist: str = ""
    quote: str = ""
    link: str = ""
    beschreibung: str = ""
    quelle: str = ""
    abgerufen_am: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Konvertiert das Programm in ein Dictionary."""
        return {
            "titel": self.titel,
            "traeger": self.traeger,
            "bundesland": self.bundesland,
            "themenfeld": self.themenfeld,
            "frist": self.frist,
            "quote": self.quote,
            "link": self.link,
            "beschreibung": self.beschreibung,
            "quelle": self.quelle,
            "abgerufen_am": self.abgerufen_am,
        }

    def inhalts_hash(self) -> str:
        """Erzeugt einen Hash des Inhalts zur Duplikat-Erkennung."""
        inhalt = f"{self.titel}|{self.traeger}|{self.frist}"
        return hashlib.sha256(inhalt.encode("utf-8")).hexdigest()[:16]


class BasisParser:
    """Basisklasse für alle Quell-Parser."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Foerdermittel-Kompass/1.0 (kommunaler-Foerder-Checker)",
        })

    def pruefe_robots_txt(self, url: str) -> bool:
        """Prüft die robots.txt, ob die URL gecrawlt werden darf."""
        try:
            rp = RobotFileParser()
            rp.set_url(urljoin(url, "/robots.txt"))
            rp.read()
            return rp.can_fetch(self.session.headers["User-Agent"], url)
        except Exception:
            # Im Zweifel erlauben
            return True

    def lade_seite(self, url: str) -> Optional[str]:
        """Lädt den Inhalt einer URL herunter."""
        if not self.pruefe_robots_txt(url):
            return None
        try:
            antwort = self.session.get(url, timeout=self.timeout)
            antwort.raise_for_status()
            return antwort.text
        except requests.RequestException:
            return None


class RSSParser(BasisParser):
    """Parser für RSS/Atom-Feeds von Fördermittel-Seiten."""

    def parse(self, feed_url: str) -> list:
        """Parst einen RSS-Feed und extrahiert Förderprogramme."""
        try:
            import xml.etree.ElementTree as ET
        except ImportError:
            return []

        inhalt = self.lade_seite(feed_url)
        if not inhalt:
            return []

        programme = []
        try:
            root = ET.fromstring(inhalt)
            # RSS 2.0
            eintraege = root.findall(".//item")
            if not eintraege:
                # Atom Feed
                eintraege = root.findall(".//{http://www.w3.org/2005/Atom}entry")

            for eintrag in eintraege:
                titel = self._extrahiere_text(eintrag, "title")
                link = self._extrahiere_text(eintrag, "link")
                beschreibung = self._extrahiere_text(eintrag, "description") or self._extrahiere_text(eintrag, "summary")

                if titel:
                    programme.append(Foerderprogramm(
                        titel=titel.strip(),
                        link=link or feed_url,
                        beschreibung=self._bereinige_html(beschreibung or ""),
                        quelle=feed_url,
                    ))
        except ET.ParseError:
            pass

        return programme

    def _extrahiere_text(self, element, tag):
        """Extrahiert Text aus einem XML-Element."""
        kind = element.find(tag)
        if kind is not None and kind.text:
            return kind.text.strip()
        return None

    def _bereinige_html(self, text: str) -> str:
        """Entfernt HTML-Tags aus einem Text."""
        return re.sub(r"<[^>]+>", "", text).strip()


class HTMLParser(BasisParser):
    """Parser für HTML-Seiten mit Förderprogrammen."""

    def parse(self, url: str, selektoren: dict = None) -> list:
        """
        Parst eine HTML-Seite basierend auf CSS-Selektoren.

        Parameter:
            url: Die zu parsende URL
            selektoren: Dictionary mit Selektoren:
                - container: CSS-Selektor für Programm-Container
                - titel: Selektor für den Titel innerhalb des Containers
                - beschreibung: Selektor für die Beschreibung
                - link: Selektor für den Link
                - frist: Selektor für die Frist
        """
        if selektoren is None:
            selektoren = {}

        inhalt = self.lade_seite(url)
        if not inhalt:
            return []

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return []

        suppe = BeautifulSoup(inhalt, "html.parser")
        container_selektor = selektoren.get("container", "article, .foerderung, .program")
        container = suppe.select(container_selektor)

        programme = []
        for element in container:
            titel_el = element.select_one(selektoren.get("titel", "h2, h3, .title"))
            beschreibung_el = element.select_one(selektoren.get("beschreibung", "p, .description"))
            link_el = element.select_one(selektoren.get("link", "a[href]"))
            frist_el = element.select_one(selektoren.get("frist", ".deadline, .frist, time"))

            titel = titel_el.get_text(strip=True) if titel_el else ""
            if not titel:
                continue

            link = ""
            if link_el and link_el.get("href"):
                link = urljoin(url, link_el["href"])

            programme.append(Foerderprogramm(
                titel=titel,
                beschreibung=beschreibung_el.get_text(strip=True) if beschreibung_el else "",
                link=link,
                frist=frist_el.get_text(strip=True) if frist_el else "",
                quelle=url,
            ))

        return programme


class CSVParser:
    """Parser für CSV-Dateien mit Förderprogrammen."""

    ERFORDERLICHE_SPALTEN = ["titel"]

    def parse(self, dateipfad: str) -> list:
        """Liest eine CSV-Datei und erstellt Förderprogramm-Objekte."""
        programme = []
        try:
            with open(dateipfad, "r", encoding="utf-8") as f:
                leser = csv.DictReader(f)
                for zeile in leser:
                    titel = zeile.get("titel", "").strip()
                    if not titel:
                        continue
                    programme.append(Foerderprogramm(
                        titel=titel,
                        traeger=zeile.get("traeger", ""),
                        bundesland=zeile.get("bundesland", ""),
                        themenfeld=zeile.get("themenfeld", ""),
                        frist=zeile.get("frist", ""),
                        quote=zeile.get("quote", ""),
                        link=zeile.get("link", ""),
                        beschreibung=zeile.get("beschreibung", ""),
                        quelle=dateipfad,
                    ))
        except (FileNotFoundError, UnicodeDecodeError):
            pass
        return programme

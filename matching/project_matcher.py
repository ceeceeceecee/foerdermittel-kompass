"""
Projekt-Matcher mit lokaler KI (Ollama)
Prüft die Übereinstimmung von Projektvorhaben mit Förderprogrammen.
DSGVO-konform: Alle Daten bleiben lokal, kein Cloud-Dienst.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Standard-Konfiguration
STANDARD_OLLAMA_HOST = os.getenv("OLLAMA_HOST", os.getenv("OLLAMA_HOST", "http://localhost:11434"))
STANDARD_MODell = os.getenv("MODEL_NAME", "llama3")
PROMPT_VERZEICHNIS = Path(__file__).parent.parent / "prompts"


class ProjectMatcher:
    """
    KI-gestützter Abgleich von Projektvorhaben mit Förderprogrammen.
    Verwendet Ollama (lokal) — keine Clouddienste, voll DSGVO-konform.
    """

    def __init__(self, ollama_host: str = None, modell: str = None):
        """
        Initialisiert den Matcher.

        Parameter:
            ollama_host: URL des lokalen Ollama-Servers
            modell: Name des zu verwendenden KI-Modells
        """
        self.ollama_host = ollama_host or STANDARD_OLLAMA_HOST
        self.modell = modell or STANDARD_MODell
        self.prompt_verzeichnis = PROMPT_VERZEICHNIS

    def _lade_prompt(self, dateiname: str) -> str:
        """Lädt einen Prompt aus einer Textdatei."""
        pfad = self.prompt_verzeichnis / dateiname
        try:
            return pfad.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("Prompt-Datei nicht gefunden: %s", pfad)
            return ""

    def _ollama_anfrage(self, system_prompt: str, nutzer_prompt: str) -> Optional[str]:
        """
        Sendet eine Anfrage an den lokalen Ollama-Server.

        Parameter:
            system_prompt: System-Prompt mit Anweisungen
            nutzer_prompt: Nutzer-Prompt mit den konkreten Daten

        Rückgabe:
            Antwort des Modells als Text oder None bei Fehler
        """
        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": self.modell,
            "prompt": f"{system_prompt}\n\n{nutzer_prompt}",
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 2000,
            },
        }

        try:
            antwort = requests.post(url, json=payload, timeout=120)
            antwort.raise_for_status()
            return antwort.json().get("response", "")
        except requests.ConnectionError:
            logger.error("Ollama nicht erreichbar unter %s", self.ollama_host)
            return None
        except requests.Timeout:
            logger.error("Ollama-Anfrage timeout")
            return None
        except Exception as e:
            logger.error("Ollama-Fehler: %s", e)
            return None

    def _parse_json_antwort(self, antwort: str) -> Optional[dict]:
        """Extrahiert JSON aus einer KI-Antwort."""
        if not antwort:
            return None
        # Versuche, JSON-Block zu finden
        for start_marker in ["```json", "```"]:
            if start_marker in antwort:
                antwort = antwort.split(start_marker, 1)[1]
                break
        if "```" in antwort:
            antwort = antwort.split("```", 1)[0]
        antwort = antwort.strip()
        try:
            return json.loads(antwort)
        except json.JSONDecodeError:
            logger.warning("Konnte keine gültige JSON-Antwort parsen")
            return None

    def analyze_project(self, projekt_beschreibung: str) -> Optional[dict]:
        """
        Strukturiert eine Projektbeschreibung in formalisierbare Felder.

        Parameter:
            projekt_beschreibung: Freitext-Beschreibung des Projektvorhabens

        Rückgabe:
            Strukturierte Projektdaten oder None bei Fehler
        """
        system_prompt = self._lade_prompt("project_description.txt")
        if not system_prompt:
            system_prompt = (
                "Du bist ein Experte für Fördermittel in Deutschland. "
                "Strukturiere die folgende Projektbeschreibung in die Felder: "
                "ausgangslage, ziel, massnahmen, nutzen, wirkung. "
                "Antworte ausschliesslich im JSON-Format."
            )

        nutzer_prompt = (
            f"Bitte analysiere folgendes Projektvorhaben und strukturiere es:\n\n"
            f"{projekt_beschreibung}"
        )

        antwort = self._ollama_anfrage(system_prompt, nutzer_prompt)
        return self._parse_json_antwort(antwort)

    def score_program_fit(self, projekt_beschreibung: str, programme: list) -> list:
        """
        Bewertet die Übereinstimmung eines Projekts mit Förderprogrammen.

        Parameter:
            projekt_beschreibung: Beschreibung des Projektvorhabens
            programme: Liste der zu prüfenden Förderprogramme (Dictionaries)

        Rückgabe:
            Liste der Bewertungsergebnisse mit Score, Begründung und Risiken
        """
        system_prompt = self._lade_prompt("project_match.txt")
        if not system_prompt:
            system_prompt = (
                "Du bist ein Experte für Fördermittel in deutschen Kommunen. "
                "Prüfe objektiv, ob das Projekt zum Förderprogramm passt. "
                "Gib keinen Score von 100, wenn Unsicherheiten bestehen. "
                "Nenne klare Risiken und nächste Schritte. "
                "Antworte im JSON-Format mit: score (0-100), begruendung, "
                "risiken (Liste), next_steps (Liste)."
            )

        ergebnisse = []
        for prog in programme:
            prog_text = json.dumps(prog, ensure_ascii=False, indent=2)
            nutzer_prompt = (
                f"## Projektvorhaben\n{projekt_beschreibung}\n\n"
                f"## Förderprogramm\n{prog_text}\n\n"
                f"Bitte bewerte die Übereinstimmung."
            )

            antwort = self._ollama_anfrage(system_prompt, nutzer_prompt)
            bewertung = self._parse_json_antwort(antwort)

            if bewertung:
                bewertung["titel"] = prog.get("titel", "Unbekanntes Programm")
                # Score begrenzen
                try:
                    score = int(bewertung.get("score", 0))
                    bewertung["score"] = max(0, min(100, score))
                except (ValueError, TypeError):
                    bewertung["score"] = 0
                ergebnisse.append(bewertung)
            else:
                # Fallback bei KI-Fehler
                ergebnisse.append({
                    "titel": prog.get("titel", "Unbekannt"),
                    "score": 0,
                    "begruendung": "KI-Analyse nicht verfügbar",
                    "risiken": ["Manuelle Prüfung erforderlich"],
                    "next_steps": ["Programmrichtlinie prüfen"],
                })

        # Nach Score sortieren
        ergebnisse.sort(key=lambda x: x.get("score", 0), reverse=True)
        return ergebnisse

    def identify_gaps(self, projekt_beschreibung: str, programm: dict) -> list:
        """
        Identifiziert fehlende Voraussetzungen für einen Förderantrag.

        Parameter:
            projekt_beschreibung: Beschreibung des Projektvorhabens
            programm: Förderprogramm als Dictionary

        Rückgabe:
            Liste der identifizierten Lücken
        """
        system_prompt = (
            "Du bist ein Experte für Fördermittel in Deutschland. "
            "Identifiziere fehlende Voraussetzungen und Anforderungen, "
            "die für diesen Förderantrag noch erfüllt werden müssen. "
            "Antworte im JSON-Format mit einem Feld 'luecken' (Liste von Strings)."
        )

        nutzer_prompt = (
            f"## Projektvorhaben\n{projekt_beschreibung}\n\n"
            f"## Förderprogramm\n{json.dumps(programm, ensure_ascii=False)}\n\n"
            f"Welche Voraussetzungen fehlen noch?"
        )

        antwort = self._ollama_anfrage(system_prompt, nutzer_prompt)
        ergebnis = self._parse_json_antwort(antwort)
        if ergebnis and "luecken" in ergebnis:
            return ergebnis["luecken"]
        return []

    def generate_next_steps(self, projekt_beschreibung: str, programm: dict, luecken: list = None) -> list:
        """
        Generiert konkrete nächste Schritte für den Förderantrag.

        Parameter:
            projekt_beschreibung: Beschreibung des Projektvorhabens
            programm: Förderprogramm als Dictionary
            luecken: Bereits identifizierte Lücken

        Rückgabe:
            Liste konkreter Handlungsschritte
        """
        system_prompt = (
            "Du bist ein Experte für Fördermittel in deutschen Kommunen. "
            "Erstelle konkrete, umsetzbare nächste Schritte für den Förderantrag. "
            "Jeder Schritt soll spezifisch und überprüfbar sein. "
            "Antworte im JSON-Format mit einem Feld 'schritte' (Liste von Strings)."
        )

        luecken_text = "\n".join(f"- {l}" for l in (luecken or []))
        nutzer_prompt = (
            f"## Projektvorhaben\n{projekt_beschreibung}\n\n"
            f"## Förderprogramm\n{json.dumps(programm, ensure_ascii=False)}\n\n"
            f"## Identifizierte Lücken\n{luecken_text or 'Keine bekannt'}\n\n"
            f"Erstelle konkrete nächste Schritte."
        )

        antwort = self._ollama_anfrage(system_prompt, nutzer_prompt)
        ergebnis = self._parse_json_antwort(antwort)
        if ergebnis and "schritte" in ergebnis:
            return ergebnis["schritte"]
        return ["Fördermittelantrag manuell prüfen", "Programmrichtlinie vollständig lesen"]

"""
Datenbank-Manager für den Fördermittel-Kompass
Bietet CRUD-Operationen für Programme, Projekte, Matches und Fristen.
"""

import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Zentraler Datenbank-Manager für den Fördermittel-Kompass.
    Verwendet psycopg2 für PostgreSQL-Verbindungen.
    """

    def __init__(self):
        """Initialisiert den Datenbank-Manager mit Umgebungsvariablen."""
        import os
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.datenbank = os.getenv("DB_NAME", "foerdermittel")
        self.benutzer = os.getenv("DB_USER", "foerdermittel")
        self.passwort = os.getenv("DB_PASSWORD", "foerdermittel")
        self._verbindung = None

    def _verbinde(self):
        """Stellt eine Verbindung zur Datenbank her."""
        if self._verbindung and not self._verbindung.closed:
            return self._verbindung
        try:
            import psycopg2
            self._verbindung = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.datenbank,
                user=self.benutzer,
                password=self.passwort,
            )
            return self._verbindung
        except ImportError:
            logger.warning("psycopg2 nicht installiert — Datenbank nicht verfügbar")
            return None
        except Exception as e:
            logger.error("Datenbankverbindung fehlgeschlagen: %s", e)
            return None

    def _schliesse(self):
        """Schliesst die Datenbankverbindung."""
        if self._verbindung and not self._verbindung.closed:
            self._verbindung.close()

    def initialisiere_schema(self, schema_pfad: str = "database/schema.sql"):
        """Lädt das Datenbankschema."""
        verbindung = self._verbinde()
        if not verbindung:
            return False
        try:
            with open(schema_pfad, "r", encoding="utf-8") as f:
                sql = f.read()
            with verbindung.cursor() as cursor:
                cursor.execute(sql)
            verbindung.commit()
            logger.info("Datenbankschema erfolgreich geladen")
            return True
        except Exception as e:
            logger.error("Schema-Laden fehlgeschlagen: %s", e)
            return False

    # ============================================================
    # Förderprogramme (CRUD)
    # ============================================================

    def speichere_programm(self, programm: dict) -> Optional[int]:
        """Speichert ein Förderprogramm und gibt die ID zurück."""
        verbindung = self._verbinde()
        if not verbindung:
            return None
        try:
            with verbindung.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO programs (titel, traeger, bundesland, themenfeld,
                                         frist, quote, link, beschreibung, quelle, inhalts_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (inhalts_hash) DO NOTHING
                    RETURNING id
                """, (
                    programm.get("titel", ""),
                    programm.get("traeger", ""),
                    programm.get("bundesland", "Alle"),
                    programm.get("themenfeld", ""),
                    programm.get("frist"),
                    programm.get("quote", ""),
                    programm.get("link", ""),
                    programm.get("beschreibung", ""),
                    programm.get("quelle", ""),
                    programm.get("inhalts_hash", ""),
                ))
                ergebnis = cursor.fetchone()
                verbindung.commit()
                return ergebnis[0] if ergebnis else None
        except Exception as e:
            logger.error("Fehler beim Speichern des Programms: %s", e)
            return None

    def lade_programme(self, filtern: dict = None) -> list:
        """Lädt Förderprogramme mit optionalen Filtern."""
        verbindung = self._verbinde()
        if not verbindung:
            return []
        try:
            sql = "SELECT * FROM programs WHERE aktiv = TRUE"
            parameter = []
            if filtern:
                if filtern.get("themenfeld"):
                    sql += " AND themenfeld = %s"
                    parameter.append(filtern["themenfeld"])
                if filtern.get("bundesland"):
                    sql += " AND (bundesland = %s OR bundesland = 'Alle')"
                    parameter.append(filtern["bundesland"])
                if filtern.get("suchbegriff"):
                    sql += " AND titel ILIKE %s"
                    parameter.append(f"%{filtern['suchbegriff']}%")
            sql += " ORDER BY frist ASC NULLS LAST"
            with verbindung.cursor() as cursor:
                cursor.execute(sql, parameter)
                spalten = [desc[0] for desc in cursor.description]
                return [dict(zip(spalten, zeile)) for zeile in cursor.fetchall()]
        except Exception as e:
            logger.error("Fehler beim Laden der Programme: %s", e)
            return []

    def loesche_programm(self, programm_id: int) -> bool:
        """Löscht ein Förderprogramm (Soft-Delete)."""
        verbindung = self._verbinde()
        if not verbindung:
            return False
        try:
            with verbindung.cursor() as cursor:
                cursor.execute("UPDATE programs SET aktiv = FALSE WHERE id = %s", (programm_id,))
                verbindung.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error("Fehler beim Löschen des Programms: %s", e)
            return False

    # ============================================================
    # Projekte (CRUD)
    # ============================================================

    def speichere_projekt(self, projekt: dict) -> Optional[int]:
        """Speichert ein Projektvorhaben und gibt die ID zurück."""
        verbindung = self._verbinde()
        if not verbindung:
            return None
        try:
            with verbindung.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO projects (name, beschreibung, thema, budget,
                                         bundesland, zielgruppe, zeitrahmen, strukturiert)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    projekt.get("name", ""),
                    projekt.get("beschreibung", ""),
                    projekt.get("thema", ""),
                    projekt.get("budget", ""),
                    projekt.get("bundesland", ""),
                    projekt.get("zielgruppe", ""),
                    projekt.get("zeitrahmen", ""),
                    json.dumps(projekt.get("strukturiert", {}), ensure_ascii=False),
                ))
                ergebnis = cursor.fetchone()
                verbindung.commit()
                return ergebnis[0] if ergebnis else None
        except Exception as e:
            logger.error("Fehler beim Speichern des Projekts: %s", e)
            return None

    def lade_projekte(self) -> list:
        """Lädt alle Projektvorhaben."""
        verbindung = self._verbinde()
        if not verbindung:
            return []
        try:
            with verbindung.cursor() as cursor:
                cursor.execute("SELECT * FROM projects ORDER BY erstellt_am DESC")
                spalten = [desc[0] for desc in cursor.description]
                return [dict(zip(spalten, zeile)) for zeile in cursor.fetchall()]
        except Exception as e:
            logger.error("Fehler beim Laden der Projekte: %s", e)
            return []

    # ============================================================
    # Matching-Ergebnisse
    # ============================================================

    def speichere_match(self, match: dict) -> Optional[int]:
        """Speichert ein Matching-Ergebnis."""
        verbindung = self._verbinde()
        if not verbindung:
            return None
        try:
            with verbindung.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO matches (projekt_id, programm_id, score,
                                        begruendung, risiken, next_steps, modell)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    match.get("projekt_id"),
                    match.get("programm_id"),
                    match.get("score", 0),
                    match.get("begruendung", ""),
                    json.dumps(match.get("risiken", []), ensure_ascii=False),
                    json.dumps(match.get("next_steps", []), ensure_ascii=False),
                    match.get("modell", "unbekannt"),
                ))
                ergebnis = cursor.fetchone()
                verbindung.commit()
                return ergebnis[0] if ergebnis else None
        except Exception as e:
            logger.error("Fehler beim Speichern des Matches: %s", e)
            return None

    def lade_matches(self, projekt_id: int) -> list:
        """Lädt alle Matching-Ergebnisse für ein Projekt."""
        verbindung = self._verbinde()
        if not verbindung:
            return []
        try:
            with verbindung.cursor() as cursor:
                cursor.execute("""
                    SELECT m.*, p.titel as programm_titel
                    FROM matches m
                    JOIN programs p ON m.programm_id = p.id
                    WHERE m.projekt_id = %s
                    ORDER BY m.score DESC
                """, (projekt_id,))
                spalten = [desc[0] for desc in cursor.description]
                return [dict(zip(spalten, zeile)) for zeile in cursor.fetchall()]
        except Exception as e:
            logger.error("Fehler beim Laden der Matches: %s", e)
            return []

    # ============================================================
    # Fristen
    # ============================================================

    def lade_fristen(self) -> list:
        """Lädt alle aktiven Fristen."""
        verbindung = self._verbinde()
        if not verbindung:
            return []
        try:
            with verbindung.cursor() as cursor:
                cursor.execute("""
                    SELECT d.*, p.titel as programm_titel
                    FROM deadlines d
                    JOIN programs p ON d.programm_id = p.id
                    WHERE d.fristdatum >= CURRENT_DATE
                    ORDER BY d.fristdatum ASC
                """)
                spalten = [desc[0] for desc in cursor.description]
                return [dict(zip(spalten, zeile)) for zeile in cursor.fetchall()]
        except Exception as e:
            logger.error("Fehler beim Laden der Fristen: %s", e)
            return []

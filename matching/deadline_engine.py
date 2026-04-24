"""
Fristverwaltung für Förderprogramme
Ampelsystem, E-Mail-Erinnerungen und Dashboard-Benachrichtigungen.
"""

import logging
import smtplib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Frist:
    """Repräsentiert eine Förderfrist."""
    programm_id: str
    programm_titel: str
    fristdatum: str
    benachrichtigungen: list = field(default_factory=list)

    @property
    def verbleibende_tage(self) -> int:
        """Berechnet die verbleibenden Tage bis zur Frist."""
        try:
            frist = datetime.strptime(self.fristdatum, "%Y-%m-%d").date()
            return (frist - datetime.now().date()).days
        except ValueError:
            return -999

    @property
    def ampelfarbe(self) -> str:
        """Gibt die Ampelfarbe basierend auf verbleibenden Tagen zurück."""
        tage = self.verbleibende_tage
        if tage < 0:
            return "rot"
        elif tage <= 30:
            return "rot"
        elif tage <= 90:
            return "gelb"
        return "gruen"

    @property
    def ampel_emoji(self) -> str:
        """Gibt das Ampel-Emoji zurück."""
        farben = {"gruen": "🟢", "gelb": "🟡", "rot": "🔴"}
        return farben.get(self.ampelfarbe, "⚪")


class DeadlineEngine:
    """
    Verwaltet Fristen, erstellt Erinnerungen und steuert das Ampelsystem.
    """

    # Standard-Schwellenwerte in Tagen
    STANDARD_SCHWELLEN = {
        "rot": 30,
        "gelb": 90,
        "gruen": 91,
    }

    # Standard-Benachrichtigungszeitpunkte in Tagen vor Frist
    STANDARD_BENACHRICHTIGUNGEN = [7, 14, 30, 60, 90]

    def __init__(self, email_einstellungen: dict = None):
        """
        Initialisiert die Fristverwaltung.

        Parameter:
            email_einstellungen: Dictionary mit SMTP-Einstellungen:
                - host: SMTP-Server
                - port: SMTP-Port
                - benutzer: Benutzername
                - passwort: Passwort
                - absender: Absender-E-Mail
                - empfaenger: Liste der Empfänger-E-Mails
        """
        self.email_einstellungen = email_einstellungen or {}
        self.fristen: list[Frist] = []
        self.benachrichtigungszeitpunkte = self.STANDARD_BENACHRICHTIGUNGEN

    def lade_fristen(self, programme: list) -> None:
        """
        Lädt Fristen aus einer Liste von Förderprogrammen.

        Parameter:
            programme: Liste von Programmen mit 'frist'-Feld
        """
        self.fristen = []
        for prog in programme:
            fristdatum = prog.get("frist", "")
            if not fristdatum:
                continue
            try:
                # Fristformat validieren
                datetime.strptime(fristdatum, "%Y-%m-%d")
                self.fristen.append(Frist(
                    programm_id=str(prog.get("id", "")),
                    programm_titel=prog.get("titel", "Unbekannt"),
                    fristdatum=fristdatum,
                ))
            except ValueError:
                logger.warning("Ungültiges Fristformat für '%s': %s", prog.get("titel"), fristdatum)

    def pruefe_fristen(self) -> list[dict]:
        """
        Prüft alle Fristen und gibt den aktuellen Status zurück.

        Rückgabe:
            Liste mit Status-Informationen pro Programm
        """
        status = []
        for frist in self.fristen:
            status.append({
                "programm_titel": frist.programm_titel,
                "programm_id": frist.programm_id,
                "fristdatum": frist.fristdatum,
                "verbleibende_tage": frist.verbleibende_tage,
                "ampel": frist.ampelfarbe,
                "emoji": frist.ampel_emoji,
                "status_text": self._status_text(frist.verbleibende_tage),
            })

        # Nach Dringlichkeit sortieren
        status.sort(key=lambda x: x["verbleibende_tage"])
        return status

    def _status_text(self, tage: int) -> str:
        """Erzeugt einen lesbaren Statustext."""
        if tage < 0:
            return f"Abgelaufen seit {abs(tage)} Tagen"
        elif tage == 0:
            return "Frist ist heute!"
        elif tage == 1:
            return "Nur noch 1 Tag!"
        elif tage <= 7:
            return f"Kritisch: {tage} Tage verbleibend"
        elif tage <= 30:
            return f"Dringend: {tage} Tage verbleibend"
        elif tage <= 90:
            return f"Achtung: {tage} Tage verbleibend"
        else:
            return f"Verfügbar: {tage} Tage verbleibend"

    def ermittle_benachrichtigungen(self) -> list[dict]:
        """
        Ermittelt, welche Fristen eine Benachrichtigung erfordern.

        Rückgabe:
            Liste der zu benachrichtigenden Fristen mit Zeitpunkt
        """
        benachrichtigungen = []
        heute = datetime.now().date()

        for frist in self.fristen:
            tage = frist.verbleibende_tage
            if tage < 0:
                continue  # Abgelaufene Fristen nicht benachrichtigen

            for zeitpunkt in self.benachrichtigungszeitpunkte:
                if tage <= zeitpunkt and tage > zeitpunkt - 7:
                    benachrichtigungen.append({
                        "programm_titel": frist.programm_titel,
                        "fristdatum": frist.fristdatum,
                        "verbleibende_tage": tage,
                        "art": "dringend" if zeitpunkt <= 14 else "hinweis",
                        "nachricht": (
                            f"⚠️ {frist.programm_titel}: "
                            f"Noch {tage} Tage bis zur Frist ({frist.fristdatum})"
                        ),
                    })
                    break  # Nur eine Benachrichtigung pro Frist

        return benachrichtigungen

    def sende_email_benachrichtigung(self, benachrichtigungen: list) -> bool:
        """
        Sendet E-Mail-Benachrichtigungen für anstehende Fristen.

        Parameter:
            benachrichtigungen: Liste der Benachrichtigungen

        Rückgabe:
            True bei Erfolg, False bei Fehler
        """
        if not benachrichtigungen:
            logger.info("Keine Benachrichtigungen zu senden")
            return True

        if not self.email_einstellungen.get("host"):
            logger.warning("E-Mail nicht konfiguriert — Benachrichtigungen übersprungen")
            return False

        try:
            nachricht = self._erstelle_email(benachrichtigungen)
            return self._versende_email(nachricht)
        except Exception as e:
            logger.error("Fehler beim Senden der E-Mail: %s", e)
            return False

    def _erstelle_email(self, benachrichtigungen: list) -> MIMEMultipart:
        """Erstellt die E-Mail-Nachricht."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Fördermittel-Kompass: Fristen-Erinnerung"
        msg["From"] = self.email_einstellungen.get("absender", "foerdermittel@kommune.de")

        empfaenger = self.email_einstellungen.get("empfaenger", [])
        msg["To"] = ", ".join(empfaenger)

        # Textinhalt
        text_teile = [
            "Fördermittel-Kompass — Fristen-Erinnerung\n",
            "=" * 50, "",
        ]
        for b in benachrichtigungen:
            text_teile.append(b["nachricht"])

        text_teile.extend([
            "", "-" * 50,
            "Dies ist eine automatisierte Benachrichtigung des Fördermittel-Kompass.",
        ])

        text_inhalt = MIMEText("\n".join(text_teile), "plain", "utf-8")
        msg.attach(text_inhalt)
        return msg

    def _versende_email(self, msg: MIMEMultipart) -> bool:
        """Versendet die E-Mail über SMTP."""
        host = self.email_einstellungen["host"]
        port = self.email_einstellungen.get("port", 587)
        benutzer = self.email_einstellungen.get("benutzer", "")
        passwort = self.email_einstellungen.get("passwort", "")
        use_tls = self.email_einstellungen.get("tls", True)

        with smtplib.SMTP(host, port) as server:
            if use_tls:
                server.starttls()
            if benutzer and passwort:
                server.login(benutzer, passwort)
            empfaenger = self.email_einstellungen.get("empfaenger", [])
            server.sendmail(msg["From"], empfaenger, msg.as_string())
            logger.info("E-Mail an %d Empfänger gesendet", len(empfaenger))
            return True

    def dashboard_zusammenfassung(self) -> dict:
        """
        Erstellt eine Zusammenfassung für das Dashboard.

        Rückgabe:
            Dictionary mit Ampel-Statistiken
        """
        rot = sum(1 for f in self.fristen if f.ampelfarbe == "rot")
        gelb = sum(1 for f in self.fristen if f.ampelfarbe == "gelb")
        gruen = sum(1 for f in self.fristen if f.ampelfarbe == "gruen")

        naechste_frist = None
        if self.fristen:
            aktive = [f for f in self.fristen if f.verbleibende_tage >= 0]
            if aktive:
                naechste_frist = min(aktive, key=lambda f: f.verbleibende_tage)

        return {
            "gesamt": len(self.fristen),
            "rot": rot,
            "gelb": gelb,
            "gruen": gruen,
            "naechste_frist": {
                "titel": naechste_frist.programm_titel,
                "datum": naechste_frist.fristdatum,
                "tage": naechste_frist.verbleibende_tage,
            } if naechste_frist else None,
        }

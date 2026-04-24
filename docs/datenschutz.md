# Datenschutz und Datensicherheit — Fördermittel-Kompass

## Selbstgehosteter Betrieb

Der Fördermittel-Kompass ist für den **selbstgehosteten Betrieb** konzipiert. Alle Daten bleiben auf den Servern der jeweiligen Kommune. Es werden keine Daten an externe Cloud-Dienste übermittelt.

### Warum selbstgehostet?

- **Kommunale Datenhoheit:** Alle Projektvorhaben und Matching-Ergebnisse verbleiben auf den eigenen Servern.
- **Keine Drittanbieter:** Weder die Förderdatenbank noch die KI-Analyse verlassen die Infrastruktur der Kommune.
- **Vollständige Kontrolle:** Die Kommune bestimmt über Zugriff, Backup und Löschung aller Daten.

## Umgang mit sensiblen Projektdaten

### Projektvorhaben

Projektbeschreibungen können strategisch sensible Informationen enthalten (z.B. Planungsziele, Budgets). Diese Daten werden:

- Nur in der lokalen PostgreSQL-Datenbank gespeichert
- Nicht an Dritte übermittelt
- Bei Löschung eines Projekts vollständig entfernt (inkl. Matching-Ergebnisse)

### KI-Analyse

Die KI-Analyse erfolgt **ausschliesslich über Ollama (lokal)**. Es gibt keine Cloud-Verbindung für die KI-Verarbeitung.

- Keine Daten verlassen den lokalen Server während der KI-Analyse
- Keine Modelldaten werden an externe Dienste gesendet
- Ollama läuft vollständig isoliert im Docker-Netzwerk

## Minimierung der Protokollierung

Der Fördermittel-Kompass minimiert die Datenerfassung:

- **Keine Nutzungsprofile:** Es werden keine Benutzerprofile oder Verhaltensdaten erstellt.
- **Keine Tracking-Cookies:** Die Anwendung verwendet keine Cookies für Tracking-Zwecke.
- **Minimale Logs:** Nur technische Fehler und Quell-Abrufe werden protokolliert.
- **Keine IP-Adressen:** Client-IPs werden nicht dauerhaft gespeichert.

## Datenlöschung

- **Projekte:** Über die Benutzeroberfläche löschbar (Cascading-Löschung aller zugehörigen Daten).
- **Fristen:** Automatische Bereinigung abgelaufener Einträge nach 90 Tagen.
- **Logs:** Rotation nach 30 Tagen, automatische Löschung.

## Empfehlungen für den produktiven Betrieb

1. **Verschlüsselung:** HTTPS (TLS 1.2+) für den Zugriff aktivieren.
2. **Zugriffskontrolle:** LDAP/Active Directory-Anbindung für die Benutzerauthentifizierung.
3. **Backup:** Tägliche Datenbank-Backups mit automatischer Rotation.
4. **Netzwerk:** Ollama-Port (11434) nicht nach aussen freigeben.
5. **Updates:** Regelmässige Sicherheitsupdates für Docker, PostgreSQL und Python-Abhängigkeiten.

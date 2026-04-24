#!/bin/bash
# ============================================================
# Quellen aktualisieren — Fördermittel-Kompass
# Führt den Sammler aus, aktualisiert die Datenbank
# ============================================================

set -euo pipefail

LOG_DATEI="data/update_$(date +%Y%m%d_%H%M%S).log"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_DATEI"
}

fehler() {
    log "FEHLER: $*"
    exit 1
}

# Verzeichnis prüfen
if [ ! -f "app.py" ]; then
    fehler "Skript muss aus dem Projektverzeichnis gestartet werden"
fi

# Daten-Verzeichnis erstellen
mkdir -p data

log "=== Fördermittel-Kompass: Quellen-Aktualisierung gestartet ==="

# 1. Virtuelle Umgebung prüfen
if [ ! -d "venv" ]; then
    log "Erstelle virtuelle Umgebung..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt 2>&1 | tail -5 | tee -a "$LOG_DATEI"
else
    source venv/bin/activate
fi

# 2. Quellen abrufen
log "Rufe Fördermittel-Quellen ab..."
python3 -c "
from collector.program_collector import ProgramCollector
from database.db_manager import DatabaseManager

# Sammler starten
sammler = ProgramCollector('config/sources.yaml')
programme = sammler.parse_programs()
print(f'{len(programme)} eindeutige Programme gefunden')

# In Datenbank speichern
db = DatabaseManager()
gespeichert = 0
for prog in programme:
    prog_dict = prog.to_dict()
    prog_dict['inhalts_hash'] = prog.inhalts_hash()
    if db.speichere_programm(prog_dict):
        gespeichert += 1

print(f'{gespeichert} neue Programme in der Datenbank gespeichert')
" 2>&1 | tee -a "$LOG_DATEI"

# 3. Fristen prüfen
log "Prüfe Fristen..."
python3 -c "
from matching.deadline_engine import DeadlineEngine
from database.db_manager import DatabaseManager

db = DatabaseManager()
programme = db.lade_programme()
engine = DeadlineEngine()
engine.lade_fristen(programme)
zusammenfassung = engine.dashboard_zusammenfassung()
print(f'Fristen: {zusammenfassung[\"rot\"]} rot, {zusammenfassung[\"gelb\"]} gelb, {zusammenfassung[\"gruen\"]} grün')
if zusammenfassung.get('naechste_frist'):
    nf = zusammenfassung['naechste_frist']
    print(f'Nächste Frist: {nf[\"titel\"]} ({nf[\"datum\"]}, {nf[\"tage\"]} Tage)')
" 2>&1 | tee -a "$LOG_DATEI"

log "=== Aktualisierung abgeschlossen ==="
exit 0

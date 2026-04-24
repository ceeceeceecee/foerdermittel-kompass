# Setup-Leitfaden — Fördermittel-Kompass

## Voraussetzungen

- Docker und Docker Compose (Version 20.10+)
- Mindestens 4 GB RAM (8 GB empfohlen)
- 10 GB freier Speicherplatz
- Grundkenntnisse in der Kommandozeile

## Schritt 1: Repository klonen

```bash
git clone https://github.com/ceeceeceecee/foerdermittel-kompass.git
cd foerdermittel-kompass
```

## Schritt 2: Konfiguration vorbereiten

```bash
# Umgebungsvariablen konfigurieren
cp .env.example .env

# Quellen konfigurieren
cp config/sources.example.yaml config/sources.yaml

# Einstellungen konfigurieren
cp config/settings.example.yaml config/settings.yaml
```

### .env anpassen

Öffnen Sie `.env` und passen Sie die Datenbank-Einstellungen an:

```env
DB_PASSWORD=ihr-sicheres-passwort
APP_SECRET_KEY=zufaelliger-schluessel
```

## Schritt 3: Docker starten

```bash
docker compose up -d
```

Die folgenden Container werden gestartet:
- **app** — Streamlit-Anwendung (Port 8501)
- **postgres** — PostgreSQL-Datenbank (Port 5432)
- **ollama** — Lokaler KI-Server (Port 11434)
- **worker** — Periodische Quell-Aktualisierung (optional)

## Schritt 4: Ollama-Modell laden

Nach dem ersten Start muss das KI-Modell heruntergeladen werden:

```bash
docker exec -it foerdermittel-kompass-ollama ollama pull llama3
```

Alternativ ein kleineres Modell für weniger RAM:

```bash
docker exec -it foerdermittel-kompass-ollama ollama pull phi3
```

Passen Sie dann `MODEL_NAME` in der `.env`-Datei an.

## Schritt 5: Quellen konfigurieren

Öffnen Sie `config/sources.yaml` und passen Sie die Quellen an Ihre Bedürfnisse an:

```yaml
quellen:
  - name: "Meine Förderquelle"
    typ: html
    url: "https://foerderportal.example.de"
    selektoren:
      container: ".program-item"
      titel: "h3"
      beschreibung: "p"
    aktiv: true
```

## Schritt 6: Erste Quellen abrufen

```bash
chmod +x scripts/update_sources.sh
./scripts/update_sources.sh
```

## Schritt 7: Anwendung öffnen

Öffnen Sie im Browser:

```
http://localhost:8501
```

## Erstes Projekt erstellen

1. Wechseln Sie zum Tab **"Projektvorhaben eingeben"**
2. Geben Sie Projektname und Beschreibung ein
3. Wählen Sie Themenfeld und Bundesland
4. Klicken Sie auf **"KI-Matching starten"**
5. Wechseln Sie zum Tab **"KI-Matching-Ergebnis"** für die Analyse

## Fehlerbehebung

### Ollama nicht erreichbar

```bash
# Ollama-Status prüfen
docker logs foerdermittel-kompass-ollama

# Neustart
docker restart foerdermittel-kompass-ollama
```

### Datenbankverbindung fehlgeschlagen

```bash
# PostgreSQL-Status prüfen
docker logs foerdermittel-kompass-db

# Passwort in .env prüfen
cat .env | grep DB_
```

### KI-Matching liefert keine Ergebnisse

- Prüfen Sie, ob das Ollama-Modell geladen ist: `docker exec foerdermittel-kompass-ollama ollama list`
- Kleinere Modelle verwenden (weniger RAM erforderlich)
- Timeout in `.env` erhöhen: `OLLAMA_TIMEOUT=180`

# Fördermittel-Kompass für Kommunen – passende Programme schneller finden

**DE:** Webbasierte Anwendung, die Kommunen hilft, passende Förderprogramme zu finden, Projekte mit Förderkriterien abzugleichen und Fristen zu überwachen – komplett DSGVO-konform und selbstgehostet.

**EN:** Web application that helps German municipalities discover matching funding programs, compare projects against eligibility criteria, and track deadlines — fully GDPR-compliant and self-hosted.

![MIT License](https://img.shields.io/badge/Lizenz-MIT-333)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB)
![DSGVO](https://img.shields.io/badge/DSGVO-konform-009B3A)
![Ollama](https://img.shields.io/badge/KI-Ollama_ohne_Cloud-000)
![Docker](https://img.shields.io/badge/Docker-bereit-2496ED)

---

## Problem

Kommunen verpassen jährlich Millionen an Fördergeldern, weil:

- Hunderte Förderprogramme auf dutzenden Websites verstreut sind
- Die Prüfung, ob ein Projekt zu einem Programm passt, extrem zeitaufwändig ist
- Fristen übersehen werden und Antragsfenster geschlossen sind
- Fachkräfte fehlen, um sich systematisch um Fördermittel zu kümmern

## Lösung

Der Fördermittel-Kompass automatisiert die Suche, Prüfung und Überwachung:

- [x] Zentrale Datenbank mit Förderprogrammen aus Bund, Ländern und EU
- [x] KI-gestützter Abgleich von Projektvorhaben mit Förderkriterien
- [x] Ampelsystem für Fristen (grün/gelb/rot)
- [x] Checklisten für den gesamten Antragsprozess
- [x] Lokale KI-Verarbeitung via Ollama – keine Cloud-Dienste, voll DSGVO-konform
- [x] Selbstgehostet, Docker-basiert, einfach zu部署en

## Architektur

```
+-------------------+     +-------------------+     +-------------------+
|   Streamlit UI    |     |   PostgreSQL DB   |     |     Ollama KI     |
|   (app.py)        |<--->|   (schema.sql)    |     |   (lokal)         |
|   Port 8501       |     |   Port 5432       |     |   Port 11434      |
+-------------------+     +-------------------+     +-------------------+
        ^                         ^
        |                         |
+-------v-------+       +---------v--------+
|   Collector   |       |  Deadline-Engine |
| (Quellen)     |       |  (Fristen)       |
+---------------+       +------------------+
```

## Systemanforderungen

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| RAM        | 4 GB    | 8 GB      |
| CPU        | 2 Kerne | 4 Kerne   |
| Speicher   | 10 GB   | 20 GB     |
| Docker     | 20.10+  | 24.0+     |
| Python     | 3.11+   | 3.12      |
| Ollama     | Latest  | Latest    |

## Schnellstart

```bash
# 1. Repository klonen
git clone https://github.com/ceeceeceecee/foerdermittel-kompass.git
cd foerdermittel-kompass

# 2. Konfiguration vorbereiten
cp .env.example .env
cp config/sources.example.yaml config/sources.yaml
cp config/settings.example.yaml config/settings.yaml

# 3. Docker starten
docker compose up -d

# 4. Ollama-Modell laden (lokal)
docker exec -it foerdermittel-kompass-ollama ollama pull llama3

# 5. Anwendung öffnen
open http://localhost:8501
```

## Installation

Siehe [docs/setup-guide.md](docs/setup-guide.md) für eine detaillierte Schritt-für-Schritt-Anleitung.

## Dokumentation

| Dokument | Inhalt |
|----------|--------|
| [Setup-Leitfaden](docs/setup-guide.md) | Installation und Konfiguration |
| [Datenschutzerklärung](docs/datenschutz.md) | DSGVO-Konformität und Datenschutz |
| [Quellenstrategie](docs/quellenstrategie.md) | Förderquellen pflegen und erweitern |
| [Nutzungsgrenzen](docs/nutzungsgrenzen.md) | Grenzen und Haftungsausschluss |

## Technologie-Stack

- **Frontend:** Streamlit
- **Backend:** Python
- **Datenbank:** PostgreSQL
- **KI:** Ollama (lokal, kein Cloud-Dienst)
- **Container:** Docker / Docker Compose

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).

## 👤 Autor

**Cela** — Freelancer für digitale Verwaltungslösungen

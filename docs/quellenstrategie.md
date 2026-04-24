# Quellenstrategie — Fördermittel-Kompass

## Neue Förderquellen hinzufügen

Der Fördermittel-Kompass unterstützt drei Quelltypen:

### 1. RSS-Feeds

Für Quellen, die einen RSS- oder Atom-Feed anbieten:

```yaml
quellen:
  - name: "Förderportal Bundesland"
    typ: rss
    url: "https://foerderportal.bundesland.de/rss.xml"
    aktiv: true
```

**Geeignet für:** Portale mit automatisierten Feeds, regelmässige Aktualisierungen.

### 2. HTML-Seiten

Für Websites, die Förderprogramme in strukturierter Form auflisten:

```yaml
quellen:
  - name: "Förderdatenbank"
    typ: html
    url: "https://www.foerderportal.de/programme"
    selektoren:
      container: ".program-card"     # Container für jedes Programm
      titel: "h3.title"              # Titel des Programms
      beschreibung: "p.description"  # Beschreibungstext
      link: "a.more-link"            # Link zum Programm
      frist: "span.deadline"         # Fristdatum
    aktiv: true
```

**Hinweis:** CSS-Selektoren müssen an die jeweilige Website angepasst werden. Nutzen Sie die Browser-Entwicklertools (F12), um die richtigen Selektoren zu ermitteln.

### 3. CSV-Import

Für manuell gepflegte Förderprogramme:

```yaml
quellen:
  - name: "Eigene Programme"
    typ: csv
    datei: "data/eigene_programme.csv"
    aktiv: true
```

Die CSV-Datei muss folgende Spalten enthalten (mindestens `titel`):

```
titel,traeger,bundesland,themenfeld,frist,quote,link,beschreibung
```

## Qualitätskriterien für Quellen

### Pflichtkriterien

- **Aktualität:** Quelle wird mindestens monatlich aktualisiert
- **Vollständigkeit:** Förderprogramme enthalten mindestens Titel und Beschreibung
- **Verlässlichkeit:** Offizielle Quelle (Ministerium, Landesbehörde, EU)
- **Zugänglichkeit:** Keine Paywalls oder Login-Sperren

### Wunsch-Kriterien

- **Fristangaben:** Konkrete Einreichungsfristen
- **Fördersatz:** Angabe der Förderquote in Prozent
- **Regionale Zuordnung:** Bundesland-spezifische Programme
- **Themenkategorisierung:** Klare Zuordnung zu Themenfeldern

## Empfohlene Quellen

| Quelle | Typ | Bundesland |
|--------|-----|-----------|
| Förderdatenbank Bund | HTML | Bund |
| BMWK-Förderportal | RSS | Bund |
| EU-Fördermittel | RSS | EU |
| Digitale-Modelle.Region | RSS | Bund |
| Landeseigenes Förderportal | HTML | Je Bundesland |

## Pflegeprozess

### Wöchentlich

1. Prüfen, ob alle Quellen erreichbar sind
2. Fehlermeldungen im Log prüfen
3. Neue Programme manuell prüfen

### Monatlich

1. Selektoren bei HTML-Quellen auf Änderungen prüfen
2. Neue Quellen recherchieren und hinzufügen
3. Abgelaufene Programme deaktivieren

### Quartalsweise

1. Komplette Quellenliste überprüfen
2. CSS-Selektoren bei Website-Änderungen anpassen
3. Qualitätsbericht erstellen (Anzahl Programme, Abdeckung)

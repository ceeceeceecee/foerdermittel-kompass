-- ============================================================
-- Fördermittel-Kompass — Datenbankschema
-- PostgreSQL-kompatibel
-- ============================================================

-- Tabelle: Förderprogramme
-- Speichert alle erfassten Förderprogramme
CREATE TABLE IF NOT EXISTS programs (
    id              SERIAL PRIMARY KEY,
    titel           VARCHAR(500) NOT NULL,
    traeger         VARCHAR(300),
    bundesland      VARCHAR(200) DEFAULT 'Alle',
    themenfeld      VARCHAR(200),
    frist           DATE,
    quote           VARCHAR(50),
    link            TEXT,
    beschreibung    TEXT,
    quelle          VARCHAR(500),
    inhalts_hash    VARCHAR(32) UNIQUE,
    aktiv           BOOLEAN DEFAULT TRUE,
    erstellt_am     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index für Schnellsuche
CREATE INDEX IF NOT EXISTS idx_programs_themenfeld ON programs(themenfeld);
CREATE INDEX IF NOT EXISTS idx_programs_bundesland ON programs(bundesland);
CREATE INDEX IF NOT EXISTS idx_programs_frist ON programs(frist);
CREATE INDEX IF NOT EXISTS idx_programs_titel ON programs USING gin(to_tsvector('german', titel));

-- ============================================================
-- Tabelle: Quellen
-- Verwaltet die Konfiguration der Fördermittel-Quellen
-- ============================================================
CREATE TABLE IF NOT EXISTS sources (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(300) NOT NULL,
    typ         VARCHAR(50) NOT NULL,  -- rss, html, csv
    url         TEXT,
    selektoren  JSONB,                  -- CSS-Selektoren für HTML-Parser
    aktiv       BOOLEAN DEFAULT TRUE,
    letzter_abruf TIMESTAMP,
    fehler      TEXT,
    erstellt_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Tabelle: Fristen
-- Speichert Fristen mit Benachrichtigungsstatus
-- ============================================================
CREATE TABLE IF NOT EXISTS deadlines (
    id              SERIAL PRIMARY KEY,
    programm_id     INTEGER REFERENCES programs(id) ON DELETE CASCADE,
    fristdatum      DATE NOT NULL,
    ampel_farbe     VARCHAR(10),         -- gruen, gelb, rot
    benachrichtigt  BOOLEAN DEFAULT FALSE,
    benachricht_am  TIMESTAMP,
    erstellt_am     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deadlines_frist ON deadlines(fristdatum);
CREATE INDEX IF NOT EXISTS idx_deadlines_ampel ON deadlines(ampel_farbe);

-- ============================================================
-- Tabelle: Projekte
-- Speichert die Projektvorhaben der Nutzer
-- ============================================================
CREATE TABLE IF NOT EXISTS projects (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(500) NOT NULL,
    beschreibung    TEXT,
    thema           VARCHAR(200),
    budget          VARCHAR(100),
    bundesland      VARCHAR(200),
    zielgruppe      VARCHAR(300),
    zeitrahmen      VARCHAR(200),
    strukturiert    JSONB,               -- KI-strukturierte Projektdaten
    erstellt_am     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aktualisiert_am TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Tabelle: Matching-Ergebnisse
-- Speichert die KI-Matching-Ergebnisse
-- ============================================================
CREATE TABLE IF NOT EXISTS matches (
    id              SERIAL PRIMARY KEY,
    projekt_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    programm_id     INTEGER REFERENCES programs(id) ON DELETE CASCADE,
    score           INTEGER CHECK (score >= 0 AND score <= 100),
    begruendung     TEXT,
    risiken         JSONB,               -- Liste der Risiken
    next_steps      JSONB,               -- Liste der nächsten Schritte
    modell          VARCHAR(100),         -- Verwendetes KI-Modell
    erstellt_am     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_matches_projekt ON matches(projekt_id);
CREATE INDEX IF NOT EXISTS idx_matches_score ON matches(score DESC);

-- ============================================================
-- Tabelle: Aufgaben
-- Checklisten und Aufgaben für Förderanträge
-- ============================================================
CREATE TABLE IF NOT EXISTS tasks (
    id              SERIAL PRIMARY KEY,
    projekt_id      INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    text            VARCHAR(500) NOT NULL,
    faellig         DATE,
    erledigt        BOOLEAN DEFAULT FALSE,
    erstellt_am     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    erledigt_am     TIMESTAMP
);

-- ============================================================
-- Tabelle: Benachrichtigungen
-- Protokollierte Benachrichtigungen
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id              SERIAL PRIMARY KEY,
    typ             VARCHAR(50) NOT NULL, -- email, dashboard
    betreff         VARCHAR(500),
    inhalt          TEXT,
    empfaenger      VARCHAR(500),
    status          VARCHAR(20) DEFAULT 'gesendet',  -- gesendet, fehlgeschlagen
    erstellt_am     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Aktualisierungs-Funktion für aktualisiert_am
-- ============================================================
CREATE OR REPLACE FUNCTION aktualisiere_zeitstempel()
RETURNS TRIGGER AS $$
BEGIN
    NEW.aktualisiert_am = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger für Programme
CREATE TRIGGER trg_programs_aktualisiert
    BEFORE UPDATE ON programs
    FOR EACH ROW EXECUTE FUNCTION aktualisiere_zeitstempel();

-- Trigger für Projekte
CREATE TRIGGER trg_projects_aktualisiert
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION aktualisiere_zeitstempel();

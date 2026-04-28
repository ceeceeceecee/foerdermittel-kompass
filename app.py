#!/usr/bin/env python3
"""
Fördermittel-Kompass für Kommunen
Streamlit-Hauptanwendung – DSGVO-konform, selbstgehostet
"""

import os
import sys
import json
import yaml
from datetime import datetime, timedelta

# -- Unified Theme System --
import sys, os as _theme_os
sys.path.insert(0, _theme_os.path.dirname(_theme_os.path.abspath(__file__)))
from theme import init_theme, theme_toggle_sidebar, app_footer

import streamlit as st
import pandas as pd

# Pfad für Konfigurationen
CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")


def lade_konfiguration():
    """Lädt die Anwendungseinstellungen aus der YAML-Datei."""
    settings_path = os.path.join(CONFIG_DIR, "settings.yaml")
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def lade_foerderprogramme():
    """Lädt Förderprogramme aus der Datenbank oder einer Beispieldatei."""
    try:
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        programme = db.lade_programme()
        if programme:
            return pd.DataFrame(programme)
    except Exception:
        pass
    # Beispieldaten für Demo-Betrieb
    return pd.DataFrame([
        {
            "titel": "Städtische Digitalisierung",
            "traeger": "Bundesministerium für Digitales",
            "bundesland": "Alle",
            "themenfeld": "Digitalisierung",
            "frist": "2026-09-30",
            "quote": "80%",
            "link": "https://example.de/foerderung1",
            "beschreibung": "Förderung von Digitalisierungsprojekten in Kommunen zur Verbesserung der digitalen Verwaltung.",
        },
        {
            "titel": "Klimaschutz in Kommunen",
            "traeger": "Bundesumweltministerium",
            "bundesland": "Alle",
            "themenfeld": "Klimaschutz",
            "frist": "2026-06-15",
            "quote": "90%",
            "link": "https://example.de/foerderung2",
            "beschreibung": "Förderung von Klimaschutzmassnahmen wie Energieeffizienz, erneuerbare Energien und nachhaltige Mobilität.",
        },
        {
            "titel": "Soziale Integration",
            "traeger": "Bundesfamilienministerium",
            "bundesland": "NRW, BY, BW",
            "themenfeld": "Soziales",
            "frist": "2026-12-31",
            "quote": "70%",
            "link": "https://example.de/foerderung3",
            "beschreibung": "Förderung von Projekten zur sozialen Integration und Teilhabe in kommunalen Gemeinschaften.",
        },
        {
            "titel": "Smart-City-Initiative",
            "traeger": "Bundesministerium für Verkehr",
            "bundesland": "Alle",
            "themenfeld": "Smart City",
            "frist": "2026-07-31",
            "quote": "85%",
            "link": "https://example.de/foerderung4",
            "beschreibung": "Förderung intelligenter Stadtentwicklung, IoT-Infrastruktur und datenbasierte Verwaltung.",
        },
        {
            "titel": "Denkmalschutz-Förderung",
            "traeger": "Landeskulturbehörde",
            "bundesland": "BY",
            "themenfeld": "Kultur",
            "frist": "2026-10-15",
            "quote": "60%",
            "link": "https://example.de/foerderung5",
            "beschreibung": "Förderung von Restaurierung und Erhaltung historischer Bausubstanz in bayerischen Kommunen.",
        },
    ])


def fristenampel(frist_str):
    """Berechnet die Ampelfarbe basierend auf der verbleibenden Zeit."""
    try:
        frist = datetime.strptime(frist_str, "%Y-%m-%d").date()
        heute = datetime.now().date()
        tage = (frist - heute).days
        if tage < 0:
            return "rot", f"Abgelaufen ({abs(tage)} Tage)"
        elif tage <= 30:
            return "rot", f"Kritisch: {tage} Tage"
        elif tage <= 90:
            return "gelb", f"Dringend: {tage} Tage"
        else:
            return "gruen", f"Verfügbar: {tage} Tage"
    except (ValueError, TypeError):
        return "grau", "Unbekannt"


def zeige_programmdetails(zeile):
    """Zeigt detaillierte Informationen zu einem Förderprogramm."""
    st.markdown(f"### {zeile['titel']}")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Fördergeber:** {zeile['traeger']}")
        st.write(f"**Bundesland:** {zeile.get('bundesland', 'Alle')}")
        st.write(f"**Themenfeld:** {zeile.get('themenfeld', '—')}")
    with col2:
        st.write(f"**Fördersatz:** {zeile.get('quote', '—')}")
        farbe, text = fristenampel(zeile.get('frist', ''))
        ampel_emoji = {"gruen": "🟢", "gelb": "🟡", "rot": "🔴", "grau": "⚪"}
        st.write(f"**Frist:** {ampel_emoji.get(farbe, '⚪')} {text}")
        if zeile.get('link'):
            st.markdown(f"[🔗 Zum Programm]({zeile['link']})")
    st.write(f"**Beschreibung:** {zeile.get('beschreibung', 'Keine Beschreibung vorhanden.')}")


def seite_suche(df):
    """Seite: Förderprogramme durchsuchen."""
    st.header("🔍 Förderprogramme durchsuchen")
    st.markdown("Durchsuchen Sie die Datenbank nach passenden Förderprogrammen.")

    with st.expander("Filteroptionen", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            suchbegriff = st.text_input("Suchbegriff", placeholder="z.B. Digitalisierung, Klima...")
        with col2:
            themenfelder = sorted(df["themenfeld"].dropna().unique().tolist()) if "themenfeld" in df.columns else []
            gewaehltes_feld = st.selectbox("Themenfeld", ["Alle"] + themenfelder)
        with col3:
            bundeslaender = sorted(df["bundesland"].dropna().unique().tolist()) if "bundesland" in df.columns else []
            gewaehltes_land = st.selectbox("Bundesland", ["Alle"] + bundeslaender)

    # Filter anwenden
    gefiltert = df.copy()
    if suchbegriff:
        maske = gefiltert.apply(lambda z: suchbegriff.lower() in str(z).lower(), axis=1)
        gefiltert = gefiltert[maske]
    if gewaehltes_feld != "Alle":
        gefiltert = gefiltert[gefiltert["themenfeld"] == gewaehltes_feld]
    if gewaehltes_land != "Alle":
        gefiltert = gefiltert[gefiltert["bundesland"].str.contains(gewaehltes_land, na=False)]

    st.markdown(f"**{len(gefiltert)} Programme gefunden**")

    for idx, zeile in gefiltert.iterrows():
        with st.container():
            zeige_programmdetails(zeile)
            st.divider()


def seite_projekt(df):
    """Seite: Projektvorhaben eingeben."""
    st.header("🧭 Projektvorhaben eingeben")
    st.markdown("Beschreiben Sie Ihr Projektvorhaben, damit die KI passende Förderprogramme findet.")

    with st.form("projekt_formular"):
        projektname = st.text_input("Projektname*", placeholder="z.B. Digitaler Bürgerservice")
        beschreibung = st.text_area(
            "Projektbeschreibung*",
            placeholder="Beschreiben Sie das Vorhaben ausführlich: Ziele, Massnahmen, Zielgruppe, Zeitraum...",
            height=150,
        )
        col1, col2 = st.columns(2)
        with col1:
            thema = st.selectbox("Themenfeld", ["Digitalisierung", "Klimaschutz", "Soziales", "Smart City", "Kultur", "Mobilität", "Bildung", "Sonstiges"])
        with col2:
            budget = st.text_input("Geschätztes Budget (EUR)", placeholder="z.B. 500000")
        bundesland = st.selectbox("Bundesland", ["Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen", "Mecklenburg-Vorpommern", "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt", "Schleswig-Holstein", "Thüringen"])
        zielgruppe = st.text_input("Zielgruppe", placeholder="z.B. Bürger, Verwaltung, Unternehmen")
        zeitrahmen = st.text_input("Zeitrahmen", placeholder="z.B. 12 Monate, Start Q3 2026")

        submitted = st.form_submit_button("🤖 KI-Matching starten", use_container_width=True)

    if submitted:
        if not projektname.strip() or not beschreibung.strip():
            st.error("Bitte füllen Sie mindestens Projektname und Beschreibung aus.")
            return
        projekt = {
            "name": projektname,
            "beschreibung": beschreibung,
            "thema": thema,
            "budget": budget,
            "bundesland": bundesland,
            "zielgruppe": zielgruppe,
            "zeitrahmen": zeitrahmen,
            "erstellt_am": datetime.now().isoformat(),
        }
        st.session_state["aktuelles_projekt"] = projekt
        st.success("Projekt gespeichert! Wechseln Sie zum Tab 'KI-Matching-Ergebnis'.")


def seite_matching(df):
    """Seite: KI-Matching-Ergebnis."""
    st.header("🤖 KI-Matching-Ergebnis")
    st.markdown("KI-gestützter Abgleich Ihres Projektvorhabens mit Förderprogrammen.")

    projekt = st.session_state.get("aktuelles_projekt")
    if not projekt:
        st.info("Bitte geben Sie zuerst ein Projektvorhaben im Tab 'Projektvorhaben eingeben' ein.")
        return

    st.markdown(f"**Projekt:** {projekt['name']}")
    with st.expander("Projektdetails anzeigen"):
        for k, v in projekt.items():
            st.write(f"**{k.replace('_', ' ').title()}:** {v}")

    st.markdown("---")

    if st.button("🔍 Matching durchführen", use_container_width=True, type="primary"):
        with st.spinner("Analysiere Programme mit lokaler KI (Ollama)..."):
            try:
                from matching.project_matcher import ProjectMatcher
                matcher = ProjectMatcher()
                ergebnisse = matcher.score_program_fit(
                    projekt_beschreibung=projekt["beschreibung"],
                    programme=df.to_dict("records"),
                )
                st.session_state["matching_ergebnisse"] = ergebnisse
            except Exception as e:
                st.warning(f"KI-Matching nicht verfügbar (Ollama nicht erreichbar). Zeige ergebnisbasierte Vorschläge an.\n\nFehler: {e}")
                # Fallback: einfache themenbasierte Vorschläge
                ergebnisse = []
                for _, prog in df.iterrows():
                    score = 0
                    if projekt["thema"] == prog.get("themenfeld"):
                        score += 40
                    if projekt["bundesland"] in prog.get("bundesland", "") or "Alle" in prog.get("bundesland", ""):
                        score += 30
                    if any(wort in str(prog.get("beschreibung", "")).lower() for wort in projekt["beschreibung"].lower().split()[:5]):
                        score += 20
                    score = min(score, 95)
                    if score > 0:
                        ergebnisse.append({
                            "titel": prog["titel"],
                            "score": score,
                            "begruendung": "Themen- und regionaler Abgleich",
                            "risiken": ["Förderrichtlinie muss im Detail geprüft werden"],
                            "next_steps": ["Programmrichtlinie herunterladen", "Kriterien prüfen"],
                        })
                ergebnisse.sort(key=lambda x: x["score"], reverse=True)
                st.session_state["matching_ergebnisse"] = ergebnisse

    ergebnisse = st.session_state.get("matching_ergebnisse")
    if ergebnisse:
        for erg in ergebnisse:
            score = erg.get("score", 0)
            farbe = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
            with st.container():
                st.markdown(f"### {farbe} {erg['titel']} — Übereinstimmung: {score}%")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Begründung:**")
                    st.write(erg.get("begruendung", "—"))
                with col2:
                    st.markdown("**Risiken:**")
                    for risiko in erg.get("risiken", []):
                        st.write(f"⚠️ {risiko}")
                if erg.get("next_steps"):
                    st.markdown("**Nächste Schritte:**")
                    for schritt in erg["next_steps"]:
                        st.write(f"✅ {schritt}")
                st.divider()


def seite_fristen(df):
    """Seite: Fristenkalender."""
    st.header("📅 Fristenkalender")
    st.markdown("Überwachen Sie approaching Fristen und verpassen Sie keine Antragsfenster.")

    if df.empty or "frist" not in df.columns:
        st.warning("Keine Förderprogramme mit Fristen vorhanden.")
        return

    # Fristen sortieren
    heute = datetime.now().date()
    fristen_daten = []
    for _, zeile in df.iterrows():
        try:
            frist = datetime.strptime(zeile["frist"], "%Y-%m-%d").date()
            farbe, text = fristenampel(zeile["frist"])
            fristen_daten.append({
                "titel": zeile["titel"],
                "frist": zeile["frist"],
                "tage": (frist - heute).days,
                "ampel": farbe,
                "anzeige": text,
            })
        except (ValueError, TypeError):
            continue

    fristen_df = pd.DataFrame(fristen_daten)
    fristen_df = fristen_df.sort_values("tage")

    # Übersicht
    col1, col2, col3 = st.columns(3)
    abgelaufen = len(fristen_df[fristen_df["tage"] < 0])
    kritisch = len(fristen_df[(fristen_df["tage"] >= 0) & (fristen_df["tage"] <= 30)])
    verfuegbar = len(fristen_df[fristen_df["tage"] > 30])
    with col1:
        st.metric("🔴 Kritisch / Abgelaufen", abgelaufen + kritisch)
    with col2:
        st.metric("🟡 Dringend", len(fristen_df[(fristen_df["tage"] > 30) & (fristen_df["tage"] <= 90)]))
    with col3:
        st.metric("🟢 Verfügbar", len(fristen_df[fristen_df["tage"] > 90]))

    # Tabelle
    for _, zeile in fristen_df.iterrows():
        ampel_emoji = {"gruen": "🟢", "gelb": "🟡", "rot": "🔴", "grau": "⚪"}
        emoji = ampel_emoji.get(zeile["ampel"], "⚪")
        st.markdown(f"{emoji} **{zeile['titel']}** — {zeile['anzeige']} (Frist: {zeile['frist']})")


def seite_checklisten():
    """Seite: Checklisten & Aufgaben."""
    st.header("✅ Checklisten & Aufgaben")
    st.markdown("Verwalten Sie Ihre Aufgaben für den Förderantragsprozess.")

    if "aufgaben" not in st.session_state:
        st.session_state["aufgaben"] = []

    # Neue Aufgabe hinzufügen
    with st.form("aufgabe_formular"):
        col1, col2 = st.columns([3, 1])
        with col1:
            aufgabe_text = st.text_input("Neue Aufgabe", placeholder="z.B. Förderrichtlinie herunterladen")
        with col2:
            aufgabe_frist = st.date_input("Fällig bis", value=None)
        submitted = st.form_submit_button("Hinzufügen")

    if submitted and aufgabe_text.strip():
        st.session_state["aufgaben"].append({
            "text": aufgabe_text,
            "fällig": aufgabe_frist.isoformat() if aufgabe_frist else "",
            "erledigt": False,
            "erstellt": datetime.now().isoformat(),
        })

    # Vorlagen
    st.markdown("### Vorlagen für Förderanträge")
    vorlagen = [
        "Förderrichtlinie lesen und verstehen",
        "Förderfähigkeit der Gemeinde prüfen",
        "Projektkostenplan erstellen",
        "Kooperationspartner identifizieren",
        "Antragstellung vorbereiten",
        "Antrag einreichen",
        "Zwischenbericht erstellen",
        "Verwendungsnachweis einreichen",
    ]
    if st.button("📋 Standard-Checkliste laden"):
        for vorlage in vorlagen:
            st.session_state["aufgaben"].append({
                "text": vorlage,
                "fällig": "",
                "erledigt": False,
                "erstellt": datetime.now().isoformat(),
            })
        st.success("Standard-Checkliste geladen!")

    # Aufgaben anzeigen
    if not st.session_state["aufgaben"]:
        st.info("Noch keine Aufgaben vorhanden.")
        return

    erledigt_count = sum(1 for a in st.session_state["aufgaben"] if a["erledigt"])
    gesamt = len(st.session_state["aufgaben"])
    st.progress(erledigt_count / gesamt if gesamt else 0, text=f"{erledigt_count}/{gesamt} erledigt")

    for i, aufgabe in enumerate(st.session_state["aufgaben"]):
        status = "✅" if aufgabe["erledigt"] else "⬜"
        frist_text = f" (bis {aufgabe['fällig']})" if aufgabe["fällig"] else ""
        col1, col2 = st.columns([5, 1])
        with col1:
            geaendert = st.checkbox(
                f"{status} {aufgabe['text']}{frist_text}",
                value=aufgabe["erledigt"],
                key=f"aufgabe_{i}",
            )
            if geaendert != aufgabe["erledigt"]:
                st.session_state["aufgaben"][i]["erledigt"] = geaendert
        with col2:
            if st.button("🗑", key=f"loesche_{i}"):
                st.session_state["aufgaben"].pop(i)
                st.rerun()


def main():
    """Hauptfunktion der Streamlit-Anwendung."""
    st.set_page_config(
        page_title="Fördermittel-Kompass",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_theme()

    st.title("🧭 Fördermittel-Kompass für Kommunen")
    st.caption("Passende Förderprogramme schneller finden — DSGVO-konform und selbstgehostet")

    # Seitennavigation
    tabs = st.tabs([
        "🔍 Förderprogramme durchsuchen",
        "🧭 Projektvorhaben eingeben",
        "🤖 KI-Matching-Ergebnis",
        "📅 Fristenkalender",
        "✅ Checklisten & Aufgaben",
    ])

    # Daten laden
    df = lade_foerderprogramme()

    # Seiten rendern
    with tabs[0]:
        seite_suche(df)
    with tabs[1]:
        seite_projekt(df)
    with tabs[2]:
        seite_matching(df)
    with tabs[3]:
        seite_fristen(df)
    with tabs[4]:
        seite_checklisten()

    # Fusszeile
    st.sidebar.markdown("---")
    st.sidebar.markdown("Fördermittel-Kompass v1.0")
    st.sidebar.markdown("Lokale KI via Ollama — keine Clouddienste")
    st.sidebar.markdown("© 2026 — MIT Lizenz")


if __name__ == "__main__":
    main()

# -- Theme Toggle --
theme_toggle_sidebar()

# -- Footer --
app_footer()

# OpenLigaDB Home Assistant Integration (HACS)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/custom-components/ha-openligadb)

Eine leistungsstarke Home Assistant Custom Integration zur Einbindung von Spieldaten, Live-Ergebnissen und Liga-Tabellen direkt von [OpenLigaDB.de](https://www.openligadb.de).

---

## ⚽ Features

- **Team-Sensoren**:
  - Status des Teams (z. B. `Live: 2 - 1`, `Upcoming (@ FC Bayern)`, `Finished: 3 - 1`).
  - `last_match`: Letztes beendetes Spiel mit Datum, Gegner, Ergebnis, Heim/Auswärts & Torschützenliste.
  - `current_match`: Live-Spiel Daten mit Spielminute & Zwischenstand.
  - `next_match`: Nächstes anstehendes Spiel mit ISO-Zeitstempel (ideal für Countdown-Karten), Gegner, Spielort & Spieltag.
  - `entity_picture`: Automatisches Einbinden des offiziellen Vereinslogos in der HA Benutzeroberfläche.

- **Liga-Sensoren**:
  - Status: Aktueller Spieltag (z. B. `4. Spieltag`).
  - `table`: Vollständige Tabelle als strukturiertes Array (Platz, Team, Spiele, Siege, Unentschieden, Niederlagen, Tore, Gegentore, Tordifferenz, Punkte & Logo-URL).

- **Adaptive Polling-Rate**:
  - Standardmäßig Abruf alle 15 Minuten.
  - Erkennt automatisch aktive Live-Spiele und schaltet während der Partie auf **1-Minuten-Intervalle** um.

- **Event-Triggers für Automationen**:
  - Feuert `openligadb_goal` Event bei neuen Toren.
  - Feuert `openligadb_match_start` und `openligadb_match_end`.

---

## 📦 Installation via HACS

1. Öffne **HACS** in deinem Home Assistant Dashboard.
2. Klicke oben rechts auf die 3 Punkte -> **Benutzerdefinierte Repositories** (*Custom repositories*).
3. Füge die URL dieses GitHub-Repositories ein:
   - **Repository**: `https://github.com/Belgadon/HA-OpenLigaDB`
   - **Kategorie**: `Integration`
4. Klicke auf **Hinzufügen** und installiere die Integration **OpenLigaDB**.
5. Starte Home Assistant neu.

---

## ⚙️ Konfiguration in Home Assistant

1. Gehe zu **Einstellungen** -> **Geräte & Dienste** -> **Integration hinzufügen**.
2. Suche nach **OpenLigaDB**.
3. Wähle aus:
   - **Team-Sensor**: Wähle die Liga (z.B. `bl1`) und dein Team (z.B. *FC Bayern München*, *BVB*, *Bayer 04 Leverkusen*).
   - **Liga-Sensor**: Wähle die Liga (z.B. `bl1` für 1. Bundesliga, `bl2`, `bl3`, `dfb` etc.).

---

## 📊 Sensor-Attribute Übersicht

### Team-Sensor (`sensor.openligadb_bayern`)

| Attribut | Typ | Beschreibung |
| :--- | :--- | :--- |
| `team_name` | String | Vollständiger Teamname |
| `entity_picture` | URL | Link zum offiziellen Vereinslogo |
| `last_match` | Object | `date`, `opponent_name`, `score_str`, `is_home`, `goals`, `group` |
| `current_match` | Object / null | Live-Daten bei laufender Partie |
| `next_match` | Object | `date`, `opponent_name`, `is_home`, `location`, `group` |

### Liga-Sensor (`sensor.openligadb_bl1_tabelle_2024`)

| Attribut | Typ | Beschreibung |
| :--- | :--- | :--- |
| `current_group` | Object | `groupName` (z.B. "4. Spieltag"), `groupOrderID` |
| `table` | Array | Rangliste aller Teams mit Platz, Punkten, Toren & W/D/L |

---

## 🖼️ Lovelace Dashboard Beispiele

### 1. Team Match Card (Markdown Card)

```yaml
type: markdown
title: "⚽ FC Bayern München - Naechstes & Letztes Spiel"
content: >
  {% set team = state_attr('sensor.openligadb_bayern', 'team_name') %}
  {% set last = state_attr('sensor.openligadb_bayern', 'last_match') %}
  {% set next = state_attr('sensor.openligadb_bayern', 'next_match') %}
  {% set current = state_attr('sensor.openligadb_bayern', 'current_match') %}

  {% if current and current.is_live %}
    ### 🔴 LIVE SPIEL
    **{{ current.opponent_name }}** ({{ 'Heim' if current.is_home else 'Auswärts' }})  
    **Spielstand: {{ current.score_str }}**
  {% endif %}

  {% if next %}
    ### 📅 Nächstes Spiel ({{ next.group }})
    **Gegner:** {{ next.opponent_name }} ({{ 'Heimspiel' if next.is_home else 'Auswärtsspiel' }})  
    **Anpfiff:** {{ as_timestamp(next.date) | timestamp_custom('%d.%m.%Y um %H:%M Uhr') }}  
    **Ort:** {{ next.location }}
  {% endif %}

  ---

  {% if last %}
    ### 📋 Letztes Spiel ({{ last.group }})
    **Gegner:** {{ last.opponent_name }}  
    **Ergebnis:** {{ last.score_str }}  
  {% endif %}
```

---

### 2. Bundesliga Tabelle (Markdown Card)

```yaml
type: markdown
title: "🏆 1. Bundesliga Tabelle"
content: >
  | # | Team | Sp. | Tore | Diff | Pkt |
  |---|:---|:---:|:---:|:---:|:---:|
  {% for row in state_attr('sensor.openligadb_bl1_tabelle_2024', 'table') %}
  | {{ row.rank }} | <img src="{{ row.team_icon_url }}" width="18" height="18"/> **{{ row.short_name or row.team_name }}** | {{ row.matches }} | {{ row.goals }}:{{ row.opponent_goals }} | {{ '+' if row.goal_diff > 0 else '' }}{{ row.goal_diff }} | **{{ row.points }}** |
  {% endfor %}
```

---

## 🔔 Automationen & Benachrichtigungen

### Beispiel: Smartphone Benachrichtigung & Licht-Blinken bei Tor

```yaml
alias: "OpenLigaDB Tor Benachrichtigung"
trigger:
  - platform: event
    event_type: openligadb_goal
condition: []
action:
  - service: notify.notify
    data:
      title: "⚽ TOR FUER {{ trigger.event.data.team }}!"
      message: "{{ trigger.event.data.goal_getter or 'Tor' }} zum {{ trigger.event.data.score }} gegen {{ trigger.event.data.opponent }}! (Minute: {{ trigger.event.data.minute }})"
  - service: light.turn_on
    target:
      entity_id: light.wohnzimmer
    data:
      flash: short
```

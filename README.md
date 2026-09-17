# OpenLigaDB Home Assistant Integration (HACS)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/custom-components/ha-openligadb)
[![Open your Home Assistant instance and open a repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Belgadon&repository=HA-OpenLigaDB&category=integration)

A powerful custom integration for Home Assistant to fetch match data, live scores, and league standings directly from [OpenLigaDB.de](https://www.openligadb.de).

---

## ⚽ Features

- **Team Sensors**:
  - Main state showing the current team status (e.g., `Live: 2 - 1`, `Upcoming (@ FC Bayern)`, `Finished: 3 - 1`).
  - `last_match`: Details of the most recently finished match, including date, opponent, result, home/away status, and a list of goal scorers.
  - `current_match`: Live match data featuring the current minute of play and the live score.
  - `next_match`: Details for the upcoming match with an ISO timestamp (perfect for countdown cards), opponent, location, and matchday.
  - `entity_picture`: Automatically fetches and displays the official club logo within the Home Assistant UI.

- **League Sensors**:
  - Main state indicating the current matchday (e.g., `Matchday 4`).
  - `table`: Comprehensive league standings provided as a structured array (Rank, Team, Matches Played, Wins, Draws, Losses, Goals For, Goals Against, Goal Difference, Points, and Logo URL).

- **Adaptive Polling Rate**:
  - Defaults to a standard 15-minute update interval.
  - Automatically detects active live matches and shifts to a **1-minute interval** during the game to ensure real-time updates.

- **Event Triggers for Automations**:
  - Fires the `openligadb_goal` event whenever a new goal is scored.
  - Fires `openligadb_match_start` and `openligadb_match_end` events.

---

## 📦 Installation via HACS

**Quick Install:** Click the badge at the top of this page to directly add this repository to your HACS instance, or follow the manual steps below.

**Manual Installation:**
1. Open **HACS** in your Home Assistant dashboard.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Add the URL of this GitHub repository:
   - **Repository**: `https://github.com/Belgadon/HA-OpenLigaDB`
   - **Category**: `Integration`
4. Click **Add** and then install the **OpenLigaDB** integration from the newly added repository.
5. Restart Home Assistant.

---

## ⚙️ Configuration in Home Assistant

1. Navigate to **Settings** -> **Devices & Services** -> **Add Integration**.
2. Search for **OpenLigaDB**.
3. Choose what you want to track:
   - **Team Sensor**: Select the league (e.g., `bl1`) and your specific team (e.g., *FC Bayern München*, *BVB*, *Bayer 04 Leverkusen*).
   - **League Sensor**: Select the league to track the standings (e.g., `bl1` for 1st Bundesliga, `bl2`, `bl3`, `dfb`, etc.).

---

## 📊 Sensor Attributes Overview

### Team Sensor (`sensor.openligadb_bayern`)

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `team_name` | String | The full name of the tracked team |
| `entity_picture` | URL | URL linking to the official club logo |
| `last_match` | Object | `date`, `opponent_name`, `score_str`, `is_home`, `goals`, `group` |
| `current_match` | Object / null | Live data (populated only when a match is currently active) |
| `next_match` | Object | `date`, `opponent_name`, `is_home`, `location`, `group` |

### League Sensor (`sensor.openligadb_bl1_tabelle_2024`)

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `current_group` | Object | `groupName` (e.g., "Matchday 4"), `groupOrderID` |
| `table` | Array | Structured ranking of all teams with their rank, points, goals, and W/D/L stats |

---

## 🖼️ Lovelace Dashboard Examples

### 1. Team Match Card (Markdown Card)

```yaml
type: markdown
title: "⚽ FC Bayern Munich - Next & Last Match"
content: >
  {% set team = state_attr('sensor.openligadb_bayern', 'team_name') %}
  {% set last = state_attr('sensor.openligadb_bayern', 'last_match') %}
  {% set next = state_attr('sensor.openligadb_bayern', 'next_match') %}
  {% set current = state_attr('sensor.openligadb_bayern', 'current_match') %}

  {% if current and current.is_live %}
    ### 🔴 LIVE MATCH
    **{{ current.opponent_name }}** ({{ 'Home' if current.is_home else 'Away' }})  
    **Score: {{ current.score_str }}**
  {% endif %}

  {% if next %}
    ### 📅 Next Match ({{ next.group }})
    **Opponent:** {{ next.opponent_name }} ({{ 'Home' if next.is_home else 'Away' }})  
    **Kickoff:** {{ as_timestamp(next.date) | timestamp_custom('%b %d, %Y at %H:%M') }}  
    **Location:** {{ next.location }}
  {% endif %}

  ---

  {% if last %}
    ### 📋 Last Match ({{ last.group }})
    **Opponent:** {{ last.opponent_name }}  
    **Result:** {{ last.score_str }}  
  {% endif %}
```

---

### 2. Bundesliga Standings Table (Markdown Card)

```yaml
type: markdown
title: "🏆 1. Bundesliga Standings"
content: >
  | # | Team | P | Goals | Diff | Pts |
  |---|:---|:---:|:---:|:---:|:---:|
  {% for row in state_attr('sensor.openligadb_bl1_tabelle_2024', 'table') %}
  | {{ row.rank }} | <img src="{{ row.team_icon_url }}" width="18" height="18"/> **{{ row.short_name or row.team_name }}** | {{ row.matches }} | {{ row.goals }}:{{ row.opponent_goals }} | {{ '+' if row.goal_diff > 0 else '' }}{{ row.goal_diff }} | **{{ row.points }}** |
  {% endfor %}
```

---

## 🔔 Automations & Notifications

### Example: Smartphone Notification & Light Flash on Goal

```yaml
alias: "OpenLigaDB Goal Notification"
trigger:
  - platform: event
    event_type: openligadb_goal
condition: []
action:
  - service: notify.notify
    data:
      title: "⚽ GOAL FOR {{ trigger.event.data.team }}!"
      message: "{{ trigger.event.data.goal_getter or 'Goal' }} makes it {{ trigger.event.data.score }} against {{ trigger.event.data.opponent }}! (Minute: {{ trigger.event.data.minute }})"
  - service: light.turn_on
    target:
      entity_id: light.living_room
    data:
      flash: short
```

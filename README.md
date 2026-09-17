# OpenLigaDB Home Assistant Integration (HACS)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/custom-components/ha-openligadb)

A powerful Home Assistant Custom Integration for integrating match data, live scores, and league standings directly from [OpenLigaDB.de](https://www.openligadb.de).

---

## ⚽ Features

- **Team Sensors**:
  - Team match state (e.g. `Live: 2 - 1`, `Upcoming (@ FC Bayern)`, `Finished: 3 - 1`).
  - `last_match`: Last completed match with date, opponent, score, home/away status, goal scorers (separated by Home & Away) & card events.
  - `current_match`: Live match details including minute & live score.
  - `next_match`: Next upcoming match with ISO timestamp (ideal for HA countdown cards), opponent, venue & matchday.
  - `entity_picture`: Automatically embeds official team crest/logo in Home Assistant UI.

- **League Sensors**:
  - State: Current matchday (e.g. `Matchday 4`).
  - `table`: Full standings as a structured array (Rank, Team, Matches, Won, Draw, Lost, Goals For, Goals Against, Goal Diff, Points & Crest URL).

- **Adaptive Polling Rate**:
  - Default polling every 15 minutes.
  - Automatically detects active live matches and switches to **1-minute polling** during live games.

- **Event Triggers for Automations**:
  - Fires `openligadb_goal` event when goals are scored live.
  - Fires `openligadb_match_start` and `openligadb_match_end` events.

---

## 📦 Installation via HACS

**Quick Install:** Click the badge to directly add this repository to your HACS instance, or follow the manual steps below.
[![Open your Home Assistant instance and open a repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Belgadon&repository=HA-OpenLigaDB&category=integration)

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

1. Go to **Settings** -> **Devices & Services** -> **Add Integration**.
2. Search for **OpenLigaDB**.
3. Choose what to set up:
   - **Team Sensor**: Select the league (e.g. `bl1`) and your team (e.g. *FC Bayern München*, *BVB*, *Bayer 04 Leverkusen*).
   - **League Sensor**: Select the league (e.g. `bl1` for 1. Bundesliga, `bl2`, `bl3`, `dfb`, etc.).

---

## 🖼️ Lovelace Dashboard HTML Cards

### 1. Match Card with Crests, Scores & Goal Scorers / Cards

Add a **Markdown Card** in your dashboard and paste this code:

```yaml
type: markdown
title: "⚽ Matchday Card"
content: >
  {% set team_sensor = 'sensor.openligadb_bayern' %}
  {% set match = state_attr(team_sensor, 'current_match') or state_attr(team_sensor, 'next_match') or state_attr(team_sensor, 'last_match') %}

  {% if match %}
  <div style="font-family: var(--primary-font-family, sans-serif); background: var(--ha-card-background, var(--card-background-color, #1e1e24)); border-radius: 12px; padding: 16px; color: var(--primary-text-color, #fff); box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
    
    <!-- Matchday Header -->
    <div style="text-align: center; font-size: 11px; font-weight: 700; opacity: 0.7; text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 12px;">
      {{ match.group or 'Matchday' }}
    </div>

    <!-- Match Header: Home (Left) | Score (Center) | Away (Right) -->
    <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
      
      <!-- Home Team (Left) -->
      <div style="flex: 1; text-align: center;">
        <img src="{{ match.home_team_icon }}" style="width: 48px; height: 48px; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));"><br>
        <span style="font-weight: 700; font-size: 14px; display: block; margin-top: 6px; line-height: 1.2;">{{ match.home_team_name }}</span>
      </div>

      <!-- Center: Score / Time -->
      <div style="text-align: center; min-width: 100px;">
        {% if match.is_live %}
          <div style="display: inline-block; background: #e53935; color: #fff; font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 10px; margin-bottom: 4px;">🔴 LIVE {{ match.minute or '' }}</div>
          <div style="font-size: 26px; font-weight: 900; letter-spacing: 2px;">{{ match.score_home }} : {{ match.score_away }}</div>
        {% elif match.is_finished %}
          <div style="display: inline-block; background: rgba(255,255,255,0.15); color: #ccc; font-size: 9px; font-weight: 700; padding: 2px 6px; border-radius: 4px; margin-bottom: 4px;">FT</div>
          <div style="font-size: 26px; font-weight: 900; letter-spacing: 2px;">{{ match.score_home }} : {{ match.score_away }}</div>
        {% else %}
          <div style="font-size: 13px; font-weight: 700; color: var(--primary-color, #03a9f4);">{{ as_timestamp(match.date) | timestamp_custom('%a. %d.%m.') }}</div>
          <div style="font-size: 18px; font-weight: 800; margin: 2px 0;">{{ as_timestamp(match.date) | timestamp_custom('%H:%M') }}</div>
          <div style="font-size: 10px; opacity: 0.7;">{{ match.location }}</div>
        {% endif %}
      </div>

      <!-- Away Team (Right) -->
      <div style="flex: 1; text-align: center;">
        <img src="{{ match.away_team_icon }}" style="width: 48px; height: 48px; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));"><br>
        <span style="font-weight: 700; font-size: 14px; display: block; margin-top: 6px; line-height: 1.2;">{{ match.away_team_name }}</span>
      </div>

    </div>

    <!-- Divider -->
    <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.12); margin: 14px 0 10px 0;">

    <!-- Match Events: Goal Scorers & Cards -->
    <div style="display: flex; justify-content: space-between; font-size: 11px; gap: 12px; line-height: 1.5;">
      
      <!-- Home Events (Left-aligned) -->
      <div style="flex: 1; text-align: left;">
        {% for goal in match.home_goals %}
          <div>⚽ <b>{{ goal.player }}</b> ({{ goal.minute }}'{% if goal.is_penalty %}, Pen.{% endif %}{% if goal.is_own_goal %}, OG{% endif %})</div>
        {% endfor %}
        {% for card in match.home_cards %}
          <div>{{ '🟨' if card.card_type == 'yellow' else '🟥' }} <b>{{ card.player }}</b> ({{ card.minute }}')</div>
        {% endfor %}
      </div>

      <!-- Away Events (Right-aligned) -->
      <div style="flex: 1; text-align: right;">
        {% for goal in match.away_goals %}
          <div>({{ goal.minute }}'{% if goal.is_penalty %}, Pen.{% endif %}{% if goal.is_own_goal %}, OG{% endif %}) <b>{{ goal.player }}</b> ⚽</div>
        {% endfor %}
        {% for card in match.away_cards %}
          <div>({{ card.minute }}') <b>{{ card.player }}</b> {{ '🟨' if card.card_type == 'yellow' else '🟥' }}</div>
        {% endfor %}
      </div>

    </div>

  </div>
  {% else %}
    <p>No match data available.</p>
  {% endif %}
```

---

### 2. Formatted Bundesliga Standings Table (HTML Table Card)

Uses a clean HTML `<table>` layout inside the Markdown Card, rendering **perfectly as a table in Home Assistant**:

```yaml
type: markdown
title: "🏆 1. Bundesliga Standings"
content: >
  <table style="width: 100%; border-collapse: collapse; font-family: var(--primary-font-family, sans-serif); font-size: 12px;">
    <thead>
      <tr style="border-bottom: 2px solid rgba(255,255,255,0.2); text-align: left; opacity: 0.7; font-size: 10px; text-transform: uppercase;">
        <th style="padding: 6px 4px; text-align: center;">#</th>
        <th style="padding: 6px 4px;">Team</th>
        <th style="padding: 6px 4px; text-align: center;">P</th>
        <th style="padding: 6px 4px; text-align: center;">Goals</th>
        <th style="padding: 6px 4px; text-align: center;">Diff</th>
        <th style="padding: 6px 4px; text-align: center;">Pts</th>
      </tr>
    </thead>
    <tbody>
      {% for row in state_attr('sensor.openligadb_bl1_tabelle_2024', 'table') %}
      <tr style="border-bottom: 1px solid rgba(255,255,255,0.06);">
        <td style="padding: 6px 4px; text-align: center; font-weight: bold;">{{ row.rank }}</td>
        <td style="padding: 6px 4px;">
          <img src="{{ row.team_icon_url }}" style="width: 16px; height: 16px; vertical-align: middle; margin-right: 6px; object-fit: contain;">
          <span style="vertical-align: middle; font-weight: 600;">{{ row.short_name or row.team_name }}</span>
        </td>
        <td style="padding: 6px 4px; text-align: center;">{{ row.matches }}</td>
        <td style="padding: 6px 4px; text-align: center;">{{ row.goals }}:{{ row.opponent_goals }}</td>
        <td style="padding: 6px 4px; text-align: center;">{{ '+' if row.goal_diff > 0 else '' }}{{ row.goal_diff }}</td>
        <td style="padding: 6px 4px; text-align: center; font-weight: 800; color: var(--primary-color, #03a9f4);">{{ row.points }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
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
      message: "{{ trigger.event.data.goal_getter or 'Goal' }} scored ({{ trigger.event.data.score }}) vs {{ trigger.event.data.opponent }}! (Minute: {{ trigger.event.data.minute }})"
  - service: light.turn_on
    target:
      entity_id: light.living_room
    data:
      flash: short
```

# OpenLigaDB Home Assistant Integration

Integration für Home Assistant zur Einbindung von Fußball-Spieldaten und Tabellen von **OpenLigaDB.de**.

## Features
- **Team-Sensoren**: Zeigt das letzte bzw. aktuelle Spiel sowie das nächste anstehende Spiel inklusive Gegner, Spielort, Uhrzeit, Endergebnis und Torschützen.
- **Liga-Sensoren**: Zeigt den aktuellen Spieltag und die vollständige Bundesliga-Tabelle mit Punkten, Toren und Platzierungen als Attribut.
- **Adaptive Polling-Rate**: Erkennt Live-Spiele automatisch und schaltet während der Partie auf 1-Minuten-Intervalle.
- **Goal Events**: Feuert `openligadb_goal`-Events bei Live-Toren für Home Assistant Automationen.

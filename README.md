# BetNova

![Python](https://img.shields.io/badge/Python-Flask-3776AB?logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-1.60-2EAD33?logo=playwright&logoColor=white)
![SQL Server](https://img.shields.io/badge/SQL_Server-pyodbc-CC2927?logo=microsoftsqlserver&logoColor=white)
![React Native](https://img.shields.io/badge/React_Native-Expo-61DAFB?logo=react&logoColor=black)

A custom REST API for Argentine football data, built by reverse-engineering [promiedos.com.ar](https://www.promiedos.com.ar/) — the main real-time football results site in Argentina, which has no public API.

The API is the core of this project. On top of it, two practical integrations were built: a **SQL Server pipeline** that ingests and persists match data, and a **React Native mobile app** for visualization.

---

## The API

Since promiedos.com.ar renders all match data dynamically via JavaScript, standard HTTP scraping is insufficient. The solution is a Flask REST API (`app.py`) that drives a headless Chromium browser via Playwright, parses the live DOM, and returns structured JSON — effectively acting as a REST layer over a site that doesn't expose one.

The API includes an in-memory cache with differentiated TTLs: live match data expires every 30 seconds, historical results are cached for 1 hour, and static data (standings, scorers) for 10 minutes.

### Endpoints

| Method | Endpoint | Cache TTL | Description |
|---|---|---|---|
| `GET` | `/health` | — | Health check |
| `GET` | `/results` | 30 s | All today's matches (live + finished + upcoming) |
| `GET` | `/live` | 30 s | Currently in-progress matches only |
| `GET` | `/results/<YYYY-MM-DD>` | 1 h | Matches for a specific past date |
| `GET` | `/game/<game_id>` | 30 s | Single match detail and events |
| `GET` | `/league/<league_id>/tabla` | 10 min | League standings table |
| `GET` | `/league/<league_id>/goleadores` | 10 min | League top scorers |

### `GET /results` and `GET /live` — Match schema

| Field | Type | Description |
|---|---|---|
| `liga` | string | Competition name (e.g. `"Liga Profesional"`) |
| `local` | string | Home team |
| `visitante` | string | Away team |
| `goles_local` | string | Home goals (`"-"` if not started) |
| `goles_visitante` | string | Away goals (`"-"` if not started) |
| `tiempo` | string | Match time (`"45"`, `"90+2"`, `"E"` for half-time, `"Final"`, or `"HH:MM"` for upcoming) |
| `game_id` | string | Match identifier, used to call `/game/<game_id>` |

**Example:**
```json
[
  {
    "liga": "Liga Profesional",
    "local": "River Plate",
    "visitante": "Boca Juniors",
    "goles_local": "1",
    "goles_visitante": "0",
    "tiempo": "67",
    "game_id": "123456"
  }
]
```

### Live match detection

The API determines whether a match is in progress by evaluating the `tiempo` field:

| `tiempo` value | State |
|---|---|
| `"HH:MM"` (e.g. `"20:30"`) | Upcoming |
| `"E"` | Half-time |
| Numeric string (`"45"`, `"90+2"`) | In progress |
| `"Final"` | Finished |

---

## SQL Server integration

`db_integration.py` consumes the `/results` endpoint and upserts match data into a SQL Server database. It handles team and competition resolution (insert-or-select), links teams to competitions, and updates live match state without creating duplicates.

### Data model

| Table | Key columns |
|---|---|
| `Equipo` | `Equipo_ID` (PK), `Nombre` |
| `Competicion` | `Competicion_ID` (PK), `Nombre`, `Deporte_ID` |
| `EquipoEnComp` | `Equipo_ID` + `Competicion_ID` (composite unique) |
| `Partido` | `Partido_ID` (PK), `Estado`, `ResultadoLocal`, `ResultadoVisitante`, `Fecha`, `Competicion_ID`, `EquipoLocal_ID`, `EquipoVisitante_ID` |

### Match state values

| Value | Meaning |
|---|---|
| `0` | Pending |
| `1` | In progress |
| `2` | Half-time |
| `3` | Finished |

### Running

```bash
# Flask API must be running first
python db_integration.py
# Prompts for SQL Server instance name
# Connects via Windows Authentication (Trusted Connection)
```

---

## React Native frontend

A simple app built with Expo that consumes the API for visualization. It displays matches grouped by league with two views: **Todos** (all matches) and **En vivo** (live only). Tapping a match navigates to the detail screen via `/game/<id>`. Pull-to-refresh supported.

---

## Setup

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.9+ |
| Node.js | 18+ |
| SQL Server | 2019+ |

### API

```bash
pip install -r requirements.txt
playwright install chromium
python app.py
# Running at http://127.0.0.1:5000
```

### Database integration

```bash
# API must be running
python db_integration.py
```

### React App

```bash
cd BetNovaFRNT
npm install
npx expo start
```

---

## Project structure

```
BetNova/
├── app.py               # Core — Flask API over promiedos.com.ar
├── db_integration.py    # SQL Server upsert pipeline
├── requirements.txt
└── BetNovaFRNT/         # React Native / Expo frontend
    ├── app/
    │   ├── index.tsx    # Match list (Todos / En vivo tabs)
    │   └── game/[id].tsx
    ├── components/
    │   └── MatchCard.tsx
    └── lib/
        └── api.ts       # API client (getLive, getResults)
```

---

## License

Private — not licensed for public distribution.

---

**Author:** [pat0nsio](https://github.com/pat0nsio)

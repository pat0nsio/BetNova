# BetNova

BetNova is a sports data tracking application that scrapes live football (soccer) match results and stores them in a database. It consists of a Python Flask scraping backend, a SQL Server database integration module, and a React Native (Expo) mobile frontend.

## Architecture

```
┌─────────────────────┐        ┌──────────────────────┐        ┌─────────────────┐
│   React Native App  │        │   Flask Scraper API   │        │   SQL Server DB │
│   (BetNovaFRNT)     │  ────▶ │   (app.py)            │        │                 │
│   Expo / TypeScript │        │   Playwright scraper  │        │  Partido        │
└─────────────────────┘        └──────────────────────┘        │  Equipo         │
                                          │                     │  Competicion    │
                                          ▼                     │  EquipoEnComp   │
                                 ┌─────────────────┐           └─────────────────┘
                                 │ db_integration  │  ────────▶        ▲
                                 │   .py           │                   │
                                 └─────────────────┘ ──────────────────┘
```

- **`app.py`** — Flask REST API that uses Playwright to scrape live match results from [promiedos.com.ar](https://www.promiedos.com.ar/).
- **`db_integration.py`** — Script that fetches data from the Flask API and persists it to a SQL Server database.
- **`BetNovaFRNT/`** — React Native mobile app built with Expo.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.9+ |
| Node.js | 18+ |
| npm | 9+ |
| SQL Server | 2019+ (for DB integration) |
| [Playwright](https://playwright.dev/) | (installed via pip) |

---

## Backend — Flask Scraper (`app.py`)

The Flask API exposes match data scraped in real time from promiedos.com.ar.

### Installation

```bash
pip install flask playwright requests pyodbc
playwright install chromium
```

### Running the server

```bash
python app.py
```

The server starts on `http://127.0.0.1:5000` by default.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check — returns a greeting string |
| `GET` | `/results` | Returns a JSON array of current match results |

#### Example `/results` response

All field names are in Spanish, matching the source data:

| Field | Description |
|-------|-------------|
| `liga` | Competition / league name |
| `local` | Home team name |
| `visitante` | Away team name |
| `goles_local` | Home team goals (or `"-"` if not started) |
| `goles_visitante` | Away team goals (or `"-"` if not started) |
| `tiempo` | Match time string (e.g. `"45"`, `"Final"`, `"E"` for half time) |

```json
[
  {
    "liga": "Liga Profesional",
    "local": "River Plate",
    "visitante": "Boca Juniors",
    "goles_local": "1",
    "goles_visitante": "0",
    "tiempo": "45"
  }
]
```

---

## Database Integration (`db_integration.py`)

Fetches results from the Flask API and upserts them into a SQL Server database named `BetNova`.

### Prerequisites

- A running SQL Server instance with a `BetNova` database.
- The following tables must exist in the database:

  | Table | Key columns |
  |-------|-------------|
  | `Equipo` | `Equipo_ID` (PK, identity), `Nombre` (varchar) |
  | `Competicion` | `Competicion_ID` (PK, identity), `Nombre` (varchar), `Deporte_ID` (int) |
  | `EquipoEnComp` | `Equipo_ID` (FK), `Competicion_ID` (FK) — composite unique |
  | `Partido` | `Partido_ID` (PK, identity), `Estado` (int), `ResultadoLocal` (int), `ResultadoVisitante` (int), `Fecha` (date), `Competicion_ID` (FK), `EquipoLocal_ID` (FK), `EquipoVisitante_ID` (FK) |

- Windows Authentication (Trusted Connection) is used by default.
- The Flask scraper (`app.py`) must be running on `http://127.0.0.1:5000`.

### Running

Make sure the Flask server is running first, then:

```bash
python db_integration.py
```

You will be prompted to enter the SQL Server name. The script will:
1. Contact the scraper API to retrieve match data.
2. Create or reuse `Equipo` (team) and `Competicion` (competition) records.
3. Insert new matches or update existing ones based on score and status changes.

### Match state values

| Value | Meaning |
|-------|---------|
| `0` | Pending (not started) |
| `1` | In progress |
| `2` | Half time |
| `3` | Finished |

---

## Frontend — React Native App (`BetNovaFRNT/`)

A mobile application built with [Expo](https://expo.dev) and React Native.

### Installation

```bash
cd BetNovaFRNT
npm install
```

### Running the app

```bash
npx expo start
```

From the terminal output you can open the app in:

- A [development build](https://docs.expo.dev/develop/development-builds/introduction/)
- [Android emulator](https://docs.expo.dev/workflow/android-studio-emulator/)
- [iOS simulator](https://docs.expo.dev/workflow/ios-simulator/)
- [Expo Go](https://expo.dev/go) — for quick on-device testing

### Linting

```bash
cd BetNovaFRNT
npm run lint
```

### Resetting the project

```bash
cd BetNovaFRNT
npm run reset-project
```

This moves the starter code to `app-example/` and creates a blank `app/` directory for a clean start. **Warning:** any custom code already in `app/` will be moved to `app-example/`.

---

## Project Structure

```
BetNova/
├── app.py               # Flask scraper API (Playwright + promiedos.com.ar)
├── db_integration.py    # SQL Server database integration script
├── .gitignore
└── BetNovaFRNT/         # React Native / Expo frontend
    ├── app/
    │   ├── _layout.tsx  # Root navigation layout
    │   └── index.tsx    # Home screen
    ├── assets/          # Images and icons
    ├── package.json
    ├── tsconfig.json
    └── eslint.config.js
```

---

## License

This project is private and not licensed for public distribution.

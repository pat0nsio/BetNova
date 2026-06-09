import re
import time
from functools import wraps

from playwright.sync_api import sync_playwright
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_URL = "https://www.promiedos.com.ar"

_CACHE = {}


TTL_LIVE = 30        # /results, /live, /game (cambian en juego)
TTL_DAY = 3600       # /results/<fecha> de días pasados
TTL_STATIC = 600     # tablas y goleadores


def cached(ttl_seconds):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = (fn.__name__, args, tuple(sorted(kwargs.items())))
            entry = _CACHE.get(key)
            now = time.time()
            if entry and (now - entry[0]) < ttl_seconds:
                return entry[1]
            result = fn(*args, **kwargs)
            # Solo cacheamos respuestas OK (no errores 5xx/4xx).
            status = result[1] if isinstance(result, tuple) else 200
            if status == 200:
                _CACHE[key] = (now, result)
            return result
        return wrapper
    return decorator


def scrape(path, selector, parser_fn, timeout=10000):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
                page.wait_for_selector(selector, state="visible", timeout=timeout)
                data = parser_fn(page)
            finally:
                browser.close()
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Parsers ------------------------------------------------------------------
def parse_homepage_matches(page):
    resultados = []
    league_containers = page.query_selector_all('div[class^="match-info_itemevent__"]')

    for container in league_containers:
        league_header = container.query_selector('div[class*="event-header_button"]')
        league_name = "N/A"
        if league_header:
            league_el = league_header.query_selector('a[href^="/league/"]')
            if league_el:
                league_name = league_el.text_content().strip()

        partidos = container.query_selector_all('a[href^="/game/"]')
        for partido in partidos:
            equipo_local_el = partido.query_selector('div[class*="team_left"]')
            equipo_visitante_el = partido.query_selector('div[class*="team_right"]')
            time_el = partido.query_selector('div[class*="time_block"]')
            scores_elements = partido.query_selector_all('span[class^="scores_scoreseventresult"]')

            goles_local = "-"
            goles_visitante = "-"
            if len(scores_elements) == 2:
                goles_local = scores_elements[0].text_content().strip()
                goles_visitante = scores_elements[1].text_content().strip()

            game_href = partido.get_attribute("href")
            game_id = game_href.split("/game/", 1)[1] if game_href and "/game/" in game_href else None

            resultados.append({
                "liga": league_name,
                "local": equipo_local_el.text_content().strip() if equipo_local_el else 'N/A',
                "visitante": equipo_visitante_el.text_content().strip() if equipo_visitante_el else 'N/A',
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
                "tiempo": time_el.text_content().strip() if time_el else 'N/A',
                "game_id": game_id,
            })

    return resultados


def _es_en_vivo(tiempo):

    if not tiempo:
        return False
    t = str(tiempo).strip().lower()
    if t in ("final", "n/a", "-"):
        return False
    if t == "e":  # entretiempo
        return True
    if re.fullmatch(r"\d{1,2}:\d{2}", t):  # horario de inicio -> aún no empieza
        return False
    return bool(re.search(r"\d", t))  # minuto de juego ("45", "45'", "90+2")


def parse_match_detail(page):
    def text(sel):
        el = page.query_selector(sel)
        return el.text_content().strip() if el else None

    eventos = []
    for ev in page.query_selector_all('div[class*="event-min"], div[class*="incident"]'):
        txt = ev.text_content().strip()
        if txt:
            eventos.append(txt)

    return {
        "local": text('div[class*="team_left"], [class*="teamname"]'),
        "visitante": text('div[class*="team_right"]'),
        "estado": text('div[class*="time_block"], [class*="status"]'),
        "eventos": eventos,
    }


def parse_standings(page):
    filas = []
    for row in page.query_selector_all('tr[class*="table_row"], tbody tr'):
        celdas = [c.text_content().strip() for c in row.query_selector_all("td")]
        if celdas:
            filas.append(celdas)
    return {"tabla": filas}


def parse_scorers(page):
    goleadores = []
    for row in page.query_selector_all('tr[class*="table_row"], tbody tr'):
        celdas = [c.text_content().strip() for c in row.query_selector_all("td")]
        if celdas:
            goleadores.append(celdas)
    return {"goleadores": goleadores}


# --- Endpoints ----------------------------------------------------------------
@app.route('/')
def hello_world():
    return 'hola'


@app.route('/health')
def health():
    return jsonify({"status": "ok"})


@app.route('/results')
@cached(TTL_LIVE)
def results():
    return scrape("/", 'div[class^="match-info_itemevent__"]', parse_homepage_matches)


@app.route('/live')
@cached(TTL_LIVE)
def live():
    def parser(page):
        return [m for m in parse_homepage_matches(page) if _es_en_vivo(m["tiempo"])]
    return scrape("/", 'div[class^="match-info_itemevent__"]', parser)


@app.route('/results/<fecha>')
@cached(TTL_DAY)
def results_by_date(fecha):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        return jsonify({"error": "Formato de fecha inválido, usar YYYY-MM-DD"}), 400
    # Promiedos acepta la fecha como query param en la portada.
    return scrape(f"/?date={fecha}", 'div[class^="match-info_itemevent__"]', parse_homepage_matches)


@app.route('/game/<path:game_id>')
@cached(TTL_LIVE)
def game_detail(game_id):
    return scrape(f"/game/{game_id}", 'div[class*="team"]', parse_match_detail)


@app.route('/league/<path:league_id>/tabla')
@cached(TTL_STATIC)
def league_standings(league_id):
    return scrape(f"/league/{league_id}", "table, tbody tr", parse_standings)


@app.route('/league/<path:league_id>/goleadores')
@cached(TTL_STATIC)
def league_scorers(league_id):
    return scrape(f"/league/{league_id}/goleadores", "table, tbody tr", parse_scorers)


if __name__ == '__main__':
    app.run(debug=True, port=5000)

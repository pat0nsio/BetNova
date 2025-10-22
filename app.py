# app.py
from playwright.sync_api import sync_playwright
from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/')
def helloWorld():
    return 'hola causas'


@app.route('/results')
def scrapeData():
    print("debug")
    resultados = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.promiedos.com.ar", wait_until="domcontentloaded")

            page.wait_for_selector(
                'div[class^="match-info_itemevent__"]', state='visible', timeout=10000)

            leagueContainers = page.query_selector_all(
                'div[class^="match-info_itemevent__"]')

            for container in leagueContainers:


                leagueHeader = container.query_selector(
                    'div[class*="event-header_button"]')
                leagueName = "N/A"

                if leagueHeader:
                    leagueEl = leagueHeader.query_selector(
                        'a[href^="/league/"]')
                    if leagueEl:
                        leagueName = leagueEl.text_content().strip()

                partidos = container.query_selector_all('a[href^="/game/"]')

                if not partidos:
                    continue

                for partido in partidos:


                    equipoLocalEl = partido.query_selector(
                        'div[class*="team_left"]')
                    equipoVisitanteEl = partido.query_selector(
                        'div[class*="team_right"]')

                    timeEl = partido.query_selector('div[class*="time_block"]')


                    scoresElements = partido.query_selector_all(
                        'span[class^="scores_scoreseventresult"]')

                    golesLocal = "-"
                    golesVisitante = "-"

                    if len(scoresElements) == 2:
                        golesLocal = scoresElements[0].text_content().strip()
                        golesVisitante = scoresElements[1].text_content().strip()

                    resultados.append({
                        "liga": leagueName,
                        "local": equipoLocalEl.text_content().strip() if equipoLocalEl else 'N/A',
                        "visitante": equipoVisitanteEl.text_content().strip() if equipoVisitanteEl else 'N/A',
                        "golesLocal": golesLocal,
                        "golesVisitante": golesVisitante,
                        "tiempo": timeEl.text_content().strip() if timeEl else 'N/A',
                    })

            browser.close()

        return jsonify(resultados)

    except Exception as e:
        print(f"Error durante el scraping: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
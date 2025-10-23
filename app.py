from playwright.sync_api import sync_playwright
from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'hola causas'


@app.route('/results')
def scrape_data():
    partidos_con_links = []
    resultados_finales = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto("https://www.promiedos.com.ar", wait_until="domcontentloaded")
            page.wait_for_selector(
                'div[class^="match-info_itemevent__"]', state='visible', timeout=10000)
            league_containers = page.query_selector_all(
                'div[class^="match-info_itemevent__"]')

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
                    link_partido = partido.get_attribute('href')
                    url_completa = f"https://www.promiedos.com.ar{link_partido}"

                    partidos_con_links.append({
                        "liga": league_name,
                        "local": equipo_local_el.text_content().strip() if equipo_local_el else 'N/A',
                        "visitante": equipo_visitante_el.text_content().strip() if equipo_visitante_el else 'N/A',
                        "goles_local": goles_local,
                        "goles_visitante": goles_visitante,
                        "tiempo": time_el.text_content().strip() if time_el else 'N/A',
                        "url_partido": url_completa
                    })

            selector_xpath_estadio = "//div[contains(@class, 'info-list_left') and (contains(., 'Estadio') or contains(., 'Estádio'))]/following-sibling::div[contains(@class, 'info-list_right')]"

            for i, partido_data in enumerate(partidos_con_links):
                nombre_estadio = "N/A"

                try:
                    page.goto(partido_data['url_partido'], wait_until="networkidle")
                    estadio_el = page.query_selector(selector_xpath_estadio)

                    if estadio_el:
                        nombre_estadio = estadio_el.text_content().strip()

                    partido_data['estadio'] = nombre_estadio

                except Exception as e_partido:
                    partido_data['estadio'] = 'N/A (Error Nav/Scrape)'

                resultados_finales.append(partido_data)

            browser.close()
            return jsonify(resultados_finales)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
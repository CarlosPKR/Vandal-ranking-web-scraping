from .utils import create_session, get_soup, clean_text
from .parser import extract_game_details, parse_score

import os
import time
import pandas as pd
from urllib.parse import urljoin

BASE_URL = "https://vandal.elespanol.com"
RANKING_URL = f"{BASE_URL}/rankings/videojuegos"
OUTPUT_PATH = "data/dataset_vandal.csv"

def scrape_vandal_games(limit=50, delay=1.5, save_path=OUTPUT_PATH):
    """
    Extrae videojuegos del ranking de Vandal y los guarda en CSV.

    limit: número máximo de juegos.
    delay: pausa entre fichas para no cargar la web.
    save_path: ruta de salida del CSV.
    """
    session = create_session()
    rows = []
    offset = 0

    while len(rows) < limit:
        if offset == 0:
            url = RANKING_URL
        else:
            url = f"{RANKING_URL}/todos/10/{offset}"

        soup = get_soup(url, session)
        items = soup.find_all("td", class_="striped4")

        for item in items:
            link_tag = item.select_one('a[href*="/juegos/"][title]')
            if not link_tag:
                continue

            href = link_tag.get("href", "")
            if "/juegos/" not in href:
                continue

            title = clean_text(link_tag.get_text())
            game_url = urljoin(BASE_URL, href)

            platform_tag = item.find("span", class_=lambda value: value and value.startswith("color"))
            platform = clean_text(platform_tag.get_text()) if platform_tag else "N/A"

            score = parse_score(item)
            print(f"Capturando: {title} [{platform}]")

            # Entramos en la ficha individual para sacar más campos.
            details = extract_game_details(game_url, session)

            rows.append(
                {
                    "Ranking": len(rows) + 1,
                    "Título": title,
                    "Plataforma": platform,
                    "Nota": score,
                    "Descripción": details["Descripcion"],
                    "Desarrollador": details["Desarrollador"],
                    "Productora": details["Productora"],
                    "Genero": details["Genero"],
                    "Fecha_lanzamiento": details["Fecha_lanzamiento"],
                    "Año_lanzamiento": details["Año_lanzamiento"],
                    "URL": game_url,
                }
            )

            if len(rows) >= limit:
                break

            time.sleep(delay)

        offset += 100

    return rows
from .utils import clean_text, get_soup

import re
import requests

# Algunas fichas meten varias etiquetas seguidas y a veces toca recortar ese sobrante.
TRAILING_LABELS = [
    "Desarrollo",
    "Producción",
    "Distribución",
    "Precio",
    "Jugadores",
    "Formato",
    "Textos",
    "Voces",
    "Online",
    "Requisitos PC",
]

def remove_trailing_labels(value):
    """Recorta otras etiquetas si se han quedado pegadas al valor."""
    pattern = r"\s+(?=(?:" + "|".join(re.escape(label) for label in TRAILING_LABELS) + r")\s*:)"
    return re.split(pattern, value, maxsplit=1)[0].strip()


def extract_labeled_value(soup, label):
    """Busca valores del tipo 'Etiqueta: valor' dentro de los li de la ficha."""
    normalized_label = label.lower().rstrip(":")

    for item in soup.find_all("li"):
        text = clean_text(item.get_text(" ", strip=True))
        if not text:
            continue

        match = re.match(rf"^{re.escape(normalized_label)}\s*:\s*(.+)$", text, flags=re.IGNORECASE)
        if match:
            return remove_trailing_labels(match.group(1).strip())

    return "N/A"


def extract_linked_value(soup, label):
    """Extrae campos como desarrollo o producción, priorizando el texto de los enlaces."""
    normalized_label = label.lower().rstrip(":")

    for item in soup.find_all("li"):
        text = clean_text(" ".join(item.stripped_strings))
        if not text:
            continue

        if re.match(rf"^{re.escape(normalized_label)}\s*:", text, flags=re.IGNORECASE):
            links = [clean_text(link.get_text(" ", strip=True)) for link in item.find_all("a")]
            if links:
                return " / ".join(links)

            parts = text.split(":", 1)
            return clean_text(parts[1]) if len(parts) > 1 else "N/A"

    return "N/A"


def extract_year(value):
    """Saca el año de una fecha si aparece en el texto."""
    match = re.search(r"(19|20)\d{2}", str(value))
    return match.group(0) if match else "N/A"


def extract_genre(soup):
    """Intenta sacar el género aunque no aparezca dentro de la ficha técnica."""
    # Primero probamos la vía normal por si en esa ficha sí viene dentro de los li.
    genre = extract_labeled_value(soup, "Género/s")
    if genre != "N/A":
        return genre

    # En muchas páginas de Vandal el género aparece arriba, junto a Plataformas.
    full_text = clean_text(soup.get_text(" ", strip=True))
    match = re.search(
        r"Género/s\s*:\s*(.+?)(?=\s+Plataformas\s*:|\s+Ficha técnica|\s+Más información|\s+A la venta en España)",
        full_text,
        flags=re.IGNORECASE,
    )
    if match:
        return clean_text(match.group(1))

    return "N/A"


def extract_description(soup):
    """Intenta recuperar la descripción principal del videojuego."""
    # Primero intentamos localizar el bloque típico de información del juego.
    heading_patterns = ("información del juego", "resumen")

    for heading in soup.find_all(["h1", "h2", "h3", "strong", "div", "span"]):
        heading_text = clean_text(heading.get_text(" ", strip=True)).lower()
        if not any(pattern in heading_text for pattern in heading_patterns):
            continue

        for block in heading.find_all_next(["p", "div"], limit=10):
            text = clean_text(block.get_text(" ", strip=True))
            if len(text) < 80:
                continue
            if "a la venta en españa" in text.lower():
                continue
            return text

    # Si arriba no sale bien, probamos con la meta description.
    meta_description = soup.find("meta", attrs={"name": "description"})
    if meta_description and meta_description.get("content"):
        return clean_text(meta_description["content"])

    # Como última opción, cogemos el párrafo largo más razonable.
    paragraphs = []
    for paragraph in soup.find_all("p"):
        text = clean_text(paragraph.get_text(" ", strip=True))
        if len(text) >= 80:
            paragraphs.append(text)

    return max(paragraphs, key=len, default="N/A")


def extract_game_details(game_url, session):
    """Entra en la ficha de cada juego y saca los datos extra."""
    try:
        soup = get_soup(game_url, session)
        release_date = extract_labeled_value(soup, "Fecha de lanzamiento")

        return {
            "Desarrollador": extract_linked_value(soup, "Desarrollo"),
            "Productora": extract_linked_value(soup, "Producción"),
            "Genero": extract_genre(soup),
            "Fecha_lanzamiento": release_date,
            "Año_lanzamiento": extract_year(release_date),
            "Descripcion": extract_description(soup),
        }
    except requests.RequestException as error:
        print(f"No se pudieron obtener los detalles de {game_url}: {error}")
        return {
            "Desarrollador": "Error",
            "Productora": "Error",
            "Genero": "Error",
            "Fecha_lanzamiento": "Error",
            "Año_lanzamiento": "Error",
            "Descripcion": "Error",
        }


def parse_score(item):
    """Intenta convertir la nota a número; si no puede, la deja como texto."""
    score_tag = item.select_one(".circuloanalisis_saga a, .circuloanalisis_saga")
    score_text = clean_text(score_tag.get_text(" ", strip=True)) if score_tag else "N/A"

    try:
        return float(score_text.replace(",", "."))
    except ValueError:
        return score_text
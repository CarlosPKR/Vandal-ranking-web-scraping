import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

def clean_text(text):
    """Limpia espacios y saltos de línea repetidos."""
    return re.sub(r"\s+", " ", text or "").strip()


def create_session():
    """Crea una sesión para reutilizar la conexión en todas las peticiones."""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def get_soup(url, session):
    """Descarga una página y la devuelve parseada con BeautifulSoup."""
    response = session.get(url, timeout=20)
    response.raise_for_status()

    # Ajustamos la codificación si requests no la detecta bien.
    if not response.encoding or response.encoding.lower() == "utf-8":
        response.encoding = response.apparent_encoding

    return BeautifulSoup(response.text, "html.parser")
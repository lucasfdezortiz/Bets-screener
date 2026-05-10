"""
Recolector de datos de tenis.

Fuente primaria : scraping de atptour.com / wtatennis.com para rankings
Fuente fallback : entrada manual del usuario (puntos ATP/WTA)
"""

import requests
from bs4 import BeautifulSoup

HEADERS_WEB = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _get_atp_ranking_points(player_name: str) -> int | None:
    """
    Intenta obtener los puntos ATP de un jugador desde la web de ATP.
    Retorna None si no lo encuentra (se pedirá al usuario).
    """
    url = "https://www.atptour.com/en/rankings/singles"
    try:
        r = requests.get(url, headers=HEADERS_WEB, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        # La tabla de rankings tiene class "mega-table"
        table = soup.find("table", class_="mega-table")
        if not table:
            return None

        name_lower = player_name.lower()
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            player_cell = cells[1].get_text(strip=True).lower()
            if name_lower in player_cell or any(
                part in player_cell for part in name_lower.split()
            ):
                try:
                    points_text = cells[3].get_text(strip=True).replace(",", "")
                    return int(points_text)
                except ValueError:
                    pass
    except Exception as e:
        print(f"  [Tennis/ATP] Error al obtener ranking de {player_name}: {e}")
    return None


def _get_wta_ranking_points(player_name: str) -> int | None:
    """Mismo proceso para WTA."""
    url = "https://www.wtatennis.com/rankings/singles"
    try:
        r = requests.get(url, headers=HEADERS_WEB, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        name_lower = player_name.lower()
        for row in soup.find_all("tr"):
            text = row.get_text(" ", strip=True).lower()
            if name_lower in text or any(p in text for p in name_lower.split()):
                # Buscar número de puntos en la fila
                for cell in row.find_all("td"):
                    txt = cell.get_text(strip=True).replace(",", "")
                    if txt.isdigit() and int(txt) > 10:
                        return int(txt)
    except Exception as e:
        print(f"  [Tennis/WTA] Error al obtener ranking de {player_name}: {e}")
    return None


def get_player_data(
    player_name: str,
    tour: str = "atp",
    manual_points: int | None = None,
) -> dict:
    """
    Devuelve datos de un jugador de tenis.

    Args:
        player_name: nombre del jugador (ej. "Carlos Alcaraz")
        tour: "atp" o "wta"
        manual_points: puntos manuales si el scraping falla

    Returns:
        dict con name, points, ranking (si disponible)
    """
    points = None

    if manual_points is None:
        print(f"  [Tennis] Buscando puntos de {player_name} ({tour.upper()})...")
        if tour.lower() == "atp":
            points = _get_atp_ranking_points(player_name)
        else:
            points = _get_wta_ranking_points(player_name)

        if points is None:
            print(f"  [Tennis] No se encontraron puntos automáticos para {player_name}.")
    else:
        points = manual_points

    return {
        "name": player_name,
        "points": points or 0,
        "tour": tour.upper(),
    }


def get_tennis_match_data(
    player1_name: str,
    player2_name: str,
    tour: str = "atp",
    surface: str = "hard",
    best_of: int = 3,
    p1_points: int | None = None,
    p2_points: int | None = None,
) -> dict:
    """
    Recoge datos de un partido de tenis.

    Args:
        player1_name: nombre del favorito / local (jugador 1)
        player2_name: nombre del rival (jugador 2)
        tour: "atp" o "wta"
        surface: "hard", "clay", "grass"
        best_of: 3 o 5
        p1_points / p2_points: puntos manuales (si el scraping falla)

    Returns:
        dict con datos de ambos jugadores y configuración del partido.
    """
    p1 = get_player_data(player1_name, tour, p1_points)
    p2 = get_player_data(player2_name, tour, p2_points)

    return {
        "player1": p1,
        "player2": p2,
        "surface": surface.lower(),
        "best_of": best_of,
        "tour": tour.upper(),
    }

"""
Módulo 1: Recolector de datos de partidos de fútbol.

Fuente primaria : football-data.org API v4
Fuente fallback : FBref.com (web scraping con BeautifulSoup + pandas)
"""

import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from config import FOOTBALL_API_BASE, COMPETITION_CODES

# Mapa de IDs de FBref por código de competición
FBREF_COMP_IDS = {
    "PD": ("12", "La-Liga"),
    "PL": ("9", "Premier-League"),
    "BL1": ("20", "Bundesliga"),
    "SA": ("11", "Serie-A"),
    "FL1": ("13", "Ligue-1"),
    "CL": ("8", "Champions-League"),
}

HEADERS_API = lambda key: {"X-Auth-Token": key}
HEADERS_WEB = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


# ---------------------------------------------------------------------------
# Fuente primaria: football-data.org
# ---------------------------------------------------------------------------

def _api_get(path: str, api_key: str, params: dict | None = None) -> dict | None:
    url = f"{FOOTBALL_API_BASE}{path}"
    try:
        r = requests.get(url, headers=HEADERS_API(api_key), params=params or {}, timeout=10)
        if r.status_code == 429:
            print("  [API] Rate limit alcanzado, esperando 60s...")
            time.sleep(61)
            r = requests.get(url, headers=HEADERS_API(api_key), params=params or {}, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"  [API] Error en {path}: {e}")
        return None


def _find_team_id(name: str, competition_code: str, api_key: str) -> int | None:
    """Busca el ID de un equipo por nombre dentro de una competición."""
    data = _api_get(f"/competitions/{competition_code}/teams", api_key)
    if not data:
        return None
    name_lower = name.lower()
    for team in data.get("teams", []):
        if (name_lower in team["name"].lower() or
                name_lower in team.get("shortName", "").lower() or
                name_lower in team.get("tla", "").lower()):
            return team["id"]
    return None


def _get_standings(competition_code: str, api_key: str) -> list[dict]:
    """Devuelve la tabla de posiciones como lista de dicts."""
    data = _api_get(f"/competitions/{competition_code}/standings", api_key)
    if not data:
        return []
    standings = data.get("standings", [])
    # La primera tabla suele ser la general (TOTAL)
    for table in standings:
        if table.get("type") == "TOTAL":
            return table.get("table", [])
    return standings[0].get("table", []) if standings else []


def _extract_team_stats_from_standings(team_id: int, table: list[dict]) -> dict | None:
    """Extrae stats de un equipo de la tabla de clasificación."""
    for row in table:
        if row["team"]["id"] == team_id:
            played = row.get("playedGames", 1) or 1
            return {
                "position": row.get("position", 0),
                "goals_scored_avg": round(row.get("goalsFor", 0) / played, 3),
                "goals_conceded_avg": round(row.get("goalsAgainst", 0) / played, 3),
                "played": played,
            }
    return None


def _get_team_form(team_id: int, api_key: str, limit: int = 5) -> list[dict]:
    """Últimos `limit` partidos del equipo."""
    data = _api_get(f"/teams/{team_id}/matches", api_key,
                    params={"status": "FINISHED", "limit": limit})
    if not data:
        return []
    form = []
    for match in data.get("matches", [])[-limit:]:
        home_id = match["homeTeam"]["id"]
        score = match["score"]["fullTime"]
        home_g = score.get("home") or 0
        away_g = score.get("away") or 0

        if team_id == home_id:
            scored, conceded = home_g, away_g
        else:
            scored, conceded = away_g, home_g

        if scored > conceded:
            result = "W"
        elif scored == conceded:
            result = "D"
        else:
            result = "L"

        form.append({"result": result, "scored": scored, "conceded": conceded,
                     "date": match.get("utcDate", "")[:10]})
    return form


def _get_h2h(team_id_home: int, team_id_away: int, api_key: str, limit: int = 50) -> list[dict]:
    """Filtra partidos H2H de los últimos ~50 partidos de cada equipo."""
    data = _api_get(f"/teams/{team_id_home}/matches", api_key,
                    params={"status": "FINISHED", "limit": limit})
    if not data:
        return []
    h2h = []
    for match in data.get("matches", []):
        ids = {match["homeTeam"]["id"], match["awayTeam"]["id"]}
        if team_id_home in ids and team_id_away in ids:
            score = match["score"]["fullTime"]
            h2h.append({
                "date": match.get("utcDate", "")[:10],
                "home": match["homeTeam"]["name"],
                "away": match["awayTeam"]["name"],
                "home_goals": score.get("home") or 0,
                "away_goals": score.get("away") or 0,
            })
    return h2h[-10:]  # últimos 10


def _league_avg_from_table(table: list[dict]) -> float:
    """Calcula la media de goles por partido de la liga a partir de la tabla."""
    total_goals = sum(r.get("goalsFor", 0) for r in table)
    total_played = sum(r.get("playedGames", 0) for r in table)
    if total_played == 0:
        return 1.35
    return round(total_goals / total_played, 4)


def _collect_from_api(home_name: str, away_name: str, comp_code: str, api_key: str) -> dict | None:
    print(f"  [API] Buscando datos para {home_name} vs {away_name} ({comp_code})...")

    table = _get_standings(comp_code, api_key)
    if not table:
        print("  [API] No se pudo obtener la tabla de posiciones.")
        return None

    home_id = _find_team_id(home_name, comp_code, api_key)
    time.sleep(6)  # respetar rate limit
    away_id = _find_team_id(away_name, comp_code, api_key)
    time.sleep(6)

    if not home_id:
        print(f"  [API] Equipo local '{home_name}' no encontrado.")
        return None
    if not away_id:
        print(f"  [API] Equipo visitante '{away_name}' no encontrado.")
        return None

    home_stats = _extract_team_stats_from_standings(home_id, table)
    away_stats = _extract_team_stats_from_standings(away_id, table)

    if not home_stats or not away_stats:
        print("  [API] No se pudieron obtener estadísticas de los equipos.")
        return None

    league_avg = _league_avg_from_table(table)

    time.sleep(6)
    home_form = _get_team_form(home_id, api_key)
    time.sleep(6)
    away_form = _get_team_form(away_id, api_key)
    time.sleep(6)
    h2h = _get_h2h(home_id, away_id, api_key)

    return {
        "home": {
            "name": home_name,
            "id": home_id,
            **home_stats,
            "form": home_form,
        },
        "away": {
            "name": away_name,
            "id": away_id,
            **away_stats,
            "form": away_form,
        },
        "h2h": h2h,
        "league_avg_goals": league_avg,
        "source": "football-data.org",
    }


# ---------------------------------------------------------------------------
# Fuente fallback: FBref.com
# ---------------------------------------------------------------------------

def _collect_from_fbref(home_name: str, away_name: str, comp_code: str) -> dict | None:
    comp_info = FBREF_COMP_IDS.get(comp_code)
    if not comp_info:
        print(f"  [FBref] Competición '{comp_code}' no soportada en fallback.")
        return None

    comp_id, comp_slug = comp_info
    url = f"https://fbref.com/en/comps/{comp_id}/{comp_slug}-Stats"
    print(f"  [FBref] Scraping {url} ...")

    try:
        r = requests.get(url, headers=HEADERS_WEB, timeout=15)
        r.raise_for_status()
        tables = pd.read_html(r.text, attrs={"id": f"results{comp_id}021_overall"})
        if not tables:
            # Intentar con la primera tabla que contenga "Squad"
            tables = pd.read_html(r.text)
    except Exception as e:
        print(f"  [FBref] Error al descargar/parsear: {e}")
        return None

    df = tables[0]
    # Normalizar nombres de columnas (pueden ser multi-nivel)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(c).strip() for c in df.columns]

    # Buscar columnas clave
    col_map = {}
    for col in df.columns:
        cl = col.lower()
        if "squad" in cl or "equipo" in cl or "club" in cl:
            col_map["squad"] = col
        elif "mp" in cl and "match" in cl.replace("mp", "match"):
            col_map["mp"] = col
        elif col.strip().upper() in ("MP", "PJ"):
            col_map["mp"] = col
        elif col.strip() in ("GF", "Gls", "Goals For"):
            col_map["gf"] = col
        elif col.strip() in ("GA", "Goals Against"):
            col_map["ga"] = col

    # Búsqueda más amplia si no encontramos las columnas
    for col in df.columns:
        if col not in col_map.values():
            if df[col].dtype in ("int64", "float64"):
                pass  # columna numérica, seguimos buscando

    if "squad" not in col_map:
        # Usar primera columna de texto como squad
        for col in df.columns:
            if df[col].dtype == object:
                col_map["squad"] = col
                break

    if "squad" not in col_map:
        print("  [FBref] No se encontró columna de equipo.")
        return None

    def find_team_row(name: str):
        name_lower = name.lower()
        for _, row in df.iterrows():
            squad = str(row.get(col_map["squad"], "")).lower()
            if name_lower in squad or squad in name_lower:
                return row
        return None

    home_row = find_team_row(home_name)
    away_row = find_team_row(away_name)

    if home_row is None or away_row is None:
        print(f"  [FBref] No se encontraron datos para {home_name} o {away_name}.")
        return None

    def safe_avg(row, col_key, default=1.35):
        if col_key not in col_map:
            return default
        try:
            mp = float(row.get(col_map.get("mp", "MP"), 1)) or 1
            val = float(row.get(col_map[col_key], default * mp))
            return round(val / mp, 3)
        except (ValueError, TypeError):
            return default

    # Calcular media de liga
    league_total_goals = 0
    league_total_played = 0
    for _, row in df.iterrows():
        try:
            mp = float(row.get(col_map.get("mp", "MP"), 0))
            gf = float(row.get(col_map.get("gf", "GF"), 0))
            league_total_goals += gf
            league_total_played += mp
        except (ValueError, TypeError):
            continue

    league_avg = round(league_total_goals / max(league_total_played, 1), 4)

    return {
        "home": {
            "name": home_name,
            "position": 0,  # FBref no siempre da posición fácilmente
            "goals_scored_avg": safe_avg(home_row, "gf"),
            "goals_conceded_avg": safe_avg(home_row, "ga"),
            "played": int(home_row.get(col_map.get("mp", "MP"), 1)),
            "form": [],
        },
        "away": {
            "name": away_name,
            "position": 0,
            "goals_scored_avg": safe_avg(away_row, "gf"),
            "goals_conceded_avg": safe_avg(away_row, "ga"),
            "played": int(away_row.get(col_map.get("mp", "MP"), 1)),
            "form": [],
        },
        "h2h": [],
        "league_avg_goals": league_avg if league_avg > 0 else 1.35,
        "source": "FBref.com",
    }


# ---------------------------------------------------------------------------
# Punto de entrada público
# ---------------------------------------------------------------------------

def get_match_data(
    home_team: str,
    away_team: str,
    competition: str,
    api_key: str | None = None,
) -> dict | None:
    """
    Recoge datos del partido. Intenta la API primero, luego FBref como fallback.

    Args:
        home_team: nombre del equipo local (ej. "Real Madrid")
        away_team: nombre del equipo visitante (ej. "Barcelona")
        competition: nombre o código de la competición (ej. "laliga", "PD")
        api_key: clave de football-data.org (None = saltar API)

    Returns:
        dict con los datos del partido, o None si no se pudo obtener nada.
    """
    # Normalizar código de competición
    comp_code = COMPETITION_CODES.get(competition.lower(), competition.upper())

    data = None

    if api_key:
        data = _collect_from_api(home_team, away_team, comp_code, api_key)

    if data is None:
        print("  [Fallback] Intentando FBref.com...")
        data = _collect_from_fbref(home_team, away_team, comp_code)

    return data

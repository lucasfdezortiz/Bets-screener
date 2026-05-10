"""
Escáner diario de value bets.

Flujo:
  1. The Odds API  → partidos próximos + cuotas (Winamax, Pinnacle, William Hill)
  2. football-data.org / ESPN → estadísticas de equipos
  3. Modelo de Poisson → probabilidades
  4. Kelly calculator → edge y apuesta recomendada
  5. Ranking de top value bets del día
"""

import time
import difflib
import requests
from datetime import datetime, timezone, timedelta

from modules.poisson_model import calculate_probabilities
from modules.kelly_calculator import analyze_bets
from config import FOOTBALL_API_BASE, FOOTBALL_DATA_API_KEY, BANKROLL

ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Ligas soportadas: clave Odds API → código football-data.org (None = usar ESPN)
LEAGUE_MAP = {
    "soccer_spain_la_liga":        "PD",
    "soccer_epl":                  "PL",
    "soccer_germany_bundesliga":   "BL1",
    "soccer_italy_serie_a":        "SA",
    "soccer_france_ligue_one":     "FL1",
    "soccer_spain_segunda_division": None,  # ESPN fallback
}

# Bookmakers preferidos (orden de prioridad para mostrar cuotas)
BOOKMAKERS = ["winamax_fr", "pinnacle", "williamhill"]
PRIMARY_BM  = "winamax_fr"   # cuotas que se usan para el cálculo de edge

HEADERS_API  = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
HEADERS_ESPN = {"User-Agent": "Mozilla/5.0"}


# ---------------------------------------------------------------------------
# 1. Odds API
# ---------------------------------------------------------------------------

def fetch_odds(leagues: list[str], odds_api_key: str, days_ahead: int = 2) -> list[dict]:
    """
    Obtiene partidos + cuotas de las ligas indicadas para las próximas `days_ahead` días.
    Devuelve lista de partidos con sus cuotas.
    """
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)

    all_matches = []
    for league_key in leagues:
        params = {
            "apiKey":      odds_api_key,
            "regions":     "eu",
            "markets":     "h2h,totals",
            "oddsFormat":  "decimal",
            "bookmakers":  ",".join(BOOKMAKERS),
            "commenceTimeFrom": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "commenceTimeTo":   end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        try:
            r = requests.get(f"{ODDS_API_BASE}/sports/{league_key}/odds",
                             params=params, timeout=12)
            r.raise_for_status()
            league_matches = r.json()
            for match in league_matches:
                match["_league_key"] = league_key
            all_matches.extend(league_matches)
        except Exception as e:
            print(f"  [OddsAPI] Error en {league_key}: {e}")

    return all_matches


def derive_dnb_odds(home_odds: float, draw_odds: float, away_odds: float,
                     dnb_margin: float = 0.04) -> tuple[float, float]:
    """
    Deriva las cuotas DNB (apuesta no válida en caso de empate) a partir de las
    cuotas 1X2 eliminando el margen de la casa y aplicando uno típico para DNB.

    Fórmula:
      1. Prob sin margen: p_h, p_d, p_a = normalizar probabilidades implícitas
      2. DNB home fair = (p_h + p_a) / p_h
      3. Aplicar margen DNB típico (~4%): DNB_bm = fair / (1 + margin)
    """
    impl_h = 1 / home_odds
    impl_d = 1 / draw_odds
    impl_a = 1 / away_odds
    total  = impl_h + impl_d + impl_a

    p_h = impl_h / total   # probabilidad sin margen
    p_a = impl_a / total

    fair_dnb_home = (p_h + p_a) / p_h
    fair_dnb_away = (p_h + p_a) / p_a

    # Aplicar margen: la casa reduce la cuota para quedarse con margen
    bm_dnb_home = round(fair_dnb_home / (1 + dnb_margin), 2)
    bm_dnb_away = round(fair_dnb_away / (1 + dnb_margin), 2)

    return bm_dnb_home, bm_dnb_away


def extract_bookmaker_odds(match: dict, bm_key: str) -> dict | None:
    """
    Extrae cuotas de un bookmaker concreto para un partido.
    Incluye h2h, totals y DNB derivado de h2h.
    """
    for bm in match.get("bookmakers", []):
        if bm["key"] == bm_key:
            result = {}
            for mkt in bm.get("markets", []):
                if mkt["key"] == "h2h":
                    for o in mkt["outcomes"]:
                        if o["name"] == match["home_team"]:
                            result["home_win"] = o["price"]
                        elif o["name"] == match["away_team"]:
                            result["away_win"] = o["price"]
                        elif o["name"] == "Draw":
                            result["draw"] = o["price"]
                elif mkt["key"] == "totals":
                    for o in mkt["outcomes"]:
                        if o["name"] == "Over":
                            result["over_2_5"] = o["price"]
                        elif o["name"] == "Under":
                            result["under_2_5"] = o["price"]

            # Derivar DNB si tenemos las tres cuotas h2h
            if all(k in result for k in ("home_win", "draw", "away_win")):
                dnb_h, dnb_a = derive_dnb_odds(
                    result["home_win"], result["draw"], result["away_win"]
                )
                result["dnb_home"] = dnb_h
                result["dnb_away"] = dnb_a

            return result if result else None
    return None


# ---------------------------------------------------------------------------
# 2. Estadísticas de equipos
# ---------------------------------------------------------------------------

_standings_cache: dict[str, list] = {}

def _get_standings_fd(comp_code: str) -> list[dict]:
    """Obtiene tabla de la liga desde football-data.org (con caché)."""
    if comp_code in _standings_cache:
        return _standings_cache[comp_code]
    try:
        r = requests.get(f"{FOOTBALL_API_BASE}/competitions/{comp_code}/standings",
                         headers=HEADERS_API, timeout=10)
        r.raise_for_status()
        data = r.json()
        table = next(
            (t["table"] for t in data.get("standings", []) if t.get("type") == "TOTAL"),
            data.get("standings", [{}])[0].get("table", [])
        )
        _standings_cache[comp_code] = table
        time.sleep(6)   # respetar rate limit
        return table
    except Exception as e:
        print(f"  [FD] Error standings {comp_code}: {e}")
        return []


def _get_standings_espn(espn_league: str) -> list[dict]:
    """Obtiene tabla de ESPN para ligas no cubiertas por football-data.org."""
    cache_key = f"espn_{espn_league}"
    if cache_key in _standings_cache:
        return _standings_cache[cache_key]
    try:
        url = f"https://site.api.espn.com/apis/v2/sports/soccer/{espn_league}/standings"
        r = requests.get(url, headers=HEADERS_ESPN, timeout=10)
        r.raise_for_status()
        rows = []
        for g in r.json().get("children", []):
            for entry in g.get("standings", {}).get("entries", []):
                stats = {s["name"]: s.get("value", 0) for s in entry.get("stats", [])}
                rows.append({
                    "team": {"name": entry["team"]["displayName"], "id": 0},
                    "position":      int(stats.get("rank", 0)),
                    "playedGames":   int(stats.get("gamesPlayed", 1)),
                    "goalsFor":      int(stats.get("pointsFor", 0)),
                    "goalsAgainst":  int(stats.get("pointsAgainst", 0)),
                })
        _standings_cache[cache_key] = rows
        return rows
    except Exception as e:
        print(f"  [ESPN] Error standings {espn_league}: {e}")
        return []


ESPN_LEAGUE_MAP = {
    "soccer_spain_segunda_division": "esp.2",
    "soccer_germany_bundesliga2":    "ger.2",
    "soccer_france_ligue_two":       "fra.2",
    "soccer_italy_serie_b":          "ita.2",
}


def _fuzzy_match(name: str, candidates: list[str], cutoff: float = 0.55) -> str | None:
    """Búsqueda por nombre aproximado."""
    name_l = name.lower()
    # Búsqueda directa primero
    for c in candidates:
        if name_l in c.lower() or c.lower() in name_l:
            return c
    # Búsqueda difusa
    matches = difflib.get_close_matches(name_l, [c.lower() for c in candidates],
                                        n=1, cutoff=cutoff)
    if matches:
        for c in candidates:
            if c.lower() == matches[0]:
                return c
    return None


def get_team_stats_from_table(team_name: str, table: list[dict]) -> dict | None:
    """Busca las estadísticas de un equipo en la tabla."""
    names = [row["team"]["name"] for row in table]
    matched = _fuzzy_match(team_name, names)
    if not matched:
        return None
    row = next(r for r in table if r["team"]["name"] == matched)
    played = max(row.get("playedGames", 1), 1)
    return {
        "name":               team_name,
        "position":           row.get("position", 0),
        "goals_scored_avg":   row.get("goalsFor", 0) / played,
        "goals_conceded_avg": row.get("goalsAgainst", 0) / played,
        "played":             played,
        "form":               [],
    }


def get_league_avg(table: list[dict]) -> float:
    total_goals  = sum(r.get("goalsFor", 0)    for r in table)
    total_played = sum(r.get("playedGames", 0) for r in table)
    return round(total_goals / max(total_played, 1), 4)


def get_table_for_league(league_key: str) -> tuple[list[dict], float]:
    """Devuelve (tabla, media_goles) para la liga indicada."""
    fd_code = LEAGUE_MAP.get(league_key)
    if fd_code:
        table = _get_standings_fd(fd_code)
    else:
        espn_code = ESPN_LEAGUE_MAP.get(league_key, "")
        table = _get_standings_espn(espn_code) if espn_code else []
    league_avg = get_league_avg(table) if table else 1.35
    return table, league_avg


# ---------------------------------------------------------------------------
# 3. Escáner principal
# ---------------------------------------------------------------------------

def scan_value_bets(
    odds_api_key: str,
    leagues: list[str] | None = None,
    days_ahead: int = 2,
    min_edge: float = 3.0,
    bookmaker: str = PRIMARY_BM,
    bankroll: float = BANKROLL,
) -> list[dict]:
    """
    Escanea todos los partidos próximos y devuelve los value bets ordenados por edge.

    Args:
        odds_api_key : clave de the-odds-api.com
        leagues      : lista de claves de liga (None = todas las soportadas)
        days_ahead   : cuántos días hacia adelante buscar
        min_edge     : edge mínimo (%) para incluir en los resultados
        bookmaker    : bookmaker cuyas cuotas se usan para el cálculo
        bankroll     : bankroll en euros

    Returns:
        Lista de dicts con los value bets encontrados, ordenados por edge desc.
    """
    if leagues is None:
        leagues = list(LEAGUE_MAP.keys())

    print(f"\n[Scanner] Obteniendo cuotas para {len(leagues)} ligas...")
    matches = fetch_odds(leagues, odds_api_key, days_ahead)
    print(f"[Scanner] {len(matches)} partidos encontrados.")

    # Pre-cargar tablas de cada liga (una sola request por liga)
    tables: dict[str, tuple[list, float]] = {}
    for league_key in set(m["_league_key"] for m in matches):
        print(f"  [Scanner] Cargando estadísticas de {league_key}...")
        tables[league_key] = get_table_for_league(league_key)

    value_bets = []

    for match in matches:
        home_name = match["home_team"]
        away_name = match["away_team"]
        league_key = match["_league_key"]
        kickoff = match["commence_time"][:16].replace("T", " ")

        table, league_avg = tables.get(league_key, ([], 1.35))
        if not table:
            continue

        home_stats = get_team_stats_from_table(home_name, table)
        away_stats = get_team_stats_from_table(away_name, table)
        if not home_stats or not away_stats:
            continue

        match_data = {
            "home": home_stats,
            "away": away_stats,
            "league_avg_goals": league_avg,
        }

        try:
            probs = calculate_probabilities(match_data)
        except Exception:
            continue

        # Cuotas del bookmaker primario
        odds = extract_bookmaker_odds(match, bookmaker)
        if not odds:
            for bm_fallback in BOOKMAKERS:
                odds = extract_bookmaker_odds(match, bm_fallback)
                if odds:
                    break
        if not odds:
            continue

        # Las probabilidades DNB no las da calculate_probabilities, las pasa analyze_bets
        # directamente desde home_win/away_win/draw — no necesitan clave adicional en probs

        results = analyze_bets(probs, odds, bankroll)

        for r in results:
            if r["edge"] >= min_edge:
                is_dnb = r.get("is_dnb", False)
                value_bets.append({
                    "league":   league_key.replace("soccer_", "").replace("_", " ").title(),
                    "match":    f"{home_name} vs {away_name}",
                    "kickoff":  kickoff,
                    "market":   r["label"],
                    "is_dnb":   is_dnb,
                    "odds":     r["odds"],
                    "implied":  r["implied_prob"],
                    "model":    r["model_prob"],
                    "edge":     r["edge"],
                    "ev_10":    r["ev_10"],
                    "kelly":    r["kelly_stake"],
                    "verdict":  r["verdict"],
                    "lambda_h": probs["lambda_home"],
                    "lambda_a": probs["lambda_away"],
                })

    value_bets.sort(key=lambda x: x["edge"], reverse=True)
    return value_bets

"""
Escáner de value bets para tenis.

Modelo: Pinnacle como referencia sharp (precios sin margen = probabilidad real).
Target: Winamax FR (cuota donde apostamos).
Edge = P(Pinnacle sin margen) − P_implícita(Winamax)

No se necesitan rankings externos. Pinnacle ya incorpora forma,
superficie, H2H, lesiones y condiciones del torneo.
"""

import requests
from datetime import datetime, timezone, timedelta
from config import BANKROLL, KELLY_FRACTION, VALUE_BET_THRESHOLD, MARGINAL_THRESHOLD

ODDS_API_BASE = "https://api.the-odds-api.com/v4"

# Todos los torneos ATP/WTA soportados por la API
TENNIS_SPORTS = [
    "tennis_atp_aus_open_singles",
    "tennis_atp_french_open",
    "tennis_atp_wimbledon",
    "tennis_atp_us_open",
    "tennis_atp_italian_open",
    "tennis_atp_madrid_open",
    "tennis_atp_canadian_open",
    "tennis_atp_cincinnati_open",
    "tennis_atp_indian_wells",
    "tennis_atp_monte_carlo_masters",
    "tennis_atp_shanghai_masters",
    "tennis_atp_paris_masters",
    "tennis_atp_barcelona_open",
    "tennis_atp_dubai",
    "tennis_atp_china_open",
    "tennis_atp_miami_open",
    "tennis_atp_munich",
    "tennis_atp_qatar_open",
    "tennis_wta_aus_open_singles",
    "tennis_wta_french_open",
    "tennis_wta_wimbledon",
    "tennis_wta_us_open",
    "tennis_wta_italian_open",
    "tennis_wta_madrid_open",
    "tennis_wta_canadian_open",
    "tennis_wta_cincinnati_open",
    "tennis_wta_indian_wells",
    "tennis_wta_dubai",
    "tennis_wta_china_open",
    "tennis_wta_miami_open",
    "tennis_wta_qatar_open",
    "tennis_wta_stuttgart_open",
    "tennis_wta_charleston_open",
    "tennis_wta_wuhan_open",
]

SHARP_BM   = "pinnacle"
TARGET_BM  = "winamax_fr"
FALLBACK_BMS = ["williamhill", "betfair_ex_eu", "unibet_fr"]


# ---------------------------------------------------------------------------
# Obtención de cuotas
# ---------------------------------------------------------------------------

def _fetch_active_tennis_sports(odds_api_key: str) -> list[str]:
    """Devuelve solo los sports de tenis que tienen partidos ahora mismo."""
    r = requests.get(
        f"{ODDS_API_BASE}/sports",
        params={"apiKey": odds_api_key},
        timeout=10,
    )
    r.raise_for_status()
    active_keys = {s["key"] for s in r.json() if s.get("active")}
    return [s for s in TENNIS_SPORTS if s in active_keys]


def _fetch_tennis_odds(sport: str, odds_api_key: str, days_ahead: int) -> list[dict]:
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)
    try:
        r = requests.get(
            f"{ODDS_API_BASE}/sports/{sport}/odds",
            params={
                "apiKey":            odds_api_key,
                "regions":           "eu",
                "markets":           "h2h",
                "oddsFormat":        "decimal",
                "bookmakers":        f"{SHARP_BM},{TARGET_BM}," + ",".join(FALLBACK_BMS),
                "commenceTimeFrom":  now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "commenceTimeTo":    end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            timeout=12,
        )
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"  [Tennis] Error en {sport}: {e}")
        return []


# ---------------------------------------------------------------------------
# Modelo: Pinnacle sin margen → probabilidades reales
# ---------------------------------------------------------------------------

def _extract_h2h(match: dict, bm_key: str) -> dict | None:
    """Extrae cuotas h2h de un bookmaker para un partido de tenis."""
    for bm in match.get("bookmakers", []):
        if bm["key"] == bm_key:
            for mkt in bm.get("markets", []):
                if mkt["key"] == "h2h":
                    odds = {o["name"]: o["price"] for o in mkt["outcomes"]}
                    if len(odds) == 2:
                        return odds
    return None


def _remove_overround(odds_dict: dict) -> dict:
    """
    Elimina el margen del bookmaker y devuelve probabilidades reales (suman 1.0).
    Método: normalización simple (Shin adjustment aproximado).
    """
    implied = {k: 1 / v for k, v in odds_dict.items()}
    total   = sum(implied.values())
    return {k: round(v / total, 6) for k, v in implied.items()}


def _pinnacle_probs(match: dict) -> dict | None:
    """Extrae probabilidades reales de Pinnacle (sin margen)."""
    raw = _extract_h2h(match, SHARP_BM)
    if not raw:
        return None
    return _remove_overround(raw)


def _target_odds(match: dict) -> dict | None:
    """Cuotas del bookmaker objetivo (Winamax). Fallback a otros si no disponible."""
    raw = _extract_h2h(match, TARGET_BM)
    if raw:
        return raw
    for bm in FALLBACK_BMS:
        raw = _extract_h2h(match, bm)
        if raw:
            return raw
    return None


# ---------------------------------------------------------------------------
# Cálculo de edge y Kelly
# ---------------------------------------------------------------------------

def _analyze_tennis_match(match: dict, bankroll: float) -> list[dict]:
    """
    Analiza un partido de tenis:
      - Probabilidades reales: Pinnacle sin margen
      - Cuotas de apuesta: Winamax (o fallback)
      - Edge = P_pinnacle - P_implícita_winamax
    """
    sharp_probs = _pinnacle_probs(match)
    if not sharp_probs:
        return []

    target = _target_odds(match)
    if not target:
        return []

    results = []
    for player, odds in target.items():
        if odds <= 1.0 or player not in sharp_probs:
            continue

        p_model   = sharp_probs[player]           # prob Pinnacle sin margen
        p_implied = 1 / odds                       # prob implícita Winamax
        edge_pct  = round((p_model - p_implied) * 100, 2)

        b        = odds - 1.0
        q        = 1.0 - p_model
        kelly_f  = (b * p_model - q) / b if b > 0 else 0.0
        stake    = round(max(0.0, kelly_f * KELLY_FRACTION * bankroll), 2)
        ev_10    = round((p_model * b - q) * 10, 2)

        if edge_pct > VALUE_BET_THRESHOLD:
            verdict = "VALUE BET"
        elif edge_pct > MARGINAL_THRESHOLD:
            verdict = "MARGINAL"
        else:
            verdict = "SIN VALUE"

        results.append({
            "player":   player,
            "opponent": [k for k in sharp_probs if k != player][0],
            "p_model":  round(p_model * 100, 2),
            "p_implied": round(p_implied * 100, 2),
            "odds":     odds,
            "edge":     edge_pct,
            "ev_10":    ev_10,
            "kelly":    stake,
            "verdict":  verdict,
        })

    return results


# ---------------------------------------------------------------------------
# Escáner principal de tenis
# ---------------------------------------------------------------------------

def scan_tennis_value_bets(
    odds_api_key: str,
    days_ahead:   int   = 2,
    min_edge:     float = 3.0,
    bankroll:     float = BANKROLL,
) -> list[dict]:
    """
    Escanea todos los torneos de tenis activos y devuelve value bets ordenados por edge.
    """
    active_sports = _fetch_active_tennis_sports(odds_api_key)
    if not active_sports:
        print("  [Tennis] No hay torneos activos ahora mismo.")
        return []

    print(f"  [Tennis] Torneos activos: {', '.join(s.replace('tennis_','') for s in active_sports)}")

    value_bets = []

    for sport in active_sports:
        matches = _fetch_tennis_odds(sport, odds_api_key, days_ahead)

        # Nombre del torneo legible
        tour_name = (sport
                     .replace("tennis_atp_", "ATP ")
                     .replace("tennis_wta_", "WTA ")
                     .replace("_", " ")
                     .title())

        for match in matches:
            p1   = match["home_team"]
            p2   = match["away_team"]
            kick = match["commence_time"][:16].replace("T", " ")

            results = _analyze_tennis_match(match, bankroll)

            for r in results:
                if r["edge"] >= min_edge:
                    value_bets.append({
                        "sport":    "tennis",
                        "league":   tour_name,
                        "match":    f"{p1} vs {p2}",
                        "kickoff":  kick,
                        "market":   r["player"],
                        "is_dnb":   False,
                        "odds":     r["odds"],
                        "implied":  r["p_implied"],
                        "model":    r["p_model"],
                        "edge":     r["edge"],
                        "ev_10":    r["ev_10"],
                        "kelly":    r["kelly"],
                        "verdict":  r["verdict"],
                        "note":     "Pinnacle ref",
                    })

    value_bets.sort(key=lambda x: x["edge"], reverse=True)
    return value_bets

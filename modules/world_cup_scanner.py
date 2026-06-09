"""
Escáner de value bets para el Mundial 2026 (FIFA World Cup).

Las selecciones nacionales no tienen tabla de liga (football-data.org / ESPN
no las cubren), así que no podemos usar el modelo de Poisson basado en standings.

Mismo enfoque que en tenis: Pinnacle como referencia sharp.
Pinnacle ya incorpora la fuerza real de cada selección, forma, lesiones, etc.
Sus precios sin margen (no-vig) = probabilidad real del partido.

Modelo: Pinnacle 1X2 sin margen → probabilidad real
Target: Winamax FR (cuota donde apostamos)
Edge   = P(Pinnacle sin margen) − P_implícita(Winamax)

También derivamos DNB (empate apuesta no válida) matemáticamente a partir
de las propias cuotas 1X2 de Winamax, igual que en el escáner de clubes.
"""

import requests
from datetime import datetime, timezone, timedelta
from config import BANKROLL, KELLY_FRACTION, VALUE_BET_THRESHOLD, MARGINAL_THRESHOLD

ODDS_API_BASE = "https://api.the-odds-api.com/v4"

WORLD_CUP_SPORT = "soccer_fifa_world_cup"

SHARP_BM     = "pinnacle"
TARGET_BM    = "winamax_fr"
FALLBACK_BMS = ["williamhill", "betfair_ex_eu", "unibet_fr"]

MARKET_LABELS = {
    "home_win": "Local gana (1)",
    "draw":     "Empate (X)",
    "away_win": "Visitante gana (2)",
    "dnb_home": "Local DNB",
    "dnb_away": "Visitante DNB",
}


# ---------------------------------------------------------------------------
# Obtención de cuotas
# ---------------------------------------------------------------------------

def _fetch_world_cup_odds(odds_api_key: str, days_ahead: int) -> list[dict]:
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)
    try:
        r = requests.get(
            f"{ODDS_API_BASE}/sports/{WORLD_CUP_SPORT}/odds",
            params={
                "apiKey":           odds_api_key,
                "regions":          "eu",
                "markets":          "h2h",
                "oddsFormat":       "decimal",
                "bookmakers":       f"{SHARP_BM},{TARGET_BM}," + ",".join(FALLBACK_BMS),
                "commenceTimeFrom": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "commenceTimeTo":   end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            timeout=12,
        )
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"  [Mundial] Error: {e}")
        return []


# ---------------------------------------------------------------------------
# Modelo: Pinnacle 1X2 sin margen → probabilidades reales
# ---------------------------------------------------------------------------

def _extract_1x2(match: dict, bm_key: str) -> dict | None:
    """Extrae cuotas 1X2 (home/draw/away) de un bookmaker."""
    for bm in match.get("bookmakers", []):
        if bm["key"] == bm_key:
            for mkt in bm.get("markets", []):
                if mkt["key"] == "h2h":
                    odds = {}
                    for o in mkt["outcomes"]:
                        if o["name"] == match["home_team"]:
                            odds["home_win"] = o["price"]
                        elif o["name"] == match["away_team"]:
                            odds["away_win"] = o["price"]
                        elif o["name"] == "Draw":
                            odds["draw"] = o["price"]
                    if len(odds) == 3:
                        return odds
    return None


def _remove_overround(odds_dict: dict) -> dict:
    """Elimina el margen del bookmaker → probabilidades reales (suman 1.0)."""
    implied = {k: 1 / v for k, v in odds_dict.items()}
    total   = sum(implied.values())
    return {k: round(v / total, 6) for k, v in implied.items()}


def _target_odds(match: dict) -> dict | None:
    """Cuotas 1X2 del bookmaker objetivo (Winamax). Fallback a otros si no disponible."""
    raw = _extract_1x2(match, TARGET_BM)
    if raw:
        return raw
    for bm in FALLBACK_BMS:
        raw = _extract_1x2(match, bm)
        if raw:
            return raw
    return None


def _derive_dnb_odds(home_odds: float, draw_odds: float, away_odds: float,
                      dnb_margin: float = 0.04) -> tuple[float, float]:
    """Deriva cuotas DNB a partir de las cuotas 1X2 (mismo método que en clubes)."""
    impl_h = 1 / home_odds
    impl_d = 1 / draw_odds
    impl_a = 1 / away_odds
    total  = impl_h + impl_d + impl_a

    p_h = impl_h / total
    p_a = impl_a / total

    fair_dnb_home = (p_h + p_a) / p_h
    fair_dnb_away = (p_h + p_a) / p_a

    return (round(fair_dnb_home / (1 + dnb_margin), 2),
            round(fair_dnb_away / (1 + dnb_margin), 2))


# ---------------------------------------------------------------------------
# Cálculo de edge, EV y Kelly
# ---------------------------------------------------------------------------

def _verdict(edge_pct: float) -> str:
    if edge_pct > VALUE_BET_THRESHOLD:
        return "VALUE BET"
    elif edge_pct > MARGINAL_THRESHOLD:
        return "MARGINAL"
    return "SIN VALUE"


def _analyze_match(match: dict, bankroll: float) -> list[dict]:
    """
    Analiza un partido del Mundial:
      - Probabilidades reales: Pinnacle 1X2 sin margen
      - Cuotas de apuesta: Winamax (o fallback)
      - Mercados: 1X2 + DNB derivado
    """
    sharp_raw = _extract_1x2(match, SHARP_BM)
    if not sharp_raw:
        return []
    sharp_probs = _remove_overround(sharp_raw)   # {home_win, draw, away_win} sin margen

    target = _target_odds(match)
    if not target:
        return []

    results = []

    # ── Mercados 1X2 ────────────────────────────────────────────────────────
    for market, odds in target.items():
        if odds <= 1.0 or market not in sharp_probs:
            continue

        p_model   = sharp_probs[market]
        p_implied = 1 / odds
        edge_pct  = round((p_model - p_implied) * 100, 2)

        b       = odds - 1.0
        q       = 1.0 - p_model
        kelly_f = (b * p_model - q) / b if b > 0 else 0.0
        stake   = round(max(0.0, kelly_f * KELLY_FRACTION * bankroll), 2)
        ev_10   = round((p_model * b - q) * 10, 2)

        results.append({
            "market":   market,
            "label":    MARKET_LABELS[market],
            "is_dnb":   False,
            "odds":     odds,
            "implied":  round(p_implied * 100, 2),
            "model":    round(p_model * 100, 2),
            "edge":     edge_pct,
            "ev_10":    ev_10,
            "kelly":    stake,
            "verdict":  _verdict(edge_pct),
        })

    # ── DNB derivado (Local/Visitante apuesta no válida) ────────────────────
    if all(k in target for k in ("home_win", "draw", "away_win")):
        dnb_h_odds, dnb_a_odds = _derive_dnb_odds(
            target["home_win"], target["draw"], target["away_win"]
        )
        p_h, p_a = sharp_probs["home_win"], sharp_probs["away_win"]

        for market, odds, p_win, p_lose in (
            ("dnb_home", dnb_h_odds, p_h, p_a),
            ("dnb_away", dnb_a_odds, p_a, p_h),
        ):
            if odds <= 1.0:
                continue

            p_cond = p_win / (p_win + p_lose) if (p_win + p_lose) > 0 else 0.5
            ip     = 1 / odds
            edge_pct = round((p_cond - ip) * 100, 2)

            b       = odds - 1.0
            ev_10   = round((p_win * b - p_lose * 1.0) * 10, 2)
            kelly_f = (b * p_win - p_lose) / b if b > 0 else 0.0
            stake   = round(max(0.0, kelly_f * KELLY_FRACTION * bankroll), 2)

            results.append({
                "market":   market,
                "label":    MARKET_LABELS[market],
                "is_dnb":   True,
                "odds":     odds,
                "implied":  round(ip * 100, 2),
                "model":    round(p_cond * 100, 2),
                "edge":     edge_pct,
                "ev_10":    ev_10,
                "kelly":    stake,
                "verdict":  _verdict(edge_pct),
            })

    return results


# ---------------------------------------------------------------------------
# Escáner principal del Mundial
# ---------------------------------------------------------------------------

def get_world_cup_projections(
    odds_api_key: str,
    days_ahead:   int   = 7,
) -> list[dict]:
    """
    Devuelve todos los partidos del Mundial con análisis completo de probabilidades,
    cuotas, DNB y margen de seguridad. Usado para la sección de Pronósticos.
    Sin filtro de edge — muestra todos los partidos disponibles.
    """
    matches = _fetch_world_cup_odds(odds_api_key, days_ahead)
    projections = []

    for match in matches:
        home = match["home_team"]
        away = match["away_team"]
        kick = match["commence_time"][:16].replace("T", " ")

        sharp_raw = _extract_1x2(match, SHARP_BM)
        target    = _target_odds(match)
        if not sharp_raw or not target:
            continue

        probs = _remove_overround(sharp_raw)
        p_h, p_a, p_d = probs["home_win"], probs["away_win"], probs["draw"]

        dnb_h, dnb_a = _derive_dnb_odds(
            target["home_win"], target["draw"], target["away_win"]
        )

        p_h_dnb = p_h / (p_h + p_a) if (p_h + p_a) > 0 else 0.5
        p_a_dnb = p_a / (p_h + p_a) if (p_h + p_a) > 0 else 0.5

        # Favorito
        if p_h >= p_a:
            fav, fav_prob, fav_odds = home, p_h, target["home_win"]
            fav_dnb_odds, fav_dnb_prob = dnb_h, p_h_dnb
        else:
            fav, fav_prob, fav_odds = away, p_a, target["away_win"]
            fav_dnb_odds, fav_dnb_prob = dnb_a, p_a_dnb

        gap_win = round(fav_prob * 100 - 100 / fav_odds, 1)
        gap_dnb = round(fav_dnb_prob * 100 - 100 / fav_dnb_odds, 1)

        projections.append({
            "kickoff":      kick,
            "home":         home,
            "away":         away,
            "match":        f"{home} vs {away}",
            "home_prob":    round(p_h * 100, 1),
            "draw_prob":    round(p_d * 100, 1),
            "away_prob":    round(p_a * 100, 1),
            "home_odds":    target["home_win"],
            "draw_odds":    target["draw"],
            "away_odds":    target["away_win"],
            "fav":          fav,
            "fav_prob":     round(fav_prob * 100, 1),
            "fav_odds":     fav_odds,
            "fav_dnb_odds": fav_dnb_odds,
            "fav_dnb_prob": round(fav_dnb_prob * 100, 1),
            "gap_win":      gap_win,
            "gap_dnb":      gap_dnb,
        })

    # Ordenar por menor margen negativo (más "justos" primero)
    projections.sort(key=lambda x: x["gap_win"], reverse=True)
    return projections


def scan_world_cup_value_bets(
    odds_api_key: str,
    days_ahead:   int   = 7,
    min_edge:     float = 3.0,
    bankroll:     float = BANKROLL,
) -> list[dict]:
    """Escanea los partidos del Mundial 2026 y devuelve value bets ordenados por edge."""
    matches = _fetch_world_cup_odds(odds_api_key, days_ahead)
    if not matches:
        print("  [Mundial] No hay partidos del Mundial en este rango de fechas.")
        return []

    print(f"  [Mundial] {len(matches)} partidos encontrados.")

    value_bets = []
    for match in matches:
        home = match["home_team"]
        away = match["away_team"]
        kick = match["commence_time"][:16].replace("T", " ")

        for r in _analyze_match(match, bankroll):
            if r["edge"] >= min_edge:
                value_bets.append({
                    "sport":    "world_cup",
                    "league":   "Mundial 2026",
                    "match":    f"{home} vs {away}",
                    "kickoff":  kick,
                    "market":   r["label"],
                    "is_dnb":   r["is_dnb"],
                    "odds":     r["odds"],
                    "implied":  r["implied"],
                    "model":    r["model"],
                    "edge":     r["edge"],
                    "ev_10":    r["ev_10"],
                    "kelly":    r["kelly"],
                    "verdict":  r["verdict"],
                    "note":     "Pinnacle ref",
                })

    value_bets.sort(key=lambda x: x["edge"], reverse=True)
    return value_bets

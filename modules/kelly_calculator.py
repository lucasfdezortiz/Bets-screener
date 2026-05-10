"""
Módulo 3: Calculadora de edge y criterio de Kelly.

Para cada mercado calcula:
  - Probabilidad implícita de la cuota
  - Edge (%)
  - EV por €10
  - Apuesta recomendada (Medio Kelly sobre bankroll)
  - Veredicto: VALUE BET / MARGINAL / SIN VALUE
"""

from config import BANKROLL, KELLY_FRACTION, VALUE_BET_THRESHOLD, MARGINAL_THRESHOLD

MARKET_LABELS = {
    "home_win":  "Local gana (1)",
    "draw":      "Empate (X)",
    "away_win":  "Visitante gana (2)",
    "over_2_5":  "Over 2.5 goles",
    "under_2_5": "Under 2.5 goles",
    "btts_yes":  "BTTS - Sí",
    "btts_no":   "BTTS - No",
    "dnb_home":  "Local DNB",
    "dnb_away":  "Visitante DNB",
}

DNB_MARKETS = {"dnb_home", "dnb_away"}


def implied_probability(decimal_odds: float) -> float:
    """Probabilidad implícita de una cuota decimal."""
    if decimal_odds <= 1.0:
        return 1.0
    return 1.0 / decimal_odds


def edge(model_prob: float, impl_prob: float) -> float:
    """Edge en puntos porcentuales."""
    return (model_prob - impl_prob) * 100.0


def expected_value(model_prob: float, decimal_odds: float, stake: float = 10.0) -> float:
    """EV para una apuesta de `stake` euros."""
    net_win = (decimal_odds - 1.0) * stake
    return round(model_prob * net_win - (1.0 - model_prob) * stake, 2)


def kelly_stake(model_prob: float, decimal_odds: float, bankroll: float = BANKROLL) -> float:
    """
    Apuesta recomendada con Medio Kelly.
    Retorna 0 si el edge es negativo o la cuota no tiene valor.
    """
    b = decimal_odds - 1.0
    if b <= 0:
        return 0.0
    q = 1.0 - model_prob
    kelly_f = (b * model_prob - q) / b
    if kelly_f <= 0:
        return 0.0
    stake = kelly_f * KELLY_FRACTION * bankroll
    return round(stake, 2)


def verdict(edge_pct: float) -> str:
    if edge_pct > VALUE_BET_THRESHOLD:
        return "VALUE BET"
    elif edge_pct > MARGINAL_THRESHOLD:
        return "MARGINAL"
    else:
        return "SIN VALUE"


def analyze_bets(model_probs: dict, bookmaker_odds: dict, bankroll: float = BANKROLL) -> list[dict]:
    """
    Analiza cada mercado comparando probabilidades del modelo con las cuotas de la casa.
    Soporta mercados estándar (1X2, Over/Under) y DNB (apuesta no válida en empate).
    """
    results = []
    for market, odds in bookmaker_odds.items():
        if odds is None or odds <= 1.0:
            continue

        # Mercados DNB: probabilidad condicional excluyendo empate, EV con 3 resultados
        if market in DNB_MARKETS:
            win_market  = "home_win" if market == "dnb_home" else "away_win"
            lose_market = "away_win" if market == "dnb_home" else "home_win"
            if win_market not in model_probs or lose_market not in model_probs:
                continue

            p_win  = model_probs[win_market]
            p_lose = model_probs[lose_market]
            p_draw = model_probs.get("draw", 0.0)

            # Probabilidad condicional (excluye empate) vs probabilidad implícita
            p_cond = p_win / (p_win + p_lose) if (p_win + p_lose) > 0 else 0.5
            ip     = implied_probability(odds)
            e      = round((p_cond - ip) * 100, 2)

            # EV real (los 3 resultados cuentan): draw → 0
            b  = odds - 1.0
            ev = round((p_win * b - p_lose * 1.0) * 10, 2)

            # Kelly DNB: draw neutro → fracción = (b*p_win - p_lose) / b
            kelly_f = (b * p_win - p_lose) / b if b > 0 else 0.0
            ks      = round(max(0.0, kelly_f * KELLY_FRACTION * bankroll), 2)
            v       = verdict(e)

            results.append({
                "market":       market,
                "label":        MARKET_LABELS.get(market, market),
                "odds":         odds,
                "implied_prob": round(ip * 100, 2),
                "model_prob":   round(p_cond * 100, 2),
                "edge":         e,
                "ev_10":        ev,
                "kelly_stake":  ks,
                "verdict":      v,
                "is_dnb":       True,
            })
            continue

        # Mercados estándar
        if market not in model_probs:
            continue

        mp = model_probs[market]
        ip = implied_probability(odds)
        e  = round(edge(mp, ip), 2)
        ev = expected_value(mp, odds)
        ks = kelly_stake(mp, odds, bankroll)
        v  = verdict(e)

        results.append({
            "market":       market,
            "label":        MARKET_LABELS.get(market, market),
            "odds":         odds,
            "implied_prob": round(ip * 100, 2),
            "model_prob":   round(mp * 100, 2),
            "edge":         e,
            "ev_10":        ev,
            "kelly_stake":  ks,
            "verdict":      v,
            "is_dnb":       False,
        })

    return results

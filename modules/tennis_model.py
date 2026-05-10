"""
Modelo de tenis con Bradley-Terry.

P(player1 gana) = rating1 / (rating1 + rating2)

El rating se basa en puntos ATP/WTA con un ajuste por superficie.
Para la probabilidad de sets usamos la P(ganar un set) y la
distribución binomial de sets (best-of-3 o best-of-5).
"""

import math
from config import SURFACE_FACTORS


# Factores de ajuste por superficie (relativos, no exactos por jugador)
# Más refinado: se ajusta según si el jugador es especialista de tierra o pista dura.
# Como no tenemos datos de superficie por jugador, aplicamos un ruido pequeño.
SURFACE_ELO_ADJUST = {
    "clay": 1.05,   # ligeramente favorece a jugadores de tierra
    "hard": 1.00,   # neutro
    "grass": 0.97,  # ligeramente menos predecible
}


def _bradley_terry_prob(rating1: float, rating2: float) -> float:
    """Probabilidad de que el jugador 1 gane el partido (Bradley-Terry)."""
    if rating1 + rating2 <= 0:
        return 0.5
    return rating1 / (rating1 + rating2)


def _prob_win_sets(p_set: float, best_of: int) -> dict:
    """
    Calcula las probabilidades de ganar por 2-0 y 2-1 (best_of=3)
    o 3-0, 3-1, 3-2 (best_of=5).

    Args:
        p_set: P(jugador 1 gana un set)
        best_of: 3 o 5

    Returns:
        dict con P(win), P(lose) y distribución de sets.
    """
    q = 1.0 - p_set

    if best_of == 3:
        # Necesita ganar 2 sets
        # 2-0: pp
        # 2-1: p*q*p + q*p*p = 2*p²*q
        p_2_0 = p_set ** 2
        p_2_1 = 2 * p_set ** 2 * q
        p_win = p_2_0 + p_2_1

        p_0_2 = q ** 2
        p_1_2 = 2 * q ** 2 * p_set
        p_lose = p_0_2 + p_1_2

        return {
            "win_prob": round(p_win, 4),
            "lose_prob": round(p_lose, 4),
            "set_results": {
                "2-0": round(p_2_0, 4),
                "2-1": round(p_2_1, 4),
                "1-2": round(p_1_2, 4),
                "0-2": round(p_0_2, 4),
            },
            "under_sets": round(p_2_0 + p_0_2, 4),       # ≤2 sets (termina en 2)
            "over_sets": round(p_2_1 + p_1_2, 4),         # exactamente 3 sets
        }

    elif best_of == 5:
        # Necesita ganar 3 sets
        # 3-0: p³
        # 3-1: C(3,1)*p³*q  (el perdedor gana 1 de los primeros 3, el ganador gana el 4º)
        # 3-2: C(4,2)*p³*q² (el perdedor gana 2 de los primeros 4, el ganador gana el 5º)
        p_3_0 = p_set ** 3
        p_3_1 = 3 * p_set ** 3 * q
        p_3_2 = 6 * p_set ** 3 * q ** 2

        p_0_3 = q ** 3
        p_1_3 = 3 * q ** 3 * p_set
        p_2_3 = 6 * q ** 3 * p_set ** 2

        p_win = p_3_0 + p_3_1 + p_3_2
        p_lose = p_0_3 + p_1_3 + p_2_3

        return {
            "win_prob": round(p_win, 4),
            "lose_prob": round(p_lose, 4),
            "set_results": {
                "3-0": round(p_3_0, 4),
                "3-1": round(p_3_1, 4),
                "3-2": round(p_3_2, 4),
                "2-3": round(p_2_3, 4),
                "1-3": round(p_1_3, 4),
                "0-3": round(p_0_3, 4),
            },
            "under_sets": round(p_3_0 + p_0_3, 4),         # termina en 3 sets
            "over_sets": round(p_3_1 + p_3_2 + p_1_3 + p_2_3, 4),  # 4 o 5 sets
        }

    else:
        raise ValueError(f"best_of debe ser 3 o 5, recibido: {best_of}")


def calculate_tennis_probabilities(match_data: dict) -> dict:
    """
    Calcula las probabilidades de un partido de tenis.

    Args:
        match_data: dict de tennis_collector.get_tennis_match_data()

    Returns:
        dict con:
            - player1_win, player2_win (ML)
            - set_distribution (probabilidades por marcador de sets)
            - over_sets, under_sets (mercado de número de sets)
            - p_set: P(jugador1 gana un set)
    """
    p1 = match_data["player1"]
    p2 = match_data["player2"]
    surface = match_data.get("surface", "hard")
    best_of = match_data.get("best_of", 3)

    pts1 = max(p1.get("points", 1), 1)
    pts2 = max(p2.get("points", 1), 1)

    # Ajuste de superficie (pequeño factor empírico)
    surf_factor = SURFACE_ELO_ADJUST.get(surface, 1.0)
    # Ajuste: si la superficie es arcilla, históricamente favorece ligeramente al local
    # Aquí lo aplicamos al jugador 1 como heurística neutra
    rating1 = pts1 * surf_factor
    rating2 = pts2

    # P(jugador1 gana el partido) con Bradley-Terry
    p_match_win = _bradley_terry_prob(rating1, rating2)

    # Inferir P(jugador1 gana un set) desde P(ganar el partido)
    # Para best-of-3: P_match ≈ p²(3-2p) → resolver numéricamente
    p_set = _infer_p_set(p_match_win, best_of)

    set_probs = _prob_win_sets(p_set, best_of)

    return {
        "player1_win": round(p_match_win, 4),
        "player2_win": round(1.0 - p_match_win, 4),
        "p_set": round(p_set, 4),
        **set_probs,
    }


def _infer_p_set(p_match: float, best_of: int, iterations: int = 50) -> float:
    """
    Inferencia numérica de P(ganar un set) dado P(ganar el partido).
    Búsqueda binaria sobre [0, 1].
    """
    lo, hi = 0.0, 1.0
    for _ in range(iterations):
        mid = (lo + hi) / 2.0
        result = _prob_win_sets(mid, best_of)
        if result["win_prob"] < p_match:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0

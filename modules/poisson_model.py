"""
Módulo 2: Modelo de Poisson para calcular probabilidades de partido.

Usa el método de Dixon-Coles simplificado:
  λ_home = attack_home × defense_away × home_advantage × league_avg_goals
  λ_away = attack_away × defense_home × league_avg_goals
"""

import numpy as np
from scipy.stats import poisson
from config import HOME_ADVANTAGE, MAX_GOALS_SIMULATED


def _attack_strength(team_goals_avg: float, league_avg: float) -> float:
    """Fuerza de ataque relativa a la media de la liga."""
    if league_avg <= 0:
        return 1.0
    return team_goals_avg / league_avg


def _defense_strength(team_conceded_avg: float, league_avg: float) -> float:
    """Fuerza defensiva: valores > 1 indican defensa débil (concede más que la media)."""
    if league_avg <= 0:
        return 1.0
    return team_conceded_avg / league_avg


def _score_matrix(lambda_home: float, lambda_away: float, max_goals: int) -> np.ndarray:
    """
    Devuelve una matriz (max_goals × max_goals) donde M[i][j] = P(home=i, away=j).
    Los goles i, j van de 0 a max_goals-1.
    """
    home_probs = np.array([poisson.pmf(i, lambda_home) for i in range(max_goals)])
    away_probs = np.array([poisson.pmf(j, lambda_away) for j in range(max_goals)])
    return np.outer(home_probs, away_probs)


def calculate_probabilities(match_data: dict) -> dict:
    """
    Calcula las probabilidades de todos los mercados a partir de los datos del partido.

    Args:
        match_data: dict con campos:
            - home.goals_scored_avg, home.goals_conceded_avg
            - away.goals_scored_avg, away.goals_conceded_avg
            - league_avg_goals

    Returns:
        dict con probabilidades para 1X2, Over/Under 2.5, BTTS, y los λ usados.
    """
    home = match_data["home"]
    away = match_data["away"]
    league_avg = match_data.get("league_avg_goals", 1.35)

    att_home = _attack_strength(home["goals_scored_avg"], league_avg)
    def_home = _defense_strength(home["goals_conceded_avg"], league_avg)
    att_away = _attack_strength(away["goals_scored_avg"], league_avg)
    def_away = _defense_strength(away["goals_conceded_avg"], league_avg)

    lambda_home = att_home * def_away * HOME_ADVANTAGE * league_avg
    lambda_away = att_away * def_home * league_avg

    # Clamp para evitar valores extremos
    lambda_home = max(0.1, min(lambda_home, 8.0))
    lambda_away = max(0.1, min(lambda_away, 8.0))

    matrix = _score_matrix(lambda_home, lambda_away, MAX_GOALS_SIMULATED)

    # 1X2
    home_win = float(np.sum(np.tril(matrix, -1)))   # i > j → filas mayores que diagonal
    draw = float(np.sum(np.diag(matrix)))
    away_win = float(np.sum(np.triu(matrix, 1)))     # j > i

    # Normalizar por si hay error de redondeo
    total_1x2 = home_win + draw + away_win
    home_win /= total_1x2
    draw /= total_1x2
    away_win /= total_1x2

    # Over / Under 2.5
    rows, cols = np.indices(matrix.shape)
    over_mask = (rows + cols) > 2
    over_2_5 = float(np.sum(matrix[over_mask]))
    under_2_5 = 1.0 - over_2_5

    # BTTS
    btts_yes = float(1.0 - matrix[0, :].sum() - matrix[:, 0].sum() + matrix[0, 0])
    btts_no = 1.0 - btts_yes

    return {
        "home_win": round(home_win, 4),
        "draw": round(draw, 4),
        "away_win": round(away_win, 4),
        "over_2_5": round(over_2_5, 4),
        "under_2_5": round(under_2_5, 4),
        "btts_yes": round(btts_yes, 4),
        "btts_no": round(btts_no, 4),
        "lambda_home": round(lambda_home, 3),
        "lambda_away": round(lambda_away, 3),
    }

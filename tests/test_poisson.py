"""Tests del modelo de Poisson."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.poisson_model import calculate_probabilities, _score_matrix
import numpy as np


LIGA_AVG = 1.35

def make_match(home_scored, home_conceded, away_scored, away_conceded, league_avg=LIGA_AVG):
    return {
        "home": {"goals_scored_avg": home_scored, "goals_conceded_avg": home_conceded},
        "away": {"goals_scored_avg": away_scored, "goals_conceded_avg": away_conceded},
        "league_avg_goals": league_avg,
    }


def test_probabilities_sum_to_one():
    data = make_match(1.8, 0.9, 1.2, 1.4)
    probs = calculate_probabilities(data)
    total = probs["home_win"] + probs["draw"] + probs["away_win"]
    assert abs(total - 1.0) < 1e-6, f"1X2 suma {total}, esperado ~1.0"


def test_over_under_sum_to_one():
    data = make_match(1.8, 0.9, 1.2, 1.4)
    probs = calculate_probabilities(data)
    total = probs["over_2_5"] + probs["under_2_5"]
    assert abs(total - 1.0) < 1e-6, f"Over+Under suma {total}"


def test_btts_sum_to_one():
    data = make_match(1.8, 0.9, 1.2, 1.4)
    probs = calculate_probabilities(data)
    total = probs["btts_yes"] + probs["btts_no"]
    assert abs(total - 1.0) < 1e-6, f"BTTS suma {total}"


def test_strong_home_favored():
    # Equipo local muy superior
    data = make_match(3.0, 0.5, 0.5, 2.5)
    probs = calculate_probabilities(data)
    assert probs["home_win"] > probs["away_win"], "Local muy superior debe tener mayor P(victoria)"
    assert probs["home_win"] > 0.6, f"P(local gana) = {probs['home_win']}, esperado > 0.6"


def test_equal_teams_draw_relevant():
    # Equipos idénticos: empate debe ser la segunda probabilidad más alta
    data = make_match(1.35, 1.35, 1.35, 1.35)
    probs = calculate_probabilities(data)
    # Con home advantage, local gana más, pero empate > visita_gana debería darse
    assert probs["home_win"] >= probs["away_win"], "Con ventaja local, local >= visitante"
    assert probs["draw"] > 0.20, f"Empate con equipos iguales: {probs['draw']}"


def test_high_scoring_over():
    # Equipos que marcan mucho → Over 2.5 probable
    data = make_match(2.5, 2.0, 2.0, 2.5)
    probs = calculate_probabilities(data)
    assert probs["over_2_5"] > 0.7, f"Partido de muchos goles: Over={probs['over_2_5']}"


def test_score_matrix_sums_correctly():
    matrix = _score_matrix(1.5, 1.0, 9)
    assert abs(matrix.sum() - 1.0) < 1e-4, f"Matriz suma {matrix.sum()}, esperado ~1.0"


def test_lambda_clamping():
    # Valores extremos no deben romper el modelo
    data = make_match(10.0, 0.01, 0.01, 10.0, league_avg=1.0)
    probs = calculate_probabilities(data)
    total = probs["home_win"] + probs["draw"] + probs["away_win"]
    assert abs(total - 1.0) < 1e-6


if __name__ == "__main__":
    tests = [
        test_probabilities_sum_to_one,
        test_over_under_sum_to_one,
        test_btts_sum_to_one,
        test_strong_home_favored,
        test_equal_teams_draw_relevant,
        test_high_scoring_over,
        test_score_matrix_sums_correctly,
        test_lambda_clamping,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests pasados")

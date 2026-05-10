"""Tests del módulo Kelly / calculadora de edge."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.kelly_calculator import (
    implied_probability, edge, expected_value, kelly_stake, verdict, analyze_bets
)


def test_implied_probability_basic():
    assert abs(implied_probability(2.0) - 0.5) < 1e-6
    assert abs(implied_probability(4.0) - 0.25) < 1e-6
    assert abs(implied_probability(1.5) - 0.6667) < 1e-3


def test_implied_probability_edge_cases():
    assert implied_probability(1.0) == 1.0
    assert implied_probability(0.5) == 1.0  # cuota inválida


def test_edge_positive():
    # Modelo dice 55%, cuota implica 50% → edge +5%
    e = edge(0.55, 0.50)
    assert abs(e - 5.0) < 1e-6


def test_edge_negative():
    # Modelo dice 40%, cuota implica 50% → edge -10%
    e = edge(0.40, 0.50)
    assert abs(e - (-10.0)) < 1e-6


def test_expected_value_positive():
    # 55% de probabilidad, cuota 2.0 → EV = 0.55*10 - 0.45*10 = 1.0
    ev = expected_value(0.55, 2.0, stake=10.0)
    assert abs(ev - 1.0) < 0.01


def test_expected_value_negative():
    # 40% de probabilidad, cuota 2.0 → EV = 0.40*10 - 0.60*10 = -2.0
    ev = expected_value(0.40, 2.0, stake=10.0)
    assert abs(ev - (-2.0)) < 0.01


def test_kelly_positive_edge():
    # Kelly = (b*p - q) / b; b=1, p=0.60, q=0.40 → kelly=0.20; medio kelly = 0.10
    stake = kelly_stake(0.60, 2.0, bankroll=200.0)
    expected = 0.10 * 200.0 * 0.5  # medio kelly
    # Medio Kelly: fraction = 0.20 * 0.5 = 0.10 → 0.10 * 200 = 20
    assert stake > 0, "Debe recomendar apuesta con edge positivo"
    assert abs(stake - 20.0) < 0.1


def test_kelly_negative_edge():
    # Sin edge → debe recomendar €0
    stake = kelly_stake(0.40, 2.0, bankroll=200.0)
    assert stake == 0.0, f"Sin edge no debe apostar, got {stake}"


def test_verdict_labels():
    assert verdict(10.0) == "VALUE BET"
    assert verdict(5.1) == "VALUE BET"
    assert verdict(3.0) == "MARGINAL"
    assert verdict(0.1) == "MARGINAL"
    assert verdict(0.0) == "SIN VALUE"
    assert verdict(-5.0) == "SIN VALUE"


def test_analyze_bets_full():
    model_probs = {
        "home_win": 0.55,
        "draw": 0.25,
        "away_win": 0.20,
        "over_2_5": 0.60,
        "under_2_5": 0.40,
    }
    odds = {
        "home_win": 2.10,   # implica 0.476 → edge ~7.4% → VALUE BET
        "draw": 3.50,       # implica 0.286 → edge ~-3.6% → SIN VALUE
        "over_2_5": 1.80,   # implica 0.556 → edge ~4.4% → MARGINAL
    }
    results = analyze_bets(model_probs, odds)
    assert len(results) == 3

    home_result = next(r for r in results if r["market"] == "home_win")
    assert home_result["verdict"] == "VALUE BET"
    assert home_result["edge"] > 5.0
    assert home_result["kelly_stake"] > 0

    draw_result = next(r for r in results if r["market"] == "draw")
    assert draw_result["verdict"] == "SIN VALUE"
    assert draw_result["kelly_stake"] == 0.0


def test_analyze_bets_skips_invalid_odds():
    model_probs = {"home_win": 0.55}
    # Cuota <= 1.0 debe ignorarse
    results = analyze_bets(model_probs, {"home_win": 0.9})
    assert len(results) == 0


if __name__ == "__main__":
    tests = [
        test_implied_probability_basic,
        test_implied_probability_edge_cases,
        test_edge_positive,
        test_edge_negative,
        test_expected_value_positive,
        test_expected_value_negative,
        test_kelly_positive_edge,
        test_kelly_negative_edge,
        test_verdict_labels,
        test_analyze_bets_full,
        test_analyze_bets_skips_invalid_odds,
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

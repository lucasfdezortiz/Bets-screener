#!/usr/bin/env python3
"""
Value Bets Analyzer — CLI principal.

Uso:
    python3 main.py

Flujo:
    1. Elegir deporte (fútbol / tenis)
    2. Introducir datos del partido
    3. Se calculan probabilidades con Poisson (fútbol) o Bradley-Terry (tenis)
    4. Introducir cuotas de la casa
    5. Se muestra la tabla de análisis con veredictos y apuestas Kelly
"""

import os
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.prompt import Prompt

console = Console()

# ---------------------------------------------------------------------------
# Helpers de input
# ---------------------------------------------------------------------------

def ask(prompt: str, default: str = "") -> str:
    value = Prompt.ask(f"[bold cyan]{prompt}[/bold cyan]", default=default)
    return value.strip()


def ask_float(prompt: str, default: float | None = None) -> float | None:
    default_str = str(default) if default is not None else ""
    raw = ask(prompt, default_str)
    if not raw:
        return None
    try:
        return float(raw.replace(",", "."))
    except ValueError:
        console.print(f"[red]Valor inválido '{raw}', ignorando.[/red]")
        return None


def ask_int(prompt: str, default: int | None = None) -> int | None:
    default_str = str(default) if default is not None else ""
    raw = ask(prompt, default_str)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _verdict_style(verdict: str) -> str:
    if verdict == "VALUE BET":
        return "bold green"
    elif verdict == "MARGINAL":
        return "bold yellow"
    else:
        return "bold red"


def print_match_data(data: dict, sport: str = "football"):
    """Muestra los datos recopilados del partido en pantalla."""
    if sport == "football":
        home = data["home"]
        away = data["away"]

        console.print(Panel(
            f"[bold]{home['name']}[/bold] vs [bold]{away['name']}[/bold]\n"
            f"Fuente: [dim]{data.get('source', '?')}[/dim]",
            title="Datos del Partido",
            border_style="blue"
        ))

        t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
        t.add_column("Stat", style="dim")
        t.add_column(home["name"], justify="right")
        t.add_column(away["name"], justify="right")

        t.add_row("Posición en tabla",
                  str(home.get("position", "?")),
                  str(away.get("position", "?")))
        t.add_row("Goles marcados/partido",
                  f"{home['goals_scored_avg']:.2f}",
                  f"{away['goals_scored_avg']:.2f}")
        t.add_row("Goles encajados/partido",
                  f"{home['goals_conceded_avg']:.2f}",
                  f"{away['goals_conceded_avg']:.2f}")
        t.add_row("Media goles liga",
                  f"{data['league_avg_goals']:.2f}", "—")

        console.print(t)

        # Forma reciente
        for team_key, label in [("home", "Local"), ("away", "Visitante")]:
            form = data[team_key].get("form", [])
            if form:
                form_str = " ".join(
                    f"[green]{m['result']}[/green]" if m["result"] == "W"
                    else f"[yellow]{m['result']}[/yellow]" if m["result"] == "D"
                    else f"[red]{m['result']}[/red]"
                    for m in form
                )
                console.print(f"  Forma {label}: {form_str}")

        # H2H
        h2h = data.get("h2h", [])
        if h2h:
            console.print(f"\n  [bold]H2H (últimos {len(h2h)} partidos):[/bold]")
            for m in h2h[-5:]:
                console.print(
                    f"    {m['date']}  {m['home']} {m['home_goals']} - "
                    f"{m['away_goals']} {m['away']}"
                )

    else:
        p1 = data["player1"]
        p2 = data["player2"]
        console.print(Panel(
            f"[bold]{p1['name']}[/bold] ({p1['points']:,} pts) vs "
            f"[bold]{p2['name']}[/bold] ({p2['points']:,} pts)\n"
            f"Superficie: {data['surface']} | Best of {data['best_of']}",
            title="Datos del Partido de Tenis",
            border_style="blue"
        ))


def print_probabilities(probs: dict, sport: str = "football"):
    """Muestra las probabilidades del modelo."""
    console.print("\n[bold magenta]── Probabilidades del Modelo ──[/bold magenta]")

    if sport == "football":
        console.print(
            f"  λ local = [bold]{probs['lambda_home']}[/bold]  |  "
            f"λ visitante = [bold]{probs['lambda_away']}[/bold]"
        )
        t = Table(box=box.SIMPLE, show_header=True, header_style="bold")
        t.add_column("Mercado")
        t.add_column("Probabilidad", justify="right")

        markets = [
            ("Local gana (1)", probs["home_win"]),
            ("Empate (X)", probs["draw"]),
            ("Visitante gana (2)", probs["away_win"]),
            ("Over 2.5", probs["over_2_5"]),
            ("Under 2.5", probs["under_2_5"]),
            ("BTTS Sí", probs["btts_yes"]),
            ("BTTS No", probs["btts_no"]),
        ]
        for label, p in markets:
            t.add_row(label, f"{p*100:.1f}%")
        console.print(t)

    else:
        console.print(
            f"  P(set) jugador 1 = [bold]{probs['p_set']*100:.1f}%[/bold]"
        )
        t = Table(box=box.SIMPLE, show_header=True, header_style="bold")
        t.add_column("Mercado")
        t.add_column("Probabilidad", justify="right")

        t.add_row("Jugador 1 gana", f"{probs['player1_win']*100:.1f}%")
        t.add_row("Jugador 2 gana", f"{probs['player2_win']*100:.1f}%")

        if "set_results" in probs:
            for score, p in probs["set_results"].items():
                t.add_row(f"Sets {score}", f"{p*100:.1f}%")
            t.add_row("≤ mínimos sets", f"{probs['under_sets']*100:.1f}%")
            t.add_row("> mínimos sets", f"{probs['over_sets']*100:.1f}%")
        console.print(t)


def print_results(results: list[dict]):
    """Tabla final con veredictos y Kelly."""
    if not results:
        console.print("\n[yellow]No se introdujeron cuotas para analizar.[/yellow]")
        return

    console.print("\n")
    t = Table(
        title="Análisis de Value Bets",
        box=box.DOUBLE_EDGE,
        show_header=True,
        header_style="bold white on dark_blue",
        title_style="bold white",
    )
    t.add_column("Mercado", min_width=18)
    t.add_column("Cuota", justify="right", min_width=6)
    t.add_column("P. Implícita", justify="right", min_width=12)
    t.add_column("P. Modelo", justify="right", min_width=10)
    t.add_column("Edge", justify="right", min_width=8)
    t.add_column("EV/€10", justify="right", min_width=8)
    t.add_column("Kelly (€)", justify="right", min_width=10)
    t.add_column("Veredicto", min_width=12)

    for r in results:
        style = _verdict_style(r["verdict"])
        edge_str = f"{r['edge']:+.1f}%"
        ev_str = f"{r['ev_10']:+.2f}€"
        kelly_str = f"{r['kelly_stake']:.2f}€" if r["kelly_stake"] > 0 else "—"

        t.add_row(
            r["label"],
            str(r["odds"]),
            f"{r['implied_prob']:.1f}%",
            f"{r['model_prob']:.1f}%",
            Text(edge_str, style=style),
            Text(ev_str, style="green" if r["ev_10"] > 0 else "red"),
            Text(kelly_str, style="green" if r["kelly_stake"] > 0 else "dim"),
            Text(r["verdict"], style=style),
        )

    console.print(t)

    # Resumen
    value_bets = [r for r in results if r["verdict"] == "VALUE BET"]
    if value_bets:
        total_kelly = sum(r["kelly_stake"] for r in value_bets)
        console.print(
            f"\n  [bold green]VALUE BETS encontradas: {len(value_bets)}[/bold green]  |  "
            f"Total recomendado: [bold green]{total_kelly:.2f}€[/bold green]"
        )
    else:
        console.print("\n  [bold red]Sin value bets en este partido.[/bold red]")


# ---------------------------------------------------------------------------
# Flujos por deporte
# ---------------------------------------------------------------------------

def run_football():
    from modules.data_collector import get_match_data
    from modules.poisson_model import calculate_probabilities
    from modules.kelly_calculator import analyze_bets

    console.print("\n[bold]── Partido de Fútbol ──[/bold]")
    home = ask("Equipo local")
    away = ask("Equipo visitante")
    competition = ask("Competición (ej: laliga, premier, bundesliga, seriea, champions)")
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()

    if not api_key:
        api_key_input = ask("API key de football-data.org (Enter para omitir)")
        if api_key_input:
            api_key = api_key_input

    console.print("\n[dim]Recopilando datos...[/dim]")
    data = get_match_data(home, away, competition, api_key or None)

    if data is None:
        console.print("[bold red]No se pudieron obtener datos del partido.[/bold red]")
        console.print("Puedes introducir las estadísticas manualmente:")
        data = _manual_football_data(home, away)

    print_match_data(data, sport="football")

    probs = calculate_probabilities(data)
    print_probabilities(probs, sport="football")

    # Pedir cuotas
    console.print("\n[bold cyan]Introduce las cuotas de la casa de apuestas[/bold cyan]")
    console.print("[dim](Enter para saltar un mercado)[/dim]\n")

    markets = [
        ("home_win", "Local gana (1)"),
        ("draw", "Empate (X)"),
        ("away_win", "Visitante gana (2)"),
        ("over_2_5", "Over 2.5 goles"),
        ("under_2_5", "Under 2.5 goles"),
        ("btts_yes", "BTTS Sí"),
        ("btts_no", "BTTS No"),
    ]

    odds = {}
    for key, label in markets:
        val = ask_float(f"  Cuota {label}")
        if val and val > 1.0:
            odds[key] = val

    from config import BANKROLL
    results = analyze_bets(probs, odds, BANKROLL)
    print_results(results)


def run_tennis():
    from modules.tennis_collector import get_tennis_match_data
    from modules.tennis_model import calculate_tennis_probabilities
    from modules.kelly_calculator import analyze_bets, MARKET_LABELS

    console.print("\n[bold]── Partido de Tenis ──[/bold]")
    p1_name = ask("Jugador 1 (el que buscas apostar)")
    p2_name = ask("Jugador 2 (rival)")
    tour = ask("Tour (atp/wta)", default="atp")
    surface = ask("Superficie (hard/clay/grass)", default="hard")
    best_of_str = ask("Best of (3/5)", default="3")
    best_of = int(best_of_str) if best_of_str in ("3", "5") else 3

    console.print("\n[dim]Intentando obtener puntos de ranking automáticamente...[/dim]")
    data = get_tennis_match_data(p1_name, p2_name, tour, surface, best_of)

    # Si no se obtuvieron puntos, pedir manualmente
    if data["player1"]["points"] == 0:
        pts = ask_int(f"Puntos ATP/WTA de {p1_name} (manual)")
        data["player1"]["points"] = pts or 1000
    if data["player2"]["points"] == 0:
        pts = ask_int(f"Puntos ATP/WTA de {p2_name} (manual)")
        data["player2"]["points"] = pts or 1000

    print_match_data(data, sport="tennis")

    probs = calculate_tennis_probabilities(data)
    print_probabilities(probs, sport="tennis")

    # Cuotas
    console.print("\n[bold cyan]Introduce las cuotas de la casa[/bold cyan]")
    console.print("[dim](Enter para saltar)[/dim]\n")

    tennis_markets = [
        ("player1_win", f"{p1_name} gana"),
        ("player2_win", f"{p2_name} gana"),
        ("under_sets", f"Menos de {best_of} sets (termina rápido)"),
        ("over_sets", f"Más sets (llega al límite)"),
    ]

    # Actualizar labels dinámicos
    for key, label in tennis_markets:
        MARKET_LABELS[key] = label

    odds = {}
    for key, label in tennis_markets:
        val = ask_float(f"  Cuota {label}")
        if val and val > 1.0:
            odds[key] = val

    from config import BANKROLL
    results = analyze_bets(probs, odds, BANKROLL)
    print_results(results)


def _manual_football_data(home_name: str, away_name: str) -> dict:
    """Permite introducir datos del partido manualmente si la API falla."""
    console.print("\n[dim]Introduce las estadísticas de la temporada:[/dim]")

    def get_team_stats(team_name: str) -> dict:
        console.print(f"\n  [bold]{team_name}[/bold]")
        scored = ask_float(f"  Goles marcados por partido", default=1.35) or 1.35
        conceded = ask_float(f"  Goles encajados por partido", default=1.35) or 1.35
        pos = ask_int(f"  Posición en la tabla", default=10) or 10
        return {
            "name": team_name,
            "position": pos,
            "goals_scored_avg": scored,
            "goals_conceded_avg": conceded,
            "played": 20,
            "form": [],
        }

    home_stats = get_team_stats(home_name)
    away_stats = get_team_stats(away_name)
    league_avg = ask_float("Media de goles por partido en la liga", default=1.35) or 1.35

    return {
        "home": home_stats,
        "away": away_stats,
        "h2h": [],
        "league_avg_goals": league_avg,
        "source": "manual",
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    console.print(Panel(
        "[bold white]VALUE BETS ANALYZER[/bold white]\n"
        "[dim]Modelo de Poisson (fútbol) + Bradley-Terry (tenis)[/dim]\n"
        "[dim]Criterio de Medio Kelly | Bankroll: €200[/dim]",
        border_style="bright_blue",
        expand=False,
    ))

    sport = ask("\nDeporte (futbol/tenis)", default="futbol").lower()

    if sport in ("futbol", "fútbol", "football", "f"):
        run_football()
    elif sport in ("tenis", "tennis", "t"):
        run_tennis()
    else:
        console.print(f"[red]Deporte '{sport}' no reconocido. Usa 'futbol' o 'tenis'.[/red]")
        sys.exit(1)

    console.print("\n[dim]Análisis completado.[/dim]\n")


if __name__ == "__main__":
    main()

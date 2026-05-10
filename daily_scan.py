#!/usr/bin/env python3
"""
Escaneo diario de value bets — Fútbol + Tenis.
Uso: python3 daily_scan.py
"""

import sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, "/Users/lucasfdezortiz/value-bets")
from modules.scanner        import scan_value_bets
from modules.tennis_scanner import scan_tennis_value_bets

ODDS_API_KEY = "2e0cc7717f96a25817a3c781429437b8"
BANKROLL     = 200.0
MIN_EDGE     = 3.0
DAYS_AHEAD   = 2
BOOKMAKER    = "winamax_fr"

FOOTBALL_LEAGUES = [
    "soccer_spain_la_liga",
    "soccer_spain_segunda_division",
    "soccer_epl",
    "soccer_germany_bundesliga",
    "soccer_italy_serie_a",
    "soccer_france_ligue_one",
    "soccer_uefa_champs_league",
]

console = Console(width=120)


def print_section(items: list[dict], title: str, color: str):
    if not items:
        return
    console.print(f"\n[bold {color}]{'━'*110}[/bold {color}]")
    console.print(f"[bold {color}]  {title}[/bold {color}]")
    console.print(f"[bold {color}]{'━'*110}[/bold {color}]")

    header = (
        f"  {'#':<3} {'Deporte/Liga':<18} {'Partido':<30} "
        f"{'Fecha/Hora':<12} {'Apuesta':<24} {'Cuota':>6}  "
        f"{'Impl%':>6}  {'Mod%':>6}  {'Edge':>7}  {'EV/10€':>7}  {'Kelly':>7}"
    )
    console.print(f"[dim]{header}[/dim]")
    console.print(f"[dim]  {'─'*108}[/dim]")

    for i, b in enumerate(items, 1):
        dt         = b["kickoff"]
        fecha_hora = f"{dt[5:10]} {dt[11:16]}" if len(dt) > 10 else dt
        edge_str   = f"+{b['edge']:.1f}%"
        ev_str     = f"+{b['ev_10']:.2f}€"
        kelly_str  = f"{b['kelly']:.2f}€" if b["kelly"] > 0 else "—"
        partido    = b["match"][:29]
        liga       = b["league"][:17]

        # Tag de mercado
        sport = b.get("sport", "football")
        if sport == "tennis":
            tag = "[🎾]"
        elif b.get("is_dnb"):
            tag = "[DNB]"
        else:
            tag = "     "
        mercado = f"{tag} {b['market']}"[:23]

        line = (
            f"  {i:<3} {liga:<18} {partido:<30} {fecha_hora:<12} "
            f"{mercado:<24} {b['odds']:>6}  {b['implied']:>5.1f}%  "
            f"{b['model']:>5.1f}%  {edge_str:>7}  {ev_str:>7}  {kelly_str:>7}"
        )
        console.print(f"[{color}]{line}[/{color}]")


def run():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    console.print(Panel(
        f"[bold white]ESCANEO DIARIO DE VALUE BETS  —  Fútbol + Tenis[/bold white]\n"
        f"[dim]{now}  |  Modelo: Poisson (fútbol) · Pinnacle sharp (tenis)  |  "
        f"Target: Winamax FR  |  Bankroll: €{BANKROLL}[/dim]",
        border_style="bright_blue", expand=False,
    ))

    # ── Fútbol ──────────────────────────────────────────────────────────────
    console.print("\n[bold cyan]⚽  Escaneando fútbol...[/bold cyan]")
    football_bets = scan_value_bets(
        odds_api_key=ODDS_API_KEY,
        leagues=FOOTBALL_LEAGUES,
        days_ahead=DAYS_AHEAD,
        min_edge=MIN_EDGE,
        bookmaker=BOOKMAKER,
        bankroll=BANKROLL,
    )
    for b in football_bets:
        b.setdefault("sport", "football")

    # ── Tenis ───────────────────────────────────────────────────────────────
    console.print("\n[bold cyan]🎾  Escaneando tenis...[/bold cyan]")
    tennis_bets = scan_tennis_value_bets(
        odds_api_key=ODDS_API_KEY,
        days_ahead=DAYS_AHEAD,
        min_edge=MIN_EDGE,
        bankroll=BANKROLL,
    )

    # ── Combinar y ordenar por edge ──────────────────────────────────────────
    all_bets = sorted(football_bets + tennis_bets, key=lambda x: x["edge"], reverse=True)

    if not all_bets:
        console.print(f"\n[yellow]Sin value bets hoy con edge ≥ {MIN_EDGE}%.[/yellow]")
        return

    value = [b for b in all_bets if b["verdict"] == "VALUE BET"]
    marg  = [b for b in all_bets if b["verdict"] == "MARGINAL"]

    print_section(value, f"✓  VALUE BETS — edge > 5%  ({len(value)} encontradas)", "green")
    print_section(marg,  f"~  MARGINALES — edge 3-5%  ({len(marg)} encontradas)", "yellow")

    # ── Resumen ──────────────────────────────────────────────────────────────
    futbol_v  = [b for b in value if b.get("sport") != "tennis"]
    tenis_v   = [b for b in value if b.get("sport") == "tennis"]
    total_kelly = sum(b["kelly"] for b in value)

    console.print(f"\n[bold]{'━'*110}[/bold]")
    console.print(
        f"  [bold green]VALUE BETS: {len(value)}[/bold green]  "
        f"[dim](⚽ {len(futbol_v)} fútbol  |  🎾 {len(tenis_v)} tenis  |  "
        f"Marginales: {len(marg)})[/dim]\n"
        f"  Apuesta Kelly total recomendada: [bold green]€{total_kelly:.2f}[/bold green] "
        f"sobre bankroll de €{BANKROLL}"
    )
    console.print()


if __name__ == "__main__":
    run()

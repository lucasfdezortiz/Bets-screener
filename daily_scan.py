#!/usr/bin/env python3
"""
Value Bets Scanner — Estrategia de Alta Convicción.

Filosofía:
  - Solo apostamos cuando el modelo dice ≥ 62% de probabilidad de ganar
  - Y hay edge real (≥ 5%) frente a Winamax
  - Con cuota ≤ 1.75 → baja varianza, hit rate alto, apuesta fuerte

Hit rate esperado = probabilidad del modelo (si el modelo está calibrado).
A cuota 1.60 necesitas acertar 62.5% para no perder.
Si el modelo dice 72% → margen real de 9.5 puntos porcentuales.
"""

import sys
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, "/Users/lucasfdezortiz/value-bets")
from modules.scanner            import scan_value_bets
from modules.tennis_scanner     import scan_tennis_value_bets
from modules.world_cup_scanner  import scan_world_cup_value_bets

ODDS_API_KEY  = "2e0cc7717f96a25817a3c781429437b8"
BANKROLL      = 200.0
DAYS_AHEAD    = 3        # 3 días para capturar más partidos de tenis
BOOKMAKER     = "winamax_fr"

# ── Filtros de convicción ───────────────────────────────────────────────────
MAX_ODDS_CONVICTION = 1.75   # Cuota máxima para apostar fuerte
MIN_MODEL_PROB      = 62.0   # % mínimo de probabilidad del modelo
MIN_EDGE_CONVICTION = 5.0    # Edge mínimo para convicción
MIN_EDGE_WATCH      = 3.0    # Edge mínimo para sección "en vigilancia"

FOOTBALL_LEAGUES = [
    "soccer_spain_la_liga",
    "soccer_spain_segunda_division",
    "soccer_epl",
    "soccer_germany_bundesliga",
    "soccer_italy_serie_a",
    "soccer_france_ligue_one",
    "soccer_uefa_champs_league",
]

console = Console(width=125)


def conviction_score(b: dict) -> float:
    """edge × probabilidad_modelo / 100 — premia alta prob Y alto edge."""
    return b["edge"] * b["model"] / 100


def breakeven_rate(odds: float) -> float:
    """% mínimo de acierto para no perder dinero a esa cuota."""
    return round(100 / odds, 1)


def print_section(items: list[dict], title: str, color: str, show_hitrate: bool = True):
    if not items:
        return
    console.print(f"\n[bold {color}]{'━'*115}[/bold {color}]")
    console.print(f"[bold {color}]  {title}[/bold {color}]")
    console.print(f"[bold {color}]{'━'*115}[/bold {color}]")

    hr_col = f"{'HitRate':>8}  {'Break-ev':>8}  " if show_hitrate else ""
    header = (
        f"  {'#':<3} {'Liga/Torneo':<16} {'Partido':<27} "
        f"{'Hora':<11} {'Apuesta':<21} {'Cuota':>6}  "
        f"{'Edge':>7}  {hr_col}"
        f"{'Score':>6}  {'EV/10€':>7}  {'Kelly':>8}"
    )
    console.print(f"[dim]{header}[/dim]")
    console.print(f"[dim]  {'─'*112}[/dim]")

    for i, b in enumerate(items, 1):
        dt        = b["kickoff"]
        hora      = f"{dt[5:10]} {dt[11:16]}" if len(dt) > 10 else dt
        edge_str  = f"+{b['edge']:.1f}%"
        ev_str    = f"+{b['ev_10']:.2f}€"
        kelly_str = f"{b['kelly']:.2f}€" if b["kelly"] > 0 else "—"
        partido   = b["match"][:26]
        liga      = b["league"][:15]
        score     = conviction_score(b)

        sport = b.get("sport", "football")
        if sport == "tennis":
            tag = "[🎾]"
        elif sport == "world_cup":
            tag = "[🏆 DNB]" if b.get("is_dnb") else "[🏆]"
        elif b.get("is_dnb"):
            tag = "[DNB]"
        else:
            tag = "     "
        mercado = f"{tag} {b['market']}"[:20]

        if show_hitrate:
            hit_str   = f"{b['model']:>6.1f}%  "
            break_str = f"{breakeven_rate(b['odds']):>6.1f}%  "
            hr_part   = f"{hit_str}{break_str}"
        else:
            hr_part = ""

        line = (
            f"  {i:<3} {liga:<16} {partido:<27} {hora:<11} "
            f"{mercado:<21} {b['odds']:>6}  {edge_str:>7}  "
            f"{hr_part}{score:>5.1f}  {ev_str:>7}  {kelly_str:>9}"
        )
        console.print(f"[{color}]{line}[/{color}]")


def run():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    console.print(Panel(
        f"[bold white]VALUE BETS — ESTRATEGIA ALTA CONVICCIÓN[/bold white]\n"
        f"[dim]{now}  |  ⚽ Fútbol · 🎾 Tenis · 🏆 Mundial 2026  |  "
        f"Filtro: cuota ≤ {MAX_ODDS_CONVICTION} · prob modelo ≥ {MIN_MODEL_PROB}% · edge ≥ {MIN_EDGE_CONVICTION}%  |  "
        f"Winamax FR · Bankroll: €{BANKROLL}[/dim]",
        border_style="bright_blue", expand=False,
    ))

    # ── Fútbol ──────────────────────────────────────────────────────────────
    console.print("\n[bold cyan]⚽  Escaneando fútbol...[/bold cyan]")
    football_bets = scan_value_bets(
        odds_api_key=ODDS_API_KEY,
        leagues=FOOTBALL_LEAGUES,
        days_ahead=DAYS_AHEAD,
        min_edge=MIN_EDGE_WATCH,
        bookmaker=BOOKMAKER,
        bankroll=BANKROLL,
    )
    for b in football_bets:
        b.setdefault("sport", "football")

    # ── Tenis (todos los partidos, 3 días) ──────────────────────────────────
    console.print("\n[bold cyan]🎾  Escaneando tenis (todos los partidos)...[/bold cyan]")
    tennis_bets = scan_tennis_value_bets(
        odds_api_key=ODDS_API_KEY,
        days_ahead=DAYS_AHEAD,
        min_edge=MIN_EDGE_WATCH,
        bankroll=BANKROLL,
    )

    # ── Mundial 2026 (Pinnacle como referencia, sin tabla de liga) ──────────
    console.print("\n[bold cyan]🏆  Escaneando Mundial 2026...[/bold cyan]")
    world_cup_bets = scan_world_cup_value_bets(
        odds_api_key=ODDS_API_KEY,
        days_ahead=max(DAYS_AHEAD, 7),   # el calendario del Mundial es más amplio
        min_edge=MIN_EDGE_WATCH,
        bankroll=BANKROLL,
    )

    all_bets = football_bets + tennis_bets + world_cup_bets

    if not all_bets:
        console.print(f"\n[yellow]Sin value bets hoy.[/yellow]")
        return

    # ── Clasificar ──────────────────────────────────────────────────────────

    # CONVICCIÓN: cuota ≤ 1.75 + prob ≥ 62% + edge ≥ 5%
    conviction = [
        b for b in all_bets
        if b["odds"] <= MAX_ODDS_CONVICTION
        and b["model"] >= MIN_MODEL_PROB
        and b["edge"]  >= MIN_EDGE_CONVICTION
    ]
    conviction.sort(key=conviction_score, reverse=True)

    # ALTO EDGE: edge ≥ 5% pero no pasan el filtro de cuota/prob de convicción
    high_edge = [
        b for b in all_bets
        if b not in conviction
        and b["edge"] >= MIN_EDGE_CONVICTION
        and b["verdict"] in ("VALUE BET", "MARGINAL")
    ]
    high_edge.sort(key=lambda x: x["edge"], reverse=True)

    # EN VIGILANCIA: edge entre 3-5%, cualquier cuota razonable (≤ 3.00)
    watch = [
        b for b in all_bets
        if b not in conviction
        and b not in high_edge
        and b["edge"] >= MIN_EDGE_WATCH
        and b["verdict"] in ("VALUE BET", "MARGINAL")
        and b["odds"] <= 3.00
    ]
    watch.sort(key=lambda x: x["edge"], reverse=True)

    # ── Output ──────────────────────────────────────────────────────────────
    if conviction:
        print_section(
            conviction,
            f"🎯  ALTA CONVICCIÓN — cuota ≤ {MAX_ODDS_CONVICTION} · prob ≥ {MIN_MODEL_PROB}% · edge ≥ {MIN_EDGE_CONVICTION}%"
            f"  →  APOSTAR FUERTE  ({len(conviction)} apuestas)",
            color="green",
            show_hitrate=True,
        )
    else:
        console.print(
            f"\n[yellow]  Sin apuestas de alta convicción hoy "
            f"(cuota ≤ {MAX_ODDS_CONVICTION} + prob ≥ {MIN_MODEL_PROB}% + edge ≥ {MIN_EDGE_CONVICTION}%).[/yellow]"
        )

    if high_edge:
        print_section(
            high_edge,
            f"⚡  ALTO EDGE — edge ≥ {MIN_EDGE_CONVICTION}% · cualquier cuota  ({len(high_edge)})  →  Apostar moderado",
            color="yellow",
            show_hitrate=True,
        )

    if watch:
        print_section(
            watch,
            f"👁  EN VIGILANCIA — edge ≥ {MIN_EDGE_WATCH}% · cuota ≤ 3.00  ({len(watch)})  →  Solo seguimiento",
            color="cyan",
            show_hitrate=True,
        )

    # ── Resumen ──────────────────────────────────────────────────────────────
    def _counts(items):
        f = sum(1 for b in items if b.get("sport") in (None, "football"))
        t = sum(1 for b in items if b.get("sport") == "tennis")
        m = sum(1 for b in items if b.get("sport") == "world_cup")
        return f, t, m

    kelly_total = sum(b["kelly"] for b in conviction)
    futbol_c, tenis_c, mundial_c       = _counts(conviction)
    he_futbol, he_tenis, he_mundial    = _counts(high_edge)

    console.print(f"\n[bold]{'━'*115}[/bold]")
    if conviction:
        avg_hit  = sum(b["model"] for b in conviction) / len(conviction)
        avg_edge = sum(b["edge"]  for b in conviction) / len(conviction)
        console.print(
            f"  [bold green]🎯 CONVICCIÓN: {len(conviction)}[/bold green]  "
            f"[dim](⚽ {futbol_c}  🎾 {tenis_c}  🏆 {mundial_c})[/dim]  "
            f"  Hit rate medio: [bold green]{avg_hit:.1f}%[/bold green]  "
            f"  Edge medio: [bold green]+{avg_edge:.1f}%[/bold green]  "
            f"  Kelly total: [bold green]€{kelly_total:.2f}[/bold green]"
        )
    if high_edge:
        he_avg_edge = sum(b["edge"] for b in high_edge) / len(high_edge)
        console.print(
            f"  [bold yellow]⚡ ALTO EDGE:   {len(high_edge)}[/bold yellow]  "
            f"[dim](⚽ {he_futbol}  🎾 {he_tenis}  🏆 {he_mundial})[/dim]  "
            f"  Edge medio: [bold yellow]+{he_avg_edge:.1f}%[/bold yellow]"
        )
    if watch:
        console.print(
            f"  [bold cyan]👁  VIGILANCIA:  {len(watch)}[/bold cyan]  "
            f"[dim]bets con edge {MIN_EDGE_WATCH}-{MIN_EDGE_CONVICTION}%[/dim]"
        )
    console.print(
        f"  [dim]HitRate = prob del modelo = % acierto esperado  |  "
        f"Break-ev = % mínimo para no perder a esa cuota[/dim]"
    )
    console.print()


if __name__ == "__main__":
    run()

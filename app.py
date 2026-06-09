import streamlit as st
import pandas as pd
from datetime import datetime

ODDS_API_KEY        = "2e0cc7717f96a25817a3c781429437b8"
BANKROLL            = 200.0
MIN_EDGE_WATCH      = 3.0
DAYS_AHEAD          = 3
BOOKMAKER           = "winamax_fr"
MAX_ODDS_CONVICTION = 1.75
MIN_MODEL_PROB      = 62.0
MIN_EDGE_CONVICTION = 5.0

FOOTBALL_LEAGUES = [
    "soccer_spain_la_liga",
    "soccer_spain_segunda_division",
    "soccer_epl",
    "soccer_germany_bundesliga",
    "soccer_italy_serie_a",
    "soccer_france_ligue_one",
    "soccer_uefa_champs_league",
]

st.set_page_config(page_title="Value Bets Scanner", page_icon="🏆", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

/* ═══════════════════════════════════════════
   FONDO — ESTADIO NOCTURNO
═══════════════════════════════════════════ */
html, body, .stApp {
    background-color: #04080f !important;
    background-image:
        radial-gradient(ellipse 120% 60% at 50% -10%, rgba(18, 90, 40, 0.35) 0%, transparent 65%),
        radial-gradient(ellipse 80% 40% at 20% 110%, rgba(8, 40, 80, 0.4) 0%, transparent 60%),
        radial-gradient(ellipse 80% 40% at 80% 110%, rgba(8, 40, 80, 0.4) 0%, transparent 60%),
        linear-gradient(180deg, #04080f 0%, #060d1a 50%, #04080f 100%) !important;
}

/* Líneas de campo sutiles en el fondo */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
        repeating-linear-gradient(
            0deg,
            transparent,
            transparent 79px,
            rgba(255,255,255,0.012) 79px,
            rgba(255,255,255,0.012) 80px
        );
    pointer-events: none;
    z-index: 0;
}

/* Ocultar decoración nativa de Streamlit */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; }

/* ═══════════════════════════════════════════
   HEADER
═══════════════════════════════════════════ */
.header {
    position: relative;
    overflow: hidden;
    border-radius: 16px;
    padding: 2.4rem 2.8rem;
    margin-bottom: 1.8rem;
    background: linear-gradient(135deg, #071428 0%, #0a1f1a 50%, #071428 100%);
    border: 1px solid rgba(212, 175, 55, 0.4);
    box-shadow:
        0 0 60px rgba(18, 90, 40, 0.25),
        0 0 120px rgba(18, 90, 40, 0.1),
        inset 0 1px 0 rgba(212,175,55,0.2);
}
/* Reflejo de hierba en header */
.header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background:
        radial-gradient(ellipse 100% 80% at 50% 110%, rgba(18,120,50,0.3) 0%, transparent 60%),
        radial-gradient(ellipse 40% 60% at 0% 50%, rgba(212,175,55,0.06) 0%, transparent 50%),
        radial-gradient(ellipse 40% 60% at 100% 50%, rgba(212,175,55,0.06) 0%, transparent 50%);
    pointer-events: none;
}
/* Patrón de líneas del campo en header */
.header::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: repeating-linear-gradient(
        90deg, transparent, transparent 49px,
        rgba(255,255,255,0.025) 49px, rgba(255,255,255,0.025) 50px
    );
    pointer-events: none;
}
.header-eyebrow {
    font-family: 'Barlow', sans-serif;
    font-size: 0.72rem; font-weight: 700;
    letter-spacing: 5px; text-transform: uppercase;
    color: #d4af37;
    margin-bottom: 0.5rem;
    position: relative; z-index: 1;
}
.header-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 4rem; color: #ffffff;
    letter-spacing: 6px; line-height: 1;
    margin-bottom: 0.7rem;
    position: relative; z-index: 1;
    text-shadow: 0 0 40px rgba(212,175,55,0.3), 0 2px 4px rgba(0,0,0,0.6);
}
.header-title span {
    color: #d4af37;
    text-shadow: 0 0 30px rgba(212,175,55,0.6);
}
.header-info {
    font-family: 'Barlow', sans-serif;
    font-size: 0.8rem; color: #7a9ab5;
    position: relative; z-index: 1;
}
.header-trophy {
    position: absolute;
    right: 2.5rem; top: 50%; transform: translateY(-50%);
    font-size: 5rem; opacity: 0.15;
    z-index: 1;
    filter: drop-shadow(0 0 20px rgba(212,175,55,0.5));
}

/* ═══════════════════════════════════════════
   MÉTRICAS
═══════════════════════════════════════════ */
.metrics {
    display: flex; gap: 12px;
    margin-bottom: 2rem; flex-wrap: wrap;
}
.metric {
    flex: 1; min-width: 110px;
    background: linear-gradient(145deg, #0d1e30, #08131e);
    border: 1px solid #1a3050;
    border-radius: 12px; padding: 1.1rem 1rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 28px rgba(0,0,0,0.4);
}
.metric.highlight { border-color: rgba(212,175,55,0.4); background: linear-gradient(145deg, #14200d, #0a1508); }
.metric-val {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.6rem; line-height: 1;
    color: #d4af37;
}
.metric-val.blanco   { color: #e8f0f8; }
.metric-val.amarillo { color: #ffd166; text-shadow: 0 0 15px rgba(255,209,102,0.4); }
.metric-val.verde    { color: #3dd878; text-shadow: 0 0 15px rgba(61,216,120,0.4); }
.metric-val.oro      { color: #d4af37; text-shadow: 0 0 15px rgba(212,175,55,0.4); }
.metric-lbl {
    font-family: 'Barlow', sans-serif;
    font-size: 0.65rem; font-weight: 700;
    color: #4a6a85; text-transform: uppercase;
    letter-spacing: 2px; margin-top: 6px;
}

/* ═══════════════════════════════════════════
   SECTION HEADERS
═══════════════════════════════════════════ */
.section-header {
    display: flex; align-items: center; gap: 12px;
    margin: 2rem 0 1rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid #132035;
}
.section-badge {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.75rem; letter-spacing: 2px;
    padding: 5px 14px; border-radius: 6px;
}
.section-badge.conviction { background: #3dd878; color: #04080f; }
.section-badge.high       { background: #ffd166; color: #04080f; }
.section-badge.watch      { background: transparent; color: #60c0ff; border: 1px solid rgba(96,192,255,0.5); }
.section-badge.mundial    { background: linear-gradient(90deg, #d4af37, #f0d060); color: #04080f; }
.section-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem; color: #e8f0f8; letter-spacing: 3px;
}
.section-desc {
    font-family: 'Barlow', sans-serif;
    font-size: 0.7rem; color: #4a6a85; margin-left: auto;
}

/* ═══════════════════════════════════════════
   TARJETAS DE APUESTAS
═══════════════════════════════════════════ */
.bet {
    border-radius: 12px; padding: 1.2rem 1.6rem;
    margin-bottom: 10px;
    display: grid; grid-template-columns: 1fr auto;
    gap: 2rem; align-items: center;
    transition: transform 0.15s, box-shadow 0.15s;
}
.bet:hover { transform: translateX(3px); }

.bet.conviction {
    background: linear-gradient(135deg, #071f10, #0a2814);
    border: 1px solid rgba(61,216,120,0.25);
    border-left: 4px solid #3dd878;
    box-shadow: 0 4px 24px rgba(61,216,120,0.08), inset 0 1px 0 rgba(61,216,120,0.1);
}
.bet.high {
    background: linear-gradient(135deg, #1a1a07, #221e08);
    border: 1px solid rgba(255,209,102,0.2);
    border-left: 4px solid #ffd166;
    box-shadow: 0 4px 24px rgba(255,209,102,0.06);
}
.bet.watch {
    background: linear-gradient(135deg, #07101a, #0a1520);
    border: 1px solid rgba(96,192,255,0.15);
    border-left: 4px solid rgba(96,192,255,0.5);
    opacity: 0.9;
}

.bet-league {
    font-family: 'Barlow', sans-serif; font-size: 0.68rem;
    font-weight: 700; color: #4a6a85;
    text-transform: uppercase; letter-spacing: 2px; margin-bottom: 5px;
}
.bet-match {
    font-family: 'Bebas Neue', sans-serif; font-size: 1.45rem;
    color: #ffffff; letter-spacing: 1.5px; margin-bottom: 8px; line-height: 1.1;
}
.bet-market-pill {
    display: inline-block; border-radius: 20px;
    padding: 4px 16px; font-family: 'Barlow', sans-serif;
    font-size: 0.78rem; font-weight: 600;
}
.bet-market-pill.conviction { background: rgba(61,216,120,0.1); border: 1px solid rgba(61,216,120,0.4); color: #3dd878; }
.bet-market-pill.high       { background: rgba(255,209,102,0.1); border: 1px solid rgba(255,209,102,0.4); color: #ffd166; }
.bet-market-pill.watch      { background: rgba(96,192,255,0.08); border: 1px solid rgba(96,192,255,0.3); color: #60c0ff; }

.bet-stats-row { display: flex; gap: 14px; margin-top: 9px; flex-wrap: wrap; }
.bet-stat      { font-family: 'Barlow', sans-serif; font-size: 0.7rem; color: #4a6a85; }
.bet-stat span { color: #c8d8e8; font-weight: 600; }
.bet-date      { font-family: 'Barlow', sans-serif; font-size: 0.7rem; color: #3a5a75; margin-top: 7px; }

.bet-right     { text-align: right; min-width: 130px; }
.bet-odds      { font-family: 'Bebas Neue', sans-serif; font-size: 3rem; line-height: 1; }
.bet-odds.conviction { color: #3dd878; text-shadow: 0 0 20px rgba(61,216,120,0.4); }
.bet-odds.high       { color: #ffd166; text-shadow: 0 0 20px rgba(255,209,102,0.4); }
.bet-odds.watch      { color: #60c0ff; }

.bet-edge { font-family: 'Barlow', sans-serif; font-size: 0.82rem; font-weight: 800; margin-top: 3px; letter-spacing: 0.5px; }
.bet-edge.conviction { color: #3dd878; }
.bet-edge.high       { color: #ffd166; }
.bet-edge.watch      { color: #60c0ff; }
.bet-ev    { font-family: 'Barlow', sans-serif; font-size: 0.7rem; color: #4a6a85; margin-top: 3px; }
.bet-kelly {
    font-family: 'Barlow', sans-serif; font-size: 0.78rem; font-weight: 700;
    color: #c8d8e8; margin-top: 7px;
    background: rgba(255,255,255,0.05); border: 1px solid #1a3050;
    padding: 3px 12px; border-radius: 6px; display: inline-block;
}

/* ═══════════════════════════════════════════
   MUNDIAL — TOP 5
═══════════════════════════════════════════ */
.top5-header-note {
    font-family: 'Barlow', sans-serif; font-size: 0.72rem;
    color: #4a6a85; margin-bottom: 16px;
    padding: 8px 14px; background: rgba(212,175,55,0.05);
    border-left: 3px solid rgba(212,175,55,0.3);
    border-radius: 0 6px 6px 0;
}
.top5-row {
    background: linear-gradient(135deg, #0a1828, #071220);
    border: 1px solid #132035;
    border-radius: 12px; padding: 1rem 1.4rem;
    margin-bottom: 10px;
    display: grid;
    grid-template-columns: 52px 1fr 130px 130px 130px 130px;
    align-items: center; gap: 10px;
    transition: transform 0.15s;
}
.top5-row:hover { transform: translateX(3px); }
.top5-row.gold   { border-left: 4px solid #d4af37; background: linear-gradient(135deg, #14180a, #0e1408); }
.top5-row.silver { border-left: 4px solid #9ca8b4; }
.top5-row.bronze { border-left: 4px solid #a0632a; }
.top5-row.norm   { border-left: 4px solid #1a3050; }

.top5-medal {
    font-size: 1.9rem; text-align: center; line-height: 1;
    filter: drop-shadow(0 2px 6px rgba(0,0,0,0.5));
}
.top5-match  { font-family: 'Bebas Neue', sans-serif; font-size: 1.1rem; color: #e8f0f8; letter-spacing: 1px; line-height: 1.2; }
.top5-date   { font-family: 'Barlow', sans-serif; font-size: 0.67rem; color: #3a5a75; margin-top: 3px; }

.top5-cell   { text-align: center; }
.top5-lbl    { font-family: 'Barlow', sans-serif; font-size: 0.6rem; font-weight: 700; color: #3a5a75; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px; }
.top5-val    { font-family: 'Bebas Neue', sans-serif; font-size: 1.35rem; color: #e8f0f8; line-height: 1; }
.top5-val.gold   { color: #d4af37; text-shadow: 0 0 12px rgba(212,175,55,0.4); }
.top5-val.green  { color: #3dd878; text-shadow: 0 0 12px rgba(61,216,120,0.4); }
.top5-val.yellow { color: #ffd166; text-shadow: 0 0 12px rgba(255,209,102,0.3); }
.top5-val.grey   { color: #7a9ab5; }
.top5-sub    { font-family: 'Barlow', sans-serif; font-size: 0.62rem; color: #3a5a75; margin-top: 2px; }

/* ═══════════════════════════════════════════
   MUNDIAL — TABLA COMPLETA
═══════════════════════════════════════════ */
.table-title {
    font-family: 'Bebas Neue', sans-serif; font-size: 1rem;
    color: #d4af37; letter-spacing: 4px;
    margin: 2rem 0 0.6rem; display: flex; align-items: center; gap: 10px;
}
.wc-table-wrap {
    border-radius: 12px; overflow: hidden;
    border: 1px solid #132035;
    box-shadow: 0 8px 40px rgba(0,0,0,0.4);
}
.wc-table { width: 100%; border-collapse: collapse; }

.wc-table thead tr {
    background: linear-gradient(90deg, #0d1e32, #0a1828);
    border-bottom: 2px solid rgba(212,175,55,0.2);
}
.wc-table thead th {
    padding: 12px 14px;
    font-family: 'Barlow', sans-serif;
    font-size: 0.65rem; font-weight: 700;
    color: #4a6a85; text-transform: uppercase;
    letter-spacing: 2px; text-align: center;
    white-space: nowrap;
}
.wc-table thead th:first-child,
.wc-table thead th:nth-child(2) { text-align: left; }

.wc-table tbody tr {
    border-bottom: 1px solid #0d1825;
    transition: background 0.12s;
}
.wc-table tbody tr:hover { background: rgba(212,175,55,0.04); }
.wc-table tbody tr:nth-child(even) { background: rgba(255,255,255,0.015); }
.wc-table tbody tr:nth-child(even):hover { background: rgba(212,175,55,0.05); }

.wc-table td {
    padding: 11px 14px;
    font-family: 'Barlow', sans-serif;
    font-size: 0.78rem; color: #8aaac4;
    text-align: center; vertical-align: middle;
}
.wc-table td:nth-child(2) {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.95rem; color: #e8f0f8; letter-spacing: 0.5px;
    text-align: left;
}
.wc-table td:first-child { text-align: left; color: #3a5a75; font-size: 0.7rem; white-space: nowrap; }

.prob-hi  { color: #3dd878 !important; font-weight: 700; }
.prob-med { color: #ffd166 !important; font-weight: 700; }
.prob-lo  { color: #8aaac4; }

.margin-ok  { color: #3dd878 !important; font-weight: 700; font-size: 0.78rem; }
.margin-mid { color: #ffd166 !important; font-weight: 700; font-size: 0.78rem; }
.margin-bad { color: #3a5a75; font-size: 0.75rem; }

.fav-pill {
    display: inline-block; padding: 3px 10px; border-radius: 5px;
    font-family: 'Barlow', sans-serif; font-size: 0.7rem; font-weight: 700;
    background: rgba(212,175,55,0.1); color: #d4af37;
    border: 1px solid rgba(212,175,55,0.3); white-space: nowrap;
}
.dnb-pill {
    display: inline-block; padding: 3px 9px; border-radius: 5px;
    font-family: 'Bebas Neue', sans-serif; font-size: 0.82rem;
    background: rgba(96,192,255,0.08); color: #60c0ff;
    border: 1px solid rgba(96,192,255,0.25); white-space: nowrap;
}

.wc-legend {
    background: rgba(255,255,255,0.02);
    border: 1px solid #0d1825; border-top: none;
    border-radius: 0 0 12px 12px;
    padding: 10px 16px;
    font-family: 'Barlow', sans-serif; font-size: 0.68rem;
    color: #3a5a75; display: flex; gap: 22px; flex-wrap: wrap;
}

/* ═══════════════════════════════════════════
   MISCELÁNEA
═══════════════════════════════════════════ */
.empty {
    text-align: center; padding: 2.5rem;
    border: 1px dashed #132035; border-radius: 12px;
    font-family: 'Barlow', sans-serif; font-size: 0.82rem;
    color: #3a5a75; letter-spacing: 3px; text-transform: uppercase;
}

div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #d4af37, #c49a22) !important;
    color: #04080f !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.25rem !important; letter-spacing: 6px !important;
    border: none !important; border-radius: 10px !important;
    padding: 0.9rem !important; width: 100% !important;
    box-shadow: 0 4px 20px rgba(212,175,55,0.25) !important;
    transition: opacity 0.2s, transform 0.1s !important;
}
div[data-testid="stButton"] > button:hover {
    opacity: 0.9 !important; transform: translateY(-1px) !important;
    box-shadow: 0 6px 28px rgba(212,175,55,0.35) !important;
}
.stDownloadButton > button {
    background: transparent !important; color: #4a6a85 !important;
    border: 1px solid #132035 !important;
    font-family: 'Barlow', sans-serif !important; font-size: 0.78rem !important;
    border-radius: 8px !important;
}
.stDownloadButton > button:hover { color: #d4af37 !important; border-color: rgba(212,175,55,0.3) !important; }
</style>
""", unsafe_allow_html=True)


# ── Header ───────────────────────────────────────────────────────────────────
now = datetime.now()
st.markdown(f"""
<div class="header">
    <div class="header-trophy">🏆</div>
    <div class="header-eyebrow">⚽ Fútbol &nbsp;·&nbsp; 🎾 Tenis &nbsp;·&nbsp; 🏆 Mundial 2026 &nbsp;·&nbsp; Winamax FR</div>
    <div class="header-title">Value Bets <span>Scanner</span></div>
    <div class="header-info">
        {now.strftime('%A %d %B %Y').capitalize()} &nbsp;&nbsp;|&nbsp;&nbsp;
        Bankroll <b style="color:#d4af37">€{BANKROLL}</b> &nbsp;&nbsp;|&nbsp;&nbsp;
        Edge mínimo <b style="color:#d4af37">{MIN_EDGE_WATCH}%</b> &nbsp;&nbsp;|&nbsp;&nbsp;
        Modelo: Poisson (fútbol) · Pinnacle sharp (tenis &amp; Mundial)
    </div>
</div>
""", unsafe_allow_html=True)


# ── Botón ────────────────────────────────────────────────────────────────────
if st.button("🔍  ESCANEAR APUESTAS DE HOY"):
    import sys
    sys.path.insert(0, "/mount/src/bets-screener")
    from modules.scanner           import scan_value_bets
    from modules.tennis_scanner    import scan_tennis_value_bets
    from modules.world_cup_scanner import scan_world_cup_value_bets, get_world_cup_projections

    with st.spinner("⚽  Escaneando ligas de fútbol..."):
        football_bets = scan_value_bets(
            odds_api_key=ODDS_API_KEY, leagues=FOOTBALL_LEAGUES,
            days_ahead=DAYS_AHEAD, min_edge=MIN_EDGE_WATCH,
            bookmaker=BOOKMAKER, bankroll=BANKROLL,
        )
        for b in football_bets:
            b.setdefault("sport", "football")

    with st.spinner("🎾  Escaneando torneos de tenis..."):
        tennis_bets = scan_tennis_value_bets(
            odds_api_key=ODDS_API_KEY, days_ahead=DAYS_AHEAD,
            min_edge=MIN_EDGE_WATCH, bankroll=BANKROLL,
        )

    with st.spinner("🏆  Escaneando Mundial 2026..."):
        world_cup_bets = scan_world_cup_value_bets(
            odds_api_key=ODDS_API_KEY, days_ahead=7,
            min_edge=MIN_EDGE_WATCH, bankroll=BANKROLL,
        )
        wc_proj = get_world_cup_projections(odds_api_key=ODDS_API_KEY, days_ahead=7)

    all_bets = football_bets + tennis_bets + world_cup_bets

    # ── Clasificar ───────────────────────────────────────────────────────────
    conviction = [
        b for b in all_bets
        if b["odds"] <= MAX_ODDS_CONVICTION
        and b["model"] >= MIN_MODEL_PROB
        and b["edge"] >= MIN_EDGE_CONVICTION
    ]
    conviction.sort(key=lambda x: x["edge"] * x["model"] / 100, reverse=True)

    high_edge = [
        b for b in all_bets
        if b not in conviction
        and b["edge"] >= MIN_EDGE_CONVICTION
        and b["verdict"] in ("VALUE BET", "MARGINAL")
    ]
    high_edge.sort(key=lambda x: x["edge"], reverse=True)

    watch = [
        b for b in all_bets
        if b not in conviction and b not in high_edge
        and b["edge"] >= MIN_EDGE_WATCH
        and b["verdict"] in ("VALUE BET", "MARGINAL")
        and b["odds"] <= 3.00
    ]
    watch.sort(key=lambda x: x["edge"], reverse=True)

    total_kelly = sum(b["kelly"] for b in conviction)

    # ── Métricas ──────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="metrics">
        <div class="metric highlight">
            <div class="metric-val verde">{len(conviction)}</div>
            <div class="metric-lbl">🎯 Alta Convicción</div>
        </div>
        <div class="metric">
            <div class="metric-val amarillo">{len(high_edge)}</div>
            <div class="metric-lbl">⚡ Alto Edge</div>
        </div>
        <div class="metric">
            <div class="metric-val blanco">{len(watch)}</div>
            <div class="metric-lbl">👁 Vigilancia</div>
        </div>
        <div class="metric">
            <div class="metric-val oro">{len(wc_proj)}</div>
            <div class="metric-lbl">🏆 Partidos Mundial</div>
        </div>
        <div class="metric highlight">
            <div class="metric-val verde">€{total_kelly:.0f}</div>
            <div class="metric-lbl">Kelly Total</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Render secciones de apuestas ─────────────────────────────────────────
    def render_section(bets, css, badge_css, badge_text, label, desc):
        st.markdown(f"""
        <div class="section-header">
            <span class="section-badge {badge_css}">{badge_text}</span>
            <span class="section-label">{label}</span>
            <span class="section-desc">{desc}</span>
        </div>""", unsafe_allow_html=True)

        if not bets:
            st.markdown('<div class="empty">Sin apuestas en esta categoría hoy</div>',
                        unsafe_allow_html=True)
            return

        cards = ""
        for b in bets:
            dt    = b["kickoff"]
            fecha = f"{dt[5:10]}  ·  {dt[11:16]}" if len(dt) > 10 else dt
            sport = b.get("sport", "football")
            icon  = "🎾" if sport == "tennis" else ("🏆" if sport == "world_cup" else "⚽")
            kelly_str = f"€{b['kelly']:.2f}" if b["kelly"] > 0 else "—"
            breakeven = round(100 / b["odds"], 1)
            cards += f"""
            <div class="bet {css}">
                <div>
                    <div class="bet-league">{icon}&nbsp; {b['league']}</div>
                    <div class="bet-match">{b['match']}</div>
                    <span class="bet-market-pill {css}">{b['market']}</span>
                    <div class="bet-stats-row">
                        <span class="bet-stat">Modelo: <span>{b['model']:.1f}%</span></span>
                        <span class="bet-stat">Break-even: <span>{breakeven}%</span></span>
                        <span class="bet-stat">Prob implícita: <span>{b['implied']:.1f}%</span></span>
                    </div>
                    <div class="bet-date">📅 {fecha}</div>
                </div>
                <div class="bet-right">
                    <div class="bet-odds {css}">{b['odds']}</div>
                    <div class="bet-edge {css}">▲ +{b['edge']:.1f}% edge</div>
                    <div class="bet-ev">EV / 10€ &nbsp;+{b['ev_10']:.2f}€</div>
                    <div class="bet-kelly">Kelly &nbsp;{kelly_str}</div>
                </div>
            </div>"""
        st.markdown(cards, unsafe_allow_html=True)

    render_section(conviction, "conviction", "conviction",
        "🎯 ALTA CONVICCIÓN", f"{len(conviction)} apuestas — APOSTAR FUERTE",
        f"Cuota ≤ {MAX_ODDS_CONVICTION} · Prob ≥ {MIN_MODEL_PROB}% · Edge ≥ {MIN_EDGE_CONVICTION}%")

    render_section(high_edge, "high", "high",
        "⚡ ALTO EDGE", f"{len(high_edge)} apuestas — Apostar moderado",
        f"Edge ≥ {MIN_EDGE_CONVICTION}% · Cualquier cuota")

    render_section(watch, "watch", "watch",
        "👁 VIGILANCIA", f"{len(watch)} apuestas — Solo seguimiento",
        f"Edge {MIN_EDGE_WATCH}-{MIN_EDGE_CONVICTION}% · Cuota ≤ 3.00")

    # ════════════════════════════════════════════════════════════════════════
    # SECCIÓN MUNDIAL 2026
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class="section-header" style="border-bottom-color: rgba(212,175,55,0.2);">
        <span class="section-badge mundial">🏆 MUNDIAL 2026</span>
        <span class="section-label">PROYECCIONES — TODOS LOS PARTIDOS</span>
        <span class="section-desc">Pinnacle sharp sin margen · Cuotas Winamax FR</span>
    </div>
    """, unsafe_allow_html=True)

    if not wc_proj:
        st.markdown('<div class="empty">Sin partidos del Mundial disponibles esta semana</div>',
                    unsafe_allow_html=True)
    else:
        # ── TOP 5 ────────────────────────────────────────────────────────────
        st.markdown("""
        <div class="table-title">🥇 TOP 5 — MEJOR RELACIÓN SEGURIDAD / CUOTA</div>
        <div class="top5-header-note">
            Ordenado por menor margen negativo en DNB — el favorito tiene el empate como "red de seguridad".
            <b style="color:#3dd878">Verde</b> ≥ −1.5% · <b style="color:#ffd166">Amarillo</b> ≥ −3%
        </div>
        """, unsafe_allow_html=True)

        top5   = sorted(wc_proj, key=lambda x: x["gap_dnb"], reverse=True)[:5]
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        rows_css = ["gold", "silver", "bronze", "norm", "norm"]

        top5_html = ""
        for i, p in enumerate(top5):
            mg_css = "green" if p["gap_dnb"] >= -1.5 else ("yellow" if p["gap_dnb"] >= -3.0 else "grey")
            fecha_str = p["kickoff"].replace("2026-", "").replace("-", "/")
            top5_html += f"""
            <div class="top5-row {rows_css[i]}">
                <div class="top5-medal">{medals[i]}</div>
                <div>
                    <div class="top5-match">{p['home']} vs {p['away']}</div>
                    <div class="top5-date">📅 {fecha_str}</div>
                </div>
                <div class="top5-cell">
                    <div class="top5-lbl">Favorito</div>
                    <div class="top5-val gold">{p['fav']}</div>
                    <div class="top5-sub">{p['fav_prob']}% prob modelo</div>
                </div>
                <div class="top5-cell">
                    <div class="top5-lbl">Victoria directa</div>
                    <div class="top5-val">@ {p['fav_odds']}</div>
                    <div class="top5-sub">Break-even {round(100/p['fav_odds'],1)}%</div>
                </div>
                <div class="top5-cell">
                    <div class="top5-lbl">DNB (sin empate)</div>
                    <div class="top5-val">@ {p['fav_dnb_odds']}</div>
                    <div class="top5-sub">{p['fav_dnb_prob']}% prob condicional</div>
                </div>
                <div class="top5-cell">
                    <div class="top5-lbl">Margen DNB</div>
                    <div class="top5-val {mg_css}">{p['gap_dnb']:+.1f}%</div>
                    <div class="top5-sub">prob − break-even</div>
                </div>
            </div>"""

        st.markdown(top5_html, unsafe_allow_html=True)

        # ── Cuadro completo ──────────────────────────────────────────────────
        st.markdown('<div class="table-title">📋 CUADRO COMPLETO — TODOS LOS PARTIDOS</div>',
                    unsafe_allow_html=True)

        def pc(v):
            return "prob-hi" if v >= 65 else ("prob-med" if v >= 50 else "prob-lo")

        def mc(v):
            return "margin-ok" if v >= -1.5 else ("margin-mid" if v >= -3.0 else "margin-bad")

        rows_html = ""
        for p in wc_proj:
            fd   = p["kickoff"].replace("2026-", "").replace("-", "/")
            dnb  = (f'<span class="dnb-pill">@ {p["fav_dnb_odds"]}</span>'
                    f'<div style="font-size:0.62rem;color:#3a5a75;margin-top:2px;">{p["fav_dnb_prob"]}%</div>'
                    ) if p["fav_dnb_odds"] >= 1.05 else "—"
            rows_html += f"""
            <tr>
                <td>{fd}</td>
                <td>{p['home']} vs {p['away']}</td>
                <td><span class="{pc(p['home_prob'])}">{p['home_prob']}%</span>
                    <div style="font-size:0.62rem;color:#3a5a75;">@ {p['home_odds']}</div></td>
                <td><span style="color:#8aaac4;">{p['draw_prob']}%</span>
                    <div style="font-size:0.62rem;color:#3a5a75;">@ {p['draw_odds']}</div></td>
                <td><span class="{pc(p['away_prob'])}">{p['away_prob']}%</span>
                    <div style="font-size:0.62rem;color:#3a5a75;">@ {p['away_odds']}</div></td>
                <td><span class="fav-pill">{p['fav']}</span></td>
                <td>{dnb}</td>
                <td><span class="{mc(p['gap_win'])}">{p['gap_win']:+.1f}%</span></td>
                <td><span class="{mc(p['gap_dnb'])}">{p['gap_dnb']:+.1f}%</span></td>
            </tr>"""

        st.markdown(f"""
        <div class="wc-table-wrap">
            <table class="wc-table">
                <thead><tr>
                    <th>Fecha</th><th>Partido</th>
                    <th>Local</th><th>Empate</th><th>Visitante</th>
                    <th>Favorito</th><th>DNB</th>
                    <th>Margen Vic.</th><th>Margen DNB</th>
                </tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
            <div class="wc-legend">
                <span>🔑 <b style="color:#d4af37">Margen</b> = prob modelo − break-even (menos negativo = mejor precio)</span>
                <span>🛡 <b style="color:#60c0ff">DNB</b> = Draw No Bet — empate devuelve la apuesta</span>
                <span><b style="color:#3dd878">Verde</b> ≥ −1.5% &nbsp;·&nbsp; <b style="color:#ffd166">Amarillo</b> ≥ −3% &nbsp;·&nbsp; Gris = peor precio</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Export ───────────────────────────────────────────────────────────────
    if all_bets:
        st.markdown("<br>", unsafe_allow_html=True)
        df = pd.DataFrame([{
            "Liga": b["league"], "Partido": b["match"],
            "Fecha": b["kickoff"], "Apuesta": b["market"],
            "Cuota": b["odds"], "Modelo%": b["model"],
            "Edge%": b["edge"], "Kelly€": b["kelly"],
            "Veredicto": b["verdict"],
        } for b in all_bets])
        st.download_button(
            "↓  Descargar CSV completo",
            df.to_csv(index=False).encode("utf-8"),
            f"value_bets_{now.strftime('%Y%m%d')}.csv",
            "text/csv",
        )

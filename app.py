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

st.set_page_config(page_title="Value Bets Scanner", page_icon="⚽", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;500;600;700&display=swap');

html, body, .stApp { background-color: #0d1b2a !important; }

/* ── Header ── */
.header {
    background: #1a2e45;
    border: 2px solid #c9a84c;
    border-radius: 14px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
}
.header-eyebrow {
    font-family: 'Barlow', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #c9a84c;
    margin-bottom: 0.4rem;
}
.header-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.5rem;
    color: #ffffff;
    letter-spacing: 4px;
    line-height: 1;
    margin-bottom: 0.6rem;
}
.header-title span { color: #c9a84c; }
.header-info {
    font-family: 'Barlow', sans-serif;
    font-size: 0.82rem;
    color: #a0b4c8;
}

/* ── Métricas ── */
.metrics {
    display: flex;
    gap: 12px;
    margin-bottom: 1.8rem;
    flex-wrap: wrap;
}
.metric {
    flex: 1;
    min-width: 120px;
    background: #1a2e45;
    border: 1px solid #2a4060;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
}
.metric-val { font-family:'Bebas Neue',sans-serif; font-size:2.4rem; color:#c9a84c; line-height:1; }
.metric-val.blanco   { color:#ffffff; }
.metric-val.amarillo { color:#ffd166; }
.metric-val.verde    { color:#4cdb82; }
.metric-val.oro      { color:#c9a84c; }
.metric-lbl { font-family:'Barlow',sans-serif; font-size:0.7rem; font-weight:600; color:#a0b4c8; text-transform:uppercase; letter-spacing:2px; margin-top:6px; }

/* ── Section headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 1.8rem 0 1rem;
    padding-bottom: 0.7rem;
    border-bottom: 2px solid #2a4060;
}
.section-badge { font-family:'Bebas Neue',sans-serif; font-size:0.8rem; letter-spacing:2px; padding:4px 12px; border-radius:5px; }
.section-badge.conviction { background:#4cdb82; color:#0d1b2a; }
.section-badge.high       { background:#ffd166; color:#0d1b2a; }
.section-badge.watch      { background:transparent; color:#60c0ff; border:1px solid #60c0ff; }
.section-badge.mundial    { background:#c9a84c; color:#0d1b2a; }
.section-label { font-family:'Bebas Neue',sans-serif; font-size:1.1rem; color:#ffffff; letter-spacing:2px; }
.section-desc  { font-family:'Barlow',sans-serif; font-size:0.72rem; color:#a0b4c8; margin-left:auto; }

/* ── Tarjetas de apuestas ── */
.bet {
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 2rem;
    align-items: center;
}
.bet.conviction { background:#0d2a1a; border:1px solid #2a6040; border-left:5px solid #4cdb82; }
.bet.high       { background:#1a2a0d; border:1px solid #4a4020; border-left:5px solid #ffd166; }
.bet.watch      { background:#0d1a2a; border:1px solid #1a3050; border-left:5px solid #60c0ff; opacity:0.85; }

.bet-league { font-family:'Barlow',sans-serif; font-size:0.72rem; font-weight:700; color:#a0b4c8; text-transform:uppercase; letter-spacing:2px; margin-bottom:5px; }
.bet-match  { font-family:'Bebas Neue',sans-serif; font-size:1.4rem; color:#ffffff; letter-spacing:1px; margin-bottom:8px; line-height:1.1; }
.bet-market-pill { display:inline-block; border-radius:20px; padding:4px 14px; font-family:'Barlow',sans-serif; font-size:0.8rem; font-weight:600; }
.bet-market-pill.conviction { background:#0d1b2a; border:1px solid #4cdb82; color:#4cdb82; }
.bet-market-pill.high       { background:#0d1b2a; border:1px solid #ffd166; color:#ffd166; }
.bet-market-pill.watch      { background:#0d1b2a; border:1px solid #60c0ff; color:#60c0ff; }
.bet-stats-row { display:flex; gap:12px; margin-top:8px; flex-wrap:wrap; }
.bet-stat      { font-family:'Barlow',sans-serif; font-size:0.7rem; color:#a0b4c8; }
.bet-stat span { color:#ffffff; font-weight:600; }
.bet-date  { font-family:'Barlow',sans-serif; font-size:0.72rem; color:#a0b4c8; margin-top:6px; }
.bet-right { text-align:right; min-width:130px; }
.bet-odds  { font-family:'Bebas Neue',sans-serif; font-size:2.8rem; line-height:1; }
.bet-odds.conviction { color:#4cdb82; }
.bet-odds.high       { color:#ffd166; }
.bet-odds.watch      { color:#60c0ff; }
.bet-edge  { font-family:'Barlow',sans-serif; font-size:0.8rem; font-weight:700; margin-top:4px; }
.bet-edge.conviction { color:#4cdb82; }
.bet-edge.high       { color:#ffd166; }
.bet-edge.watch      { color:#60c0ff; }
.bet-ev    { font-family:'Barlow',sans-serif; font-size:0.72rem; color:#a0b4c8; margin-top:3px; }
.bet-kelly { font-family:'Barlow',sans-serif; font-size:0.78rem; font-weight:700; color:#ffffff; margin-top:6px; background:#0d1b2a; border:1px solid #2a4060; padding:3px 10px; border-radius:5px; display:inline-block; }

/* ── TOP 5 Mundial ── */
.top5-row {
    background: #0f2035;
    border: 1px solid #2a4060;
    border-radius: 10px;
    padding: 1rem 1.4rem;
    margin-bottom: 10px;
    display: grid;
    grid-template-columns: 40px 1fr 110px 110px 110px 110px;
    align-items: center;
    gap: 12px;
}
.top5-row.gold   { border-left: 5px solid #c9a84c; }
.top5-row.silver { border-left: 5px solid #a0b4c8; }
.top5-row.bronze { border-left: 5px solid #cd7f32; }
.top5-row.norm   { border-left: 5px solid #2a4060; }

.top5-num   { font-family:'Bebas Neue',sans-serif; font-size:1.8rem; color:#2a4060; text-align:center; }
.top5-num.gold   { color:#c9a84c; }
.top5-num.silver { color:#a0b4c8; }
.top5-num.bronze { color:#cd7f32; }

.top5-match  { font-family:'Bebas Neue',sans-serif; font-size:1.1rem; color:#ffffff; letter-spacing:1px; line-height:1.2; }
.top5-date   { font-family:'Barlow',sans-serif; font-size:0.68rem; color:#607080; margin-top:2px; }
.top5-cell   { text-align:center; }
.top5-lbl    { font-family:'Barlow',sans-serif; font-size:0.62rem; font-weight:600; color:#607080; text-transform:uppercase; letter-spacing:1px; margin-bottom:3px; }
.top5-val    { font-family:'Bebas Neue',sans-serif; font-size:1.3rem; color:#ffffff; line-height:1; }
.top5-val.gold    { color:#c9a84c; }
.top5-val.green   { color:#4cdb82; }
.top5-val.yellow  { color:#ffd166; }
.top5-val.grey    { color:#a0b4c8; }
.top5-sub    { font-family:'Barlow',sans-serif; font-size:0.62rem; color:#607080; }

/* ── Tabla completa Mundial ── */
.wc-table-wrap { border-radius:10px; overflow:hidden; border:1px solid #2a4060; margin-top:12px; }
.wc-table { width:100%; border-collapse:collapse; font-family:'Barlow',sans-serif; }
.wc-table thead tr { background:#1a3050; }
.wc-table thead th { padding:10px 12px; font-size:0.68rem; font-weight:700; color:#a0b4c8; text-transform:uppercase; letter-spacing:2px; text-align:center; white-space:nowrap; }
.wc-table thead th:nth-child(1),
.wc-table thead th:nth-child(2) { text-align:left; }
.wc-table tbody tr { border-bottom:1px solid #1a2e40; transition:background 0.15s; }
.wc-table tbody tr:hover { background:#1a2e45; }
.wc-table tbody tr:nth-child(even) { background:#0f1e30; }
.wc-table tbody tr:nth-child(even):hover { background:#1a2e45; }
.wc-table td { padding:10px 12px; font-size:0.78rem; color:#d0e0f0; text-align:center; vertical-align:middle; }
.wc-table td:nth-child(1),
.wc-table td:nth-child(2) { text-align:left; }
.wc-table td:nth-child(2) { font-family:'Bebas Neue',sans-serif; font-size:0.95rem; color:#ffffff; letter-spacing:0.5px; }
.prob-hi  { color:#4cdb82; font-weight:700; }
.prob-med { color:#ffd166; font-weight:700; }
.prob-lo  { color:#a0b4c8; }
.margin-ok   { color:#4cdb82; font-weight:700; font-size:0.75rem; }
.margin-mid  { color:#ffd166; font-weight:700; font-size:0.75rem; }
.margin-bad  { color:#607080; font-size:0.75rem; }
.fav-pill {
    display:inline-block; padding:2px 8px; border-radius:4px;
    font-family:'Barlow',sans-serif; font-size:0.7rem; font-weight:700;
    background:#1a3050; color:#c9a84c; border:1px solid #c9a84c;
    white-space:nowrap;
}
.dnb-pill {
    display:inline-block; padding:3px 8px; border-radius:4px;
    font-family:'Bebas Neue',sans-serif; font-size:0.8rem;
    background:#0d2030; color:#60c0ff; border:1px solid #2a5070;
    white-space:nowrap;
}

.wc-note-box {
    background:#0f1e30; border:1px solid #2a4060; border-radius:8px;
    padding:0.8rem 1.2rem; margin-top:12px;
    font-family:'Barlow',sans-serif; font-size:0.72rem; color:#607080;
    display:flex; gap:24px; flex-wrap:wrap;
}

/* ── Misc ── */
.empty { text-align:center; padding:2rem; border:1px dashed #2a4060; border-radius:10px; font-family:'Barlow',sans-serif; font-size:0.85rem; color:#a0b4c8; letter-spacing:2px; text-transform:uppercase; }

div[data-testid="stButton"] > button {
    background:#c9a84c !important; color:#0d1b2a !important;
    font-family:'Bebas Neue',sans-serif !important; font-size:1.2rem !important;
    letter-spacing:5px !important; border:none !important;
    border-radius:8px !important; padding:0.8rem !important; width:100% !important;
}
div[data-testid="stButton"] > button:hover { opacity:0.85 !important; }
.stDownloadButton > button {
    background:transparent !important; color:#c9a84c !important;
    border:1px solid #2a4060 !important; font-family:'Barlow',sans-serif !important; font-size:0.8rem !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
now = datetime.now()
st.markdown(f"""
<div class="header">
    <div class="header-eyebrow">⚽ Fútbol · 🎾 Tenis · 🏆 Mundial 2026 · Winamax FR</div>
    <div class="header-title">Value Bets <span>Scanner</span></div>
    <div class="header-info">{now.strftime('%A %d %B %Y')} &nbsp;·&nbsp; Bankroll €{BANKROLL} &nbsp;·&nbsp; Edge mínimo {MIN_EDGE_WATCH}%</div>
</div>
""", unsafe_allow_html=True)


# ── Botón de escaneo ─────────────────────────────────────────────────────────
if st.button("🔍  ESCANEAR HOY"):
    import sys
    sys.path.insert(0, "/mount/src/bets-screener")
    from modules.scanner           import scan_value_bets
    from modules.tennis_scanner    import scan_tennis_value_bets
    from modules.world_cup_scanner import scan_world_cup_value_bets, get_world_cup_projections

    with st.spinner("⚽  Escaneando fútbol..."):
        football_bets = scan_value_bets(
            odds_api_key=ODDS_API_KEY, leagues=FOOTBALL_LEAGUES,
            days_ahead=DAYS_AHEAD, min_edge=MIN_EDGE_WATCH,
            bookmaker=BOOKMAKER, bankroll=BANKROLL,
        )
        for b in football_bets:
            b.setdefault("sport", "football")

    with st.spinner("🎾  Escaneando tenis..."):
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

    # ── Clasificar apuestas ──────────────────────────────────────────────────
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

    # ── Métricas ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="metrics">
        <div class="metric"><div class="metric-val verde">{len(conviction)}</div><div class="metric-lbl">🎯 Alta Convicción</div></div>
        <div class="metric"><div class="metric-val amarillo">{len(high_edge)}</div><div class="metric-lbl">⚡ Alto Edge</div></div>
        <div class="metric"><div class="metric-val blanco">{len(watch)}</div><div class="metric-lbl">👁 Vigilancia</div></div>
        <div class="metric"><div class="metric-val oro">{len(wc_proj)}</div><div class="metric-lbl">🏆 Partidos Mundial</div></div>
        <div class="metric"><div class="metric-val verde">€{total_kelly:.0f}</div><div class="metric-lbl">Kelly Total</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Función render secciones de apuestas ─────────────────────────────────
    def render_section(bets, css, badge_css, badge_text, label, desc):
        st.markdown(f"""
        <div class="section-header">
            <span class="section-badge {badge_css}">{badge_text}</span>
            <span class="section-label">{label}</span>
            <span class="section-desc">{desc}</span>
        </div>
        """, unsafe_allow_html=True)
        if not bets:
            st.markdown('<div class="empty">Sin apuestas en esta categoría hoy</div>', unsafe_allow_html=True)
            return
        cards = ""
        for b in bets:
            dt    = b["kickoff"]
            fecha = f"{dt[5:10]} · {dt[11:16]}" if len(dt) > 10 else dt
            sport = b.get("sport", "football")
            icon  = "🎾" if sport == "tennis" else ("🏆" if sport == "world_cup" else "⚽")
            kelly_str = f"€{b['kelly']:.2f}" if b["kelly"] > 0 else "—"
            breakeven = round(100 / b["odds"], 1)
            cards += f"""
            <div class="bet {css}">
                <div>
                    <div class="bet-league">{icon} {b['league']}</div>
                    <div class="bet-match">{b['match']}</div>
                    <span class="bet-market-pill {css}">{b['market']}</span>
                    <div class="bet-stats-row">
                        <span class="bet-stat">Modelo: <span>{b['model']:.1f}%</span></span>
                        <span class="bet-stat">Break-even: <span>{breakeven}%</span></span>
                        <span class="bet-stat">Impl: <span>{b['implied']:.1f}%</span></span>
                    </div>
                    <div class="bet-date">📅 {fecha}</div>
                </div>
                <div class="bet-right">
                    <div class="bet-odds {css}">{b['odds']}</div>
                    <div class="bet-edge {css}">▲ +{b['edge']:.1f}% edge</div>
                    <div class="bet-ev">EV/10€: +{b['ev_10']:.2f}€</div>
                    <div class="bet-kelly">Kelly {kelly_str}</div>
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
    <div class="section-header">
        <span class="section-badge mundial">🏆 MUNDIAL 2026</span>
        <span class="section-label">PROYECCIONES — TODOS LOS PARTIDOS</span>
        <span class="section-desc">Modelo: Pinnacle sharp sin margen · Cuotas: Winamax FR</span>
    </div>
    """, unsafe_allow_html=True)

    if not wc_proj:
        st.markdown('<div class="empty">Sin partidos del Mundial disponibles esta semana</div>',
                    unsafe_allow_html=True)
    else:
        # ── TOP 5 Mejor relación seguridad / cuota ──────────────────────────
        st.markdown("""
        <div style="font-family:'Bebas Neue',sans-serif; font-size:1rem; color:#c9a84c;
                    letter-spacing:3px; margin:0.5rem 0 0.8rem;">
            🥇 TOP 5 — MEJOR RELACIÓN SEGURIDAD / CUOTA
        </div>
        <div style="font-family:'Barlow',sans-serif; font-size:0.72rem; color:#607080; margin-bottom:14px;">
            Ordenado por menor margen negativo en apuesta DNB · El favorito tiene empate como "red de seguridad"
        </div>
        """, unsafe_allow_html=True)

        top5 = sorted(wc_proj, key=lambda x: x["gap_dnb"], reverse=True)[:5]
        medal_css = ["gold", "silver", "bronze", "norm", "norm"]
        medal_sym = ["🥇", "🥈", "🥉", "4", "5"]

        top5_html = ""
        for i, p in enumerate(top5):
            mc   = medal_css[i]
            sym  = medal_sym[i]
            # color del margen DNB
            if p["gap_dnb"] >= -1.5:
                mg_css = "green"
            elif p["gap_dnb"] >= -3.0:
                mg_css = "yellow"
            else:
                mg_css = "grey"

            margin_str = f"{p['gap_dnb']:+.1f}%"
            fecha_str  = p["kickoff"].replace("2026-", "").replace("-", "/")

            top5_html += f"""
            <div class="top5-row {mc}">
                <div class="top5-num {mc}">{sym}</div>
                <div>
                    <div class="top5-match">{p['home']} vs {p['away']}</div>
                    <div class="top5-date">📅 {fecha_str}</div>
                </div>
                <div class="top5-cell">
                    <div class="top5-lbl">Favorito</div>
                    <div class="top5-val gold">{p['fav']}</div>
                    <div class="top5-sub">{p['fav_prob']}% prob</div>
                </div>
                <div class="top5-cell">
                    <div class="top5-lbl">Victoria @</div>
                    <div class="top5-val">{p['fav_odds']}</div>
                    <div class="top5-sub">break-ev {round(100/p['fav_odds'],1)}%</div>
                </div>
                <div class="top5-cell">
                    <div class="top5-lbl">DNB @</div>
                    <div class="top5-val">{p['fav_dnb_odds']}</div>
                    <div class="top5-sub">{p['fav_dnb_prob']}% prob</div>
                </div>
                <div class="top5-cell">
                    <div class="top5-lbl">Margen DNB</div>
                    <div class="top5-val {mg_css}">{margin_str}</div>
                    <div class="top5-sub">cuota vs prob</div>
                </div>
            </div>"""

        st.markdown(top5_html, unsafe_allow_html=True)

        # ── Tabla completa ───────────────────────────────────────────────────
        st.markdown("""
        <div style="font-family:'Bebas Neue',sans-serif; font-size:1rem; color:#c9a84c;
                    letter-spacing:3px; margin:1.8rem 0 0.8rem;">
            📋 CUADRO COMPLETO — TODOS LOS PARTIDOS
        </div>
        """, unsafe_allow_html=True)

        def prob_class(p):
            if p >= 65: return "prob-hi"
            if p >= 50: return "prob-med"
            return "prob-lo"

        def margin_class(m):
            if m >= -1.5: return "margin-ok"
            if m >= -3.0: return "margin-mid"
            return "margin-bad"

        rows_html = ""
        for p in wc_proj:
            fecha_str = p["kickoff"].replace("2026-", "").replace("-", "/")
            pc_h = prob_class(p["home_prob"])
            pc_a = prob_class(p["away_prob"])
            mc_w = margin_class(p["gap_win"])
            mc_d = margin_class(p["gap_dnb"])
            show_dnb = p["fav_dnb_odds"] >= 1.05

            dnb_cell = (
                f'<span class="dnb-pill">{p["fav_dnb_odds"]}</span>'
                f'<div style="font-size:0.62rem;color:#607080;margin-top:2px;">{p["fav_dnb_prob"]}%</div>'
            ) if show_dnb else "—"

            rows_html += f"""
            <tr>
                <td style="color:#607080;font-size:0.7rem;white-space:nowrap;">{fecha_str}</td>
                <td>{p['home']} vs {p['away']}</td>
                <td><span class="{pc_h}">{p['home_prob']}%</span><br><span style="color:#607080;font-size:0.65rem;">@ {p['home_odds']}</span></td>
                <td><span style="color:#a0b4c8;">{p['draw_prob']}%</span><br><span style="color:#607080;font-size:0.65rem;">@ {p['draw_odds']}</span></td>
                <td><span class="{pc_a}">{p['away_prob']}%</span><br><span style="color:#607080;font-size:0.65rem;">@ {p['away_odds']}</span></td>
                <td><span class="fav-pill">{p['fav']}</span></td>
                <td>{dnb_cell}</td>
                <td><span class="{mc_w}">{p['gap_win']:+.1f}%</span></td>
                <td><span class="{mc_d}">{p['gap_dnb']:+.1f}%</span></td>
            </tr>"""

        table_html = f"""
        <div class="wc-table-wrap">
        <table class="wc-table">
            <thead>
                <tr>
                    <th>Fecha</th>
                    <th>Partido</th>
                    <th>Local</th>
                    <th>Empate</th>
                    <th>Visitante</th>
                    <th>Favorito</th>
                    <th>DNB @cuota</th>
                    <th>Margen Vic.</th>
                    <th>Margen DNB</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        </div>
        <div class="wc-note-box">
            <span>🔑 <b style="color:#c9a84c">Margen</b> = prob. modelo − % break-even (cuanto menos negativo, mejor precio)</span>
            <span>🛡 <b style="color:#60c0ff">DNB</b> = Draw No Bet (empate devuelve la apuesta)</span>
            <span><b style="color:#4cdb82">Verde</b> ≥ −1.5% · <b style="color:#ffd166">Amarillo</b> ≥ −3% · Gris peor</span>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)

    # ── Export CSV ───────────────────────────────────────────────────────────
    if all_bets:
        st.markdown("<br>", unsafe_allow_html=True)
        df = pd.DataFrame([{
            "Liga": b["league"], "Partido": b["match"],
            "Fecha": b["kickoff"], "Apuesta": b["market"],
            "Cuota": b["odds"], "Modelo%": b["model"],
            "Edge%": b["edge"], "Kelly€": b["kelly"],
            "Veredicto": b["verdict"]
        } for b in all_bets])
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "↓ Descargar CSV completo",
            csv,
            f"value_bets_{now.strftime('%Y%m%d')}.csv",
            "text/csv",
        )

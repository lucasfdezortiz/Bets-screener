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

.metrics {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 1.8rem;
}
.metric {
    background: #1a2e45;
    border: 1px solid #2a4060;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
}
.metric-val {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.4rem;
    color: #c9a84c;
    line-height: 1;
}
.metric-val.blanco  { color: #ffffff; }
.metric-val.amarillo{ color: #ffd166; }
.metric-val.verde   { color: #4cdb82; }
.metric-val.oro     { color: #c9a84c; }
.metric-lbl {
    font-family: 'Barlow', sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    color: #a0b4c8;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 6px;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 1.8rem 0 1rem;
    padding-bottom: 0.7rem;
    border-bottom: 2px solid #2a4060;
}
.section-badge {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.8rem;
    letter-spacing: 2px;
    padding: 4px 12px;
    border-radius: 5px;
}
.section-badge.conviction { background: #4cdb82; color: #0d1b2a; }
.section-badge.high       { background: #ffd166; color: #0d1b2a; }
.section-badge.watch      { background: transparent; color: #60c0ff; border: 1px solid #60c0ff; }
.section-badge.mundial    { background: #c9a84c; color: #0d1b2a; }
.section-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    color: #ffffff;
    letter-spacing: 2px;
}
.section-desc {
    font-family: 'Barlow', sans-serif;
    font-size: 0.72rem;
    color: #a0b4c8;
    margin-left: auto;
}

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
.bet.conviction { background: #0d2a1a; border: 1px solid #2a6040; border-left: 5px solid #4cdb82; }
.bet.high       { background: #1a2a0d; border: 1px solid #4a4020; border-left: 5px solid #ffd166; }
.bet.watch      { background: #0d1a2a; border: 1px solid #1a3050; border-left: 5px solid #60c0ff; opacity: 0.85; }

.bet-league { font-family:'Barlow',sans-serif; font-size:0.72rem; font-weight:700; color:#a0b4c8; text-transform:uppercase; letter-spacing:2px; margin-bottom:5px; }
.bet-match  { font-family:'Bebas Neue',sans-serif; font-size:1.4rem; color:#ffffff; letter-spacing:1px; margin-bottom:8px; line-height:1.1; }
.bet-market-pill { display:inline-block; border-radius:20px; padding:4px 14px; font-family:'Barlow',sans-serif; font-size:0.8rem; font-weight:600; }
.bet-market-pill.conviction { background:#0d1b2a; border:1px solid #4cdb82; color:#4cdb82; }
.bet-market-pill.high       { background:#0d1b2a; border:1px solid #ffd166; color:#ffd166; }
.bet-market-pill.watch      { background:#0d1b2a; border:1px solid #60c0ff; color:#60c0ff; }
.bet-stats-row { display:flex; gap:12px; margin-top:8px; flex-wrap:wrap; }
.bet-stat      { font-family:'Barlow',sans-serif; font-size:0.7rem; color:#a0b4c8; }
.bet-stat span { color:#ffffff; font-weight:600; }
.bet-date      { font-family:'Barlow',sans-serif; font-size:0.72rem; color:#a0b4c8; margin-top:6px; }
.bet-right     { text-align:right; min-width:130px; }
.bet-odds      { font-family:'Bebas Neue',sans-serif; font-size:2.8rem; line-height:1; }
.bet-odds.conviction { color:#4cdb82; }
.bet-odds.high       { color:#ffd166; }
.bet-odds.watch      { color:#60c0ff; }
.bet-edge      { font-family:'Barlow',sans-serif; font-size:0.8rem; font-weight:700; margin-top:4px; }
.bet-edge.conviction { color:#4cdb82; }
.bet-edge.high       { color:#ffd166; }
.bet-edge.watch      { color:#60c0ff; }
.bet-ev   { font-family:'Barlow',sans-serif; font-size:0.72rem; color:#a0b4c8; margin-top:3px; }
.bet-kelly{ font-family:'Barlow',sans-serif; font-size:0.78rem; font-weight:700; color:#ffffff; margin-top:6px; background:#0d1b2a; border:1px solid #2a4060; padding:3px 10px; border-radius:5px; display:inline-block; }

/* ── Tarjetas de proyecciones Mundial ── */
.wc-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 14px;
    margin-top: 1rem;
}
.wc-card {
    background: #0f2035;
    border: 1px solid #2a4060;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    position: relative;
    overflow: hidden;
}
.wc-card.top3  { border-left: 4px solid #c9a84c; }
.wc-card.safe  { border-left: 4px solid #4cdb82; }
.wc-card.mid   { border-left: 4px solid #60c0ff; }
.wc-card.risky { border-left: 4px solid #a0b4c8; }

.wc-date  { font-family:'Barlow',sans-serif; font-size:0.68rem; font-weight:600; color:#a0b4c8; letter-spacing:2px; text-transform:uppercase; margin-bottom:4px; }
.wc-match { font-family:'Bebas Neue',sans-serif; font-size:1.35rem; color:#ffffff; letter-spacing:1px; line-height:1.1; margin-bottom:10px; }

.wc-probs { display:flex; gap:6px; margin-bottom:10px; }
.wc-prob-box {
    flex:1; text-align:center; background:#0d1b2a; border-radius:8px; padding:6px 4px;
    border: 1px solid #1e3550;
}
.wc-prob-box.winner { border-color:#c9a84c; background:#1a2a10; }
.wc-prob-lbl { font-family:'Barlow',sans-serif; font-size:0.6rem; color:#a0b4c8; text-transform:uppercase; letter-spacing:1px; }
.wc-prob-val { font-family:'Bebas Neue',sans-serif; font-size:1.4rem; color:#ffffff; line-height:1.1; }
.wc-prob-val.gold   { color:#c9a84c; }
.wc-prob-val.green  { color:#4cdb82; }
.wc-prob-odds { font-family:'Barlow',sans-serif; font-size:0.65rem; color:#607080; }

.wc-rec {
    background: #0d2030;
    border: 1px solid #2a5070;
    border-radius: 8px;
    padding: 8px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 6px;
}
.wc-rec-label { font-family:'Barlow',sans-serif; font-size:0.72rem; font-weight:700; color:#a0b4c8; }
.wc-rec-val   { font-family:'Bebas Neue',sans-serif; font-size:1.1rem; color:#c9a84c; }
.wc-margin-badge {
    display:inline-block; font-family:'Barlow',sans-serif; font-size:0.68rem; font-weight:700;
    padding: 2px 8px; border-radius:4px; margin-left: 6px;
}
.wc-margin-badge.neg-low  { background:#1a2e1a; color:#4cdb82; border:1px solid #4cdb82; }
.wc-margin-badge.neg-mid  { background:#1a2510; color:#ffd166; border:1px solid #ffd166; }
.wc-margin-badge.neg-high { background:#1a1a2e; color:#a0b4c8; border:1px solid #2a4060; }

.wc-note { font-family:'Barlow',sans-serif; font-size:0.65rem; color:#607080; margin-top:6px; text-align:right; }

.empty {
    text-align:center; padding:2rem; border:1px dashed #2a4060; border-radius:10px;
    font-family:'Barlow',sans-serif; font-size:0.85rem; color:#a0b4c8;
    letter-spacing:2px; text-transform:uppercase;
}

div[data-testid="stButton"] > button {
    background: #c9a84c !important; color: #0d1b2a !important;
    font-family: 'Bebas Neue', sans-serif !important; font-size: 1.2rem !important;
    letter-spacing: 5px !important; border: none !important;
    border-radius: 8px !important; padding: 0.8rem !important; width: 100% !important;
}
div[data-testid="stButton"] > button:hover { opacity: 0.85 !important; }
.stDownloadButton > button {
    background: transparent !important; color: #c9a84c !important;
    border: 1px solid #2a4060 !important; font-family: 'Barlow', sans-serif !important;
    font-size: 0.8rem !important;
}
</style>
""", unsafe_allow_html=True)

now = datetime.now()
st.markdown(f"""
<div class="header">
    <div class="header-eyebrow">⚽ Fútbol · 🎾 Tenis · 🏆 Mundial 2026 · Winamax FR</div>
    <div class="header-title">Value Bets <span>Scanner</span></div>
    <div class="header-info">{now.strftime('%A %d %B %Y')} &nbsp;·&nbsp; Bankroll €{BANKROLL} &nbsp;·&nbsp; Edge mínimo {MIN_EDGE_WATCH}%</div>
</div>
""", unsafe_allow_html=True)

if st.button("🔍  ESCANEAR HOY"):
    import sys
    sys.path.insert(0, "/mount/src/bets-screener")
    from modules.scanner            import scan_value_bets
    from modules.tennis_scanner     import scan_tennis_value_bets
    from modules.world_cup_scanner  import scan_world_cup_value_bets, get_world_cup_projections

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
        wc_projections = get_world_cup_projections(
            odds_api_key=ODDS_API_KEY, days_ahead=7,
        )

    all_bets = football_bets + tennis_bets + world_cup_bets

    # ── Clasificar ─────────────────────────────────────────────────────────
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
        if b not in conviction
        and b not in high_edge
        and b["edge"] >= MIN_EDGE_WATCH
        and b["verdict"] in ("VALUE BET", "MARGINAL")
        and b["odds"] <= 3.00
    ]
    watch.sort(key=lambda x: x["edge"], reverse=True)

    total_kelly = sum(b["kelly"] for b in conviction)
    wc_count    = len([b for b in all_bets if b.get("sport") == "world_cup"])

    # ── Métricas ────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="metrics">
        <div class="metric">
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
            <div class="metric-val oro">{len(wc_projections)}</div>
            <div class="metric-lbl">🏆 Partidos Mundial</div>
        </div>
        <div class="metric">
            <div class="metric-val verde">€{total_kelly:.0f}</div>
            <div class="metric-lbl">Kelly Convicción</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Función render secciones de apuestas ───────────────────────────────
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
            dt        = b["kickoff"]
            fecha     = f"{dt[5:10]} · {dt[11:16]}" if len(dt) > 10 else dt
            sport     = b.get("sport", "football")
            if sport == "tennis":
                icon = "🎾"
            elif sport == "world_cup":
                icon = "🏆"
            else:
                icon = "⚽"
            kelly_str  = f"€{b['kelly']:.2f}" if b["kelly"] > 0 else "—"
            breakeven  = round(100 / b["odds"], 1)

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
            </div>
            """
        st.markdown(cards, unsafe_allow_html=True)

    render_section(
        conviction, "conviction", "conviction",
        "🎯 ALTA CONVICCIÓN",
        f"{len(conviction)} apuestas — APOSTAR FUERTE",
        f"Cuota ≤ {MAX_ODDS_CONVICTION} · Prob ≥ {MIN_MODEL_PROB}% · Edge ≥ {MIN_EDGE_CONVICTION}%"
    )
    render_section(
        high_edge, "high", "high",
        "⚡ ALTO EDGE",
        f"{len(high_edge)} apuestas — Apostar moderado",
        f"Edge ≥ {MIN_EDGE_CONVICTION}% · Cualquier cuota"
    )
    render_section(
        watch, "watch", "watch",
        "👁 VIGILANCIA",
        f"{len(watch)} apuestas — Solo seguimiento",
        f"Edge {MIN_EDGE_WATCH}-{MIN_EDGE_CONVICTION}% · Cuota ≤ 3.00"
    )

    # ── Sección: PROYECCIONES MUNDIAL 2026 ─────────────────────────────────
    st.markdown("""
    <div class="section-header">
        <span class="section-badge mundial">🏆 MUNDIAL</span>
        <span class="section-label">MUNDIAL 2026 — PRONÓSTICOS</span>
        <span class="section-desc">Probabilidades Pinnacle (sharp) · Modelo Pinnacle sin margen · Winamax cuotas</span>
    </div>
    """, unsafe_allow_html=True)

    if not wc_projections:
        st.markdown('<div class="empty">Sin partidos del Mundial disponibles en los próximos 7 días</div>', unsafe_allow_html=True)
    else:
        # Leyenda
        st.markdown("""
        <div style="font-family:'Barlow',sans-serif; font-size:0.72rem; color:#607080; margin-bottom:12px; display:flex; gap:20px; flex-wrap:wrap;">
            <span>🔑 <b style="color:#c9a84c">Margen</b> = prob. modelo − % mínimo para no perder &nbsp;|&nbsp;
            <b style="color:#4cdb82">DNB</b> = empate anula apuesta &nbsp;|&nbsp;
            Cuotas: <b style="color:#fff">Winamax FR</b> &nbsp;|&nbsp;
            Modelo: <b style="color:#fff">Pinnacle sin margen</b></span>
        </div>
        """, unsafe_allow_html=True)

        cards_html = '<div class="wc-grid">'
        for i, p in enumerate(wc_projections):
            # Clase visual según probabilidad favorito
            if i < 3:
                card_css = "top3"
            elif p["fav_prob"] >= 65:
                card_css = "safe"
            elif p["fav_prob"] >= 50:
                card_css = "mid"
            else:
                card_css = "risky"

            # Identificar qué columna es el favorito
            if p["fav"] == p["home"]:
                h_winner, a_winner, d_winner = "winner", "", ""
                h_color, a_color = "gold", ""
            else:
                h_winner, a_winner, d_winner = "", "winner", ""
                h_color, a_color = "", "gold"

            # Badge del margen DNB
            if p["gap_dnb"] >= -1.5:
                badge_css, badge_txt = "neg-low", f"{p['gap_dnb']:+.1f}%"
            elif p["gap_dnb"] >= -3.0:
                badge_css, badge_txt = "neg-mid", f"{p['gap_dnb']:+.1f}%"
            else:
                badge_css, badge_txt = "neg-high", f"{p['gap_dnb']:+.1f}%"

            # No mostrar DNB si la cuota es casi 1.0 (inútil)
            show_dnb = p["fav_dnb_odds"] >= 1.05

            fecha_display = p["kickoff"].replace("-", "/")

            cards_html += f"""
            <div class="wc-card {card_css}">
                <div class="wc-date">📅 {fecha_display}</div>
                <div class="wc-match">{p['home']} vs {p['away']}</div>
                <div class="wc-probs">
                    <div class="wc-prob-box {h_winner}">
                        <div class="wc-prob-lbl">{p['home'][:10]}</div>
                        <div class="wc-prob-val {h_color}">{p['home_prob']}%</div>
                        <div class="wc-prob-odds">@ {p['home_odds']}</div>
                    </div>
                    <div class="wc-prob-box">
                        <div class="wc-prob-lbl">Empate</div>
                        <div class="wc-prob-val">{p['draw_prob']}%</div>
                        <div class="wc-prob-odds">@ {p['draw_odds']}</div>
                    </div>
                    <div class="wc-prob-box {a_winner}">
                        <div class="wc-prob-lbl">{p['away'][:10]}</div>
                        <div class="wc-prob-val {a_color}">{p['away_prob']}%</div>
                        <div class="wc-prob-odds">@ {p['away_odds']}</div>
                    </div>
                </div>
            """

            if show_dnb:
                cards_html += f"""
                <div class="wc-rec">
                    <div>
                        <span class="wc-rec-label">🛡 {p['fav']} DNB</span>
                        <span class="wc-margin-badge {badge_css}">{badge_txt}</span>
                    </div>
                    <div style="text-align:right;">
                        <span class="wc-rec-val">@ {p['fav_dnb_odds']}</span>
                        <div style="font-family:'Barlow',sans-serif;font-size:0.65rem;color:#607080;">Prob: {p['fav_dnb_prob']}%</div>
                    </div>
                </div>
                """

            cards_html += f"""
                <div class="wc-note">Margen victoria directa: {p['gap_win']:+.1f}%</div>
            </div>
            """

        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)

    # ── Export CSV ──────────────────────────────────────────────────────────
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
            "text/csv"
        )

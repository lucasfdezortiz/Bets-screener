import streamlit as st
import pandas as pd
from datetime import datetime

ODDS_API_KEY = "2e0cc7717f96a25817a3c781429437b8"
BANKROLL = 200.0
MIN_EDGE = 3.0
DAYS_AHEAD = 2
BOOKMAKER = "winamax_fr"

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
    grid-template-columns: repeat(4, 1fr);
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
.metric-val.blanco { color: #ffffff; }
.metric-val.amarillo { color: #ffd166; }
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
    background: #c9a84c;
    color: #0d1b2a;
}
.section-badge.marg {
    background: #2a3a00;
    color: #ffd166;
    border: 1px solid #4a5a00;
}
.section-label {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    color: #ffffff;
    letter-spacing: 2px;
}

.bet {
    background: #1a2e45;
    border: 1px solid #2a4060;
    border-left: 4px solid #c9a84c;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 2rem;
    align-items: center;
}
.bet.marg { border-left-color: #ffd166; }

.bet-league {
    font-family: 'Barlow', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    color: #a0b4c8;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 5px;
}
.bet-match {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem;
    color: #ffffff;
    letter-spacing: 1px;
    margin-bottom: 8px;
    line-height: 1.1;
}
.bet-market-pill {
    display: inline-block;
    background: #0d1b2a;
    border: 1px solid #c9a84c;
    border-radius: 20px;
    padding: 4px 14px;
    font-family: 'Barlow', sans-serif;
    font-size: 0.8rem;
    font-weight: 600;
    color: #c9a84c;
}
.bet-market-pill.marg {
    border-color: #ffd166;
    color: #ffd166;
}
.bet-date {
    font-family: 'Barlow', sans-serif;
    font-size: 0.72rem;
    color: #a0b4c8;
    margin-top: 8px;
}

.bet-right { text-align: right; min-width: 120px; }
.bet-odds {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.8rem;
    color: #c9a84c;
    line-height: 1;
}
.bet-edge {
    font-family: 'Barlow', sans-serif;
    font-size: 0.8rem;
    font-weight: 700;
    color: #4cdb82;
    margin-top: 4px;
}
.bet-ev {
    font-family: 'Barlow', sans-serif;
    font-size: 0.72rem;
    color: #a0b4c8;
    margin-top: 3px;
}
.bet-kelly {
    font-family: 'Barlow', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    color: #ffffff;
    margin-top: 6px;
    background: #0d1b2a;
    border: 1px solid #2a4060;
    padding: 3px 10px;
    border-radius: 5px;
    display: inline-block;
}

.empty {
    text-align: center;
    padding: 3rem;
    border: 1px dashed #2a4060;
    border-radius: 10px;
    font-family: 'Barlow', sans-serif;
    font-size: 0.9rem;
    color: #a0b4c8;
    letter-spacing: 2px;
    text-transform: uppercase;
}

div[data-testid="stButton"] > button {
    background: #c9a84c !important;
    color: #0d1b2a !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.2rem !important;
    letter-spacing: 5px !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.8rem !important;
    width: 100% !important;
}
div[data-testid="stButton"] > button:hover { opacity: 0.85 !important; }

.stDownloadButton > button {
    background: transparent !important;
    color: #c9a84c !important;
    border: 1px solid #2a4060 !important;
    font-family: 'Barlow', sans-serif !important;
    font-size: 0.8rem !important;
}
</style>
""", unsafe_allow_html=True)

now = datetime.now()
st.markdown(f"""
<div class="header">
    <div class="header-eyebrow">⚽ Fútbol · 🎾 Tenis · Winamax FR</div>
    <div class="header-title">Value Bets <span>Scanner</span></div>
    <div class="header-info">{now.strftime('%A %d %B %Y')} &nbsp;·&nbsp; Bankroll €{BANKROLL} &nbsp;·&nbsp; Edge mínimo {MIN_EDGE}%</div>
</div>
""", unsafe_allow_html=True)

if st.button("⚽  ESCANEAR HOY"):
    import sys
    sys.path.insert(0, "/mount/src/bets-screener")
    from modules.scanner import scan_value_bets
    from modules.tennis_scanner import scan_tennis_value_bets

    with st.spinner("Escaneando fútbol..."):
        football_bets = scan_value_bets(
            odds_api_key=ODDS_API_KEY, leagues=FOOTBALL_LEAGUES,
            days_ahead=DAYS_AHEAD, min_edge=MIN_EDGE,
            bookmaker=BOOKMAKER, bankroll=BANKROLL,
        )
        for b in football_bets:
            b.setdefault("sport", "football")

    with st.spinner("Escaneando tenis..."):
        tennis_bets = scan_tennis_value_bets(
            odds_api_key=ODDS_API_KEY, days_ahead=DAYS_AHEAD,
            min_edge=MIN_EDGE, bankroll=BANKROLL,
        )

    all_bets = sorted(football_bets + tennis_bets, key=lambda x: x["edge"], reverse=True)

    if not all_bets:
        st.markdown(f'<div class="empty">Sin value bets hoy con edge ≥ {MIN_EDGE}%</div>', unsafe_allow_html=True)
    else:
        value = [b for b in all_bets if b["verdict"] == "VALUE BET"]
        marg  = [b for b in all_bets if b["verdict"] == "MARGINAL"]
        total_kelly = sum(b["kelly"] for b in value)

        st.markdown(f"""
        <div class="metrics">
            <div class="metric">
                <div class="metric-val">{len(value)}</div>
                <div class="metric-lbl">Value Bets</div>
            </div>
            <div class="metric">
                <div class="metric-val amarillo">{len(marg)}</div>
                <div class="metric-lbl">Marginales</div>
            </div>
            <div class="metric">
                <div class="metric-val">€{total_kelly:.0f}</div>
                <div class="metric-lbl">Kelly Total</div>
            </div>
            <div class="metric">
                <div class="metric-val blanco" style="font-size:1.6rem">{now.strftime('%H:%M')}</div>
                <div class="metric-lbl">Escaneado</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        def render_bets(bets, is_value):
            css = "" if is_value else "marg"
            badge = "VALUE BET" if is_value else "MARGINAL"
            label = f"{len(bets)} encontradas"
            st.markdown(f"""
            <div class="section-header">
                <span class="section-badge {css}">{badge}</span>
                <span class="section-label">{label}</span>
            </div>
            """, unsafe_allow_html=True)

            cards = ""
            for b in bets:
                dt = b["kickoff"]
                fecha = f"{dt[5:10]} · {dt[11:16]}" if len(dt) > 10 else dt
                icon = "🎾" if b.get("sport") == "tennis" else "⚽"
                kelly_str = f"€{b['kelly']:.2f}" if b["kelly"] > 0 else "—"
                cards += f"""
                <div class="bet {css}">
                    <div>
                        <div class="bet-league">{icon} {b['league']}</div>
                        <div class="bet-match">{b['match']}</div>
                        <span class="bet-market-pill {css}">{b['market']}</span>
                        <div class="bet-date">📅 {fecha}</div>
                    </div>
                    <div class="bet-right">
                        <div class="bet-odds">{b['odds']}</div>
                        <div class="bet-edge">▲ +{b['edge']:.1f}% edge</div>
                        <div class="bet-ev">EV/10€: +{b['ev_10']:.2f}€</div>
                        <div class="bet-kelly">Kelly {kelly_str}</div>
                    </div>
                </div>
                """
            st.markdown(cards, unsafe_allow_html=True)

        if value:
            render_bets(value, True)
        else:
            st.markdown('<div class="empty">Sin value bets con edge &gt; 5% hoy</div>', unsafe_allow_html=True)

        if marg:
            render_bets(marg, False)

        df = pd.DataFrame([{
            "Liga": b["league"], "Partido": b["match"],
            "Fecha": b["kickoff"], "Apuesta": b["market"],
            "Cuota": b["odds"], "Edge%": b["edge"],
            "Kelly€": b["kelly"], "Veredicto": b["verdict"]
        } for b in all_bets])
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("↓ Descargar CSV", csv,
            f"value_bets_{now.strftime('%Y%m%d')}.csv", "text/csv")
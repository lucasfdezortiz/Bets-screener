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

st.set_page_config(
    page_title="Value Bets Scanner",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Inter:wght@400;500&display=swap');

    .stApp { background: #0a0f0a; }

    .hero {
        background: linear-gradient(135deg, #0d1f0d 0%, #0a0f0a 50%, #0d1a0d 100%);
        border: 1px solid #1a3a1a;
        border-radius: 16px;
        padding: 2.5rem 2rem 2rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #00c853, #69f0ae, #00c853);
    }
    .hero-title {
        font-family: 'Oswald', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: 2px;
        margin: 0;
        text-transform: uppercase;
    }
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        color: #4caf50;
        font-size: 0.85rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-top: 0.3rem;
    }
    .hero-date {
        font-family: 'Inter', sans-serif;
        color: #555;
        font-size: 0.8rem;
        margin-top: 0.8rem;
    }

    .metric-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #0d1f0d;
        border: 1px solid #1a3a1a;
        border-radius: 12px;
        padding: 1.2rem 1rem;
        text-align: center;
    }
    .metric-value {
        font-family: 'Oswald', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #00c853;
        margin: 0;
    }
    .metric-label {
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 0.3rem;
    }

    .section-title {
        font-family: 'Oswald', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #ffffff;
        text-transform: uppercase;
        letter-spacing: 3px;
        padding: 0.5rem 0;
        border-bottom: 1px solid #1a3a1a;
        margin-bottom: 1rem;
    }
    .section-title.value { color: #00c853; }
    .section-title.marginal { color: #ffc107; }

    .bet-card {
        background: #0d1a0d;
        border: 1px solid #1a3a1a;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        display: grid;
        grid-template-columns: auto 1fr auto;
        gap: 1rem;
        align-items: center;
        transition: border-color 0.2s;
    }
    .bet-card:hover { border-color: #00c853; }
    .bet-card.marginal { border-color: #2a2000; }
    .bet-card.marginal:hover { border-color: #ffc107; }

    .bet-sport {
        font-size: 1.6rem;
        width: 40px;
        text-align: center;
    }
    .bet-main { flex: 1; }
    .bet-match {
        font-family: 'Oswald', sans-serif;
        font-size: 1rem;
        color: #ffffff;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .bet-meta {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        color: #555;
        margin-top: 3px;
    }
    .bet-market {
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #00c853;
        margin-top: 5px;
    }
    .bet-market.marginal { color: #ffc107; }

    .bet-stats { text-align: right; }
    .bet-odds {
        font-family: 'Oswald', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: #ffffff;
    }
    .bet-edge {
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        color: #00c853;
        margin-top: 2px;
    }
    .bet-edge.marginal { color: #ffc107; }
    .bet-kelly {
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        color: #555;
        margin-top: 2px;
    }

    .no-bets {
        text-align: center;
        padding: 3rem;
        color: #333;
        font-family: 'Oswald', sans-serif;
        font-size: 1rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        border: 1px dashed #1a3a1a;
        border-radius: 12px;
    }

    div[data-testid="stButton"] button {
        background: #00c853 !important;
        color: #000 !important;
        font-family: 'Oswald', sans-serif !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: 3px !important;
        text-transform: uppercase !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.8rem 2rem !important;
        width: 100% !important;
        cursor: pointer !important;
    }

    .stDownloadButton button {
        background: transparent !important;
        color: #00c853 !important;
        border: 1px solid #1a3a1a !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.8rem !important;
        letter-spacing: 1px !important;
    }

    .market-warning {
        background: #1a0a00;
        border: 1px solid #3a2000;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        color: #ffc107;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def render_hero():
    now = datetime.now().strftime("%A, %d %B %Y — %H:%M")
    st.markdown(f"""
    <div class="hero">
        <div class="hero-subtitle">⚽ Football + Tennis · Winamax FR</div>
        <div class="hero-title">Value Bets</div>
        <div class="hero-title" style="color:#00c853;font-size:2rem;">Scanner</div>
        <div class="hero-date">{now} · Bankroll €{BANKROLL} · Edge mín. {MIN_EDGE}%</div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(value, marg, total_kelly, hora):
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-value">{len(value)}</div>
            <div class="metric-label">Value Bets</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color:#ffc107">{len(marg)}</div>
            <div class="metric-label">Marginales</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">€{total_kelly:.0f}</div>
            <div class="metric-label">Kelly Total</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" style="color:#ffffff;font-size:1.4rem">{hora}</div>
            <div class="metric-label">Escaneado</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_bets(bets, is_value=True):
    css_class = "value" if is_value else "marginal"
    title = f"✓ Value Bets — {len(bets)} encontradas" if is_value else f"~ Marginales — {len(bets)} encontradas"
    st.markdown(f'<div class="section-title {css_class}">{title}</div>', unsafe_allow_html=True)

    cards_html = ""
    for b in bets:
        dt = b["kickoff"]
        fecha = f"{dt[5:10]} {dt[11:16]}" if len(dt) > 10 else dt
        icon = "🎾" if b.get("sport") == "tennis" else "⚽"
        edge_str = f"+{b['edge']:.1f}% edge"
        kelly_str = f"Kelly: €{b['kelly']:.2f}" if b["kelly"] > 0 else "Kelly: —"
        ev_str = f"EV/10€: +{b['ev_10']:.2f}€"
        card_class = "" if is_value else "marginal"
        market_class = "" if is_value else "marginal"
        edge_class = "" if is_value else "marginal"

        cards_html += f"""
        <div class="bet-card {card_class}">
            <div class="bet-sport">{icon}</div>
            <div class="bet-main">
                <div class="bet-match">{b['match']}</div>
                <div class="bet-meta">{b['league']} · {fecha}</div>
                <div class="bet-market {market_class}">{b['market']}</div>
            </div>
            <div class="bet-stats">
                <div class="bet-odds">{b['odds']}</div>
                <div class="bet-edge {edge_class}">{edge_str}</div>
                <div class="bet-kelly">{ev_str} · {kelly_str}</div>
            </div>
        </div>
        """
    st.markdown(cards_html, unsafe_allow_html=True)


render_hero()

if st.button("ESCANEAR HOY"):
    import sys
    sys.path.insert(0, "/mount/src/bets-screener")

    from modules.scanner import scan_value_bets
    from modules.tennis_scanner import scan_tennis_value_bets

    with st.spinner("Escaneando fútbol..."):
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

    with st.spinner("Escaneando tenis..."):
        tennis_bets = scan_tennis_value_bets(
            odds_api_key=ODDS_API_KEY,
            days_ahead=DAYS_AHEAD,
            min_edge=MIN_EDGE,
            bankroll=BANKROLL,
        )

    all_bets = sorted(football_bets + tennis_bets, key=lambda x: x["edge"], reverse=True)

    if not all_bets:
        st.markdown(f'<div class="no-bets">Sin value bets hoy con edge ≥ {MIN_EDGE}%</div>', unsafe_allow_html=True)
    else:
        value = [b for b in all_bets if b["verdict"] == "VALUE BET"]
        marg = [b for b in all_bets if b["verdict"] == "MARGINAL"]

        render_metrics(value, marg, sum(b["kelly"] for b in value), datetime.now().strftime("%H:%M"))

        if value:
            render_bets(value, is_value=True)
        else:
            st.markdown('<div class="no-bets">Sin value bets con edge &gt; 5% hoy</div>', unsafe_allow_html=True)

        if marg:
            st.markdown("<br>", unsafe_allow_html=True)
            render_bets(marg, is_value=False)

        df = pd.DataFrame([{
            "Liga": b["league"], "Partido": b["match"],
            "Fecha": b["kickoff"], "Apuesta": b["market"],
            "Cuota": b["odds"], "Edge": b["edge"],
            "Kelly": b["kelly"], "Veredicto": b["verdict"]
        } for b in all_bets])

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "↓ Descargar CSV",
            csv,
            f"value_bets_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
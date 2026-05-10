import streamlit as st
import sys
import io
from datetime import datetime

sys.path.insert(0, "/Users/lucasfdezortiz/Bets-screener")

from modules.scanner import scan_value_bets
from modules.tennis_scanner import scan_tennis_value_bets

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

st.title("⚽🎾 Value Bets Scanner")
st.caption(f"Bankroll: €{BANKROLL} · Edge mínimo: {MIN_EDGE}% · Target: Winamax FR")

if st.button("🔍 Escanear hoy", type="primary", use_container_width=True):
    with st.spinner("Escaneando fútbol y tenis..."):

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

        tennis_bets = scan_tennis_value_bets(
            odds_api_key=ODDS_API_KEY,
            days_ahead=DAYS_AHEAD,
            min_edge=MIN_EDGE,
            bankroll=BANKROLL,
        )

        all_bets = sorted(football_bets + tennis_bets, key=lambda x: x["edge"], reverse=True)

    if not all_bets:
        st.warning(f"Sin value bets hoy con edge ≥ {MIN_EDGE}%")
    else:
        value = [b for b in all_bets if b["verdict"] == "VALUE BET"]
        marg  = [b for b in all_bets if b["verdict"] == "MARGINAL"]

        # Resumen
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✅ Value Bets", len(value))
        col2.metric("🟡 Marginales", len(marg))
        col3.metric("💰 Kelly Total", f"€{sum(b['kelly'] for b in value):.2f}")
        col4.metric("🕐 Escaneado", datetime.now().strftime("%H:%M"))

        def render_table(bets, title, color):
            if not bets:
                return
            st.subheader(title)
            rows = []
            for b in bets:
                dt = b["kickoff"]
                fecha = f"{dt[5:10]} {dt[11:16]}" if len(dt) > 10 else dt
                sport_icon = "🎾" if b.get("sport") == "tennis" else "⚽"
                rows.append({
                    "Deporte": sport_icon,
                    "Liga": b["league"][:20],
                    "Partido": b["match"][:35],
                    "Fecha": fecha,
                    "Apuesta": b["market"][:25],
                    "Cuota": b["odds"],
                    "Impl%": f"{b['implied']:.1f}%",
                    "Modelo%": f"{b['model']:.1f}%",
                    "Edge": f"+{b['edge']:.1f}%",
                    "EV/10€": f"+{b['ev_10']:.2f}€",
                    "Kelly": f"{b['kelly']:.2f}€" if b["kelly"] > 0 else "—",
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

        render_table(value, f"✅ Value Bets — {len(value)} encontradas", "green")
        render_table(marg, f"🟡 Marginales — {len(marg)} encontradas", "yellow")

        # Botón exportar
        import pandas as pd
        df = pd.DataFrame([{
            "Liga": b["league"], "Partido": b["match"],
            "Fecha": b["kickoff"], "Apuesta": b["market"],
            "Cuota": b["odds"], "Edge": b["edge"],
            "Kelly": b["kelly"], "Veredicto": b["verdict"]
        } for b in all_bets])

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Descargar CSV",
            csv,
            f"value_bets_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
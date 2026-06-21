import streamlit as st
import pandas as pd
from datetime import datetime

ODDS_API_KEY        = "2e0cc7717f96a25817a3c781429437b8"
BANKROLL            = 200.0
DAYS_AHEAD          = 3
BOOKMAKER           = "winamax_fr"

# ── Filtros Convicción ───────────────────────────────────────────────────────
MIN_ODDS_CONV  = 1.50   # cuota mínima (evitar odds irrisorias)
MAX_ODDS_CONV  = 2.00   # cuota máxima (baja varianza)
MIN_PROB_CONV  = 60.0   # % mínimo del modelo
MIN_EDGE_CONV  = 5.0    # edge mínimo para convicción

# ── Filtros Value Bets generales ─────────────────────────────────────────────
MIN_EDGE_ALL   = 3.0    # edge mínimo para aparecer en el scanner general

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

# ════════════════════════════════════════════════════════════════════════════
# CSS — Tema Estadio Nocturno
# ════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;500;600;700;800&display=swap');

html, body, .stApp {
    background-color: #04080f !important;
    background-image:
        radial-gradient(ellipse 130% 55% at 50% -5%, rgba(15,90,35,0.30) 0%, transparent 60%),
        radial-gradient(ellipse 70% 35% at 10% 105%, rgba(5,30,70,0.35) 0%, transparent 55%),
        radial-gradient(ellipse 70% 35% at 90% 105%, rgba(5,30,70,0.35) 0%, transparent 55%);
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.2rem !important; max-width: 1400px !important; }

/* ── HEADER ── */
.vb-header {
    position: relative; overflow: hidden;
    border-radius: 16px; padding: 2.2rem 2.8rem;
    margin-bottom: 1.6rem;
    background: linear-gradient(135deg, #071528 0%, #091e18 50%, #071528 100%);
    border: 1px solid rgba(212,175,55,0.35);
    box-shadow: 0 0 80px rgba(15,90,35,0.2), 0 0 120px rgba(5,30,70,0.2),
                inset 0 1px 0 rgba(212,175,55,0.15);
}
.vb-header::before {
    content:''; position:absolute; inset:0;
    background: radial-gradient(ellipse 100% 70% at 50% 110%, rgba(15,110,45,0.25) 0%, transparent 55%);
    pointer-events:none;
}
.vb-header::after {
    content:''; position:absolute; inset:0;
    background-image: repeating-linear-gradient(
        90deg, transparent, transparent 59px,
        rgba(255,255,255,0.018) 59px, rgba(255,255,255,0.018) 60px
    );
    pointer-events:none;
}
.vb-eyebrow {
    font-family:'Barlow',sans-serif; font-size:0.7rem; font-weight:700;
    letter-spacing:5px; text-transform:uppercase; color:#d4af37;
    margin-bottom:0.4rem; position:relative; z-index:1;
}
.vb-title {
    font-family:'Bebas Neue',sans-serif; font-size:3.8rem; color:#fff;
    letter-spacing:6px; line-height:1; margin-bottom:0.5rem;
    position:relative; z-index:1;
    text-shadow: 0 0 50px rgba(212,175,55,0.25);
}
.vb-title span { color:#d4af37; text-shadow: 0 0 30px rgba(212,175,55,0.5); }
.vb-info {
    font-family:'Barlow',sans-serif; font-size:0.78rem; color:#5a7a95;
    position:relative; z-index:1;
}
.vb-info b { color:#d4af37; }
.vb-trophy {
    position:absolute; right:2.5rem; top:50%; transform:translateY(-50%);
    font-size:6rem; opacity:0.12; z-index:1;
    filter: drop-shadow(0 0 15px rgba(212,175,55,0.4));
}

/* ── MÉTRICAS ── */
.vb-metrics {
    display:flex; gap:10px; margin-bottom:1.6rem; flex-wrap:wrap;
}
.vb-metric {
    flex:1; min-width:100px;
    background:linear-gradient(145deg,#0c1c2e,#08121e);
    border:1px solid #162030; border-radius:12px;
    padding:1rem 0.8rem; text-align:center;
}
.vb-metric.em { border-color:rgba(212,175,55,0.25); }
.vm-val {
    font-family:'Bebas Neue',sans-serif;
    font-size:2.6rem; line-height:1;
}
.vm-val.g  { color:#3dd878; text-shadow:0 0 12px rgba(61,216,120,0.3); }
.vm-val.y  { color:#ffd166; text-shadow:0 0 12px rgba(255,209,102,0.3); }
.vm-val.w  { color:#e8f0f8; }
.vm-val.au { color:#d4af37; text-shadow:0 0 12px rgba(212,175,55,0.3); }
.vm-lbl {
    font-family:'Barlow',sans-serif; font-size:0.62rem; font-weight:700;
    color:#3a5a75; text-transform:uppercase; letter-spacing:2px; margin-top:5px;
}

/* ── SECTION HEADER ── */
.vb-section {
    display:flex; align-items:center; gap:12px;
    margin:2rem 0 1rem;
    padding-bottom:0.75rem;
    border-bottom:1px solid #0f1e2e;
}
.vb-badge {
    font-family:'Bebas Neue',sans-serif; font-size:0.75rem;
    letter-spacing:2px; padding:5px 14px; border-radius:6px; white-space:nowrap;
}
.vb-badge.conv { background:linear-gradient(90deg,#d4af37,#eecc44); color:#04080f; }
.vb-badge.all  { background:linear-gradient(90deg,#3dd878,#2ac864); color:#04080f; }
.vb-badge.wc   { background:linear-gradient(90deg,#c9a84c,#e0bc5a); color:#04080f; }
.vb-section-title {
    font-family:'Bebas Neue',sans-serif; font-size:1.15rem;
    color:#e8f0f8; letter-spacing:3px;
}
.vb-section-desc {
    font-family:'Barlow',sans-serif; font-size:0.7rem;
    color:#3a5a75; margin-left:auto; text-align:right;
}

/* ── TARJETAS DE APUESTAS ── */
.vb-card {
    border-radius:11px; padding:1.1rem 1.5rem; margin-bottom:9px;
    display:grid; grid-template-columns:1fr auto;
    gap:1.5rem; align-items:center;
}
.vb-card.conv {
    background:linear-gradient(135deg,#0d2215,#081a10);
    border:1px solid rgba(212,175,55,0.2); border-left:4px solid #d4af37;
    box-shadow:0 3px 20px rgba(212,175,55,0.06);
}
.vb-card.all {
    background:linear-gradient(135deg,#091825,#060e1a);
    border:1px solid #102030; border-left:4px solid #3dd878;
}
.vc-league { font-family:'Barlow',sans-serif; font-size:0.66rem; font-weight:700; color:#3a5a75; text-transform:uppercase; letter-spacing:2px; margin-bottom:4px; }
.vc-match  { font-family:'Bebas Neue',sans-serif; font-size:1.4rem; color:#fff; letter-spacing:1.5px; margin-bottom:7px; line-height:1.1; }
.vc-pill {
    display:inline-block; border-radius:20px; padding:3px 14px;
    font-family:'Barlow',sans-serif; font-size:0.78rem; font-weight:600;
}
.vc-pill.conv { background:rgba(212,175,55,0.1); border:1px solid rgba(212,175,55,0.35); color:#d4af37; }
.vc-pill.all  { background:rgba(61,216,120,0.08); border:1px solid rgba(61,216,120,0.3); color:#3dd878; }
.vc-stats { display:flex; gap:14px; margin-top:8px; flex-wrap:wrap; }
.vc-stat  { font-family:'Barlow',sans-serif; font-size:0.7rem; color:#3a5a75; }
.vc-stat span { color:#b0c8e0; font-weight:600; }
.vc-date  { font-family:'Barlow',sans-serif; font-size:0.68rem; color:#2a4a65; margin-top:6px; }
.vc-right { text-align:right; min-width:120px; }
.vc-odds  { font-family:'Bebas Neue',sans-serif; font-size:3rem; line-height:1; }
.vc-odds.conv { color:#d4af37; text-shadow:0 0 18px rgba(212,175,55,0.35); }
.vc-odds.all  { color:#3dd878; text-shadow:0 0 18px rgba(61,216,120,0.3); }
.vc-edge  { font-family:'Barlow',sans-serif; font-size:0.82rem; font-weight:800; margin-top:2px; }
.vc-edge.conv { color:#d4af37; }
.vc-edge.all  { color:#3dd878; }
.vc-ev    { font-family:'Barlow',sans-serif; font-size:0.68rem; color:#3a5a75; margin-top:2px; }
.vc-kelly { font-family:'Barlow',sans-serif; font-size:0.76rem; font-weight:700; color:#c8d8e8; margin-top:6px; background:rgba(255,255,255,0.04); border:1px solid #142030; padding:3px 10px; border-radius:6px; display:inline-block; }

/* ── INFO BOX ── */
.vb-info-box {
    background:rgba(96,192,255,0.04);
    border:1px solid rgba(96,192,255,0.15); border-radius:10px;
    padding:0.9rem 1.3rem; margin-bottom:1rem;
    font-family:'Barlow',sans-serif; font-size:0.76rem; color:#5a8aaa;
    line-height:1.6;
}
.vb-info-box b { color:#7ab0d0; }

/* ── VACÍO ── */
.vb-empty {
    text-align:center; padding:2.5rem;
    border:1px dashed #0f1e2e; border-radius:12px;
    font-family:'Barlow',sans-serif; font-size:0.8rem;
    color:#2a4a65; letter-spacing:3px; text-transform:uppercase;
}

/* ── TOP 5 MUNDIAL ── */
.t5-note {
    font-family:'Barlow',sans-serif; font-size:0.72rem; color:#3a5a75;
    margin-bottom:14px; padding:8px 14px;
    background:rgba(212,175,55,0.04); border-left:3px solid rgba(212,175,55,0.3);
    border-radius:0 6px 6px 0; line-height:1.5;
}
.t5-row {
    background:linear-gradient(135deg,#0a1828,#060e1c);
    border:1px solid #0f1e30; border-radius:11px;
    padding:0.95rem 1.4rem; margin-bottom:9px;
    display:grid;
    grid-template-columns:50px 1fr 120px 120px 120px 120px;
    align-items:center; gap:10px;
}
.t5-row.g1 { border-left:4px solid #d4af37; background:linear-gradient(135deg,#141206,#0c0e04); }
.t5-row.g2 { border-left:4px solid #9ca8b4; }
.t5-row.g3 { border-left:4px solid #8c5e22; }
.t5-row.gn { border-left:4px solid #142030; }
.t5-medal { font-size:2rem; text-align:center; line-height:1; }
.t5-match { font-family:'Bebas Neue',sans-serif; font-size:1.05rem; color:#e8f0f8; letter-spacing:1px; line-height:1.25; }
.t5-date  { font-family:'Barlow',sans-serif; font-size:0.65rem; color:#2a4a65; margin-top:3px; }
.t5-cell  { text-align:center; }
.t5-lbl   { font-family:'Barlow',sans-serif; font-size:0.58rem; font-weight:700; color:#2a4a65; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:4px; }
.t5-val   { font-family:'Bebas Neue',sans-serif; font-size:1.25rem; color:#e8f0f8; line-height:1; }
.t5-val.au { color:#d4af37; text-shadow:0 0 10px rgba(212,175,55,0.35); }
.t5-val.gn { color:#3dd878; }
.t5-val.ye { color:#ffd166; }
.t5-val.gr { color:#4a6a85; }
.t5-sub   { font-family:'Barlow',sans-serif; font-size:0.6rem; color:#2a4a65; margin-top:2px; }

/* ── TABLA COMPLETA MUNDIAL ── */
.wc-tbl-wrap { border-radius:12px; overflow:hidden; border:1px solid #0f1e30; box-shadow:0 8px 40px rgba(0,0,0,0.35); }
.wc-tbl { width:100%; border-collapse:collapse; }
.wc-tbl thead tr { background:#0a1828; border-bottom:2px solid rgba(212,175,55,0.15); }
.wc-tbl thead th {
    padding:11px 14px; font-family:'Barlow',sans-serif;
    font-size:0.62rem; font-weight:700; color:#2a4a65;
    text-transform:uppercase; letter-spacing:2px;
    text-align:center; white-space:nowrap;
}
.wc-tbl thead th:nth-child(1),
.wc-tbl thead th:nth-child(2) { text-align:left; }
.wc-tbl tbody tr { border-bottom:1px solid #080e18; transition:background 0.1s; }
.wc-tbl tbody tr:hover { background:rgba(212,175,55,0.03); }
.wc-tbl tbody tr:nth-child(even) { background:rgba(255,255,255,0.012); }
.wc-tbl td {
    padding:10px 14px; font-family:'Barlow',sans-serif;
    font-size:0.76rem; color:#6a8aa4; text-align:center; vertical-align:middle;
}
.wc-tbl td:nth-child(1) { text-align:left; color:#2a4a65; font-size:0.68rem; white-space:nowrap; }
.wc-tbl td:nth-child(2) { text-align:left; font-family:'Bebas Neue',sans-serif; font-size:0.92rem; color:#e0ecf8; letter-spacing:0.5px; }
.ph { color:#3dd878 !important; font-weight:700; }
.pm { color:#ffd166 !important; font-weight:700; }
.mk-ok  { color:#3dd878 !important; font-weight:700; font-size:0.76rem; }
.mk-mid { color:#ffd166 !important; font-weight:700; font-size:0.76rem; }
.mk-bad { color:#2a4a65; font-size:0.73rem; }
.fav-p { display:inline-block; padding:2px 9px; border-radius:5px; font-family:'Barlow',sans-serif; font-size:0.68rem; font-weight:700; background:rgba(212,175,55,0.08); color:#c9a030; border:1px solid rgba(212,175,55,0.25); }
.dnb-p { display:inline-block; padding:2px 8px; border-radius:5px; font-family:'Bebas Neue',sans-serif; font-size:0.78rem; background:rgba(96,192,255,0.06); color:#4aa8d8; border:1px solid rgba(96,192,255,0.2); }
.wc-legend {
    background:rgba(0,0,0,0.2); border-top:1px solid #080e18;
    padding:9px 16px; font-family:'Barlow',sans-serif;
    font-size:0.66rem; color:#2a4a65;
    display:flex; gap:20px; flex-wrap:wrap;
}

/* ── BOTÓN & DOWNLOAD ── */
div[data-testid="stButton"] > button {
    background:linear-gradient(135deg,#d4af37,#b8952a) !important;
    color:#04080f !important; font-family:'Bebas Neue',sans-serif !important;
    font-size:1.2rem !important; letter-spacing:6px !important;
    border:none !important; border-radius:10px !important;
    padding:0.85rem !important; width:100% !important;
    box-shadow:0 4px 24px rgba(212,175,55,0.2) !important;
}
div[data-testid="stButton"] > button:hover {
    opacity:0.88 !important; transform:translateY(-1px) !important;
}
.stDownloadButton > button {
    background:transparent !important; color:#3a5a75 !important;
    border:1px solid #0f1e30 !important; border-radius:8px !important;
    font-family:'Barlow',sans-serif !important; font-size:0.76rem !important;
}
.stDownloadButton > button:hover { color:#d4af37 !important; border-color:rgba(212,175,55,0.3) !important; }
</style>
""", unsafe_allow_html=True)


# ── HEADER ──────────────────────────────────────────────────────────────────
now = datetime.now()
st.markdown(f"""
<div class="vb-header">
    <div class="vb-trophy">🏆</div>
    <div class="vb-eyebrow">⚽ Ligas Europeas &nbsp;·&nbsp; 🎾 Tenis ATP/WTA &nbsp;·&nbsp; 🏆 Mundial 2026 &nbsp;·&nbsp; Winamax FR</div>
    <div class="vb-title">Value Bets <span>Scanner</span></div>
    <div class="vb-info">
        {now.strftime('%A %d %B %Y').capitalize()} &nbsp;&nbsp;|&nbsp;&nbsp;
        Bankroll <b>€{BANKROLL}</b> &nbsp;&nbsp;|&nbsp;&nbsp;
        Modelo: Poisson (fútbol) · Pinnacle sharp (tenis &amp; Mundial) &nbsp;&nbsp;|&nbsp;&nbsp;
        Target: <b>Winamax FR</b>
    </div>
</div>
""", unsafe_allow_html=True)


# ── BOTÓN ────────────────────────────────────────────────────────────────────
if st.button("🔍  ESCANEAR APUESTAS DE HOY"):
    import sys
    sys.path.insert(0, "/mount/src/bets-screener")
    from modules.scanner           import scan_value_bets
    from modules.tennis_scanner    import scan_tennis_value_bets
    from modules.world_cup_scanner import scan_world_cup_value_bets, get_world_cup_projections

    with st.spinner("⚽  Escaneando ligas de fútbol..."):
        football_bets = scan_value_bets(
            odds_api_key=ODDS_API_KEY, leagues=FOOTBALL_LEAGUES,
            days_ahead=DAYS_AHEAD, min_edge=MIN_EDGE_ALL,
            bookmaker=BOOKMAKER, bankroll=BANKROLL,
        )
        for b in football_bets:
            b.setdefault("sport", "football")

    with st.spinner("🎾  Escaneando tenis ATP/WTA..."):
        tennis_bets = scan_tennis_value_bets(
            odds_api_key=ODDS_API_KEY, days_ahead=DAYS_AHEAD,
            min_edge=MIN_EDGE_ALL, bankroll=BANKROLL,
        )

    with st.spinner("🏆  Escaneando Mundial 2026..."):
        world_cup_bets = scan_world_cup_value_bets(
            odds_api_key=ODDS_API_KEY, days_ahead=7,
            min_edge=MIN_EDGE_ALL, bankroll=BANKROLL,
        )
        wc_proj = get_world_cup_projections(odds_api_key=ODDS_API_KEY, days_ahead=7)

    all_bets = football_bets + tennis_bets + world_cup_bets
    all_bets.sort(key=lambda x: x["edge"], reverse=True)

    # ── Clasificar ───────────────────────────────────────────────────────────
    # CONVICCIÓN: cuota 1.50–2.00 + prob alta + edge alto
    conv = [
        b for b in all_bets
        if b["odds"] >= MIN_ODDS_CONV
        and b["odds"] <= MAX_ODDS_CONV
        and b["model"] >= MIN_PROB_CONV
        and b["edge"]  >= MIN_EDGE_CONV
    ]
    conv.sort(key=lambda x: x["edge"] * x["model"] / 100, reverse=True)

    # VALUE BETS: todo lo que tiene edge ≥ 3% (excluye ya listados en conv)
    value = [b for b in all_bets if b["edge"] >= MIN_EDGE_ALL and b not in conv]

    total_kelly = sum(b["kelly"] for b in conv)
    wc_value    = len([b for b in all_bets if b.get("sport") == "world_cup"])

    # ── MÉTRICAS ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="vb-metrics">
        <div class="vb-metric em">
            <div class="vm-val au">{len(conv)}</div>
            <div class="vm-lbl">🎯 Alta Convicción</div>
        </div>
        <div class="vb-metric">
            <div class="vm-val g">{len(value)}</div>
            <div class="vm-lbl">⚡ Value Bets</div>
        </div>
        <div class="vb-metric">
            <div class="vm-val w">{len(all_bets)}</div>
            <div class="vm-lbl">📊 Total con Edge</div>
        </div>
        <div class="vb-metric">
            <div class="vm-val au">{len(wc_proj)}</div>
            <div class="vm-lbl">🏆 Partidos Mundial</div>
        </div>
        <div class="vb-metric em">
            <div class="vm-val g">€{total_kelly:.0f}</div>
            <div class="vm-lbl">Kelly Convicción</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # SCANNER 1 — ALTA CONVICCIÓN
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(f"""
    <div class="vb-section">
        <span class="vb-badge conv">🎯 SCANNER 1</span>
        <span class="vb-section-title">ALTA CONVICCIÓN — APOSTAR FUERTE</span>
        <span class="vb-section-desc">Cuota {MIN_ODDS_CONV}–{MAX_ODDS_CONV} · Prob ≥ {MIN_PROB_CONV}% · Edge ≥ {MIN_EDGE_CONV}% · Ordenado por conviction score</span>
    </div>
    """, unsafe_allow_html=True)

    if not conv:
        st.markdown('<div class="vb-empty">Sin apuestas de alta convicción hoy</div>', unsafe_allow_html=True)
    else:
        cards = ""
        for b in conv:
            dt    = b["kickoff"]
            fecha = f"{dt[5:10]}  ·  {dt[11:16]}" if len(dt) > 10 else dt
            sport = b.get("sport","football")
            icon  = "🎾" if sport=="tennis" else ("🏆" if sport=="world_cup" else "⚽")
            kelly = f"€{b['kelly']:.2f}" if b["kelly"]>0 else "—"
            be    = round(100/b["odds"],1)
            score = round(b["edge"] * b["model"] / 100, 1)
            cards += f"""
            <div class="vb-card conv">
                <div>
                    <div class="vc-league">{icon}&nbsp; {b['league']}</div>
                    <div class="vc-match">{b['match']}</div>
                    <span class="vc-pill conv">{b['market']}</span>
                    <div class="vc-stats">
                        <span class="vc-stat">Modelo: <span>{b['model']:.1f}%</span></span>
                        <span class="vc-stat">Break-even: <span>{be}%</span></span>
                        <span class="vc-stat">Impl. Winamax: <span>{b['implied']:.1f}%</span></span>
                        <span class="vc-stat">Conviction Score: <span>{score}</span></span>
                    </div>
                    <div class="vc-date">📅 {fecha}</div>
                </div>
                <div class="vc-right">
                    <div class="vc-odds conv">{b['odds']}</div>
                    <div class="vc-edge conv">▲ +{b['edge']:.1f}% edge</div>
                    <div class="vc-ev">EV / 10€ &nbsp;+{b['ev_10']:.2f}€</div>
                    <div class="vc-kelly">Kelly &nbsp;{kelly}</div>
                </div>
            </div>"""
        st.markdown(cards, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # SCANNER 2 — TODOS LOS VALUE BETS
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(f"""
    <div class="vb-section">
        <span class="vb-badge all">⚡ SCANNER 2</span>
        <span class="vb-section-title">TODOS LOS VALUE BETS — EDGE ≥ {MIN_EDGE_ALL}%</span>
        <span class="vb-section-desc">⚽ Ligas + 🎾 Tenis + 🏆 Mundial · Ordenado por edge · {len(value)} apuestas</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="vb-info-box">
        📌 <b>Mercados disponibles vía Winamax API:</b> 1X2 (victoria/empate/derrota) + DNB (empate apuesta no válida, derivado matemáticamente).
        Over/Under goles, córners, tarjetas y hándicap <b>no están disponibles</b> para Winamax en el proveedor de odds actual (The Odds API).
        El modelo de Poisson calcula probabilidades de Over/Under y BTTS internamente, pero Winamax no expone esas cuotas por esta vía.
    </div>
    """, unsafe_allow_html=True)

    if not value:
        st.markdown(f'<div class="vb-empty">Sin value bets adicionales con edge ≥ {MIN_EDGE_ALL}% hoy</div>',
                    unsafe_allow_html=True)
    else:
        cards2 = ""
        for b in value:
            dt    = b["kickoff"]
            fecha = f"{dt[5:10]}  ·  {dt[11:16]}" if len(dt) > 10 else dt
            sport = b.get("sport","football")
            icon  = "🎾" if sport=="tennis" else ("🏆" if sport=="world_cup" else "⚽")
            kelly = f"€{b['kelly']:.2f}" if b["kelly"]>0 else "—"
            be    = round(100/b["odds"],1)
            cards2 += f"""
            <div class="vb-card all">
                <div>
                    <div class="vc-league">{icon}&nbsp; {b['league']}</div>
                    <div class="vc-match">{b['match']}</div>
                    <span class="vc-pill all">{b['market']}</span>
                    <div class="vc-stats">
                        <span class="vc-stat">Modelo: <span>{b['model']:.1f}%</span></span>
                        <span class="vc-stat">Break-even: <span>{be}%</span></span>
                        <span class="vc-stat">Impl. Winamax: <span>{b['implied']:.1f}%</span></span>
                    </div>
                    <div class="vc-date">📅 {fecha}</div>
                </div>
                <div class="vc-right">
                    <div class="vc-odds all">{b['odds']}</div>
                    <div class="vc-edge all">▲ +{b['edge']:.1f}% edge</div>
                    <div class="vc-ev">EV / 10€ &nbsp;+{b['ev_10']:.2f}€</div>
                    <div class="vc-kelly">Kelly &nbsp;{kelly}</div>
                </div>
            </div>"""
        st.markdown(cards2, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════════════
    # MUNDIAL 2026 — TOP 5 + CUADRO COMPLETO
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class="vb-section" style="border-bottom-color:rgba(212,175,55,0.12);">
        <span class="vb-badge wc">🏆 MUNDIAL 2026</span>
        <span class="vb-section-title">PROYECCIONES — PRONÓSTICOS DE PARTIDOS</span>
        <span class="vb-section-desc">Modelo Pinnacle sharp sin margen · Cuotas y DNB: Winamax FR</span>
    </div>
    """, unsafe_allow_html=True)

    if not wc_proj:
        st.markdown('<div class="vb-empty">Sin partidos del Mundial disponibles</div>', unsafe_allow_html=True)
    else:
        # ── TOP 5 ────────────────────────────────────────────────────────────
        st.markdown("""
        <div style="font-family:'Bebas Neue',sans-serif;font-size:0.95rem;color:#d4af37;
                    letter-spacing:4px;margin:0.4rem 0 0.6rem;">
            🥇 TOP 5 — MEJOR RELACIÓN SEGURIDAD / CUOTA (DNB)
        </div>
        <div class="t5-note">
            Ordenado por menor margen negativo en apuesta DNB.
            <b style="color:#3dd878">Verde</b> ≤ −1.5% &nbsp;·&nbsp;
            <b style="color:#ffd166">Amarillo</b> ≤ −3% &nbsp;·&nbsp;
            Gris = precio más ajustado.
            DNB = empate devuelve la apuesta.
        </div>
        """, unsafe_allow_html=True)

        top5     = sorted(wc_proj, key=lambda x: x["gap_dnb"], reverse=True)[:5]
        medals   = ["🥇","🥈","🥉","4️⃣","5️⃣"]
        row_css  = ["g1","g2","g3","gn","gn"]

        t5_html = ""
        for i, p in enumerate(top5):
            mc  = "gn" if p["gap_dnb"] < -3.0 else ("ye" if p["gap_dnb"] < -1.5 else "gn")
            vc  = "gn" if p["gap_dnb"] >= -1.5 else ("ye" if p["gap_dnb"] >= -3.0 else "gr")
            fd  = p["kickoff"].replace("2026-","").replace("-","/")
            t5_html += f"""
            <div class="t5-row {row_css[i]}">
                <div class="t5-medal">{medals[i]}</div>
                <div>
                    <div class="t5-match">{p['home']} vs {p['away']}</div>
                    <div class="t5-date">📅 {fd}</div>
                </div>
                <div class="t5-cell">
                    <div class="t5-lbl">Favorito</div>
                    <div class="t5-val au">{p['fav']}</div>
                    <div class="t5-sub">{p['fav_prob']}% prob modelo</div>
                </div>
                <div class="t5-cell">
                    <div class="t5-lbl">Victoria @</div>
                    <div class="t5-val">{p['fav_odds']}</div>
                    <div class="t5-sub">break-ev {round(100/p['fav_odds'],1)}%</div>
                </div>
                <div class="t5-cell">
                    <div class="t5-lbl">DNB @</div>
                    <div class="t5-val">{p['fav_dnb_odds']}</div>
                    <div class="t5-sub">{p['fav_dnb_prob']}% cond.</div>
                </div>
                <div class="t5-cell">
                    <div class="t5-lbl">Margen DNB</div>
                    <div class="t5-val {vc}">{p['gap_dnb']:+.1f}%</div>
                    <div class="t5-sub">prob − break-even</div>
                </div>
            </div>"""

        st.markdown(t5_html, unsafe_allow_html=True)

        # ── CUADRO COMPLETO — ordenado por fecha asc ─────────────────────────
        st.markdown("""
        <div style="font-family:'Bebas Neue',sans-serif;font-size:0.95rem;color:#d4af37;
                    letter-spacing:4px;margin:1.8rem 0 0.8rem;">
            📋 CUADRO COMPLETO — PARTIDOS POR FECHA
        </div>
        """, unsafe_allow_html=True)

        # Ordenar cronológicamente (más próximo primero)
        proj_sorted = sorted(wc_proj, key=lambda x: x["kickoff"])

        def pc(v): return "ph" if v>=65 else ("pm" if v>=50 else "")
        def mc_fn(v): return "mk-ok" if v>=-1.5 else ("mk-mid" if v>=-3.0 else "mk-bad")

        rows_html = ""
        for p in proj_sorted:
            fd   = p["kickoff"].replace("2026-","").replace("-","/")
            dnb  = (
                f'<span class="dnb-p">@ {p["fav_dnb_odds"]}</span>'
                f'<div style="font-size:0.6rem;color:#2a4a65;margin-top:2px;">{p["fav_dnb_prob"]}%</div>'
            ) if p["fav_dnb_odds"]>=1.05 else "—"
            rows_html += f"""
            <tr>
                <td>{fd}</td>
                <td>{p['home']} vs {p['away']}</td>
                <td><span class="{pc(p['home_prob'])}">{p['home_prob']}%</span>
                    <div style="font-size:0.6rem;color:#2a4a65;">@ {p['home_odds']}</div></td>
                <td><span>{p['draw_prob']}%</span>
                    <div style="font-size:0.6rem;color:#2a4a65;">@ {p['draw_odds']}</div></td>
                <td><span class="{pc(p['away_prob'])}">{p['away_prob']}%</span>
                    <div style="font-size:0.6rem;color:#2a4a65;">@ {p['away_odds']}</div></td>
                <td><span class="fav-p">{p['fav']}</span></td>
                <td>{dnb}</td>
                <td><span class="{mc_fn(p['gap_win'])}">{p['gap_win']:+.1f}%</span></td>
                <td><span class="{mc_fn(p['gap_dnb'])}">{p['gap_dnb']:+.1f}%</span></td>
            </tr>"""

        st.markdown(f"""
        <div class="wc-tbl-wrap">
            <table class="wc-tbl">
                <thead><tr>
                    <th>Fecha</th><th>Partido</th>
                    <th>Local</th><th>Empate</th><th>Visitante</th>
                    <th>Favorito</th><th>DNB</th>
                    <th>Margen Vic.</th><th>Margen DNB</th>
                </tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
            <div class="wc-legend">
                <span>Margen = prob. modelo − break-even · menos negativo = mejor precio</span>
                <span><b style="color:#3dd878">Verde</b> ≥ −1.5% &nbsp;·&nbsp; <b style="color:#ffd166">Amarillo</b> ≥ −3%</span>
                <span>DNB = Draw No Bet · empate devuelve apuesta</span>
                <span>Modelo: Pinnacle sin margen (no-vig)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── EXPORT ───────────────────────────────────────────────────────────────
    if all_bets:
        st.markdown("<br>", unsafe_allow_html=True)
        df = pd.DataFrame([{
            "Liga":b["league"], "Partido":b["match"], "Fecha":b["kickoff"],
            "Apuesta":b["market"], "Cuota":b["odds"], "Modelo%":b["model"],
            "Edge%":b["edge"], "Kelly€":b["kelly"], "Veredicto":b["verdict"],
        } for b in all_bets])
        st.download_button(
            "↓  Descargar CSV completo",
            df.to_csv(index=False).encode("utf-8"),
            f"value_bets_{now.strftime('%Y%m%d')}.csv", "text/csv",
        )

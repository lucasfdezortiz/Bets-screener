import os

# --- API Keys ---
FOOTBALL_DATA_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "205181fa9288458ab368620ea2ed043f")
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "2e0cc7717f96a25817a3c781429437b8")

# --- Modelo ---
HOME_ADVANTAGE = 1.35       # Factor ventaja de campo (empírico)
MAX_GOALS_SIMULATED = 9     # Goles máximos en la matriz de Poisson (0..8)

# --- Kelly ---
BANKROLL = 200.0            # Bankroll en euros
KELLY_FRACTION = 0.5        # Medio Kelly
VALUE_BET_THRESHOLD = 5.0   # Edge mínimo (%) para considerar value bet
MARGINAL_THRESHOLD = 0.0    # Edge mínimo para "marginal"

# --- Football-data.org API v4 ---
FOOTBALL_API_BASE = "https://api.football-data.org/v4"

COMPETITION_CODES = {
    "laliga": "PD",
    "la liga": "PD",
    "premier": "PL",
    "premier league": "PL",
    "bundesliga": "BL1",
    "serie a": "SA",
    "seriea": "SA",
    "ligue 1": "FL1",
    "ligue1": "FL1",
    "champions": "CL",
    "champions league": "CL",
    "eredivisie": "DED",
    "primeira liga": "PPL",
    "championship": "ELC",
}

# --- Tenis ---
SURFACE_FACTORS = {
    # Factor de ajuste relativo por superficie (empírico)
    # Jugadores de tierra batida rinden ~10% mejor en tierra
    "clay": {"clay_specialist_boost": 1.10, "hard_specialist_boost": 0.95},
    "hard": {"clay_specialist_boost": 0.95, "hard_specialist_boost": 1.05},
    "grass": {"clay_specialist_boost": 0.90, "hard_specialist_boost": 1.02},
}

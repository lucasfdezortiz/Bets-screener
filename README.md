# Bets-screener

Herramienta de terminal para detectar **value bets** en fútbol y tenis.  
Modelo de Poisson (fútbol) + Pinnacle como referencia sharp (tenis) · Target: **Winamax FR**.

---

## Estrategia: Alta Convicción

El objetivo es maximizar el **% de acierto** apostando fuerte donde el modelo tiene alta confianza y el edge es real:

| Sección | Filtro | Acción |
|---|---|---|
| 🎯 **Alta Convicción** | cuota ≤ 1.75 · prob modelo ≥ 62% · edge ≥ 5% | **Apostar fuerte** |
| ⚡ **Alto Edge** | edge ≥ 5% · cualquier cuota | Apostar moderado |
| 👁 **Vigilancia** | edge 3-5% · cuota ≤ 3.00 | Solo seguimiento |

- **HitRate** = probabilidad del modelo = % de acierto esperado  
- **Break-even** = % mínimo de acierto para no perder a esa cuota  
- **Kelly** = apuesta recomendada con Medio Kelly sobre bankroll de €200

---

## Uso

```bash
python3 daily_scan.py
```

> **Nota**: `config.py` contiene las API keys y NO debe subirse a GitHub (está en `.gitignore`).

---

## Estructura

```
modules/
├── scanner.py          # Escáner de fútbol (Odds API + football-data.org)
├── tennis_scanner.py   # Escáner de tenis (Pinnacle como sharp reference)
├── poisson_model.py    # Modelo de Poisson para fútbol
└── kelly_calculator.py # Edge, EV y criterio de Kelly
daily_scan.py           # Script principal — reporte diario
main.py                 # CLI interactivo para análisis manual de partidos
```

---

## Fuentes de datos

- **The Odds API** — cuotas de Winamax FR y Pinnacle en tiempo real
- **football-data.org** — estadísticas de equipos (La Liga, Premier, Bundesliga, Serie A, Ligue 1)
- **ESPN API** — standings de Segunda División española
- **Pinnacle** — referencia sharp para tenis (probabilidades sin margen)

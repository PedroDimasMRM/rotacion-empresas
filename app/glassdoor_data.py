"""
Ratings de referencia de Glassdoor para las 20 multinacionales.
Datos públicos obtenidos de Glassdoor.com (ratings 1-5).
Se pueden actualizar manualmente editando este archivo o via data/glassdoor_custom.json.

Última revisión de referencia: abril 2026.
"""

# (ticker): (rating 1-5, fecha_referencia)
GLASSDOOR_RATINGS = {
    "AAPL":      (4.2, "2026-Q1"),   # Apple - consistentemente alto
    "MSFT":      (4.3, "2026-Q1"),   # Microsoft - cultura fuerte post-Nadella
    "AMZN":      (3.4, "2026-Q1"),   # Amazon - polarizado, almacenes vs corporate
    "GOOGL":     (4.3, "2026-Q1"),   # Google/Alphabet - sigue alto pero bajando
    "META":      (3.9, "2026-Q1"),   # Meta - recuperándose tras layoffs 2023
    "TSLA":      (3.1, "2026-Q1"),   # Tesla - alta presión, bajo rating
    "WMT":       (3.3, "2026-Q1"),   # Walmart - retail, ratings moderados
    "005930.KS": (3.7, "2026-Q1"),   # Samsung - bueno para tech coreana
    "TM":        (3.8, "2026-Q1"),   # Toyota - estable, cultura japonesa
    "JPM":       (3.9, "2026-Q1"),   # JPMorgan - banca top, exigente
    "JNJ":       (4.0, "2026-Q1"),   # J&J - farmacéutica, buen ambiente
    "NESN.SW":   (3.9, "2026-Q1"),   # Nestlé - referencia en FMCG
    "SIE.DE":    (3.8, "2026-Q1"),   # Siemens - industria alemana
    "MC.PA":     (3.6, "2026-Q1"),   # LVMH - lujo, selectiva
    "ULVR.L":    (3.8, "2026-Q1"),   # Unilever - consumo masivo
    "PG":        (3.9, "2026-Q1"),   # P&G - cultura corporativa fuerte
    "PFE":       (3.7, "2026-Q1"),   # Pfizer - post-COVID ajuste
    "ACN":       (3.9, "2026-Q1"),   # Accenture - consultoría top
    "NVDA":      (4.5, "2026-Q1"),   # NVIDIA - empresa del momento
    "BRK-B":     (3.7, "2026-Q1"),   # Berkshire - conglomerado diverso
}

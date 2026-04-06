"""
Configuración central del proyecto.
Lista de empresas objetivo, parámetros y constantes.
"""

# ── Empresas a analizar ──────────────────────────────────────────────
# Cada entrada: (nombre_display, ticker_yahoo_finance, sector, país_sede)
EMPRESAS = [
    ("Apple Inc.", "AAPL", "Tecnología", "EE.UU."),
    ("Microsoft Corporation", "MSFT", "Tecnología", "EE.UU."),
    ("Amazon.com, Inc.", "AMZN", "E-commerce / Cloud", "EE.UU."),
    ("Alphabet Inc. (Google)", "GOOGL", "Tecnología", "EE.UU."),
    ("Meta Platforms, Inc.", "META", "Tecnología / RRSS", "EE.UU."),
    ("Tesla, Inc.", "TSLA", "Automoción / Energía", "EE.UU."),
    ("Walmart Inc.", "WMT", "Retail", "EE.UU."),
    ("Samsung Electronics Co., Ltd.", "005930.KS", "Electrónica", "Corea del Sur"),
    ("Toyota Motor Corporation", "TM", "Automoción", "Japón"),
    ("JPMorgan Chase & Co.", "JPM", "Banca / Finanzas", "EE.UU."),
    ("Johnson & Johnson", "JNJ", "Farmacéutica", "EE.UU."),
    ("Nestlé S.A.", "NESN.SW", "Alimentación", "Suiza"),
    ("Siemens AG", "SIE.DE", "Industria / Tech", "Alemania"),
    ("LVMH Moët Hennessy", "MC.PA", "Lujo", "Francia"),
    ("Unilever PLC", "ULVR.L", "Consumo masivo", "Reino Unido"),
    ("Procter & Gamble Co.", "PG", "Consumo masivo", "EE.UU."),
    ("Pfizer Inc.", "PFE", "Farmacéutica", "EE.UU."),
    ("Accenture PLC", "ACN", "Consultoría", "Irlanda"),
    ("NVIDIA Corporation", "NVDA", "Tecnología / Semiconductores", "EE.UU."),
    ("Berkshire Hathaway Inc.", "BRK-B", "Conglomerado / Finanzas", "EE.UU."),
]

# ── Parámetros del estimador ─────────────────────────────────────────
# Pesos para el proxy de rotación (deben sumar 1.0)
PESOS_ROTACION = {
    "ofertas_vs_empleados": 0.25,   # ratio ofertas abiertas / total empleados
    "noticias_despidos": 0.20,      # menciones de layoffs en noticias
    "rating_glassdoor": 0.15,       # rating real de Glassdoor (invertido)
    "google_trends": 0.15,          # interés en "[empresa] layoffs" vía Google Trends
    "crecimiento_empleados": 0.15,  # variación interanual de plantilla
    "sentimiento_rrss": 0.10,       # sentimiento negativo en redes
}

# Pesos para el índice de tamaño de empresa
PESOS_TAMANIO = {
    "ingresos": 0.35,
    "market_cap": 0.25,
    "num_empleados": 0.25,
    "paises": 0.15,
}

# ── Niveles de referencia de rotación ────────────────────────────────
NIVELES_ROTACION = [
    (10, "Bajo", "Alta retención, empresa estable"),
    (20, "Moderado", "Normal en la mayoría de industrias"),
    (30, "Alto", "Señal de alerta, revisar causas"),
    (100, "Muy alto", "Problema estructural serio"),
]

# ── Configuración de búsqueda de noticias ────────────────────────────
# Palabras clave para detectar noticias de despidos/rotación
KEYWORDS_DESPIDOS = [
    "layoffs", "laid off", "job cuts", "workforce reduction",
    "downsizing", "restructuring", "despidos", "recortes de personal",
    "firing", "let go", "headcount reduction",
]

# Número máximo de noticias a buscar por empresa
MAX_NOTICIAS_POR_EMPRESA = 10

# ── Rutas de salida ──────────────────────────────────────────────────
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(os.path.dirname(BASE_DIR), "output")
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")

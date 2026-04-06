"""
Recopilador de ratings de Glassdoor.
Usa un dataset de referencia con ratings conocidos para las 20 multinacionales
y permite overrides via data/glassdoor_custom.json.

Los ratings de Glassdoor (1-5) se convierten a un score de rotación (0-100):
  5.0 → 0  (empresa excelente, rotación baja)
  3.0 → 50 (neutro)
  1.0 → 100 (muy mala, rotación alta)
"""

import json
import os

from config import DATA_DIR
from glassdoor_data import GLASSDOOR_RATINGS


_CUSTOM_FILE = os.path.join(DATA_DIR, "glassdoor_custom.json")


def obtener_ratings_glassdoor(empresas: list) -> dict:
    """
    Obtiene ratings de Glassdoor para cada empresa.
    Prioridad: 1) Override en glassdoor_custom.json, 2) Dataset de referencia.

    Args:
        empresas: lista de tuplas (nombre, ticker, sector, país)

    Returns:
        dict keyed by ticker, con rating (1-5), score (0-100), fuente, etc.
    """
    # Cargar overrides si existen
    overrides = _cargar_overrides()

    resultados = {}
    total = len(empresas)

    for i, (nombre, ticker, sector, pais) in enumerate(empresas, 1):
        # Prioridad 1: override personalizado
        if ticker in overrides:
            rating = overrides[ticker]
            fuente = "glassdoor_custom.json"
        # Prioridad 2: dataset de referencia
        elif ticker in GLASSDOOR_RATINGS:
            rating, periodo = GLASSDOOR_RATINGS[ticker]
            fuente = f"Dataset referencia ({periodo})"
        else:
            # Sin datos
            resultados[ticker] = {
                "rating": None,
                "score": 50,
                "fuente": None,
                "error": "No hay rating de referencia para esta empresa",
            }
            print(f"  [{i}/{total}] {nombre}: ⚠️ Sin rating de Glassdoor")
            continue

        score = _rating_a_score(rating)
        resultados[ticker] = {
            "rating": rating,
            "score": score,
            "fuente": fuente,
            "error": None,
        }
        print(f"  [{i}/{total}] {nombre}: ⭐ {rating}/5.0 → Score rotación: {score}/100 [{fuente}]")

    return resultados


def _rating_a_score(rating: float) -> int:
    """
    Convierte un rating de Glassdoor (1-5) a un score de rotación (0-100).
    Rating alto = empresa buena = rotación baja = score bajo.

    Escala:
        5.0 → 0  (empresa excelente, sin rotación esperada)
        4.0 → 25
        3.0 → 50 (neutro)
        2.0 → 75
        1.0 → 100 (muy mala, rotación máxima esperada)
    """
    return max(0, min(100, round((5.0 - rating) * 25)))


def _cargar_overrides() -> dict:
    """Carga ratings personalizados desde data/glassdoor_custom.json si existe."""
    if not os.path.exists(_CUSTOM_FILE):
        return {}
    try:
        with open(_CUSTOM_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Espera formato: {"AAPL": 4.2, "MSFT": 4.3, ...}
        return {k: float(v) for k, v in data.items()}
    except (json.JSONDecodeError, ValueError):
        return {}


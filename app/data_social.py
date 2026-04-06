"""
Análisis de sentimiento en redes sociales (RRSS).
Busca menciones negativas sobre condiciones laborales de cada empresa
usando Google News RSS como proxy de redes sociales y foros.
"""

import urllib.parse
import xml.etree.ElementTree as ET
import re

import requests


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

_TIMEOUT = 15

# Palabras clave negativas sobre ambiente laboral
_KEYWORDS_NEGATIVAS = [
    "toxic workplace", "burnout", "overworked", "quit",
    "resignation", "great resignation", "employee complaints",
    "hostile work environment", "labor dispute", "strike",
    "walkout", "union", "unfair", "worst place to work",
]

# Palabras clave positivas (para contrastar)
_KEYWORDS_POSITIVAS = [
    "best place to work", "top employer", "employee satisfaction",
    "great workplace", "award employer", "happy employees",
]


def analizar_sentimiento_rrss(empresas: list) -> dict:
    """
    Analiza el sentimiento laboral en medios/redes para cada empresa.
    Busca menciones negativas vs positivas como proxy de satisfacción.

    Args:
        empresas: lista de tuplas (nombre, ticker, sector, país)

    Returns:
        dict con clave=ticker, valor=dict(score, menciones_negativas, menciones_positivas, ...)
    """
    resultados = {}
    total = len(empresas)

    for i, (nombre, ticker, sector, pais) in enumerate(empresas, 1):
        nombre_corto = _nombre_busqueda(nombre)
        print(f"  [{i}/{total}] Sentimiento RRSS: {nombre_corto}...")

        negativas = _buscar_menciones(nombre_corto, _KEYWORDS_NEGATIVAS)
        positivas = _buscar_menciones(nombre_corto, _KEYWORDS_POSITIVAS)

        # Score: más menciones negativas y menos positivas = mayor rotación estimada
        neg_count = negativas["relevantes"]
        pos_count = positivas["relevantes"]

        if neg_count + pos_count > 0:
            ratio_negativo = neg_count / (neg_count + pos_count)
        else:
            ratio_negativo = 0.5  # neutro sin datos

        score = min(100, int(ratio_negativo * 70 + min(neg_count, 8) * 4))

        resultados[ticker] = {
            "menciones_negativas": neg_count,
            "menciones_positivas": pos_count,
            "total_neg_resultados": negativas["total"],
            "total_pos_resultados": positivas["total"],
            "ratio_negativo": round(ratio_negativo, 2),
            "score": score,
            "error": negativas.get("error") or positivas.get("error"),
        }

    return resultados


def _buscar_menciones(empresa: str, keywords: list) -> dict:
    """Busca menciones en Google News RSS con las keywords dadas."""
    kw_query = " OR ".join(f'"{kw}"' for kw in keywords[:5])
    query = f'"{empresa}" ({kw_query})'
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en&gl=US&ceid=US:en"

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        total = len(items)

        relevantes = 0
        for item in items:
            titulo = (item.findtext("title", "") or "").lower()
            if any(kw.lower() in titulo for kw in keywords):
                relevantes += 1

        return {"total": total, "relevantes": relevantes, "error": None}

    except Exception as e:
        return {"total": 0, "relevantes": 0, "error": str(e)}


def _nombre_busqueda(nombre: str) -> str:
    match = re.search(r'\(([^)]+)\)', nombre)
    if match:
        return match.group(1)
    for sufijo in ["Inc.", "Corp.", "Corporation", "Co., Ltd.", "Co.",
                    "Ltd.", "PLC", "S.A.", "AG", "SE", "N.V."]:
        nombre = nombre.replace(sufijo, "")
    return nombre.strip().split(",")[0].strip()

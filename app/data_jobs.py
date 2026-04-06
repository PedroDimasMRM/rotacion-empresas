"""
Estimador de ofertas de empleo abiertas por empresa.
Usa Google Search RSS para contar cuántas ofertas de trabajo aparecen
publicadas recientemente (indicador indirecto de rotación).
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


def estimar_ofertas_empleo(empresas: list) -> dict:
    """
    Estima la cantidad de ofertas de empleo abiertas buscando en Google News
    menciones de hiring/jobs para cada empresa.

    Args:
        empresas: lista de tuplas (nombre, ticker, sector, país)

    Returns:
        dict con clave=ticker, valor=dict(ofertas_encontradas, score, ratio)
    """
    resultados = {}
    total = len(empresas)

    for i, (nombre, ticker, sector, pais) in enumerate(empresas, 1):
        nombre_corto = _nombre_busqueda(nombre)
        print(f"  [{i}/{total}] Ofertas de empleo: {nombre_corto}...")

        ofertas = _buscar_ofertas_google(nombre_corto)
        resultados[ticker] = ofertas

    return resultados


def _buscar_ofertas_google(empresa: str) -> dict:
    """
    Busca en Google News RSS menciones de contratación masiva o
    gran número de vacantes de una empresa.
    """
    keywords_hiring = ["hiring", "job openings", "open positions", "vacantes", "recruiting"]
    kw_query = " OR ".join(f'"{kw}"' for kw in keywords_hiring[:4])
    query = f'"{empresa}" ({kw_query})'
    encoded = urllib.parse.quote(query)

    url = f"https://news.google.com/rss/search?q={encoded}&hl=en&gl=US&ceid=US:en"

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        items = root.findall(".//item")

        total_resultados = len(items)

        # Contar cuántos títulos realmente mencionan hiring/jobs
        relevantes = 0
        for item in items:
            titulo = (item.findtext("title", "") or "").lower()
            if any(kw.lower() in titulo for kw in keywords_hiring):
                relevantes += 1

        # Score: empresas que aparecen mucho contratando pueden tener alta rotación
        # (necesitan reponer personal constantemente)
        if total_resultados > 0:
            ratio = relevantes / total_resultados
        else:
            ratio = 0

        score = min(100, int(ratio * 60 + min(relevantes, 8) * 5))

        return {
            "total_resultados": total_resultados,
            "ofertas_relevantes": relevantes,
            "ratio": round(ratio, 2),
            "score": score,
            "error": None,
        }

    except Exception as e:
        return {
            "total_resultados": 0,
            "ofertas_relevantes": 0,
            "ratio": 0,
            "score": 0,
            "error": str(e),
        }


def _nombre_busqueda(nombre: str) -> str:
    """Extrae el nombre más reconocible para búsqueda."""
    match = re.search(r'\(([^)]+)\)', nombre)
    if match:
        return match.group(1)
    for sufijo in ["Inc.", "Corp.", "Corporation", "Co., Ltd.", "Co.",
                    "Ltd.", "PLC", "S.A.", "AG", "SE", "N.V."]:
        nombre = nombre.replace(sufijo, "")
    return nombre.strip().split(",")[0].strip()

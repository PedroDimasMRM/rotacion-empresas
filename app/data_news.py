"""
Recopilador de noticias sobre despidos y rotación.
Usa búsqueda web gratuita (sin API key) mediante scraping de Google News RSS.
"""

import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional

import requests
import re


# User-Agent para las peticiones HTTP
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

_TIMEOUT = 15


def buscar_noticias_google_rss(empresa: str, keywords: list[str],
                                max_resultados: int = 10) -> list[dict]:
    """
    Busca noticias sobre despidos de una empresa usando Google News RSS (gratuito).
    
    Args:
        empresa: Nombre de la empresa (ej: "Amazon")
        keywords: Lista de palabras clave de despidos
        max_resultados: Máximo de noticias a devolver
    
    Returns:
        Lista de dicts con título, enlace, fecha y fuente
    """
    # Construir query: "Amazon" AND (layoffs OR "job cuts" OR despidos ...)
    kw_query = " OR ".join(f'"{kw}"' for kw in keywords[:5])  # limitar para no alargar la URL
    query = f'"{empresa}" ({kw_query})'
    encoded = urllib.parse.quote(query)

    url = f"https://news.google.com/rss/search?q={encoded}&hl=en&gl=US&ceid=US:en"

    noticias = []
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        items = root.findall(".//item")

        for item in items[:max_resultados]:
            titulo = item.findtext("title", "")
            enlace = item.findtext("link", "")
            fecha_str = item.findtext("pubDate", "")
            fuente = item.findtext("source", "Desconocida")

            fecha = _parsear_fecha(fecha_str)

            noticias.append({
                "titulo": titulo,
                "enlace": enlace,
                "fecha": fecha,
                "fuente": fuente,
            })
    except Exception as e:
        noticias.append({
            "titulo": f"[ERROR] No se pudieron obtener noticias: {e}",
            "enlace": "",
            "fecha": None,
            "fuente": "Error",
        })

    return noticias


def calcular_score_noticias(noticias: list[dict], keywords: list[str]) -> dict:
    """
    Analiza las noticias encontradas y calcula un score indicativo de rotación.
    
    Retorna:
        dict con score (0-100), total de noticias relevantes, y detalle
    """
    if not noticias:
        return {"score": 0, "total_noticias": 0, "noticias_relevantes": 0, "detalle": "Sin datos"}

    # Filtrar errores
    noticias_validas = [n for n in noticias if not n["titulo"].startswith("[ERROR]")]
    total = len(noticias_validas)

    if total == 0:
        return {"score": 0, "total_noticias": 0, "noticias_relevantes": 0, "detalle": "Sin noticias válidas"}

    # Contar cuántas mencionan palabras clave de despidos en el título
    relevantes = 0
    for n in noticias_validas:
        titulo_lower = n["titulo"].lower()
        if any(kw.lower() in titulo_lower for kw in keywords):
            relevantes += 1

    # Score: proporción de noticias sobre despidos (normalizado a 0-100)
    if total > 0:
        ratio = relevantes / total
    else:
        ratio = 0

    # Ajustar: más noticias totales encontradas = mayor confianza
    # y la cantidad absoluta de noticias de despidos también importa
    score = min(100, int(ratio * 70 + min(relevantes, 10) * 3))

    recientes = _contar_recientes(noticias_validas, meses=6)

    return {
        "score": score,
        "total_noticias": total,
        "noticias_relevantes": relevantes,
        "noticias_recientes_6m": recientes,
        "detalle": f"{relevantes}/{total} noticias sobre despidos/rotación",
    }


def recopilar_noticias_empresas(empresas: list, keywords: list[str],
                                 max_por_empresa: int = 10) -> dict:
    """
    Busca noticias de despidos para todas las empresas.
    
    Args:
        empresas: lista de tuplas (nombre, ticker, sector, país)
        keywords: palabras clave de búsqueda
        max_por_empresa: máximo de noticias por empresa
    
    Returns:
        dict con clave=ticker, valor=dict(noticias, score)
    """
    resultados = {}
    total = len(empresas)

    for i, (nombre, ticker, sector, pais) in enumerate(empresas, 1):
        # Usar nombre corto para búsqueda (sin "Inc.", "Corp.", etc.)
        nombre_busqueda = _limpiar_nombre(nombre)
        print(f"  [{i}/{total}] Buscando noticias de {nombre_busqueda}...")

        noticias = buscar_noticias_google_rss(
            nombre_busqueda, keywords, max_por_empresa
        )
        score_info = calcular_score_noticias(noticias, keywords)

        resultados[ticker] = {
            "nombre": nombre,
            "noticias": noticias,
            "score": score_info,
        }

    return resultados


def _limpiar_nombre(nombre: str) -> str:
    """Elimina sufijos corporativos para mejorar la búsqueda."""
    sufijos = [
        "Inc.", "Corp.", "Corporation", "Co., Ltd.", "Co.",
        "Ltd.", "PLC", "S.A.", "AG", "SE", "N.V.",
    ]
    resultado = nombre
    for s in sufijos:
        resultado = resultado.replace(s, "")
    # Limpiar paréntesis tipo "(Google)"
    match = re.search(r'\(([^)]+)\)', resultado)
    if match:
        # Si hay algo entre paréntesis, probablemente es el nombre más conocido
        resultado = match.group(1)
    return resultado.strip()


def _parsear_fecha(fecha_str: str) -> Optional[str]:
    """Parsea fecha de Google News RSS."""
    if not fecha_str:
        return None
    try:
        # Formato típico: "Mon, 01 Jan 2026 12:00:00 GMT"
        dt = datetime.strptime(fecha_str.strip(), "%a, %d %b %Y %H:%M:%S %Z")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return fecha_str


def _contar_recientes(noticias: list[dict], meses: int = 6) -> int:
    """Cuenta noticias de los últimos N meses."""
    ahora = datetime.now()
    count = 0
    for n in noticias:
        if n.get("fecha"):
            try:
                fecha = datetime.strptime(n["fecha"], "%Y-%m-%d")
                diff = (ahora - fecha).days
                if diff <= meses * 30:
                    count += 1
            except (ValueError, TypeError):
                pass
    return count

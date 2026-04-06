"""
Recopilador de datos financieros usando yfinance.
Obtiene: ingresos, capitalización bursátil, número de empleados, etc.
"""

import yfinance as yf
import pandas as pd
from typing import Optional


def obtener_datos_financieros(ticker: str, nombre: str) -> dict:
    """
    Obtiene datos financieros clave de una empresa vía Yahoo Finance.
    Retorna un diccionario con los datos o valores None si no están disponibles.
    """
    resultado = {
        "nombre": nombre,
        "ticker": ticker,
        "ingresos_usd": None,
        "market_cap_usd": None,
        "num_empleados": None,
        "pais": None,
        "sector": None,
        "industria": None,
        "website": None,
        "moneda": None,
        "precio_accion": None,
        "error": None,
    }

    try:
        empresa = yf.Ticker(ticker)
        info = empresa.info

        if not info or info.get("trailingPegRatio") is None and info.get("marketCap") is None:
            # Intentar obtener al menos datos básicos
            pass

        resultado["ingresos_usd"] = info.get("totalRevenue") or info.get("revenue")
        resultado["market_cap_usd"] = info.get("marketCap")
        resultado["num_empleados"] = info.get("fullTimeEmployees")
        resultado["pais"] = info.get("country")
        resultado["sector"] = info.get("sector")
        resultado["industria"] = info.get("industry")
        resultado["website"] = info.get("website")
        resultado["moneda"] = info.get("currency", "USD")
        resultado["precio_accion"] = info.get("currentPrice") or info.get("regularMarketPrice")

    except Exception as e:
        resultado["error"] = str(e)

    return resultado


def obtener_historial_empleados(ticker: str) -> Optional[dict]:
    """
    Intenta estimar la variación de empleados.
    yfinance no siempre tiene histórico de empleados, pero podemos
    guardar el dato actual para comparar en futuras ejecuciones.
    """
    try:
        empresa = yf.Ticker(ticker)
        empleados_actual = empresa.info.get("fullTimeEmployees")
        return {
            "ticker": ticker,
            "empleados_actual": empleados_actual,
        }
    except Exception:
        return None


def recopilar_todas_las_empresas(empresas: list) -> pd.DataFrame:
    """
    Recorre la lista de empresas y recopila datos financieros de cada una.
    
    Args:
        empresas: lista de tuplas (nombre, ticker, sector, país)
    
    Returns:
        DataFrame con todos los datos financieros
    """
    resultados = []
    total = len(empresas)

    for i, (nombre, ticker, sector, pais) in enumerate(empresas, 1):
        print(f"  [{i}/{total}] Obteniendo datos de {nombre} ({ticker})...")
        datos = obtener_datos_financieros(ticker, nombre)
        datos["sector_config"] = sector
        datos["pais_config"] = pais
        resultados.append(datos)

    df = pd.DataFrame(resultados)
    return df


def formatear_numero(valor) -> str:
    """Formatea un número grande para lectura humana."""
    if valor is None:
        return "N/D"
    if valor >= 1_000_000_000_000:
        return f"${valor / 1_000_000_000_000:.2f}T"
    if valor >= 1_000_000_000:
        return f"${valor / 1_000_000_000:.2f}B"
    if valor >= 1_000_000:
        return f"${valor / 1_000_000:.2f}M"
    return f"${valor:,.0f}"

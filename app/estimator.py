"""
Estimador de rotación de empleados.
Combina datos financieros, noticias, Google Trends, Glassdoor,
ofertas de empleo y sentimiento RRSS para calcular un proxy-score de rotación.
(6 fuentes de datos)
"""

import pandas as pd
from config import PESOS_ROTACION, PESOS_TAMANIO, NIVELES_ROTACION
from database import obtener_variacion_empleados


def calcular_indice_tamanio(row: pd.Series, maximos: dict) -> float:
    """
    Calcula un índice normalizado (0-100) del tamaño de la empresa.
    """
    score = 0.0

    if row.get("ingresos_usd") and maximos.get("ingresos") and maximos["ingresos"] > 0:
        score += (row["ingresos_usd"] / maximos["ingresos"]) * PESOS_TAMANIO["ingresos"] * 100

    if row.get("market_cap_usd") and maximos.get("market_cap") and maximos["market_cap"] > 0:
        score += (row["market_cap_usd"] / maximos["market_cap"]) * PESOS_TAMANIO["market_cap"] * 100

    if row.get("num_empleados") and maximos.get("empleados") and maximos["empleados"] > 0:
        score += (row["num_empleados"] / maximos["empleados"]) * PESOS_TAMANIO["num_empleados"] * 100

    return round(min(score, 100), 1)


def calcular_proxy_rotacion(datos_financieros: dict, datos_noticias: dict,
                             datos_trends: dict = None, datos_ofertas: dict = None,
                             datos_social: dict = None,
                             datos_glassdoor: dict = None) -> dict:
    """
    Calcula el proxy-score de rotación para una empresa combinando
    las 6 fuentes de datos disponibles (Fase 4).
    """
    desglose = {}
    score_total = 0.0
    fuentes_activas = 0

    # ── Score por noticias de despidos (peso: 0.20) ──
    score_noticias = datos_noticias.get("score", {}).get("score", 0) if datos_noticias else 0
    contribucion = score_noticias * PESOS_ROTACION["noticias_despidos"]
    desglose["noticias_despidos"] = {
        "score_bruto": score_noticias,
        "peso": PESOS_ROTACION["noticias_despidos"],
        "contribucion": round(contribucion, 1),
        "estado": "✅ Activo",
    }
    score_total += contribucion
    fuentes_activas += 1

    # ── Score por ofertas de empleo (peso: 0.25) ──
    if datos_ofertas and datos_ofertas.get("error") is None:
        score_ofertas = datos_ofertas.get("score", 0)
        fuentes_activas += 1
        estado = "✅ Activo"
    else:
        score_ofertas = 50
        estado = "⚠️ Sin datos"
    contribucion = score_ofertas * PESOS_ROTACION["ofertas_vs_empleados"]
    desglose["ofertas_vs_empleados"] = {
        "score_bruto": score_ofertas,
        "peso": PESOS_ROTACION["ofertas_vs_empleados"],
        "contribucion": round(contribucion, 1),
        "estado": estado,
    }
    score_total += contribucion

    # ── Score por rating Glassdoor (peso: 0.15) ──
    if datos_glassdoor and datos_glassdoor.get("error") is None:
        score_glassdoor = datos_glassdoor.get("score", 50)
        fuentes_activas += 1
        estado = "✅ Activo"
    else:
        score_glassdoor = 50
        estado = "⚠️ Sin datos"
    contribucion = score_glassdoor * PESOS_ROTACION["rating_glassdoor"]
    desglose["rating_glassdoor"] = {
        "score_bruto": score_glassdoor,
        "peso": PESOS_ROTACION["rating_glassdoor"],
        "contribucion": round(contribucion, 1),
        "estado": estado,
    }
    score_total += contribucion

    # ── Score por Google Trends (peso: 0.15) ──
    if datos_trends and datos_trends.get("error") is None:
        score_trends = datos_trends.get("score", 0)
        fuentes_activas += 1
        estado = "✅ Activo"
    else:
        score_trends = 50
        estado = "⚠️ Sin datos"
    contribucion = score_trends * PESOS_ROTACION["google_trends"]
    desglose["google_trends"] = {
        "score_bruto": score_trends,
        "peso": PESOS_ROTACION["google_trends"],
        "contribucion": round(contribucion, 1),
        "estado": estado,
    }
    score_total += contribucion

    # ── Score por variación de empleados (peso: 0.15) ──
    ticker = datos_financieros.get("ticker", "")
    variacion = obtener_variacion_empleados(ticker)
    score_empleados = variacion["score"]
    contribucion = score_empleados * PESOS_ROTACION["crecimiento_empleados"]
    desglose["crecimiento_empleados"] = {
        "score_bruto": score_empleados,
        "peso": PESOS_ROTACION["crecimiento_empleados"],
        "contribucion": round(contribucion, 1),
        "estado": "✅ Activo" if variacion.get("variacion_pct") is not None else "⏳ Acumulando datos",
        "nota": variacion.get("nota", ""),
    }
    score_total += contribucion
    if variacion.get("variacion_pct") is not None:
        fuentes_activas += 1

    # ── Score por sentimiento RRSS (peso: 0.10) ──
    if datos_social and datos_social.get("error") is None:
        score_rrss = datos_social.get("score", 0)
        fuentes_activas += 1
        estado = "✅ Activo"
    else:
        score_rrss = 50
        estado = "⚠️ Sin datos"
    contribucion = score_rrss * PESOS_ROTACION["sentimiento_rrss"]
    desglose["sentimiento_rrss"] = {
        "score_bruto": score_rrss,
        "peso": PESOS_ROTACION["sentimiento_rrss"],
        "contribucion": round(contribucion, 1),
        "estado": estado,
    }
    score_total += contribucion

    # ── Resultado final ──
    score_final = round(score_total, 1)
    nivel = clasificar_rotacion(score_final)

    confianza = "Alta" if fuentes_activas >= 5 else "Media" if fuentes_activas >= 3 else "Baja"
    confianza_detalle = f"{confianza} — {fuentes_activas}/6 fuentes activas"

    return {
        "score_rotacion": score_final,
        "nivel": nivel["nivel"],
        "descripcion_nivel": nivel["descripcion"],
        "desglose": desglose,
        "confianza": confianza_detalle,
        "fuentes_activas": fuentes_activas,
        "scores_parciales": {
            "noticias": score_noticias,
            "glassdoor": score_glassdoor if datos_glassdoor else None,
            "trends": score_trends if datos_trends else None,
            "ofertas": score_ofertas if datos_ofertas else None,
            "social": score_rrss if datos_social else None,
            "empleados": score_empleados,
        },
    }


def clasificar_rotacion(score: float) -> dict:
    if score < 25:
        return {"nivel": "Bajo", "descripcion": "Alta retención, empresa estable"}
    elif score < 50:
        return {"nivel": "Moderado", "descripcion": "Normal en la mayoría de industrias"}
    elif score < 75:
        return {"nivel": "Alto", "descripcion": "Señal de alerta, revisar causas"}
    else:
        return {"nivel": "Muy alto", "descripcion": "Problema estructural serio"}


def generar_tabla_resultados(df_financiero: pd.DataFrame,
                              noticias_por_empresa: dict,
                              trends_por_empresa: dict = None,
                              ofertas_por_empresa: dict = None,
                              social_por_empresa: dict = None,
                              glassdoor_por_empresa: dict = None) -> pd.DataFrame:
    """
    Genera la tabla final combinando todas las fuentes de datos (6 fuentes).
    """
    trends_por_empresa = trends_por_empresa or {}
    ofertas_por_empresa = ofertas_por_empresa or {}
    social_por_empresa = social_por_empresa or {}
    glassdoor_por_empresa = glassdoor_por_empresa or {}

    maximos = {
        "ingresos": df_financiero["ingresos_usd"].max() if "ingresos_usd" in df_financiero else 0,
        "market_cap": df_financiero["market_cap_usd"].max() if "market_cap_usd" in df_financiero else 0,
        "empleados": df_financiero["num_empleados"].max() if "num_empleados" in df_financiero else 0,
    }

    filas = []
    for _, row in df_financiero.iterrows():
        ticker = row["ticker"]

        idx_tamanio = calcular_indice_tamanio(row, maximos)

        datos_noticias = noticias_por_empresa.get(ticker, {})
        datos_trends = trends_por_empresa.get(ticker)
        datos_ofertas = ofertas_por_empresa.get(ticker)
        datos_social = social_por_empresa.get(ticker)
        datos_glassdoor = glassdoor_por_empresa.get(ticker)

        proxy = calcular_proxy_rotacion(
            row.to_dict(), datos_noticias,
            datos_trends, datos_ofertas, datos_social, datos_glassdoor
        )

        parciales = proxy.get("scores_parciales", {})

        filas.append({
            "Empresa": row["nombre"],
            "Ticker": ticker,
            "Sector": row.get("sector_config", row.get("sector", "")),
            "País": row.get("pais_config", row.get("pais", "")),
            "Ingresos (USD)": row.get("ingresos_usd"),
            "Market Cap (USD)": row.get("market_cap_usd"),
            "Empleados": row.get("num_empleados"),
            "Índice Tamaño": idx_tamanio,
            "Score Rotación": proxy["score_rotacion"],
            "Nivel Rotación": proxy["nivel"],
            "Score Noticias": parciales.get("noticias", 0),
            "Score Glassdoor": parciales.get("glassdoor"),
            "Score Trends": parciales.get("trends"),
            "Score Ofertas": parciales.get("ofertas"),
            "Score Social": parciales.get("social"),
            "Noticias Despidos": datos_noticias.get("score", {}).get("noticias_relevantes", 0),
            "Fuentes Activas": proxy["fuentes_activas"],
            "Confianza": proxy["confianza"],
        })

    return pd.DataFrame(filas)

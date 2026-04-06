"""
Recopilador de datos de Google Trends.
Mide el interés de búsqueda de "empresa layoffs" como proxy de rotación.
Usa pytrends (API no oficial de Google Trends).
"""

from pytrends.request import TrendReq
import time


def obtener_interes_layoffs(empresas: list, sleep_sec: float = 2.0) -> dict:
    """
    Consulta Google Trends para medir el interés de búsqueda de
    "[empresa] layoffs" en los últimos 12 meses.

    Args:
        empresas: lista de tuplas (nombre, ticker, sector, país)
        sleep_sec: pausa entre peticiones para no ser bloqueado

    Returns:
        dict con clave=ticker, valor=dict(interes_promedio, interes_max, score)
    """
    resultados = {}
    total = len(empresas)
    pytrends = TrendReq(hl="en-US", tz=360)

    for i, (nombre, ticker, sector, pais) in enumerate(empresas, 1):
        nombre_corto = _nombre_busqueda(nombre)
        keyword = f"{nombre_corto} layoffs"
        print(f"  [{i}/{total}] Google Trends: \"{keyword}\"...")

        try:
            pytrends.build_payload([keyword], timeframe="today 12-m", geo="")
            df = pytrends.interest_over_time()

            if df.empty or keyword not in df.columns:
                resultados[ticker] = {
                    "keyword": keyword,
                    "interes_promedio": 0,
                    "interes_max": 0,
                    "score": 0,
                    "error": None,
                }
            else:
                serie = df[keyword]
                promedio = float(serie.mean())
                maximo = float(serie.max())
                # Score: normalizado 0-100 (el valor de Trends ya es 0-100)
                score = min(100, int(promedio * 1.5 + maximo * 0.3))

                resultados[ticker] = {
                    "keyword": keyword,
                    "interes_promedio": round(promedio, 1),
                    "interes_max": int(maximo),
                    "score": score,
                    "error": None,
                }

        except Exception as e:
            resultados[ticker] = {
                "keyword": keyword,
                "interes_promedio": 0,
                "interes_max": 0,
                "score": 0,
                "error": str(e),
            }

        # Pausa para no ser bloqueado por Google
        if i < total:
            time.sleep(sleep_sec)

    return resultados


def _nombre_busqueda(nombre: str) -> str:
    """Extrae el nombre más reconocible para búsqueda en Trends."""
    import re
    # Si hay paréntesis, usar el contenido (ej: "Alphabet Inc. (Google)" → "Google")
    match = re.search(r'\(([^)]+)\)', nombre)
    if match:
        return match.group(1)
    # Limpiar sufijos corporativos
    for sufijo in ["Inc.", "Corp.", "Corporation", "Co., Ltd.", "Co.",
                    "Ltd.", "PLC", "S.A.", "AG", "SE", "N.V."]:
        nombre = nombre.replace(sufijo, "")
    return nombre.strip().split(",")[0].strip()

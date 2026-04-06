"""
Script principal — Informe de Rotación de Empleados en Grandes Multinacionales.
Fase 4: 6 fuentes de datos (Noticias + Trends + Ofertas + Social + Glassdoor + DB histórica).

Ejecutar:
    cd app
    python main.py                  # ejecución completa
    python main.py --skip-trends    # sin Google Trends (más rápido)
"""

import os
import sys
import time
import argparse

# Asegurar que el directorio app está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import EMPRESAS, KEYWORDS_DESPIDOS, MAX_NOTICIAS_POR_EMPRESA, OUTPUT_DIR
from data_finance import recopilar_todas_las_empresas
from data_news import recopilar_noticias_empresas
from data_jobs import estimar_ofertas_empleo
from data_social import analizar_sentimiento_rrss
from data_glassdoor import obtener_ratings_glassdoor
from estimator import generar_tabla_resultados
from report_generator import generar_informe_markdown, exportar_csv, exportar_excel
from pdf_generator import generar_pdf
from database import guardar_ejecucion, contar_ejecuciones


def main():
    parser = argparse.ArgumentParser(description="Informe de Rotación de Empleados")
    parser.add_argument("--skip-trends", action="store_true",
                        help="Omitir Google Trends (ahorra tiempo, requiere pytrends)")
    args = parser.parse_args()

    print("=" * 65)
    print("  INFORME DE ROTACIÓN DE EMPLEADOS — GRANDES MULTINACIONALES")
    print("  Fase 4: Análisis multi-fuente (6 fuentes)")
    print("=" * 65)
    print()

    inicio = time.time()
    total_pasos = 8 if not args.skip_trends else 7
    paso = 0

    # ── Paso 1: Datos financieros ────────────────────────────────────
    paso += 1
    print(f"📊 [{paso}/{total_pasos}] Recopilando datos financieros (Yahoo Finance)...")
    print()
    df_financiero = recopilar_todas_las_empresas(EMPRESAS)

    exitos = df_financiero["error"].isna().sum()
    print(f"\n  ✓ Datos obtenidos: {exitos}/{len(EMPRESAS)} empresas")
    print()

    # ── Paso 2: Noticias de despidos ─────────────────────────────────
    paso += 1
    print(f"📰 [{paso}/{total_pasos}] Buscando noticias de despidos y rotación...")
    print()
    noticias = recopilar_noticias_empresas(
        EMPRESAS, KEYWORDS_DESPIDOS, MAX_NOTICIAS_POR_EMPRESA
    )
    total_noticias = sum(
        n.get("score", {}).get("total_noticias", 0) for n in noticias.values()
    )
    print(f"\n  ✓ Total de noticias recopiladas: {total_noticias}")
    print()

    # ── Paso 3: Ofertas de empleo ────────────────────────────────────
    paso += 1
    print(f"💼 [{paso}/{total_pasos}] Analizando ofertas de empleo abiertas...")
    print()
    ofertas = estimar_ofertas_empleo(EMPRESAS)
    ofertas_total = sum(o.get("ofertas_relevantes", 0) for o in ofertas.values())
    print(f"\n  ✓ Ofertas relevantes detectadas: {ofertas_total}")
    print()

    # ── Paso 4: Sentimiento RRSS ─────────────────────────────────────
    paso += 1
    print(f"💬 [{paso}/{total_pasos}] Analizando sentimiento en medios/redes sociales...")
    print()
    social = analizar_sentimiento_rrss(EMPRESAS)
    neg_total = sum(s.get("menciones_negativas", 0) for s in social.values())
    pos_total = sum(s.get("menciones_positivas", 0) for s in social.values())
    print(f"\n  ✓ Menciones: {neg_total} negativas, {pos_total} positivas")
    print()

    # ── Paso 5: Google Trends (opcional) ─────────────────────────────
    trends = {}
    if not args.skip_trends:
        paso += 1
        print(f"📈 [{paso}/{total_pasos}] Consultando Google Trends (interés en layoffs)...")
        print()
        try:
            from data_trends import obtener_interes_layoffs
            trends = obtener_interes_layoffs(EMPRESAS)
            trends_ok = sum(1 for t in trends.values() if t.get("error") is None)
            print(f"\n  ✓ Datos de Trends obtenidos: {trends_ok}/{len(EMPRESAS)}")
        except ImportError:
            print("  ⚠️  pytrends no instalado. Ejecuta: pip install pytrends")
            print("     Continuando sin Google Trends...")
        except Exception as e:
            print(f"  ⚠️  Error en Google Trends: {e}")
            print("     Continuando sin Google Trends...")
        print()
    # ── Paso 6: Glassdoor ratings ──────────────────────────────
    paso += 1
    print(f"⭐ [{paso}/{total_pasos}] Buscando ratings de Glassdoor...")
    print()
    glassdoor = obtener_ratings_glassdoor(EMPRESAS)
    glassdoor_ok = sum(1 for g in glassdoor.values() if g.get("error") is None)
    print(f"\n  ✓ Ratings obtenidos: {glassdoor_ok}/{len(EMPRESAS)}")
    print()
    # ── Paso 6: Calcular estimaciones ────────────────────────────────
    paso += 1
    print(f"🧮 [{paso}/{total_pasos}] Calculando scores de rotación (6 fuentes)...")
    df_resultados = generar_tabla_resultados(
        df_financiero, noticias, trends, ofertas, social, glassdoor
    )
    print(f"  ✓ Tabla de resultados generada: {len(df_resultados)} empresas")
    print()

    # ── Paso 7: Guardar en DB y generar informes ─────────────────────
    paso += 1
    print(f"📝 [{paso}/{total_pasos}] Guardando datos y generando informes...")

    # Guardar en base de datos histórica
    ejecucion_previas = contar_ejecuciones()
    ejecucion_id = guardar_ejecucion(df_resultados)
    print(f"  ✓ Base de datos: ejecución #{ejecucion_id} guardada ({ejecucion_previas} anteriores)")

    ruta_md = generar_informe_markdown(df_resultados, noticias, OUTPUT_DIR)
    print(f"  ✓ Informe Markdown: {ruta_md}")

    ruta_csv = exportar_csv(df_resultados, OUTPUT_DIR)
    print(f"  ✓ Datos CSV: {ruta_csv}")

    ruta_excel = exportar_excel(df_resultados, OUTPUT_DIR)
    print(f"  ✓ Datos Excel: {ruta_excel}")

    ruta_pdf = generar_pdf(df_resultados, noticias, OUTPUT_DIR)
    print(f"  ✓ Informe PDF: {ruta_pdf}")

    # ── Resumen ──────────────────────────────────────────────────────
    duracion = time.time() - inicio
    print()
    print("=" * 65)
    print(f"  ✅ COMPLETADO en {duracion:.1f} segundos")
    print(f"  📁 Archivos generados en: {OUTPUT_DIR}")
    print("=" * 65)
    print()

    # Top 5 por rotación
    top5 = df_resultados.sort_values("Score Rotación", ascending=False).head(5)
    print("  🔝 Top 5 empresas con mayor score de rotación:")
    print()
    for i, (_, row) in enumerate(top5.iterrows(), 1):
        confianza = row.get("Confianza", "")
        print(f"     {i}. {row['Empresa']}: {row['Score Rotación']} "
              f"({row['Nivel Rotación']}) [{confianza}]")

    # Bottom 3
    bottom3 = df_resultados.sort_values("Score Rotación", ascending=True).head(3)
    print()
    print("  🟢 Top 3 empresas con mejor retención:")
    print()
    for i, (_, row) in enumerate(bottom3.iterrows(), 1):
        print(f"     {i}. {row['Empresa']}: {row['Score Rotación']} ({row['Nivel Rotación']})")
    print()


if __name__ == "__main__":
    main()

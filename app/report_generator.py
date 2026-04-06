"""
Generador de informes.
Crea el informe final en formato Markdown y CSV.
Opcionalmente exporta a HTML para visualización.
"""

import os
from datetime import datetime

import pandas as pd

from data_finance import formatear_numero


def generar_informe_markdown(df: pd.DataFrame, noticias: dict,
                              output_dir: str) -> str:
    """
    Genera un informe completo en Markdown.
    
    Args:
        df: DataFrame con los resultados consolidados
        noticias: dict con noticias por empresa
        output_dir: directorio de salida
    
    Returns:
        Ruta del archivo generado
    """
    os.makedirs(output_dir, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(output_dir, f"informe_rotacion_{fecha}.md")

    # Ordenar por score de rotación descendente
    df_sorted = df.sort_values("Score Rotación", ascending=False).reset_index(drop=True)

    lines = []
    lines.append("# Informe de Rotación de Empleados — Grandes Multinacionales")
    lines.append("")
    lines.append(f"> **Fecha de generación:** {fecha}")
    lines.append(f"> **Empresas analizadas:** {len(df)}")
    lines.append(f"> **Metodología:** Proxy-score multi-fuente (noticias + ofertas + RRSS + tendencias)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Resumen ejecutivo ──
    lines.append("## Resumen Ejecutivo")
    lines.append("")

    alto_o_muy_alto = df_sorted[df_sorted["Nivel Rotación"].isin(["Alto", "Muy alto"])]
    bajo = df_sorted[df_sorted["Nivel Rotación"] == "Bajo"]

    lines.append(f"- **{len(alto_o_muy_alto)}** empresas con indicadores de rotación **alto o muy alto**")
    lines.append(f"- **{len(bajo)}** empresas con indicadores de rotación **bajo** (alta retención)")
    lines.append(f"- Sectores más afectados: {_sectores_mas_afectados(df_sorted)}")
    lines.append("")

    # Confianza media
    fuentes_col = "Fuentes Activas"
    if fuentes_col in df_sorted.columns:
        media_fuentes = df_sorted[fuentes_col].mean()
        lines.append(f"- **Fuentes de datos activas (promedio):** {media_fuentes:.1f}/5")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Ranking ──
    lines.append("## Ranking por Score de Rotación")
    lines.append("")
    lines.append("| # | Empresa | Sector | Score | Nivel | Noticias | Glassdoor | Ofertas | Social | Trends | Empleados | Ingresos |")
    lines.append("|---|---------|--------|-------|-------|----------|-----------|---------|--------|--------|-----------|----------|")

    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        emoji = _emoji_nivel(row["Nivel Rotación"])
        s_not = row.get("Score Noticias", "—")
        s_gla = row.get("Score Glassdoor", "—") if row.get("Score Glassdoor") is not None else "—"
        s_ofe = row.get("Score Ofertas", "—") if row.get("Score Ofertas") is not None else "—"
        s_soc = row.get("Score Social", "—") if row.get("Score Social") is not None else "—"
        s_tre = row.get("Score Trends", "—") if row.get("Score Trends") is not None else "—"
        lines.append(
            f"| {i} | {row['Empresa']} | {row['Sector']} | "
            f"**{row['Score Rotación']}** | {emoji} {row['Nivel Rotación']} | "
            f"{s_not} | {s_gla} | {s_ofe} | {s_soc} | {s_tre} | "
            f"{_fmt_empleados(row['Empleados'])} | "
            f"{formatear_numero(row['Ingresos (USD)'])} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Detalle por empresa ──
    lines.append("## Detalle por Empresa")
    lines.append("")

    for _, row in df_sorted.iterrows():
        ticker = row["Ticker"]
        emoji = _emoji_nivel(row["Nivel Rotación"])
        lines.append(f"### {emoji} {row['Empresa']}")
        lines.append("")
        lines.append(f"| Dato | Valor |")
        lines.append(f"|------|-------|")
        lines.append(f"| **Ticker** | {ticker} |")
        lines.append(f"| **Sector** | {row['Sector']} |")
        lines.append(f"| **País** | {row['País']} |")
        lines.append(f"| **Empleados** | {_fmt_empleados(row['Empleados'])} |")
        lines.append(f"| **Ingresos** | {formatear_numero(row['Ingresos (USD)'])} |")
        lines.append(f"| **Market Cap** | {formatear_numero(row['Market Cap (USD)'])} |")
        lines.append(f"| **Índice Tamaño** | {row['Índice Tamaño']}/100 |")
        lines.append(f"| **Score Rotación** | **{row['Score Rotación']}/100** |")
        lines.append(f"| **Nivel** | {row['Nivel Rotación']} |")
        lines.append(f"| **Confianza** | {row.get('Confianza', 'N/D')} |")
        lines.append(f"| **Noticias de despidos encontradas** | {row['Noticias Despidos']} |")

        # Scores parciales
        s_not = row.get("Score Noticias", "—")
        s_gla = row.get("Score Glassdoor") if row.get("Score Glassdoor") is not None else "—"
        s_ofe = row.get("Score Ofertas") if row.get("Score Ofertas") is not None else "—"
        s_soc = row.get("Score Social") if row.get("Score Social") is not None else "—"
        s_tre = row.get("Score Trends") if row.get("Score Trends") is not None else "—"
        lines.append(f"| **Score Noticias** | {s_not}/100 |")
        lines.append(f"| **Score Glassdoor** | {s_gla}/100 |")
        lines.append(f"| **Score Ofertas** | {s_ofe}/100 |")
        lines.append(f"| **Score Social** | {s_soc}/100 |")
        lines.append(f"| **Score Trends** | {s_tre}/100 |")
        lines.append("")

        # Noticias destacadas
        datos_noticias = noticias.get(ticker, {})
        lista_noticias = datos_noticias.get("noticias", [])
        noticias_validas = [n for n in lista_noticias if not n.get("titulo", "").startswith("[ERROR]")]

        if noticias_validas:
            lines.append("**Noticias recientes:**")
            lines.append("")
            for n in noticias_validas[:5]:
                fecha_n = n.get("fecha", "s/f")
                lines.append(f"- [{n['titulo']}]({n['enlace']}) — {fecha_n}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # ── Metodología ──
    lines.append("## Metodología")
    lines.append("")
    lines.append("### Índice de Tamaño (0-100)")
    lines.append("Índice compuesto normalizado:")
    lines.append("- Ingresos anuales: 35%")
    lines.append("- Capitalización bursátil: 25%")
    lines.append("- Número de empleados: 25%")
    lines.append("- Presencia geográfica: 15% (pendiente)")
    lines.append("")
    lines.append("### Score de Rotación (0-100)")
    lines.append("Proxy-score combinando señales indirectas:")
    lines.append("- Ofertas abiertas / contratación masiva: 25% ✅")
    lines.append("- Noticias de despidos: 20% ✅")
    lines.append("- Rating Glassdoor (invertido): 15% ✅")
    lines.append("- Google Trends (interés en layoffs): 15% ✅")
    lines.append("- Variación interanual de empleados: 15% ✅ *(mejora con ejecuciones sucesivas)*")
    lines.append("- Sentimiento en medios/RRSS: 10% ✅")
    lines.append("")
    lines.append("### Fuentes de datos")
    lines.append("- **Financieros:** Yahoo Finance (vía yfinance)")
    lines.append("- **Noticias:** Google News RSS")
    lines.append("- **Glassdoor:** Ratings de empleados (vía búsqueda web)")
    lines.append("- **Ofertas de empleo:** Google News RSS (hiring, job openings)")
    lines.append("- **Sentimiento RRSS:** Google News RSS (workplace, burnout, strike)")
    lines.append("- **Tendencias:** Google Trends (pytrends)")
    lines.append("- **Histórico:** SQLite local (comparación entre ejecuciones)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*Informe generado automáticamente el {fecha}.*")

    contenido = "\n".join(lines)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(contenido)

    return filepath


def exportar_csv(df: pd.DataFrame, output_dir: str) -> str:
    """Exporta los resultados a CSV."""
    os.makedirs(output_dir, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(output_dir, f"datos_rotacion_{fecha}.csv")
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    return filepath


def exportar_excel(df: pd.DataFrame, output_dir: str) -> str:
    """Exporta los resultados a Excel (requiere openpyxl)."""
    os.makedirs(output_dir, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(output_dir, f"datos_rotacion_{fecha}.xlsx")
    try:
        df.to_excel(filepath, index=False, engine="openpyxl")
        return filepath
    except ImportError:
        print("  [!] openpyxl no instalado, exportando como CSV en su lugar.")
        return exportar_csv(df, output_dir)


# ── Helpers privados ─────────────────────────────────────────────────

def _emoji_nivel(nivel: str) -> str:
    return {
        "Bajo": "🟢",
        "Moderado": "🟡",
        "Alto": "🟠",
        "Muy alto": "🔴",
    }.get(nivel, "⚪")


def _fmt_empleados(valor) -> str:
    if valor is None or pd.isna(valor):
        return "N/D"
    valor = int(valor)
    if valor >= 1_000_000:
        return f"{valor / 1_000_000:.1f}M"
    if valor >= 1_000:
        return f"{valor / 1_000:.0f}K"
    return str(valor)


def _sectores_mas_afectados(df: pd.DataFrame) -> str:
    """Identifica los sectores con mayor score promedio de rotación."""
    if df.empty:
        return "N/D"
    por_sector = df.groupby("Sector")["Score Rotación"].mean().sort_values(ascending=False)
    top = por_sector.head(3)
    return ", ".join(f"{s} ({v:.0f})" for s, v in top.items())

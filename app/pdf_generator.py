"""
Generador de informe PDF profesional.
Crea un PDF descargable con portada, resumen ejecutivo, ranking,
graficos y detalle por empresa.
"""

import os
import math
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF

from data_finance import formatear_numero


# -- Colores ----------------------------------------------------------------
COLORES_NIVEL = {
    "Bajo": (46, 204, 113),
    "Moderado": (243, 156, 18),
    "Alto": (230, 126, 34),
    "Muy alto": (231, 76, 60),
}

COLOR_HEADER = (44, 62, 80)
COLOR_ACCENT = (52, 152, 219)
COLOR_BG_LIGHT = (236, 240, 241)

# Nombre de la fuente registrada (se usa en todo el módulo)
F = "PDFFont"


def _col(df, *keywords):
    """Busca una columna en el df que contenga todas las keywords."""
    for c in df.columns:
        if all(k.lower() in c.lower() for k in keywords):
            return c
    return None


def _find_font(names):
    """Busca un archivo de fuente TTF en el proyecto, matplotlib o el sistema."""
    search_dirs = []
    # Carpeta fonts/ dentro del propio proyecto (siempre disponible)
    project_fonts = os.path.join(os.path.dirname(__file__), "fonts")
    if os.path.isdir(project_fonts):
        search_dirs.append(project_fonts)
    # matplotlib ships DejaVuSans
    try:
        import matplotlib
        mpl_fonts = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
        if os.path.isdir(mpl_fonts):
            search_dirs.append(mpl_fonts)
    except Exception:
        pass
    # Windows
    windir = os.environ.get("WINDIR")
    if windir:
        search_dirs.append(os.path.join(windir, "Fonts"))
    # Linux
    for d in ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts")]:
        if os.path.isdir(d):
            search_dirs.append(d)
    # macOS
    for d in ["/Library/Fonts", "/System/Library/Fonts", os.path.expanduser("~/Library/Fonts")]:
        if os.path.isdir(d):
            search_dirs.append(d)

    for name in names:
        for d in search_dirs:
            path = os.path.join(d, name)
            if os.path.isfile(path):
                return path
            for root, _, files in os.walk(d):
                if name in files:
                    return os.path.join(root, name)
    return None


class InformePDF(FPDF):

    def __init__(self, fecha):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.fecha = fecha
        self.set_auto_page_break(auto=True, margin=20)
        self._font_name = self._registrar_fuente()
        global F
        F = self._font_name

    def _registrar_fuente(self):
        """Registra una fuente Unicode TTF, buscando en el sistema."""
        # Primero intentar fuentes bundled en app/fonts/
        fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
        bundled_regular = os.path.join(fonts_dir, "DejaVuSans.ttf")
        if os.path.isfile(bundled_regular):
            self.add_font("PDFFont", "", bundled_regular)
            self.add_font("PDFFont", "B", os.path.join(fonts_dir, "DejaVuSans-Bold.ttf"))
            self.add_font("PDFFont", "I", os.path.join(fonts_dir, "DejaVuSans-Oblique.ttf"))
            self.add_font("PDFFont", "BI", os.path.join(fonts_dir, "DejaVuSans-BoldOblique.ttf"))
            return "PDFFont"

        # Buscar en sistema
        regular = _find_font(["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"])
        bold = _find_font(["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"])
        italic = _find_font(["ariali.ttf", "Arial Italic.ttf", "DejaVuSans-Oblique.ttf"])
        bi = _find_font(["arialbi.ttf", "DejaVuSans-BoldOblique.ttf"])

        if regular:
            self.add_font("PDFFont", "", regular)
            self.add_font("PDFFont", "B", bold or regular)
            self.add_font("PDFFont", "I", italic or regular)
            self.add_font("PDFFont", "BI", bi or bold or regular)
            return "PDFFont"

        # Fallback: usar Helvetica (latin-1, no Unicode completo)
        return "Helvetica"

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font(F, "B", 9)
        self.set_text_color(*COLOR_HEADER)
        self.cell(0, 6, "Informe de Rotacion de Empleados - Grandes Multinacionales", align="L")
        self.cell(0, 6, self.fecha, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*COLOR_ACCENT)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font(F, "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")


def _s(text):
    """Safe string: limpia caracteres que Helvetica no soporta."""
    if text is None:
        return ""
    s = str(text)
    # Reemplazar caracteres Unicode problematicos
    s = s.replace("\u2014", "-")   # em dash
    s = s.replace("\u2013", "-")   # en dash
    s = s.replace("\u2018", "'")   # left single quote
    s = s.replace("\u2019", "'")   # right single quote
    s = s.replace("\u201c", '"')   # left double quote
    s = s.replace("\u201d", '"')   # right double quote
    s = s.replace("\u2026", "...")  # ellipsis
    s = s.replace("\u00a0", " ")   # non-breaking space
    s = s.replace("\u2022", "-")   # bullet
    # Fallback: reemplazar cualquier caracter fuera de latin-1
    try:
        s.encode("latin-1")
    except UnicodeEncodeError:
        s = s.encode("latin-1", errors="replace").decode("latin-1")
    return s


def generar_pdf(df, noticias, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    fecha = datetime.now().strftime("%Y-%m-%d")
    filepath = os.path.join(output_dir, f"informe_rotacion_{fecha}.pdf")

    sc = _col(df, "Score", "Rotaci") or "Score Rotacion"
    nc = _col(df, "Nivel", "Rotaci") or "Nivel Rotacion"
    ic = _col(df, "ndice", "Tama") or _col(df, "Indice", "Tama") or "Indice Tamano"

    df_sorted = df.sort_values(sc, ascending=False).reset_index(drop=True)

    pdf = InformePDF(fecha)
    pdf.alias_nb_pages()

    # PORTADA
    _portada(pdf, fecha, len(df))

    # RESUMEN EJECUTIVO
    pdf.add_page()
    _resumen(pdf, df_sorted, sc, nc)

    # GRAFICO RANKING
    chart_path = _chart_ranking(df_sorted, output_dir, sc, nc)
    pdf.add_page()
    pdf.set_font(F, "B", 14)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 10, "Ranking por Score de Rotacion", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.image(chart_path, x=10, w=190)

    # DISTRIBUCION + RADAR
    pie_path = _chart_pie(df_sorted, output_dir, nc)
    radar_path = _chart_radar(df_sorted, output_dir)

    pdf.add_page()
    pdf.set_font(F, "B", 14)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 10, "Distribucion y Desglose por Fuente", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.image(pie_path, x=10, y=pdf.get_y(), w=90)
    pdf.image(radar_path, x=105, y=pdf.get_y(), w=90)
    pdf.ln(85)

    # POR SECTOR
    sector_path = _chart_sector(df_sorted, output_dir, sc)
    pdf.ln(5)
    pdf.set_font(F, "B", 14)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 10, "Score Medio por Sector", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.image(sector_path, x=10, w=190)

    # TABLA RANKING
    pdf.add_page()
    _tabla(pdf, df_sorted, sc, nc)

    # DETALLE POR EMPRESA
    for _, row in df_sorted.iterrows():
        _ficha(pdf, row, noticias.get(row["Ticker"], {}), sc, nc, ic)

    # METODOLOGIA
    pdf.add_page()
    _metodologia(pdf)

    pdf.output(filepath)

    for tmp in [chart_path, pie_path, radar_path, sector_path]:
        if os.path.exists(tmp):
            os.remove(tmp)

    return filepath


# -- Portada -------------------------------------------------------------------

def _portada(pdf, fecha, total):
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font(F, "B", 28)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 15, "Informe de Rotacion", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 15, "de Empleados", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font(F, "", 16)
    pdf.set_text_color(*COLOR_ACCENT)
    pdf.cell(0, 10, "Grandes Multinacionales", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_draw_color(*COLOR_ACCENT)
    pdf.set_line_width(1)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(15)
    pdf.set_font(F, "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Fecha: {fecha}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Empresas analizadas: {total}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Metodologia: Proxy-score multi-fuente (6 fuentes)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font(F, "I", 10)
    pdf.cell(0, 6, "Fuentes: Yahoo Finance / Google News / Google Trends / Glassdoor / RRSS", align="C",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "Generado automaticamente", align="C", new_x="LMARGIN", new_y="NEXT")


# -- Resumen -------------------------------------------------------------------

def _resumen(pdf, df, sc, nc):
    pdf.set_font(F, "B", 18)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 12, "Resumen Ejecutivo", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    alto = len(df[df[nc].isin(["Alto", "Muy alto"])])
    moderado = len(df[df[nc] == "Moderado"])
    bajo = len(df[df[nc] == "Bajo"])
    media = df[sc].mean()

    kpis = [
        ("Score Medio", f"{media:.1f}/100"),
        ("Alta/Muy Alta", str(alto)),
        ("Moderada", str(moderado)),
        ("Baja", str(bajo)),
    ]

    x_start = 15
    box_w = 43
    y_base = pdf.get_y()
    for i, (label, value) in enumerate(kpis):
        x = x_start + i * (box_w + 3)
        pdf.set_fill_color(*COLOR_BG_LIGHT)
        pdf.rect(x, y_base, box_w, 22, style="F")
        pdf.set_xy(x, y_base + 2)
        pdf.set_font(F, "B", 16)
        pdf.set_text_color(*COLOR_ACCENT)
        pdf.cell(box_w, 10, value, align="C")
        pdf.set_xy(x, y_base + 12)
        pdf.set_font(F, "", 8)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(box_w, 6, label, align="C")

    pdf.set_y(y_base + 30)

    # Top 5
    pdf.set_font(F, "B", 12)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 8, "Top 5 - Mayor score de rotacion:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(F, "", 10)
    for i, (_, row) in enumerate(df.head(5).iterrows(), 1):
        color = COLORES_NIVEL.get(row[nc], (100, 100, 100))
        pdf.set_text_color(*color)
        pdf.cell(8, 6, f"{i}.")
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 6, f'{_s(row["Empresa"])} - {row[sc]}/100 ({row[nc]})',
                 new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    pdf.set_font(F, "B", 12)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 8, "Top 3 - Mejor retencion:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(F, "", 10)
    for i, (_, row) in enumerate(df.tail(3).iloc[::-1].iterrows(), 1):
        color = COLORES_NIVEL.get(row[nc], (100, 100, 100))
        pdf.set_text_color(*color)
        pdf.cell(8, 6, f"{i}.")
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 6, f'{_s(row["Empresa"])} - {row[sc]}/100 ({row[nc]})',
                 new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    por_sector = df.groupby("Sector")[sc].mean().sort_values(ascending=False).head(3)
    pdf.set_font(F, "B", 12)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 8, "Sectores con mayor indicador de rotacion:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(F, "", 10)
    pdf.set_text_color(60, 60, 60)
    for sector, score in por_sector.items():
        pdf.cell(0, 6, f"  - {sector}: {score:.1f}/100", new_x="LMARGIN", new_y="NEXT")


# -- Tabla ranking -------------------------------------------------------------

def _tabla(pdf, df, sc, nc):
    pdf.set_font(F, "B", 14)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 10, "Ranking Completo", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    cols = ["#", "Empresa", "Sector", "Score", "Nivel", "Empleados"]
    widths = [8, 55, 40, 18, 22, 25]

    pdf.set_font(F, "B", 8)
    pdf.set_fill_color(*COLOR_HEADER)
    pdf.set_text_color(255, 255, 255)
    for col, w in zip(cols, widths):
        pdf.cell(w, 7, col, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font(F, "", 8)
    for i, (_, row) in enumerate(df.iterrows(), 1):
        color = COLORES_NIVEL.get(row[nc], (100, 100, 100))
        pdf.set_fill_color(245, 245, 245) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(widths[0], 6, str(i), border=1, fill=True, align="C")
        pdf.cell(widths[1], 6, _trunc(_s(row["Empresa"]), 30), border=1, fill=True)
        pdf.cell(widths[2], 6, _trunc(_s(row["Sector"]), 22), border=1, fill=True)
        pdf.set_text_color(*color)
        pdf.set_font(F, "B", 8)
        pdf.cell(widths[3], 6, f'{row[sc]:.1f}', border=1, fill=True, align="C")
        pdf.cell(widths[4], 6, _s(row[nc]), border=1, fill=True, align="C")
        pdf.set_text_color(60, 60, 60)
        pdf.set_font(F, "", 8)
        pdf.cell(widths[5], 6, _fmt_emp(row.get("Empleados")), border=1, fill=True, align="C")
        pdf.ln()

    # Segunda tabla: scores por fuente
    pdf.ln(5)
    pdf.set_font(F, "B", 12)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 8, "Detalle de Scores por Fuente", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    src_cols = ["Score Noticias", "Score Glassdoor", "Score Ofertas", "Score Trends", "Score Social"]
    src_labels = ["Empresa", "Noticias", "Glassdoor", "Ofertas", "Trends", "Social"]
    src_w = [55, 22, 22, 22, 22, 22]

    pdf.set_font(F, "B", 8)
    pdf.set_fill_color(*COLOR_HEADER)
    pdf.set_text_color(255, 255, 255)
    for col, w in zip(src_labels, src_w):
        pdf.cell(w, 7, col, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font(F, "", 8)
    for i, (_, row) in enumerate(df.iterrows(), 1):
        pdf.set_fill_color(245, 245, 245) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(src_w[0], 6, _trunc(_s(row["Empresa"]), 30), border=1, fill=True)
        for col_name in src_cols:
            val = row.get(col_name)
            txt = f"{val:.0f}" if val is not None and not pd.isna(val) else "-"
            pdf.cell(src_w[1], 6, txt, border=1, fill=True, align="C")
        pdf.ln()


# -- Ficha empresa -------------------------------------------------------------

def _ficha(pdf, row, datos_noticias, sc, nc, ic):
    if pdf.get_y() > 220:
        pdf.add_page()

    color = COLORES_NIVEL.get(row[nc], (100, 100, 100))
    pdf.set_draw_color(*COLOR_BG_LIGHT)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font(F, "B", 12)
    pdf.set_text_color(*color)
    pdf.cell(0, 8, _s(row["Empresa"]), new_x="LMARGIN", new_y="NEXT")

    # Buscar columna pais
    pais_col = None
    for c in row.index:
        if "pais" in c.lower() or "pa\u00eds" in c.lower():
            pais_col = c
            break

    left = [
        ("Sector", _s(row["Sector"])),
        ("Pais", _s(row.get(pais_col, "N/D")) if pais_col else "N/D"),
        ("Empleados", _fmt_emp(row.get("Empleados"))),
        ("Ingresos", formatear_numero(row.get("Ingresos (USD)"))),
    ]

    idx_val = row.get(ic, "N/D") if ic else "N/D"
    right = [
        ("Score", f'{row[sc]:.1f}/100'),
        ("Nivel", _s(row[nc])),
        ("Confianza", _s(row.get("Confianza", "N/D"))),
        ("Ind. Tamano", f'{idx_val}/100' if idx_val != "N/D" else "N/D"),
    ]

    y0 = pdf.get_y()
    pdf.set_text_color(60, 60, 60)
    for label, value in left:
        pdf.set_font(F, "B", 8)
        pdf.cell(25, 5, f"{label}:")
        pdf.set_font(F, "", 8)
        pdf.cell(65, 5, _s(value), new_x="LMARGIN", new_y="NEXT")
    y1 = pdf.get_y()

    pdf.set_y(y0)
    for label, value in right:
        pdf.set_x(105)
        pdf.set_font(F, "B", 8)
        pdf.cell(25, 5, f"{label}:")
        pdf.set_font(F, "", 8)
        pdf.cell(60, 5, _s(value), new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(max(y1, pdf.get_y()))

    # Noticias destacadas
    nots = datos_noticias.get("noticias", [])
    validas = [n for n in nots if not n.get("titulo", "").startswith("[ERROR]")]
    if validas:
        pdf.set_font(F, "I", 8)
        pdf.set_text_color(100, 100, 100)
        for n in validas[:3]:
            pdf.cell(0, 4, f"- {_trunc(_s(n['titulo']), 90)}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)


# -- Metodologia ---------------------------------------------------------------

def _metodologia(pdf):
    pdf.set_font(F, "B", 18)
    pdf.set_text_color(*COLOR_HEADER)
    pdf.cell(0, 12, "Metodologia", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    secciones = [
        ("Score de Rotacion (0-100)",
         "Proxy-score que combina 6 fuentes de datos indirectas:\n"
         "  - Ofertas empleo abiertas: 25%\n"
         "  - Noticias de despidos: 20%\n"
         "  - Rating Glassdoor (invertido): 15%\n"
         "  - Google Trends (interes en layoffs): 15%\n"
         "  - Variacion interanual de empleados: 15%\n"
         "  - Sentimiento en medios/RRSS: 10%"),
        ("Indice de Tamano (0-100)",
         "Indice compuesto normalizado:\n"
         "  - Ingresos anuales: 35%\n"
         "  - Capitalizacion bursatil: 25%\n"
         "  - Numero de empleados: 25%\n"
         "  - Presencia geografica: 15%"),
        ("Fuentes de datos",
         "  - Yahoo Finance (datos financieros)\n"
         "  - Google News RSS (noticias, ofertas, sentimiento)\n"
         "  - Glassdoor (ratings de empleados)\n"
         "  - Google Trends (interes de busqueda)\n"
         "  - SQLite local (historico entre ejecuciones)"),
        ("Niveles de rotacion",
         "  - Bajo (< 25): Alta retencion\n"
         "  - Moderado (25-50): Normal\n"
         "  - Alto (50-75): Senal de alerta\n"
         "  - Muy alto (>= 75): Problema estructural"),
    ]

    for titulo, contenido in secciones:
        pdf.set_font(F, "B", 11)
        pdf.set_text_color(*COLOR_HEADER)
        pdf.cell(0, 8, titulo, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(F, "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5, contenido)
        pdf.ln(3)

    pdf.ln(10)
    pdf.set_font(F, "I", 9)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 6, f"Informe generado automaticamente el {datetime.now().strftime('%Y-%m-%d %H:%M')}.",
             align="C", new_x="LMARGIN", new_y="NEXT")


# -- Graficos ------------------------------------------------------------------

def _chart_ranking(df, output_dir, sc, nc):
    fig, ax = plt.subplots(figsize=(10, max(5, len(df) * 0.35)))
    df_plot = df.sort_values(sc, ascending=True)
    colors = [tuple(c / 255 for c in COLORES_NIVEL.get(n, (150, 150, 150))) for n in df_plot[nc]]
    bars = ax.barh(range(len(df_plot)), df_plot[sc], color=colors, height=0.7)
    ax.set_yticks(range(len(df_plot)))
    ax.set_yticklabels(df_plot["Empresa"], fontsize=8)
    ax.set_xlabel("Score de Rotacion (0-100)", fontsize=9)
    ax.set_xlim(0, 105)
    ax.grid(axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, score in zip(bars, df_plot[sc]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{score:.1f}", va="center", fontsize=7, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(output_dir, "_tmp_ranking.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _chart_pie(df, output_dir, nc):
    conteo = df[nc].value_counts()
    labels = conteo.index.tolist()
    sizes = conteo.values.tolist()
    colors = [tuple(c / 255 for c in COLORES_NIVEL.get(n, (150, 150, 150))) for n in labels]
    fig, ax = plt.subplots(figsize=(5, 4))
    _, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%",
                                  startangle=90, textprops={"fontsize": 9})
    for t in autotexts:
        t.set_fontweight("bold")
        t.set_fontsize(10)
    ax.set_title("Distribucion por Nivel", fontsize=11, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(output_dir, "_tmp_pie.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _chart_radar(df, output_dir):
    fuentes = ["Score Noticias", "Score Glassdoor", "Score Ofertas", "Score Trends", "Score Social"]
    labels = ["Noticias", "Glassdoor", "Ofertas", "Trends", "Social"]
    values = []
    for f in fuentes:
        if f in df.columns:
            col = df[f].dropna()
            values.append(col.mean() if len(col) > 0 else 0)
        else:
            values.append(0)
    values_c = values + [values[0]]
    angles = [n / len(labels) * 2 * math.pi for n in range(len(labels))]
    angles_c = angles + [angles[0]]
    fig, ax = plt.subplots(figsize=(5, 4), subplot_kw=dict(polar=True))
    ax.fill(angles_c, values_c, alpha=0.25, color="steelblue")
    ax.plot(angles_c, values_c, "o-", color="steelblue", linewidth=2)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_title("Score Promedio por Fuente", fontsize=11, fontweight="bold", pad=15)
    plt.tight_layout()
    path = os.path.join(output_dir, "_tmp_radar.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _chart_sector(df, output_dir, sc):
    por_sector = df.groupby("Sector")[sc].mean().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(10, max(3, len(por_sector) * 0.4)))
    colors = []
    for score in por_sector.values:
        if score >= 75:
            colors.append(tuple(c / 255 for c in COLORES_NIVEL["Muy alto"]))
        elif score >= 50:
            colors.append(tuple(c / 255 for c in COLORES_NIVEL["Alto"]))
        elif score >= 25:
            colors.append(tuple(c / 255 for c in COLORES_NIVEL["Moderado"]))
        else:
            colors.append(tuple(c / 255 for c in COLORES_NIVEL["Bajo"]))
    bars = ax.barh(range(len(por_sector)), por_sector.values, color=colors, height=0.6)
    ax.set_yticks(range(len(por_sector)))
    ax.set_yticklabels(por_sector.index, fontsize=8)
    ax.set_xlabel("Score Medio de Rotacion", fontsize=9)
    ax.set_xlim(0, 105)
    ax.grid(axis="x", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for bar, score in zip(bars, por_sector.values):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{score:.1f}", va="center", fontsize=8, fontweight="bold")
    plt.tight_layout()
    path = os.path.join(output_dir, "_tmp_sector.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# -- Helpers -------------------------------------------------------------------

def _trunc(texto, max_len):
    if not texto:
        return ""
    if len(texto) <= max_len:
        return texto
    return texto[:max_len - 3] + "..."


def _fmt_emp(valor):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "N/D"
    valor = int(valor)
    if valor >= 1_000_000:
        return f"{valor / 1_000_000:.1f}M"
    if valor >= 1_000:
        return f"{valor / 1_000:.0f}K"
    return str(valor)

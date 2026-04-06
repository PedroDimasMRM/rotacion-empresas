"""
Dashboard interactivo — Informe de Rotación de Empleados.
Fase 3: Visualización con Streamlit.

Ejecutar:
    cd app
    streamlit run dashboard.py
"""

import os
import sys
import sqlite3
import time
import io

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Path setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATA_DIR, EMPRESAS, PESOS_ROTACION, KEYWORDS_DESPIDOS, MAX_NOTICIAS_POR_EMPRESA, OUTPUT_DIR
from database import DB_PATH, inicializar_db

# ── Configuración de página ──────────────────────────────────────────
st.set_page_config(
    page_title="Rotación Multinacionales",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Funciones de carga de datos ──────────────────────────────────────

@st.cache_data(ttl=60)
def cargar_ultima_ejecucion() -> pd.DataFrame:
    """Carga los datos de la última ejecución desde SQLite."""
    inicializar_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT d.*, e.fecha as fecha_ejecucion
        FROM datos_empresa d
        JOIN ejecuciones e ON d.ejecucion_id = e.id
        WHERE d.ejecucion_id = (SELECT MAX(id) FROM ejecuciones)
        ORDER BY d.score_rotacion DESC
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=60)
def cargar_historico_completo() -> pd.DataFrame:
    """Carga todo el histórico de ejecuciones."""
    inicializar_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("""
        SELECT d.*, e.fecha as fecha_ejecucion, e.id as ej_id
        FROM datos_empresa d
        JOIN ejecuciones e ON d.ejecucion_id = e.id
        ORDER BY e.fecha, d.nombre
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=60)
def cargar_ejecuciones() -> pd.DataFrame:
    inicializar_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM ejecuciones ORDER BY fecha DESC", conn)
    conn.close()
    return df


def color_nivel(nivel):
    return {
        "Bajo": "#2ecc71",
        "Moderado": "#f39c12",
        "Alto": "#e67e22",
        "Muy alto": "#e74c3c",
    }.get(nivel, "#95a5a6")


def emoji_nivel(nivel):
    return {"Bajo": "🟢", "Moderado": "🟡", "Alto": "🟠", "Muy alto": "🔴"}.get(nivel, "⚪")


def ejecutar_analisis(usar_trends: bool = True):
    """Ejecuta el análisis completo y devuelve (df_resultados, noticias, ruta_pdf)."""
    from data_finance import recopilar_todas_las_empresas
    from data_news import recopilar_noticias_empresas
    from data_jobs import estimar_ofertas_empleo
    from data_social import analizar_sentimiento_rrss
    from data_glassdoor import obtener_ratings_glassdoor
    from estimator import generar_tabla_resultados
    from report_generator import generar_informe_markdown, exportar_csv, exportar_excel
    from pdf_generator import generar_pdf
    from database import guardar_ejecucion

    progress = st.progress(0, text="Iniciando análisis...")

    progress.progress(5, text="📊 Recopilando datos financieros (Yahoo Finance)...")
    df_financiero = recopilar_todas_las_empresas(EMPRESAS)

    progress.progress(20, text="📰 Buscando noticias de despidos...")
    noticias = recopilar_noticias_empresas(EMPRESAS, KEYWORDS_DESPIDOS, MAX_NOTICIAS_POR_EMPRESA)

    progress.progress(35, text="💼 Analizando ofertas de empleo...")
    ofertas = estimar_ofertas_empleo(EMPRESAS)

    progress.progress(50, text="💬 Analizando sentimiento en medios/RRSS...")
    social = analizar_sentimiento_rrss(EMPRESAS)

    trends = {}
    if usar_trends:
        progress.progress(60, text="📈 Consultando Google Trends...")
        try:
            from data_trends import obtener_interes_layoffs
            trends = obtener_interes_layoffs(EMPRESAS)
        except Exception:
            pass

    progress.progress(75, text="⭐ Obteniendo ratings de Glassdoor...")
    glassdoor = obtener_ratings_glassdoor(EMPRESAS)

    progress.progress(85, text="🧮 Calculando scores de rotación...")
    df_resultados = generar_tabla_resultados(
        df_financiero, noticias, trends, ofertas, social, glassdoor
    )

    progress.progress(90, text="💾 Guardando en base de datos...")
    guardar_ejecucion(df_resultados)

    progress.progress(93, text="📝 Generando informes MD/CSV/Excel...")
    generar_informe_markdown(df_resultados, noticias, OUTPUT_DIR)
    exportar_csv(df_resultados, OUTPUT_DIR)
    exportar_excel(df_resultados, OUTPUT_DIR)

    progress.progress(96, text="📄 Generando informe PDF...")
    ruta_pdf = generar_pdf(df_resultados, noticias, OUTPUT_DIR)

    progress.progress(100, text="✅ Análisis completado")
    time.sleep(0.5)
    progress.empty()

    return df_resultados, noticias, ruta_pdf


# ── App principal ────────────────────────────────────────────────────

def main():
    # ── Sidebar: Ejecutar análisis ───────────────────────────────────
    with st.sidebar:
        st.title("📊 Panel de Control")
        st.markdown("---")

        st.subheader("🚀 Ejecutar Análisis")
        usar_trends = st.checkbox("Incluir Google Trends", value=True,
                                  help="Añade ~1 min extra pero mejora la precisión")

        if st.button("▶️ Ejecutar análisis ahora", type="primary", use_container_width=True):
            with st.spinner("Ejecutando análisis completo..."):
                _, _, ruta_pdf = ejecutar_analisis(usar_trends)
            st.success("✅ Análisis completado")
            # Guardar ruta del PDF en session_state
            st.session_state["ultimo_pdf"] = ruta_pdf
            # Limpiar cache para recargar datos
            cargar_ultima_ejecucion.clear()
            cargar_historico_completo.clear()
            cargar_ejecuciones.clear()
            st.rerun()

        # Botón de descarga PDF
        pdf_path = st.session_state.get("ultimo_pdf")
        if pdf_path is None:
            # Buscar el PDF más reciente en output
            if os.path.exists(OUTPUT_DIR):
                pdfs = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".pdf")], reverse=True)
                if pdfs:
                    pdf_path = os.path.join(OUTPUT_DIR, pdfs[0])

        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "📥 Descargar informe PDF",
                    data=f.read(),
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf",
                    use_container_width=True,
                )

        st.markdown("---")

    # Verificar que hay datos
    ejecuciones = cargar_ejecuciones()
    if ejecuciones.empty:
        st.title("🏢 Rotación de Empleados — Grandes Multinacionales")
        st.info("👋 **Bienvenido.** No hay datos todavía. Pulsa **▶️ Ejecutar análisis ahora** en la barra lateral para iniciar el primer análisis.")
        return

    df = cargar_ultima_ejecucion()
    if df.empty:
        st.error("No se encontraron datos en la última ejecución.")
        return

    # ── Sidebar: Filtros ─────────────────────────────────────────────
    with st.sidebar:

        # Filtro por sector
        sectores = ["Todos"] + sorted(df["sector"].dropna().unique().tolist())
        sector_sel = st.selectbox("🏭 Filtrar por sector", sectores)

        # Filtro por país
        paises = ["Todos"] + sorted(df["pais"].dropna().unique().tolist())
        pais_sel = st.selectbox("🌍 Filtrar por país", paises)

        # Filtro por nivel
        niveles = ["Todos", "Bajo", "Moderado", "Alto", "Muy alto"]
        nivel_sel = st.selectbox("🎯 Filtrar por nivel de rotación", niveles)

        st.markdown("---")
        st.caption(f"📅 Última ejecución: {df['fecha_ejecucion'].iloc[0]}")
        st.caption(f"🔄 Total ejecuciones: {len(ejecuciones)}")
        st.caption(f"🏢 Empresas: {len(df)}")

    # Aplicar filtros
    df_filtrado = df.copy()
    if sector_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["sector"] == sector_sel]
    if pais_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["pais"] == pais_sel]
    if nivel_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["nivel_rotacion"] == nivel_sel]

    # ── Header ───────────────────────────────────────────────────────
    st.title("🏢 Rotación de Empleados — Grandes Multinacionales")
    st.markdown("Dashboard interactivo con datos en vivo de Yahoo Finance, Google News, Google Trends y análisis de RRSS.")

    # ── KPIs ─────────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)

    score_medio = df_filtrado["score_rotacion"].mean()
    alto_count = len(df_filtrado[df_filtrado["nivel_rotacion"].isin(["Alto", "Muy alto"])])
    bajo_count = len(df_filtrado[df_filtrado["nivel_rotacion"] == "Bajo"])
    total_empleados = df_filtrado["num_empleados"].sum()
    empresas_count = len(df_filtrado)

    col1.metric("📊 Score Medio", f"{score_medio:.1f}/100")
    col2.metric("🔴 Rotación Alta/Muy Alta", f"{alto_count}")
    col3.metric("🟢 Rotación Baja", f"{bajo_count}")
    col4.metric("👥 Total Empleados", _fmt_num(total_empleados))
    col5.metric("🏢 Empresas", f"{empresas_count}")

    st.markdown("---")

    # ── Gráficos principales ─────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Ranking", "🔍 Desglose por fuente", "📈 Comparativa",
        "🗺️ Por sector/país", "📜 Histórico"
    ])

    # ── TAB 1: Ranking ───────────────────────────────────────────────
    with tab1:
        st.subheader("Ranking por Score de Rotación")

        # Gráfico de barras horizontal
        df_rank = df_filtrado.sort_values("score_rotacion", ascending=True)
        colors = [color_nivel(n) for n in df_rank["nivel_rotacion"]]

        fig_rank = go.Figure(go.Bar(
            x=df_rank["score_rotacion"],
            y=df_rank["nombre"],
            orientation="h",
            marker_color=colors,
            text=df_rank["score_rotacion"].apply(lambda x: f"{x:.1f}"),
            textposition="outside",
        ))
        fig_rank.update_layout(
            height=max(400, len(df_rank) * 35),
            xaxis_title="Score de Rotación (0-100)",
            yaxis_title="",
            xaxis=dict(range=[0, 105]),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_rank, key="rank_chart")

        # Tabla detallada
        st.subheader("📋 Tabla detallada")
        df_tabla = df_filtrado[[
            "nombre", "sector", "pais", "score_rotacion", "nivel_rotacion",
            "num_empleados", "ingresos_usd", "market_cap_usd",
            "score_noticias", "score_glassdoor", "score_trends", "score_ofertas", "score_social",
        ]].copy()
        df_tabla.columns = [
            "Empresa", "Sector", "País", "Score", "Nivel",
            "Empleados", "Ingresos", "Market Cap",
            "📰 Noticias", "⭐ Glassdoor", "📈 Trends", "💼 Ofertas", "💬 Social",
        ]
        df_tabla = df_tabla.sort_values("Score", ascending=False).reset_index(drop=True)
        df_tabla.index += 1

        st.dataframe(
            df_tabla,
            height=min(700, len(df_tabla) * 38 + 40),
            width="stretch",
        )

    # ── TAB 2: Desglose por fuente ───────────────────────────────────
    with tab2:
        st.subheader("Desglose de Score por Fuente de Datos")

        # Selector de empresa
        empresa_sel = st.selectbox(
            "Selecciona empresa:",
            df_filtrado["nombre"].tolist(),
            key="empresa_desglose"
        )

        empresa_row = df_filtrado[df_filtrado["nombre"] == empresa_sel].iloc[0]

        col_a, col_b = st.columns([1, 2])

        with col_a:
            st.markdown(f"### {emoji_nivel(empresa_row['nivel_rotacion'])} {empresa_sel}")
            st.metric("Score Total", f"{empresa_row['score_rotacion']:.1f}/100")
            st.metric("Nivel", empresa_row["nivel_rotacion"])
            st.metric("Empleados", _fmt_num(empresa_row.get("num_empleados")))
            st.metric("Sector", empresa_row["sector"])

        with col_b:
            # Radar chart de fuentes
            categorias = ["Noticias", "Glassdoor", "Ofertas", "Trends", "Social"]
            valores = [
                empresa_row.get("score_noticias", 0) or 0,
                empresa_row.get("score_glassdoor", 0) or 0,
                empresa_row.get("score_ofertas", 0) or 0,
                empresa_row.get("score_trends", 0) or 0,
                empresa_row.get("score_social", 0) or 0,
            ]

            fig_radar = go.Figure(go.Scatterpolar(
                r=valores + [valores[0]],
                theta=categorias + [categorias[0]],
                fill="toself",
                fillcolor="rgba(231, 76, 60, 0.2)",
                line_color=color_nivel(empresa_row["nivel_rotacion"]),
                name=empresa_sel,
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                height=400,
                margin=dict(l=60, r=60, t=30, b=30),
            )
            st.plotly_chart(fig_radar, key="radar_chart")

        # Barras de cada componente
        st.markdown("#### Contribución de cada fuente")
        pesos = {
            "📰 Noticias despidos": ("score_noticias", PESOS_ROTACION["noticias_despidos"]),
            "💼 Ofertas empleo": ("score_ofertas", PESOS_ROTACION["ofertas_vs_empleados"]),
            "⭐ Rating Glassdoor": ("score_glassdoor", PESOS_ROTACION["rating_glassdoor"]),
            "📈 Google Trends": ("score_trends", PESOS_ROTACION["google_trends"]),
            "👥 Var. empleados": (None, PESOS_ROTACION["crecimiento_empleados"]),
            "💬 Sentimiento RRSS": ("score_social", PESOS_ROTACION["sentimiento_rrss"]),
        }

        for label, (col_name, peso) in pesos.items():
            score_raw = empresa_row.get(col_name, 50) if col_name else 50
            score_raw = score_raw if score_raw is not None else 50
            contribucion = score_raw * peso
            st.progress(min(int(score_raw), 100), text=f"{label}: {score_raw:.0f}/100 × {peso:.0%} = **{contribucion:.1f}**")

    # ── TAB 3: Comparativa ───────────────────────────────────────────
    with tab3:
        st.subheader("Comparativa entre empresas")

        # Scatter: Score Rotación vs Tamaño
        df_scatter = df_filtrado.dropna(subset=["num_empleados"]).copy()
        if df_scatter.empty:
            st.info("No hay datos suficientes para el scatter plot.")
        else:
            fig_scatter = px.scatter(
                df_scatter,
                x="indice_tamanio",
                y="score_rotacion",
                color="nivel_rotacion",
                size="num_empleados",
                hover_name="nombre",
                hover_data=["sector", "pais", "score_noticias", "score_glassdoor", "score_trends"],
                color_discrete_map={
                    "Bajo": "#2ecc71", "Moderado": "#f39c12",
                    "Alto": "#e67e22", "Muy alto": "#e74c3c",
                },
                labels={
                    "indice_tamanio": "Índice de Tamaño (0-100)",
                    "score_rotacion": "Score de Rotación (0-100)",
                    "nivel_rotacion": "Nivel",
                    "num_empleados": "Empleados",
                },
            )
            fig_scatter.update_layout(height=500)
            st.plotly_chart(fig_scatter, key="scatter_chart")

        # Heatmap de scores por empresa y fuente
        st.subheader("Mapa de calor: Scores por fuente")
        df_heat = df_filtrado[["nombre", "score_noticias", "score_glassdoor", "score_ofertas",
                                "score_trends", "score_social"]].copy()
        df_heat = df_heat.set_index("nombre")
        df_heat.columns = ["📰 Noticias", "⭐ Glassdoor", "💼 Ofertas", "📈 Trends", "💬 Social"]
        df_heat = df_heat.fillna(0).sort_index()

        fig_heat = px.imshow(
            df_heat,
            color_continuous_scale="RdYlGn_r",
            aspect="auto",
            labels=dict(color="Score"),
            zmin=0, zmax=100,
        )
        fig_heat.update_layout(height=max(400, len(df_heat) * 30))
        st.plotly_chart(fig_heat, key="heat_chart")

    # ── TAB 4: Por sector/país ───────────────────────────────────────
    with tab4:
        col_s, col_p = st.columns(2)

        with col_s:
            st.subheader("Score medio por sector")
            df_sector = df_filtrado.groupby("sector").agg(
                score_medio=("score_rotacion", "mean"),
                empresas=("nombre", "count"),
                empleados=("num_empleados", "sum"),
            ).sort_values("score_medio", ascending=False).reset_index()

            fig_sector = px.bar(
                df_sector, x="score_medio", y="sector",
                orientation="h", color="score_medio",
                color_continuous_scale="RdYlGn_r",
                text="score_medio",
                range_color=[0, 100],
            )
            fig_sector.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig_sector.update_layout(
                height=max(300, len(df_sector) * 45),
                xaxis=dict(range=[0, 105]),
                yaxis_title="",
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_sector)

        with col_p:
            st.subheader("Score medio por país")
            df_pais = df_filtrado.groupby("pais").agg(
                score_medio=("score_rotacion", "mean"),
                empresas=("nombre", "count"),
            ).sort_values("score_medio", ascending=False).reset_index()

            fig_pais = px.bar(
                df_pais, x="score_medio", y="pais",
                orientation="h", color="score_medio",
                color_continuous_scale="RdYlGn_r",
                text="score_medio",
                range_color=[0, 100],
            )
            fig_pais.update_traces(texttemplate="%{text:.1f}", textposition="outside")
            fig_pais.update_layout(
                height=max(300, len(df_pais) * 45),
                xaxis=dict(range=[0, 105]),
                yaxis_title="",
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_pais)

        # Pie chart distribución de niveles
        st.subheader("Distribución de niveles de rotación")
        df_niveles = df_filtrado["nivel_rotacion"].value_counts().reset_index()
        df_niveles.columns = ["Nivel", "Empresas"]
        fig_pie = px.pie(
            df_niveles, values="Empresas", names="Nivel",
            color="Nivel",
            color_discrete_map={
                "Bajo": "#2ecc71", "Moderado": "#f39c12",
                "Alto": "#e67e22", "Muy alto": "#e74c3c",
            },
        )
        fig_pie.update_layout(height=350)
        st.plotly_chart(fig_pie)

    # ── TAB 5: Histórico ─────────────────────────────────────────────
    with tab5:
        st.subheader("Evolución histórica (entre ejecuciones)")

        df_hist = cargar_historico_completo()
        if len(df_hist["ej_id"].unique()) > 1:
            # Selección de empresas para comparar
            empresas_hist = st.multiselect(
                "Empresas a comparar:",
                df_hist["nombre"].unique().tolist(),
                default=df_hist.sort_values("score_rotacion", ascending=False)["nombre"].unique()[:5].tolist(),
            )

            if empresas_hist:
                df_hist_sel = df_hist[df_hist["nombre"].isin(empresas_hist)]
                fig_hist = px.line(
                    df_hist_sel, x="fecha_ejecucion", y="score_rotacion",
                    color="nombre", markers=True,
                    labels={
                        "fecha_ejecucion": "Fecha de ejecución",
                        "score_rotacion": "Score de Rotación",
                        "nombre": "Empresa",
                    },
                )
                fig_hist.update_layout(height=450)
                st.plotly_chart(fig_hist)

            # Tabla histórica
            st.dataframe(
                df_hist[["fecha_ejecucion", "nombre", "score_rotacion", "nivel_rotacion",
                         "num_empleados", "score_noticias", "score_glassdoor", "score_trends"]].sort_values(
                    ["nombre", "fecha_ejecucion"]
                ),
                width="stretch",
            )
        else:
            st.info(
                "ℹ️ Solo hay 1 ejecución registrada. Ejecuta `python main.py` varias veces "
                "para ver la evolución histórica de los scores."
            )

            # Mostrar al menos los datos actuales en formato gráfico
            fig_ev = px.bar(
                df_filtrado.sort_values("score_rotacion", ascending=False),
                x="nombre", y="score_rotacion",
                color="nivel_rotacion",
                color_discrete_map={
                    "Bajo": "#2ecc71", "Moderado": "#f39c12",
                    "Alto": "#e67e22", "Muy alto": "#e74c3c",
                },
                labels={"nombre": "Empresa", "score_rotacion": "Score"},
            )
            fig_ev.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_ev)

    # ── Footer ───────────────────────────────────────────────────────
    st.markdown("---")
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        st.markdown(
            "📊 **Informe de Rotación de Empleados** — Datos: Yahoo Finance, Google News, "
            "Google Trends, Glassdoor | Dashboard: Streamlit + Plotly"
        )
    with col_f2:
        # Botón re-ejecutar en el footer también
        if st.button("🔄 Actualizar datos", use_container_width=True):
            with st.spinner("Ejecutando análisis..."):
                _, _, ruta_pdf = ejecutar_analisis(True)
            st.session_state["ultimo_pdf"] = ruta_pdf
            cargar_ultima_ejecucion.clear()
            cargar_historico_completo.clear()
            cargar_ejecuciones.clear()
            st.rerun()


def _fmt_num(val):
    if val is None or pd.isna(val):
        return "N/D"
    val = int(val)
    if val >= 1_000_000:
        return f"{val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val/1_000:.0f}K"
    return str(val)


if __name__ == "__main__":
    main()

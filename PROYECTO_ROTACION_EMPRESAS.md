# Informe de Rotación de Empleados en Grandes Multinacionales

> **Estado:** Funcional — análisis automatizado operativo  
> **Última actualización:** 5 de abril de 2026  
> **Versión:** 4.0 (6 fuentes de datos + Dashboard + PDF)

---

## 1. Objetivo del Proyecto

Elaborar un informe detallado sobre la **rotación de empleados** en las principales empresas multinacionales del mundo, identificando cada empresa con nombre completo (razón social / nombre comercial), cuantificando su nivel de rotación y su tamaño corporativo.

**Meta extra:** Desarrollar una herramienta (script o app) que permita recopilar y actualizar estos datos de forma semi-automática a partir de fuentes públicas de internet y redes sociales.

---

## 2. Metodología de Cuantificación

### 2.1 Índice de Rotación de Empleados

La fórmula estándar más utilizada:

$$
\text{Tasa de Rotación (\%)} = \frac{\text{Nº de salidas en el período}}{\text{Promedio de empleados en el período}} \times 100
$$

Donde:
- **Nº de salidas** = empleados que dejaron la empresa (voluntaria + involuntariamente)
- **Promedio de empleados** = (empleados al inicio + empleados al final) / 2

**Niveles de referencia:**
| Nivel         | Tasa anual       | Interpretación                          |
|---------------|------------------|-----------------------------------------|
| Bajo          | < 10%            | Alta retención, empresa estable         |
| Moderado      | 10% – 20%        | Normal en la mayoría de industrias      |
| Alto          | 20% – 30%        | Señal de alerta, revisar causas         |
| Muy alto      | > 30%            | Problema estructural serio              |

**Nota:** Cuando no se disponga del dato exacto, se estimará a partir de:
- Informes anuales (10-K, memorias de sostenibilidad)
- Datos de Glassdoor, LinkedIn, Indeed
- Noticias de despidos masivos / contrataciones
- Estimaciones de analistas

### 2.2 Tamaño de la Empresa

Se propone un **índice compuesto** con estas variables:

| Variable                  | Fuente típica              | Peso sugerido |
|---------------------------|----------------------------|---------------|
| Ingresos anuales (USD)    | Informes financieros, Fortune 500 | 35%     |
| Capitalización bursátil   | Yahoo Finance, Bloomberg   | 25%           |
| Nº total de empleados     | Informes anuales, LinkedIn | 25%           |
| Presencia geográfica (nº países) | Web corporativa     | 15%           |

**Categorías de tamaño:**
| Categoría     | Ingresos anuales (USD)   |
|---------------|--------------------------|
| Mega-cap      | > $100 mil millones      |
| Gran empresa  | $10B – $100B             |
| Mediana-grande| $1B – $10B               |

---

## 3. Fuentes de Datos

### 3.1 Fuentes Primarias (Internet)
- **Informes financieros públicos:** SEC (10-K), memorias anuales, informes ESG/sostenibilidad
- **Rankings:** Fortune Global 500, Forbes Global 2000
- **Portales financieros:** Yahoo Finance, Google Finance, MarketWatch

### 3.2 Redes Sociales y Plataformas Laborales
- **LinkedIn:** Número de empleados, tendencias de contratación, despidos anunciados
- **Glassdoor:** Reseñas de empleados, puntuaciones, señales cualitativas de rotación
- **Indeed:** Ofertas de empleo recurrentes (indicador indirecto de rotación)
- **X (Twitter):** Noticias de despidos, hashtags de layoffs
- **Reddit** (r/layoffs, r/antiwork): Testimonios y tendencias
- **Blind:** Datos internos anónimos de empleados tech

### 3.3 APIs y Datos Estructurados
- **LinkedIn API** (limitada, requiere partnership)
- **Glassdoor API** (requiere aprobación)
- **Yahoo Finance API / yfinance** (libre, datos financieros)
- **Web scraping** de páginas de empleo y noticias (con precaución legal)
- **Google Trends** (para medir interés público en "layoffs + empresa")
- **APIs de noticias** (NewsAPI, GNews) para monitorear despidos

---

## 4. Lista Inicial de Empresas a Analizar

| #  | Empresa                        | Sector              | País sede |
|----|--------------------------------|----------------------|-----------|
| 1  | Apple Inc.                     | Tecnología           | EE.UU.    |
| 2  | Microsoft Corporation          | Tecnología           | EE.UU.    |
| 3  | Amazon.com, Inc.               | E-commerce / Cloud   | EE.UU.    |
| 4  | Alphabet Inc. (Google)         | Tecnología           | EE.UU.    |
| 5  | Meta Platforms, Inc.           | Tecnología / RRSS    | EE.UU.    |
| 6  | Tesla, Inc.                    | Automoción / Energía | EE.UU.    |
| 7  | Walmart Inc.                   | Retail               | EE.UU.    |
| 8  | Samsung Electronics Co., Ltd.  | Electrónica          | Corea Sur |
| 9  | Toyota Motor Corporation       | Automoción           | Japón     |
| 10 | JPMorgan Chase & Co.           | Banca / Finanzas     | EE.UU.    |
| 11 | Johnson & Johnson              | Farmacéutica         | EE.UU.    |
| 12 | Nestlé S.A.                    | Alimentación         | Suiza     |
| 13 | Siemens AG                     | Industria / Tech     | Alemania  |
| 14 | LVMH Moët Hennessy             | Lujo                 | Francia   |
| 15 | Unilever PLC                   | Consumo masivo       | Reino Unido|
| 16 | Procter & Gamble Co.           | Consumo masivo       | EE.UU.    |
| 17 | Pfizer Inc.                    | Farmacéutica         | EE.UU.    |
| 18 | Accenture PLC                  | Consultoría          | Irlanda   |
| 19 | NVIDIA Corporation             | Tecnología / Chips   | EE.UU.    |
| 20 | Berkshire Hathaway Inc.        | Conglomerado         | EE.UU.    |

*(Lista ampliable según avance del proyecto)*

---

## 5. Propuesta Técnica: Script / App de Datos en Vivo

### 5.1 Enfoque Recomendado

Un proyecto en **Python** con dos capas:

```
┌─────────────────────────────────────────────┐
│              CAPA DE PRESENTACIÓN           │
│  Opción A: Dashboard web (Streamlit/Dash)   │
│  Opción B: Informe auto-generado (PDF/DOCX) │
│  Opción C: Notebook interactivo (Jupyter)   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           CAPA DE RECOPILACIÓN              │
│  • Scrapers (BeautifulSoup / Playwright)    │
│  • APIs (yfinance, NewsAPI, Google Trends)  │
│  • Base de datos local (SQLite / JSON)      │
└─────────────────────────────────────────────┘
```

### 5.2 Módulos Implementados

| Módulo               | Función                                              | Librerías            | Estado |
|----------------------|------------------------------------------------------|----------------------|--------|
| `config.py`          | Empresas, pesos, keywords, paths                     | —                    | ✅     |
| `data_finance.py`    | Datos financieros (ingresos, market cap, empleados)  | `yfinance`           | ✅     |
| `data_news.py`       | Noticias de despidos vía Google News RSS             | `feedparser`, `bs4`  | ✅     |
| `data_jobs.py`       | Ofertas de empleo vía Google News RSS                | `feedparser`, `bs4`  | ✅     |
| `data_social.py`     | Sentimiento en medios/RRSS                           | `feedparser`, `bs4`  | ✅     |
| `data_trends.py`     | Google Trends (interés en "layoffs")                 | `pytrends`           | ✅     |
| `data_glassdoor.py`  | Ratings Glassdoor (dataset referencia + JSON custom) | —                    | ✅     |
| `glassdoor_data.py`  | Dataset de referencia con ratings reales             | —                    | ✅     |
| `estimator.py`       | Calcular proxy-score de rotación (6 fuentes)         | `pandas`             | ✅     |
| `database.py`        | Base de datos SQLite para histórico                  | `sqlite3`            | ✅     |
| `report_generator.py`| Informe Markdown + CSV + Excel                       | `pandas`, `openpyxl` | ✅     |
| `pdf_generator.py`   | Informe PDF profesional con gráficos                 | `fpdf2`, `matplotlib`| ✅     |
| `dashboard.py`       | Dashboard interactivo web                            | `streamlit`, `plotly`| ✅     |

### 5.3 Flujo de Trabajo

```
1. Configurar lista de empresas objetivo (config.py)
2. Ejecutar recopiladores de datos (finance + social + glassdoor)
3. Almacenar datos en base de datos local (SQLite)
4. Ejecutar estimador de rotación
5. Generar informe o abrir dashboard
```

### 5.4 Ejemplo de Estimación de Rotación (sin dato directo)

Cuando no hay dato oficial, se puede construir un **proxy score** combinando:

| Señal                                      | Peso  | Ejemplo                                |
|--------------------------------------------|-------|----------------------------------------|
| Nº de ofertas de empleo abiertas / Nº empleados | 25% | Si 5% de posiciones están abiertas: alta rotación |
| Noticias de despidos recientes             | 20%   | "Amazon despide 18.000 empleados"      |
| Rating Glassdoor (invertido)               | 15%   | Rating 2.5/5 → señal de alta rotación  |
| Google Trends (interés en "layoffs")       | 15%   | Tendencia creciente = señal de alerta  |
| Crecimiento o decrecimiento de empleados   | 15%   | -10% empleados interanual              |
| Sentimiento en medios / RRSS               | 10%   | Menciones negativas en noticias        |

---

## 6. Plan de Fases

| Fase | Descripción                                          | Estado       |
|------|------------------------------------------------------|--------------|
| 1    | Script base: finanzas + noticias → MD/CSV/Excel      | ✅ Completada |
| 2    | Multi-fuente: Trends + Ofertas + Social + SQLite      | ✅ Completada |
| 3    | Dashboard interactivo (Streamlit + Plotly, 5 tabs)    | ✅ Completada |
| 4    | Mejorar calidad: Glassdoor como 6ª fuente             | ✅ Completada |
| 7    | Informe PDF profesional con gráficos (fpdf2)          | ✅ Completada |
| 8    | Actualizar documentación del proyecto                 | ✅ Completada |

---

## 7. Cómo Ejecutar

### 7.1 Instalación de dependencias

```bash
pip install yfinance feedparser beautifulsoup4 pandas openpyxl pytrends fpdf2 matplotlib streamlit plotly
```

### 7.2 Ejecución del análisis completo

```bash
cd app
python main.py                  # ejecución completa (6 fuentes, ~2 min)
python main.py --skip-trends    # sin Google Trends (más rápido, ~1 min)
```

**Archivos generados en `output/`:**
- `informe_rotacion_YYYY-MM-DD.md` — Informe Markdown
- `datos_rotacion_YYYY-MM-DD.csv` — Datos CSV
- `datos_rotacion_YYYY-MM-DD.xlsx` — Datos Excel
- `informe_rotacion_YYYY-MM-DD.pdf` — Informe PDF con gráficos

### 7.3 Dashboard interactivo

```bash
cd app
streamlit run dashboard.py
```

Abre automáticamente en `http://localhost:8501` con 5 pestañas:
1. **Ranking** — Tabla ordenada con filtros por nivel/sector
2. **Desglose** — Radar chart y contribución por fuente para cada empresa
3. **Comparador** — Scatter plot Tamaño vs Rotación
4. **Análisis Sectorial** — Heatmap y barras por sector/país
5. **Histórico** — Evolución entre ejecuciones (requiere múltiples runs)

### 7.4 Personalizar ratings de Glassdoor

Crear `data/glassdoor_custom.json` con el formato:
```json
{
    "AAPL": [4.1, "2026-Q2"],
    "MSFT": [4.4, "2026-Q2"]
}
```
Los valores del JSON sobreescriben los del dataset de referencia.

---

## 8. Consideraciones Legales y Éticas

- **Web scraping:** Respetar `robots.txt` y términos de servicio de cada plataforma
- **Datos personales:** No recopilar datos de empleados individuales (RGPD/LOPD)
- **LinkedIn/Glassdoor:** Usar datos agregados, no perfiles individuales
- **Citar fuentes:** Todo dato debe ser trazable a su fuente original
- **API keys:** Almacenar de forma segura (`.env`, nunca en el código)

---

## 8. Notas y Decisiones Pendientes

- [ ] Definir si el entregable principal es PDF, DOCX o presentación
- [ ] Decidir qué tan profundo llegar con la automatización (solo script vs. app completa)
- [ ] Confirmar presupuesto para APIs de pago (si aplica)
- [ ] Definir periodicidad de actualización del informe (¿trimestral? ¿anual?)
- [ ] Elegir entre Streamlit o Dash para el dashboard

---

*Documento vivo — se irá actualizando conforme avance el proyecto.*

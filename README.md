# Informe de Rotación de Empleados — Multinacionales

Herramienta automatizada que analiza la rotación de empleados en las 20 principales multinacionales del mundo, combinando 6 fuentes de datos públicas. Genera informes en PDF, Markdown, CSV y Excel, y ofrece un dashboard interactivo.

## Requisitos

- **Python 3.10+** (probado con 3.13)
- **Windows** (las fuentes del PDF usan Arial del sistema; adaptable a Linux/Mac)
- Conexión a internet (para Yahoo Finance, Google News, Google Trends)

## Instalación rápida

```bash
pip install -r requirements.txt
```

## Uso

### Análisis completo (genera informes)

```bash
cd app
python main.py                  # 6 fuentes, ~2 min
python main.py --skip-trends    # sin Google Trends, ~1 min
```

Archivos generados en `output/`:
- `informe_rotacion_YYYY-MM-DD.pdf` — **Informe PDF** con gráficos y portada
- `informe_rotacion_YYYY-MM-DD.md` — Informe Markdown
- `datos_rotacion_YYYY-MM-DD.csv` — Datos CSV
- `datos_rotacion_YYYY-MM-DD.xlsx` — Datos Excel con formato

### Dashboard interactivo

```bash
cd app
streamlit run dashboard.py
```

Se abre en `http://localhost:8501` con 5 pestañas: Ranking, Desglose, Comparador, Sectorial e Histórico.

## Estructura del proyecto

```
├── app/
│   ├── main.py               # Script principal (orquestador)
│   ├── config.py              # 20 empresas, pesos, keywords, paths
│   ├── data_finance.py        # Datos financieros (Yahoo Finance)
│   ├── data_news.py           # Noticias de despidos (Google News RSS)
│   ├── data_jobs.py           # Ofertas de empleo (Google News RSS)
│   ├── data_social.py         # Sentimiento en medios/RRSS
│   ├── data_trends.py         # Google Trends (interés en layoffs)
│   ├── data_glassdoor.py      # Ratings Glassdoor
│   ├── glassdoor_data.py      # Dataset de referencia Glassdoor
│   ├── estimator.py           # Proxy-score de rotación (6 fuentes)
│   ├── database.py            # SQLite para histórico entre ejecuciones
│   ├── report_generator.py    # Informes MD / CSV / Excel
│   ├── pdf_generator.py       # Informe PDF profesional con gráficos
│   └── dashboard.py           # Dashboard Streamlit + Plotly
├── data/                      # Base de datos SQLite (auto-creado)
├── output/                    # Informes generados (auto-creado)
├── requirements.txt
├── README.md
└── PROYECTO_ROTACION_EMPRESAS.md
```

## 6 Fuentes de datos y pesos

| Fuente                          | Peso | Origen                    |
|---------------------------------|------|---------------------------|
| Ofertas de empleo abiertas      | 25%  | Google News RSS           |
| Noticias de despidos            | 20%  | Google News RSS           |
| Rating Glassdoor (invertido)    | 15%  | Dataset referencia + JSON |
| Google Trends (layoffs)         | 15%  | pytrends                  |
| Variación interanual empleados  | 15%  | Yahoo Finance             |
| Sentimiento en medios/RRSS      | 10%  | Google News RSS           |

## Personalización

- **Añadir/quitar empresas:** editar `app/config.py` → diccionario `EMPRESAS`
- **Actualizar ratings Glassdoor:** crear `data/glassdoor_custom.json`:
  ```json
  {"AAPL": [4.1, "2026-Q2"], "MSFT": [4.4, "2026-Q2"]}
  ```
- **Ajustar pesos:** editar `PESOS_ROTACION` en `app/config.py`

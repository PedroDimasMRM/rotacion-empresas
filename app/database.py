"""
Base de datos histórica SQLite.
Almacena los datos de cada ejecución para poder comparar entre períodos
y detectar tendencias de rotación.
"""

import os
import sqlite3
from datetime import datetime

import pandas as pd

from config import DATA_DIR


DB_PATH = os.path.join(DATA_DIR, "historico.db")


def inicializar_db():
    """Crea las tablas si no existen."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ejecuciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            total_empresas INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datos_empresa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ejecucion_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            ticker TEXT NOT NULL,
            nombre TEXT,
            sector TEXT,
            pais TEXT,
            ingresos_usd REAL,
            market_cap_usd REAL,
            num_empleados INTEGER,
            indice_tamanio REAL,
            score_rotacion REAL,
            nivel_rotacion TEXT,
            score_noticias INTEGER,
            score_glassdoor INTEGER,
            score_trends INTEGER,
            score_ofertas INTEGER,
            score_social INTEGER,
            noticias_despidos INTEGER,
            FOREIGN KEY (ejecucion_id) REFERENCES ejecuciones(id)
        )
    """)

    # Migrar: añadir columna score_glassdoor si no existe (compat. con DB anteriores)
    try:
        cursor.execute("SELECT score_glassdoor FROM datos_empresa LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE datos_empresa ADD COLUMN score_glassdoor INTEGER")

    conn.commit()
    conn.close()


def guardar_ejecucion(df: pd.DataFrame) -> int:
    """
    Guarda los resultados de una ejecución en la base de datos.

    Args:
        df: DataFrame con los resultados consolidados

    Returns:
        ID de la ejecución guardada
    """
    inicializar_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO ejecuciones (fecha, total_empresas) VALUES (?, ?)",
        (fecha, len(df))
    )
    ejecucion_id = cursor.lastrowid

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO datos_empresa (
                ejecucion_id, fecha, ticker, nombre, sector, pais,
                ingresos_usd, market_cap_usd, num_empleados,
                indice_tamanio, score_rotacion, nivel_rotacion,
                score_noticias, score_glassdoor, score_trends, score_ofertas, score_social,
                noticias_despidos
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ejecucion_id,
            fecha,
            row.get("Ticker"),
            row.get("Empresa"),
            row.get("Sector"),
            row.get("País"),
            row.get("Ingresos (USD)"),
            row.get("Market Cap (USD)"),
            row.get("Empleados"),
            row.get("Índice Tamaño"),
            row.get("Score Rotación"),
            row.get("Nivel Rotación"),
            row.get("Score Noticias"),
            row.get("Score Glassdoor"),
            row.get("Score Trends"),
            row.get("Score Ofertas"),
            row.get("Score Social"),
            row.get("Noticias Despidos"),
        ))

    conn.commit()
    conn.close()
    return ejecucion_id


def obtener_historico_empresa(ticker: str, limite: int = 10) -> list[dict]:
    """
    Obtiene el histórico de scores para una empresa.

    Returns:
        Lista de dicts con fecha, score_rotacion, num_empleados, etc.
    """
    inicializar_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT fecha, score_rotacion, nivel_rotacion, num_empleados,
               score_noticias, score_trends, score_ofertas, score_social
        FROM datos_empresa
        WHERE ticker = ?
        ORDER BY fecha DESC
        LIMIT ?
    """, (ticker, limite))

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "fecha": r[0],
            "score_rotacion": r[1],
            "nivel_rotacion": r[2],
            "num_empleados": r[3],
            "score_noticias": r[4],
            "score_trends": r[5],
            "score_ofertas": r[6],
            "score_social": r[7],
        }
        for r in rows
    ]


def obtener_variacion_empleados(ticker: str) -> dict:
    """
    Calcula la variación de empleados comparando con la ejecución anterior.

    Returns:
        dict con empleados_anterior, empleados_actual, variacion_pct, score
    """
    inicializar_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT num_empleados, fecha
        FROM datos_empresa
        WHERE ticker = ? AND num_empleados IS NOT NULL
        ORDER BY fecha DESC
        LIMIT 2
    """, (ticker,))

    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 2:
        return {
            "empleados_anterior": None,
            "empleados_actual": rows[0][0] if rows else None,
            "variacion_pct": None,
            "score": 50,  # neutro
            "nota": "Sin dato anterior para comparar",
        }

    actual = rows[0][0]
    anterior = rows[1][0]

    if anterior and anterior > 0:
        variacion = ((actual - anterior) / anterior) * 100
    else:
        variacion = 0

    # Score: reducción de plantilla → alta rotación
    # -20% o peor → score 100, +10% o más → score 10, 0% → 50
    if variacion <= -20:
        score = 100
    elif variacion >= 10:
        score = 10
    else:
        # Mapeo lineal de [-20, +10] a [100, 10]
        score = int(100 - (variacion + 20) * (90 / 30))
        score = max(0, min(100, score))

    return {
        "empleados_anterior": anterior,
        "empleados_actual": actual,
        "variacion_pct": round(variacion, 1),
        "score": score,
        "nota": f"Variación: {variacion:+.1f}% vs ejecución anterior",
    }


def contar_ejecuciones() -> int:
    """Cuenta el número de ejecuciones almacenadas."""
    inicializar_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM ejecuciones")
    count = cursor.fetchone()[0]
    conn.close()
    return count

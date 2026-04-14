"""
Gerenciamento do banco de dados SQLite para a Lotofácil.
"""
import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "lotofacil.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """Cria as tabelas se não existirem."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sorteios (
            concurso     INTEGER PRIMARY KEY,
            data         TEXT,
            n01 INTEGER, n02 INTEGER, n03 INTEGER, n04 INTEGER, n05 INTEGER,
            n06 INTEGER, n07 INTEGER, n08 INTEGER, n09 INTEGER, n10 INTEGER,
            n11 INTEGER, n12 INTEGER, n13 INTEGER, n14 INTEGER, n15 INTEGER
        )
    """)
    conn.commit()
    conn.close()


def salvar_sorteios(df: pd.DataFrame):
    """Insere ou substitui sorteios no banco."""
    conn = get_connection()
    df.to_sql("sorteios", conn, if_exists="replace", index=False)
    conn.close()


def carregar_sorteios() -> pd.DataFrame:
    """Retorna todos os sorteios ordenados por concurso."""
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM sorteios ORDER BY concurso ASC", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


def ultimo_concurso() -> int:
    """Retorna o número do último concurso salvo."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT MAX(concurso) FROM sorteios")
        result = cursor.fetchone()[0]
    except Exception:
        result = 0
    conn.close()
    return result or 0


def inserir_sorteio(concurso: int, data: str, numeros: list):
    """Insere um único sorteio."""
    conn = get_connection()
    cursor = conn.cursor()
    nums = sorted(numeros)
    cursor.execute("""
        INSERT OR REPLACE INTO sorteios
        (concurso, data, n01,n02,n03,n04,n05,n06,n07,n08,n09,n10,n11,n12,n13,n14,n15)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, [concurso, data] + nums)
    conn.commit()
    conn.close()

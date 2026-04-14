"""
Carrega dados de arquivos CSV ou Excel para o banco SQLite.
"""
import pandas as pd
from pathlib import Path
from src.data.database import salvar_sorteios
from colorama import Fore, Style


def detectar_colunas(df: pd.DataFrame) -> pd.DataFrame | None:
    """
    Tenta detectar automaticamente o formato do arquivo
    e padroniza para o formato interno.
    """
    df.columns = [str(c).strip().lower() for c in df.columns]

    # Tenta encontrar coluna de concurso
    col_concurso = None
    for c in df.columns:
        if "concurso" in c or "numero" in c or "num" == c:
            col_concurso = c
            break

    # Tenta encontrar coluna de data
    col_data = None
    for c in df.columns:
        if "data" in c or "date" in c:
            col_data = c
            break

    # Tenta encontrar colunas de números
    num_cols = []
    for c in df.columns:
        if c.startswith("bola") or c.startswith("num") or c.startswith("n0") or c.startswith("dezena"):
            num_cols.append(c)

    if not num_cols:
        # Tenta detectar colunas numéricas (exceto concurso e data)
        skip = {col_concurso, col_data}
        for c in df.columns:
            if c not in skip:
                try:
                    vals = df[c].dropna().astype(int)
                    if vals.between(1, 25).all():
                        num_cols.append(c)
                except Exception:
                    pass

    if len(num_cols) < 15:
        print(f"{Fore.RED}  Não foi possível detectar 15 colunas de números.{Style.RESET_ALL}")
        return None

    num_cols = num_cols[:15]

    result = pd.DataFrame()
    result["concurso"] = df[col_concurso].astype(int) if col_concurso else range(1, len(df)+1)
    result["data"] = df[col_data].astype(str) if col_data else "00/00/0000"

    for i, c in enumerate(num_cols, 1):
        result[f"n{i:02d}"] = df[c].astype(int)

    return result


def carregar_csv(caminho: str) -> bool:
    """Carrega um arquivo CSV para o banco de dados."""
    path = Path(caminho)
    if not path.exists():
        print(f"{Fore.RED}  Arquivo não encontrado: {caminho}{Style.RESET_ALL}")
        return False

    try:
        df = pd.read_csv(caminho, sep=None, engine="python")
    except Exception as e:
        print(f"{Fore.RED}  Erro ao ler CSV: {e}{Style.RESET_ALL}")
        return False

    return _processar_df(df, caminho)


def carregar_excel(caminho: str) -> bool:
    """Carrega um arquivo Excel para o banco de dados."""
    path = Path(caminho)
    if not path.exists():
        print(f"{Fore.RED}  Arquivo não encontrado: {caminho}{Style.RESET_ALL}")
        return False

    try:
        df = pd.read_excel(caminho)
    except Exception as e:
        print(f"{Fore.RED}  Erro ao ler Excel: {e}{Style.RESET_ALL}")
        return False

    return _processar_df(df, caminho)


def _processar_df(df: pd.DataFrame, origem: str) -> bool:
    result = detectar_colunas(df)
    if result is None:
        return False

    salvar_sorteios(result)
    print(f"{Fore.GREEN}  ✅ {len(result)} sorteios carregados de '{origem}'.{Style.RESET_ALL}")
    return True

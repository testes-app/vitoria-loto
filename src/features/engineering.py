"""
Feature engineering para os modelos da Lotofácil.
"""
import numpy as np
import pandas as pd

COLS_NUMS = [f"n{i:02d}" for i in range(1, 16)]


def extrair_numeros(df):
    matriz = np.zeros((len(df), 25), dtype=np.float32)
    for idx, (_, row) in enumerate(df.iterrows()):
        for col in COLS_NUMS:
            num = int(row[col])
            if 1 <= num <= 25:
                matriz[idx, num - 1] = 1.0
    return matriz


def preparar_dataset(df, janela=10):
    matriz = extrair_numeros(df)
    X_rows, y_rows = [], []
    for i in range(janela, len(matriz)):
        X_rows.append(matriz[i - janela:i].flatten())
        y_rows.append(matriz[i])
    X = pd.DataFrame(X_rows, columns=[f"f{i}" for i in range(janela * 25)])
    y = pd.DataFrame(
        np.array(y_rows, dtype=np.float32),
        columns=[f"label_{n:02d}" for n in range(1, 26)]
    )
    return X, y


def gerar_features_proximo(df, janela=10):
    matriz = extrair_numeros(df)
    if len(matriz) < janela:
        janela = len(matriz)
    X_pred = matriz[-janela:].flatten().reshape(1, -1)
    return pd.DataFrame(
        X_pred.astype(np.float32),
        columns=[f"f{i}" for i in range(janela * 25)]
    )
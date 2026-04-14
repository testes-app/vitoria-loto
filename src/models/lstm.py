"""
Modelo LSTM: Rede Neural para séries temporais.
Aprende padrões sequenciais nos sorteios.
"""
import numpy as np
import joblib
from pathlib import Path
from colorama import Fore, Style

MODELS_DIR = Path(__file__).parent.parent.parent / "models"
NUMEROS = list(range(1, 26))
LOOKBACK = 20  # Janela de sorteios anteriores


def _extrair_sequencias(matriz: np.ndarray, lookback: int):
    """Cria pares (sequência de lookback sorteios, próximo sorteio)."""
    X, y = [], []
    for i in range(lookback, len(matriz)):
        X.append(matriz[i - lookback:i])
        y.append(matriz[i])
    return np.array(X), np.array(y)


class LSTMModel:
    def __init__(self):
        self.model = None
        self.trained = False

    def _build_model(self):
        try:
            import tensorflow as tf
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization

            model = Sequential([
                LSTM(128, input_shape=(LOOKBACK, 25), return_sequences=True),
                Dropout(0.3),
                LSTM(64, return_sequences=False),
                Dropout(0.3),
                BatchNormalization(),
                Dense(64, activation="relu"),
                Dense(25, activation="sigmoid")
            ])
            model.compile(optimizer="adam", loss="binary_crossentropy",
                          metrics=["accuracy"])
            return model
        except ImportError:
            print(f"{Fore.RED}  TensorFlow não instalado. Instale com: pip install tensorflow{Style.RESET_ALL}")
            return None

    def treinar(self, matriz: np.ndarray, epochs=30, verbose=True):
        """Treina a LSTM com os dados históricos."""
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

        if verbose:
            print(f"\n{Fore.CYAN}  Treinando LSTM...{Style.RESET_ALL}")

        X, y = _extrair_sequencias(matriz.astype(np.float32), LOOKBACK)

        split = int(len(X) * 0.9)
        X_tr, X_val = X[:split], X[split:]
        y_tr, y_val = y[:split], y[split:]

        self.model = self._build_model()
        if self.model is None:
            return

        import tensorflow as tf
        cb = [
            tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
            tf.keras.callbacks.ReduceLROnPlateau(patience=3, factor=0.5)
        ]

        self.model.fit(
            X_tr, y_tr,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=32,
            callbacks=cb,
            verbose=1 if verbose else 0
        )

        self.trained = True
        self.salvar()

        if verbose:
            print(f"  {Fore.GREEN}✅ LSTM treinada e salva!{Style.RESET_ALL}")

    def prever_probabilidades(self, matriz: np.ndarray) -> dict:
        """Retorna probabilidades para o próximo sorteio."""
        if not self.trained or self.model is None:
            raise RuntimeError("Modelo não treinado!")

        seq = matriz[-LOOKBACK:].astype(np.float32)
        seq = seq[np.newaxis, :, :]  # (1, LOOKBACK, 25)
        probs = self.model.predict(seq, verbose=0)[0]
        return {i + 1: float(probs[i]) for i in range(25)}

    def gerar_jogos(self, matriz: np.ndarray, n_jogos=5, tamanho=15) -> list:
        probs = self.prever_probabilidades(matriz)
        ranking = sorted(probs.items(), key=lambda x: x[1], reverse=True)

        import random
        random.seed(99)
        top = [n for n, _ in ranking[:20]]
        jogos = []
        for _ in range(n_jogos):
            jogo = sorted(random.sample(top[:17], tamanho))
            jogos.append(jogo)
        return jogos

    def salvar(self):
        if self.model:
            self.model.save(str(MODELS_DIR / "lstm_model.keras"))

    def carregar(self) -> bool:
        path = MODELS_DIR / "lstm_model.keras"
        if not path.exists():
            return False
        try:
            import tensorflow as tf
            self.model = tf.keras.models.load_model(str(path))
            self.trained = True
            return True
        except Exception:
            return False

"""
Modelos ML auxiliares para a Lotofácil.
"""
import numpy as np
from sklearn.ensemble import IsolationForest


class LotofacilML:
    def __init__(self):
        self._isolation = None

    def treinar_isolation_forest(self, concursos: list) -> bool:
        try:
            X = self._jogos_para_binario(concursos)
            self._isolation = IsolationForest(
                n_estimators=200,
                contamination=0.05,
                random_state=42
            )
            self._isolation.fit(X)
            return True
        except Exception as e:
            print(f"Erro ao treinar Isolation Forest: {e}")
            return False

    def filtrar_jogos_isolation(self, jogos: list, top_n: int = 5) -> list:
        if self._isolation is None:
            return []
        X = self._jogos_para_binario(jogos)
        scores = self._isolation.score_samples(X)
        ranqueados = sorted(
            [{"jogo": jogos[i], "score": scores[i]} for i in range(len(jogos))],
            key=lambda x: x["score"],
            reverse=True
        )
        return ranqueados[:top_n]

    def _jogos_para_binario(self, jogos: list) -> np.ndarray:
        X = np.zeros((len(jogos), 25), dtype=np.float32)
        for i, jogo in enumerate(jogos):
            for num in jogo:
                if 1 <= int(num) <= 25:
                    X[i, int(num) - 1] = 1.0
        return X

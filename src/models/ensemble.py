"""
Modelo Ensemble: Random Forest + XGBoost + LightGBM
Treina um modelo por número (1-25) e combina as probabilidades.
"""
import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score
import xgboost as xgb
import lightgbm as lgb
from colorama import Fore, Style

MODELS_DIR = Path(__file__).parent.parent.parent / "models"
NUMEROS = list(range(1, 26))


class EnsembleModel:
    def __init__(self):
        self.models = {}   # {num: {'rf': ..., 'xgb': ..., 'lgb': ...}}
        self.weights = {}  # {num: [w_rf, w_xgb, w_lgb]}
        self.trained = False

    def treinar(self, X, y, verbose=True):
        """Treina RF + XGB + LGB para cada número 1-25."""
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

        if verbose:
            print(f"\n{Fore.CYAN}  Treinando Ensemble (RF + XGB + LGB)...{Style.RESET_ALL}")

        tscv = TimeSeriesSplit(n_splits=5)

        for num in NUMEROS:
            col = f"label_{num:02d}"
            if col not in y.columns:
                continue
            y_num = y[col].values

            rf = RandomForestClassifier(
                n_estimators=200, max_depth=8, min_samples_leaf=5,
                n_jobs=-1, random_state=42
            )
            xgb_m = xgb.XGBClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                use_label_encoder=False, eval_metric="logloss",
                verbosity=0, random_state=42
            )
            lgb_m = lgb.LGBMClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.05,
                subsample=0.8, colsample_bytree=0.8,
                verbose=-1, random_state=42
            )

            # Validação cruzada temporal para calcular pesos
            aucs = {"rf": [], "xgb": [], "lgb": []}
            for train_idx, val_idx in tscv.split(X):
                X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_tr, y_val = y_num[train_idx], y_num[val_idx]
                if y_val.sum() == 0:
                    continue
                for name, m in [("rf", rf), ("xgb", xgb_m), ("lgb", lgb_m)]:
                    m.fit(X_tr, y_tr)
                    prob = m.predict_proba(X_val)[:, 1]
                    aucs[name].append(roc_auc_score(y_val, prob))

            w = {k: np.mean(v) if v else 0.33 for k, v in aucs.items()}
            total = sum(w.values()) or 1
            self.weights[num] = [w["rf"] / total, w["xgb"] / total, w["lgb"] / total]

            # Treina nos dados completos
            rf.fit(X, y_num)
            xgb_m.fit(X, y_num)
            lgb_m.fit(X, y_num)

            self.models[num] = {"rf": rf, "xgb": xgb_m, "lgb": lgb_m}

            if verbose and num % 5 == 0:
                print(f"    {Fore.GREEN}✅ Número {num:02d} treinado.{Style.RESET_ALL}")

        self.trained = True
        self.salvar()
        if verbose:
            print(f"  {Fore.GREEN}✅ Ensemble treinado e salvo!{Style.RESET_ALL}")

    def prever_probabilidades(self, X_pred) -> dict:
        """Retorna {num: probabilidade} para o próximo sorteio."""
        if not self.trained:
            raise RuntimeError("Modelo não treinado!")

        probs = {}
        for num in NUMEROS:
            m = self.models.get(num)
            if not m:
                probs[num] = 0.0
                continue
            w = self.weights.get(num, [1/3, 1/3, 1/3])
            p_rf  = m["rf"].predict_proba(X_pred)[:, 1][0]
            p_xgb = m["xgb"].predict_proba(X_pred)[:, 1][0]
            p_lgb = m["lgb"].predict_proba(X_pred)[:, 1][0]
            probs[num] = w[0]*p_rf + w[1]*p_xgb + w[2]*p_lgb

        return probs

    def gerar_jogos(self, X_pred, n_jogos=5, tamanho=15) -> list:
        """Gera n_jogos com os números de maior probabilidade."""
        probs = self.prever_probabilidades(X_pred)
        ranking = sorted(probs.items(), key=lambda x: x[1], reverse=True)

        jogos = []
        top = [n for n, _ in ranking[:20]]  # top 20 candidatos

        import random
        random.seed(42)
        for _ in range(n_jogos):
            jogo = sorted(random.sample(top[:17], tamanho))
            jogos.append(jogo)

        return jogos

    def salvar(self):
        path = MODELS_DIR / "ensemble.pkl"
        joblib.dump({"models": self.models, "weights": self.weights}, path)

    def carregar(self) -> bool:
        path = MODELS_DIR / "ensemble.pkl"
        if not path.exists():
            return False
        data = joblib.load(path)
        self.models = data["models"]
        self.weights = data["weights"]
        self.trained = True
        return True

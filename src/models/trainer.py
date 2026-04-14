"""
Gerencia o treinamento e carregamento de todos os modelos.
"""
import numpy as np
from pathlib import Path
from colorama import Fore, Style
from collections import Counter

from src.data.database import carregar_sorteios
from src.features.engineering import preparar_dataset, extrair_numeros, gerar_features_proximo
from src.models.ensemble import EnsembleModel
from src.models.lstm import LSTMModel
from src.models.genetic import AlgoritmoGenetico

MODELS_DIR = Path(__file__).parent.parent.parent / "models"


class Trainer:
    def __init__(self):
        self.ensemble = EnsembleModel()
        self.lstm = LSTMModel()
        self.ag = AlgoritmoGenetico()
        self._df = None
        self._X = None
        self._y = None
        self._matriz = None
        self._ultimo_ranking_preditivo = None
        self._ultimos_jogos = None
        self._isolation_ml = None

    def _carregar_dados(self):
        self._df = carregar_sorteios()
        if self._df.empty:
            raise ValueError("Nenhum dado no banco! Atualize os dados primeiro.")
        self._X, self._y = preparar_dataset(self._df)
        self._matriz = extrair_numeros(self._df)

    # ─────────────────────────────────────────────
    # Treinamento
    # ─────────────────────────────────────────────

    def treinar_ensemble(self, verbose=True):
        if self._df is None:
            self._carregar_dados()
        self.ensemble.treinar(self._X, self._y, verbose=verbose)

    def treinar_lstm(self, verbose=True):
        if self._df is None:
            self._carregar_dados()
        self.lstm.treinar(self._matriz, verbose=verbose)

    def treinar_tudo(self, verbose=True):
        print(f"\n{Fore.CYAN}══════════════════════════════════{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  TREINANDO TODOS OS MODELOS...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}══════════════════════════════════{Style.RESET_ALL}")
        self._carregar_dados()
        self.treinar_ensemble(verbose)
        self.treinar_lstm(verbose)
        print(f"\n{Fore.GREEN}✅ Todos os modelos treinados!{Style.RESET_ALL}")

    def carregar_modelos(self) -> dict:
        """Carrega modelos salvos. Retorna quais foram carregados."""
        return {
            "ensemble": self.ensemble.carregar(),
            "lstm": self.lstm.carregar()
        }

    # ─────────────────────────────────────────────
    # Integração com Ranking Turbo (17 dezenas)
    # ─────────────────────────────────────────────

    def _carregar_ranking_turbo(self) -> list:
        """
        Tenta carregar o ranking preditivo de 17 dezenas salvo em CSV.
        Retorna lista de (combo, stats, pi) ou [] se não encontrado.
        """
        try:
            from src.analysis.turbo import carregar_ranking_do_csv
            df = self._df if self._df is not None else carregar_sorteios()
            ranking = carregar_ranking_do_csv(df)
            if ranking:
                print(f"  {Fore.GREEN}✅ Ranking turbo carregado: {len(ranking)} combos de 17 dezenas.{Style.RESET_ALL}")
            return ranking
        except Exception as e:
            print(f"  {Fore.YELLOW}⚠️  Não foi possível carregar ranking turbo: {e}{Style.RESET_ALL}")
            return []

    def _probs_do_ranking(self, ranking: list, top_n: int = 50, peso_turbo: float = 0.5) -> dict:
        """
        Gera dicionário de probabilidades {1..25: float} a partir
        das dezenas mais frequentes no top_n do ranking de 17 dezenas.

        peso_turbo: quanto o ranking influencia (0.0 = ignora, 1.0 = só ranking)
        """
        freq = Counter()
        for combo, _, pi in ranking[:top_n]:
            # Pondera cada dezena pelo índice preditivo
            for d in combo:
                freq[d] += pi

        total = sum(freq.values()) or 1.0
        probs_turbo = {n: freq.get(n, 0.0) / total for n in range(1, 26)}

        return probs_turbo

    def _combinar_probs(self, probs_ml: dict, probs_turbo: dict,
                        peso_turbo: float = 0.5) -> dict:
        """
        Combina probabilidades do ML com as do ranking turbo.
        peso_turbo=0.5 → 50% ML + 50% ranking
        """
        probs_final = {}
        for n in range(1, 26):
            ml_val = probs_ml.get(n, 1/25)
            turbo_val = probs_turbo.get(n, 1/25)
            probs_final[n] = (1 - peso_turbo) * ml_val + peso_turbo * turbo_val

        # Normaliza
        total = sum(probs_final.values()) or 1.0
        return {n: v / total for n, v in probs_final.items()}

    def _exibir_top_dezenas(self, probs: dict, titulo: str = "TOP DEZENAS", top=17):
        """Exibe as dezenas mais prováveis formatadas."""
        print(f"\n{Fore.CYAN}  📊 {titulo}:{Style.RESET_ALL}")
        ranking = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:top]
        for num, prob in ranking:
            barra = "█" * int(prob * 200)
            print(f"  {Fore.GREEN}Nº {num:02d}{Style.RESET_ALL}: {barra:<20} {prob*100:.2f}%")

    # ─────────────────────────────────────────────
    # Geração de jogos — métodos originais
    # ─────────────────────────────────────────────

    def gerar_jogos_ensemble(self, n_jogos=5) -> list:
        if self._df is None:
            self._carregar_dados()
        X_pred = gerar_features_proximo(self._df)
        return self.ensemble.gerar_jogos(X_pred, n_jogos)

    def gerar_jogos_lstm(self, n_jogos=5) -> list:
        if self._df is None:
            self._carregar_dados()
        return self.lstm.gerar_jogos(self._matriz, n_jogos)

    def gerar_jogos_genetico(self, n_jogos=5, verbose=True) -> list:
        if self._df is None:
            self._carregar_dados()

        if self.ensemble.trained:
            X_pred = gerar_features_proximo(self._df)
            probs = self.ensemble.prever_probabilidades(X_pred)
        elif self.lstm.trained:
            probs = self.lstm.prever_probabilidades(self._matriz)
        else:
            probs = {n: 1/25 for n in range(1, 26)}

        return self.ag.otimizar(probs, self._matriz, n_jogos, verbose)

    def gerar_jogos_super_combo(self, n_jogos=5) -> list:
        """Combina todos os modelos e gera os melhores jogos."""
        if self._df is None:
            self._carregar_dados()

        probs_combinadas = {n: 0.0 for n in range(1, 26)}
        count = 0

        if self.ensemble.trained:
            X_pred = gerar_features_proximo(self._df)
            pe = self.ensemble.prever_probabilidades(X_pred)
            for n in range(1, 26):
                probs_combinadas[n] += pe[n]
            count += 1

        if self.lstm.trained:
            pl = self.lstm.prever_probabilidades(self._matriz)
            for n in range(1, 26):
                probs_combinadas[n] += pl[n]
            count += 1

        if count > 0:
            for n in range(1, 26):
                probs_combinadas[n] /= count

        return self.ag.otimizar(probs_combinadas, self._matriz, n_jogos, verbose=True)

    # ─────────────────────────────────────────────
    # Geração de jogos — com ranking 17 dezenas
    # ─────────────────────────────────────────────

    def gerar_jogos_turbo_ensemble(self, n_jogos=5, top_n=50,
                                    peso_turbo=0.5, verbose=True) -> list:
        """
        Ensemble + ranking de 17 dezenas combinados.
        peso_turbo: influência do ranking (0.0 a 1.0)
        """
        if self._df is None:
            self._carregar_dados()

        if not self.ensemble.trained:
            print(f"  {Fore.RED}❌ Treine o Ensemble primeiro (opção 13 ou 15).{Style.RESET_ALL}")
            return []

        # Probs do ML
        X_pred = gerar_features_proximo(self._df)
        probs_ml = self.ensemble.prever_probabilidades(X_pred)

        # Probs do ranking turbo
        ranking = self._ultimo_ranking_preditivo or self._carregar_ranking_turbo()
        if not ranking:
            print(f"  {Fore.YELLOW}⚠️  Sem ranking turbo — usando só Ensemble.{Style.RESET_ALL}")
            return self.ensemble.gerar_jogos(X_pred, n_jogos)

        probs_turbo = self._probs_do_ranking(ranking, top_n=top_n)
        probs_final = self._combinar_probs(probs_ml, probs_turbo, peso_turbo)

        if verbose:
            self._exibir_top_dezenas(probs_final,
                f"TOP 17 — ENSEMBLE + TURBO (peso_turbo={peso_turbo:.0%})")

        return self.ag.otimizar(probs_final, self._matriz, n_jogos, verbose=verbose)

    def gerar_jogos_turbo_lstm(self, n_jogos=5, top_n=50,
                                peso_turbo=0.5, verbose=True) -> list:
        """
        LSTM + ranking de 17 dezenas combinados.
        """
        if self._df is None:
            self._carregar_dados()

        if not self.lstm.trained:
            print(f"  {Fore.RED}❌ Treine a LSTM primeiro (opção 14 ou 15).{Style.RESET_ALL}")
            return []

        probs_ml = self.lstm.prever_probabilidades(self._matriz)

        ranking = self._ultimo_ranking_preditivo or self._carregar_ranking_turbo()
        if not ranking:
            print(f"  {Fore.YELLOW}⚠️  Sem ranking turbo — usando só LSTM.{Style.RESET_ALL}")
            return self.lstm.gerar_jogos(self._matriz, n_jogos)

        probs_turbo = self._probs_do_ranking(ranking, top_n=top_n)
        probs_final = self._combinar_probs(probs_ml, probs_turbo, peso_turbo)

        if verbose:
            self._exibir_top_dezenas(probs_final,
                f"TOP 17 — LSTM + TURBO (peso_turbo={peso_turbo:.0%})")

        return self.ag.otimizar(probs_final, self._matriz, n_jogos, verbose=verbose)

    def gerar_jogos_turbo_super_combo(self, n_jogos=5, top_n=50,
                                       peso_turbo=0.5, verbose=True) -> list:
        """
        Super Combo (todos os modelos) + ranking de 17 dezenas.
        O método mais poderoso — usa tudo junto.
        """
        if self._df is None:
            self._carregar_dados()

        probs_combinadas = {n: 0.0 for n in range(1, 26)}
        count = 0

        if self.ensemble.trained:
            X_pred = gerar_features_proximo(self._df)
            pe = self.ensemble.prever_probabilidades(X_pred)
            for n in range(1, 26):
                probs_combinadas[n] += pe[n]
            count += 1

        if self.lstm.trained:
            pl = self.lstm.prever_probabilidades(self._matriz)
            for n in range(1, 26):
                probs_combinadas[n] += pl[n]
            count += 1

        if count == 0:
            print(f"  {Fore.YELLOW}⚠️  Nenhum modelo treinado — usando só ranking turbo.{Style.RESET_ALL}")
            probs_ml = {n: 1/25 for n in range(1, 26)}
        else:
            for n in range(1, 26):
                probs_combinadas[n] /= count
            probs_ml = probs_combinadas

        ranking = self._ultimo_ranking_preditivo or self._carregar_ranking_turbo()
        if not ranking:
            print(f"  {Fore.YELLOW}⚠️  Sem ranking turbo — usando só modelos ML.{Style.RESET_ALL}")
            return self.ag.otimizar(probs_ml, self._matriz, n_jogos, verbose=verbose)

        probs_turbo = self._probs_do_ranking(ranking, top_n=top_n)
        probs_final = self._combinar_probs(probs_ml, probs_turbo, peso_turbo)

        if verbose:
            self._exibir_top_dezenas(probs_final,
                f"TOP 17 — SUPER COMBO TURBO (peso_turbo={peso_turbo:.0%})")

        return self.ag.otimizar(probs_final, self._matriz, n_jogos, verbose=verbose)
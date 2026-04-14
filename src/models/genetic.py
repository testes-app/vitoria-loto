"""
Algoritmo Genético para otimizar seleção de jogos da Lotofácil.
Evolui populações de jogos maximizando um score baseado em
probabilidades do modelo + restrições estatísticas.
"""
import numpy as np
import random
from colorama import Fore, Style

NUMEROS = list(range(1, 26))


def _score_jogo(jogo: list, probs: dict, historico: np.ndarray, ult_sorteio: list = None) -> float:
    """
    Calcula o score de um jogo considerando critérios de elite:
    - Probabilidades dos números (ML Inteligência)
    - Soma das dezenas (Variação entre 180-220)
    - Repetição do sorteio anterior (8-10 números)
    - Sequências consecutivas (Evita clusters irreais)
    """
    # 1. Score base: Probabilidades IA
    score = sum(probs.get(n, 0) for n in jogo) * 10.0

    # 2. Soma das dezenas (Objetivo: 170-210)
    soma = sum(jogo)
    if not (170 <= soma <= 210):
        score -= 0.5 # Penalidade leve por estar fora da média histórica

    # 3. Repetição do anterior (Se fornecido)
    if ult_sorteio is not None:
        repetidos = len(set(jogo) & set(ult_sorteio))
        if not (8 <= repetidos <= 10):
            score -= abs(repetidos - 9) * 0.1

    # 4. Sequências (Evita mais de 4 seguidos)
    sequencia_max = 0
    atual = 1
    for i in range(len(jogo)-1):
        if jogo[i] + 1 == jogo[i+1]:
            atual += 1
        else:
            sequencia_max = max(sequencia_max, atual)
            atual = 1
    sequencia_max = max(sequencia_max, atual)
    if sequencia_max > 4:
        score -= (sequencia_max - 4) * 0.2

    # 5. Mix Par/Ímpar (Objetivo 8/7)
    pares = sum(1 for n in jogo if n % 2 == 0)
    if not (7 <= pares <= 9):
        score -= abs(pares - 8) * 0.05

    return score


def _crossover(p1: list, p2: list) -> list:
    """Combina dois jogos gerando um filho."""
    pool = list(set(p1 + p2))
    random.shuffle(pool)
    return sorted(pool[:15])


def _mutacao(jogo: list, taxa=0.1) -> list:
    """Substitui aleatoriamente alguns números."""
    jogo = jogo[:]
    for i in range(len(jogo)):
        if random.random() < taxa:
            candidatos = [n for n in NUMEROS if n not in jogo]
            if candidatos:
                jogo[i] = random.choice(candidatos)
    return sorted(set(jogo))[:15]


def _completar_jogo(jogo: list) -> list:
    """Garante exatamente 15 números únicos."""
    jogo = list(set(jogo))
    while len(jogo) < 15:
        n = random.choice(NUMEROS)
        if n not in jogo:
            jogo.append(n)
    return sorted(jogo[:15])


class AlgoritmoGenetico:
    def __init__(self, pop_size=200, geracoes=100, elite=20):
        self.pop_size = pop_size
        self.geracoes = geracoes
        self.elite = elite

    def otimizar(self, probs: dict, historico: np.ndarray,
                 n_jogos=5, verbose=True) -> list:
        """
        Evolui uma população de jogos e retorna os melhores.

        probs: {num: probabilidade} do modelo ML
        historico: matriz N x 25
        """
        if verbose:
            print(f"\n{Fore.CYAN}  Executando Algoritmo Genético...{Style.RESET_ALL}")

        # Inicializa população com viés nas probabilidades
        ranking = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        pesos = [p for _, p in ranking]
        nums_ord = [n for n, _ in ranking]

        # Normaliza pesos
        total_p = sum(pesos) or 1
        pesos = [p / total_p for p in pesos]

        populacao = []
        for _ in range(self.pop_size):
            selecionados = np.random.choice(
                nums_ord, size=15, replace=False, p=pesos
            ).tolist()
            populacao.append(sorted(selecionados))

        melhor_score = -np.inf
        melhor_jogo = None

        # Pega último sorteio para critérios de repetição
        ult_sorteio = None
        if len(historico) > 0:
            ult_sorteio = [i+1 for i, v in enumerate(historico[-1]) if v > 0]

        for gen in range(self.geracoes):
            # Avalia população
            scores = [_score_jogo(j, probs, historico, ult_sorteio) for j in populacao]
            idx_ord = np.argsort(scores)[::-1]

            top_score = scores[idx_ord[0]]
            if top_score > melhor_score:
                melhor_score = top_score
                melhor_jogo = populacao[idx_ord[0]]

            if verbose and gen % 20 == 0:
                print(f"    Gen {gen:3d} | Melhor score: {melhor_score:.4f}")

            # Elitismo
            elite_jogos = [populacao[i] for i in idx_ord[:self.elite]]

            # Nova população
            nova_pop = elite_jogos[:]
            while len(nova_pop) < self.pop_size:
                p1, p2 = random.choices(elite_jogos, k=2)
                filho = _crossover(p1, p2)
                filho = _completar_jogo(filho)
                filho = _mutacao(filho, taxa=0.15)
                filho = _completar_jogo(filho)
                nova_pop.append(filho)

            populacao = nova_pop

        # Retorna os n_jogos melhores únicos
        scores_finais = [(populacao[i], scores[i]) for i in idx_ord]
        jogos_unicos = []
        vistos = set()
        for jogo, _ in scores_finais:
            chave = tuple(jogo)
            if chave not in vistos:
                vistos.add(chave)
                jogos_unicos.append(jogo)
            if len(jogos_unicos) >= n_jogos:
                break

        if verbose:
            print(f"  {Fore.GREEN}✅ Algoritmo Genético concluído!{Style.RESET_ALL}")

        return jogos_unicos

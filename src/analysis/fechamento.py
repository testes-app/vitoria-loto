"""
Fechamento Matemático — Lotofácil Pro
Gera jogos com cobertura garantida de acertos mínimos.
"""
from itertools import combinations
from colorama import Fore, Style


def _gerar_fechamento(dezenas: list, tamanho_jogo: int = 15,
                      garantia: int = 11, verbose: bool = True) -> list:
    """
    Gera conjunto minimo de jogos com cobertura garantida.
    Algoritmo guloso otimizado com bitwise para 25 dezenas.
    """
    import random
    dezenas = sorted(dezenas)
    n = len(dezenas)
    idx = {d: i for i, d in enumerate(dezenas)}

    # Representa cada jogo e alvo como bitmask
    todos_jogos = list(combinations(dezenas, tamanho_jogo))
    alvos = list(combinations(dezenas, garantia))

    # Bitmasks
    jogo_masks = []
    for jogo in todos_jogos:
        mask = 0
        for d in jogo:
            mask |= (1 << idx[d])
        jogo_masks.append(mask)

    alvo_masks = []
    for alvo in alvos:
        mask = 0
        for d in alvo:
            mask |= (1 << idx[d])
        alvo_masks.append(mask)

    nao_cobertos = set(range(len(alvo_masks)))
    jogos_escolhidos = []

    if verbose:
        print(f"\n{Fore.CYAN}  ⚙️  Calculando fechamento...{Style.RESET_ALL}")
        print(f"  Grupo: {n} dezenas | Jogo: {tamanho_jogo} dezenas | Garantia: {garantia}pts")
        print(f"  Total de subconjuntos para cobrir: {len(alvo_masks):,}")

    while nao_cobertos:
        melhor_idx = -1
        melhor_ganho = 0

        # Amostra maior para 25 dezenas
        tamanho_amostra = min(2000, len(todos_jogos))
        indices = random.sample(range(len(todos_jogos)), tamanho_amostra)

        for ji in indices:
            jmask = jogo_masks[ji]
            ganho = sum(1 for ai in nao_cobertos if (alvo_masks[ai] & jmask) == alvo_masks[ai])
            if ganho > melhor_ganho:
                melhor_ganho = ganho
                melhor_idx = ji

        if melhor_idx == -1 or melhor_ganho == 0:
            break

        jogos_escolhidos.append(list(todos_jogos[melhor_idx]))
        jmask = jogo_masks[melhor_idx]
        nao_cobertos = {ai for ai in nao_cobertos if (alvo_masks[ai] & jmask) != alvo_masks[ai]}

        if verbose and len(jogos_escolhidos) % 5 == 0:
            pct = (1 - len(nao_cobertos)/len(alvo_masks)) * 100
            print(f"  Jogos: {len(jogos_escolhidos):3d} | Cobertura: {pct:.1f}%", end="\r")

    cobertura_final = (1 - len(nao_cobertos)/len(alvo_masks)) * 100

    if verbose:
        print(f"\n  {Fore.GREEN}✅ Fechamento concluído!{Style.RESET_ALL}")
        print(f"  Jogos gerados: {len(jogos_escolhidos)}")
        print(f"  Cobertura: {cobertura_final:.1f}%")
        if nao_cobertos:
            print(f"  {Fore.YELLOW}⚠️  {len(nao_cobertos)} subconjuntos nao cobertos{Style.RESET_ALL}")

    return jogos_escolhidos



def exibir_fechamento(jogos: list, dezenas: list, garantia: int):
    """Exibe os jogos do fechamento formatados."""
    custo = len(jogos) * 3.50
    print(f"\n{Fore.CYAN}{'═'*60}")
    print(f"  🎯 FECHAMENTO — {len(dezenas)} DEZENAS | GARANTIA {garantia}pts")
    print(f"  {len(jogos)} jogos | Custo: R$ {custo:.2f}")
    print(f"{'═'*60}{Style.RESET_ALL}")

    for i, jogo in enumerate(jogos, 1):
        nums = "  ".join(f"{Fore.GREEN}{n:02d}{Style.RESET_ALL}"
                        if n in set(dezenas[:12])
                        else f"{Fore.YELLOW}{n:02d}{Style.RESET_ALL}"
                        for n in sorted(jogo))
        print(f"  Jogo {i:02d}: {nums}")

    print(f"\n{Fore.CYAN}{'═'*60}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}= núcleo  {Fore.YELLOW}= variável{Style.RESET_ALL}")
    print(f"  Custo total: {Fore.GREEN}R$ {custo:.2f}{Style.RESET_ALL}")


def analisar_fechamento(jogos: list, df_sorteios, ultimos_n: int = 20):
    """Analisa o fechamento contra sorteios reais."""
    from collections import Counter
    import pandas as pd

    cols = [f"n{i:02d}" for i in range(1, 16)]
    sorteios = df_sorteios.tail(ultimos_n)
    total = len(sorteios)

    print(f"\n{Fore.CYAN}{'═'*65}")
    print(f"  📊 ANÁLISE DO FECHAMENTO — ÚLTIMOS {ultimos_n} SORTEIOS")
    print(f"{'─'*65}{Style.RESET_ALL}")
    print(f"  {'Concurso':<10} {'Data':<12} {'Melhor':>7} {'Premiados':>10}  Status")
    print(f"  {'-'*55}")

    total_premios = 0
    total_ganho = 0.0
    premios_por_pts = Counter()

    premios_valor = {11: 7.0, 12: 14.0, 13: 30.0, 14: 1500.0, 15: 50000.0}

    for _, row in sorteios.iterrows():
        nums = set(int(row[c]) for c in cols)
        acertos = [len(set(j) & nums) for j in jogos]
        melhor = max(acertos)
        premiados = sum(1 for a in acertos if a >= 11)

        if premiados > 0:
            total_premios += premiados
            ganho = sum(premios_valor.get(a, 0) for a in acertos if a >= 11)
            total_ganho += ganho
            premios_por_pts[melhor] += 1
            cor = Fore.GREEN if melhor >= 13 else Fore.YELLOW
            print(f"  {row['concurso']:<10} {str(row['data']):<12} "
                  f"{cor}{melhor:>7}pts{Style.RESET_ALL} "
                  f"{premiados:>8}x  ✅ R${ganho:.0f}")
        else:
            print(f"  {row['concurso']:<10} {str(row['data']):<12} "
                  f"{melhor:>7}pts {'—':>10}")

    custo_total = len(jogos) * 3.50
    saldo = total_ganho - custo_total

    print(f"\n{Fore.CYAN}{'═'*65}{Style.RESET_ALL}")
    print(f"  💰 RESUMO FINANCEIRO")
    print(f"  Sorteios analisados: {total}")
    print(f"  Total de premiações: {total_premios}")
    print(f"  Custo total: {Fore.RED}R$ {custo_total:.2f}{Style.RESET_ALL}")
    print(f"  Total ganho: {Fore.GREEN}R$ {total_ganho:.2f}{Style.RESET_ALL}")
    sinal = "+" if saldo >= 0 else ""
    cor = Fore.GREEN if saldo >= 0 else Fore.RED
    print(f"  Saldo: {cor}{sinal}R$ {saldo:.2f}{Style.RESET_ALL}")
    print(f"\n  Distribuição de acertos:")
    for pts in sorted(premios_por_pts.keys(), reverse=True):
        print(f"  {pts}pts: {premios_por_pts[pts]}x")
    print(f"{Fore.CYAN}{'═'*65}{Style.RESET_ALL}")


def rodar_fechamento_interativo(df_sorteios, ranking_preditivo=None):
    """Interface interativa para o fechamento matemático."""
    from src.ui.menu import pedir_numero, pedir_string

    print(f"\n{Fore.CYAN}{'═'*60}")
    print(f"  🎯 FECHAMENTO MATEMÁTICO")
    print(f"{'═'*60}{Style.RESET_ALL}")

    # Escolhe grupo de dezenas
    print(f"\n  Grupo de dezenas:")
    print(f"  1. 17 dezenas do Índice Preditivo")
    print(f"  2. 18 dezenas do Índice Preditivo")
    print(f"  3. 20 dezenas do Índice Preditivo")
    print(f"  4. Digitar manualmente")
    print(f"  5. Todos os 25 números")

    escolha_grupo = pedir_string("  Opção: ")

    if escolha_grupo in ("1", "2", "3", "5"):
        n_dez = {"1": 17, "2": 18, "3": 20, "5": 25}[escolha_grupo]

        if ranking_preditivo:
            # Extrai dezenas mais frequentes do ranking
            from collections import Counter
            freq = Counter()
            for combo, _, pi in ranking_preditivo[:50]:
                for d in combo:
                    freq[d] += pi
            dezenas = [n for n, _ in freq.most_common(n_dez)]
            dezenas = sorted(dezenas)
        else:
            # Usa frequência histórica
            cols = [f"n{i:02d}" for i in range(1, 16)]
            from collections import Counter
            freq = Counter()
            for _, row in df_sorteios.iterrows():
                for c in cols:
                    freq[int(row[c])] += 1
            dezenas = [n for n, _ in freq.most_common(n_dez)]
            dezenas = sorted(dezenas)

        print(f"\n  {Fore.GREEN}Dezenas selecionadas ({n_dez}):{Style.RESET_ALL}")
        print(f"  {' '.join(f'{d:02d}' for d in dezenas)}")

    else:
        entrada = pedir_string("  Digite as dezenas separadas por espaço: ")
        try:
            dezenas = sorted(set(int(x) for x in entrada.split()))
            if not all(1 <= d <= 25 for d in dezenas):
                print(f"  {Fore.RED}❌ Dezenas devem ser entre 1 e 25!{Style.RESET_ALL}")
                return []
        except ValueError:
            print(f"  {Fore.RED}❌ Entrada inválida!{Style.RESET_ALL}")
            return []

    # Escolhe garantia
    print(f"\n  Garantia mínima:")
    print(f"  1. 11 pontos")
    print(f"  2. 12 pontos")
    print(f"  3. 13 pontos")

    escolha_garantia = pedir_string("  Opção: ")
    garantia = {"1": 11, "2": 12, "3": 13}.get(escolha_garantia, 11)

    print(f"\n  {Fore.YELLOW}⚠️  Calculando fechamento com {len(dezenas)} dezenas e garantia {garantia}pts...{Style.RESET_ALL}")
    print(f"  Isso pode levar alguns minutos!")

    # Gera fechamento — roda 5 vezes e pega o menor resultado
    n_tentativas = 3
    print(f"  Rodando {n_tentativas} tentativas para minimizar jogos...")
    melhor_resultado = None
    for tentativa in range(1, n_tentativas + 1):
        print(f"  Tentativa {tentativa}/{n_tentativas}...", end="\r")
        jogos = _gerar_fechamento(dezenas, tamanho_jogo=15, garantia=garantia, verbose=(tentativa==1))
        if melhor_resultado is None or len(jogos) < len(melhor_resultado):
            melhor_resultado = jogos
    jogos = melhor_resultado
    print(f"  Melhor resultado: {len(jogos)} jogos!")

    if not jogos:
        print(f"  {Fore.RED}❌ Não foi possível gerar o fechamento!{Style.RESET_ALL}")
        return []

    # Exibe jogos
    exibir_fechamento(jogos, dezenas, garantia)

    # Analisa contra sorteios reais
    analisar = pedir_string("\n  Analisar contra sorteios reais? (s/n): ")
    if analisar.lower() == "s":
        n = pedir_numero("  Quantos sorteios? (10-50): ", 10, 50)
        analisar_fechamento(jogos, df_sorteios, ultimos_n=n)

    # Salva jogos
    import json
    import os
    caminho = "/mnt/c/Users/nome_do_usuario/Desktop/super-lotofacil/data/fechamento_jogos.json"
    with open(caminho, "w") as f:
        json.dump(jogos, f)
    print(f"\n  {Fore.GREEN}💾 Jogos salvos em fechamento_jogos.json!{Style.RESET_ALL}")

    return jogos

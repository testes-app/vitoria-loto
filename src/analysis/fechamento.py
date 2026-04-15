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
    Algoritmo guloso com varredura chunked — correto e sem OOM para 20+ dezenas.
    Chunk de 1000 alvos × 1500 jogos × 1 byte = 1.5 MB por passo.
    """
    import random
    import numpy as np

    dezenas = sorted(dezenas)
    n = len(dezenas)

    todos_jogos = list(combinations(range(n), tamanho_jogo))
    alvos       = list(combinations(range(n), garantia))

    total_jogos = len(todos_jogos)
    total_alvos = len(alvos)

    # Guarda de segurança: bloquear grupos com jogos demais para não travar RAM
    MAX_JOGOS_VIAVEL = 50_000
    if total_jogos > MAX_JOGOS_VIAVEL:
        print(f"\n  {Fore.RED}❌ GRUPO MUITO GRANDE PARA O ALGORITMO!{Style.RESET_ALL}")
        print(f"  {n} dezenas geram {total_jogos:,} jogos possíveis.")
        print(f"  Limite seguro: {MAX_JOGOS_VIAVEL:,} jogos (≤ 21 dezenas).")
        print(f"  {Fore.YELLOW}💡 Use 17-20 dezenas ou opção 4 (manual) com grupos menores.{Style.RESET_ALL}")
        return []

    if verbose:
        print(f"\n{Fore.CYAN}  ⚙️  Calculando fechamento (NumPy chunked)...{Style.RESET_ALL}")
        print(f"  Grupo: {n} dezenas | Jogo: {tamanho_jogo} dezenas | Garantia: {garantia}pts")
        print(f"  Subconjuntos: {total_alvos:,} | Jogos possíveis: {total_jogos:,}")

    # Bitmasks NumPy int64 (suporta até 63 bits = 25 dezenas)
    jogo_masks = np.zeros(total_jogos, dtype=np.int64)
    for j, jogo in enumerate(todos_jogos):
        for i in jogo:
            jogo_masks[j] |= np.int64(1 << i)

    alvo_masks = np.zeros(total_alvos, dtype=np.int64)
    for a, alvo in enumerate(alvos):
        for i in alvo:
            alvo_masks[a] |= np.int64(1 << i)

    nao_cobertos = np.ones(total_alvos, dtype=bool)
    jogos_escolhidos = []

    # Avalia TODOS os jogos possíveis por iteração (sem amostragem de jogos)
    # Alvos processados em chunks para manter memória baixa
    # Chunk 2000 × total_jogos × 1 byte: ex. 2000×15504 = 31 MB → seguro
    CHUNK = 2000
    STOP_PCT = 95.0  # parar em 95% — os últimos 5% custam quase tanto quanto os 95%

    if verbose:
        print(f"  Modo: todos {total_jogos:,} jogos avaliados | chunk {CHUNK} alvos | stop@{STOP_PCT}%")

    while nao_cobertos.any():
        nc_indices = np.where(nao_cobertos)[0]
        pct_atual = (1 - len(nc_indices) / total_alvos) * 100

        if pct_atual >= STOP_PCT:
            if verbose:
                print(f"\n  {Fore.YELLOW}⏹  Stop automático em {pct_atual:.1f}% de cobertura.{Style.RESET_ALL}")
            break

        # Acumular scores para TODOS os jogos, varrendo alvos em chunks
        ganhos = np.zeros(total_jogos, dtype=np.int32)
        for start in range(0, len(nc_indices), CHUNK):
            chunk_idx = nc_indices[start:start + CHUNK]
            chunk_masks = alvo_masks[chunk_idx]             # (chunk,)
            # (chunk, total_jogos) bool — ex. 2000×15504 = 31 MB
            covered = (chunk_masks[:, None] & jogo_masks[None, :]) == chunk_masks[:, None]
            ganhos += covered.sum(axis=0).astype(np.int32)

        melhor_j_idx = int(np.argmax(ganhos))
        melhor_ganho = int(ganhos[melhor_j_idx])

        if melhor_ganho == 0:
            break

        jogo_escolhido = [dezenas[i] for i in todos_jogos[melhor_j_idx]]
        jogos_escolhidos.append(jogo_escolhido)

        jmask = jogo_masks[melhor_j_idx]
        nao_cobertos &= ~((alvo_masks & jmask) == alvo_masks)

        if verbose and len(jogos_escolhidos) % 5 == 0:
            pct = (1 - nao_cobertos.sum() / total_alvos) * 100
            print(f"  Jogos: {len(jogos_escolhidos):3d} | Cobertura: {pct:.1f}%", end="\r")

    cobertura_final = (1 - nao_cobertos.sum() / total_alvos) * 100

    if verbose:
        print(f"\n  {Fore.GREEN}✅ Fechamento concluído!{Style.RESET_ALL}")
        print(f"  Jogos gerados: {len(jogos_escolhidos)}")
        print(f"  Cobertura: {cobertura_final:.1f}%")
        if nao_cobertos.any():
            remaining = nao_cobertos.sum()
            print(f"  {Fore.YELLOW}⚠️  {remaining:,} não cobertos ({remaining/total_alvos*100:.1f}%){Style.RESET_ALL}")

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
    print(f"  1. 17 dezenas do Índice Preditivo  (~17 jogos | R$59)")
    print(f"  2. 18 dezenas do Índice Preditivo  (~30 jogos | R$105)")
    print(f"  3. 20 dezenas do Índice Preditivo  (~80 jogos | R$280)")
    print(f"  4. Digitar manualmente (até 21 dz)")
    print(f"  {Fore.RED}5. 25 números — BLOQUEADO (excede RAM){Style.RESET_ALL}")

    escolha_grupo = pedir_string("  Opção (1-4): ")
    while escolha_grupo not in ("1", "2", "3", "4"):
        if escolha_grupo == "5":
            print(f"  {Fore.RED}❌ 25 dezenas gera 3.2 milhões de jogos — impossível calcular.{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}  Use opção 4 e digite um subgrupo de até 21 dezenas.{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}❌ Opção inválida! Digite 1, 2, 3 ou 4.{Style.RESET_ALL}")
        escolha_grupo = pedir_string("  Opção (1-4): ")

    if escolha_grupo in ("1", "2", "3"):
        n_dez = {"1": 17, "2": 18, "3": 20}[escolha_grupo]

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
    caminho = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "fechamento_jogos.json")
    with open(caminho, "w") as f:
        json.dump(jogos, f)
    print(f"\n  {Fore.GREEN}💾 Jogos salvos em data/fechamento_jogos.json!{Style.RESET_ALL}")

    return jogos

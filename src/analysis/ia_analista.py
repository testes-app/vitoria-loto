"""
Módulo de IA Analista — Lotofácil Pro
Gera uma análise textual inteligente baseada no ranking preditivo e estatísticas.
"""

from colorama import Fore, Style


def exibir_analise_ia(ranking, stats, dia_hoje):
    """
    Exibe um resumo de IA com análise do dia atual.

    Args:
        ranking: Lista de tuplas [(jogo, score), ...]
        stats: Dicionário com estatísticas gerais
        dia_hoje: String com o dia da semana atual
    """
    print(f"\n{'═'*56}")
    print(f"  {Fore.CYAN}🧠 IA ANALISTA — LOTOFÁCIL PRO{Style.RESET_ALL}")
    print(f"{'═'*56}")

    total = stats.get("total_sorteios", 0)
    print(f"\n  {Fore.WHITE}📊 Base analisada: {Fore.GREEN}{total}{Fore.WHITE} sorteios{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}📅 Dia atual: {Fore.YELLOW}{dia_hoje}{Style.RESET_ALL}")

    # Top frequências
    freq = stats.get("frequencia", [])
    if freq:
        print(f"\n  {Fore.CYAN}🔥 Top 5 dezenas mais frequentes:{Style.RESET_ALL}")
        for num, pct in freq[:5]:
            barra = "█" * int(pct / 5)
            print(f"    {Fore.GREEN}{num:02d}{Style.RESET_ALL} → {pct:.1f}% {Fore.BLUE}{barra}{Style.RESET_ALL}")

    # Padrões do dia
    padroes = stats.get("padroes_dia", {})
    favoritas_dia = padroes.get(dia_hoje, [])
    if favoritas_dia:
        nums_str = ", ".join([f"{Fore.GREEN}{n:02d}{Style.RESET_ALL}" for n in favoritas_dia])
        print(f"\n  {Fore.YELLOW}📅 Favoritas para {dia_hoje}:{Style.RESET_ALL} {nums_str}")

    # Repetições
    rep = stats.get("repeticoes_mais_comum", 0)
    if rep:
        print(f"  {Fore.WHITE}🔄 Repetições mais comuns do último sorteio: {Fore.GREEN}{rep}{Style.RESET_ALL}")

    # Jogo recomendado (primeiro do ranking)
    if ranking:
        melhor_jogo, melhor_score = ranking[0]
        jogo_str = "  ".join([f"{Fore.GREEN}{n:02d}{Style.RESET_ALL}" for n in sorted(melhor_jogo)])
        print(f"\n  {Fore.YELLOW}🎯 JOGO RECOMENDADO:{Style.RESET_ALL}")
        print(f"  {jogo_str}")
        print(f"  {Fore.CYAN}PI: {melhor_score:.4f}{Style.RESET_ALL}")

        # Top 5 jogos
        print(f"\n  {Fore.CYAN}📋 Top 5 do ranking preditivo:{Style.RESET_ALL}")
        for i, (jogo, score) in enumerate(ranking[:5], 1):
            nums = " ".join([f"{n:02d}" for n in sorted(jogo)])
            print(f"    {Fore.WHITE}{i}. {nums}  →  PI: {Fore.GREEN}{score:.4f}{Style.RESET_ALL}")

    print(f"\n  {Fore.YELLOW}⚠️  Jogo responsável — resultados são estatísticos, não garantias.{Style.RESET_ALL}")
    print(f"{'═'*56}\n")

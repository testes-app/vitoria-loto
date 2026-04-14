"""
Módulo 5 — Aprendizado da AGI
Analisa o histórico de jogos e identifica padrões de sucesso.
Ajusta automaticamente a estratégia baseado nos resultados reais.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style
from src.analysis.memoria import historico_completo, resumo_semana

PREMIOS = {15: 1000000, 14: 1500, 13: 25, 12: 10, 11: 5}


def analisar_desempenho() -> dict:
    """Analisa o desempenho geral dos jogos registrados."""
    df = historico_completo()
    conferidos = df[df["conferido"] == 1]

    if conferidos.empty:
        return None

    total = len(conferidos)
    acertos = conferidos["acertos"].values

    return {
        "total_jogos": total,
        "media_acertos": float(np.mean(acertos)),
        "melhor": int(np.max(acertos)),
        "pior": int(np.min(acertos)),
        "acima_11": int((acertos >= 11).sum()),
        "acima_12": int((acertos >= 12).sum()),
        "acima_13": int((acertos >= 13).sum()),
        "taxa_11": float((acertos >= 11).mean() * 100),
        "taxa_12": float((acertos >= 12).mean() * 100),
        "taxa_13": float((acertos >= 13).mean() * 100),
        "total_investido": float(total * 3.50),
        "total_ganho": float(conferidos["premio"].sum()),
        "saldo_total": float(conferidos["saldo"].sum()),
        "roi": float((conferidos["premio"].sum() / (total * 3.50) - 1) * 100),
    }


def aprendizado_por_dia() -> dict:
    """Analisa qual dia da semana tem melhor desempenho."""
    df = historico_completo()
    conferidos = df[df["conferido"] == 1]

    if conferidos.empty:
        return {}

    resultado = {}
    for dia in conferidos["dia_semana"].unique():
        sub = conferidos[conferidos["dia_semana"] == dia]
        resultado[dia] = {
            "jogos": len(sub),
            "media_acertos": float(sub["acertos"].mean()),
            "saldo": float(sub["saldo"].sum()),
            "taxa_12": float((sub["acertos"] >= 12).mean() * 100),
        }
    return resultado


def aprendizado_semanal() -> list:
    """Analisa saldo por semana."""
    df = historico_completo()
    if df.empty:
        return []

    semanas = df.groupby("semana").agg(
        jogos=("id", "count"),
        custo=("custo", "sum"),
        premio=("premio", "sum"),
        saldo=("saldo", "sum"),
    ).reset_index()

    return semanas.to_dict("records")


def gerar_recomendacao() -> str:
    """Gera recomendação baseada no aprendizado."""
    desemp = analisar_desempenho()

    if desemp is None or desemp["total_jogos"] < 5:
        return "Poucos jogos registrados. Continue jogando para o sistema aprender!"

    recomendacoes = []

    # Analisa taxa de acerto
    if desemp["taxa_12"] >= 20:
        recomendacoes.append(f"✅ Excelente! Você acerta 12+ pontos em {desemp['taxa_12']:.0f}% dos jogos!")
    elif desemp["taxa_12"] >= 10:
        recomendacoes.append(f"🟡 Você acerta 12+ pontos em {desemp['taxa_12']:.0f}% dos jogos. Bom progresso!")
    else:
        recomendacoes.append(f"⚠️ Taxa de 12+ pontos baixa ({desemp['taxa_12']:.0f}%). Tente jogos do ranking preditivo.")

    # Analisa ROI
    if desemp["roi"] > 0:
        recomendacoes.append(f"✅ ROI positivo: +{desemp['roi']:.1f}%! Continue com a estratégia atual.")
    else:
        recomendacoes.append(f"📊 ROI: {desemp['roi']:.1f}%. Normal nas primeiras semanas — continue!")

    # Analisa por dia
    dias = aprendizado_por_dia()
    if dias:
        melhor_dia = max(dias.items(), key=lambda x: x[1]["media_acertos"])
        recomendacoes.append(f"📅 Melhor dia: {melhor_dia[0]} (média {melhor_dia[1]['media_acertos']:.1f} acertos)")

    return "\n  ".join(recomendacoes)


def exibir_aprendizado():
    """Exibe análise completa de aprendizado."""
    print(f"\n{Fore.CYAN}{'═'*65}")
    print(f"  🧠 MÓDULO 5 — APRENDIZADO DA AGI")
    print(f"{'═'*65}{Style.RESET_ALL}")

    desemp = analisar_desempenho()

    if desemp is None:
        print(f"\n  {Fore.YELLOW}Nenhum resultado conferido ainda.{Style.RESET_ALL}")
        print(f"  Registre jogos (opção 28) e confira resultados (opção 29)!")
        return

    # Desempenho geral
    print(f"\n{Fore.CYAN}  ── DESEMPENHO GERAL ──{Style.RESET_ALL}")
    print(f"  Total de jogos conferidos: {desemp['total_jogos']}")
    print(f"  Média de acertos:  {desemp['media_acertos']:.1f} pontos")
    print(f"  Melhor resultado:  {Fore.GREEN}{desemp['melhor']} pontos{Style.RESET_ALL}")

    print(f"\n  Taxa de acerto:")
    cor11 = Fore.GREEN if desemp['taxa_11'] >= 30 else Fore.YELLOW
    cor12 = Fore.GREEN if desemp['taxa_12'] >= 15 else Fore.YELLOW
    cor13 = Fore.GREEN if desemp['taxa_13'] >= 5 else Fore.WHITE
    print(f"  {cor11}11+ pontos: {desemp['acima_11']:3d}x ({desemp['taxa_11']:.1f}%){Style.RESET_ALL}")
    print(f"  {cor12}12+ pontos: {desemp['acima_12']:3d}x ({desemp['taxa_12']:.1f}%){Style.RESET_ALL}")
    print(f"  {cor13}13+ pontos: {desemp['acima_13']:3d}x ({desemp['taxa_13']:.1f}%){Style.RESET_ALL}")

    # Financeiro
    print(f"\n{Fore.CYAN}  ── FINANCEIRO ──{Style.RESET_ALL}")
    print(f"  Total investido: R${desemp['total_investido']:.2f}")
    print(f"  Total ganho:     R${desemp['total_ganho']:.2f}")
    cor_saldo = Fore.GREEN if desemp['saldo_total'] >= 0 else Fore.RED
    sinal = "+" if desemp['saldo_total'] >= 0 else ""
    print(f"  {cor_saldo}Saldo total:     {sinal}R${desemp['saldo_total']:.2f}{Style.RESET_ALL}")
    cor_roi = Fore.GREEN if desemp['roi'] >= 0 else Fore.RED
    print(f"  {cor_roi}ROI:             {desemp['roi']:+.1f}%{Style.RESET_ALL}")

    # Por dia da semana
    dias = aprendizado_por_dia()
    if dias:
        print(f"\n{Fore.CYAN}  ── POR DIA DA SEMANA ──{Style.RESET_ALL}")
        for dia, d in sorted(dias.items(), key=lambda x: x[1]['media_acertos'], reverse=True):
            cor = Fore.GREEN if d['saldo'] >= 0 else Fore.RED
            print(f"  {dia:<10} | média {d['media_acertos']:.1f}pts | "
                  f"12+: {d['taxa_12']:.0f}% | {cor}saldo: R${d['saldo']:+.2f}{Style.RESET_ALL}")

    # Semanas
    semanas = aprendizado_semanal()
    if len(semanas) > 1:
        print(f"\n{Fore.CYAN}  ── POR SEMANA ──{Style.RESET_ALL}")
        for s in semanas[-5:]:
            cor = Fore.GREEN if s['saldo'] >= 0 else Fore.RED
            print(f"  {s['semana']} | {int(s['jogos'])} jogos | "
                  f"{cor}saldo: R${s['saldo']:+.2f}{Style.RESET_ALL}")

    # Recomendação
    print(f"\n{Fore.CYAN}  ── RECOMENDAÇÃO DA AGI ──{Style.RESET_ALL}")
    rec = gerar_recomendacao()
    print(f"  {rec}")
    print(f"\n{Fore.CYAN}{'═'*65}{Style.RESET_ALL}")

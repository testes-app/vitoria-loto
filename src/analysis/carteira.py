"""
Módulo 6 — Carteira da AGI
Controla o orçamento semanal de R$21,00 (6 jogos x R$3,50).
Gerencia saldo, metas e alertas automáticos.
"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from colorama import Fore, Style
from src.analysis.memoria import historico_completo, resumo_semana

DB_PATH = Path(__file__).parent.parent.parent / "data" / "lotofacil.db"
ORCAMENTO_SEMANAL = 21.00
CUSTO_JOGO = 3.50
JOGOS_POR_SEMANA = 6


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_carteira():
    """Cria tabela de configuração da carteira."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS carteira_config (
            id              INTEGER PRIMARY KEY,
            orcamento       REAL DEFAULT 21.00,
            meta_semanal    REAL DEFAULT 0.0,
            saldo_acumulado REAL DEFAULT 0.0,
            semanas_positivas INTEGER DEFAULT 0,
            semanas_negativas INTEGER DEFAULT 0,
            ultima_atualizacao TEXT
        )
    """)
    # Insere config padrão se não existir
    conn.execute("""
        INSERT OR IGNORE INTO carteira_config
        (id, orcamento, meta_semanal, saldo_acumulado, ultima_atualizacao)
        VALUES (1, 21.00, 0.0, 0.0, ?)
    """, [datetime.now().strftime("%d/%m/%Y")])
    conn.commit()
    conn.close()


def obter_config() -> dict:
    init_carteira()
    conn = get_conn()
    row = conn.execute("SELECT * FROM carteira_config WHERE id=1").fetchone()
    conn.close()
    if row:
        return {
            "orcamento": row[1],
            "meta_semanal": row[2],
            "saldo_acumulado": row[3],
            "semanas_positivas": row[4],
            "semanas_negativas": row[5],
        }
    return {}


def atualizar_saldo_acumulado():
    """Recalcula saldo acumulado baseado em todos os jogos conferidos."""
    df = historico_completo()
    conferidos = df[df["conferido"] == 1]
    saldo = float(conferidos["saldo"].sum()) if not conferidos.empty else 0.0

    # Conta semanas positivas e negativas
    semanas = df.groupby("semana")["saldo"].sum()
    pos = int((semanas > 0).sum())
    neg = int((semanas <= 0).sum())

    conn = get_conn()
    conn.execute("""
        UPDATE carteira_config SET
        saldo_acumulado=?, semanas_positivas=?, semanas_negativas=?,
        ultima_atualizacao=? WHERE id=1
    """, [saldo, pos, neg, datetime.now().strftime("%d/%m/%Y")])
    conn.commit()
    conn.close()


def status_semana_atual() -> dict:
    """Retorna status detalhado da semana atual."""
    semana = datetime.now().strftime("%Y-W%W")
    df = historico_completo()
    sem = df[df["semana"] == semana]

    jogos_feitos = len(sem)
    jogos_restantes = JOGOS_POR_SEMANA - jogos_feitos
    gasto = jogos_feitos * CUSTO_JOGO
    orcamento_restante = ORCAMENTO_SEMANAL - gasto
    premio = float(sem["premio"].sum())
    saldo = float(sem["saldo"].sum())

    conferidos = sem[sem["conferido"] == 1]
    pendentes = sem[sem["conferido"] == 0]

    return {
        "semana": semana,
        "jogos_feitos": jogos_feitos,
        "jogos_restantes": jogos_restantes,
        "gasto": gasto,
        "orcamento_restante": orcamento_restante,
        "premio": premio,
        "saldo": saldo,
        "conferidos": len(conferidos),
        "pendentes": len(pendentes),
        "meta_atingida": saldo >= 0,
    }


def exibir_carteira():
    """Exibe painel completo da carteira."""
    atualizar_saldo_acumulado()
    config = obter_config()
    status = status_semana_atual()

    print(f"\n{Fore.CYAN}{'═'*65}")
    print(f"  💰 MÓDULO 6 — CARTEIRA DA AGI")
    print(f"{'═'*65}{Style.RESET_ALL}")

    # Status da semana atual
    print(f"\n{Fore.CYAN}  ── SEMANA ATUAL ({status['semana']}) ──{Style.RESET_ALL}")

    # Barra de progresso do orçamento
    jogos = status['jogos_feitos']
    barra = "█" * jogos + "░" * (JOGOS_POR_SEMANA - jogos)
    print(f"  Jogos:    [{barra}] {jogos}/{JOGOS_POR_SEMANA}")

    gasto_pct = (status['gasto'] / ORCAMENTO_SEMANAL * 100)
    print(f"  Gasto:    R${status['gasto']:.2f} / R${ORCAMENTO_SEMANAL:.2f} ({gasto_pct:.0f}%)")
    print(f"  Restante: R${status['orcamento_restante']:.2f} ({JOGOS_POR_SEMANA - jogos} jogos)")

    # Saldo da semana
    saldo = status['saldo']
    cor = Fore.GREEN if saldo >= 0 else Fore.RED
    sinal = "+" if saldo >= 0 else ""
    emoji = "✅" if saldo >= 0 else "📊"
    print(f"\n  {emoji} Saldo semana: {cor}{sinal}R${saldo:.2f}{Style.RESET_ALL}")

    if status['pendentes'] > 0:
        print(f"  {Fore.YELLOW}⏳ {status['pendentes']} jogo(s) aguardando resultado{Style.RESET_ALL}")

    # Alerta de orçamento
    if status['jogos_restantes'] == 0:
        print(f"\n  {Fore.YELLOW}⚠️  Orçamento da semana esgotado!{Style.RESET_ALL}")
        if saldo >= 0:
            print(f"  {Fore.GREEN}🎉 Semana POSITIVA! Meta atingida!{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}Semana negativa. Próxima semana será melhor!{Style.RESET_ALL}")
    elif status['jogos_restantes'] <= 2:
        print(f"  {Fore.YELLOW}⚠️  Apenas {status['jogos_restantes']} jogo(s) restante(s) no orçamento!{Style.RESET_ALL}")

    # Histórico acumulado
    print(f"\n{Fore.CYAN}  ── HISTÓRICO ACUMULADO ──{Style.RESET_ALL}")
    saldo_acc = config.get('saldo_acumulado', 0)
    cor_acc = Fore.GREEN if saldo_acc >= 0 else Fore.RED
    sinal_acc = "+" if saldo_acc >= 0 else ""
    print(f"  Saldo total:       {cor_acc}{sinal_acc}R${saldo_acc:.2f}{Style.RESET_ALL}")
    print(f"  Semanas positivas: {Fore.GREEN}{config.get('semanas_positivas', 0)}{Style.RESET_ALL}")
    print(f"  Semanas negativas: {Fore.RED}{config.get('semanas_negativas', 0)}{Style.RESET_ALL}")

    total_semanas = config.get('semanas_positivas', 0) + config.get('semanas_negativas', 0)
    if total_semanas > 0:
        taxa_pos = config['semanas_positivas'] / total_semanas * 100
        cor_taxa = Fore.GREEN if taxa_pos >= 50 else Fore.YELLOW
        print(f"  Taxa de semanas +: {cor_taxa}{taxa_pos:.0f}%{Style.RESET_ALL}")

    # Projeção mensal
    print(f"\n{Fore.CYAN}  ── PROJEÇÃO MENSAL ──{Style.RESET_ALL}")
    print(f"  Investimento mensal: R${ORCAMENTO_SEMANAL * 4:.2f}")
    if total_semanas > 0:
        media_semanal = saldo_acc / total_semanas if total_semanas > 0 else 0
        proj_mensal = media_semanal * 4
        cor_proj = Fore.GREEN if proj_mensal >= 0 else Fore.RED
        print(f"  Média por semana:    {cor_proj}{'+' if media_semanal >= 0 else ''}R${media_semanal:.2f}{Style.RESET_ALL}")
        print(f"  Projeção mensal:     {cor_proj}{'+' if proj_mensal >= 0 else ''}R${proj_mensal:.2f}{Style.RESET_ALL}")

    # Recomendação
    print(f"\n{Fore.CYAN}  ── RECOMENDAÇÃO ──{Style.RESET_ALL}")
    if status['jogos_restantes'] > 0 and saldo < 0:
        necessario = abs(saldo) + 3.50
        print(f"  Para fechar positivo: precisa ganhar R${necessario:.2f} nos próximos {status['jogos_restantes']} jogos")
        print(f"  Foque nos jogos com 12-13pts quentes do ranking preditivo!")
    elif saldo >= 0:
        print(f"  {Fore.GREEN}✅ Semana no positivo! Mantenha a estratégia.{Style.RESET_ALL}")
    else:
        print(f"  Use a opção 26 para carregar o ranking e escolher o melhor jogo!")

    print(f"\n{Fore.CYAN}{'═'*65}{Style.RESET_ALL}")

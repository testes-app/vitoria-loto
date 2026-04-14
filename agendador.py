"""
Agendador Automático da AGI — Lotofácil Pro
Roda automaticamente antes de cada sorteio.
Execute uma vez e ele cuida de tudo!

Uso: python3 agendador.py
"""
import sys
import time
import schedule
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

sys.path.insert(0, str(Path(__file__).parent))

from src.data.database import carregar_sorteios, ultimo_concurso
from src.data.scraper import atualizar_dados
from src.analysis.turbo import carregar_ranking_do_csv
from src.analysis.carteira import status_semana_atual
from src.analysis.aprendizado import analisar_desempenho

# Horários dos sorteios (Lotofácil)
HORARIO_SORTEIO = "20:00"
HORARIO_ALERTA  = "19:30"  # 30 min antes
HORARIO_SEGUNDA = "08:00"  # Resumo semanal


def cabecalho():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════╗
║    🤖 AGI AGENDADOR — LOTOFÁCIL PRO                  ║
║    Rodando automaticamente...                        ║
╚══════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")


def tarefa_pre_sorteio():
    """Roda 30 min antes do sorteio — sugere o jogo do dia."""
    now = datetime.now()
    dias = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
    dia = dias[now.weekday()]

    print(f"\n{Fore.CYAN}{'═'*55}")
    print(f"  🎯 PRÉ-SORTEIO — {dia} {now.strftime('%H:%M')}")
    print(f"{'═'*55}{Style.RESET_ALL}")

    # Atualiza dados
    print(f"  Atualizando dados...")
    n = atualizar_dados(verbose=False)
    if n > 0:
        print(f"  {Fore.GREEN}✅ {n} novos sorteios!{Style.RESET_ALL}")

    # Carrega ranking
    df = carregar_sorteios()
    ranking = carregar_ranking_do_csv(df)

    if not ranking:
        print(f"  {Fore.YELLOW}⚠️  Ranking não encontrado. Rode a opção 22 primeiro!{Style.RESET_ALL}")
        return

    # Encontra melhor jogo
    melhor = None
    for combo, c, pi in ranking[:20]:
        a12 = c.get("atraso12", 99)
        a13 = c.get("atraso13", 99)
        a11 = c.get("atraso11", 99)
        if a12 <= 10 and a11 <= 10:
            melhor = (combo, c, pi)
            break
    if melhor is None:
        melhor = ranking[0]

    combo, c, pi = melhor
    dz = "  ".join(f"{Fore.GREEN}{n:02d}{Style.RESET_ALL}" for n in combo)

    print(f"\n  🎯 JOGO RECOMENDADO PARA HOJE:")
    print(f"  {dz}")
    print(f"\n  PI: {pi:.4f}")
    print(f"  12pts: {c.get('atraso12',0)} sorteios atrás")
    print(f"  11pts: {c.get('atraso11',0)} sorteios atrás")

    # Status da carteira
    status = status_semana_atual()
    print(f"\n  💰 Carteira: {status['jogos_feitos']}/6 jogos | Saldo: {'+' if status['saldo']>=0 else ''}R${status['saldo']:.2f}")

    # Envia email se configurado
    try:
        from src.analysis.notificador import alerta_jogo_do_dia
        alerta_jogo_do_dia(ranking, dia)
        print(f"  {Fore.GREEN}📧 Email enviado!{Style.RESET_ALL}")
    except Exception:
        pass

    print(f"\n  {Fore.YELLOW}⏰ Sorteio em 30 minutos! Boa sorte! 🍀{Style.RESET_ALL}")


def tarefa_pos_sorteio():
    """Roda após o sorteio — atualiza dados."""
    print(f"\n{Fore.CYAN}  🔄 PÓS-SORTEIO — Atualizando dados...{Style.RESET_ALL}")
    n = atualizar_dados(verbose=False)
    if n > 0:
        print(f"  {Fore.GREEN}✅ Concurso {ultimo_concurso()} atualizado!{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}⚠️  Não esqueça de conferir seu jogo (opção 29)!{Style.RESET_ALL}")


def tarefa_resumo_semanal():
    """Roda toda segunda — envia resumo da semana."""
    now = datetime.now()
    if now.weekday() != 0:  # Só segunda
        return

    print(f"\n{Fore.CYAN}  📊 RESUMO SEMANAL{Style.RESET_ALL}")

    desemp = analisar_desempenho()
    status = status_semana_atual()

    saldo = status['saldo']
    print(f"  Saldo da semana: {'+' if saldo>=0 else ''}R${saldo:.2f}")
    if desemp:
        print(f"  ROI acumulado: {desemp.get('roi',0):+.1f}%")

    try:
        from src.analysis.notificador import alerta_saldo_semanal
        alerta_saldo_semanal()
        print(f"  {Fore.GREEN}📧 Resumo enviado por email!{Style.RESET_ALL}")
    except Exception:
        pass


def main():
    cabecalho()

    print(f"  {Fore.CYAN}Agendando tarefas...{Style.RESET_ALL}")

    # Agenda tarefas
    # Segunda a Sábado — pré-sorteio 19:30
    for dia in ["monday","tuesday","wednesday","thursday","friday","saturday"]:
        getattr(schedule.every(), dia).at(HORARIO_ALERTA).do(tarefa_pre_sorteio)
        getattr(schedule.every(), dia).at("20:30").do(tarefa_pos_sorteio)

    # Toda segunda às 8h — resumo semanal
    schedule.every().monday.at(HORARIO_SEGUNDA).do(tarefa_resumo_semanal)

    print(f"  {Fore.GREEN}✅ Agendador ativo!{Style.RESET_ALL}")
    print(f"\n  Tarefas programadas:")
    print(f"  {Fore.YELLOW}19:30{Style.RESET_ALL} — Sugestão do jogo do dia (seg-sáb)")
    print(f"  {Fore.YELLOW}20:30{Style.RESET_ALL} — Atualização pós-sorteio")
    print(f"  {Fore.YELLOW}08:00 seg{Style.RESET_ALL} — Resumo semanal")
    print(f"\n  {Fore.CYAN}Pressione Ctrl+C para parar.{Style.RESET_ALL}\n")

    # Loop principal
    while True:
        schedule.run_pending()
        now = datetime.now()
        print(f"  ⏰ {now.strftime('%d/%m/%Y %H:%M:%S')} — aguardando próxima tarefa...", end="\r")
        time.sleep(30)


if __name__ == "__main__":
    main()

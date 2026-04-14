"""
LOTOFÁCIL PRO — Automação Completa
Roda todo o fluxo automaticamente:
1. Atualiza dados
2. Treina modelos (se necessário)
3. Gera jogos Super Combo Turbo
4. Confere jogos anteriores
5. Envia relatório por email

Uso:
  python auto.py              → roda tudo
  python auto.py --so-jogos   → só gera jogos e envia email
  python auto.py --so-treino  → só treina os modelos
  python auto.py --status     → mostra status do sistema
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent
DATA_DIR  = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

JOGOS_PATH   = DATA_DIR / "ultimos_jogos.json"
STATUS_PATH  = DATA_DIR / "auto_status.json"


# ── Helpers ────────────────────────────────────────────────────────────

def log(msg: str, cor=Fore.CYAN):
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"{cor}  [{hora}] {msg}{Style.RESET_ALL}")


def salvar_status(dados: dict):
    with open(STATUS_PATH, "w") as f:
        json.dump(dados, f, indent=2, default=str)


def carregar_status() -> dict:
    if not STATUS_PATH.exists():
        return {}
    with open(STATUS_PATH) as f:
        return json.load(f)


def cabecalho():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════╗
║    🤖 LOTOFÁCIL PRO — AUTOMAÇÃO COMPLETA             ║
║    Fluxo: Dados → Treino → Jogos → Email             ║
╚══════════════════════════════════════════════════════╝{Style.RESET_ALL}""")


# ── Etapas ─────────────────────────────────────────────────────────────

def etapa_atualizar_dados() -> int:
    """Etapa 1 — Atualiza dados da Caixa."""
    log("📡 ETAPA 1 — Atualizando dados...", Fore.YELLOW)
    from src.data.database import init_db
    from src.data.scraper import atualizar_dados
    init_db()
    n = atualizar_dados(verbose=False)
    if n > 0:
        log(f"✅ {n} novos sorteios baixados!", Fore.GREEN)
    else:
        log("✅ Dados já atualizados.", Fore.GREEN)
    return n


def etapa_treinar(forcar=False) -> bool:
    """Etapa 2 — Treina modelos se necessário."""
    log("🧠 ETAPA 2 — Verificando modelos...", Fore.YELLOW)

    status = carregar_status()
    ultimo_treino = status.get("ultimo_treino", "nunca")

    # Treina se nunca treinou ou se forçado
    if not forcar and ultimo_treino != "nunca":
        # Verifica se treinou há menos de 7 dias
        try:
            dt = datetime.fromisoformat(ultimo_treino)
            dias = (datetime.now() - dt).days
            if dias < 7:
                log(f"✅ Modelos treinados há {dias} dias — pulando treino.", Fore.GREEN)
                return True
        except:
            pass

    log("🚀 Treinando todos os modelos...", Fore.CYAN)
    from src.models.trainer import Trainer
    trainer = Trainer()
    trainer.carregar_modelos()
    trainer.treinar_tudo(verbose=False)

    status["ultimo_treino"] = datetime.now().isoformat()
    salvar_status(status)
    log("✅ Modelos treinados e salvos!", Fore.GREEN)
    return True


def etapa_preditivo(forcar=False) -> bool:
    """Etapa 3 — Recalcula Índice Preditivo se necessário."""
    log("🔮 ETAPA 3 — Verificando Índice Preditivo...", Fore.YELLOW)

    status = carregar_status()
    ultimo_preditivo = status.get("ultimo_preditivo", "nunca")

    if not forcar and ultimo_preditivo != "nunca":
        try:
            dt = datetime.fromisoformat(ultimo_preditivo)
            dias = (datetime.now() - dt).days
            if dias < 3:
                log(f"✅ Índice Preditivo calculado há {dias} dias — usando CSV salvo.", Fore.GREEN)
                return True
        except:
            pass

    log("⚡ Calculando Índice Preditivo (17 dezenas)...", Fore.CYAN)
    log("   Isso leva ~5 minutos...", Fore.YELLOW)

    from src.data.database import carregar_sorteios
    from src.analysis.turbo import rodar_indice_preditivo
    df = carregar_sorteios()
    rodar_indice_preditivo(df, tamanho=17, top_n=500, verbose=False)

    status["ultimo_preditivo"] = datetime.now().isoformat()
    salvar_status(status)
    log("✅ Índice Preditivo calculado e salvo!", Fore.GREEN)
    return True


def etapa_gerar_jogos(n_jogos=10, top_n=50, peso_turbo=0.5) -> list:
    """Etapa 4 — Gera jogos Super Combo Turbo."""
    log("🏆 ETAPA 4 — Gerando jogos Super Combo Turbo...", Fore.YELLOW)

    from src.data.database import carregar_sorteios
    from src.analysis.turbo import carregar_ranking_do_csv
    from src.models.trainer import Trainer

    df = carregar_sorteios()
    trainer = Trainer()
    trainer.carregar_modelos()
    trainer._carregar_dados()

    # Carrega ranking
    ranking = carregar_ranking_do_csv(df)
    if not ranking:
        log("❌ Ranking não encontrado! Rode etapa_preditivo primeiro.", Fore.RED)
        return []

    trainer._ultimo_ranking_preditivo = ranking
    log(f"   Ranking carregado: {len(ranking)} combinações", Fore.CYAN)

    # Gera jogos
    jogos = trainer.gerar_jogos_turbo_super_combo(
        n_jogos=n_jogos,
        top_n=top_n,
        peso_turbo=peso_turbo,
        verbose=False
    )

    # Salva jogos
    with open(JOGOS_PATH, "w") as f:
        json.dump(jogos, f)

    log(f"✅ {len(jogos)} jogos gerados e salvos!", Fore.GREEN)
    for i, jogo in enumerate(jogos, 1):
        dz = "  ".join(f"{n:02d}" for n in jogo)
        print(f"  {Fore.CYAN}Jogo {i:02d}: {dz}{Style.RESET_ALL}")

    return jogos


def etapa_conferir(ultimos_n=10) -> dict:
    """Etapa 5 — Confere jogos anteriores."""
    log("✅ ETAPA 5 — Conferindo jogos anteriores...", Fore.YELLOW)

    if not JOGOS_PATH.exists():
        log("⚠️  Nenhum jogo salvo para conferir.", Fore.YELLOW)
        return {}

    from src.data.database import carregar_sorteios
    from src.analysis.stats import conferir_jogos

    with open(JOGOS_PATH) as f:
        jogos = json.load(f)

    df = carregar_sorteios()
    resultado = conferir_jogos(df, jogos, ultimos_n=ultimos_n)
    return resultado or {}


def etapa_email(jogos: list, resultado: dict = None):
    """Etapa 6 — Envia relatório completo por email."""
    log("📧 ETAPA 6 — Enviando relatório por email...", Fore.YELLOW)

    from src.analysis.notificador import enviar_email

    dias = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
    dia_hoje = dias[datetime.now().weekday()]
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Monta corpo do email
    linhas_jogos = "\n".join(
        f"  Jogo {i:02d}: {' '.join(f'{n:02d}' for n in jogo)}"
        for i, jogo in enumerate(jogos, 1)
    )

    corpo = f"""
🏆 SUPER COMBO TURBO — {dia_hoje.upper()}
Gerado em: {agora}
{'='*50}

🎯 JOGOS RECOMENDADOS PARA HOJE:
{linhas_jogos}

💡 COMO FORAM GERADOS:
  • Índice Preditivo (17 dezenas) — análise histórica
  • LSTM + Ensemble — modelos de ML treinados
  • Algoritmo Genético — otimização final
  • Peso Turbo: 50% ranking + 50% ML

💰 CUSTO ESTIMADO: R$ {len(jogos) * 3.50:.2f} ({len(jogos)} jogos × R$3,50)

🍀 Boa sorte!
"""

    ok = enviar_email(f"Jogos do dia — {dia_hoje}", corpo)
    if ok:
        log("✅ Email enviado com sucesso!", Fore.GREEN)
    else:
        log("⚠️  Falha no envio — verifique configuração (opção 33 no menu).", Fore.YELLOW)


def mostrar_status():
    """Mostra status atual do sistema."""
    from src.data.database import init_db, ultimo_concurso, carregar_sorteios
    init_db()

    status = carregar_status()
    ult = ultimo_concurso()
    df = carregar_sorteios()

    print(f"""
{Fore.CYAN}╔══════════════════════════════════════╗
║  📊 STATUS DO SISTEMA                ║
╚══════════════════════════════════════╝{Style.RESET_ALL}

  Banco de dados:
    Total de sorteios : {Fore.GREEN}{len(df)}{Style.RESET_ALL}
    Último concurso   : {Fore.GREEN}{ult}{Style.RESET_ALL}

  Modelos ML:
    Último treino     : {Fore.GREEN}{status.get('ultimo_treino', 'nunca')}{Style.RESET_ALL}

  Índice Preditivo:
    Último cálculo    : {Fore.GREEN}{status.get('ultimo_preditivo', 'nunca')}{Style.RESET_ALL}

  Jogos salvos:
    Arquivo           : {Fore.GREEN}{'✅ existe' if JOGOS_PATH.exists() else '❌ não existe'}{Style.RESET_ALL}
""")


# ── Fluxos principais ──────────────────────────────────────────────────

def fluxo_completo(n_jogos=10, top_n=50, peso_turbo=0.5,
                   forcar_treino=False, forcar_preditivo=False,
                   enviar=True):
    """Roda o fluxo completo de automação."""
    cabecalho()
    inicio = datetime.now()
    log("🚀 Iniciando fluxo completo...", Fore.CYAN)

    try:
        # 1. Atualiza dados
        etapa_atualizar_dados()

        # 2. Treina modelos
        etapa_treinar(forcar=forcar_treino)

        # 3. Índice Preditivo
        etapa_preditivo(forcar=forcar_preditivo)

        # 4. Gera jogos
        jogos = etapa_gerar_jogos(n_jogos=n_jogos, top_n=top_n,
                                   peso_turbo=peso_turbo)
        if not jogos:
            log("❌ Falha ao gerar jogos.", Fore.RED)
            return

        # 5. Confere jogos anteriores
        etapa_conferir(ultimos_n=10)

        # 6. Envia email
        if enviar:
            etapa_email(jogos)

        # Resumo final
        duracao = (datetime.now() - inicio).seconds
        print(f"""
{Fore.GREEN}╔══════════════════════════════════════╗
║  ✅ AUTOMAÇÃO CONCLUÍDA!             ║
╚══════════════════════════════════════╝{Style.RESET_ALL}
  Duração  : {duracao}s
  Jogos    : {len(jogos)}
  Arquivo  : {JOGOS_PATH}
""")

    except Exception as e:
        log(f"❌ Erro na automação: {e}", Fore.RED)
        import traceback
        traceback.print_exc()


def fluxo_so_jogos(n_jogos=10, top_n=50, peso_turbo=0.5, enviar=True):
    """Só gera jogos e envia email — sem treinar."""
    cabecalho()
    log("⚡ Fluxo rápido — só jogos...", Fore.CYAN)

    etapa_atualizar_dados()
    jogos = etapa_gerar_jogos(n_jogos=n_jogos, top_n=top_n,
                               peso_turbo=peso_turbo)
    if jogos and enviar:
        etapa_email(jogos)


# ── Entry point ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Lotofácil Pro — Automação Completa"
    )
    parser.add_argument("--so-jogos",      action="store_true",
                        help="Só gera jogos (sem treinar)")
    parser.add_argument("--so-treino",     action="store_true",
                        help="Só treina os modelos")
    parser.add_argument("--status",        action="store_true",
                        help="Mostra status do sistema")
    parser.add_argument("--forcar-treino", action="store_true",
                        help="Força novo treino mesmo se recente")
    parser.add_argument("--forcar-pred",   action="store_true",
                        help="Força novo cálculo do Índice Preditivo")
    parser.add_argument("--sem-email",     action="store_true",
                        help="Não envia email")
    parser.add_argument("--jogos",         type=int, default=10,
                        help="Quantos jogos gerar (padrão: 10)")
    parser.add_argument("--top-ranking",   type=int, default=50,
                        help="Quantos do ranking usar (padrão: 50)")
    parser.add_argument("--peso",          type=float, default=0.5,
                        help="Peso do ranking 0.0-1.0 (padrão: 0.5)")

    args = parser.parse_args()
    enviar = not args.sem_email

    if args.status:
        mostrar_status()

    elif args.so_treino:
        cabecalho()
        etapa_atualizar_dados()
        etapa_treinar(forcar=True)
        etapa_preditivo(forcar=True)

    elif args.so_jogos:
        fluxo_so_jogos(
            n_jogos=args.jogos,
            top_n=args.top_ranking,
            peso_turbo=args.peso,
            enviar=enviar
        )

    else:
        fluxo_completo(
            n_jogos=args.jogos,
            top_n=args.top_ranking,
            peso_turbo=args.peso,
            forcar_treino=args.forcar_treino,
            forcar_preditivo=args.forcar_pred,
            enviar=enviar
        )


if __name__ == "__main__":
    main()

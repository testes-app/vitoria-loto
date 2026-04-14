"""
Módulo 4 — Memória da AGI
Salva e consulta o histórico de jogos apostados, resultados e saldo.
"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style
from src.data.scraper import buscar_concurso, _descobrir_ultimo_concurso

DB_PATH = Path(__file__).parent.parent.parent / "data" / "lotofacil.db"

PREMIOS = {
    15: 1_000_000.00,
    14: 1_500.00,
    13: 30.00,
    12: 14.00,
    11: 7.00,
}


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_memoria():
    """Cria tabela de memória se não existir."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memoria_jogos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            data        TEXT,
            concurso    INTEGER,
            dia_semana  TEXT,
            dezenas     TEXT,
            acertos     INTEGER DEFAULT 0,
            premio      REAL DEFAULT 0.0,
            custo       REAL DEFAULT 3.50,
            saldo       REAL DEFAULT -3.50,
            conferido   INTEGER DEFAULT 0,
            semana      TEXT
        )
    """)
    conn.commit()
    conn.close()


def registrar_jogo(dezenas: list, concurso: int = 0,
                   data: str = None, dia_semana: str = None) -> int:
    """Registra um jogo apostado. Retorna o ID."""
    init_memoria()
    if data is None:
        data = datetime.now().strftime("%d/%m/%Y")
    if dia_semana is None:
        dias = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
        dia_semana = dias[datetime.now().weekday()]
    semana = datetime.now().strftime("%Y-W%W")
    dz_str = "-".join(f"{n:02d}" for n in sorted(dezenas))

    conn = get_conn()
    cursor = conn.execute("""
        INSERT INTO memoria_jogos
        (data, concurso, dia_semana, dezenas, custo, saldo, semana)
        VALUES (?, ?, ?, ?, 3.50, -3.50, ?)
    """, [data, concurso, dia_semana, dz_str, semana])
    jogo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jogo_id


def registrar_jogos_memoria(jogos: list):
    """Registra uma lista de jogos apostados de uma vez."""
    for jogo in jogos:
        registrar_jogo(jogo)


def conferir_resultado(jogo_id: int, acertos: int):
    """Atualiza resultado de um jogo após o sorteio."""
    premio = PREMIOS.get(acertos, 0.0)
    saldo = premio - 3.50

    conn = get_conn()
    conn.execute("""
        UPDATE memoria_jogos
        SET acertos=?, premio=?, saldo=?, conferido=1
        WHERE id=?
    """, [acertos, premio, saldo, jogo_id])
    conn.commit()
    conn.close()


def resumo_semana(semana: str = None) -> dict:
    """Retorna resumo financeiro da semana."""
    if semana is None:
        semana = datetime.now().strftime("%Y-W%W")

    conn = get_conn()
    df = pd.read_sql("""
        SELECT * FROM memoria_jogos WHERE semana=?
    """, conn, params=[semana])
    conn.close()

    if df.empty:
        return {"semana": semana, "jogos": 0, "custo": 0, "premio": 0, "saldo": 0}

    return {
        "semana": semana,
        "jogos": len(df),
        "custo": df["custo"].sum(),
        "premio": df["premio"].sum(),
        "saldo": df["saldo"].sum(),
        "acertos_medio": df[df["conferido"]==1]["acertos"].mean() if df["conferido"].sum() > 0 else 0,
        "melhor": df["acertos"].max(),
        "jogos_conferidos": df["conferido"].sum(),
    }


def historico_completo() -> pd.DataFrame:
    """Retorna todo o histórico de jogos."""
    init_memoria()
    conn = get_conn()
    df = pd.read_sql("""
        SELECT * FROM memoria_jogos ORDER BY id DESC
    """, conn)
    conn.close()
    return df


def exibir_memoria(ultimos_n: int = 10):
    """Exibe os últimos N jogos registrados."""
    df = historico_completo()

    print(f"\n{Fore.CYAN}{'═'*65}")
    print(f"  🧠 MEMÓRIA — HISTÓRICO DE JOGOS")
    print(f"{'═'*65}{Style.RESET_ALL}")

    if df.empty:
        print(f"  {Fore.YELLOW}Nenhum jogo registrado ainda.{Style.RESET_ALL}")
        print(f"  Use a opção 28 para registrar um jogo!")
        return

    print(f"\n  {'ID':>4}  {'Data':>12}  {'Conc':>6}  {'Ac':>3}  {'Prêmio':>10}  {'Dezenas':<45}")
    print(f"  {'─'*4}  {'─'*12}  {'─'*6}  {'─'*3}  {'─'*10}  {'─'*45}")

    for _, row in df.head(ultimos_n).iterrows():
        ac = int(row["acertos"])
        conf = bool(row["conferido"])
        premio = float(row["premio"])
        saldo = float(row["saldo"])

        if not conf:
            ac_str = f"{Fore.YELLOW}?{Style.RESET_ALL}"
            pr_str = f"{Fore.YELLOW}pendente{Style.RESET_ALL}"
        elif ac >= 13:
            ac_str = f"{Fore.GREEN}{ac}{Style.RESET_ALL}"
            pr_str = f"{Fore.GREEN}R${premio:.2f}{Style.RESET_ALL}"
        elif ac >= 11:
            ac_str = f"{Fore.YELLOW}{ac}{Style.RESET_ALL}"
            pr_str = f"{Fore.YELLOW}R${premio:.2f}{Style.RESET_ALL}"
        else:
            ac_str = f"{Fore.RED}{ac}{Style.RESET_ALL}"
            pr_str = f"{Fore.RED}R$0,00{Style.RESET_ALL}"

        dz_fmt = str(row["dezenas"]).replace("-", " ")
        print(f"  {int(row['id']):>4}  {row['data']:>12}  "
              f"{int(row['concurso']) if row['concurso'] else '?':>6}  "
              f"{ac_str:>3}  {pr_str:>10}  {Fore.CYAN}{dz_fmt:<45}{Style.RESET_ALL}")

    # Resumo semanal
    sem = resumo_semana()
    conn = get_conn()
    total_db = conn.execute("SELECT COUNT(*) FROM memoria_jogos").fetchone()[0]
    conn.close()

    print(f"\n{Fore.CYAN}  ── ESTATÍSTICAS DA MEMÓRIA ─────────────────{Style.RESET_ALL}")
    print(f"  Total Acumulado (Histórico): {Fore.YELLOW}{total_db} jogos{Style.RESET_ALL}")
    print(f"  Jogos nesta semana: {sem['jogos']}  |  Custo semanal: R${sem['custo']:.2f}")
    
    saldo_sem = sem['saldo']
    cor = Fore.GREEN if saldo_sem >= 0 else Fore.RED
    sinal = "+" if saldo_sem >= 0 else ""
    print(f"  Prêmios da semana: R${sem['premio']:.2f}  |  {cor}Saldo: {sinal}R${saldo_sem:.2f}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═'*65}{Style.RESET_ALL}")


def registrar_jogo_interativo():
    """Interface para registrar um jogo manualmente."""
    print(f"\n{Fore.CYAN}  📝 REGISTRAR JOGO{Style.RESET_ALL}")
    print(f"  Digite as 15 dezenas separadas por espaço:")
    entrada = input(f"  {Fore.GREEN}> {Style.RESET_ALL}").strip()

    try:
        dezenas = [int(x) for x in entrada.split()]
        if len(dezenas) != 15:
            print(f"  {Fore.RED}❌ Digite exatamente 15 números!{Style.RESET_ALL}")
            return
        if not all(1 <= n <= 25 for n in dezenas):
            print(f"  {Fore.RED}❌ Números entre 1 e 25!{Style.RESET_ALL}")
            return
    except ValueError:
        print(f"  {Fore.RED}❌ Entrada inválida!{Style.RESET_ALL}")
        return

    conc = input(f"  Concurso (Enter para deixar em branco): ").strip()
    concurso = int(conc) if conc.isdigit() else 0

    jogo_id = registrar_jogo(dezenas, concurso)
    dz_fmt = " ".join(f"{n:02d}" for n in sorted(dezenas))
    print(f"\n  {Fore.GREEN}✅ Jogo #{jogo_id} registrado!{Style.RESET_ALL}")
    print(f"  Dezenas: {Fore.CYAN}{dz_fmt}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Após o sorteio use a opção 29 para conferir o resultado.{Style.RESET_ALL}")


def conferir_resultado_interativo():
    """Interface para conferir resultado de um jogo com busca automática."""
    df = historico_completo()
    pendentes = df[df["conferido"] == 0]

    if pendentes.empty:
        print(f"  {Fore.YELLOW}Nenhum jogo pendente de conferência.{Style.RESET_ALL}")
        return

    print(f"\n{Fore.CYAN}  ── JOGOS PENDENTES ──{Style.RESET_ALL}")
    for _, row in pendentes.iterrows():
        print(f"  #{int(row['id'])} | {row['data']} | {row['dezenas']} | Conc: {int(row['concurso']) if row['concurso'] else '?'}")

    jogo_id_input = input(f"\n  {Fore.GREEN}ID do jogo para conferir (ou Enter p/ cancelar): {Style.RESET_ALL}").strip()
    if not jogo_id_input: return
    if not jogo_id_input.isdigit():
        print(f"  {Fore.RED}❌ ID inválido!{Style.RESET_ALL}")
        return

    jogo_id = int(jogo_id_input)
    jogo = df[df["id"] == jogo_id]
    if jogo.empty:
        print(f"  {Fore.RED}❌ Jogo não encontrado!{Style.RESET_ALL}")
        return

    jogo = jogo.iloc[0]
    num_aposta = [int(n) for n in str(jogo["dezenas"]).split("-")]
    conc_alvo = int(jogo["concurso"]) if jogo["concurso"] else 0

    print(f"\n  {Fore.CYAN}🔍 Buscando resultado oficial...{Style.RESET_ALL}")
    
    # Se não tem concurso definido, tenta o último
    if conc_alvo == 0:
        conc_alvo = _descobrir_ultimo_concurso()
        if not conc_alvo:
            print(f"  {Fore.RED}❌ Falha ao conectar com a API.{Style.RESET_ALL}")
            return

    resultado_data = buscar_concurso(conc_alvo)
    if not resultado_data:
        print(f"  {Fore.RED}❌ Resultado do concurso {conc_alvo} ainda não disponível.{Style.RESET_ALL}")
        return

    from src.data.scraper import parse_concurso
    parsed = parse_concurso(resultado_data)
    if not parsed:
        print(f"  {Fore.RED}❌ Erro ao processar dados da API.{Style.RESET_ALL}")
        return

    conc_oficial, data_oficial, dezenas_oficiais = parsed
    
    # Cálculo de acertos
    set_aposta = set(num_aposta)
    set_oficial = set(dezenas_oficiais)
    acertos = len(set_aposta & set_oficial)
    
    # Confirmação visual
    print(f"  {Fore.GREEN}✅ Resultado encontrado: Concurso {conc_oficial} ({data_oficial}){Style.RESET_ALL}")
    dz_res_str = " ".join(f"{n:02d}" for n in sorted(dezenas_oficiais))
    print(f"  Dezenas Oficiais: {Fore.YELLOW}{dz_res_str}{Style.RESET_ALL}")

    conferir_resultado(jogo_id, acertos)
    
    premio = PREMIOS.get(acertos, 0.0)
    saldo = premio - 3.50
    cor = Fore.GREEN if saldo >= 0 else Fore.RED
    
    print(f"\n  {Fore.GREEN}✅ Conferência concluída!{Style.RESET_ALL}")
    print(f"  Acertos: {Fore.CYAN}{acertos}{Style.RESET_ALL} | Prêmio: {Fore.GREEN}R${premio:.2f}{Style.RESET_ALL} | {cor}Saldo: R${saldo:+.2f}{Style.RESET_ALL}")

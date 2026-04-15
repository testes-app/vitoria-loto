"""
Análises estatísticas completas da Lotofácil.
"""
import numpy as np
import pandas as pd
from collections import Counter
from itertools import combinations
from colorama import Fore, Style, Back

NUMEROS = list(range(1, 26))


def _extrair_lista_sorteios(df: pd.DataFrame) -> list:
    """Retorna lista de sets com os números de cada sorteio."""
    num_cols = [f"n{i:02d}" for i in range(1, 16)]
    return [set(row[num_cols].astype(int).tolist()) for _, row in df.iterrows()]


# ─────────────────────────────────────────────
# 1. Frequência geral
# ─────────────────────────────────────────────
def frequencia_geral(df: pd.DataFrame):
    sorteios = _extrair_lista_sorteios(df)
    freq = Counter()
    for s in sorteios:
        freq.update(s)

    total = len(sorteios)
    print(f"\n{Fore.CYAN}{'─'*50}")
    print(f"  📊 FREQUÊNCIA GERAL — {total} sorteios")
    print(f"{'─'*50}{Style.RESET_ALL}")

    ranking = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    for i, (num, cnt) in enumerate(ranking):
        pct = cnt / total * 100
        barra = "█" * int(pct / 2)
        cor = Fore.GREEN if pct > 58 else (Fore.YELLOW if pct > 54 else Fore.RED)
        print(f"  {cor}Nº {num:02d}: {barra:<30} {cnt:4d}x ({pct:.1f}%){Style.RESET_ALL}")


# ─────────────────────────────────────────────
# 2. Análise de atraso
# ─────────────────────────────────────────────
def analise_atraso(df: pd.DataFrame):
    sorteios = _extrair_lista_sorteios(df)
    atraso = {}

    for num in NUMEROS:
        a = 0
        for s in reversed(sorteios):
            if num in s:
                break
            a += 1
        atraso[num] = a

    print(f"\n{Fore.CYAN}{'─'*50}")
    print(f"  ⏳ ANÁLISE DE ATRASO")
    print(f"{'─'*50}{Style.RESET_ALL}")

    ranking = sorted(atraso.items(), key=lambda x: x[1], reverse=True)
    for num, a in ranking:
        cor = Fore.RED if a > 10 else (Fore.YELLOW if a > 5 else Fore.GREEN)
        print(f"  {cor}Nº {num:02d}: atrasado há {a:3d} sorteios{Style.RESET_ALL}")


# ─────────────────────────────────────────────
# 3. Parceiros de um número
# ─────────────────────────────────────────────
def parceiros_numero(df: pd.DataFrame, numero: int):
    sorteios = _extrair_lista_sorteios(df)
    aparicoes = [s for s in sorteios if numero in s]
    parceiros = Counter()
    for s in aparicoes:
        for n in s:
            if n != numero:
                parceiros[n] += 1

    print(f"\n{Fore.CYAN}{'─'*50}")
    print(f"  🔍 PARCEIROS DO NÚMERO {numero:02d} ({len(aparicoes)} aparições)")
    print(f"{'─'*50}{Style.RESET_ALL}")

    for num, cnt in parceiros.most_common(10):
        pct = cnt / len(aparicoes) * 100
        print(f"  Nº {num:02d}: {cnt:4d}x ({pct:.1f}%)")


# ─────────────────────────────────────────────
# 4. Padrões por dia da semana
# ─────────────────────────────────────────────
def padroes_dia_semana(df: pd.DataFrame):
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    freq_dia = {d: Counter() for d in dias}
    count_dia = Counter()

    for _, row in df.iterrows():
        try:
            dow = pd.to_datetime(row["data"], dayfirst=True).dayofweek
            dia = dias[dow]
            count_dia[dia] += 1
            num_cols = [f"n{i:02d}" for i in range(1, 16)]
            for c in num_cols:
                freq_dia[dia][int(row[c])] += 1
        except Exception:
            continue

    print(f"\n{Fore.CYAN}{'─'*50}")
    print(f"  📅 PADRÕES POR DIA DA SEMANA")
    print(f"{'─'*50}{Style.RESET_ALL}")

    for dia in dias:
        n = count_dia[dia]
        if n == 0:
            continue
        top5 = freq_dia[dia].most_common(5)
        nums = ", ".join([f"{num:02d}({cnt})" for num, cnt in top5])
        print(f"  {Fore.YELLOW}{dia:<10}{Style.RESET_ALL} ({n:4d} sorteios) Top5: {nums}")


# ─────────────────────────────────────────────
# 5. Pares mais frequentes
# ─────────────────────────────────────────────
def pares_frequentes(df: pd.DataFrame, top_n=20):
    sorteios = _extrair_lista_sorteios(df)
    pares = Counter()
    for s in sorteios:
        for par in combinations(sorted(s), 2):
            pares[par] += 1

    print(f"\n{Fore.CYAN}{'─'*50}")
    print(f"  👫 TOP {top_n} PARES MAIS FREQUENTES")
    print(f"{'─'*50}{Style.RESET_ALL}")

    for par, cnt in pares.most_common(top_n):
        pct = cnt / len(sorteios) * 100
        print(f"  {par[0]:02d}-{par[1]:02d}: {cnt:4d}x ({pct:.1f}%)")


# ─────────────────────────────────────────────
# 6. Trios mais frequentes
# ─────────────────────────────────────────────
def trios_frequentes(df: pd.DataFrame, top_n=15):
    sorteios = _extrair_lista_sorteios(df)
    trios = Counter()
    for s in sorteios:
        for trio in combinations(sorted(s), 3):
            trios[trio] += 1

    print(f"\n{Fore.CYAN}{'─'*50}")
    print(f"  🔺 TOP {top_n} TRIOS MAIS FREQUENTES")
    print(f"{'─'*50}{Style.RESET_ALL}")

    for trio, cnt in trios.most_common(top_n):
        pct = cnt / len(sorteios) * 100
        print(f"  {trio[0]:02d}-{trio[1]:02d}-{trio[2]:02d}: {cnt:4d}x ({pct:.1f}%)")


# ─────────────────────────────────────────────
# 7. Sequências consecutivas
# ─────────────────────────────────────────────
def analise_sequencias(df: pd.DataFrame):
    sorteios = _extrair_lista_sorteios(df)
    contagens = Counter()
    for s in sorteios:
        nums = sorted(s)
        seq = 1
        max_seq = 1
        for i in range(1, len(nums)):
            if nums[i] == nums[i-1] + 1:
                seq += 1
                max_seq = max(max_seq, seq)
            else:
                seq = 1
        contagens[max_seq] += 1

    total = len(sorteios)
    print(f"\n{Fore.CYAN}{'─'*50}")
    print(f"  📈 DISTRIBUIÇÃO DE SEQUÊNCIAS CONSECUTIVAS")
    print(f"{'─'*50}{Style.RESET_ALL}")

    for seq_len in sorted(contagens.keys()):
        cnt = contagens[seq_len]
        pct = cnt / total * 100
        print(f"  Máx sequência {seq_len}: {cnt:4d}x ({pct:.1f}%)")


# ─────────────────────────────────────────────
# 8. Repetição do sorteio anterior
# ─────────────────────────────────────────────
def repeticao_anterior(df: pd.DataFrame):
    sorteios = _extrair_lista_sorteios(df)
    reps = Counter()
    for i in range(1, len(sorteios)):
        r = len(sorteios[i] & sorteios[i-1])
        reps[r] += 1

    total = len(sorteios) - 1
    print(f"\n{Fore.CYAN}{'─'*50}")
    print(f"  🔄 REPETIÇÕES DO SORTEIO ANTERIOR")
    print(f"{'─'*50}{Style.RESET_ALL}")

    for n_rep in sorted(reps.keys()):
        cnt = reps[n_rep]
        pct = cnt / total * 100
        print(f"  {n_rep:2d} repetições: {cnt:4d}x ({pct:.1f}%)")


# ─────────────────────────────────────────────
# 9. Distribuição por quadrante
# ─────────────────────────────────────────────
def distribuicao_quadrante(df: pd.DataFrame):
    """
    Analisa a força dos quadrantes (Top Left, Top Right, Bottom Left, Bottom Right)
    """
    def get_quadrante(n):
        row = (n - 1) // 5 
        col = (n - 1) % 5 
        v = "T" if row < 3 else "B"
        h = "L" if col < 3 else "R"
        return v + h

    sorteios = []
    for _, row in df.iterrows():
        s = set()
        for i in range(1, 16):
            s.add(row[f'n{i:02d}'])
        sorteios.append(s)

    dist = Counter()
    for s in sorteios:
        for n in s:
            dist[get_quadrante(n)] += 1

    total_nums = len(sorteios) * 15
    print(f"\n{Fore.CYAN}{'─'*50}")
    print(f"  🗺️  DISTRIBUIÇÃO POR QUADRANTE (Histórico)")
    print(f"{'─'*50}{Style.RESET_ALL}")

    nomes = {"TL": "Superior Esq", "TR": "Superior Dir",
             "BL": "Inferior Esq", "BR": "Inferior Dir"}
    for q, nome in nomes.items():
        cnt = dist[q]
        pct = cnt / total_nums * 100
        print(f"  {nome:15}: {cnt:6d}x ({pct:.1f}%)")

def radar_atraso_reis(df: pd.DataFrame, dados_hall: dict):
    print(f"\n{Fore.CYAN}╔{'═'*62}╗")
    print(f"║ 📡 RADAR DE JEJUM DOS REIS (POTENCIAL DE ACERTO)           ║")
    print(f"╚{'═'*62}╝{Style.RESET_ALL}")
    
    lista_sorteios = _extrair_lista_sorteios(df)

    info_reis = []
    for k in ["15", "14", "13", "12", "11"]:
        if k in dados_hall:
            rei = dados_hall[k]
            dezenas_rei = set(rei["dezenas"])
            atraso = 0
            
            # Calcular Atraso
            for i in range(len(lista_sorteios)-1, -1, -1):
                if len(dezenas_rei & lista_sorteios[i]) >= 11: break
                atraso += 1
            
            # Calcular Média Histórica (Todos os Sorteios)
            todos_acertos = []
            for s in lista_sorteios:
                todos_acertos.append(len(dezenas_rei & s))
            media = sum(todos_acertos) / len(todos_acertos) if todos_acertos else 0
            
            info_reis.append({
                "titulo": rei["titulo"], 
                "atraso": atraso, 
                "media": media,
                "dezenas": sorted(list(dezenas_rei))
            })

    # Descobrir o maior atraso
    max_atraso = max(r["atraso"] for r in info_reis) if info_reis else 0

    print(f"  {Fore.WHITE}🎯 Análise de Oportunidade (Foco em Atrasos Longos):{Style.RESET_ALL}\n")

    for r in info_reis:
        # Só fica Vermelho quem tem o MAIOR atraso e esse atraso é > 0
        if r["atraso"] == max_atraso and max_atraso > 0:
            cor = Fore.RED
            status = f"🚨 ALERTA CRÍTICO: {r['atraso']} sorteios"
            bg = Back.RED + Fore.WHITE
        elif r["atraso"] == 0:
            cor = Fore.GREEN
            status = "🔥 QUENTE (Pontuou Ontem)"
            bg = Back.GREEN + Fore.BLACK
        else:
            cor = Fore.WHITE
            status = f"⏳ Jejum: {r['atraso']} sorteios"
            bg = ""
        
        # Calcular Ciclo para colorir dezenas (Igual ao Caçador de Ciclo)
        vistos = set()
        for s in lista_sorteios:
            hits = s & dezenas_rei
            for h in hits:
                if vistos == dezenas_rei: vistos = set()
                vistos.add(h)
        faltantes = dezenas_rei - vistos
        
        # Formatar dezenas com cores de ciclo
        dz_formatted = []
        for d in r["dezenas"]:
            if d in faltantes:
                dz_formatted.append(f"{Back.RED}{Fore.WHITE}{d:02d}{Style.RESET_ALL}")
            else:
                dz_formatted.append(f"{Fore.GREEN}{d:02d}{Style.RESET_ALL}")
        dz_str = " ".join(dz_formatted)

        print(f"  {Fore.YELLOW}👑 {r['titulo']:12}{Style.RESET_ALL} │ {Fore.CYAN}Média: {r['media']:.1f}{Style.RESET_ALL} │ {cor}{status}{Style.RESET_ALL}")
        print(f"  └─ {dz_str}\n")

    if max_atraso > 0:
        print(f"  {Fore.MAGENTA}💡 ESTRATÉGIA:{Style.RESET_ALL}")
        print(f"  Dê preferência aos jogos com {Fore.RED}MAIOR JEJUM{Style.RESET_ALL}. A estatística")
        print(f"  indica que a tendência de retorno aumenta a cada sorteio falho.")
    
    print(f"\n  {Back.RED}  {Style.RESET_ALL} = Dezenas Pendentes (Faltam no Ciclo)")
    print(f"  {Fore.GREEN}00{Style.RESET_ALL} = Dezenas de Reforço (Já saíram no Ciclo)")


def listar_intervalos_reis(df: pd.DataFrame, dados_hall: dict):
    print(f"\n{Fore.CYAN}╔{'═'*62}╗")
    print(f"║ 📅 HISTÓRICO DE INTERVALOS (PONTUAÇÕES RECENTES)           ║")
    print(f"╚{'═'*62}╝{Style.RESET_ALL}")
    
    lista_sorteios = _extrair_lista_sorteios(df)
    concursos = df['concurso'].tolist()
    
    for k in ["15", "14", "13", "12", "11"]:
        if k in dados_hall:
            rei = dados_hall[k]
            dezenas_rei = set(rei["dezenas"])
            print(f"\n  {Fore.BLACK}{Back.YELLOW} 👑 {rei['titulo']} {Style.RESET_ALL}")
            
            aparicoes = []
            ultimo_idx = None
            intervalos = []
            
            for idx, s in enumerate(lista_sorteios):
                acertos = len(dezenas_rei & s)
                if acertos >= 11:
                    if ultimo_idx is not None:
                        intervalo = idx - ultimo_idx
                        intervalos.append(intervalo)
                    else:
                        intervalo = 0 
                    
                    aparicoes.append({
                        "concurso": concursos[idx],
                        "pontos": acertos,
                        "intervalo": intervalo
                    })
                    ultimo_idx = idx
            
            if not aparicoes:
                print("    Nenhuma pontuação >= 11 registrada.")
                continue
            
            if intervalos:
                media = sum(intervalos) / len(intervalos)
                max_int = max(intervalos)
                min_int = min(intervalos)
                frequencia = len(aparicoes) / len(lista_sorteios) * 100
            else:
                media = max_int = min_int = frequencia = 0
                
            print(f"    {Fore.WHITE}Stats: Média {media:.1f} | Máx {max_int} | Min {min_int} | Freq {frequencia:.1f}%{Style.RESET_ALL}")
            
            print(f"    {'Concurso':<10} │ {'Acertos':<8} │ {'Delay':<10}")
            print(f"    {'─'*10}─┼──{'─'*7}─┼──{'─'*10}")
            
            # Mostrar os últimos 15 hits para cada rei (reduzido para caber bem)
            exibir = aparicoes[-15:]
            for r in exibir:
                p = r['pontos']
                c = r['concurso']
                i = r['intervalo']
                
                if p >= 14: cor = Fore.MAGENTA
                elif p == 13: cor = Fore.GREEN
                elif p == 12: cor = Fore.YELLOW
                else: cor = Fore.CYAN
                
                cor_int = Fore.RED if i > media * 2.5 and i > 5 else (Fore.YELLOW if i > media * 1.5 else Fore.WHITE)
                
                int_str = f"{i:>4} draws" if i > 0 else "  --    "
                print(f"    {Fore.WHITE}{c:<10}{Style.RESET_ALL} │ {cor}{p:>2} pts{Style.RESET_ALL}    │ {cor_int}{int_str}{Style.RESET_ALL}")


def exibir_mapa_calor_reis(df: pd.DataFrame, dados_hall: dict, ultimos_n: int = 30):
    print(f"\n{Fore.CYAN}╔{'═'*62}╗")
    print(f"║ 📊 MAPA DE CALOR: ÚLTIMOS {ultimos_n:2d} SORTEIOS (ELITE DOS REIS)     ║")
    print(f"╚{'═'*62}╝{Style.RESET_ALL}")
    
    # Pegar os últimos N sorteios do dataframe
    df_recent = df.tail(ultimos_n).copy()
    lista_sorteios = _extrair_lista_sorteios(df_recent)
    concursos = df_recent['concurso'].tolist()
    
    # Cores fixas para cada Rei para facilitar a distinção visual
    cores_reis = {
        "15": Fore.LIGHTBLUE_EX,
        "14": Fore.LIGHTGREEN_EX,
        "13": Fore.LIGHTYELLOW_EX,
        "12": Fore.LIGHTMAGENTA_EX,
        "11": Fore.LIGHTCYAN_EX
    }
    
    # Cabeçalho da Tabela (Alinhado com o prefixo '  ' ou 'X ')
    # Prefixo(2) + CONC(6) + " │" (2) = 10 chars
    header_base = f"  {Fore.WHITE}{'CONC.':<6} │"
    header_reis = ""
    for k in ["15", "14", "13", "12", "11"]:
        cor = cores_reis[k]
        header_reis += f" {cor}REI {k}{Style.RESET_ALL} │"
    
    print(header_base + header_reis)
    # Comprimento visível: 2 + 6 + 2 (base) + 5 * 9 (reis) = 10 + 45 = 55
    print("  " + "─" * 53)
    
    # Linhas (do mais recente para o mais antigo)
    for i in range(len(lista_sorteios)-1, -1, -1):
        conc = concursos[i]
        sorteio = lista_sorteios[i]
        
        # Verificar se houve algum premiado na linha toda
        alguem_premiado = False
        premiados_na_linha = 0
        for k in ["15", "14", "13", "12", "11"]:
            if k in dados_hall:
                dezenas = set(dados_hall[k]["dezenas"])
                if len(dezenas & sorteio) >= 11:
                    alguem_premiado = True
                    premiados_na_linha += 1
        
        # Prefixo da linha (X se ninguém ganhou, espaço se alguém ganhou)
        if not alguem_premiado:
            prefixo = f"{Fore.RED}X {Style.RESET_ALL}"
            cor_conc = Fore.RED
        else:
            prefixo = "  "
            cor_conc = Fore.WHITE
            
        row = f"{prefixo}{cor_conc}{conc:<6}{Fore.WHITE} │"
        
        for k in ["15", "14", "13", "12", "11"]:
            if k in dados_hall:
                dezenas = set(dados_hall[k]["dezenas"])
                pontos = len(dezenas & sorteio)
                cor_rei = cores_reis[k]
                
                if pontos >= 11:
                    # Se pontuou, destaque com cor vibrante
                    # Usar negrito se for 13+
                    estilo = Style.BRIGHT if pontos >= 13 else ""
                    row += f" {estilo}{cor_rei}{pontos:02d} pts{Style.RESET_ALL} │"
                else:
                    # Se não pontuou, usa cinza apagado
                    row += f" {Style.DIM}{pontos:02d} pts{Style.RESET_ALL} │"
            else:
                row += f" {'--':^8} │"
        
        print(row)
    
    print("  " + "─" * 53)
    print(f"  {Fore.YELLOW}Legenda: {Style.BRIGHT}PONTUOU (11+ pts){Style.RESET_ALL} {Style.DIM}│ Sem Ponto (<11 pts){Style.RESET_ALL}")

def exibir_mapa_calor_todos_reis(df: pd.DataFrame, dados_halls: dict, ultimos_n: int = 30):
    """
    Painel de Performance Elite v3.2: Foco em legibilidade e clareza.
    """
    LIMIARES = {"17": 12, "18": 13, "19": 13, "20": 14}
    CORES = {
        "17": Fore.CYAN,
        "18": Fore.GREEN,
        "19": Fore.YELLOW,
        "20": Fore.LIGHTRED_EX,
    }

    df_recent = df.tail(ultimos_n).copy()
    lista_sorteios = _extrair_lista_sorteios(df_recent)
    concursos = df_recent['concurso'].tolist()

    # Largura total para 5 colunas de reis por bloco
    width = 138
    print(f"\n{Fore.WHITE}┌{'─'*width}┐")
    titulo = f"📊 PAINEL DE PERFORMANCE DOS REIS — ÚLTIMOS {ultimos_n} SORTEIOS (ELITE)"
    print(f"│ {titulo.center(width - 2)} │")
    print(f"└{'─'*width}┘{Style.RESET_ALL}")

    # Cabeçalho Duplo
    h1 = f"  {' ':^7} │"
    h2 = f"  {'CONC.':<7} │"
    
    for e in ["17", "18", "19", "20"]:
        cor = CORES[e]
        label = f"{e} DEZENAS"
        h1 += f"{cor}{label:^31}{Style.RESET_ALL} │"
        for k in ["15", "14", "13", "12", "11"]:
            h2 += f" {cor}R{k:<2}{Style.RESET_ALL}   "
        h2 = h2[:-2] + "│"
    
    print(h1)
    print(h2)
    print("  " + "─" * (len(h2) - 3))

    # Linhas
    for i in range(len(lista_sorteios) - 1, -1, -1):
        conc = concursos[i]
        sorteio = lista_sorteios[i]
        
        flags_vitoria = [] # Para o prefixo X
        secoes = []
        for e in ["17", "18", "19", "20"]:
            limiar = LIMIARES[e]
            cor_e = CORES[e]
            bloco_dz = ""
            if e in dados_halls:
                for k in ["15", "14", "13", "12", "11"]:
                    if k in dados_halls[e]:
                        dezenas = set(dados_halls[e][k]["dezenas"])
                        pts = len(dezenas & sorteio)
                        ganhou = pts >= limiar
                        flags_vitoria.append(ganhou)
                        
                        # Definição do Estilo Gradual
                        if pts >= 15:
                            style = Fore.YELLOW + Style.BRIGHT # OURO para 15 pts
                        elif ganhou:
                            style = cor_e + Style.BRIGHT       # BRILHANTE para acertos de Elite
                        elif pts >= 11:
                            style = cor_e + Style.NORMAL       # VÍVIDO para 11-12 pts
                        else:
                            style = cor_e + Style.DIM          # APAGADO para baixa pontuação
                        
                        bloco_dz += f" {style}{pts:02d}pts{Style.RESET_ALL} "
                    else:
                        bloco_dz += f" {'--pts':^7}"
            else:
                bloco_dz = " " * 31
            secoes.append(bloco_dz + "│")

        prefixo = f"{Fore.RED}✗ {Style.RESET_ALL}" if not any(flags_vitoria) else "  "
        print(f"{prefixo}{conc:<7} │" + "".join(secoes))

    print("  " + "─" * (len(h2) - 3))
    print(f"  {Fore.LIGHTBLACK_EX}Legenda de Performance:{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}15pts (MÁX){Style.RESET_ALL} │ {Style.BRIGHT}Brilhante (Elite){Style.RESET_ALL} │ {Style.NORMAL}Normal (Premios 11+){Style.RESET_ALL} │ {Style.DIM}Apagado (<11pts){Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Cores: {CORES['17']}17DZ{Style.RESET_ALL} │ {CORES['18']}18DZ{Style.RESET_ALL} │ {CORES['19']}19DZ{Style.RESET_ALL} │ {CORES['20']}20DZ{Style.RESET_ALL}")








# ─────────────────────────────────────────────
# Exibe um jogo formatado
# ─────────────────────────────────────────────
def exibir_jogos(jogos: list, titulo: str = "JOGOS GERADOS"):
    print(f"\n{Fore.CYAN}{'═'*50}")
    print(f"  🎯 {titulo}")
    print(f"{'═'*50}{Style.RESET_ALL}")
    for i, jogo in enumerate(jogos, 1):
        nums = "  ".join([f"{Fore.GREEN}{n:02d}{Style.RESET_ALL}" for n in jogo])
        print(f"  Jogo {i}: {nums}")
    print(f"{Fore.CYAN}{'═'*50}{Style.RESET_ALL}")


# ─────────────────────────────────────────────
# Conferidor de jogos
# ─────────────────────────────────────────────

def conferir_jogos(df: pd.DataFrame, jogos: list, ultimos_n: int = 10):
    """
    Confere uma lista de jogos contra os últimos N sorteios reais.
    Mostra quantos acertos cada jogo teve em cada concurso.
    """
    num_cols = [f"n{i:02d}" for i in range(1, 16)]
    sorteios_recentes = df.tail(ultimos_n).reset_index(drop=True)

    print(f"\n{Fore.CYAN}{'═'*60}")
    print(f"  🎯 CONFERIDOR DE JOGOS — ÚLTIMOS {ultimos_n} SORTEIOS")
    print(f"{'═'*60}{Style.RESET_ALL}")

    # Cabeçalho com concursos
    print(f"\n  {'Jogo':<6}", end="")
    for _, row in sorteios_recentes.iterrows():
        print(f"  {int(row['concurso']):>5}", end="")
    print(f"  {'Max':>5}  {'Média':>6}")
    print(f"  {'-'*6}", end="")
    for _ in sorteios_recentes.iterrows():
        print(f"  {'─'*5}", end="")
    print(f"  {'─'*5}  {'─'*6}")

    for i, jogo in enumerate(jogos, 1):
        jogo_set = set(jogo)
        acertos_lista = []

        print(f"  J{i:02d}   ", end="")
        for _, row in sorteios_recentes.iterrows():
            resultado = set(int(row[c]) for c in num_cols)
            acertos = len(jogo_set & resultado)
            acertos_lista.append(acertos)

            # Colorir por acertos
            if acertos >= 14:
                cor = Fore.MAGENTA
            elif acertos == 13:
                cor = Fore.GREEN
            elif acertos == 12:
                cor = Fore.YELLOW
            elif acertos == 11:
                cor = Fore.CYAN
            else:
                cor = Fore.WHITE
            print(f"  {cor}{acertos:>5}{Style.RESET_ALL}", end="")

        maximo = max(acertos_lista)
        media = sum(acertos_lista) / len(acertos_lista)
        cor_max = Fore.MAGENTA if maximo >= 14 else (Fore.GREEN if maximo >= 13 else Fore.YELLOW)
        print(f"  {cor_max}{maximo:>5}{Style.RESET_ALL}  {media:>6.1f}")

    # Legenda
    print(f"\n  {Fore.MAGENTA}14-15 acertos{Style.RESET_ALL}  "
          f"{Fore.GREEN}13 acertos{Style.RESET_ALL}  "
          f"{Fore.YELLOW}12 acertos{Style.RESET_ALL}  "
          f"{Fore.CYAN}11 acertos{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═'*60}{Style.RESET_ALL}")


    # Resumo financeiro
    PREMIOS = {15: 1_000_000.00, 14: 1_500.00, 13: 30.00, 12: 14.00, 11: 7.00}
    CUSTO = 3.50
    total_gasto = len(jogos) * len(sorteios_recentes) * CUSTO
    total_ganho = 0.0
    resumo = []
    for i, jogo in enumerate(jogos, 1):
        jogo_set = set(jogo)
        for _, row in sorteios_recentes.iterrows():
            resultado = set(int(row[c]) for c in num_cols)
            acertos = len(jogo_set & resultado)
            premio = PREMIOS.get(acertos, 0.0)
            if premio > 0:
                total_ganho += premio
                resumo.append((i, int(row["concurso"]), acertos, premio))
    print(f"\n  {Fore.CYAN}💰 RESUMO FINANCEIRO{Style.RESET_ALL}")
    print(f"  Jogos apostados : {len(jogos)} x R$ {CUSTO:.2f} = {Fore.RED}R$ {total_gasto:.2f}{Style.RESET_ALL}")
    if resumo:
        resumo.sort(key=lambda x: (x[1], x[0]))
        for j, conc, ac, prem in resumo:
            print(f"  {Fore.GREEN}✅ J{j:02d} no concurso {conc}: {ac} pontos = R$ {prem:.2f}{Style.RESET_ALL}")
    else:
        print(f"  {Fore.YELLOW}Nenhum premio nos sorteios conferidos.{Style.RESET_ALL}")
    saldo = total_ganho - total_gasto
    cor_saldo = Fore.GREEN if saldo >= 0 else Fore.RED
    print(f"  Total ganho     : {Fore.GREEN}R$ {total_ganho:.2f}{Style.RESET_ALL}")
    print(f"  Saldo           : {cor_saldo}R$ {saldo:.2f}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")

def conferir_jogo_manual(df: pd.DataFrame, jogo: list, ultimos_n: int = 20):
    """
    Confere um único jogo digitado manualmente contra os últimos N sorteios.
    Mostra detalhes de cada concurso.
    """
    num_cols = [f"n{i:02d}" for i in range(1, 16)]
    sorteios_recentes = df.tail(ultimos_n).reset_index(drop=True)
    jogo_set = set(jogo)

    print(f"\n{Fore.CYAN}{'═'*60}")
    print(f"  🔍 CONFERINDO JOGO: {' '.join(f'{n:02d}' for n in sorted(jogo))}")
    print(f"{'═'*60}{Style.RESET_ALL}")

    total_11 = total_12 = total_13 = total_14 = total_15 = 0

    for _, row in sorteios_recentes.iterrows():
        resultado = set(int(row[c]) for c in num_cols)
        acertos = len(jogo_set & resultado)
        numeros_acertados = sorted(jogo_set & resultado)
        concurso = int(row['concurso'])
        data = row['data']

        if acertos >= 11:
            if acertos == 15: total_15 += 1; cor = Fore.MAGENTA
            elif acertos == 14: total_14 += 1; cor = Fore.MAGENTA
            elif acertos == 13: total_13 += 1; cor = Fore.GREEN
            elif acertos == 12: total_12 += 1; cor = Fore.YELLOW
            else: total_11 += 1; cor = Fore.CYAN

            acertos_fmt = " ".join(f"{n:02d}" for n in numeros_acertados)
            print(f"  {cor}Concurso {concurso} ({data}): {acertos} acertos → [{acertos_fmt}]{Style.RESET_ALL}")
        else:
            print(f"  {Fore.WHITE}Concurso {concurso} ({data}): {acertos} acertos{Style.RESET_ALL}")

    print(f"\n  {Fore.CYAN}Resumo nos últimos {ultimos_n} sorteios:{Style.RESET_ALL}")
    print(f"  15 acertos: {Fore.MAGENTA}{total_15}x{Style.RESET_ALL}")
    print(f"  14 acertos: {Fore.MAGENTA}{total_14}x{Style.RESET_ALL}")
    print(f"  13 acertos: {Fore.GREEN}{total_13}x{Style.RESET_ALL}")
    print(f"  12 acertos: {Fore.YELLOW}{total_12}x{Style.RESET_ALL}")
    print(f"  11 acertos: {Fore.CYAN}{total_11}x{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═'*60}{Style.RESET_ALL}")

# ─────────────────────────────────────────────
# Gera HTML de repetições do sorteio anterior
# ─────────────────────────────────────────────
def gerar_html_repeticoes_anterior(df: pd.DataFrame, caminho: str = "analises/repeticoes_anterior.html"):
    import json, os
    sorteios_raw = df.sort_values("concurso").reset_index(drop=True)
    cols = [c for c in df.columns if c.startswith("n")]
    sorteios = [set(row[cols].tolist()) for _, row in sorteios_raw.iterrows()]
    concursos = sorteios_raw["concurso"].tolist()
    datas = sorteios_raw["data"].tolist()

    # Distribuição de repetições
    reps = Counter()
    for i in range(1, len(sorteios)):
        r = len(sorteios[i] & sorteios[i-1])
        reps[r] += 1
    total = len(sorteios) - 1

    # Últimos dois sorteios
    ant = sorted(sorteios[-2])
    atu = sorted(sorteios[-1])
    repetidos = sorted(set(ant) & set(atu))
    novos     = sorted(set(atu) - set(ant))
    sairam    = sorted(set(ant) - set(atu))
    conc_ant, data_ant = concursos[-2], datas[-2]
    conc_atu, data_atu = concursos[-1], datas[-1]

    # Fidelidade: % de vezes que cada número repetiu no sorteio seguinte
    fidelidade = Counter()
    apareceu   = Counter()
    for i in range(1, len(sorteios)):
        for n in sorteios[i-1]:
            apareceu[n] += 1
            if n in sorteios[i]:
                fidelidade[n] += 1
    fid_pct = {n: round(fidelidade[n]/apareceu[n]*100, 1) for n in range(1,26)}

    # Atraso: quantos sorteios desde a última aparição
    atraso = {}
    for n in range(1, 26):
        for i in range(len(sorteios)-1, -1, -1):
            if n in sorteios[i]:
                atraso[n] = len(sorteios) - 1 - i
                break

    # Dados para os gráficos
    rep_labels = sorted(reps.keys())
    rep_data   = [reps[k] for k in rep_labels]
    rep_pct    = [round(reps[k]/total*100,1) for k in rep_labels]
    mais_comum = max(reps, key=reps.get)
    zona_quente= round(sum(reps[k] for k in reps if 8<=k<=10)/total*100,1)
    mais_fiel  = max(fid_pct, key=fid_pct.get)
    menos_fiel = min(fid_pct, key=fid_pct.get)

    fid_nums  = list(range(1,26))
    fid_vals  = [fid_pct[n] for n in fid_nums]
    atr_nums  = list(range(1,26))
    atr_vals  = [atraso[n] for n in atr_nums]
    top3_atr  = sorted(atraso.items(), key=lambda x: x[1], reverse=True)[:3]

    os.makedirs(os.path.dirname(caminho) if os.path.dirname(caminho) else ".", exist_ok=True)

    html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Repeticoes do Sorteio Anterior - Lotofacil</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
body{{font-family:sans-serif;padding:2rem;background:#f5f5f5;color:#333;}}
h1{{font-size:20px;font-weight:500;margin-bottom:.5rem;}}
p{{font-size:13px;color:#888;margin-bottom:1rem;}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:1.5rem;}}
.card{{background:#fff;border-radius:8px;padding:.75rem;text-align:center;}}
.card small{{display:block;font-size:12px;color:#888;}}
.card strong{{font-size:20px;}}
.box{{background:#fff;border-radius:8px;padding:1rem;margin-bottom:1.5rem;}}
.legenda{{display:flex;gap:16px;font-size:12px;color:#888;margin-bottom:8px;flex-wrap:wrap;}}
.leg{{display:flex;align-items:center;gap:4px;}}
.dot{{width:10px;height:10px;border-radius:2px;}}
.tabs{{display:flex;gap:8px;margin-bottom:1rem;flex-wrap:wrap;}}
.tab{{padding:6px 16px;border-radius:6px;cursor:pointer;font-size:13px;font-weight:500;border:2px solid #ddd;background:#fff;}}
.tab.ativo{{background:#D85A30;color:#fff;border-color:#D85A30;}}
.grid5{{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;}}
.num{{border-radius:8px;padding:8px;text-align:center;}}
.num span{{display:block;font-size:13px;font-weight:600;color:#fff;}}
.num small{{font-size:11px;color:rgba(255,255,255,.9);}}
.sorteio{{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;}}
.bola{{width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;color:#fff;}}
.titulo-sorteio{{font-size:13px;font-weight:500;margin-bottom:6px;}}
.legenda-bolas{{display:flex;gap:16px;font-size:12px;color:#888;margin:12px 0;}}
.atraso-cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:1.2rem;}}
.atraso-card{{border-radius:10px;padding:14px;text-align:center;color:#fff;}}
.atraso-card .num-big{{font-size:32px;font-weight:700;line-height:1;}}
.atraso-card .label{{font-size:12px;margin-top:4px;opacity:.85;}}
.atraso-card .concursos{{font-size:13px;font-weight:500;margin-top:2px;}}
.grid-atraso{{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin-top:1rem;}}
.bola-atraso{{border-radius:10px;padding:10px 6px;text-align:center;}}
.bola-atraso .n{{font-size:16px;font-weight:700;color:#fff;line-height:1;}}
.bola-atraso .a{{font-size:11px;color:rgba(255,255,255,.85);margin-top:3px;}}
.bola-atraso .barra{{height:4px;border-radius:2px;background:rgba(255,255,255,.3);margin-top:6px;overflow:hidden;}}
.bola-atraso .fill{{height:100%;border-radius:2px;background:rgba(255,255,255,.8);}}
</style>
</head>
<body>
<h1>Lotofacil - Repeticoes do Sorteio Anterior</h1>
<p>Analise completa de quantos numeros se repetem e quais sao os mais fieis</p>
<div class="cards">
  <div class="card"><small>Mais comum</small><strong>{mais_comum} <span style="font-size:13px;color:#888">{round(reps[mais_comum]/total*100,1)}%</span></strong></div>
  <div class="card"><small>8 ou 9 repeticoes</small><strong>{zona_quente}%</strong></div>
  <div class="card"><small>Mais fiel</small><strong>{mais_fiel} <span style="font-size:13px;color:#888">{fid_pct[mais_fiel]}%</span></strong></div>
  <div class="card"><small>Menos fiel</small><strong>{menos_fiel} <span style="font-size:13px;color:#888">{fid_pct[menos_fiel]}%</span></strong></div>
</div>
<div class="tabs">
  <div class="tab ativo" onclick="mostrarTab(1,this)">Ultimos sorteios</div>
  <div class="tab" onclick="mostrarTab(2,this)">Quantidade de repeticoes</div>
  <div class="tab" onclick="mostrarTab(3,this)">Numeros mais fieis</div>
  <div class="tab" onclick="mostrarTab(4,this)">Atraso dos numeros</div>
</div>
<div id="tab1">
  <div class="box">
    <div class="titulo-sorteio">Concurso {conc_ant} - {data_ant} (anterior)</div>
    <div class="sorteio" id="bolas_anterior"></div>
    <div style="margin-top:1.5rem;" class="titulo-sorteio">Concurso {conc_atu} - {data_atu} (atual)</div>
    <div class="sorteio" id="bolas_atual"></div>
    <div class="legenda-bolas">
      <div class="leg"><div class="dot" style="background:#D85A30;border-radius:50%;width:12px;height:12px;"></div>Repetiu</div>
      <div class="leg"><div class="dot" style="background:#1D9E75;border-radius:50%;width:12px;height:12px;"></div>Novo</div>
      <div class="leg"><div class="dot" style="background:#3c89d0;border-radius:50%;width:12px;height:12px;"></div>Saiu</div>
    </div>
    <div style="background:#f5f5f5;border-radius:8px;padding:12px;font-size:13px;line-height:1.8;">
      <strong>{len(repetidos)} repetiram:</strong> {repetidos}<br>
      <strong>{len(novos)} novos:</strong> {novos}<br>
      <strong>{len(sairam)} sairam:</strong> {sairam}
    </div>
  </div>
</div>
<div id="tab2" style="display:none;">
  <div class="box">
    <div class="legenda">
      <div class="leg"><div class="dot" style="background:#D85A30"></div>Zona quente (8-10)</div>
      <div class="leg"><div class="dot" style="background:#1D9E75"></div>Normal (7-11)</div>
      <div class="leg"><div class="dot" style="background:#3c89d0"></div>Raro</div>
    </div>
    <div style="position:relative;height:300px;"><canvas id="chart1"></canvas></div>
  </div>
</div>
<div id="tab3" style="display:none;">
  <div class="box">
    <div class="legenda">
      <div class="leg"><div class="dot" style="background:#D85A30"></div>Muito fiel (+{fid_pct[mais_fiel]-1:.0f}%)</div>
      <div class="leg"><div class="dot" style="background:#1D9E75"></div>Normal</div>
      <div class="leg"><div class="dot" style="background:#3c89d0"></div>Menos fiel</div>
    </div>
    <div style="position:relative;height:300px;"><canvas id="chart2"></canvas></div>
  </div>
  <div class="box">
    <div style="font-size:13px;color:#888;margin-bottom:8px;">Ranking dos mais fieis</div>
    <div class="grid5" id="grid2"></div>
  </div>
</div>
<div id="tab4" style="display:none;">
  <div class="box">
    <div style="font-size:13px;color:#888;margin-bottom:12px;">Sorteios sem aparecer ate o concurso {conc_atu}</div>
    <div class="atraso-cards" id="top3-atraso"></div>
    <div class="legenda" style="margin-bottom:10px;">
      <div class="leg"><div class="dot" style="background:#1D9E75"></div>Apareceu agora (0)</div>
      <div class="leg"><div class="dot" style="background:#3c89d0"></div>Pouco atrasado (1-3)</div>
      <div class="leg"><div class="dot" style="background:#BA7517"></div>Atrasado (4-6)</div>
      <div class="leg"><div class="dot" style="background:#D85A30"></div>Muito atrasado (7+)</div>
    </div>
    <div style="position:relative;height:280px;margin-bottom:1rem;"><canvas id="chart-atraso"></canvas></div>
    <div style="font-size:13px;color:#888;margin-bottom:8px;">Todos os numeros</div>
    <div class="grid-atraso" id="grade-atraso"></div>
  </div>
</div>
<script>
function corRep(k){{return k>=8&&k<=10?"#D85A30":k>=7&&k<=11?"#1D9E75":"#3c89d0";}}
function corNum(p){{return p>=37?"#D85A30":p>=35?"#1D9E75":"#3c89d0";}}
function corAtraso(a){{return a===0?"#1D9E75":a<=3?"#3c89d0":a<=6?"#BA7517":"#D85A30";}}
function labelAtraso(a){{return a===0?"Em dia":a===1?"1 sorteio":a+" sorteios";}}
function mostrarTab(n,el){{
  [1,2,3,4].forEach(i=>document.getElementById("tab"+i).style.display="none");
  document.querySelectorAll(".tab").forEach(t=>t.classList.remove("ativo"));
  document.getElementById("tab"+n).style.display="";
  el.classList.add("ativo");
}}
const ant={json.dumps(ant)}, atu={json.dumps(atu)}, rep={json.dumps(repetidos)}, sai={json.dumps(sairam)};
ant.forEach(n=>{{
  const b=document.createElement("div");
  b.className="bola";
  b.style.background=rep.includes(n)?"#3c89d0":"#aaa";
  b.textContent=String(n).padStart(2,"0");
  document.getElementById("bolas_anterior").appendChild(b);
}});
atu.forEach(n=>{{
  const b=document.createElement("div");
  b.className="bola";
  b.style.background=rep.includes(n)?"#D85A30":"#1D9E75";
  b.textContent=String(n).padStart(2,"0");
  document.getElementById("bolas_atual").appendChild(b);
}});
const repLabels={json.dumps(rep_labels)}, repData={json.dumps(rep_data)}, repPct={json.dumps(rep_pct)};
new Chart(document.getElementById("chart1"),{{type:"bar",data:{{labels:repLabels.map(k=>k+" rep"),datasets:[{{data:repData,backgroundColor:repLabels.map(k=>corRep(k)),borderRadius:6}}]}},options:{{plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>repPct[ctx.dataIndex]+"% ("+ctx.raw+" sorteios)"}}}}}}  ,scales:{{y:{{beginAtZero:true}}}}}}}});
const fidNums={json.dumps(fid_nums)}, fidVals={json.dumps(fid_vals)};
new Chart(document.getElementById("chart2"),{{type:"bar",data:{{labels:fidNums.map(n=>"N"+String(n).padStart(2,"0")),datasets:[{{data:fidVals,backgroundColor:fidVals.map(v=>corNum(v)),borderRadius:6}}]}},options:{{plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>ctx.raw+"%"}}}}}}  ,scales:{{y:{{beginAtZero:true,max:100}}}}}}}});
const fidSorted=[...fidNums].sort((a,b)=>fidVals[b-1]-fidVals[a-1]);
const g2=document.getElementById("grid2");
fidSorted.forEach(n=>{{
  const pct=fidVals[n-1],cor=corNum(pct);
  g2.innerHTML+=`<div class="num" style="background:${{cor}}"><span>${{String(n).padStart(2,"0")}}</span><small>${{pct}}%</small></div>`;
}});
const atrNums={json.dumps(atr_nums)}, atrVals={json.dumps(atr_vals)};
const top3={json.dumps(top3_atr)};
const t3=document.getElementById("top3-atraso");
top3.forEach(([n,a])=>{{
  t3.innerHTML+=`<div class="atraso-card" style="background:${{corAtraso(a)}}"><div class="num-big">${{String(n).padStart(2,"0")}}</div><div class="label">Numero</div><div class="concursos">${{labelAtraso(a)}}</div></div>`;
}});
const maxAtr=Math.max(...atrVals)||1;
new Chart(document.getElementById("chart-atraso"),{{type:"bar",data:{{labels:atrNums.map(n=>"N"+String(n).padStart(2,"0")),datasets:[{{data:atrVals,backgroundColor:atrVals.map(a=>corAtraso(a)),borderRadius:6}}]}},options:{{plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>labelAtraso(ctx.raw)}}}}}}  ,scales:{{y:{{beginAtZero:true}}}}}}}});
const ga=document.getElementById("grade-atraso");
atrNums.forEach((n,i)=>{{
  const a=atrVals[i],cor=corAtraso(a),pct=Math.round(a/maxAtr*100);
  ga.innerHTML+=`<div class="bola-atraso" style="background:${{cor}}"><div class="n">${{String(n).padStart(2,"0")}}</div><div class="a">${{labelAtraso(a)}}</div><div class="barra"><div class="fill" style="width:${{pct}}%"></div></div></div>`;
}});
</script>
</body>
</html>"""

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html)
    return caminho

def exibir_ciclo_unificado(df: pd.DataFrame, dados_hall: dict, k: str):
    """
    Analisa e exibe o monitor de ciclo interno para um Rei específico.
    """
    if k not in dados_hall:
        print(f"  {Fore.RED}❌ Rei {k} não encontrado!{Style.RESET_ALL}")
        return

    rei = dados_hall[k]
    dezenas_alvo = set(rei["dezenas"])
    num_cols = [f"n{i:02d}" for i in range(1, 16)]
    
    # Converter sorteios para lista de sets (do mais antigo para o mais recente)
    sorteios = []
    for _, row in df.iterrows():
        sorteios.append({
            "concurso": int(row["concurso"]),
            "dz": set(int(row[c]) for c in num_cols)
        })
    
    # Rastrear ciclos
    vistos = set()
    inicio_ciclo = sorteios[0]["concurso"]
    ciclos_finalizados = []
    
    for s in sorteios:
        acertos = s["dz"] & dezenas_alvo
        vistos.update(acertos)
        
        if vistos == dezenas_alvo:
            # Ciclo fechou!
            ciclos_finalizados.append({
                "inicio": inicio_ciclo,
                "fim": s["concurso"]
            })
            vistos = set()
            inicio_ciclo = s["concurso"] + 1

    # Estado atual (Ciclo Aberto)
    faltando = dezenas_alvo - vistos
    concursos_passados = (sorteios[-1]["concurso"] - inicio_ciclo + 1) if sorteios[-1]["concurso"] >= inicio_ciclo else 0
    
    print(f"\n{Fore.CYAN}╔{'═'*62}╗")
    print(f"║ 📊 MONITOR DE CICLO INTERNO — {rei['titulo']:24} ║")
    print(f"╚{'═'*62}╝{Style.RESET_ALL}")
    
    print(f"\n  {Fore.YELLOW}Ciclo Atual iniciado no Concurso:{Style.RESET_ALL} {inicio_ciclo}")
    print(f"  {Fore.YELLOW}Concursos transcorridos:{Style.RESET_ALL} {concursos_passados}")
    
    if not faltando:
        print(f"\n  {Fore.GREEN}✅ TUDO EM DIA! O ciclo fechou no último sorteio.{Style.RESET_ALL}")
    else:
        print(f"\n  {Fore.CYAN}🚀 DEZENAS PENDENTES (FALTAM PARA FECHAR O CICLO):{Style.RESET_ALL}")
        dz_faltantes = "  ".join(f"{d:02d}" for d in sorted(list(faltando)))
        print(f"  {Back.RED}{Fore.WHITE} {dz_faltantes} {Style.RESET_ALL}")
        
        print(f"\n  {Fore.WHITE}Progresso: {len(vistos)} / {len(dezenas_alvo)} dezenas sorteadas.{Style.RESET_ALL}")
        
        if len(faltando) <= 3:
            print(f"\n  {Fore.YELLOW}⚠️  ALERTA DE MATURIDADE: Restam apenas {len(faltando)} dezenas!{Style.RESET_ALL}")
            print(f"  A probabilidade de retorno alto aumenta exponencialmente.")

    if ciclos_finalizados:
        print(f"\n  {Fore.WHITE}Histórico de Fechamentos Recentes:{Style.RESET_ALL}")
        for c in reversed(ciclos_finalizados[-5:]):
            duracao = c['fim'] - c['inicio'] + 1
            print(f"  - Concursos {c['inicio']} a {c['fim']} ({duracao} sorteios)")
    
    print(f"\n{Fore.CYAN}{'═'*64}{Style.RESET_ALL}")

def exibir_resumo_ciclos_completo(df: pd.DataFrame, dados_hall: dict, label: str = "18 DZ"):
    """
    Exibe um resumo tabular dos ciclos de todos os Reis (17 ou 18 DZ).
    """
    print(f"\n{Fore.CYAN}╔{'═'*72}╗")
    print(f"║ 📊 RESUMO GERAL DE CICLOS INTERNOS — OS REIS DE {label:<10}       ║")
    print(f"╚{'═'*72}╝{Style.RESET_ALL}")
    
    num_cols = [f"n{i:02d}" for i in range(1, 16)]
    sorteios = []
    for _, row in df.iterrows():
        sorteios.append(set(int(row[c]) for c in num_cols))
    
    print(f"\n  {'REI':<15} │ {'INÍCIO':<6} │ {'CONC':<4} │ {'FALTA':<4} │ {'DEZENAS PENDENTES'}")
    print(f"  {'─'*15}─┼─{'─'*6}─┼─{'─'*4}─┼─{'─'*4}─┼─{'─'*30}")

    for k in ["15", "14", "13", "12", "11"]:
        if k not in dados_hall: continue
        
        rei = dados_hall[k]
        target = set(rei["dezenas"])
        
        # Calcular ciclo atual
        vistos = set()
        inicio = 0
        concursos = sorted(df['concurso'].tolist())
        
        # Modo rápido: de trás para frente até fechar
        for i in range(len(sorteios)-1, -1, -1):
            vistos.update(sorteios[i] & target)
            if vistos == target:
                inicio = concursos[i+1] if i < len(concursos)-1 else concursos[-1]
                break
        
        if inicio == 0: inicio = concursos[0]
        
        # Recalcular vistos desde o inicio
        vistos_desde_inicio = set()
        count = 0
        for i in range(len(concursos)):
            if concursos[i] >= inicio:
                vistos_desde_inicio.update(sorteios[i] & target)
                count += 1
        
        faltam = target - vistos_desde_inicio
        n_faltam = len(faltam)
        
        # Cores para o status
        cor_falta = Fore.RED if n_faltam <= 3 and n_faltam > 0 else (Fore.GREEN if n_faltam == 0 else Fore.YELLOW)
        status_txt = f"{n_faltam:02d}"
        
        dz_pendentes = " ".join(f"{d:02d}" for d in sorted(list(faltam)))
        if not dz_pendentes: dz_pendentes = f"{Fore.GREEN}CICLO COMPLETO ✅{Style.RESET_ALL}"
        
        print(f"  {rei['titulo']:15} │ {inicio:<6} │ {count:4d} │ {cor_falta}{status_txt:4} {Style.RESET_ALL} │ {dz_pendentes}")

    print(f"\n  {Fore.YELLOW}Legenda: INÍCIO = Concurso que começou | CONC = Sorteios passados | FALTA = Qtd dezenas pendentes{Style.RESET_ALL}")
    print(f"  {Fore.CYAN}{'═'*74}{Style.RESET_ALL}")

def exibir_radar_unificado_reis(df: pd.DataFrame, dados_halls: dict):
    """
    Radar Unificado v3.2: Compara o atraso (jejum) atual de todos os Reis.
    Ajustado para alinhamento milimétrico com emojis.
    """
    LIMIARES = {"17": 12, "18": 13, "19": 13, "20": 14}
    CORES = {
        "17": Fore.CYAN,
        "18": Fore.GREEN,
        "19": Fore.YELLOW,
        "20": Fore.LIGHTRED_EX,
    }

    lista_sorteios = _extrair_lista_sorteios(df)
    width = 138
    print(f"\n{Fore.LIGHTCYAN_EX}╔{'═'*width}╗")
    titulo = f"📡 RADAR UNIFICADO DE JEJUM — STATUS DE OPORTUNIDADE ATUAL (17-20 DZ)"
    print(f"║ {titulo.center(width - 2)} ║")
    print(f"╚{'═'*width}╝{Style.RESET_ALL}")

    # Cabeçalhos com larguras fixas: REI (10) + [31] * 4
    h1 = f"  {' ':^9} │"
    h2 = f"  {' REI':<9} │"
    
    for e in ["17", "18", "19", "20"]:
        cor = CORES[e]
        h1 += f"{cor}{e + ' DEZENAS (ELITE)':^31}{Style.RESET_ALL} │"
        h2 += f" {'Atraso   Média   Status':^31} │"
    
    print(h1)
    print(h2)
    print("  " + "─" * (len(h2) - 3))

    # Nomes e Status com larguras controladas
    for k in ["15", "14", "13", "12", "11"]:
        linha = f"  {Fore.WHITE} R{k:<7}{Style.RESET_ALL} │"
        
        for e in ["17", "18", "19", "20"]:
            if e in dados_halls and k in dados_halls[e]:
                dezenas = set(dados_halls[e][k]["dezenas"])
                limiar = LIMIARES[e]
                
                # Cálculo de atraso
                atraso = 0
                for i in range(len(lista_sorteios)-1, -1, -1):
                    if len(dezenas & lista_sorteios[i]) >= limiar: break
                    atraso += 1
                
                # Média (Janela focada)
                historico = df.tail(300).copy()
                sorteios_hist = _extrair_lista_sorteios(historico)
                hits = [len(dezenas & s) >= limiar for s in sorteios_hist]
                last_h = -1
                ints = []
                for idx, h in enumerate(hits):
                    if h:
                        if last_h != -1: ints.append(idx - last_h)
                        last_h = idx
                media = sum(ints) / len(ints) if ints else 8.0
                
                # Status com compensação manual de largura (Emoji = 2 chars visuais)
                if atraso == 0:
                    status_fmt = f"{Fore.GREEN}🔥 QUENTE!{Style.RESET_ALL}  "
                elif atraso > media * 1.5:
                    status_fmt = f"{Fore.RED}🚨 ALERTA!!{Style.RESET_ALL} "
                elif atraso >= media:
                    status_fmt = f"{Fore.YELLOW}🎯 CHANCE   {Style.RESET_ALL}"
                else:
                    status_fmt = f"{Fore.WHITE}⏳ JEJUM    {Style.RESET_ALL}"
                
                # Parte dos dados: 
                # "  00 s   00.0   " = 16 chars
                # status_fmt = 12 chars visuais (ajustado acima)
                # Total = 28 + 3 espaços = 31
                col_data = f"   {atraso:02d} s   {media:04.1f}   {status_fmt} "
                linha += f"{col_data}│"
            else:
                linha += f" {'-':^31} │"
        
        print(linha)

    print("  " + "─" * (len(h2) - 3))
    print(f"  {Fore.CYAN}Legenda:{Style.RESET_ALL} {Fore.RED}🚨 ALERTA (Acima da Média){Style.RESET_ALL} │ {Fore.YELLOW}🎯 CHANCE (Em ponto de bala){Style.RESET_ALL} │ {Fore.GREEN}🔥 QUENTE (Pontuou Agora){Style.RESET_ALL}")
    print(f"  {Fore.WHITE}💡 DICA: Os Reis em {Fore.RED}ALERTA{Style.RESET_ALL} são os que mais provavelmente pontuarão nos próximos 2 concursos.{Style.RESET_ALL}")


def exibir_resumo_ciclos_unificado(df: pd.DataFrame, dados_halls: dict):
    """
    Monitor de Ciclos Unificado v1.0: 
    Compara o progresso de fechamento de ciclo de todos os Reis em todas as Elites.
    """
    CORES = {
        "17": Fore.CYAN,
        "18": Fore.GREEN,
        "19": Fore.YELLOW,
        "20": Fore.LIGHTRED_EX,
    }

    num_cols = [f"n{i:02d}" for i in range(1, 16)]
    sorteios = [set(row[num_cols].astype(int)) for _, row in df.iterrows()]
    concursos = df['concurso'].tolist()

    width = 120
    print(f"\n{Fore.MAGENTA}╔{'═'*width}╗")
    titulo = "🔭 MONITOR DE CICLOS UNIFICADO — BUSCA POR MATURIDADE (17-20 DZ)"
    print(f"║ {titulo.center(width - 2)} ║")
    print(f"╚{'═'*width}╝{Style.RESET_ALL}")

    print(f"\n  {'ELITE':<7} │ {'REI':<20} │ {'CONC':<5} │ {'FALTA':<8} │ {'DEZENAS PENDENTES'}")
    print(f"  {'─'*7}─┼─{'─'*20}─┼─{'─'*5}─┼─{'─'*8}─┼─{'─'*70}")

    todos_resultados = []

    for elite in ["17", "18", "19", "20"]:
        if elite not in dados_halls: continue
        cor_e = CORES[elite]
        
        for k in ["15", "14", "13", "12", "11"]:
            if k not in dados_halls[elite]: continue
            
            rei = dados_halls[elite][k]
            target = set(rei["dezenas"])
            
            # Calcular ciclo atual (de trás para frente)
            vistos = set()
            inicio_idx = -1
            for i in range(len(sorteios)-1, -1, -1):
                vistos.update(sorteios[i] & target)
                if vistos == target:
                    inicio_idx = i + 1
                    break
            
            if inicio_idx == -1: inicio_idx = 0
            if inicio_idx >= len(sorteios): 
                # Ciclo fechou no último sorteio
                n_faltam = 0
                faltam = set()
                count = 0
            else:
                vistos_atuais = set()
                count = 0
                for i in range(inicio_idx, len(sorteios)):
                    vistos_atuais.update(sorteios[i] & target)
                    count += 1
                faltam = target - vistos_atuais
                n_faltam = len(faltam)

            status_cor = Fore.RED + Style.BRIGHT if 0 < n_faltam <= 3 else (Fore.GREEN if n_faltam == 0 else Fore.YELLOW)
            
            todos_resultados.append({
                "elite": elite,
                "cor": cor_e,
                "titulo": rei["titulo"],
                "conc": count,
                "n_faltam": n_faltam,
                "faltam_dz": sorted(list(faltam)),
                "status_cor": status_cor
            })

    # Ordenar por proximidade de fechar (n_faltam ascendente, mas 0 por último ou com destaque)
    ranking = sorted(todos_resultados, key=lambda x: (x["n_faltam"] == 0, x["n_faltam"]))

    for r in ranking:
        dz_str = " ".join(f"{d:02d}" for d in r["faltam_dz"])
        if r["n_faltam"] == 0:
            dz_str = f"{Fore.GREEN}FECHADO NO ÚLTIMO SORTEIO ✅{Style.RESET_ALL}"
        
        # Alinhamento manual para compensar códigos de cores
        elite_fmt = f"{r['cor']}{r['elite']:<7}{Style.RESET_ALL}"
        falta_fmt = f"{r['status_cor']}{r['n_faltam']:02d} DZ{Style.RESET_ALL}"
        
        print(f"  {elite_fmt} │ "
              f"{r['titulo']:20} │ "
              f"{r['conc']:^5d} │ "
              f"{falta_fmt}  │ "
              f"{dz_str}")

    print(f"\n  {Fore.YELLOW}Legenda: CONC = Sorteios passados no ciclo atual | FALTA = Dezenas que ainda não saíram no ciclo.{Style.RESET_ALL}")
    print(f"  {Fore.MAGENTA}💡 ESTRATÉGIA: Foque nos Reis que faltam entre {Fore.RED}01 e 03 dezenas{Style.RESET_ALL}. "
          f"Eles são os alvos maduros para a Caçada de Ciclo.{Style.RESET_ALL}")

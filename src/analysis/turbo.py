"""
Motor Bitwise Turbo - integrado do v2.0
Analisa combinações de 17 dezenas usando operações bit a bit.
Gera Score Master e Índice Preditivo com multiprocessamento.
"""
import itertools
import multiprocessing
import time
import csv
import os
from datetime import datetime
from pathlib import Path
from colorama import Fore, Style, Back

# Novos Pesos Super Code - Foco em Lucro e Consistência
PESOS = {
    15: 500,  # O prêmio máximo
    14: 100,  # Valorizado para detectar conjuntos consistentes como o seu
    13: 20,   # Prêmios recorrentes
    12: 5,    # Base de sustentação
    11: 1     # Frequência mínima
}

RECENT_WINDOW = 100  # Últimos N sorteios para tendência recente
OUTPUT_DIR = Path(__file__).parent.parent.parent / "resultados"
# Fallback para path absoluto se necessário
import os as _os
_BASE = Path(_os.path.expanduser("~")) / "lotofacil_pro" / "resultados"


# ---------------------------------------------
# Utilitários Bitwise
# ---------------------------------------------

def para_bitmask(dezenas: list) -> int:
    mask = 0
    for d in dezenas:
        mask |= (1 << (d - 1))
    return mask


def formatar_tempo(segundos: float) -> str:
    m, s = divmod(int(segundos), 60)
    return f"{m}m {s:02d}s" if m > 0 else f"{s}s"


# ---------------------------------------------
# Blocos de processamento paralelo
# ---------------------------------------------

def _bloco_score_master(combos_chunk, res_masks):
    """Calcula Score Master para um bloco de combinações."""
    w15, w14, w13, w12, w11 = PESOS[15], PESOS[14], PESOS[13], PESOS[12], PESOS[11]
    resultados = []
    for combo_mask, combo_tuple in combos_chunk:
        c15 = c14 = c13 = c12 = c11 = 0
        for res_mask in res_masks:
            a = (combo_mask & res_mask).bit_count()
            if a == 15: c15 += 1
            elif a == 14: c14 += 1
            elif a == 13: c13 += 1
            elif a == 12: c12 += 1
            elif a == 11: c11 += 1
        # Cálculo de Score Super Code (Soma ponderada pela recorrência)
        score = (c15 * w15) + (c14 * w14) + (c13 * w13) + (c12 * w12) + (c11 * w11)
        
        # Bônus de Recorrência: Valoriza conjuntos que premiam com frequência
        total_premios = c15 + c14 + c13 + c12 + c11
        bonus = total_premios * 0.5
        score += bonus

        if score > 0:
            resultados.append((combo_tuple, {15:c15,14:c14,13:c13,12:c12,11:c11}, score))
    return resultados


def _bloco_preditivo(combos_chunk, res_data_all, res_masks_recent):
    """Calcula Índice Preditivo para um bloco de combinações."""
    w15, w14, w13, w12, w11 = PESOS[15], PESOS[14], PESOS[13], PESOS[12], PESOS[11]
    total = len(res_data_all)
    resultados = []

    for combo_mask, combo_tuple in combos_chunk:
        h15=h14=h13=h12=h11=0
        ultima_pos = -1
        conc15=conc14=conc13=conc12=conc11=-1
        atraso15=atraso14=atraso13=atraso12=atraso11=-1

        for idx, (res_mask, concurso, data) in enumerate(res_data_all):
            a = (combo_mask & res_mask).bit_count()
            if a >= 11 and ultima_pos == -1: ultima_pos = idx
            if a == 15 and atraso15 == -1: atraso15 = idx; conc15 = concurso
            if a == 14 and atraso14 == -1: atraso14 = idx; conc14 = concurso
            if a == 13 and atraso13 == -1: atraso13 = idx; conc13 = concurso
            if a == 12 and atraso12 == -1: atraso12 = idx; conc12 = concurso
            if a == 11 and atraso11 == -1: atraso11 = idx; conc11 = concurso
            if a == 15: h15 += 1
            elif a == 14: h14 += 1
            elif a == 13: h13 += 1
            elif a == 12: h12 += 1
            elif a == 11: h11 += 1

        score_hist = (h15*w15+h14*w14+h13*w13+h12*w12+h11*w11) / total

        r15=r14=r13=r12=r11=0
        for res_mask in res_masks_recent:
            a = (combo_mask & res_mask).bit_count()
            if a == 15: r15 += 1
            elif a == 14: r14 += 1
            elif a == 13: r13 += 1
            elif a == 12: r12 += 1
            elif a == 11: r11 += 1
        score_recent = (r15*w15+r14*w14+r13*w13+r12*w12+r11*w11) / len(res_masks_recent)

        atraso = ultima_pos if ultima_pos != -1 else total
        fator_atraso = min(atraso / 50, 2.0)
        pi = (score_recent * 0.4) + (score_hist * 0.3) + (fator_atraso * 0.3)

        if pi > 0:
            resultados.append((combo_tuple, {
                'h14': h14, 'h13': h13, 'h12': h12,
                'r14': r14, 'r13': r13,
                'atraso': atraso,
                'atraso15': atraso15 if atraso15 != -1 else total,
                'atraso14': atraso14 if atraso14 != -1 else total,
                'atraso13': atraso13 if atraso13 != -1 else total,
                'atraso12': atraso12 if atraso12 != -1 else total,
                'atraso11': atraso11 if atraso11 != -1 else total,
                'conc15': conc15, 'conc14': conc14, 'conc13': conc13,
                'conc12': conc12, 'conc11': conc11,
            }, pi))
    return resultados


# ---------------------------------------------
# Funções principais
# ---------------------------------------------

def _preparar_masks(df):
    """Converte DataFrame de sorteios em lista de bitmasks."""
    num_cols = [f"n{i:02d}" for i in range(1, 16)]
    masks = []
    for _, row in df.iterrows():
        dezenas = [int(row[c]) for c in num_cols]
        masks.append(para_bitmask(dezenas))
    return masks

def _preparar_masks_com_concurso(df):
    """Converte DataFrame em lista de (bitmask, concurso, data)."""
    num_cols = [f"n{i:02d}" for i in range(1, 16)]
    result = []
    for _, row in df.iterrows():
        dezenas = [int(row[c]) for c in num_cols]
        result.append((para_bitmask(dezenas), int(row['concurso']), str(row['data'])))
    return result


def _gerar_combo_data(tamanho=17):
    """Gera todas as combinações de `tamanho` dezenas entre 1-25."""
    combos = list(itertools.combinations(range(1, 26), tamanho))
    return [(para_bitmask(c), c) for c in combos]


def _dividir_chunks(data, n):
    size = max(1, len(data) // n)
    return [data[i:i+size] for i in range(0, len(data), size)]


def _salvar_resultados_master(ranking, top_n=100):
    """Salva TXT e CSV do Score Master."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # TXT
    txt_path = OUTPUT_DIR / "score_master.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"LOTOFÁCIL - SCORE MASTER\nData: {agora}\n")
        f.write("-" * 80 + "\n")
        for i, (combo, c, sc) in enumerate(ranking[:top_n], 1):
            dz = " ".join(f"{d:02d}" for d in combo)
            f.write(f"#{i:03d} | Score:{sc:7.1f} | 15:{c[15]}x 14:{c[14]:2d}x 13:{c[13]:3d}x 12:{c[12]:3d}x 11:{c[11]:4d}x | [{dz}]\n")

    # CSV
    csv_path = OUTPUT_DIR / "score_master.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Posicao","Score","15","14","13","12","11","Dezenas"])
        for i, (combo, c, sc) in enumerate(ranking[:1000], 1):
            dz = "-".join(f"{d:02d}" for d in combo)
            w.writerow([i, f"{sc:.1f}".replace(".",","), c[15],c[14],c[13],c[12],c[11], dz])

    return txt_path, csv_path


def _salvar_resultados_preditivo(ranking, top_n=100):
    """Salva TXT e CSV do Índice Preditivo."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    txt_path = OUTPUT_DIR / "indice_preditivo.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"LOTOFÁCIL - ÍNDICE PREDITIVO\nData: {agora}\n")
        f.write("Lógica: 40% Recente | 30% Histórico | 30% Atraso\n")
        f.write("-" * 110 + "\n")
        for i, (combo, c, pi) in enumerate(ranking[:top_n], 1):
            dz = " ".join(f"{d:02d}" for d in combo)
            f.write(f"#{i:03d} | PI:{pi:.4f} | Atr14:{c['atraso14']:3d} Atr13:{c['atraso13']:3d} | "
                    f"H14:{c['h14']:2d} H13:{c['h13']:3d} | R14:{c['r14']} R13:{c['r13']} | [{dz}]\n")

    csv_path = OUTPUT_DIR / "indice_preditivo.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Rank","PI",
                    "Atraso14","Conc14","Atraso13","Conc13",
                    "Atraso12","Conc12","Atraso11","Conc11",
                    "Hist14","Hist13","Rec14","Rec13","Dezenas"])
        for i, (combo, c, pi) in enumerate(ranking[:1000], 1):
            dz = "-".join(f"{d:02d}" for d in combo)
            w.writerow([i, f"{pi:.5f}".replace(".",","),
                        c.get("atraso14",0), c.get("conc14",0),
                        c.get("atraso13",0), c.get("conc13",0),
                        c.get("atraso12",0), c.get("conc12",0),
                        c.get("atraso11",0), c.get("conc11",0),
                        c.get("h14",0), c.get("h13",0),
                        c.get("r14",0), c.get("r13",0), dz])

    return txt_path, csv_path


# ---------------------------------------------
# API pública
# ---------------------------------------------

def rodar_score_master(df, tamanho=17, top_n=100, verbose=True):
    """
    Analisa todas as combinações de `tamanho` dezenas e
    gera ranking por Score Master.
    """
    if verbose:
        n_combos = len(list(itertools.combinations(range(1,26), tamanho)))
        print(f"\n{Fore.CYAN}  --> Score Master -- {n_combos:,} combinações de {tamanho} dezenas{Style.RESET_ALL}")

    res_masks = _preparar_masks(df)
    combo_data = _gerar_combo_data(tamanho)
    n_proc = multiprocessing.cpu_count()
    chunks = _dividir_chunks(combo_data, n_proc)

    if verbose:
        print(f"  [CPU] Usando {n_proc} núcleos...{Style.RESET_ALL}")

    inicio = time.time()
    with multiprocessing.Pool(processes=n_proc) as pool:
        ar = pool.starmap_async(_bloco_score_master, [(c, res_masks) for c in chunks])
        while not ar.ready():
            if verbose:
                print(f"  Processando... [{formatar_tempo(time.time()-inicio)}]", end="\r")
            time.sleep(0.5)
        resultados = [item for sub in ar.get() for item in sub]

    ranking = sorted(resultados, key=lambda x: x[2], reverse=True)

    if verbose:
        print(f"\n  {Fore.GREEN}[OK] Concluído em {formatar_tempo(time.time()-inicio)}! "
              f"{len(ranking):,} combinações com score > 0.{Style.RESET_ALL}")

    txt, csv_p = _salvar_resultados_master(ranking, top_n)

    if verbose:
        print(f"  📁 Salvos: {txt.name}, {csv_p.name}")
        print(f"\n{Fore.CYAN}  TOP 10 - SCORE MASTER:{Style.RESET_ALL}")
        for i, (combo, c, sc) in enumerate(ranking[:10], 1):
            dz = "  ".join(f"{Fore.GREEN}{d:02d}{Style.RESET_ALL}" for d in combo)
            print(f"  #{i:02d} Score:{sc:7.1f} | {dz}")

    return ranking


def rodar_indice_preditivo(df, tamanho=17, top_n=100, verbose=True):
    """
    Gera ranking pelo Índice Preditivo:
    40% Tendência Recente + 30% Histórico + 30% Ciclo de Atraso
    """
    if verbose:
        n_combos = len(list(itertools.combinations(range(1,26), tamanho)))
        print(f"\n{Fore.CYAN}   Índice Preditivo - {n_combos:,} combinações{Style.RESET_ALL}")

    res_data_all = _preparar_masks_com_concurso(df)
    res_data_all.reverse()  # mais recente primeiro
    res_masks_recent = [m for m, _, _ in res_data_all[:RECENT_WINDOW]]

    combo_data = _gerar_combo_data(tamanho)
    n_proc = multiprocessing.cpu_count()
    chunks = _dividir_chunks(combo_data, n_proc)

    if verbose:
        print(f"    {n_proc} núcleos | Janela recente: {RECENT_WINDOW} sorteios")

    inicio = time.time()
    with multiprocessing.Pool(processes=n_proc) as pool:
        args = [(c, res_data_all, res_masks_recent) for c in chunks]
        ar = pool.starmap_async(_bloco_preditivo, args)
        while not ar.ready():
            if verbose:
                print(f"  Calculando... [{formatar_tempo(time.time()-inicio)}]", end="\r")
            time.sleep(0.5)
        resultados = [item for sub in ar.get() for item in sub]

    ranking = sorted(resultados, key=lambda x: x[2], reverse=True)

    if verbose:
        print(f"\n  {Fore.GREEN}[OK] Concluído em {formatar_tempo(time.time()-inicio)}!{Style.RESET_ALL}")

    txt, csv_p = _salvar_resultados_preditivo(ranking, top_n)

    if verbose:
        print(f"  📁 Salvos: {txt.name}, {csv_p.name}")

        def cor_atr(v):
            if v <= 10: return Fore.GREEN
            if v <= 30: return Fore.YELLOW
            return Fore.RED

        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}   TOP 10 - ÍNDICE PREDITIVO{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  {Fore.GREEN}Verde ≤10  {Fore.YELLOW}Amarelo 11-30  {Fore.RED}Vermelho >30{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-'*60}{Style.RESET_ALL}")

        for i, (combo, c, pi) in enumerate(ranking[:10], 1):
            dz = "  ".join(f"{Fore.CYAN}{d:02d}{Style.RESET_ALL}" for d in combo)
            a15 = c.get("atraso15", c.get("atraso", 0))
            a14 = c.get("atraso14", 0)
            a13 = c.get("atraso13", 0)
            a12 = c.get("atraso12", 0)
            a11 = c.get("atraso11", 0)
            k15 = c.get("conc15", -1)
            k14 = c.get("conc14", -1)
            k13 = c.get("conc13", -1)
            k12 = c.get("conc12", -1)
            k11 = c.get("conc11", -1)

            def fmt(a, k):
                cor = cor_atr(a)
                conc = f"conc.{k}" if k > 0 else "nunca"
                return f"{cor}{'[OK]' if a<=10 else '⚠️ ' if a<=30 else '🔴'} {a:>3} sorteios ({conc}){Style.RESET_ALL}"

            print(f"\n{Fore.CYAN}  +- #{i:02d}  PI: {pi:.4f} {'★'*min(i,5)}{Style.RESET_ALL}")
            print(f"  |  15pts: {fmt(a15,k15)}")
            print(f"  |  14pts: {fmt(a14,k14)}")
            print(f"  |  13pts: {fmt(a13,k13)}")
            print(f"  |  12pts: {fmt(a12,k12)}")
            print(f"  |  11pts: {fmt(a11,k11)}")
            print(f"  +- {dz}")

        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

    return ranking


def carregar_ranking_csv() -> list:
    """Carrega o ranking preditivo salvo em CSV."""
    csv_path = OUTPUT_DIR / "indice_preditivo.csv"
    if not csv_path.exists():
        return []
    try:
        import pandas as pd
        df = pd.read_csv(csv_path, sep=";", decimal=",")
        ranking = []
        for _, row in df.iterrows():
            dezenas = tuple(int(d) for d in str(row["Dezenas"]).split("-"))
            c = {
                "atraso14": int(row.get("Atraso14", 0)),
                "atraso13": int(row.get("Atraso13", 0)),
                "atraso12": int(row.get("Atraso12", 0)),
                "atraso11": int(row.get("Atraso11", 0)),
                "h14": int(row.get("Hist14", 0)),
                "h13": int(row.get("Hist13", 0)),
                "r14": int(row.get("Rec14", 0)),
                "r13": int(row.get("Rec13", 0)),
                "atraso": int(row.get("Atraso14", 0)),
                "conc14": -1, "conc13": -1, "conc12": -1, "conc11": -1,
            }
            # [OK] CORRIGIDO: coluna correta é "PI"
            pi = float(str(row["PI"]).replace(",", "."))
            ranking.append((dezenas, c, pi))
        return ranking
    except Exception as e:
        print(f"Erro ao carregar CSV: {e}")
        return []


def carregar_ranking_do_csv(df_sorteios=None) -> list:
    """
    Carrega o ranking do CSV salvo sem precisar recalcular.
    Também busca o último concurso que cada combinação saiu.
    """
    import pandas as pd
    csv_path = OUTPUT_DIR / "indice_preditivo.csv"
    if not csv_path.exists():
        csv_path = _BASE / "indice_preditivo.csv"
    if not csv_path.exists():
        return []

    df = pd.read_csv(csv_path, sep=";")
    ranking = []

    # Prepara histórico para buscar concursos
    num_cols = [f"n{i:02d}" for i in range(1, 16)]
    historico = []
    if df_sorteios is not None:
        for _, row in df_sorteios.iterrows():
            historico.append({
                "concurso": int(row["concurso"]),
                "data": row["data"],
                "nums": set(int(row[c]) for c in num_cols)
            })
        historico.reverse()  # mais recente primeiro

    for _, row in df.iterrows():
        try:
            dezenas = row["Dezenas"].split("-")
            combo = tuple(int(d) for d in dezenas)
            # [OK] CORRIGIDO: coluna correta é "PI" (não "Indice_Preditivo")
            pi = float(str(row["PI"]).replace(",", "."))
            c = {
                "atraso14": int(row.get("Atraso14", 0)),
                "conc14":   int(row.get("Conc14", 0)),
                "atraso13": int(row.get("Atraso13", 0)),
                "conc13":   int(row.get("Conc13", 0)),
                "atraso12": int(row.get("Atraso12", 0)),
                "conc12":   int(row.get("Conc12", 0)),
                "atraso11": int(row.get("Atraso11", 0)),
                "conc11":   int(row.get("Conc11", 0)),
                "h14": int(row.get("Hist14", 0)),
                "h13": int(row.get("Hist13", 0)),
                "r14": int(row.get("Rec14", 0)),
                "r13": int(row.get("Rec13", 0)),
                "atraso": 0,
                "ultimo_concurso": 0,
                "ultima_data": "",
                "ultimo_acertos": 0,
            }

            # Busca último concurso que essa combo saiu (11+ acertos)
            if historico:
                combo_set = set(combo)
                for h in historico:
                    acertos = len(combo_set & h["nums"])
                    if acertos >= 11:
                        c["ultimo_concurso"] = h["concurso"]
                        c["ultima_data"] = h["data"]
                        c["ultimo_acertos"] = acertos
                        break

            ranking.append((combo, c, pi))
        except Exception:
            continue

    return ranking


def exibir_ranking_csv(df_sorteios=None, top_n=10):
    """Carrega e exibe o ranking salvo com concursos."""
    print(f"\n{Fore.CYAN}  Carregando ranking salvo...{Style.RESET_ALL}")
    ranking = carregar_ranking_do_csv(df_sorteios)
    if not ranking:
        print(f"  {Fore.RED}❌ Nenhum arquivo salvo. Rode o Índice Preditivo (opção 22) primeiro!{Style.RESET_ALL}")
        return []

    print(f"  {Fore.GREEN}[OK] {len(ranking)} combinações carregadas!{Style.RESET_ALL}")
    print(f"\n{Fore.CYAN}{'='*75}")
    print(f"  TOP {top_n} - ÍNDICE PREDITIVO (do arquivo salvo)")
    print(f"{'-'*75}{Style.RESET_ALL}")

    for i, (combo, c, pi) in enumerate(ranking[:top_n], 1):
        dz = " ".join(f"{d:02d}" for d in combo)

        def cor(v):
            if v <= 10: return Fore.GREEN
            if v <= 30: return Fore.YELLOW
            return Fore.RED

        def fmt(faixa, atr, conc):
            c2 = cor(atr)
            conc_str = f"conc.{conc}" if conc > 0 else "nunca"
            return f"{c2}{faixa}: {atr:>4} sorteios ({conc_str}){Style.RESET_ALL}"

        a14 = c.get("atraso14", 0); k14 = c.get("conc14", 0)
        a13 = c.get("atraso13", 0); k13 = c.get("conc13", 0)
        a12 = c.get("atraso12", 0); k12 = c.get("conc12", 0)
        a11 = c.get("atraso11", 0); k11 = c.get("conc11", 0)
        ult = c.get("ultimo_concurso", 0)
        ult_data = c.get("ultima_data", "")
        ult_ac = c.get("ultimo_acertos", 0)

        print(f"\n{Fore.CYAN}  +- #{i:02d}  PI: {pi:.4f}{Style.RESET_ALL}")
        print(f"  |  {fmt('14pts', a14, k14)}")
        print(f"  |  {fmt('13pts', a13, k13)}")
        print(f"  |  {fmt('12pts', a12, k12)}")
        print(f"  |  {fmt('11pts', a11, k11)}")
        if ult > 0:
            print(f"  |  {Fore.GREEN}Último acerto: #{ult} ({ult_data}) - {ult_ac}pts{Style.RESET_ALL}")
        print(f"  +- {Fore.CYAN}{dz}{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}{'='*75}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}Verde ≤10  {Fore.YELLOW}Amarelo 11-30  {Fore.RED}Vermelho >30{Style.RESET_ALL}")
    return ranking


def extrair_nucleo_quente(ranking: list, top_n: int = 10, min_freq: int = 8):
    """Extrai dezenas mais frequentes nos top_n jogos do ranking."""
    from collections import Counter
    freq = Counter()
    for combo, _, _ in ranking[:top_n]:
        freq.update(combo)
    nucleo = sorted([n for n, c in freq.items() if c >= min_freq])
    return nucleo, freq


def gerar_jogos_15_do_preditivo(ranking: list, n_jogos: int = 10,
                                  top_n: int = 10, verbose: bool = True) -> list:
    """
    Usa o núcleo quente dos top_n jogos preditivos para gerar
    jogos completos de 15 dezenas.
    Verde = núcleo fixo | Amarelo = variável
    """
    from collections import Counter
    import random

    freq = Counter()
    for combo, _, _ in ranking[:top_n]:
        freq.update(combo)

    ranking_dez = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    todas_dez = [n for n, _ in ranking_dez]
    nucleo = todas_dez[:12]
    variaveis = todas_dez[12:20]

    if verbose:
        print(f"\n{Fore.CYAN}{'='*52}")
        print(f"  🔥 NÚCLEO QUENTE (mais frequentes no TOP {top_n}):")
        print(f"{'='*52}{Style.RESET_ALL}")
        dz_fmt = "  ".join(f"{Fore.GREEN}{n:02d}{Style.RESET_ALL}" for n in nucleo)
        print(f"  {dz_fmt}")
        print(f"\n   Frequência de cada dezena:")
        for num, cnt in ranking_dez[:20]:
            barra = "█" * cnt
            cor = Fore.GREEN if cnt >= 9 else (Fore.YELLOW if cnt >= 7 else Fore.WHITE)
            print(f"  {cor}Nº {num:02d}: {barra:<10} {cnt}/{top_n}{Style.RESET_ALL}")

    jogos = []
    random.seed(42)
    tentativas = 0
    vistos = set()

    while len(jogos) < n_jogos and tentativas < 1000:
        tentativas += 1
        extras = random.sample(variaveis, 3)
        jogo = sorted(set(nucleo + extras))[:15]
        chave = tuple(jogo)
        if chave not in vistos and len(jogo) == 15:
            vistos.add(chave)
            jogos.append(jogo)

    if verbose:
        print(f"\n{Fore.CYAN}{'='*52}")
        print(f"  🎯 {n_jogos} JOGOS DE 15 - GERADOS DO PREDITIVO")
        print(f"{'='*52}{Style.RESET_ALL}")
        for i, jogo in enumerate(jogos, 1):
            nums = "  ".join(
                f"{Fore.GREEN}{n:02d}{Style.RESET_ALL}" if n in nucleo
                else f"{Fore.YELLOW}{n:02d}{Style.RESET_ALL}"
                for n in jogo
            )
            print(f"  Jogo {i:02d}: {nums}")
        print(f"\n  {Fore.GREEN}= núcleo  {Fore.YELLOW}= variável{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*52}{Style.RESET_ALL}")

    return jogos


def carregar_preditivo_csv() -> list:
    """
    Carrega o ranking preditivo salvo em CSV.
    Retorna lista no mesmo formato do rodar_indice_preditivo.
    """
    csv_path = OUTPUT_DIR / "indice_preditivo.csv"
    if not csv_path.exists():
        return []

    import pandas as pd
    df = pd.read_csv(csv_path, sep=";", decimal=",")
    ranking = []
    for _, row in df.iterrows():
        dezenas = row["Dezenas"].split("-")
        combo = tuple(int(d) for d in dezenas)
        # [OK] CORRIGIDO: coluna correta é "PI" (não "Indice_Preditivo")
        pi = float(str(row["PI"]).replace(",", "."))
        c = {
            "h14": int(row["Hist14"]),
            "h13": int(row["Hist13"]),
            "r14": int(row["Rec14"]),
            "r13": int(row["Rec13"]),
            "atraso":    int(row["Atraso14"]),
            "atraso14":  int(row["Atraso14"]),
            "atraso13":  int(row["Atraso13"]),
            "atraso12":  int(row["Atraso12"]),
            "atraso11":  int(row["Atraso11"]),
        }
        ranking.append((combo, c, pi))
    return ranking


def mostrar_ultimo_concurso(df_sorteios, ranking: list, top_n: int = 10):
    """
    Para cada jogo do ranking, mostra o último concurso em que
    cada faixa de acertos (11-15) apareceu.
    """
    import pandas as pd
    num_cols = [f"n{i:02d}" for i in range(1, 16)]
    total = len(df_sorteios)

    print(f"\n{Fore.CYAN}{'='*72}")
    print(f"  🔍 ÚLTIMO CONCURSO POR FAIXA DE ACERTOS - TOP {top_n}")
    print(f"  {'#':>3}  {'PI':>7}  {'15ac':>6}  {'14ac':>6}  {'13ac':>6}  {'12ac':>6}  {'11ac':>6}")
    print(f"{'-'*72}{Style.RESET_ALL}")

    sorteios_lista = []
    for _, row in df_sorteios.iterrows():
        nums = set(int(row[c]) for c in num_cols)
        conc = int(row["concurso"])
        sorteios_lista.append((conc, nums))
    sorteios_lista = list(reversed(sorteios_lista))

    def cor_conc(v, total):
        if v == 0: return f"{Fore.WHITE}{'N/A':>6}{Style.RESET_ALL}"
        atraso = total - v
        if atraso <= 10: return f"{Fore.GREEN}{v:>6}{Style.RESET_ALL}"
        if atraso <= 50: return f"{Fore.YELLOW}{v:>6}{Style.RESET_ALL}"
        return f"{Fore.RED}{v:>6}{Style.RESET_ALL}"

    for i, (combo, c, pi) in enumerate(ranking[:top_n], 1):
        jogo_set = set(combo)
        ult = {15: 0, 14: 0, 13: 0, 12: 0, 11: 0}

        for conc, nums in sorteios_lista:
            acertos = len(jogo_set & nums)
            if acertos >= 11:
                for faixa in range(11, 16):
                    if acertos >= faixa and ult[faixa] == 0:
                        ult[faixa] = conc
            if all(ult[f] > 0 for f in range(11, 16)):
                break

        dz = " ".join(f"{d:02d}" for d in combo)
        print(f"  #{i:02d}  {pi:7.4f}  "
              f"{cor_conc(ult[15], total)}  "
              f"{cor_conc(ult[14], total)}  "
              f"{cor_conc(ult[13], total)}  "
              f"{cor_conc(ult[12], total)}  "
              f"{cor_conc(ult[11], total)}")
        print(f"       {Fore.CYAN}{dz}{Style.RESET_ALL}")

    print(f"{Fore.CYAN}{'='*72}{Style.RESET_ALL}")

def gerar_jogos_cacada_ciclo(df, dezenas_alvo: list, n_jogos: int = 6):
    """
    Estratégia: Caçador de Ciclo Interno.
    1. Identifica dezenas pendentes no ciclo.
    2. Define as pendentes como FIXAS.
    3. Completa com as melhores orbitais do mesmo grupo.
    """
    import random
    from src.analysis.stats import _extrair_lista_sorteios
    
    dezenas_alvo = set(dezenas_alvo)
    lista_sorteios = _extrair_lista_sorteios(df)
    
    # 1. Identificar Pendentes (Ciclo Atual - Fluxo Contínuo para Sincronia Total)
    vistos = set()
    for s in lista_sorteios:
        hits = sorted(list(s & dezenas_alvo))
        for h in hits:
            if vistos == dezenas_alvo:
                vistos = set()
            vistos.add(h)
            
    faltando = sorted(list(dezenas_alvo - vistos))
    ja_sairam = sorted(list(vistos))
    
    if not faltando:
        # Se o ciclo fechou agora, recomeça
        faltando = []
        ja_sairam = sorted(list(dezenas_alvo))

    # 2. Performance recente das dezenas no grupo
    scores = {d: 0 for d in dezenas_alvo}
    for s in lista_sorteios[-50:]: 
        for d in (s & dezenas_alvo):
            scores[d] += 1
            
    ja_sairam_ranked = sorted(ja_sairam, key=lambda d: scores[d], reverse=True)
    
    print(f"\n{Fore.CYAN}🏹 ESTRATÉGIA: CAÇADA DE CICLO (ELITE){Style.RESET_ALL}")
    print(f"  {Fore.RED}Alvos Fixos (Faltando):{Style.RESET_ALL} {' '.join(f'{d:02d}' for d in faltando)}")
    print(f"  {Fore.GREEN}Reforços (Melhor performance):{Style.RESET_ALL} {' '.join(f'{d:02d}' for d in ja_sairam_ranked[:5])}")

    jogos = []
    # Usar todas as faltando como base (se < 15)
    base = faltando
    disponiveis = ja_sairam_ranked
    
    random.seed(time.time())
    
    for i in range(n_jogos):
        # Selecionar variabilidade
        tamanho_base = len(base)
        n_necessario = 15 - tamanho_base
        
        if n_necessario > 0:
            # Usamos todas as dezenas do Rei que já saíram como pool (sem limite de 10)
            # Isso evita erros quando precisamos de muitos reforços
            pool = disponiveis
            if len(pool) >= n_necessario:
                reforcos = random.sample(pool, n_necessario)
            else:
                # Caso extremo: se não houver dezenas suficientes no Rei, pegamos o que dá
                reforcos = pool
                # E completamos com as dezenas que mais saem na Lotofácil em geral
                faltam_ainda = 15 - (tamanho_base + len(reforcos))
                if faltam_ainda > 0:
                    outras = [n for n in range(1,26) if n not in set(base + reforcos)]
                    reforcos += random.sample(outras, faltam_ainda)
            
            jogo = sorted(base + reforcos)
        else:
            # Se faltam 15 ou mais (ciclo recém começado), pegamos 15 das faltantes
            jogo = sorted(random.sample(base, 15))
            
        jogos.append(jogo)

    print(f"\n{Fore.CYAN}╔{'═'*52}╗")
    print(f"║ 🎯 {n_jogos} JOGOS GERADOS PARA FECHAMENTO DE CICLO       ║")
    print(f"╚{'═'*52}╝{Style.RESET_ALL}")
    
    for i, jogo in enumerate(jogos, 1):
        num_str = ""
        for n in jogo:
            if n in faltando:
                num_str += f"{Back.RED}{Fore.WHITE}{n:02d}{Style.RESET_ALL} "
            else:
                num_str += f"{Fore.GREEN}{n:02d}{Style.RESET_ALL} "
        print(f"  Jogo {i:02d}: {num_str}")
        
    print(f"\n  {Back.RED}  {Style.RESET_ALL} = Dezenas Pendentes (Faltam no Ciclo)")
    print(f"  {Fore.GREEN}00{Style.RESET_ALL} = Dezenas de Reforço (Melhor Performance)")
    
    return jogos

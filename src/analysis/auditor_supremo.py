"""
AUDITOR SUPREMO - v2.0
O Cérebro do Vitoria-Loto: Unificação de Ciclos, Atrasos e Recordistas com Análise Térmica.
"""
import pandas as pd
import json
from pathlib import Path
from colorama import Fore, Style, Back, init
from collections import Counter

init(autoreset=True)

class AuditorSupremo:
    def __init__(self, df: pd.DataFrame, base_path: Path):
        self.df = df
        self.base_path = base_path
        self.sorteios = self._preparar_sorteios()
        self.concursos = df['concurso'].tolist()
        self.hall_17 = self._carregar_json("hall_of_fame.json")
        self.hall_18 = self._carregar_json("hall_of_fame_18.json")
        self.hall_19 = self._carregar_json("hall_of_fame_19.json")
        self.hall_20 = self._carregar_json("hall_of_fame_20.json")

    def _carregar_json(self, filename):
        path = self.base_path / "data" / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _preparar_sorteios(self):
        num_cols = [f"n{i:02d}" for i in range(1, 16)]
        return [set(row[num_cols].astype(int)) for _, row in self.df.iterrows()]

    def calcular_atrasos(self):
        atraso = {n: 0 for n in range(1, 26)}
        for n in range(1, 26):
            for i in range(len(self.sorteios)-1, -1, -1):
                if n in self.sorteios[i]:
                    break
                atraso[n] += 1
        return atraso

    def calcular_heat(self, ultimos_n=10):
        heat = {n: 0 for n in range(1, 26)}
        for s in self.sorteios[-ultimos_n:]:
            for n in s:
                heat[n] += 1
        return heat

    def analisar_ciclo_interno(self, target_set):
        target = set(target_set)
        vistos = set()
        inicio_idx = 0
        
        for i in range(len(self.sorteios)-1, -1, -1):
            vistos.update(self.sorteios[i] & target)
            if vistos == target:
                inicio_idx = i + 1
                break
        
        vistos_atual = set()
        cronologia = {}
        for i in range(inicio_idx, len(self.sorteios)):
            acertos = self.sorteios[i] & target
            if acertos:
                vistos_atual.update(acertos)
                cronologia[self.concursos[i]] = sorted(list(acertos))
            else:
                cronologia[self.concursos[i]] = []
            
        return {
            "pendentes": target - vistos_atual,
            "vistos": vistos_atual,
            "concursos_no_ciclo": len(self.sorteios) - inicio_idx,
            "inicio_conc": self.concursos[inicio_idx] if inicio_idx < len(self.concursos) else self.concursos[-1],
            "cronologia": cronologia
        }

    def validar_dna(self, dezenas):
        """Valida se um conjunto de dezenas respeita os padrões reais."""
        pares = len([n for n in dezenas if n % 2 == 0])
        impares = 15 - pares
        soma = sum(dezenas)
        primos = len([n for n in dezenas if n in [2, 3, 5, 7, 11, 13, 17, 19, 23]])
        
        ok_pares = 6 <= pares <= 9
        ok_soma = 170 <= soma <= 220
        ok_primos = 4 <= primos <= 7
        
        erros = []
        if not ok_pares: erros.append(f"Pares ({pares}) fora do comum")
        if not ok_soma: erros.append(f"Soma ({soma}) fora da curva")
        if not ok_primos: erros.append(f"Primos ({primos}) instáveis")
        
        return len(erros) == 0, erros

    def calcular_velocidade_media(self, target_set):
        """Calcula a velocidade média histórica de fechamento para um grupo."""
        target = set(target_set)
        num_target = len(target)
        historico_velocidade = [] # Lista de [novos_no_sorteio_1, novos_no_2, ...]
        
        vistos = set()
        progresso_ciclo = []
        
        # Simular ciclos passados
        for s in self.sorteios:
            acertos = s & target
            novos = acertos - vistos
            progresso_ciclo.append(len(novos))
            vistos.update(acertos)
            
            if vistos == target:
                historico_velocidade.append(progresso_ciclo)
                vistos = set()
                progresso_ciclo = []
        
        if not historico_velocidade: return {}
        
        # Média por posição
        max_len = max(len(h) for h in historico_velocidade)
        medias = []
        for i in range(max_len):
            vals = [h[i] for h in historico_velocidade if i < len(h)]
            medias.append(sum(vals) / len(vals))
            
        return {"medias": medias, "total": num_target}

    def calcular_ciclo_geral(self):
        """Identifica dezenas pendentes no ciclo geral de 25 dezenas (v2: robusto)."""
        vistos = set()
        # Começamos do último e voltamos até ver as 25.
        # O ponto onde bater 25 é o fim do ciclo anterior.
        for i in range(len(self.sorteios)-1, -1, -1):
            temp_vistos = vistos | self.sorteios[i]
            if len(temp_vistos) == 25:
                # O sorteio 'i' fechou o ciclo anterior.
                # O ciclo ATUAL é do i+1 até o fim.
                break
            vistos = temp_vistos
        
        return set(range(1, 26)) - vistos

    def gerar_veredito(self, usar_termica: bool = False):
        atrasos_gerais = self.calcular_atrasos()
        heat_geral = self.calcular_heat()
        ciclo_geral_pendentes = self.calcular_ciclo_geral()
        radar_ciclos = Counter()
        detalhes_convergencia = {}
        status_velocidade = {}
        
        # Mapa de Calor Integrado (Se solicitado)
        termica = {}
        if usar_termica:
            from src.analysis.stats import calcular_mapa_calor_pontos_pro
            dados_halls = {"17": self.hall_17, "18": self.hall_18, "19": self.hall_19, "20": self.hall_20}
            res_calor = calcular_mapa_calor_pontos_pro(self.df, dados_halls)
            # Calcular média de pontos nos últimos 10 sorteios para cada rei
            ultimos_10 = res_calor[:10]
            for elite in ["17", "18", "19", "20"]:
                termica[elite] = {}
                for k in ["15", "14", "13", "12", "11"]:
                    pts_total = sum(d["pontos"][elite].get(k, 0) for d in ultimos_10)
                    termica[elite][k] = pts_total / 10 if ultimos_10 else 0

        halls = [("17", self.hall_17), ("18", self.hall_18), ("19", self.hall_19), ("20", self.hall_20)]
        
        for elite, dados in halls:
            for k, rei in dados.items():
                target = rei["dezenas"]
                res = self.analisar_ciclo_interno(target)
                
                # Bônus de Temperatura (Opção 80)
                bonus_termico = 0
                if usar_termica and elite in termica and k in termica[elite]:
                    media_pts = termica[elite][k]
                    # Se o Rei está pontuando bem (acima de 11.5 de média), ele é "Quente"
                    if media_pts >= 12.0: bonus_termico = 15
                    elif media_pts >= 11.0: bonus_termico = 8
                
                # Bônus de Maturidade de Ciclo
                bonus_maturidade = 0
                n_faltam = len(res["pendentes"])
                if 1 <= n_faltam <= 3:
                    bonus_maturidade = 20 # Alvo maduro!
                elif n_faltam == 0:
                    bonus_maturidade = -10 # Ciclo acabou de fechar, resfriando.

                for p in res["pendentes"]:
                    # O score de cada dezena agora leva em conta a performance do grupo que a contém
                    radar_ciclos[p] += (12 + bonus_termico + bonus_maturidade)
                    if p not in detalhes_convergencia: detalhes_convergencia[p] = []
                    detalhes_convergencia[p].append(f"{rei['titulo']}")

        ranking_convergencia = []
        for d in range(1, 26):
            total_pontos_ciclo = radar_ciclos.get(d, 0)
            peso_atraso = atrasos_gerais.get(d, 0)
            peso_heat = heat_geral.get(d, 0)
            
            bonus_ciclo_geral = 30 if d in ciclo_geral_pendentes else 0
            
            # Cálculo Final da Suplemacia
            score = total_pontos_ciclo + (min(peso_atraso, 5) * 6) + (peso_heat * 4) + bonus_ciclo_geral
            
            if score > 0:
                ranking_convergencia.append({
                    "dezena": d,
                    "score": score,
                    "qtd_ciclos": radar_ciclos.get(d, 0) // 12, # Qtd original aproximada
                    "atraso": peso_atraso,
                    "heat": peso_heat,
                    "sincronia": d in ciclo_geral_pendentes,
                    "fontes": list(set(detalhes_convergencia.get(d, [])))
                })

        ranking_convergencia.sort(key=lambda x: x["score"], reverse=True)
        return ranking_convergencia

    def exibir_relatorio(self):
        veredito = self.gerar_veredito()
        ciclo_geral = self.calcular_ciclo_geral()
        
        print(f"\n{Fore.MAGENTA}╔{'═'*118}╗")
        print(f"║ 🏛️  AUDITOR SUPREMO v2.8 — COMPARAÇÃO GERAL DE ELITE (17 DZ vs 18 DZ)                                     ║")
        print(f"╚{'═'*118}╝{Style.RESET_ALL}")

        # Cabeçalhos das Colunas
        h17 = f"{Fore.CYAN}ELITE 17 DZ (RECORDISTAS CLÁSSICOS){Style.RESET_ALL}"
        h18 = f"{Fore.YELLOW}ELITE 18 DZ (OS NOVOS REIS){Style.RESET_ALL}"
        print(f"  {h17:^58} │ {h18:^58}")
        print(f"  {'REI':<3}│{'INI':<5}│{'ATR':<3}│{'PROGRES':<10}│{'FALTAM':<20}  │  {'REI':<3}│{'INI':<5}│{'ATR':<3}│{'PROGRES':<10}│{'FALTAM':<20}")
        print(f"  {'─'*3}┼{'─'*5}┼{'─'*3}┼{'─'*10}┼{'─'*20}──┼──{'─'*3}┼{'─'*5}┼{'─'*3}┼{'─'*10}┼{'─'*20}")

        for k in ["15", "14", "13", "12", "11"]:
            # Processar 17
            rei17 = self.hall_17.get(k, {"dezenas": []})
            res17 = self.analisar_ciclo_interno(rei17["dezenas"])
            qtd17 = len(rei17["dezenas"])
            idx17 = res17["concursos_no_ciclo"]
            ini17 = str(res17["inicio_conc"])[-4:]
            prog17 = len(res17["vistos"]) / qtd17 if qtd17 > 0 else 0
            barra17 = "█" * int(prog17 * 10) + "░" * (10 - int(prog17 * 10))
            
            p_list17 = sorted(list(res17["pendentes"]))[:7]
            pend17_str = " ".join(f"{Fore.GREEN if d in ciclo_geral else Fore.WHITE}{d:02d}{Style.RESET_ALL}" for d in p_list17)
            # Pad manual para compensar cores (3 chars por numero + 2 se tiver ..)
            pad17 = " " * (22 - (len(p_list17) * 3))
            if len(res17["pendentes"]) > 7: pend17_str += ".."; pad17 = pad17[:-2]

            # Processar 18
            rei18 = self.hall_18.get(k, {"dezenas": []})
            res18 = self.analisar_ciclo_interno(rei18["dezenas"])
            qtd18 = len(rei18["dezenas"])
            idx18 = res18["concursos_no_ciclo"]
            ini18 = str(res18["inicio_conc"])[-4:]
            prog18 = len(res18["vistos"]) / qtd18 if qtd18 > 0 else 0
            barra18 = "█" * int(prog18 * 10) + "░" * (10 - int(prog18 * 10))
            
            p_list18 = sorted(list(res18["pendentes"]))[:7]
            pend18_str = " ".join(f"{Fore.GREEN if d in ciclo_geral else Fore.WHITE}{d:02d}{Style.RESET_ALL}" for d in p_list18)
            pad18 = " " * (22 - (len(p_list18) * 3))
            if len(res18["pendentes"]) > 7: pend18_str += ".."; pad18 = pad18[:-2]

            line_17 = f"{Fore.CYAN}{k:<3}{Style.RESET_ALL}│{ini17:<5}│{idx17:<3}│{barra17}│{pend17_str}{pad17}"
            line_18 = f"{Fore.YELLOW}{k:<3}{Style.RESET_ALL}│{ini18:<5}│{idx18:<3}│{barra18}│{pend18_str}{pad18}"
            print(f"  {line_17}  │  {line_18}")

        print(f"\n  {Fore.GREEN}★ Dica: Dezenas em VERDE estão pendentes no CICLO GERAL de 25 números.{Style.RESET_ALL}")
        print(f"  {Fore.MAGENTA}{'═'*120}{Style.RESET_ALL}")

        # --- AJUSTE DE ALINHAMENTO SUPREMO v3.4 ---
        import re
        def get_real_len(text):
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            return len(ansi_escape.sub('', text))

        def pad_to(text, width):
            return text + (" " * max(0, width - get_real_len(text)))

        # 1. Coletar frequências globais (17, 18, 19 e 20)
        frequencias_totais = Counter()
        for d_hall in [self.hall_17, self.hall_18, self.hall_19, self.hall_20]:
            for r_obj in d_hall.values():
                if r_obj.get("dezenas"):
                    frequencias_totais.update(r_obj["dezenas"])

        # Timeline global consolidada (17, 18, 19 e 20)
        res_list = []
        for d_hall in [self.hall_17, self.hall_18, self.hall_19, self.hall_20]:
            for r_obj in d_hall.values():
                if r_obj.get("dezenas"):
                    res_list.append(self.analisar_ciclo_interno(r_obj["dezenas"]))
        
        timeline_global = sorted(list(set().union(*(res_obj["cronologia"].keys() for res_obj in res_list))))

        def exibir_jornada(hall_dados, label_color):
            for k in ["15", "14", "13", "12", "11"]:
                rei = hall_dados.get(k, {"dezenas": []})
                if not rei["dezenas"]: continue
                res = self.analisar_ciclo_interno(rei["dezenas"])
                cron = res["cronologia"]
                faltam = res["pendentes"]

                # Início da linha
                line = f"  {label_color}REI {k:<2}{Style.RESET_ALL} │"
                
                # Identificar dezenas já vistas ANTES da janela de exibição
                inicio_timeline = timeline_global[-3] if len(timeline_global) >= 3 else timeline_global[0]
                ja_vistos = set()
                for c_past, ac_past in cron.items():
                    if c_past < inicio_timeline:
                        ja_vistos.update(ac_past)

                # Mostrar os últimos 3 sorteios ativos da timeline global
                for conc in timeline_global[-3:]:
                    acertos_todos = cron.get(conc, [])
                    # Filtro de Ordem de Chegada
                    novos_ativos = [n for n in acertos_todos if n not in ja_vistos]
                    
                    bloco_str = ""
                    if novos_ativos:
                        ja_vistos.update(novos_ativos)
                        parts = []
                        for n in novos_ativos:
                            f = frequencias_totais.get(n, 0)
                            cor = (Fore.RED + Style.BRIGHT) if f >= 8 else (Fore.YELLOW if f >= 4 else Fore.WHITE)
                            parts.append(f"{cor}{n:02d}{Style.RESET_ALL}")
                        
                        short_conc = str(conc)[-4:]
                        bloco_str = f" [{short_conc}]: {','.join(parts)} "
                    
                    # Pad do bloco de sorteio fixo em 45 (Equilíbrio entre largura e visibilidade)
                    line = pad_to(line, get_real_len(line))
                    line += pad_to(bloco_str, 45) + "│"
                
                # Coluna final do FALTA (Ancorada na coluna 160 para alinhamento profissional)
                line = pad_to(line, 160)
                if faltam:
                    f_parts = []
                    for n in sorted(list(faltam)):
                        cor = Fore.GREEN if n in ciclo_geral else Fore.WHITE
                        f_parts.append(f"{cor}{n:02d}{Style.RESET_ALL}")
                    # Usando apenas texto vermelho, sem fundo, para não "sujar" o visual
                    line += f" {Fore.RED if not any(n in ciclo_geral for n in faltam) else Fore.RED + Style.BRIGHT}[FALTAM]: {','.join(f_parts)}{Style.RESET_ALL}"
                else:
                    line += f" {Fore.GREEN}[FECHADO]{Style.RESET_ALL}"
                
                print(line)

        print(f"\n{Fore.YELLOW}🎞️  JORNADA DAS 17 DEZENAS (ORDEM DE CHEGADA):{Style.RESET_ALL}")
        exibir_jornada(self.hall_17, Fore.CYAN)

        print(f"\n{Fore.YELLOW}🎞️  JORNADA DAS 18 DEZENAS (ORDEM DE CHEGADA):{Style.RESET_ALL}")
        exibir_jornada(self.hall_18, Fore.YELLOW)

        print(f"\n{Fore.YELLOW}🎞️  JORNADA DAS 19 DEZENAS (ORDEM DE CHEGADA):{Style.RESET_ALL}")
        exibir_jornada(self.hall_19, Fore.MAGENTA)

        print(f"\n{Fore.YELLOW}🎞️  JORNADA DAS 20 DEZENAS (ORDEM DE CHEGADA):{Style.RESET_ALL}")
        exibir_jornada(self.hall_20, Fore.RED)

        print(f"\n  {Fore.GREEN}★ Dica: Dezenas em VERDE estão no Ciclo Geral.{Style.RESET_ALL} │ {Fore.RED}{Style.BRIGHT}●{Style.RESET_ALL} = Dezenas Ultra-Master (+10 Reis)")
        print(f"  {Fore.MAGENTA}{'═'*120}{Style.RESET_ALL}")

def exibir_suplemacia_ia(df, base_path):
    """
    Novo relatório (Opção 90) que mostra o Super Filtro resultante da fusão 60 + 80.
    """
    auditor = AuditorSupremo(df, base_path)
    veredito = auditor.gerar_veredito(usar_termica=True)
    
    print(f"\n{Fore.YELLOW}╔{'═'*80}╗")
    print(f"║ 🧠 SUPER FILTRO IA SUPREMO v1.0 — FUSÃO TÉRMICA & CONVERGÊNCIA             ║")
    print(f"╚{'═'*80}╝{Style.RESET_ALL}")
    
    print(f"\n  {Fore.CYAN}🎯 PADRÃO DE OURO IDENTIFICADO (TOP 18 DEZENAS):{Style.RESET_ALL}")
    
    top_18 = veredito[:18]
    # Formatação em grade 6x3
    for i in range(0, 18, 6):
        bloco = top_18[i:i+6]
        line = "  "
        for d in bloco:
            score_color = Fore.YELLOW if d['score'] > 200 else (Fore.GREEN if d['score'] > 100 else Fore.WHITE)
            line += f"{score_color}{d['dezena']:02d}{Style.RESET_ALL} (S:{int(d['score']):<3})   "
        print(line)

    print(f"\n  {Fore.MAGENTA}📊 RAIO-X DOS TOP 5 ALVOS:{Style.RESET_ALL}")
    for d in veredito[:5]:
        sinc = f"{Fore.GREEN}[SINCRO]{Style.RESET_ALL}" if d['sincronia'] else ""
        print(f"  {Fore.WHITE}Dezena {d['dezena']:02d}{Style.RESET_ALL} │ Score: {Fore.YELLOW}{d['score']}{Style.RESET_ALL} │ Ciclos: {d['qtd_ciclos']} │ Fontes: {', '.join(d['fontes'][:3])} {sinc}")

    # Gerar Filtro sugerido
    dezenas_filtro = [d['dezena'] for d in veredito[:19]]
    print(f"\n  {Fore.CYAN}🛡️  SUPER FILTRO SUGERIDO:{Style.RESET_ALL}")
    print(f"  Minimo de 11 dezenas do conjunto: {sorted(dezenas_filtro)}")

def gerar_jogos_suplemacia(df, base_path, n_jogos=10):
    """
    Gera jogos baseados no ranking de suplemacia (Opção 91).
    Usa fixas de score alto e completa com o top 19.
    """
    from src.analysis.stats import exibir_jogos
    from src.analysis.memoria import registrar_jogos_memoria
    from src.data.database import ultimo_concurso
    import random

    # Identificar o próximo concurso alvo
    prox_conc = ultimo_concurso() + 1

    auditor = AuditorSupremo(df, base_path)
    veredito = auditor.gerar_veredito(usar_termica=True)
    
    # Dezenas com Score acima de 150 são consideradas FIXAS
    fixas = [d['dezena'] for d in veredito if d['score'] >= 150]
    # Se tivermos mais de 11 fixas, pegamos as top 11 para garantir variabilidade
    if len(fixas) > 11: fixas = fixas[:11]
    
    # Pool de dezenas (as top 19 do ranking)
    pool = [d['dezena'] for d in veredito[:19]]
    candidatos = [d for d in pool if d not in fixas]
    
    jogos = []
    print(f"\n{Fore.CYAN}🚀 GERANDO {n_jogos} JOGOS DA SUPREMACIA IA...{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Base Fixa ({len(fixas)} dezenas): {fixas}{Style.RESET_ALL}")
    
    intentos = 0
    while len(jogos) < n_jogos and intentos < 500:
        intentos += 1
        # Escolher dezenas para completar 15
        precisa = 15 - len(fixas)
        if precisa > len(candidatos): 
             # Fallback: usar todas as dezenas disponíveis no banco se o pool for pequeno
             pool_completo = list(range(1,26))
             sorteados = random.sample([d for d in pool_completo if d not in fixas], precisa)
        else:
             sorteados = random.sample(candidatos, precisa)
             
        jogo = sorted(fixas + sorteados)
        
        # Validar DNA básico (Pares e Soma)
        ok, _ = auditor.validar_dna(jogo)
        if ok and jogo not in jogos:
            jogos.append(jogo)

    if jogos:
        exibir_jogos(jogos, f"JOGOS GERADOS — SUPREMACIA IA (PARA CONCURSO {prox_conc})")
        registrar_jogos_memoria(jogos, concurso=prox_conc)
        print(f"\n  {Fore.GREEN}✅ {len(jogos)} jogos registrados para o Concurso {prox_conc}!{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}❌ Falha ao encontrar combinações válidas com o DNA selecionado.{Style.RESET_ALL}")
    
    return jogos

def rodar_auditoria_suprema(df, base_path):
    auditor = AuditorSupremo(df, base_path)
    auditor.exibir_relatorio()

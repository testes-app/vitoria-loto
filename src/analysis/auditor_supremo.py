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

    def gerar_veredito(self):
        atrasos_gerais = self.calcular_atrasos()
        heat_geral = self.calcular_heat()
        ciclo_geral_pendentes = self.calcular_ciclo_geral()
        radar_ciclos = Counter()
        detalhes_convergencia = {}
        status_velocidade = {}

        halls = [("17 DZ", self.hall_17), ("18 DZ", self.hall_18)]
        
        for label, dados in halls:
            for k, rei in dados.items():
                target = rei["dezenas"]
                res = self.analisar_ciclo_interno(target)
                vel = self.calcular_velocidade_media(target)
                idx_atual = res["concursos_no_ciclo"] - 1
                if idx_atual >= 0 and "medias" in vel:
                    esperado = sum(vel["medias"][:idx_atual+1])
                    visto = len(res["vistos"])
                    diff = visto - esperado
                    status_velocidade[k] = {
                        "status": "🐢 LENTO" if diff < -1.5 else ("🚀 RÁPIDO" if diff > 1.5 else "⚖️ MÉDIA"),
                        "pressao": abs(diff) if diff < 0 else 0
                    }

                for p in res["pendentes"]:
                    radar_ciclos[p] += 1
                    if p not in detalhes_convergencia: detalhes_convergencia[p] = []
                    detalhes_convergencia[p].append(f"{rei['titulo']}")

        ranking_convergencia = []
        for d in range(1, 26):
            peso_ciclo = radar_ciclos.get(d, 0)
            peso_atraso = atrasos_gerais.get(d, 0)
            peso_heat = heat_geral.get(d, 0)
            
            # Sincronia Oficial: Se falta no ciclo geral de 25, ganha bônus de peso
            bonus_ciclo_geral = 25 if d in ciclo_geral_pendentes else 0
            
            score = (peso_ciclo * 12) + (min(peso_atraso, 5) * 6) + (peso_heat * 4) + bonus_ciclo_geral
            
            if score > 0:
                ranking_convergencia.append({
                    "dezena": d,
                    "score": score,
                    "qtd_ciclos": peso_ciclo,
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

def rodar_auditoria_suprema(df, base_path):
    auditor = AuditorSupremo(df, base_path)
    auditor.exibir_relatorio()

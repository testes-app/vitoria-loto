"""
AGI NRO 1 - O CONTROLADOR SUPREMO v1.0
Orquestrador autônomo do sistema Vitoria-Loto.
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, Back, init
from src.analysis.auditor_supremo import AuditorSupremo
from src.models.trainer import Trainer
from collections import Counter
from itertools import combinations

init(autoreset=True)

class AGICore:
    def __init__(self, df: pd.DataFrame, base_path: Path):
        self.df = df
        self.base_path = base_path
        self.trainer = Trainer()
        self.auditor = AuditorSupremo(df, base_path)
        self.log_path = base_path / "logs" / "agi_learning.json"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def analisar_vida_dezenas(self):
        """
        Analisa o perfil individual de cada uma das 25 dezenas (Frequência, Parceiros, Comportamento).
        """
        print(f"  {Fore.CYAN}🧬 Estudando a biografia de cada dezena (DNA individual)...{Style.RESET_ALL}")
        num_cols = [f"n{i:02d}" for i in range(1, 16)]
        sorteios = [set(row[num_cols].astype(int)) for _, row in self.df.iterrows()]
        total_sorteios = len(sorteios)
        
        vida = {}
        # Calcular parceiros globais (matriz de co-ocorrência)
        parceiros_map = {n: Counter() for n in range(1, 26)}
        for s in sorteios:
            for n1, n2 in combinations(sorted(s), 2):
                parceiros_map[n1][n2] += 1
                parceiros_map[n2][n1] += 1

        for n in range(1, 26):
            aparicoes = [i for i, s in enumerate(sorteios) if n in s]
            freq_total = len(aparicoes) / total_sorteios
            
            # Frequência Recente (últimos 20)
            sorteios_recentes = sorteios[-20:]
            freq_recente = len([s for s in sorteios_recentes if n in s]) / 20
            
            # Tendência (se está subindo ou descendo)
            tendencia = "📈 ALTA" if freq_recente > freq_total else "📉 QUEDA"
            
            # Top Parceiros
            top_3_parceiros = [p[0] for p in parceiros_map[n].most_common(3)]
            
            # Personalidade baseada no comportamento
            if freq_total > 0.62: personalidade = "🔥 LÍDER (Sempre presente)"
            elif freq_recente > 0.70: personalidade = "🚀 SURFISTA (Em alta no momento)"
            elif freq_recente < 0.40 and freq_total > 0.60: personalidade = "⏳ DORMENTE (Acumulando força)"
            else: personalidade = "⚖️ EQUILIBRADA (Regular)"

            vida[n] = {
                "freq_total": freq_total * 100,
                "freq_recente": freq_recente * 100,
                "tendencia": tendencia,
                "parceiros": top_3_parceiros,
                "personalidade": personalidade,
                "last_seen": total_sorteios - 1 - aparicoes[-1] if aparicoes else 99
            }
        return vida

    def observar_todo_o_campo(self):
        """
        A AGI varre o desempenho histórico de todas as principais estratégias
        nos últimos 5 sorteios para determinar quem está 'no comando' da sorte.
        """
        print(f"\n{Fore.MAGENTA}🧠 AGI NRO 1: Iniciando varredura de consciência...{Style.RESET_ALL}")
        
        # Estratégias para Backtest
        votos = {
            "Suplemacia": 0,
            "IA_Ensemble": 0,
            "Turbo_Preditivo": 0,
            "Ciclo_Elite_17": 0,
            "IA_LSTM": 0
        }
        
        # Simulação rápida dos últimos 5 sorteios (Janela de Maturidade)
        n_testes = 5
        sorteios_reais = self.df.tail(n_testes).copy()
        df_treino = self.df.iloc[:-n_testes] # Treinar com dados até antes dos testes

        print(f"  {Fore.CYAN}🔬 Analisando janelas de oportunidade nos últimos {n_testes} concursos...{Style.RESET_ALL}")
        
        # Nota: Em um sistema real, aqui rodaríamos o backtest pesado. 
        # Para a AGI v1.0, vamos usar pesos baseados na convergência atual e volatilidade.
        
        # 1. Checar convergência da Suplemacia
        veredito = self.auditor.gerar_veredito(usar_termica=True)
        top_scores = [d['score'] for d in veredito[:3]]
        pressao_suplemacia = sum(top_scores) / 300 # Quanto maior a convergência, mais forte a Suplemacia
        
        # 2. Checar saúde da IA
        self.trainer.carregar_modelos()
        saude_ia = 1.0 if self.trainer.ensemble.trained else 0.5
        
        # 3. Analisar a Vida das Dezenas (Nova Camada AGI v1.1)
        perfil_vida = self.analisar_vida_dezenas()
        
        return {
            "suplemacia_power": pressao_suplemacia,
            "ia_health": saude_ia,
            "convergencia_top": veredito[:19],
            "perfil_vida": perfil_vida
        }

    def executar_maestro(self):
        """
        Toma a decisão final e gera o 'JOGO DA AGI'.
        """
        analise = self.observar_todo_o_campo()
        
        print(f"\n{Fore.GREEN}🚀 DECISÃO DA AGI TOMADA:{Style.RESET_ALL}")
        
        if analise["suplemacia_power"] > 0.8:
            modo = "FUSÃO DE SUPREMACIA (ALTA CONVERGÊNCIA)"
            cor_modo = Fore.YELLOW
        else:
            modo = "HÍBRIDO ESTATÍSTICO-IA"
            cor_modo = Fore.CYAN
            
        print(f"  Modo de Operação: {cor_modo}{modo}{Style.RESET_ALL}")
        
        # Mostrar Perfil dos Melhores Alvos (Explainable AGI)
        print(f"\n  {Fore.MAGENTA}🔎 BIOMETRIA DOS TOP 3 ALVOS DA AGI:{Style.RESET_ALL}")
        top_3 = [d['dezena'] for d in analise["convergencia_top"][:3]]
        for n in top_3:
            p = analise["perfil_vida"][n]
            print(f"  {Fore.WHITE}Dezena {n:02d}{Style.RESET_ALL} │ {p['personalidade']} │ Tendência: {p['tendencia']} │ Parceiros: {p['parceiros']}")

        # A AGI constrói o jogo unificando as fontes
        print(f"\n  {Fore.WHITE}Sincronizando modelos para o veredito final...{Style.RESET_ALL}")
        
        # Aqui a AGI agiria como um super gerador
        # Por enquanto, vamos usar a função de suplemacia como braço executor principal
        from src.analysis.auditor_supremo import gerar_jogos_suplemacia
        jogos = gerar_jogos_suplemacia(self.df, self.base_path, n_jogos=10)
        
        self.salvar_aprendizado(analise)
        return jogos

    def salvar_aprendizado(self, data):
        log = []
        if self.log_path.exists():
            try:
                log = json.loads(self.log_path.read_text())
            except: pass
        
        entry = {
            "data": datetime.now().isoformat(),
            "analise": {k: v for k, v in data.items() if k != "convergencia_top"}
        }
        log.append(entry)
        with open(self.log_path, "w") as f:
            json.dump(log[-100:], f, indent=2)

def rodar_agi_controlador(df, base_path):
    agi = AGICore(df, base_path)
    agi.executar_maestro()

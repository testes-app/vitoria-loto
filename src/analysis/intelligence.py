import logging
import json
from datetime import datetime, timedelta
from src.config import STATUS_PATH, JOBS_PATH
from src.models.trainer import Trainer
from src.data.database import carregar_sorteios

logger = logging.getLogger("VitoriaIntelligence")

class SuperIntelligence:
    """
    Orquestrador de IA de alto nível para o projeto Vitoria-Loto.
    Gerencia modelos, decide quando treinar e aplica filtros de segurança.
    """
    def __init__(self):
        self.trainer = Trainer()
        self.last_sync = None
        
    def check_health(self):
        """Verifica se os modelos precisam de atualização."""
        status = {}
        if STATUS_PATH.exists():
            status = json.loads(STATUS_PATH.read_text())
        
        last_train = status.get("ultimo_treino")
        if not last_train:
            return "critical" # Nunca treinado
            
        dt = datetime.fromisoformat(last_train)
        if datetime.now() - dt > timedelta(days=3):
            return "warning" # Treino antigo
            
        return "healthy"

    def gerar_melhores_jogos(self, n_jogos=10):
        """Gera jogos usando o conjunto completo de IA e filtros matemáticos."""
        logger.info(f"Gerando os top {n_jogos} jogos com Super Intelligence...")
        
        # 1. Carregar dados
        self.trainer.carregar_modelos()
        
        # 2. Geração via Super Combo Turbo (Ensemble + LSTM + AG)
        jogos = self.trainer.gerar_jogos_turbo_super_combo(
            n_jogos=n_jogos * 2, # Gera o dobro para filtrar
            top_n=100, 
            peso_turbo=0.6,
            verbose=False
        )
        
        # 3. Filtro de Segurança (Isolation Forest se disponível)
        # Se tivéssemos o modelo treinado, filtraríamos aqui os jogos 'anômalos'
        
        # 4. Selecionar os top N finais
        jogos_finais = jogos[:n_jogos]
        
        # Salvar
        with open(JOBS_PATH, "w") as f:
            json.dump(jogos_finais, f)
            
        # Atualizar status
        self._update_status({"ultimo_gerado": datetime.now().isoformat()})
        
        return jogos_finais

    def _update_status(self, data):
        current = {}
        if STATUS_PATH.exists():
            current = json.loads(STATUS_PATH.read_text())
        current.update(data)
        with open(STATUS_PATH, "w") as f:
            json.dump(current, f)

intelligence_hub = SuperIntelligence()

import os
from pathlib import Path

# Caminhos base
BASE_DIR = Path("c:/Users/nome_do_usuario/Desktop/vitoria-loto")
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
ANALYSIS_DIR = BASE_DIR / "analises"

# Arquivos de dados
DB_PATH = DATA_DIR / "lotofacil.db"
JOBS_PATH = DATA_DIR / "ultimos_jogos.json"
STATUS_PATH = DATA_DIR / "auto_status.json"
MEMORIA_PATH = DATA_DIR / "memoria.json"

# Configurações do modelo
ENSEMBLE_CONF = {
    "n_estimators": 500,
    "max_depth": 10
}

LSTM_CONF = {
    "epochs": 100,
    "batch_size": 32,
    "lookback": 15
}

# Configurações de API e Email
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender": os.getenv("LOTO_EMAIL", "seu_email@gmail.com"),
}

# Cria diretórios se não existirem
for d in [DATA_DIR, MODELS_DIR, ANALYSIS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

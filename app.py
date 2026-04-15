from flask import Flask, render_template, jsonify, request
import sqlite3, json, logging, sys
from pathlib import Path
from datetime import datetime

# Adiciona o diretório src ao path para importar as configurações e módulos
sys.path.append(str(Path(__file__).parent))
from src.config import BASE_DIR, DB_PATH, JOBS_PATH, STATUS_PATH

# Configuração de Logging Superior
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / "logs" / "web_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("VitoriaApp")

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/status")
def api_status():
    try:
        return jsonify(json.loads(STATUS_PATH.read_text()) if STATUS_PATH.exists() else {})
    except Exception as e:
        logger.error(f"Erro ao ler status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/jogos")
def api_jogos():
    try:
        return jsonify(json.loads(JOBS_PATH.read_text()) if JOBS_PATH.exists() else [])
    except Exception as e:
        logger.error(f"Erro ao ler jogos: {e}")
        return jsonify([]), 500

@app.route("/api/sorteios")
def api_sorteios():
    try:
        conn = get_db()
        rows = conn.execute("SELECT * FROM sorteios ORDER BY concurso DESC LIMIT 30").fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        logger.error(f"Erro ao buscar sorteios: {e}")
        return jsonify([])

@app.route("/api/frequencia")
def api_frequencia():
    try:
        limit = request.args.get('limit', 100, type=int)
        conn = get_db()
        rows = conn.execute(f"SELECT * FROM sorteios ORDER BY concurso DESC LIMIT {limit}").fetchall()
        conn.close()
        
        freq = {i: 0 for i in range(1, 26)}
        for row in rows:
            # Colunas n01 até n15 (ou conforme estrutura detectada)
            for k, v in dict(row).items():
                if k.startswith('n') and v and str(v).isdigit():
                    n = int(v)
                    if 1 <= n <= 25:
                        freq[n] += 1
        return jsonify(freq)
    except Exception as e:
        logger.error(f"Erro calculando frequencia: {e}")
        return jsonify({})

@app.route("/api/ultimo_sorteio")
def api_ultimo_sorteio():
    try:
        conn = get_db()
        row = conn.execute("SELECT * FROM sorteios ORDER BY concurso DESC LIMIT 1").fetchone()
        conn.close()
        return jsonify(dict(row) if row else {})
    except Exception as e:
        logger.error(f"Erro em ultimo_sorteio: {e}")
        return jsonify({})

@app.route("/api/saldo")
def api_saldo():
    try:
        conn = get_db()
        query = """
            SELECT 
                COUNT(*) as total_jogos, 
                SUM(custo) as total_gasto, 
                SUM(premio) as total_ganho, 
                SUM(premio)-SUM(custo) as saldo_total, 
                MAX(acertos) as max_acertos 
            FROM memoria_jogos
        """
        row = conn.execute(query).fetchone()
        conn.close()
        return jsonify(dict(row) if row else {})
    except Exception as e:
        logger.error(f"Erro ao calcular saldo: {e}")
        return jsonify({})

@app.route("/api/elite_master")
def api_elite_master():
    try:
        from src.data.database import carregar_sorteios
        from src.analysis.stats import calcular_stats_completos_reis
        
        df = carregar_sorteios()
        halls = {
            "17": json.loads((BASE_DIR/"data"/"hall_of_fame.json").read_text(encoding="utf-8")) if (BASE_DIR/"data"/"hall_of_fame.json").exists() else {},
            "18": json.loads((BASE_DIR/"data"/"hall_of_fame_18.json").read_text(encoding="utf-8")) if (BASE_DIR/"data"/"hall_of_fame_18.json").exists() else {},
            "19": json.loads((BASE_DIR/"data"/"hall_of_fame_19.json").read_text(encoding="utf-8")) if (BASE_DIR/"data"/"hall_of_fame_19.json").exists() else {},
            "20": json.loads((BASE_DIR/"data"/"hall_of_fame_20.json").read_text(encoding="utf-8")) if (BASE_DIR/"data"/"hall_of_fame_20.json").exists() else {}
        }
        
        return jsonify(calcular_stats_completos_reis(df, halls))
    except Exception as e:
        logger.error(f"Erro na API Elite Master: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/mapa_calor_pontos")
def api_mapa_calor_pontos():
    try:
        from src.data.database import carregar_sorteios
        from src.analysis.stats import calcular_mapa_calor_pontos_pro
        
        df = carregar_sorteios()
        halls = {
            "17": json.loads((BASE_DIR/"data"/"hall_of_fame.json").read_text(encoding="utf-8")) if (BASE_DIR/"data"/"hall_of_fame.json").exists() else {},
            "18": json.loads((BASE_DIR/"data"/"hall_of_fame_18.json").read_text(encoding="utf-8")) if (BASE_DIR/"data"/"hall_of_fame_18.json").exists() else {},
            "19": json.loads((BASE_DIR/"data"/"hall_of_fame_19.json").read_text(encoding="utf-8")) if (BASE_DIR/"data"/"hall_of_fame_19.json").exists() else {},
            "20": json.loads((BASE_DIR/"data"/"hall_of_fame_20.json").read_text(encoding="utf-8")) if (BASE_DIR/"data"/"hall_of_fame_20.json").exists() else {}
        }
        
        return jsonify(calcular_mapa_calor_pontos_pro(df, halls))
    except Exception as e:
        logger.error(f"Erro na API Mapa Calor Pontos: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/hall_of_fame")
def api_hall_of_fame():
    try:
        path17 = BASE_DIR / "data" / "hall_of_fame.json"
        path18 = BASE_DIR / "data" / "hall_of_fame_18.json"
        path19 = BASE_DIR / "data" / "hall_of_fame_19.json"
        path20 = BASE_DIR / "data" / "hall_of_fame_20.json"
        
        result = {
            "r17": json.loads(path17.read_text(encoding="utf-8")) if path17.exists() else {},
            "r18": json.loads(path18.read_text(encoding="utf-8")) if path18.exists() else {},
            "r19": json.loads(path19.read_text(encoding="utf-8")) if path19.exists() else {},
            "r20": json.loads(path20.read_text(encoding="utf-8")) if path20.exists() else {}
        }
        return jsonify(result)
    except Exception as e:
        logger.error(f"Erro ao ler Hall of Fame: {e}")
        return jsonify({"error": str(e)}), 500

# ── OPERAÇÕES DE MESA (ORCHESTRATION) ──────────────────────────────────

@app.route("/api/atualizar_dados", methods=["POST"])
def api_atualizar_dados():
    logger.info("Iniciando atualização de dados via Interface...")
    try:
        from src.data.database import init_db
        from src.data.scraper import atualizar_dados
        init_db()
        n = atualizar_dados(verbose=False)
        msg = f"Sucesso! {n} novos sorteios sincronizados." if n > 0 else "Base de dados já está em dia."
        return jsonify({"ok": True, "msg": msg})
    except Exception as e:
        logger.error(f"Falha na atualização: {e}")
        return jsonify({"ok": False, "msg": f"Erro crítico: {str(e)}"})

@app.route("/api/gerar_jogos", methods=["POST"])
def api_gerar_jogos():
    logger.info("Solicitação de geração de jogos inteligentes recebida.")
    try:
        from src.data.database import init_db, carregar_sorteios
        from src.models.trainer import Trainer
        from src.analysis.turbo import carregar_ranking_do_csv
        
        init_db()
        df = carregar_sorteios()
        trainer = Trainer()
        trainer.carregar_modelos()
        
        ranking = carregar_ranking_do_csv(df)
        trainer._ultimo_ranking_preditivo = ranking
        
        # Super Combo com IA + Algoritmo Genético + Turbo
        logger.info("Processando Ensembles e Redes Neurais...")
        jogos = trainer.gerar_jogos_turbo_super_combo(n_jogos=10, top_n=100, peso_turbo=0.6)
        
        with open(JOBS_PATH, "w") as f:
            json.dump(jogos, f)
            
        logger.info(f"Gerados {len(jogos)} jogos de alta fidelidade.")
        return jsonify({"ok": True, "msg": f"Módulo IA gerou {len(jogos)} jogos!", "jogos": jogos})
    except Exception as e:
        logger.exception("Erro na engine de geração de jogos")
        return jsonify({"ok": False, "msg": f"Erro na IA: {str(e)}"})

@app.route("/api/enviar_email", methods=["POST"])
def api_enviar_email():
    try:
        from src.data.database import carregar_sorteios
        from src.analysis.notificador import alerta_jogo_do_dia
        from src.analysis.turbo import carregar_ranking_do_csv
        
        df = carregar_sorteios()
        ranking = carregar_ranking_do_csv(df)
        if not ranking:
            return jsonify({"ok": False, "msg": "Ranking não encontrado. Gere o Índice Preditivo primeiro."})
            
        alerta_jogo_do_dia(ranking)
        return jsonify({"ok": True, "msg": "Relatório enviado ao seu email!"})
    except Exception as e:
        logger.error(f"Erro no módulo de notificação: {e}")
        return jsonify({"ok": False, "msg": str(e)})

@app.route("/api/conferir", methods=["POST"])
def api_conferir():
    try:
        from src.analysis.memoria import conferir_resultado, historico_completo, PREMIOS
        from src.data.scraper import buscar_concurso, _descobrir_ultimo_concurso, parse_concurso
        
        df_mem = historico_completo()
        pendentes = df_mem[df_mem["conferido"] == 0]
        if pendentes.empty:
            return jsonify({"ok": True, "msg": "Nenhum jogo pendente."})
            
        concluidos = 0
        for _, jogo in pendentes.iterrows():
            conc = int(jogo["concurso"]) if jogo["concurso"] else _descobrir_ultimo_concurso()
            res = buscar_concurso(conc)
            if res:
                p = parse_concurso(res)
                if p:
                    _, _, dezenas_oficiais = p
                    aposta = [int(n) for n in str(jogo["dezenas"]).split("-")]
                    acertos = len(set(aposta) & set(dezenas_oficiais))
                    conferir_resultado(int(jogo["id"]), acertos)
                    concluidos += 1
                    
        return jsonify({"ok": True, "msg": f"{concluidos} jogos conferidos automaticamente!"})
    except Exception as e:
        logger.error(f"Erro na conferencia automatica: {e}")
        return jsonify({"ok": False, "msg": str(e)})

if __name__ == "__main__":
    logger.info("Lançando Servidor Vitoria-Loto em http://0.0.0.0:5000")
    app.run(debug=False, host="0.0.0.0", port=5000)

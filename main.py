"""
LOTOFÁCIL PRO — Super Analyzer v3.0
Ponto de entrada principal.
"""
import sys
import json
from pathlib import Path
from colorama import Fore, Back, Style, init

init(autoreset=True)

from src.config import JOBS_PATH

from src.data.database import init_db, carregar_sorteios, ultimo_concurso
from src.data.scraper import atualizar_dados, buscar_historico_completo
from src.data.loader import carregar_csv, carregar_excel
from src.analysis.stats import (
    conferir_jogos, conferir_jogo_manual,
    frequencia_geral, analise_atraso, parceiros_numero,
    padroes_dia_semana, pares_frequentes, trios_frequentes,
    analise_sequencias, repeticao_anterior, distribuicao_quadrante,
    exibir_jogos, radar_atraso_reis, listar_intervalos_reis, exibir_mapa_calor_reis, 
    exibir_mapa_calor_todos_reis, exibir_radar_unificado_reis,
    exibir_ciclo_unificado, exibir_resumo_ciclos_completo,
    exibir_resumo_ciclos_unificado
)
from src.analysis.auditor_supremo import rodar_auditoria_suprema
from src.analysis.turbo import (
    rodar_score_master, rodar_indice_preditivo, gerar_jogos_15_do_preditivo,
    gerar_jogos_cacada_ciclo, mostrar_ultimo_concurso, exibir_ranking_csv,
    carregar_ranking_do_csv, carregar_ranking_csv
)
from src.analysis.ia_analista import exibir_analise_ia
from src.analysis.memoria import registrar_jogo_interativo, conferir_resultado_interativo, exibir_memoria, init_memoria
from src.analysis.aprendizado import exibir_aprendizado
from src.analysis.carteira import exibir_carteira
from src.analysis.notificador import configurar_email_interativo, alerta_jogo_do_dia, alerta_saldo_semanal
from src.models.trainer import Trainer
from src.ui.menu import (
    limpar, menu_principal, pausar, pedir_numero, pedir_string, cabecalho
)

def exibir_hall_fama(dados, label, df=None):
    """Exibe o visual elegante do Hall da Fama para qualquer elite com status de ciclo."""
    from src.analysis.stats import _extrair_lista_sorteios
    print(f"\n{Fore.CYAN}╔{'═'*62}╗")
    print(f"║      🏆 HALL DA FAMA {label:7}: RECORDISTAS DE ELITE         ║")
    print(f"╚{'═'*62}╝{Style.RESET_ALL}\n")
    
    lista_sorteios = _extrair_lista_sorteios(df) if df is not None else []
    
    for k in ["15", "14", "13", "12", "11"]:
        if k in dados:
            r = dados[k]
            dezenas_rei = set(r["dezenas"])
            
            # Calcular Ciclo se tiver DF
            faltantes = set()
            if lista_sorteios:
                vistos = set()
                for s in lista_sorteios:
                    hits = s & dezenas_rei
                    for h in hits:
                        if vistos == dezenas_rei: vistos = set()
                        vistos.add(h)
                faltantes = dezenas_rei - vistos

            # Formatar dezenas
            dz_formatted = []
            for d in sorted(list(dezenas_rei)):
                if d in faltantes:
                    dz_formatted.append(f"{Back.RED}{Fore.WHITE}{d:02d}{Style.RESET_ALL}")
                else:
                    dz_formatted.append(f"{Fore.GREEN}{d:02d}{Style.RESET_ALL}")
            dz_str = " ".join(dz_formatted)

            print(f"  {Fore.YELLOW}👑 {r['titulo']} {Style.RESET_ALL}")
            print(f"  └─ {dz_str}")
            print(f"    {Fore.WHITE}📊 {r['stats']}{Style.RESET_ALL}")
            print(f"    {Fore.CYAN}{'─'*53}{Style.RESET_ALL}")
    
    if lista_sorteios:
        print(f"\n  {Back.RED}  {Style.RESET_ALL} = Pendente no Ciclo | {Fore.GREEN}00{Style.RESET_ALL} = Já saiu no Ciclo")


def inicializar():
    """Inicializa banco e carrega modelos na memória."""
    init_db()
    print(f"\n{Fore.CYAN}  Inicializando sistema...{Style.RESET_ALL}")

    total = ultimo_concurso()
    if total == 0:
        print(f"  {Fore.YELLOW}⚠️  Banco vazio!{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}  Use opção 11 para importar CSV/Excel local{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}  Use opção 10 para baixar da API da Caixa{Style.RESET_ALL}")
    else:
        print(f"  {Fore.GREEN}✅ {total} sorteios no banco.{Style.RESET_ALL}")


def main():
    limpar()
    cabecalho()
    inicializar()

    trainer = Trainer()
    status = trainer.carregar_modelos()

    while True:
        limpar()
        opcao = menu_principal()

        df = carregar_sorteios()
        if df.empty and opcao not in ("10", "11", "0"):
            print(f"  {Fore.RED}❌ Sem dados! Use a opção 10 ou 11 primeiro.{Style.RESET_ALL}")
            pausar()
            continue

        # ── ANÁLISES ──────────────────────────────────
        if opcao == "1":
            frequencia_geral(df)

        elif opcao == "2":
            analise_atraso(df)

        elif opcao == "3":
            num = pedir_numero("  Qual número? (1-25): ", 1, 25)
            parceiros_numero(df, num)

        elif opcao == "4":
            padroes_dia_semana(df)

        elif opcao == "5":
            top = pedir_numero("  Quantos pares? (10-50): ", 10, 50)
            pares_frequentes(df, top)

        elif opcao == "6":
            top = pedir_numero("  Quantos trios? (5-30): ", 5, 30)
            trios_frequentes(df, top)

        elif opcao == "7":
            analise_sequencias(df)

        elif opcao == "8":
            repeticao_anterior(df)

        elif opcao == "9":
            distribuicao_quadrante(df)

        elif opcao == "46":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                exibir_hall_fama(dados, "17 DZ", df=df)
            pausar()

        elif opcao == "47":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                
                lista_reis = []
                titulos = []
                for k in ["15", "14", "13", "12", "11"]:
                    if k in dados:
                        lista_reis.append(dados[k]["dezenas"])
                        titulos.append(dados[k]["titulo"])
                
                if not lista_reis:
                    print(f"  {Fore.RED}❌ Nenhum Rei encontrado no arquivo!{Style.RESET_ALL}")
                else:
                    n = pedir_numero("  Conferir contra quantos sorteios? (10-100): ", 10, 100)
                    print(f"\n{Fore.CYAN}  📊 ANALISANDO OS {len(lista_reis)} REIS DE 17...{Style.RESET_ALL}")
                    conferir_jogos(df, lista_reis, ultimos_n=n)
                    print(f"\n  {Fore.YELLOW}Nota: J01={titulos[0]}, J02={titulos[1]}, etc.{Style.RESET_ALL}")
            pausar()

        elif opcao == "48":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                radar_atraso_reis(df, dados)
                exibir_mapa_calor_reis(df, dados, ultimos_n=30)
            pausar()

        elif opcao == "49":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                listar_intervalos_reis(df, dados)
                exibir_mapa_calor_reis(df, dados, ultimos_n=30)
            pausar()

        elif opcao == "50":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_18.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes de 18 não encontrado! Rodar Hunter primeiro.{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                exibir_hall_fama(dados, "18 DZ", df=df)
            pausar()

        elif opcao == "51":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_18.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes de 18 não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                
                lista_reis = []
                titulos = []
                for k in ["15", "14", "13", "12", "11"]:
                    if k in dados:
                        lista_reis.append(dados[k]["dezenas"])
                        titulos.append(dados[k]["titulo"])
                
                if not lista_reis:
                    print(f"  {Fore.RED}❌ Nenhum Rei 18 encontrado!{Style.RESET_ALL}")
                else:
                    n = pedir_numero("  Conferir contra quantos sorteios? (10-100): ", 10, 100)
                    print(f"\n{Fore.CYAN}  📊 ANALISANDO OS {len(lista_reis)} REIS DE 18...{Style.RESET_ALL}")
                    conferir_jogos(df, lista_reis, ultimos_n=n)
                    print(f"\n  {Fore.YELLOW}Nota: J01={titulos[0]}, J02={titulos[1]}, etc.{Style.RESET_ALL}")
            pausar()

        elif opcao == "52":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_18.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes de 18 não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                radar_atraso_reis(df, dados)
                exibir_mapa_calor_reis(df, dados, ultimos_n=30)
            pausar()

        elif opcao == "53":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_18.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes de 18 não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                listar_intervalos_reis(df, dados)
                exibir_mapa_calor_reis(df, dados, ultimos_n=30)
            pausar()

        elif opcao == "54":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_18.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes de 18 não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                
                # Exibir todos os ciclos de 18
                exibir_resumo_ciclos_completo(df, dados, label="18 DZ")
            pausar()

        elif opcao == "56":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes de 17 não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                
                # Exibir todos os ciclos de 17
                exibir_resumo_ciclos_completo(df, dados, label="17 DZ")
            pausar()

        elif opcao == "55":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_18.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes de 18 não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                
                if "12" in dados:
                    rei_12 = dados["12"]["dezenas"]
                    jogos = gerar_jogos_cacada_ciclo(df, rei_12, n_jogos=6)
                    # Registrar na memória para o dashboard
                    from src.analysis.memoria import registrar_jogos_memoria
                    registrar_jogos_memoria(jogos)
                else:
                    print(f"  {Fore.RED}❌ Rei 12 não encontrado no arquivo.{Style.RESET_ALL}")
            pausar()

        elif opcao == "57":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes de 17 não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                
                # Para 17 DZ, vamos caçar o ciclo do REI 15 (o recordista clássico)
                if "15" in dados:
                    rei_15 = dados["15"]["dezenas"]
                    print(f"\n{Fore.YELLOW}  Iniciando Caçada de Ciclo para o REI 15 (17 DZ)...{Style.RESET_ALL}")
                    jogos = gerar_jogos_cacada_ciclo(df, rei_15, n_jogos=10)
                    from src.analysis.memoria import registrar_jogos_memoria
                    registrar_jogos_memoria(jogos)
                    print(f"\n  {Fore.GREEN}✅ 10 jogos gerados e registrados na memória!{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.RED}❌ Rei 15 não encontrado no arquivo.{Style.RESET_ALL}")
            pausar()

        elif opcao == "61":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_19.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f: dados = json.load(f)
                exibir_hall_fama(dados, "19 DZ", df=df)
            else:
                print(f"  {Fore.RED}❌ Arquivo de 19 DZ não encontrado.{Style.RESET_ALL}")
            pausar()

        elif opcao == "62":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_19.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f: dados = json.load(f)
                lista_reis = []
                titulos = []
                for k in ["15", "14", "13", "12", "11"]:
                    if k in dados:
                        lista_reis.append(dados[k]["dezenas"])
                        titulos.append(dados[k]["titulo"])

                n = pedir_numero("  Conferir contra quantos sorteios? (10-100): ", 10, 100)
                print(f"\n{Fore.CYAN}  📊 ANALISANDO OS {len(lista_reis)} REIS DE 19...{Style.RESET_ALL}")
                conferir_jogos(df, lista_reis, ultimos_n=n)
                if titulos:
                    labels = ", ".join(f"J{i+1:02d}={t}" for i, t in enumerate(titulos))
                    print(f"\n  {Fore.YELLOW}Nota: {labels}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.RED}❌ Arquivo de 19 DZ não encontrado.{Style.RESET_ALL}")
            pausar()

        elif opcao == "63":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_19.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f: dados = json.load(f)
                radar_atraso_reis(df, dados)
                exibir_mapa_calor_reis(df, dados, ultimos_n=30)
            else:
                print(f"  {Fore.RED}❌ Arquivo de 19 DZ não encontrado.{Style.RESET_ALL}")
            pausar()

        elif opcao == "64":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_19.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f: dados = json.load(f)
                listar_intervalos_reis(df, dados)
                exibir_mapa_calor_reis(df, dados, ultimos_n=30)
            else:
                print(f"  {Fore.RED}❌ Arquivo de 19 DZ não encontrado.{Style.RESET_ALL}")
            pausar()

        elif opcao == "65":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_19.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes de 19 não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                
                if "15" in dados:
                    rei_15 = dados["15"]["dezenas"]
                    print(f"\n{Fore.YELLOW}  Iniciando Caçada de Ciclo para o REI 15 (19 DZ)...{Style.RESET_ALL}")
                    jogos = gerar_jogos_cacada_ciclo(df, rei_15, n_jogos=10)
                    from src.analysis.memoria import registrar_jogos_memoria
                    registrar_jogos_memoria(jogos)
                    print(f"\n  {Fore.GREEN}✅ 10 jogos gerados e registrados na memória!{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.RED}❌ Rei 15 (19 DZ) não encontrado no arquivo.{Style.RESET_ALL}")
            pausar()

        elif opcao == "66":

            bp = Path(__file__).parent
            p = bp / "data" / "hall_of_fame_19.json"
            if p.exists():
                with open(p, "r", encoding="utf-8") as f: d = json.load(f)
                exibir_resumo_ciclos_completo(df, d, label="19 DZ")
            else:
                print(f"  {Fore.RED}❌ Arquivo de 19 DZ não encontrado.{Style.RESET_ALL}")
            pausar()

        elif opcao == "71":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_20.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f: dados = json.load(f)
                exibir_hall_fama(dados, "20 DZ", df=df)
            else:
                print(f"  {Fore.RED}❌ Arquivo de 20 DZ não encontrado.{Style.RESET_ALL}")
            pausar()

        elif opcao == "72":

            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_20.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f: dados = json.load(f)
                lista_reis = []
                titulos = []
                for k in ["15", "14", "13", "12", "11"]:
                    if k in dados:
                        lista_reis.append(dados[k]["dezenas"])
                        titulos.append(dados[k]["titulo"])

                n = pedir_numero("  Conferir contra quantos sorteios? (10-100): ", 10, 100)
                print(f"\n{Fore.CYAN}  📊 ANALISANDO OS {len(lista_reis)} REIS DE 20...{Style.RESET_ALL}")
                conferir_jogos(df, lista_reis, ultimos_n=n)
                if titulos:
                    labels = ", ".join(f"J{i+1:02d}={t}" for i, t in enumerate(titulos))
                    print(f"\n  {Fore.YELLOW}Nota: {labels}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.RED}❌ Arquivo de 20 DZ não encontrado.{Style.RESET_ALL}")
            pausar()

        elif opcao == "73":
            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_20.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f: dados = json.load(f)
                radar_atraso_reis(df, dados)
                exibir_mapa_calor_reis(df, dados, ultimos_n=30)
            else:
                print(f"  {Fore.RED}❌ Arquivo de 20 DZ não encontrado.{Style.RESET_ALL}")
            pausar()

        elif opcao == "74":
            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_20.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f: dados = json.load(f)
                listar_intervalos_reis(df, dados)
                exibir_mapa_calor_reis(df, dados, ultimos_n=30)
            else:
                print(f"  {Fore.RED}❌ Arquivo de 20 DZ não encontrado.{Style.RESET_ALL}")
            pausar()

        elif opcao == "75":
            base_dir = Path(__file__).parent
            path = base_dir / "data" / "hall_of_fame_20.json"
            if not path.exists():
                print(f"  {Fore.RED}❌ Arquivo recordes de 20 não encontrado!{Style.RESET_ALL}")
            else:
                with open(path, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                
                if "15" in dados:
                    rei_15 = dados["15"]["dezenas"]
                    print(f"\n{Fore.YELLOW}  Iniciando Caçada de Ciclo para o REI 15 (20 DZ)...{Style.RESET_ALL}")
                    jogos = gerar_jogos_cacada_ciclo(df, rei_15, n_jogos=10)
                    from src.analysis.memoria import registrar_jogos_memoria
                    registrar_jogos_memoria(jogos)
                    print(f"\n  {Fore.GREEN}✅ 10 jogos gerados e registrados na memória!{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.RED}❌ Rei 15 (20 DZ) não encontrado no arquivo.{Style.RESET_ALL}")
            pausar()

        elif opcao == "76":
            bp = Path(__file__).parent
            p = bp / "data" / "hall_of_fame_20.json"
            if p.exists():
                with open(p, "r", encoding="utf-8") as f: d = json.load(f)
                exibir_resumo_ciclos_completo(df, d, label="20 DZ")
            else:
                print(f"  {Fore.RED}❌ Arquivo de 20 DZ não encontrado.{Style.RESET_ALL}")
            pausar()

        elif opcao == "80":
            from src.analysis.stats import exibir_mapa_calor_todos_reis
            halls = {}
            for elite, arq in {"17": "hall_of_fame.json", "18": "hall_of_fame_18.json", "19": "hall_of_fame_19.json", "20": "hall_of_fame_20.json"}.items():
                p = Path(__file__).parent / "data" / arq
                if p.exists(): halls[elite] = json.loads(p.read_text(encoding="utf-8"))
            if halls: exibir_mapa_calor_todos_reis(df, halls)
            else: print(f"  {Fore.RED}❌ Nenhum dado de Hall of Fame encontrado.{Style.RESET_ALL}")
            pausar()

        elif opcao == "86":
            from src.analysis.stats import exibir_mapa_calor_pontos_reis
            halls = {}
            for elite, arq in {"17": "hall_of_fame.json", "18": "hall_of_fame_18.json", "19": "hall_of_fame_19.json", "20": "hall_of_fame_20.json"}.items():
                p = Path(__file__).parent / "data" / arq
                if p.exists(): halls[elite] = json.loads(p.read_text(encoding="utf-8"))
            if halls: exibir_mapa_calor_pontos_reis(df, halls)
            else: print(f"  {Fore.RED}❌ Nenhum dado de Hall of Fame encontrado.{Style.RESET_ALL}")
            pausar()

        elif opcao == "0":
            print(f"\n  {Fore.CYAN}Até logo! Boa sorte! 🍀{Style.RESET_ALL}")
            break

        elif opcao == "10":
            print(f"\n  {Fore.CYAN}Atualizando dados...{Style.RESET_ALL}")
            n = atualizar_dados(verbose=True)
            print(f"  {Fore.GREEN}✅ {n} novos sorteios.{Style.RESET_ALL}" if n > 0
                  else f"  {Fore.YELLOW}Dados já atualizados.{Style.RESET_ALL}")

        elif opcao == "60":

            rodar_auditoria_suprema(df, Path(__file__).parent)
            pausar()



        elif opcao == "81":
            base_dir = Path(__file__).parent
            dados_halls = {}
            mapa_arquivos = {
                "17": "hall_of_fame.json",
                "18": "hall_of_fame_18.json",
                "19": "hall_of_fame_19.json",
                "20": "hall_of_fame_20.json"
            }
            for elite, arq in mapa_arquivos.items():
                p = base_dir / "data" / arq
                if p.exists():
                    with open(p, "r", encoding="utf-8") as f:
                        dados_halls[elite] = json.load(f)
            
            if not dados_halls:
                print(f"  {Fore.RED}❌ Nenhum arquivo de Hall da Fama encontrado!{Style.RESET_ALL}")
            else:
                exibir_radar_unificado_reis(df, dados_halls)
            pausar()

        elif opcao == "82":
            base_dir = Path(__file__).parent
            dados_halls = {}
            mapa_arquivos = {
                "17": "hall_of_fame.json",
                "18": "hall_of_fame_18.json",
                "19": "hall_of_fame_19.json",
                "20": "hall_of_fame_20.json"
            }
            for elite, arq in mapa_arquivos.items():
                p = base_dir / "data" / arq
                if p.exists():
                    with open(p, "r", encoding="utf-8") as f:
                        dados_halls[elite] = json.load(f)
            
            if not dados_halls:
                print(f"  {Fore.RED}❌ Nenhum arquivo de Hall da Fama encontrado!{Style.RESET_ALL}")
            else:
                exibir_resumo_ciclos_unificado(df, dados_halls)
            pausar()

        elif opcao == "11":
            caminho = pedir_string("  Caminho do arquivo (CSV ou Excel): ")
            if caminho.endswith(".csv"):
                carregar_csv(caminho)
            elif caminho.endswith((".xlsx", ".xls")):
                carregar_excel(caminho)
            else:
                print(f"  {Fore.RED}Formato não suportado. Use .csv, .xlsx ou .xls{Style.RESET_ALL}")

        elif opcao == "12":
            ult = ultimo_concurso()
            total = len(df)
            print(f"\n  {Fore.CYAN}Banco de dados:{Style.RESET_ALL}")
            print(f"  Total de sorteios: {Fore.GREEN}{total}{Style.RESET_ALL}")
            print(f"  Último concurso:   {Fore.GREEN}{ult}{Style.RESET_ALL}")
            if not df.empty:
                print(f"  Primeiro concurso: {Fore.GREEN}{df['concurso'].min()}{Style.RESET_ALL}")
                print(f"  Última data:       {Fore.GREEN}{df['data'].iloc[-1]}{Style.RESET_ALL}")

        # ── ML ────────────────────────────────────────
        elif opcao == "13":
            print(f"\n  {Fore.CYAN}Treinando Ensemble...{Style.RESET_ALL}")
            trainer.treinar_ensemble()

        elif opcao == "14":
            print(f"\n  {Fore.CYAN}Treinando LSTM...{Style.RESET_ALL}")
            trainer.treinar_lstm()

        elif opcao == "15":
            trainer.treinar_tudo()

        elif opcao == "16":
            if not trainer.ensemble.trained:
                print(f"  {Fore.RED}❌ Treine o Ensemble primeiro (opção 13 ou 15).{Style.RESET_ALL}")
            else:
                n = pedir_numero("  Quantos jogos? (1-20): ", 1, 20)
                jogos = trainer.gerar_jogos_ensemble(n)
                trainer._ultimos_jogos = jogos
                exibir_jogos(jogos, "JOGOS — ENSEMBLE")
                with open(JOBS_PATH, "w") as _f:
                    json.dump(jogos, _f)
                print(f"  {Fore.GREEN}💾 Jogos salvos!{Style.RESET_ALL}")

        elif opcao == "17":
            if not trainer.lstm.trained:
                print(f"  {Fore.RED}❌ Treine a LSTM primeiro (opção 14 ou 15).{Style.RESET_ALL}")
            else:
                n = pedir_numero("  Quantos jogos? (1-20): ", 1, 20)
                jogos = trainer.gerar_jogos_lstm(n)
                trainer._ultimos_jogos = jogos
                exibir_jogos(jogos, "JOGOS — LSTM")
                with open(JOBS_PATH, "w") as _f:
                    json.dump(jogos, _f)
                print(f"  {Fore.GREEN}💾 Jogos salvos!{Style.RESET_ALL}")

        elif opcao == "18":
            n = pedir_numero("  Quantos jogos? (1-20): ", 1, 20)
            jogos = trainer.gerar_jogos_genetico(n)
            trainer._ultimos_jogos = jogos
            exibir_jogos(jogos, "JOGOS — ALGORITMO GENÉTICO")
            with open(JOBS_PATH, "w") as _f:
                json.dump(jogos, _f)
            print(f"  {Fore.GREEN}💾 Jogos salvos!{Style.RESET_ALL}")

        elif opcao == "19":
            n = pedir_numero("  Quantos jogos? (1-20): ", 1, 20)
            jogos = trainer.gerar_jogos_super_combo(n)
            trainer._ultimos_jogos = jogos
            exibir_jogos(jogos, "SUPER COMBO — TODOS OS MODELOS")
            with open(JOBS_PATH, "w") as _f:
                json.dump(jogos, _f)
            print(f"  {Fore.GREEN}💾 Jogos salvos!{Style.RESET_ALL}")

        # ── RELATÓRIO ─────────────────────────────────
        elif opcao == "20":
            print(f"\n{Fore.CYAN}  Gerando análise completa...{Style.RESET_ALL}")
            frequencia_geral(df)
            analise_atraso(df)
            padroes_dia_semana(df)
            pares_frequentes(df, 15)
            trios_frequentes(df, 10)
            analise_sequencias(df)
            repeticao_anterior(df)
            distribuicao_quadrante(df)

        elif opcao == "21":
            tam = pedir_numero("  Tamanho da combinação (15-18): ", 15, 18)
            top = pedir_numero("  Quantos resultados salvar? (50-500): ", 50, 500)
            rodar_score_master(df, tamanho=tam, top_n=top)

        elif opcao == "22":
            tam = pedir_numero("  Tamanho da combinação (15-18): ", 15, 18)
            top = pedir_numero("  Quantos resultados salvar? (50-500): ", 50, 500)
            ranking_pred = rodar_indice_preditivo(df, tamanho=tam, top_n=top)
            trainer._ultimo_ranking_preditivo = ranking_pred

        elif opcao == "23":
            ranking = getattr(trainer, "_ultimo_ranking_preditivo", None)
            if not ranking:
                print(f"  {Fore.YELLOW}  Carregando do arquivo salvo...{Style.RESET_ALL}")
                ranking = carregar_preditivo_csv()
                if ranking:
                    trainer._ultimo_ranking_preditivo = ranking
                    print(f"  {Fore.GREEN}✅ {len(ranking)} jogos carregados do CSV!{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.RED}❌ Rode o Índice Preditivo (opção 22) primeiro!{Style.RESET_ALL}")
            if ranking:
                n = pedir_numero("  Quantos jogos de 15? (1-20): ", 1, 20)
                top = pedir_numero("  Usar quantos jogos do ranking? (5-50): ", 5, 50)
                jogos = gerar_jogos_15_do_preditivo(ranking, n_jogos=n, top_n=top)
                trainer._ultimos_jogos = jogos

        elif opcao == "24":
            if not hasattr(trainer, "_ultimos_jogos") or not trainer._ultimos_jogos:
                try:
                    with open("/mnt/c/Users/nome_do_usuario/Desktop/super-lotofacil/data/ultimos_jogos.json", "r") as _f:
                        trainer._ultimos_jogos = json.load(_f)
                    print(f"  {Fore.CYAN}📂 Jogos carregados do arquivo salvo!{Style.RESET_ALL}")
                except:
                    pass
            if not hasattr(trainer, "_ultimos_jogos") or not trainer._ultimos_jogos:
                print(f"  {Fore.YELLOW}⚠️  Gere jogos primeiro (opções 16-19 ou 23)!{Style.RESET_ALL}")
            else:
                n = pedir_numero("  Conferir contra quantos sorteios? (5-50): ", 5, 50)
                conferir_jogos(df, trainer._ultimos_jogos, ultimos_n=n)

        elif opcao == "25":
            print(f"  Digite as 15 dezenas separadas por espaço (ex: 01 02 03 ...):")
            entrada = pedir_string("  > ")
            try:
                jogo = [int(x) for x in entrada.split()]
                if not (15 <= len(jogo) <= 18):
                    print(f"  {Fore.RED}❌ Digite entre 15 e 18 números!{Style.RESET_ALL}")
                elif not all(1 <= n <= 25 for n in jogo):
                    print(f"  {Fore.RED}❌ Números devem ser entre 1 e 25!{Style.RESET_ALL}")
                else:
                    n = pedir_numero("  Conferir contra quantos sorteios? (5-50): ", 5, 50)
                    conferir_jogo_manual(df, jogo, ultimos_n=n)
            except ValueError:
                print(f"  {Fore.RED}❌ Entrada inválida!{Style.RESET_ALL}")

        elif opcao == "26":
            print(f"  {Fore.CYAN}  Carregando ranking salvo do CSV...{Style.RESET_ALL}")
            ranking = carregar_ranking_do_csv(df)
            if ranking:
                trainer._ultimo_ranking_preditivo = ranking
                top = pedir_numero("  Quantos jogos exibir? (5-50): ", 5, 50)
                exibir_ranking_csv(df, top_n=top)
                print(f"  {Fore.GREEN}✅ {len(ranking)} jogos carregados! Use opção 23 para gerar jogos.{Style.RESET_ALL}")
            else:
                print(f"  {Fore.RED}❌ Rode o Índice Preditivo (opção 22) primeiro!{Style.RESET_ALL}")

        elif opcao == "27":
            ranking = getattr(trainer, "_ultimo_ranking_preditivo", None)
            if not ranking:
                ranking = carregar_ranking_do_csv(df)
                if ranking:
                    trainer._ultimo_ranking_preditivo = ranking
            if not ranking:
                print(f"  {Fore.RED}❌ Rode o Índice Preditivo (opção 22) ou carregue (opção 26) primeiro!{Style.RESET_ALL}")
            else:
                dias = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
                from datetime import datetime
                dia_hoje = dias[datetime.now().weekday()]
                stats = {
                    "total_sorteios": len(df),
                    "repeticoes_mais_comum": 9,
                    "frequencia": [(20,62.6),(25,62.1),(10,62.1),(11,61.5),(13,60.9)],
                    "padroes_dia": {
                        "Segunda": [10,1,20,13,11],
                        "Terça": [3,25,13,24,10],
                        "Quarta": [25,10,3,20,24],
                        "Quinta": [21,11,20,12,18],
                        "Sexta": [15,14,20,19,24],
                        "Sábado": [22,20,4,11,14],
                    }
                }
                exibir_analise_ia(ranking, stats, dia_hoje)

        elif opcao == "28":
            registrar_jogo_interativo()

        elif opcao == "29":
            conferir_resultado_interativo()

        elif opcao == "30":
            n = pedir_numero("  Quantos jogos exibir? (5-500): ", 5, 500)
            exibir_memoria(n)

        elif opcao == "31":
            exibir_aprendizado()

        elif opcao == "40":
            n = pedir_numero("  Exibir quantos sorteios recentes? (5-4000): ", 5, 4000)
            import pandas as pd
            import sqlite3
            pd.options.display.max_rows = None # Forçar exibir todas as linhas
            conn = sqlite3.connect('data/lotofacil.db')
            df_hist = pd.read_sql(f'SELECT * FROM sorteios ORDER BY concurso DESC LIMIT {n}', conn)
            conn.close()
            print(f"\n{Fore.CYAN}--- HISTÓRICO OFICIAL (LOTOFÁCIL) ---{Style.RESET_ALL}")
            print(df_hist[['concurso', 'data', 'n01', 'n02', 'n03', 'n04', 'n05', 'n06', 'n07', 'n08', 'n09', 'n10', 'n11', 'n12', 'n13', 'n14', 'n15']])
            pd.options.display.max_rows = 60 # Voltar ao padrão depois
            pausar()
            pd.options.display.max_rows = None

        elif opcao == "32":
            exibir_carteira()

        elif opcao == "33":
            configurar_email_interativo()

        elif opcao == "34":
            ranking = getattr(trainer, "_ultimo_ranking_preditivo", None)
            if not ranking:
                ranking = carregar_ranking_do_csv(df)
            if not ranking:
                print(f"  {Fore.RED}❌ Carregue o ranking primeiro (opção 26)!{Style.RESET_ALL}")
            else:
                from datetime import datetime
                dias = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
                dia_hoje = dias[datetime.now().weekday()]
                alerta_jogo_do_dia(ranking, dia_hoje)

        elif opcao == "35":
            alerta_saldo_semanal()

        # ── ISOLATION FOREST ──────────────────────────
        elif opcao == "36":
            print(f"\n  {Fore.CYAN}🌲 ISOLATION FOREST{Style.RESET_ALL}")
            print(f"  1. Treinar modelo com histórico real")
            print(f"  2. Pontuar e filtrar últimos jogos gerados")
            escolha = pedir_string("  Opção: ")

            if escolha == "1":
                cols = ['n01','n02','n03','n04','n05','n06','n07','n08',
                        'n09','n10','n11','n12','n13','n14','n15']
                concursos = df[cols].values.tolist()
                from src.ml_models import LotofacilML
                ml = LotofacilML()
                sucesso = ml.treinar_isolation_forest(concursos)
                trainer._isolation_ml = ml
                if sucesso:
                    print(f"  {Fore.GREEN}✅ Treinado com {len(concursos)} sorteios reais!{Style.RESET_ALL}")

            elif escolha == "2":
                ml = getattr(trainer, "_isolation_ml", None)
                if not ml:
                    print(f"  {Fore.RED}❌ Treine primeiro (opção 36 > 1)!{Style.RESET_ALL}")
                elif not hasattr(trainer, "_ultimos_jogos") or not trainer._ultimos_jogos:
                    print(f"  {Fore.YELLOW}⚠️  Gere jogos primeiro (opções 16-19)!{Style.RESET_ALL}")
                else:
                    top_n = pedir_numero("  Quantos jogos filtrar? (1-20): ", 1, 20)
                    ranqueados = ml.filtrar_jogos_isolation(trainer._ultimos_jogos, top_n=top_n)
                    print(f"\n  {Fore.CYAN}🌲 TOP {top_n} PELO ISOLATION FOREST:{Style.RESET_ALL}")
                    for i, r in enumerate(ranqueados, 1):
                        nums = "  ".join(f"{n:02d}" for n in r['jogo'])
                        print(f"  Jogo {i}: {nums}  │  score: {r['score']:.4f}")

        # ── FECHAMENTO MATEMÁTICO ─────────────────────
        elif opcao == "85":
            ranking = getattr(trainer, "_ultimo_ranking_preditivo", None)
            if not ranking:
                ranking = carregar_ranking_do_csv(df)
                if ranking:
                    trainer._ultimo_ranking_preditivo = ranking
            from src.analysis.fechamento import rodar_fechamento_interativo
            jogos = rodar_fechamento_interativo(df, ranking)
            if jogos:
                trainer._ultimos_jogos = jogos
        elif opcao == "41":
            import webbrowser, os
            f = os.path.abspath("analises/frequencia_geral.html")
            if os.path.exists(f):
                webbrowser.open("file://" + f)
                print("  Abrindo frequencia geral no navegador...")
            else:
                print("  Arquivo nao encontrado!")
        elif opcao == "42":
            import webbrowser, os
            f = os.path.abspath("analises/padrao_dia_semana.html")
            webbrowser.open("file://" + f)
            print("  Abrindo padrao por dia no navegador...")
        elif opcao == "43":
            import webbrowser, os
            f = os.path.abspath("analises/parceiros.html")
            webbrowser.open("file://" + f)
            print("  Abrindo parceiros do 01 no navegador...")
        elif opcao == "45":
            import webbrowser, os
            from src.analysis.stats import gerar_html_repeticoes_anterior
            gerar_html_repeticoes_anterior(df)
            f = os.path.abspath("analises/repeticoes_anterior.html")
            webbrowser.open("file://" + f)
            print("  Abrindo repeticoes do anterior no navegador...")
        elif opcao == "44":
            import webbrowser, os
            f = os.path.abspath("analises/sequencias.html")
            webbrowser.open("file://" + f)
            print("  Abrindo sequencias no navegador...")
        elif opcao == "0":
            print("\n  Ate logo!")
            sys.exit(0)

        else:
            print(f"  {Fore.RED}Opção inválida.{Style.RESET_ALL}")

        pausar()


if __name__ == "__main__":
    main()

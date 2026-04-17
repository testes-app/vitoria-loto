"""
Interface de terminal para o Lotofácil Pro.
"""
import os
import sys
from colorama import Fore, Style, init

init(autoreset=True)


def limpar():
    os.system("cls" if os.name == "nt" else "clear")


def cabecalho():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════╗
║    🎯 LOTOFÁCIL PRO — SUPER ANALYZER v3.2            ║
║    ML + LSTM + Genético + Turbo Engine               ║
╚══════════════════════════════════════════════════════╝{Style.RESET_ALL}""")


def menu_principal():
    cabecalho()
    print(f"""
{Fore.YELLOW}  ── ANÁLISES ESTATÍSTICAS ──────────────────────{Style.RESET_ALL}
  1. 📊 Frequência geral de todos os números
  2. ⏳ Análise de atraso
  3. 🔍 Parceiros de um número
  4. 📅 Padrões por dia da semana
  5. 👫 Pares mais frequentes
  6. 🔺 Trios mais frequentes
  7. 📈 Análise de sequências consecutivas
  8. 🔄 Repetição do sorteio anterior
  9. 🗺️  Distribuição por quadrante

{Fore.YELLOW}  ── DADOS ───────────────────────────────────────{Style.RESET_ALL}
 10. 🌐 Atualizar dados (internet)
 11. 📁 Carregar CSV ou Excel
 12. 🗃️  Status do banco de dados
 40. 📜 Ver Histórico de Sorteios

{Fore.YELLOW}  ── MACHINE LEARNING ────────────────────────────{Style.RESET_ALL}
 13. 🤖 Treinar Ensemble (RF + XGB + LGB)
 14. 🧠 Treinar LSTM (Rede Neural)
 15. 🚀 Treinar TODOS os modelos
 16. 🎲 Gerar jogos — Ensemble
 17. 🎲 Gerar jogos — LSTM
 18. 🧬 Gerar jogos — Algoritmo Genético
 19. 🏆 Super Combo (IA + Genético + Turbo)

{Fore.YELLOW}  ── MOTOR TURBO (BITWISE) ───────────────────────{Style.RESET_ALL}
 21. ⚡ Score Master (17 dezenas)
 22. 📈 Índice Preditivo (Motor Turbo)
 23. 🔥 Jogos de 15 (Núcleo Quente)

{Fore.YELLOW}  ── MEMÓRIA E CONFERÊNCIA ───────────────────────{Style.RESET_ALL}
 24. 📄 Ver últimos jogos gerados
 25. 🎯 Conferidor manual (15-18 dezenas)
 28. 💾 Registrar jogo na memória
 29. 🌐 Conferir resultado (Automático)
 30. 🧠 Ver jogos salvos (Memória)

{Fore.MAGENTA}  ── INTELIGÊNCIA UNIFICADA — O VEREDITO ────────{Style.RESET_ALL}
 60. 🏛️ Auditor Supremo (Cérebro Unificado)
 80. 🌡️ MAPA CALOR UNIFICADO — Todos os Reis (17-20)
 81. 📡 RADAR UNIFICADO — Atraso/Jejum de Todos os Reis
 82. 🔭 MONITOR DE CICLOS UNIFICADO — Todos os Elites
 85. 📐 FECHAMENTO MATEMÁTICO (11 pts garantidos)

{Fore.YELLOW}  ── ELITE 17 — RECORDISTAS HISTÓRICOS ───────────{Style.RESET_ALL}
 46. 👑 Hall da Fama (Os Reis da Lotofácil - 17)
 47. 📊 Performance dos Reis 17 (Tabela)
 48. 📡 Radar de Atraso Semanal 17
 49. 📅 Histórico de Intervalos 17
 56. 🔄 Monitor de Ciclo Interno (Reis 17)
 57. 🏹 Caçador de Ciclo (Gerar Jogos 17)

{Fore.YELLOW}  ── ELITE 18 — OS NOVOS REIS (NOVO) ─────────────{Style.RESET_ALL}
 50. 👑 Hall da Fama 18 (Os novos Reis de 18 DZ)
 51. 📊 Performance dos Reis 18 (Tabela)
 52. 📡 Radar de Atraso Semanal 18
 53. 📅 Histórico de Intervalos 18
 54. 🔄 Monitor de Ciclo Interno (Reis 18)
 55. 🏹 Caçador de Ciclo (Gerar Jogos 18)

{Fore.YELLOW}  ── ELITE 19 — OS SUPER REIS (COMPLETO) ─────────{Style.RESET_ALL}
 61. 👑 Hall da Fama 19 (Os Reis Supremos de 19 DZ)
 62. 📊 Performance dos Reis 19 (Tabela)
 63. 📡 Radar de Atraso Semanal 19
 64. 📅 Histórico de Intervalos 19
 65. 🏹 Caçador de Ciclo (Gerar Jogos 19)
 66. 🔄 Monitor de Ciclo Interno (Reis 19)

{Fore.YELLOW}  ── ELITE 20 — OS ULTRA REIS (A FORTALEZA) ──────{Style.RESET_ALL}
 71. 👑 Hall da Fama 20 (Os Reis de 20 DZ)
 72. 📊 Performance dos Reis 20 (Tabela)
 73. 📡 Radar de Atraso Semanal 20
 74. 📅 Histórico de Intervalos 20
 75. 🏹 Caçador de Ciclo (Gerar Jogos 20)
 76. 🔄 Monitor de Ciclo Interno (Reis 20)

{Fore.YELLOW}  ── DIAGRAMAS HTML ──────────────────────────────{Style.RESET_ALL}
 41. 🌐 Frequência geral (diagrama)
 42. 📅 Padrão por dia da semana (diagrama)
 43. 👫 Parceiros de cada número (diagrama)
 44. 📈 Sequências consecutivas (diagrama)
 45. 🔄 Repetições do sorteio anterior (diagrama)

{Fore.CYAN}  ── CONFIGURAÇÕES E UTILITÁRIOS ──────────────────{Style.RESET_ALL}
 80. 🗺️ Mapa de Calor Unificado (Todos os Reis)
 86. 🔥 Mapa de Calor por Pontos (Últimos 30)
 90. 🧠 SUPER FILTRO IA SUPREMO (Auditor + Térmico)
 91. 🎲 GERAR JOGOS — SUPREMACIA IA (Top 19)
 100. 🚀 PROJETO AGI NRO 1 — O CONTROLADOR (Auto-Pilot Master)

{Fore.RED}  0.  🚪 Sair{Style.RESET_ALL}
""")
    return input(f"{Fore.GREEN}👉 Escolha uma opção: {Style.RESET_ALL}").strip()


def pausar():
    input(f"\n{Fore.YELLOW}  Pressione ENTER para continuar...{Style.RESET_ALL}")


def pedir_numero(prompt: str, minv: int, maxv: int) -> int:
    while True:
        try:
            v = int(input(prompt))
            if minv <= v <= maxv:
                return v
            print(f"  Digite um número entre {minv} e {maxv}.")
        except ValueError:
            print("  Entrada inválida.")


def pedir_string(prompt: str) -> str:
    return input(prompt).strip()
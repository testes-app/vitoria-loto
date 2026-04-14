"""
Busca dados da Lotofácil automaticamente na internet.
Fonte principal: API pública da Caixa Econômica Federal.
"""
import requests
import time
from src.data.database import inserir_sorteio, ultimo_concurso, carregar_sorteios
from colorama import Fore, Style

API_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/{}"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}


def buscar_concurso(numero: int) -> dict | None:
    """Busca um concurso específico pela API da Caixa."""
    try:
        url = API_URL.format(numero)
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"{Fore.RED}  Erro ao buscar concurso {numero}: {e}{Style.RESET_ALL}")
    return None


def parse_concurso(data: dict) -> tuple | None:
    """Extrai concurso, data e números de um resultado da API."""
    try:
        concurso = int(data["numero"])
        data_sorteio = data["dataApuracao"]
        numeros = [int(n) for n in data["listaDezenas"]]
        return concurso, data_sorteio, numeros
    except Exception:
        return None


def atualizar_dados(verbose=True) -> int:
    """
    Busca novos sorteios a partir do último salvo.
    Retorna a quantidade de novos sorteios inseridos.
    """
    ultimo = ultimo_concurso()

    if verbose:
        print(f"{Fore.CYAN}  Último concurso salvo: {ultimo}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  Buscando novos sorteios...{Style.RESET_ALL}")

    # Descobre o último concurso disponível
    ultimo_disponivel = _descobrir_ultimo_concurso()
    if ultimo_disponivel is None:
        print(f"{Fore.RED}  Não foi possível conectar à API da Caixa.{Style.RESET_ALL}")
        return 0

    if verbose:
        print(f"{Fore.CYAN}  Último disponível: {ultimo_disponivel}{Style.RESET_ALL}")

    novos = 0
    for num in range(ultimo + 1, ultimo_disponivel + 1):
        data = buscar_concurso(num)
        if data:
            parsed = parse_concurso(data)
            if parsed:
                concurso, data_s, numeros = parsed
                inserir_sorteio(concurso, data_s, numeros)
                novos += 1
                if verbose:
                    print(f"  {Fore.GREEN}✅ Concurso {concurso} ({data_s}) salvo.{Style.RESET_ALL}")
        time.sleep(0.3)  # Respeita rate limit

    if novos == 0 and verbose:
        print(f"  {Fore.YELLOW}✅ Dados já estão atualizados!{Style.RESET_ALL}")

    return novos


def _descobrir_ultimo_concurso() -> int | None:
    """Busca o concurso mais recente disponível na API (sem número = retorna último)."""
    try:
        resp = requests.get(API_URL.format(""), headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return int(data["numero"])
    except Exception:
        pass
    return None


def buscar_historico_completo(inicio: int = 1, verbose: bool = True) -> int:
    """
    Baixa TODOS os sorteios desde o concurso `inicio`.
    Use apenas na primeira vez ou para recriar o banco.
    """
    ultimo_disp = _descobrir_ultimo_concurso()
    if not ultimo_disp:
        print(f"{Fore.RED}  Sem conexão com a API.{Style.RESET_ALL}")
        return 0

    total = 0
    print(f"{Fore.CYAN}  Baixando {ultimo_disp - inicio + 1} concursos...{Style.RESET_ALL}")
    for num in range(inicio, ultimo_disp + 1):
        data = buscar_concurso(num)
        if data:
            parsed = parse_concurso(data)
            if parsed:
                inserir_sorteio(*parsed)
                total += 1
        if verbose and num % 100 == 0:
            print(f"  {Fore.GREEN}  {num}/{ultimo_disp} concursos baixados...{Style.RESET_ALL}")
        time.sleep(0.2)
    return total

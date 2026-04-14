"""
Módulo de Notificações — envia alertas por email (Gmail).
"""
import smtplib
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style

CONFIG_PATH = Path(__file__).parent.parent.parent / "config"
EMAIL_CONFIG = CONFIG_PATH / "email_config.txt"


def salvar_config_email(remetente: str, senha_app: str, destinatario: str):
    """Salva configuração de email."""
    CONFIG_PATH.mkdir(exist_ok=True)
    with open(EMAIL_CONFIG, "w") as f:
        f.write(f"{remetente}\n{senha_app}\n{destinatario}\n")
    print(f"  {Fore.GREEN}✅ Configuração de email salva!{Style.RESET_ALL}")


def carregar_config_email() -> tuple:
    """Carrega configuração de email."""
    if not EMAIL_CONFIG.exists():
        return None, None, None
    with open(EMAIL_CONFIG) as f:
        linhas = f.read().strip().split("\n")
    if len(linhas) < 3:
        return None, None, None
    return linhas[0], linhas[1], linhas[2]


def enviar_email(assunto: str, corpo: str, verbose: bool = True) -> bool:
    """Envia email via Gmail."""
    remetente, senha, destinatario = carregar_config_email()
    if not remetente:
        if verbose:
            print(f"  {Fore.RED}❌ Email não configurado! Use a opção 33.{Style.RESET_ALL}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🎯 Lotofácil Pro — {assunto}"
        msg["From"] = remetente
        msg["To"] = destinatario

        # Versão texto
        texto = MIMEText(corpo, "plain", "utf-8")
        msg.attach(texto)

        # Versão HTML bonita
        html = f"""
        <html><body style="font-family:Arial;background:#1a1a2e;color:#fff;padding:20px">
        <div style="max-width:600px;margin:0 auto;background:#16213e;border-radius:12px;padding:24px">
        <h2 style="color:#7f77dd">🎯 Lotofácil Pro</h2>
        <h3 style="color:#1d9e75">{assunto}</h3>
        <pre style="color:#c2c0b6;white-space:pre-wrap;font-family:monospace">{corpo}</pre>
        <hr style="border-color:#444">
        <p style="color:#888;font-size:12px">Enviado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div></body></html>
        """
        html_part = MIMEText(html, "html", "utf-8")
        msg.attach(html_part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(remetente, senha)
            server.sendmail(remetente, destinatario, msg.as_string())

        if verbose:
            print(f"  {Fore.GREEN}✅ Email enviado para {destinatario}!{Style.RESET_ALL}")
        return True

    except Exception as e:
        if verbose:
            print(f"  {Fore.RED}❌ Erro ao enviar email: {e}{Style.RESET_ALL}")
        return False


def alerta_jogo_do_dia(ranking: list, dia_semana: str = None):
    """Envia sugestão do jogo do dia por email."""
    if not ranking:
        return

    if dia_semana is None:
        dias = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
        dia_semana = dias[datetime.now().weekday()]

    # Pega o melhor jogo (maior PI com 12-13 quentes)
    melhor = None
    for combo, c, pi in ranking[:20]:
        a12 = c.get("atraso12", 99)
        a13 = c.get("atraso13", 99)
        a11 = c.get("atraso11", 99)
        if a12 <= 10 and a13 <= 15 and a11 <= 10:
            melhor = (combo, c, pi)
            break

    if melhor is None:
        melhor = ranking[0]

    combo, c, pi = melhor
    dz = " ".join(f"{n:02d}" for n in combo)

    corpo = f"""
🎯 JOGO DO DIA — {dia_semana.upper()}
{'='*45}

Dezenas recomendadas:
{dz}

Índice Preditivo: {pi:.4f}

Histórico de acertos:
  14pts: {c.get('atraso14',0):3d} sorteios atrás (conc.{c.get('conc14',0)})
  13pts: {c.get('atraso13',0):3d} sorteios atrás (conc.{c.get('conc13',0)})
  12pts: {c.get('atraso12',0):3d} sorteios atrás (conc.{c.get('conc12',0)})
  11pts: {c.get('atraso11',0):3d} sorteios atrás (conc.{c.get('conc11',0)})

💰 Custo: R$3,50
🎯 Meta: fechar a semana no positivo!

Boa sorte! 🍀
"""
    enviar_email(f"Jogo do dia — {dia_semana}", corpo)


def alerta_resultado(jogo_id: int, acertos: int, premio: float, saldo: float):
    """Envia resultado de um jogo por email."""
    emoji = "🏆" if acertos >= 13 else "✅" if acertos >= 11 else "📊"
    sinal = "+" if saldo >= 0 else ""

    corpo = f"""
{emoji} RESULTADO DO JOGO #{jogo_id}
{'='*45}

Acertos:  {acertos} pontos
Prêmio:   R${premio:.2f}
Saldo:    {sinal}R${saldo:.2f}

{'🎉 PARABÉNS! Acertou ' + str(acertos) + ' pontos!' if acertos >= 13 else ''}
{'✅ Bom resultado! ' if 11 <= acertos <= 12 else ''}
{'📊 Continue jogando, a estratégia funciona no longo prazo!' if acertos < 11 else ''}
"""
    enviar_email(f"Resultado: {acertos} pontos", corpo)


def alerta_saldo_semanal():
    """Envia resumo semanal por email."""
    from src.analysis.carteira import status_semana_atual
    from src.analysis.aprendizado import analisar_desempenho

    status = status_semana_atual()
    desemp = analisar_desempenho()

    saldo = status['saldo']
    sinal = "+" if saldo >= 0 else ""
    emoji = "✅" if saldo >= 0 else "📊"

    corpo = f"""
{emoji} RESUMO SEMANAL — {status['semana']}
{'='*45}

💰 FINANCEIRO
  Jogos feitos:  {status['jogos_feitos']}/6
  Gasto:         R${status['gasto']:.2f}
  Prêmios:       R${status['premio']:.2f}
  Saldo:         {sinal}R${saldo:.2f}

{'🎉 SEMANA POSITIVA! Meta atingida!' if saldo >= 0 else '📊 Semana negativa. Continue na próxima!'}

📈 ACUMULADO
  Saldo total: {'+' if (desemp or {}).get('saldo_total',0) >= 0 else ''}R${(desemp or {}).get('saldo_total', 0):.2f}
  ROI:         {(desemp or {}).get('roi', 0):+.1f}%

Boa semana! 💪
"""
    enviar_email("Resumo semanal", corpo)


def configurar_email_interativo():
    """Interface para configurar email."""
    print(f"\n{Fore.CYAN}  📧 CONFIGURAR EMAIL{Style.RESET_ALL}")
    print(f"  Você precisa de uma senha de app do Gmail.")
    print(f"  Acesse: myaccount.google.com → Segurança → Senhas de app")

    remetente = input(f"  {Fore.GREEN}Seu email Gmail: {Style.RESET_ALL}").strip()
    senha = input(f"  {Fore.GREEN}Senha de app (16 caracteres): {Style.RESET_ALL}").strip()
    destinatario = input(f"  {Fore.GREEN}Email destino (pode ser o mesmo): {Style.RESET_ALL}").strip()

    salvar_config_email(remetente, senha, destinatario)

    print(f"\n  {Fore.CYAN}Testando envio...{Style.RESET_ALL}")
    ok = enviar_email("Teste de configuração",
                      "✅ Email configurado com sucesso!\nO Lotofácil Pro vai te enviar alertas aqui.")
    if ok:
        print(f"  {Fore.GREEN}✅ Tudo funcionando!{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}❌ Verifique as credenciais e tente novamente.{Style.RESET_ALL}")

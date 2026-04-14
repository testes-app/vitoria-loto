        # ── FECHAMENTO MATEMÁTICO ─────────────────────
        elif opcao == "40":
            ranking = getattr(trainer, "_ultimo_ranking_preditivo", None)
            if not ranking:
                ranking = carregar_ranking_do_csv(df)
                if ranking:
                    trainer._ultimo_ranking_preditivo = ranking
            from src.analysis.fechamento import rodar_fechamento_interativo
            jogos = rodar_fechamento_interativo(df, ranking)
            if jogos:
                trainer._ultimos_jogos = jogos

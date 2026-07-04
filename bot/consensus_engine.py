# ── LEVI Sub-Agent Pre-Consensus Layer ─────────────────────────────────
scout_out = SCOUT.scan(sig.symbol)
atlas_out = ATLAS.analyze(sig.symbol)
lens_out = LENS.analyze(sig.symbol, sig.direction)

        metrics = {"price": sig.price, "ema20": sig.ema20, "sma50": sig.sma50,
                   "rsi14_daily": sig.rsi14, "rsi15_intraday": rsi15,
                   "bb_upper": sig.bb_upper, "bb_lower": sig.bb_lower,
                   "pct_5d": sig.pct5d, "market_state": report.state.value,
                   "local_signal": sig.direction, "confidence": sig.confidence,
                   "x_sentiment": scout_out["sentiment"],
                   "x_confidence": scout_out["confidence"],
                   "x_signals": scout_out["key_signals"],
                   "macro_regime": atlas_out["macro_regime"],
                   "macro_bias": atlas_out["trade_bias"],
                   "catalysts": atlas_out["catalysts_ahead"],
                   "setup_quality": lens_out["setup_quality"],
                   "lens_confidence": lens_out["confidence"],
                   "trace_triggered": lens_out["trace_triggered"],
                  }

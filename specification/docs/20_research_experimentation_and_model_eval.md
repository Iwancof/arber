# 20. Research, Experimentation, and Model Evaluation

## 20.1 目的

本番運用と研究実験を混ぜすぎないため、研究フレームを明示する。

## 20.2 Experiment Object

実験は次を持つ。
- experiment_id
- hypothesis
- dataset slice
- market profiles
- worker versions
- prompt versions
- policy pack version
- evaluation metrics
- result summary

## 20.3 Dataset Slices

- by market
- by sector
- by event type
- by horizon
- by volatility regime
- by source tier
- by execution mode

## 20.4 Baselines

最低でも比較する。
- no-trade
- always flat
- simple momentum continuation
- mean reversion
- earnings drift heuristic
- rule-only event interpretation

## 20.5 Metrics

- Brier
- calibration
- directional bucket accuracy
- relative return bucket quality
- downside barrier performance
- decision uplift
- no-trade precision
- paper/live drift

## 20.6 Prompt and Worker Experiments

worker or prompt の比較は、必ず snapshot を残す。
- prompt version
- schema version
- worker adapter version
- mode
- evidence bundle version

## 20.7 Rollout Strategy

- offline replay
- shadow
- limited paper
- micro-live
- wider deployment

## 20.8 Guardrails

- no experiment directly on live without feature flag
- no hidden prompt edits
- no schema-breaking worker rollout without compatibility
- no backtest-only claims without shadow/paper confirmation

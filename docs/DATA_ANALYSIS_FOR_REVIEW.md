# データ分析レポート — 設計レビュー用

**日付**: 2026-04-08
**稼働期間**: 約12時間
**LLM Provider**: Codex (GPT-5.4 xhigh) + 初期は Anthropic Opus 4.6
**ニュースソース**: Alpaca News (EN) + BOJ RSS (JA)
**Prompt Version**: v2 (設計チーム提供)

---

## 1. パイプライン処理量

| 指標 | 値 |
|------|-----|
| Documents ingested | 55 (EN: 48, JA: 6) |
| Events extracted | 148 |
| Forecasts | 75 (うち空JSON 1件 = parse failure) |
| Decisions | 75 |
| Orders | **0** |

### 変換ファネル
```
55 docs → 148 events (1 doc から複数 event) → 74 valid forecasts → 75 decisions → 0 orders
```

**⚠️ 懸念: 1 doc から平均 2.7 events** — 同じ記事が複数サイクルで処理され、同じイベントが複数回抽出されている可能性。Dedup がドキュメントレベルでは効いているが、イベントレベルの重複チェックが甘い。

---

## 2. Event Type 分布

| event_type | 件数 | avg materiality | avg novelty |
|-----------|------|----------------|-------------|
| corp_contract_win_major | **53** | 0.62 | 0.60 |
| corp_product_launch_major | 25 | 0.46 | 0.50 |
| reg_trade_restriction_or_sanction | 15 | 0.49 | 0.48 |
| reg_litigation_favorable | 13 | 0.65 | 0.70 |
| corp_operational_disruption | 10 | 0.41 | 0.46 |
| market_analyst_upgrade_material | 9 | 0.35 | 0.30 |
| market_analyst_downgrade_material | 7 | 0.59 | 0.56 |

Taxonomy compliance: **95%** (7件が非準拠 — v1時代の古いデータ)

**⚠️ 懸念: `corp_contract_win_major` が全体の 36%** — 1つの event_type に偏りすぎ。UNH の CMS Medicare ニュースが繰り返し `corp_contract_win_major` に分類されている。もう少し細かい分類（例: `corp_government_contract`, `reg_subsidy_change`）があると良いかもしれない。

---

## 3. 方向性の分布

| direction | 件数 | 割合 |
|-----------|------|------|
| positive | 113 | **76%** |
| negative | 22 | 15% |
| mixed | 10 | 7% |
| neutral | 3 | 2% |

**⚠️ 懸念: positive が 76%** — ニュースソース（Alpaca/Benzinga）が positive-biased な金融メディアである可能性。または LLM が positive に偏りやすい傾向。negative / neutral がもっと多いのが自然。

---

## 4. Materiality 分布

```
0.00-0.15 (noise)           1  
0.15-0.30 (minor)           2  █
0.30-0.45 (modest)         39  ███████████████████
0.45-0.60 (real catalyst)  48  ████████████████████████
0.60-0.75 (clear catalyst) 47  ███████████████████████
0.75-0.90 (major)           6  ███
0.90+ (systemic)            5  ██
```

**平均: 0.562**

**⚠️ 懸念: 0.30-0.75 に集中 (91%)** — noise 帯 (< 0.30) が極端に少ない。noise classifier がヘッドラインレベルでフィルタしているため、event_extract まで到達するニュースは比較的重要なものだけ。ただし materiality 0.30-0.45 が多いのは「抽出はしたが取引価値は低い」ケースが多いことを意味する。

---

## 5. Confidence 分布（最重要）

```
0.50-0.52 (noise)     30  ██████████████████████████████  (41%)
0.52-0.55 (noise+)     8  ████████
0.55-0.58 (weak)       20  ████████████████████  (27%)
0.58-0.62 (weak+)       6  ██████
0.62-0.65 (clear-)      1  █  (1.4%)
0.65-0.72 (clear)       0
0.72-0.80 (strong)      9  █████████  (12%)
0.80+ (very strong)     0
```

**平均: 0.561**

**⚠️ 重大な懸念: 二峰性分布** — confidence が 0.50-0.52 (41%) と 0.72-0.80 (12%) に分かれ、**中間帯 (0.62-0.72) がほぼ空**。clear帯で1件しかない。

これは以下を示唆する：
1. LLM が「確信なし (0.50-0.52)」か「非常に確信あり (0.72-0.80)」の二択になっている
2. 中間的な確信度（modest edge）の表現ができていない
3. Policy Engine の clear 帯 (0.62-0.72) が実質的に使われていない
4. **v2 プロンプトのキャリブレーション指示に反して、連続的なグラデーションになっていない**

---

## 6. Directional Edge (score) 分布

```
strong short (<-0.20)        0
weak short (-0.20 to -0.10)  5  █████
neutral (-0.10 to 0.05)     39  ███████████████████████████████████████  (52%)
weak long (0.05 to 0.15)     9  █████████
modest long (0.15 to 0.25)  13  █████████████
clear long (0.25 to 0.35)    1  █
strong long (0.35+)           8  ████████
```

**平均: +0.088 (long biased)**

**⚠️ 懸念: neutral に 52% が集中** — edge 分布もconfidenceと同じ二峰性パターン。neutral cluster (0.50-0.52 confidence → ほぼゼロ edge) と strong long cluster (0.72-0.80 confidence → 0.35+ edge) に分かれている。

---

## 7. Decision 分布

| action | status | 件数 |
|--------|--------|------|
| no_trade | suppressed | **73** (97%) |
| wait_manual | waiting_manual | **2** (3%) |
| long_candidate | — | **0** |
| short_candidate | — | **0** |

**⚠️ 97% が no_trade** — long_candidate が一度も出ていない。これは confidence 分布の二峰性が原因。0.72-0.80 の9件はどれも strong 帯だが、edge が threshold に達していないか、v1 時代の旧式スコア計算で判定されたもの。

---

## 8. 仮説の質

| selected_hypothesis | 件数 |
|--------------------|------|
| already_priced_mean_reversion | **30 (41%)** |
| earnings_path_repricing | 23 (31%) |
| ai_revenue_acceleration | 4 |
| dominant_market_share_premium | 3 |
| (その他 11種) | 各1件 |

**⚠️ 懸念: `already_priced` が最多** — LLM が41%のケースで「もう織り込み済み」と判断。これは v2 プロンプトの保守性が強く出ている。本当に全て織り込み済みかは事後評価（outcome）で検証する必要がある。

---

## 9. Counterargument 使用頻度

| code | 件数 |
|------|------|
| already_priced | 62 |
| low_novelty | 53 |
| weak_magnitude | 48 |
| benchmark_shared_exposure | 37 |
| headline_without_primary_source | 32 |
| time_horizon_mismatch | 10 |
| insufficient_evidence | 6 |

良い点: 多様な counterargument が使われている。
⚠️ 点: `already_priced` + `low_novelty` + `weak_magnitude` で全体の大半を占め、「何でもダメ」パターンになっている可能性。

---

## 10. p_outperform 分布 (1d)

```
<0.45 (bearish)              6  ██████
0.45-0.49 (slight bear)      4  ████
0.49-0.51 (neutral)          6  ██████
0.51-0.55 (slight bull)     27  ███████████████████████████  (37%)
0.55-0.60 (modest bull)     16  ████████████████
0.60-0.65 (clear bull)       7  ███████
0.65-0.72 (strong bull)      3  ███
0.72+ (very strong bull)     5  █████
```

p_outperform は confidence よりも連続的に分布しているが、**0.51-0.55 に 37% が集中** — 「ほぼニュートラルだけど少しだけ long」が最多パターン。

---

## 11. 銘柄カバレッジ

| symbol | forecasts |
|--------|----------|
| UNH | **29 (39%)** |
| AAPL | 14 |
| GOOGL | 13 |
| AMZN | 11 |
| TSLA | 8 |

**⚠️ UNH が 39%** — CMS Medicare ニュースが繰り返し抽出されている。銘柄の偏りが大きい。

---

## 12. まとめ: レビュアーに見てほしいポイント

### 1. Confidence の二峰性（最優先）
0.50-0.52 と 0.72-0.80 に二極化し、中間帯がほぼ空。プロンプトのキャリブレーション指示が「連続的なグラデーション」を求めているのに、LLM が binary-like な応答をしている。**これがトレードが一度も発生しない根本原因。**

### 2. Direction positive bias (76%)
金融ニュースの positive bias か、LLM の positive bias か、source selection bias か。

### 3. `already_priced_mean_reversion` が 41%
保守的すぎるか、適切か。事後データがないと判断しにくいが、ほぼ半分を「織り込み済み」とするのはプロンプトの攻撃性が低すぎる可能性。

### 4. Event 重複 (148 events from 55 docs)
同一ニュースの再処理か、1記事から複数イベント抽出か。Dedup の検討が必要。

### 5. 銘柄偏り (UNH 39%)
特定ニュースの繰り返し処理。イベントレベルの重複排除が不足。

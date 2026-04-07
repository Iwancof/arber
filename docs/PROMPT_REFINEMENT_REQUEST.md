# プロンプト設計の洗練依頼

**宛先**: 設計担当者
**発信**: 実装チーム
**日付**: 2026-04-07
**件名**: 意思決定品質に直結するプロンプトテンプレートの設計レビュー・改訂依頼

---

## 背景

Event Intelligence OS のパイプラインが実際にライブニュースで稼働し始めました。

**パイプラインの流れ:**
```
[Alpaca News] → ①イベント抽出(LLM) → ②予測生成(LLM) → ③決定(Policy Engine) → ④注文/保留
```

- LLM は Claude Opus 4.6 を使用
- ニュースは Alpaca News API (Benzinga) から5分間隔で自動取得
- LLM は ①イベント抽出 と ②予測生成 の2箇所で呼ばれる
- ③の決定は LLM ではなく、②の出力をもとに deterministic な Policy Engine が行う

**したがって、プロンプトの品質 ＝ システム全体の意思決定品質** です。

**現在の問題:**
- 予測の大半が `no_trade`（ノイズ判定）で、有意なシグナルが少ない
- イベント抽出の event_type が自由命名で不統一
- ホライズン予測の確信度が 0.5 前後に集中し、差がつかない
- 仮説生成が表面的で、金融理論に基づく深い推論になっていない

---

## システム構造の説明

### プロンプトの使われ方

各プロンプトは `system.txt`（役割定義）と `user.txt.j2`（Jinja2 テンプレート）のペアで構成されています。

- `system.txt` は毎回そのまま Claude の system message として送られる
- `user.txt.j2` は `{{ variable }}` が実際の値に置換されて user message として送られる
- Claude は JSON のみで応答する（markdown 不可）
- 応答はパースされ、DB に保存され、後続の Policy Engine に渡される

### Policy Engine との接続

②予測生成の出力から以下を取り出し、判断を行います：
- `confidence_after` → 取引するかどうかの閾値判定（< 0.45 → no_trade）
- `horizons.1d.p_outperform` → ベンチマーク比のアウトパフォーム確率
- `horizons` のデータ → スコア計算 → アクション決定（long/short/no_trade/wait_manual）

つまり **LLM が返す数値がそのまま投資判断を左右する** ので、キャリブレーションが極めて重要です。

---

## 洗練が必要なプロンプト

---

### ■ プロンプト 1: `event_extract`（イベント抽出）— 重要

パイプラインの入口。ニュース記事から構造化されたイベント情報を抽出します。

#### 現在の system.txt
```
You are an expert financial analyst for Event Intelligence OS.
Always respond with valid JSON only. No markdown, no explanation outside JSON.
Extract structured events from the document.
Output must match the event_record schema shown in the user message.
Every field listed is REQUIRED. Do NOT invent your own field names.
```

#### 現在の user.txt.j2
```
Extract structured events from this document.

Headline: {{ headline }}
Content: {{ raw_text }}

Respond with EXACTLY this JSON structure (fill in real values):

{
  "schema_name": "event_record",
  "schema_version": "1.0.0",
  "events": [
    {
      "event_type": "earnings_beat",
      "affected_assets": ["AAPL"],
      "direction_hint": "positive",
      "materiality": 0.8,
      "novelty": 0.7,
      "evidence_spans": [
        {"text": "quoted text from the document", "start": 0, "end": 50}
      ]
    }
  ]
}

RULES:
- event_type: use descriptive snake_case (earnings_beat, guidance_cut, macro_release, etc.)
- affected_assets: ticker symbols mentioned or implied
- direction_hint: one of positive, negative, neutral, mixed
- materiality: 0.0 (irrelevant) to 1.0 (market-moving)
- novelty: 0.0 (routine) to 1.0 (unprecedented)
- evidence_spans: quote the exact text that supports the extraction
- Return raw JSON only, no markdown
```

#### 利用可能な変数
- `{{ headline }}` — ニュースのヘッドライン
- `{{ raw_text }}` — ニュース本文（ある場合。Alpaca News は summary のみの場合が多い）

#### 問題点
1. `event_type` のタクソノミーが未定義。LLM が `market_share_dominance` `industry_comparison_analysis` 等を自由に命名してしまう
2. `materiality` の判定基準が曖昧。何が 0.3 で何が 0.8 かの基準がない
3. ノイズ（業界比較記事、ランキング記事等）に対するガイダンスがない
4. 同一ドキュメントから複数イベント抽出 vs 主要1件のみ、の方針がない
5. `affected_assets` で直接言及されていないセクターETF等を推定すべきか不明

#### 設計者に求めること
- `event_type` の公式タクソノミー（corporate, macro, regulatory 等のカテゴリと具体的なサブタイプ）
- materiality のキャリブレーション表（イベント種類別の目安）
- ノイズの定義と処理方針（events を空配列で返すか、低 materiality で返すか）
- affected_assets の推定範囲のルール

---

### ■ プロンプト 2: `single_name_forecast`（予測生成）— 最重要

イベントに基づいて、特定銘柄のベンチマーク対比リターンを予測します。**全ての投資判断はこの出力から導かれます。**

#### 現在の system.txt
```
You are an expert financial analyst for Event Intelligence OS.
Always respond with valid JSON only. No markdown, no explanation outside JSON.
Generate a forecast for the given instrument based on the event.
You MUST use EXACTLY the JSON schema shown in the user message.
Every field listed is REQUIRED.
Do NOT invent your own field names.
Do NOT add fields not in the schema.
Focus on relative performance vs benchmark, never point price.
```

#### 現在の user.txt.j2
```
Forecast for {{ symbol }} based on this event.

Event type: {{ event_type }}
Direction hint: {{ direction_hint }}
Event data: {{ event_json }}

Respond with EXACTLY this JSON structure (fill in real values):

```json
{
  "hypotheses": [
    {
      "code": "hypothesis_name",
      "weight": 0.6,
      "description": "why this matters"
    }
  ],
  "selected_hypothesis": "hypothesis_name",
  "rejected_hypotheses": ["other_hypothesis"],
  "counterarguments": [
    {
      "code": "risk_name",
      "severity": "medium"
    }
  ],
  "risk_flags": [],
  "evidence_refs": [],
  "confidence_before": 0.5,
  "confidence_after": 0.65,
  "direction_hint": "positive",
  "horizons": {
    "1d": {
      "p_outperform": 0.58,
      "p_underperform": 0.42,
      "ret_q10": -0.015,
      "ret_q50": 0.005,
      "ret_q90": 0.025
    },
    "5d": {
      "p_outperform": 0.55,
      "p_underperform": 0.45,
      "ret_q10": -0.03,
      "ret_q50": 0.008,
      "ret_q90": 0.04
    }
  }
}
```

RULES:
- Use ONLY these exact field names
- hypotheses: at least 2
- horizons: must include 1d and 5d
- All numbers must be actual values
- p_outperform + p_underperform = 1.0
- confidence_after between 0 and 1
- Return raw JSON only, no markdown
```

#### 利用可能な変数
- `{{ symbol }}` — ティッカーシンボル（例: AAPL）
- `{{ event_type }}` — ①で抽出された event_type
- `{{ direction_hint }}` — ①で抽出された方向（positive/negative/neutral/mixed）
- `{{ event_json }}` — ①で抽出されたイベントの全JSON（evidence_spans含む）

#### 出力がどう使われるか（Policy Engine）
```python
confidence_after < 0.45  →  no_trade（取引しない）
score > 0.60             →  long_candidate（買い候補）
score < -0.60            →  short_candidate（売り候補）
0.40 < |score| < 0.60   →  wait_manual（人間レビュー待ち）
それ以外                 →  no_trade
```
score は `confidence_after` と `horizons.*.p_outperform` の加重平均から計算されます。

#### 問題点
1. **思考フレームワークがない** — 「何を考えるべきか」の指示がなく、スキーマ例だけ渡している
2. **キャリブレーション基準がない** — confidence 0.5 と 0.8 の違いが何か定義していない
3. **イベント種類別のアプローチがない** — earnings も macro も同じプロンプト
4. **ノイズへの対応がない** — routine news でも無理に仮説を立ててしまう
5. **ベンチマークの指定がない** — 「何に対する相対リターンか」が不明
6. **hypotheses が表面的** — "bull/bear" レベルで、メカニズムベースの推論になっていない

#### 設計者に求めること
- 金融分析の思考フレームワーク（このイベントが起きたとき、プロの分析者は何をどう考えるか）
- event_type 別の分析アプローチ（少なくとも: corporate earnings, macro release, regulatory action, M&A, market structure）
- confidence のキャリブレーション基準表
  - 0.50: 情報としてほぼ無価値（ノイズ）
  - 0.55-0.60: 弱いシグナル
  - 0.60-0.70: 明確なシグナル
  - 0.70-0.80: 強い確信
  - 0.80+: 極めて高い確信（まれ）
- ノイズ処理の明確な指示（routine news は confidence_after を 0.50-0.52 に設定、horizons の p_outperform を 0.50 近辺に設定、等）
- hypotheses の品質基準（メカニズムベース：「なぜこのイベントがリターンに影響するか」の因果連鎖）
- counterarguments の具体性（「市場は既に織り込み済み」「サンプルサイズ不足」等の定型リスク）
- ベンチマーク（SPY vs セクターETF）の使い分けガイダンス

---

### ■ プロンプト 3: `skeptic_review`（懐疑的レビュー）— 重要

予測に対する adversarial check。現在はパイプラインに未統合だが、v1.5 で使う予定。

#### 現在の system.txt
```
You are a skeptical financial analyst reviewing a forecast.
Always respond with valid JSON only. No markdown, no explanation outside JSON.
Your job is to find weaknesses, counterarguments, and risks in the forecast.
Challenge every assumption. Identify what could go wrong.
```

#### 現在の user.txt.j2
```
Review this forecast critically.

Symbol: {{ symbol }}
Forecast: {{ forecast_json }}

Respond with JSON:
{
  "overall_assessment": "agree|disagree|partially_agree",
  "confidence_adjustment": 0.0,
  "counterarguments": [
    {
      "code": "risk_name",
      "severity": "low|medium|high|critical",
      "description": "what could go wrong"
    }
  ],
  "missing_evidence": ["what information is lacking"],
  "alternative_hypothesis": "what else could explain the event",
  "recommendation": "proceed|reduce_size|wait|reject"
}
```

#### 問題点
- 具体的なレビュー基準がない（何を疑うべきか）
- 認知バイアスチェック（base rate neglect, anchoring, confirmation bias）がない
- confidence_adjustment の量的基準がない

#### 設計者に求めること
- skeptic が検証すべきチェックリスト
- confidence_adjustment の具体的基準（どの程度の問題でどれだけ下げるか）
- recommendation の判断基準

---

### ■ プロンプト 4: `judge_postmortem`（事後評価）— 中程度

予測が当たったか外れたかを事後的に評価します。

#### 現在の system.txt
```
You are a postmortem analyst evaluating forecast accuracy.
Always respond with valid JSON only. No markdown, no explanation outside JSON.
Compare the original forecast against realized outcomes.
Be objective and specific about what went right and wrong.
```

#### 現在の user.txt.j2
```
Evaluate this forecast against the realized outcome.

Symbol: {{ symbol }}
Original forecast: {{ forecast_json }}
Realized return (relative): {{ realized_rel_return }}
Horizon: {{ horizon_code }}

Respond with JSON:
{
  "verdict": "correct|wrong|mixed|insufficient",
  "direction_correct": true,
  "magnitude_assessment": "underestimated|accurate|overestimated",
  "failure_codes": [],
  "lessons_learned": ["what to improve"],
  "source_quality_note": "was the evidence sufficient",
  "prompt_quality_note": "was the question well-framed"
}
```

#### 問題点
- verdict の定量基準がない（方向正解で magnitude ±何% なら correct か）
- failure_codes の体系が未定義
- 改善提案が「次にどうするか」の actionable な形になっていない

---

### ■ プロンプト 5: `noise_classifier`（新規）

ニュースがノイズかシグナルかを**ヘッドラインだけで**事前判定するプロンプト。現在は全ニュースを forecast まで流しており、コストが無駄。

#### 利用可能な変数
- `{{ headline }}` — ニュースのヘッドライン
- `{{ symbols }}` — 関連ティッカー（Alpaca News が付与）

#### 必要な出力
```json
{
  "classification": "signal|noise|uncertain",
  "confidence": 0.85,
  "reason": "routine industry comparison with no new information"
}
```

#### 設計者に求めること
- signal/noise の分類基準
- uncertain の場合の処理方針（signal 扱いにする等）

---

### ■ プロンプト 6: `inquiry_question_generator`（新規）

Human Inquiry Orchestration で、LLM がオペレーターへの質問文を生成するためのプロンプト。

#### 利用可能な変数
- `{{ event_json }}` — イベントの構造化データ
- `{{ forecast_json }}` — 予測の構造化データ
- `{{ decision_action }}` — Policy Engine の判断
- `{{ inquiry_kind }}` — 質問の種類（pretrade_decision, position_reassessment 等）

#### 必要な出力
```json
{
  "question_title": "短いタイトル",
  "question_text": "具体的な質問文",
  "required_output_schema": { ... },
  "acceptance_rules": ["bounded evidence のみ参照", ...],
  "sla_class": "fast|normal|slow"
}
```

#### 設計者に求めること
- inquiry_kind 別の質問テンプレート方針
- bounded evidence の制約の具体的な表現
- 質問の具体性と回答可能性のバランス

---

## 成果物として期待するもの

各プロンプトについて：

1. **system.txt** — システムメッセージ（テキストファイル、変数なし）
2. **user.txt.j2** — ユーザープロンプト（Jinja2 テンプレート、`{{ variable }}` で変数埋め込み）
3. **calibration_notes.md** — キャリブレーション基準の解説（なぜこの閾値なのか）
4. **golden_cases/** — 期待する入出力の具体例（最低3ケース：典型シグナル、エッジケース、ノイズ）

---

## 技術的制約

- **モデル**: Claude Opus 4.6（1M context）
- **出力形式**: JSON のみ
- **テンプレートエンジン**: Jinja2（`{{ variable }}` で変数埋め込み）
- **トークン制約**: 1リクエスト入出力合計 ~4K tokens 以内が望ましい
- **レイテンシ**: forecast 1件あたり 10-30 秒
- **出力スキーマ変更**: 可能。ただしフィールド名を変更する場合は、Policy Engine との接続箇所（confidence_after, horizons.*.p_outperform 等）に影響するため、変更理由と新しいフィールド名を明記してください
- **対象市場**: v1 は US Equities のみ（S&P 100 + 主要ETF）
- **ベンチマーク**: SPY（デフォルト）、セクターETF（将来）

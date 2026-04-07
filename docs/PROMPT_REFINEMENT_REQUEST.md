# プロンプト設計の洗練依頼

**宛先**: 設計担当者
**発信**: 実装チーム
**日付**: 2026-04-07
**件名**: 意思決定品質に直結するプロンプトテンプレートの設計レビュー・改訂依頼

---

## 背景

パイプラインが実際にライブニュースで稼働し始めました。Claude Opus 4.6 がニュースを取得し、イベント抽出→予測→判断まで自動で回っています。

しかし、**プロンプトは実装者が暫定的に書いたもの**であり、金融分析としての精度・網羅性・一貫性が十分ではありません。プロンプトはシステム全体の性能を左右する最重要ファクターです。

**現在の問題:**
- 予測の大半が `no_trade`（ノイズ判定）で、有意なシグナルが少ない
- イベント抽出の event_type が不統一（`market_share_dominance` のような粒度のバラつき）
- ホライズン予測の確信度分布がベースレート（0.5前後）に集中しすぎている
- 仮説生成が表面的で、金融理論に基づいた深い推論になっていない

---

## 洗練が必要なプロンプト（優先度順）

### 1. `single_name_forecast`（最重要）

**場所**: `prompts/v1/single_name_forecast/`
**影響**: 全ての投資判断に直結。confidence と horizons がそのまま decision スコアになる。

**現在の問題点:**
- 「このスキーマで返して」としか言っておらず、**何を考えるべきか**の指示がない
- ベンチマーク（SPY等）に対する相対リターンの思考フレームワークがない
- イベントの種類別（earnings, macro, regulatory, M&A等）の分析アプローチが未分化
- 「ノイズイベントは confidence_after を低く、horizons を 0.5 近くに」等のキャリブレーション指示がない
- counterarguments と risk_flags が形式的で、実質的なリスク分析になっていない

**設計者に求めること:**
- 金融分析の思考フレームワーク（このイベントが起きたとき、何をどう考えるべきか）
- event_type 別の分析アプローチ（少なくとも corporate, macro, regulatory, market_structure）
- confidence のキャリブレーション基準（0.5=情報なし、0.7=明確なシグナル、0.9=極めて高確信）
- ノイズフィルタリングの明確な指示（routine news は confidence 0.50-0.55 の狭い範囲に収束させる）
- hypotheses の質に関する期待値（「bull/bear」ではなく、メカニズムベースの仮説）

---

### 2. `event_extract`（重要）

**場所**: `prompts/v1/event_extract/`
**影響**: 抽出精度がパイプライン全体の入力品質を決める。ここがズレると全て狂う。

**現在の問題点:**
- event_type のタクソノミーが定義されていない（LLM が自由に命名）
- materiality の判定基準が曖昧（0.2と0.7の違いが何か説明していない）
- 同一ドキュメントから複数イベントを抽出する vs 主要イベントのみ抽出するかのガイダンスがない
- 「このニュースは取引判断に関係ない（noise）」という判定の仕組みがない
- affected_assets の推定精度が低い（直接言及がない場合のセクター推定等）

**設計者に求めること:**
- event_type の公式タクソノミー（仕様書 doc 11 の event_type_registry に合わせたリスト）
- materiality のキャリブレーション表（例: CEO辞任=0.8, 四半期決算beat=0.6, 業界比較記事=0.1）
- noise 判定基準（materiality < 0.3 かつ novelty < 0.3 の場合は抽出不要とするか）
- affected_assets の推定ルール（直接言及, セクター推定, マクロ影響のどこまで抽出するか）

---

### 3. `skeptic_review`（重要 — 未稼働だが設計は今）

**場所**: `prompts/v1/skeptic_review/`
**影響**: forecast に対する adversarial check。v1.5 でパイプラインに統合予定。

**現在の問題点:**
- 骨格のみで、具体的なレビュー基準がない
- 「何を疑うべきか」のフレームワークがない
- base rate neglect, anchoring, confirmation bias 等の認知バイアスチェックがない

**設計者に求めること:**
- skeptic が検証すべきチェックリスト（evidence の十分性、ベースレート、時間軸の妥当性）
- confidence adjustment の具体的な基準（どの程度の問題でどれだけ下げるか）
- recommendation の判断基準（proceed/reduce_size/wait/reject それぞれの条件）

---

### 4. `judge_postmortem`（中程度 — フィードバックループ品質）

**場所**: `prompts/v1/judge_postmortem/`
**影響**: 予測精度の事後評価。プロンプト改善のフィードバックに使う。

**現在の問題点:**
- verdict の判定基準が曖昧
- 「何が原因で当たった/外れた」の根本原因分析が浅い
- failure_codes と既存の reason_code_registry の紐付けがない

**設計者に求めること:**
- verdict 判定の定量基準（方向正解かつ magnitude ±X% 以内 → correct、等）
- 失敗原因の分類体系（source_gap, timing_error, regime_change, model_overconfidence 等）
- 改善提案の構造（次回同種イベントで何を変えるべきか）

---

## 追加で設計してほしいプロンプト

### 5. `inquiry_question_generator`（新規）

Human Inquiry Orchestration で、LLM が人間への質問文を生成するためのプロンプト。現在まだ作成していません。

**必要な内容:**
- イベントと予測の文脈から、人間に聞くべき質問を生成
- bounded evidence のみを参照する制約
- 質問の具体性と回答可能性のバランス

### 6. `noise_classifier`（新規）

ニュースがノイズかシグナルかを事前判定するプロンプト。現在は全てのニュースを forecast まで流しており、API コストが無駄になっている。

**必要な内容:**
- ヘッドラインだけで noise/signal の事前分類
- signal の場合のみ full extraction + forecast に進む

---

## 成果物として期待するもの

各プロンプトについて：

1. **system.txt** — システムメッセージ（役割定義、制約、思考フレームワーク）
2. **user.txt.j2** — ユーザープロンプトテンプレート（Jinja2 変数対応）
3. **calibration_notes.md** — キャリブレーション基準の解説（なぜこの閾値か）
4. **golden_cases/** — 期待する入出力の具体例（最低3ケース：典型, エッジ, ノイズ）

---

## 技術的制約

プロンプト設計時に考慮してください：

- **モデル**: Claude Opus 4.6（1M context, structured output 対応）
- **出力形式**: JSON のみ（markdown 不可）
- **変数**: Jinja2 テンプレート（`{{ symbol }}`, `{{ event_json }}` 等）
- **出力スキーマ**: 変更可能だが、変更する場合はパイプラインの対応箇所も指定してください
- **コスト**: 1リクエストあたり入力+出力合計で ~4K tokens 以内が望ましい
- **レイテンシ**: forecast 1件あたり 10-30 秒（Opus 4.6 の応答速度）

## 現在のプロンプトファイル

```
prompts/
└── v1/
    ├── event_extract/
    │   ├── system.txt
    │   └── user.txt.j2
    ├── single_name_forecast/
    │   ├── system.txt
    │   └── user.txt.j2
    ├── skeptic_review/
    │   ├── system.txt
    │   └── user.txt.j2
    └── judge_postmortem/
        ├── system.txt
        └── user.txt.j2
```

現在の内容はリポジトリで確認可能です。v2 として新バージョンを作成していただく想定です。

# Addendum 18. Human Inquiry Orchestration / Question Ops

## 18.1 目的

既存の `Manual Expert Bridge` と `Prompt Console` は、**その時点で必要な手動プロンプトを発行して受け取る**機能としては成立している。  
ただし、次の要件までは十分に仕様化されていない。

- システムが **常時** 高度な質問候補を生成し続ける
- 質問の重要度と鮮度がリアルタイムに変化する
- ユーザーは手が空いている時だけ回答する
- 回答がなくてもシステムは安全に回り続ける
- 同じ論点に対する質問を改訂・差し替え・再発行できる
- 市場チャート、イベント、decision、manual prompt を **同一の inquiry 単位** で追跡できる

この追補では、これを `Human Inquiry Orchestration` として独立サブシステムにする。

---

## 18.2 設計方針

### 原則1: 質問は「補助入力」であり、クリティカルパスにしない
- inquiry は `optional intelligence` である
- 期限までに回答が来なくても decision engine はフォールバックで継続する
- 回答待ちを理由にパイプライン全体を止めない

### 原則2: 質問生成は 100% LLM に任せない
- **生成候補の検出** は deterministic rules / score で行う
- **自然言語の質問文作成** と **prompt pack 整形** だけ LLM を使ってよい
- これにより「なぜその質問が出たか」を説明可能にする

### 原則3: 質問は `case` と `task` に分ける
- `Inquiry Case`: 1つの論点・調査テーマ
- `Inquiry Task`: その時点の証拠スナップショットに基づく、回答可能な 1 回分の問い
- 同じ case から、時間の経過や新証拠で複数の task revision が生まれる

### 原則4: 質問は bounded evidence で出す
- 外部高性能LLMに渡す prompt は、bounded evidence bundle のみを含む
- 生のウェブ検索を暗黙に要求しない
- これにより監査・再現・比較が可能になる

### 原則5: UI は「常設トレイ + 詳細ページ + チャート注釈」
- 日常運用で見落とさない軽量 UI
- 深掘り用の Dossier
- 市場グラフ上でのオーバーレイ

---

## 18.3 用語

- `Inquiry Signal`: 質問を起票すべきかを示す検知シグナル
- `Inquiry Case`: 1論点の親単位
- `Inquiry Task`: 実際にユーザーへ提示する質問
- `Prompt Pack`: 外部高性能LLMや人間へ渡す整形済みパッケージ
- `Inquiry Response`: ユーザーが返した回答
- `Inquiry Resolution`: その回答を採用 / 却下 / 部分採用した結果
- `Inquiry SLA`: 期待する応答時間帯。hard deadline と別に持つ

---

## 18.4 アーキテクチャ

```text
[Event / Decision / Risk / Source Gap / Novelty Signals]
                     |
                     v
            [Inquiry Signal Evaluator]
                     |
                     v
              [Inquiry Planner]
        (dedupe, score, supersede, SLA)
                     |
          +----------+-----------+
          |                      |
          v                      v
 [Inquiry Case Store]    [Inquiry Task Generator]
                                |
                                v
                        [Prompt Pack Builder]
                                |
                                v
          +-----------+---------+-----------+
          |           |                     |
          v           v                     v
   [User Inbox] [Question Tray] [Chart/Event Overlay]
          |           |                     |
          +-----------+---------------------+
                                |
                                v
                        [Response Parser]
                                |
                                v
                    [Resolution / Weighting]
                                |
                                v
            [Decision Update] [Memory Update] [Postmortem Link]
```

---

## 18.5 どんな時に質問を出すか

### 18.5.1 起票トリガー
最低限、以下の signal を持つ。

- `high_materiality_low_confidence`
- `macro_single_name_conflict`
- `novel_event_type`
- `source_gap_detected`
- `policy_blocked_need_context`
- `position_monitoring_reassessment`
- `postmortem_needs_human_label`
- `schema_invalid_repeated`
- `market_regime_shift`
- `manual_watchlist_item`

### 18.5.2 起票しない条件
- 既存 inquiry case が同じ論点で active
- 期限が短すぎて human response の価値がない
- expected decision uplift が小さい
- 現在の execution_mode が replay で、しかも purely offline replay である
- global `INQUIRY_PAUSE` が有効

### 18.5.3 スコア
`inquiry_priority_score` の例:

```text
priority
= materiality
* uncertainty
* novelty
* decision_impact
* source_gap_factor
* market_stress_factor
* operator_availability_factor
- duplicate_penalty
- stale_case_penalty
```

---

## 18.6 Inquiry Case と Task の違い

### 18.6.1 Inquiry Case
case は「この論点を今追う価値があるか」の単位。

例:
- `AAPL guidance cut は 5d で XLK をアンダーパフォームするか`
- `FDA 承認ニュースは LLY の 20d 相対アウトパフォームに効くか`
- `最近の失敗は source gap か prompt design か`

### 18.6.2 Inquiry Task
task は「この証拠セットで今ユーザーに見せる問い」。

例:
- 09:31 時点の証拠で pretrade review
- 09:47 時点の追加入力込みで revised review
- 16:10 時点の postmortem question

### 18.6.3 revision ルール
新証拠で次が変わったら task を supersede する。

- affected assets
- horizon
- materiality bucket
- benchmark
- evidence set hash
- deadline / urgency class

---

## 18.7 問いの種類

`inquiry_kind` は v1 で以下に固定する。

- `pretrade_decision`
- `position_reassessment`
- `novel_event_interpretation`
- `source_gap_investigation`
- `postmortem_labeling`
- `prompt_reformat_request`
- `market_regime_call`
- `watchlist_reprioritization`

各 kind は別テンプレート / 別 SLA / 別 acceptance rule を持つ。

---

## 18.8 Prompt Pack の構造

質問を自然文 1 本だけで持たず、以下を 1 パッケージにする。

```json
{
  "task_id": "inqt_...",
  "case_id": "inqc_...",
  "title": "FDA approval impact on LLY vs XLV",
  "question": "Will this event likely cause LLY to outperform XLV over 5 trading days?",
  "deadline_utc": "2026-04-08T13:40:00Z",
  "sla_class": "fast",
  "bounded_evidence": [
    {"id":"doc_1","kind":"official","title":"FDA announcement excerpt"},
    {"id":"doc_2","kind":"headline","title":"vendor headline"},
    {"id":"doc_3","kind":"market_snapshot","title":"premarket gap and volume"}
  ],
  "required_output_schema": {
    "verdict": "outperform|neutral|underperform|insufficient",
    "horizons": {
      "1d": {"confidence": "number"},
      "5d": {"confidence": "number"},
      "20d": {"confidence": "number"}
    },
    "key_risks": ["string"],
    "citations": ["doc ids only"]
  },
  "acceptance_rules": [
    "Use only bounded evidence refs",
    "No web browsing assumption",
    "Return valid JSON only"
  ]
}
```

---

## 18.9 回答がなくても回り続ける設計

### 18.9.1 問題
high-performance LLM / human operator は常時即応ではない。  
よって、問い合わせ機能を **同期依存**にすると運用が壊れる。

### 18.9.2 正式ルール
- inquiry response は **optional**
- deadline を過ぎたら `expired` または `superseded`
- decision engine は `auto_only` または `reduced_size` にフォールバック
- inquiry が来なかったこと自体を `response_missing` reason code として残す

### 18.9.3 live/ paper への影響
- `paper/live` で large position 影響がある inquiry は、回答がない場合 `reduced_size` を推奨
- replay/shadow は inquiry なしで通してよい
- inquiry は safety gate ではなく **confidence augmentation layer**

---

## 18.10 ユーザーに「常に質問を提示」する仕組み

### 18.10.1 画面要件
以下の 3 つを追加する。

#### A. Inquiry Tray（常設）
- 画面右側または上部の常設トレイ
- `new / due soon / overdue / answered / superseded` の件数
- priority 上位 3 件を常に表示
- クリックで Dossier へ遷移

#### B. Inquiry Inbox
- フィルター、ソート、claim、snooze、assign
- status 別一覧
- `answer now`, `copy prompt`, `view evidence`, `mark unavailable`

#### C. Inquiry Dossier
- case 単位で時系列
- event / decision / prompt / response / resolution の全履歴
- chart overlay と linked evidence
- superseded chain を表示

### 18.10.2 UI 状態
最低限、以下の状態を色分けする。

- `new`
- `visible`
- `claimed`
- `awaiting_response`
- `submitted`
- `parsed`
- `accepted`
- `rejected`
- `expired`
- `superseded`
- `canceled`

---

## 18.11 質問のリアルタイム更新

### 18.11.1 更新ルール
質問は固定テキストではなく、状態変化で更新され得る。

- 新しい headline が来た
- official filing が到着した
- 価格が barrier 近くに来た
- macro regime が変わった
- decision status が `wait_manual` から `reduced_size` に変わった

### 18.11.2 ただし rewrite しすぎない
同一 case で evidence が増えるたびに task を全部作り直すと混乱する。  
したがって、materiality / benchmark / horizon / verdict space のいずれかが変わる場合のみ supersede する。  
軽微な evidence 追加は task に `evidence_revision_count` を増やして表示だけ更新する。

---

## 18.12 回答 UI の具体要件

### 18.12.1 2モード
- `direct_answer_mode`: 人間が自分で答える
- `external_llm_mode`: 外部高性能LLMへ prompt を貼って、その結果を戻す

### 18.12.2 direct_answer_mode
フォーム字段:
- verdict
- horizon confidence
- key risks
- explanation summary
- evidence refs
- optional notes

### 18.12.3 external_llm_mode
- copy prompt
- copy evidence bundle
- paste response
- parse result
- schema validation
- one-click reformat prompt
- model name input
- run metadata input (optional)

### 18.12.4 期限管理
- deadline 近接時に amber
- 期限超過で red
- 期限超過後の回答は `late_response`
- late response は analytics 用に保存するが、trade scoring には使わない設定を持てる

---

## 18.13 DB 設計追補

既存 `forecasting.prompt_task` / `prompt_response` は decision 直結の単発タスクとしては使える。  
しかし「常設質問キュー」「case と task の分離」「assignment / snooze / supersede / availability」を表現するには不足する。  
そのため、以下を追加する。

### 18.13.1 inquiry_case
- 1論点の親
- linked entity は event / decision / source candidate / postmortem / position
- dedupe key を持つ

### 18.13.2 inquiry_task
- case の revision
- prompt_task より上位
- display 用 status, priority, SLA, prompt pack hash を持つ
- `prompt_task_id` は nullable 参照としてぶら下げる

### 18.13.3 inquiry_assignment
- 誰が claim したか
- いつまで claim 有効か
- shared / exclusive か

### 18.13.4 inquiry_presence
- user availability
- focus mode
- working hours
- can_receive_push

### 18.13.5 inquiry_signal
- どの検知から case が起きたか
- planner の説明可能性のために保存

### 18.13.6 inquiry_resolution
- response をどう採用したか
- scoring weight / accepted / partial / rejected
- late / stale 判定

---

## 18.14 API 追補

### Read APIs
- `GET /v1/inquiry/cases`
- `GET /v1/inquiry/cases/{caseId}`
- `GET /v1/inquiry/tasks`
- `GET /v1/inquiry/tasks/{taskId}`
- `GET /v1/inquiry/tray`
- `GET /v1/inquiry/metrics`

### Actions
- `POST /v1/inquiry/cases/{caseId}/spawn-task`
- `POST /v1/inquiry/tasks/{taskId}/claim`
- `POST /v1/inquiry/tasks/{taskId}/snooze`
- `POST /v1/inquiry/tasks/{taskId}/submit-response`
- `POST /v1/inquiry/tasks/{taskId}/request-reformat`
- `POST /v1/inquiry/tasks/{taskId}/accept`
- `POST /v1/inquiry/tasks/{taskId}/reject`
- `POST /v1/inquiry/tasks/{taskId}/supersede`
- `POST /v1/inquiry/tasks/{taskId}/expire`
- `POST /v1/inquiry/presence`
- `POST /v1/inquiry/signal/recompute`

### Event hooks
- `inquiry.case.created`
- `inquiry.task.created`
- `inquiry.task.priority_changed`
- `inquiry.task.superseded`
- `inquiry.response.received`
- `inquiry.response.accepted`
- `inquiry.response.rejected`
- `inquiry.task.expired`

---

## 18.15 状態遷移

### Case
`open -> monitoring -> resolved | canceled`

### Task
`draft -> visible -> claimed -> awaiting_response -> submitted -> parsed -> accepted | rejected | expired | superseded | canceled`

### Response
`received -> parsed -> valid | invalid -> accepted | rejected | late`

### 重要ルール
- 同一 case で `visible/claimed/awaiting_response` の active task は原則 1 件
- supersede 時は旧 task を閉じ、新 task を visible にする
- accepted response は 1 task に最大 1 件を primary とする
- secondary responses は analytics 用に保持

---

## 18.16 Grafana/UI 追補

### 18.16.1 追加 plugin page
- Inquiry Inbox
- Inquiry Dossier
- Operator Presence / Availability
- Inquiry Metrics

### 18.16.2 追加 panel
- `Question Queue Panel`
- `Event-to-Inquiry Timeline Panel`
- `Inquiry Overlay Panel` for candlestick/state timeline

### 18.16.3 チャートオーバーレイ内容
- inquiry created marker
- inquiry superseded marker
- response submitted marker
- accepted/rejected marker
- deadline band
- unresolved high-priority badge

### 18.16.4 右レール情報
- current open inquiries for this symbol
- response SLA
- manual bridge contribution score
- latest accepted verdict summary

---

## 18.17 権限

### viewer
- 閲覧のみ

### operator
- claim, snooze, submit response, request reformat

### trader
- accepted response を trade scoring に使う承認可
- high-impact inquiry の urgent override 可

### admin
- template / SLA / inquiry policy / routing rule の変更可

---

## 18.18 監視メトリクス

- `inquiry_open_count`
- `inquiry_due_soon_count`
- `inquiry_overdue_count`
- `inquiry_supersede_rate`
- `inquiry_response_latency_p50/p95`
- `inquiry_accept_rate`
- `late_response_rate`
- `manual_uplift_brier_delta`
- `manual_uplift_score_delta`
- `operator_claim_to_submit_sec`
- `question_generation_rate`
- `question_dedup_drop_rate`

### アラート
- overdue high-priority inquiry > N
- parse failures spike
- zero inquiry generation for X hours while events exist
- supersede storm
- manual acceptance rate collapse

---

## 18.19 postmortem 連携

質問系も postmortem に入れる。

failure codes に最低限追加:
- `human_not_available`
- `question_should_have_been_asked`
- `question_asked_too_late`
- `wrong_inquiry_kind`
- `evidence_bundle_too_wide`
- `evidence_bundle_incomplete`
- `stale_manual_answer`
- `supersede_policy_too_aggressive`

これにより、後から「質問生成器そのもの」の改善ができる。

---

## 18.20 v1 / v1.5 / v2 の実装順

### v1
- inquiry_case / inquiry_task / inquiry_response / inquiry_resolution
- Inquiry Inbox / Tray / Dossier
- 主要 signal 4 種
- optional response
- one active task per case
- deadline/expire/supersede
- chart annotations

### v1.5
- assignment / presence
- push notifications
- response weighting by user/model reliability
- postmortem feedback loop

### v2
- multi-user routing
- adaptive inquiry generation by workload
- cross-market inquiry templates
- explanation quality scoring
- semi-automatic question suppression

---

## 18.21 既存設計との関係

### すでに入っているもの
- Manual Expert Bridge
- Prompt Console
- `prompt_task` / `prompt_response`
- reasoning trace
- manual model reliability

### 足りなかったもの
- 常時質問生成の planner
- case/task 分離
- queue / supersede / snooze / assignment
- user availability
- inquiry 専用 UI
- inquiry metrics / postmortem / overlays

### 正式な位置付け
本追補により、既存の Manual Expert Bridge は  
**Human Inquiry Orchestration の 1 実行チャネル** として再定義する。

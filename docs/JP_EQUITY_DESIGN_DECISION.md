# 日本株対応 設計決定 (v1.5)

## 概要
- v1.5 = replay/shadow のみ（Paper Trading は v2 で IBKR）
- ニュース取得 + 構造化抽出 + 予測 + postmortem + inquiry

## ソース (v1.5 必須)
1. JPX Company Announcements Disclosure Service（日本語） - 適時開示
2. JPX Listed Company Search - backfill/履歴参照
3. JPX Company Announcements Service（英語） - 補助証拠
4. EDINET API v2 - 法定開示
5. BOJ RSS/What's New - 金融政策
6. Cabinet Office / ESRI - GDP等マクロ
7. Statistics Bureau / e-Stat - CPI等
8. MOF trade statistics - 貿易統計
9. J-Quants API - 価格/リファレンス

## Market Profile
- market_code: JP_EQUITY
- timezone: Asia/Tokyo
- currency: JPY
- calendar: XTKS
- session: 前場 9:00-11:30, 後場 12:30-15:30

## ユニバース
- 初期: TOPIX Core30
- ベンチマーク: TOPIX/1306 (primary), 日経225/1321 (secondary)

## JP 固有 Event Types
earnings_tanshin, earnings_revision, dividend_change,
share_buyback, treasury_share_cancellation, stock_split,
tob_mbo, market_reassignment, shareholder_benefit_change,
parent_subsidiary_restructuring, large_shareholding_change,
exchange_or_regulatory_action

## プロンプト
- 日本語版を別途用意 (_ja suffix)
- JSON schema と event_type は英語共通
- 日本語原文を主、英語は補助証拠

## Dedup
- canonical: JPX日本語 > JPX英語 > EDINET > 一般ニュース
- key: issuer_code + normalized_title + disclosed_at(±10min) + event_type

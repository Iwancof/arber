# 11. Source Registry, Market Profiles, and Adapters

## 11.1 目的

米国株だけでなく、他市場・他 asset class へ広げられるように、  
取得ロジックを **publisher 固定**ではなく **source registry + endpoint + adapter + bundle** で設計する。

## 11.2 Market Profile

market_profile は市場の人格を表す。

### 必須属性
- market_code
- display_name
- asset_class
- primary_timezone
- quote_currency
- calendar_code
- session_template_json
- default_benchmark_rules_json
- default_source_bundle_id
- default_horizons_json
- default_language_priority_json
- corporate_action_policy_json
- execution_mode_policy_json

### 例
- us_equities
- jp_equities
- eu_equities
- global_macro
- fx_spot
- commodities_futures
- crypto_spot

## 11.3 Source Registry

source registry は logical publisher の台帳。  
`1 source = 1 logical publisher / provider / internal feed` を基本とする。  
その下に複数 endpoint を持つ。

### source_type
- official
- vendor
- exchange
- regulator
- macro_calendar
- community
- internal

### adapter_type
- rss
- json_api
- html_scrape
- websocket
- calendar
- file_drop
- manual_entry
- composite

### trust_tier
- official
- high_vendor
- medium_vendor
- low_vendor
- experimental

## 11.4 Endpoints

1 source が複数 endpoint を持てる。

例:
- RSS feed
- structured JSON API
- release calendar
- web socket channel
- HTML page
- downloadable file

### 理由
publisher 単位と transport 単位を分けないと、運用と信頼度を評価しづらい。

## 11.5 Source Bundle

bundle は利用文脈ごとの source 集合。

### bundle_scope
- market_core
- sector_overlay
- event_overlay
- temporary
- user_defined (future)

### 例
- us_equities_core
- us_biotech_overlay
- global_macro_core
- jp_equities_core
- fx_macro_overlay

## 11.6 Watch Planner

watch planner は次を入力として必要 source を決める。

- market_profile
- active universe
- current positions
- sector exposures
- source gap stats
- scheduled event windows
- mode

### need score
`need_score = exposure_weight × event_sensitivity × trust_score × miss_penalty - cost_penalty`

## 11.7 Adapter Interface

すべての source adapters は次を満たす。

- health()
- fetch()
- parse()
- normalize()
- checkpoint()
- backfill()
- canDryRun()

### normalize output
raw_document contract に合わせる。

## 11.8 Multilingual Handling

市場が増えると多言語になる。  
そのため source registry は次を持つ。

- primary languages
- fallback languages
- translation allowed flag
- local market relevance score

### 方針
翻訳は secondary。  
raw text と translated summary を分ける。

## 11.9 非米国市場の追加例

### 日本株
- market_profile: jp_equities
- timezone: Asia/Tokyo
- bundles: jp_equities_core + global_macro_core
- language priority: ja, en
- local regulator / exchange feeds を source registry に追加

### 欧州株
- market profile per region or venue cluster
- multi-currency support
- market holidays and session variation
- multilingual headlines handling

### FX / Commodities / Crypto
- instrument_type の違い
- benchmark の概念が異なる
- news source bundle も macro-heavy になる

## 11.10 Source Candidate Lifecycle

- candidate
- provisional
- validated
- production
- retired

### 昇格基準
- fetch stability
- parser success
- dedupe compatibility
- event contribution
- source gap reduction
- operator trust

## 11.11 将来の Source Marketplace

将来的には source adapter を plugin で増やせる。  
そのため、registry row と adapter implementation を分離し、  
manifest で capability を宣言する。

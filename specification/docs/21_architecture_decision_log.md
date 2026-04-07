# 21. Architecture Decision Log

本ドキュメントは主要な設計判断を短く一覧化した index である。  
詳細は `adrs/` を参照。

## 採用済み判断

1. market-profile-first  
   市場ごとの差異はコード分岐ではなく profile に寄せる。

2. Grafana shell with custom plugins  
   標準ダッシュボードのみではなく、app/plugin を前提とする。

3. Ledger separation  
   forecast / decision / order / outcome / postmortem は別 ledger。

4. Worker adapter contract  
   API worker, CLI worker, manual bridge を同じ task/result 契約で扱う。

5. Contract versioning + outbox  
   schema evolution と内部イベントを制御する。

## 先送りした判断

- multi-broker routing
- full plugin marketplace
- full tenant model
- overnight live by default
- provider-agnostic ensemble router

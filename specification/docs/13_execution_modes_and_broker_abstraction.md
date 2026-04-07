# 13. Execution Modes and Broker Abstraction

## 13.1 モード定義

- replay
- shadow
- paper
- micro_live
- live

## 13.2 mode の意味

### replay
過去時点のデータで deterministic に再現する。  
注文は仮想。

### shadow
リアルタイムで signal/decision まで生成するが、注文は出さない。

### paper
ブローカーの paper 環境に注文する。

### micro_live
実資金だが極小サイズ・制限付き。

### live
通常本番。

## 13.3 原則

- strategy code は共通
- execution adapter だけ切り替える
- mode ごとに risk caps を変える
- UI に mode badge を常時表示
- live への切替は明示的 arm/disarm

## 13.4 BrokerAdapter

共通契約:
- health()
- submit(intent)
- cancel(orderRef)
- replace(orderRef)
- reconcile(openOrders)
- positions()
- accountState()
- marketSessionState()

### Order Intent
- instrument
- side
- quantity
- order_type
- limit/stop params
- tif
- session policy
- decision reference

## 13.5 Execution Safety

### v1 方針
- regular session 主体
- long-only 先行
- high liquidity universe 限定
- micro_live は size cap 厳格
- kill switch always available

## 13.6 Paper と Live の差分設計

paper は本番代替ではない。  
そのため 3 種の評価を持つ。

- broker_paper_pnl
- adjusted_paper_pnl
- shadow_signal_pnl

## 13.7 Conservative Overlay

paper/live 差分を埋めるため、次を別計算で持つ。

- slippage penalty
- fee model
- borrow fee
- dividend adjustment
- queue penalty
- session penalty

## 13.8 Order Lifecycle

states:
- created
- submitted
- acknowledged
- partially_filled
- filled
- canceled
- rejected
- expired
- replaced

order ledger は broker status 原文と normalized status の両方を保存する。

## 13.9 Session Awareness

market_profile の session_template を execution が必ず参照する。  
同じ strategy でも市場ごとに session policy は変わる。

## 13.10 Future Multi-Broker

将来複数 broker を追加するなら:

- broker account registry
- broker capability matrix
- broker health score
- routing policy

ただし v1 では単一 broker でよい。

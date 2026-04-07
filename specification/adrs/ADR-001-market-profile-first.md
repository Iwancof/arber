# ADR-001: Market Profile First

## Status
Accepted

## Context
市場ごとの差異をコード上の if/else に散らすと、保守と市場追加が難しくなる。

## Decision
市場依存の設定は `market_profile` に集約する。

## Consequences
- 市場追加コストが下がる
- profile completeness review が必要になる
- すべての実装が profile を参照する discipline が必要

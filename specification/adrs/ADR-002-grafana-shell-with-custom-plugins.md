# ADR-002: Grafana Shell with Custom Plugins

## Status
Accepted

## Context
観測と運用UIを別アプリで作ると、相互参照が弱くなる。

## Decision
Grafana を shell にし、standard dashboards + app plugins + panel plugins を採用する。

## Consequences
- observability と業務UIが近づく
- plugin 開発が必要
- Grafana の制約に合わせる必要がある

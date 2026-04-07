# ADR-004: Worker Adapter Contract

## Status
Accepted

## Context
API model, CLI model, manual bridge を混在させたい。

## Decision
`WorkerTask` / `WorkerResult` の共通契約を導入し、adapter に閉じ込める。

## Consequences
- provider 差分が隠蔽される
- adapter 実装と contract tests が必要

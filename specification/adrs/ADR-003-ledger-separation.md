# ADR-003: Ledger Separation

## Status
Accepted

## Context
予測と判断と発注を上書きすると auditability が失われる。

## Decision
event / forecast / decision / order / outcome / postmortem を別 ledger に分け、append-oriented に扱う。

## Consequences
- 追跡しやすい
- join は重くなるため rollup が必要

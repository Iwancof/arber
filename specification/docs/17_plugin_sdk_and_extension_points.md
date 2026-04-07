# 17. Plugin SDK and Extension Points

## 17.1 目的

Grafana shell 上で UI と integration を伸ばすための拡張モデルを定義する。  
また、source adapter / worker adapter / broker adapter などの backend 拡張点も整理する。

## 17.2 Plugin Categories

### UI plugins
- app page plugin
- panel plugin
- overlay plugin
- action plugin

### Backend plugins
- source adapter
- worker adapter
- broker adapter
- policy pack
- experiment pack

## 17.3 Plugin Manifest

最低限の字段:
- plugin_code
- plugin_type
- display_name
- plugin_version
- plugin_api_version
- capabilities
- required_permissions
- supported_markets
- dependencies
- status

## 17.4 Extension Points

| extension point | input | output |
|---|---|---|
| source adapter | endpoint config | raw documents |
| worker adapter | worker task | worker result |
| broker adapter | order intent | normalized broker result |
| policy pack | forecast + context | decision |
| panel plugin | query payload | rendered visualization |
| action plugin | UI action request | command result |

## 17.5 Plugin Registration Flow

1. manifest registered
2. compatibility check
3. disabled by default
4. sandbox / dev enable
5. production enable per environment
6. health monitored
7. safe disable path defined

## 17.6 UI Plugin Boundaries

UI plugins should not:
- mutate DB directly
- bypass authz
- read secrets
- invent their own contracts

UI plugins should:
- call action/query facade
- declare capabilities
- emit frontend telemetry
- respect mode badges and role checks

## 17.7 Backend Plugin Boundaries

backend plugins should:
- implement declared contract
- return structured result
- emit health
- version themselves
- support timeout/cancellation where relevant

## 17.8 Safe Disable

plugin は disable されても core system が動くこと。  
特に overlay panel が壊れても decision engine は止まらないこと。

## 17.9 Future Marketplace

将来 plugin marketplace を作る余地はあるが、v1 は internal curated registry に留める。

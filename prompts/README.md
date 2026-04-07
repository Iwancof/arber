# Prompt Templates

プロンプトテンプレートのバージョン管理ディレクトリ。

## 構造

```
prompts/
├── v1/                          # バージョン 1
│   ├── event_extract/
│   │   ├── system.txt           # システムメッセージ
│   │   └── user.txt.j2          # ユーザープロンプト (Jinja2)
│   ├── single_name_forecast/
│   │   ├── system.txt
│   │   └── user.txt.j2
│   ├── skeptic_review/
│   │   ├── system.txt
│   │   └── user.txt.j2
│   └── judge_postmortem/
│       ├── system.txt
│       └── user.txt.j2
└── README.md
```

## 規約

- `system.txt`: システムメッセージ（変数なし、そのまま使用）
- `user.txt.j2`: ユーザープロンプト（Jinja2 テンプレート、変数埋め込み）
- 変数は `{{ variable_name }}` で埋め込む
- バージョンディレクトリ（v1, v2, ...）で管理
- 変更時は新バージョンを作成し、古いバージョンは残す

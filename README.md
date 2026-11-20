# LitNexus: Agent-Native Academic Literature Infrastructure  
# LitNexus: エージェント指向・学術文献知識ベース基盤

[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()
[![Architecture: Stratified Shards](https://img.shields.io/badge/Architecture-Stratified%20Shards-blue.svg)]()
[![Target: Human & LLM Agents](https://img.shields.io/badge/Designed%20For-Human%20%26%20Agents-orange.svg)]()

---

## Executive Summary / 概要

### [English]
`LitNexus` is an agent-native literature repository and autonomous survey ecosystem designed for academic laboratories. Conventional reference management platforms (e.g., Zotero, Mendeley) cater strictly to visual human consumption and suffer from severe friction when queried by Large Language Model (LLM) agents due to context-window saturation and citation hallucination. 

`LitNexus` addresses this epistemic barrier through **Stratified Knowledge Sharding**: dividing thousands of papers into bounded, fixed-entropy partitions (~48–52 KiB JSONL files), mapped via dual-index routing tables (`batch_catalog.tsv` and `paper_locator.tsv`). This enables both automated LLM ingestion agents and human researchers to systematically navigate, synthesize, and inherit deep academic corpuses without cognitive or computational degradation.

### [日本語]
`LitNexus`（リットネクサス）は、大学および企業の研究室（Lab）における持続可能な知識継承と、自律型AIエージェントによる自動文献サーベイを両立させるために設計された**エージェント指向の学術文献基盤**です。

ZoteroやMendeley等の既存文献管理ツールは人間の視覚的閲覧のみを前提としており、LLMエージェントが数千本規模の論文を横断的に探索・検証しようとすると、コンテキスト長の制限（Context Saturation）や「中だるみ現象（Lost-in-the-Middle）」、ハルシネーションの発生といった構造的障壁に直面します。

`LitNexus`は、文献全量を約48〜52 KiBの**「階層化分割シャード（Stratified Shards）」**に分散配置し、巨視的カタログ（`batch_catalog.tsv`）と決定論的ルーティング表（`paper_locator.tsv`）を組み合わせることで、エージェントが限られたコンテキスト内で数千本の文献を自由に行き来し、確固たる根拠に基づいたサーベイと自動更新を行える環境を提供します。

---

## Core System Architecture / システム構成

```text
LitNexus/
├── AGENTS.md                  # Autonomous Agent operational directive / エージェント運用指示書
├── README.md                  # Project overview (Bilingual) / プロジェクト概要（日英併記）
├── CONTRIBUTING.md            # Lab contribution & domain guide / 研究領域追加規約
├── docs/                      # Technical specifications / システム詳細仕様
│   ├── ARCHITECTURE.md        # Sharding algorithm & hybrid storage / シャーディング設計と保存方針
│   └── INGESTION_PROTOCOL.md  # Step-by-step ingestion protocol / 論文自動取り込みプロトコル
├── templates/                 # Scaffolding templates / 新規領域用テンプレート
│   └── domain_template/       # Standard domain scaffold / 標準ドメイン骨格
├── tools/                     # Deterministic automation utilities / 決定論的支援ツール群
│   ├── ingest_helper.py       # Atomic ingestion & shard auto-roller / 原子性インジェスト支援
│   ├── create_domain.py       # Domain generator / 新規ドメイン生成スクリプト
│   └── validate_domain.py     # Structural linter & validator / 整合性検証スクリプト
└── domains/                   # Research sub-repositories / 各研究領域の独立サブディレクトリ
    ├── HRI/                   # Human-Robot & Human-Agent Interaction
    └── Agent_Authority/       # Autonomous Agent Social Behaviour & Authority
```

---

## Why LitNexus? (Comparative Analysis) / なぜ LitNexus なのか？

| Dimension / 評価軸 | Conventional Tools (Zotero / PDFs) / 従来ツール | Flat LLM Feeds (arXiv-daily) / 単純なRSS/要約 | LitNexus Framework |
| :--- | :--- | :--- | :--- |
| **Agent Readability** / エージェント可読性 | ❌ Low (Unstructured PDFs, context overflow) | ⚠️ Moderate (Unbounded markdown growth) | **Optimal (Bounded ~50 KiB shards, $O(1)$ routing)** |
| **Epistemic Depth** / 学術的深度 | ⚠️ Moderate (Isolated human notes) | ❌ Shallow (Abstract-only summaries) | **Deep (Falsifiable claims, verified syntheses)** |
| **Lab Knowledge Inheritance** / 研究室資産の継承 | ❌ Fragmented (Lost when students graduate) | ❌ Discarded as daily noise | **Permanent (Versioned, modular domain code)** |
| **Multi-Domain Scalability** / 領域拡張性 | ⚠️ Manual folder tagging | ❌ Monolithic scripts | **Pluggable (Isolated namespaces & zero-conflict)** |

---

## Quickstart Guide / 利用開始手順

### For Human Researchers / 研究者向け手順

1. **Creating a New Research Domain / 新しい研究領域を立ち上げる**:
   ```bash
   python tools/create_domain.py \
     --name "Embodied_AI" \
     --title-en "Embodied AI & Manipulation" \
     --title-ja "身体性AIとマニピュレーション"
   ```
   *This automatically provisions the 4-tier directory topology (`01_rough_index`, `02_raw_materials`, `03_deep_reading`, `04_archive`) and configuration files.*  
   *（これにより、01〜04の標準ディレクトリ階層、設定ファイル、初期索引表が自動生成されます。）*

2. **Validating Repository Integrity / リポジトリの健全性を検証する**:
   ```bash
   python tools/validate_domain.py --all
   ```

### For Autonomous AI Agents / AIエージェント向け手順

Agents running in Cursor, Claude Code, Antigravity, or CI pipelines must read `AGENTS.md` upon initial activation.
To ingest a new paper autonomously without formatting errors:
```bash
python tools/ingest_helper.py \
  --domain domains/<domain_name> \
  --entry '{"id": "2405.16021", "title": "...", "year": 2026, "decision": "include", "author_claims": ["..."]}' \
  --text-file path/to/extracted.txt
```

---

## License & Attribution / ライセンス

Maintained for academic research and collaborative laboratory scholarship. All bibliographic excerpts retain original author copyright.

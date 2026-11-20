# Domain Name — Literature Repository / 研究領域文献リポジトリ

> **Domain Scope**: Formal Academic Domain Title  
> **研究領域**: 研究領域の名称  
> **Operational Guide**: Dual guidelines for autonomous agents and researchers. / エージェントおよび研究者向け利用手引き。

---

## 1. Domain Charter & Scope (領域の定義と範囲)

### [English]
This sub-repository aggregates, organizes, and analyzes literature pertaining to **Domain Title**. It is architected specifically for AI agent comprehension and human literature surveys, organizing findings across structured tiers of evidence without overflowing working context.

### [日本語]
本サブディレクトリは、**研究領域の名称**に関する学術論文を体系的に管理・分析するための基盤です。AIエージェントによる自動探索と、人間の研究者による文献精読の双方を支えるため、コンテキスト消費を抑制する階層的インデックス構造を採用しています。

---

## 2. Structural Layout (構成概要)

- `00_INDEX.md`: Charter and scope definition. / 領域定義および運用方針。
- `domain_config.yaml`: Triage rules and scraping criteria. / 判定ルールおよび検索設定。
- `01_rough_index/`:
  - `batch_catalog.tsv`: Metadata summary per ~48KiB partition shard. / 批次カタログ。
  - `paper_locator.tsv`: Deterministic ID-to-path routing table. / 論文ロケータ。
  - `*.jsonl`: Structured bibliographic records in bounded chunks. / 分割JSONLインデックス。
- `02_raw_materials/`: Extracted plaintexts (`TXT/`) and reference PDFs (`PDF/`). / テキスト本文およびPDF。
- `03_deep_reading/`: Thesis claim graphs (`claims.jsonl`) and verified notes. / 主張リストおよび精読メモ。
- `04_archive/`: Historical materials, scripts, and legacy datasets. / 過去の資料およびアーカイブ。

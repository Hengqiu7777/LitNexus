#!/usr/bin/env python3
"""
LitNexus Domain Scaffolding Tool
=================================
Initializes a new standardized academic domain directory with all structural
invariants, configuration stubs, and dual-index matrices.

Usage:
  python tools/create_domain.py --name "Embodied_AI" --title-en "Embodied AI & Manipulation" --title-ja "身体性AIとマニピュレーション"
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

TSV_LOCATOR_HEADER = (
    "id\ttitle\tyear\tindex\tbatch\tline\ttext_path\tpdf_path\treading_path\tbatch_url\ttext_url\tpdf_url\treading_url\n"
)

TSV_CATALOG_HEADER = (
    "file\tindex\texisting_group\trecords\tbytes\texisting_topics_and_counts\tfirst_id\tlast_id\tdrive_url\n"
)


def create_domain(name: str, title_en: str, title_ja: str, root_dir: Path):
    domain_dir = root_dir / "domains" / name
    if domain_dir.exists():
        print(f"Error: Domain '{name}' already exists at {domain_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Initializing domain '{name}' at {domain_dir}...")

    # Create directories
    (domain_dir / "01_rough_index").mkdir(parents=True, exist_ok=True)
    (domain_dir / "02_raw_materials" / "TXT").mkdir(parents=True, exist_ok=True)
    (domain_dir / "02_raw_materials" / "PDF").mkdir(parents=True, exist_ok=True)
    (domain_dir / "02_raw_materials" / "supplements").mkdir(parents=True, exist_ok=True)
    (domain_dir / "03_deep_reading" / "close_readings").mkdir(parents=True, exist_ok=True)
    (domain_dir / "04_archive").mkdir(parents=True, exist_ok=True)

    # Initialize empty TSVs
    with open(domain_dir / "01_rough_index" / "paper_locator.tsv", "w", encoding="utf-8") as f:
        f.write(TSV_LOCATOR_HEADER)

    with open(domain_dir / "01_rough_index" / "batch_catalog.tsv", "w", encoding="utf-8") as f:
        f.write(TSV_CATALOG_HEADER)

    # Initialize domain_config.yaml
    config_content = f"""# LitNexus Domain Configuration: {name}
# ==========================================================

domain_metadata:
  identifier: "{name}"
  title_en: "{title_en}"
  title_ja: "{title_ja}"
  maintainers: ["Lab Research Member"]
  created_at: "2026-11-20"

search_criteria:
  arxiv_categories:
    - "cs.AI"
    - "cs.RO"
  venues:
    - "RSS"
    - "ICRA"
    - "CoRL"
    - "NeurIPS"
  keywords_mandatory: []
  keywords_optional: []
  keywords_exclude: []

triage_heuristics:
  include_threshold: "Direct empirical or theoretical contributions to core mechanisms."
  pending_threshold: "Adjacent methodologies, benchmark releases, or survey papers."
  exclude_threshold: "Out-of-scope hardware designs, generic position statements."

storage:
  cloud_storage_root: ""
"""
    with open(domain_dir / "domain_config.yaml", "w", encoding="utf-8") as f:
        f.write(config_content)

    # Initialize 00_INDEX.md (Bilingual: Academic English + Natural Japanese)
    index_content = f"""# {name} — Literature Sub-Repository / 研究文献サブディレクトリ

> **Domain Scope**: {title_en}  
> **研究領域**: {title_ja}  
> **Operational Guide**: For autonomous agents and human researchers. / エージェントおよび研究者向け利用ガイド。

---

## 1. Domain Charter & Scope (研究領域の定義と範囲)

### [English]
This sub-repository systematically aggregates, indexes, and analyzes scholarly literature regarding **{title_en}**. It is architected for dual consumption: allowing autonomous AI agents to explore thematic clusters without context saturation, while offering human researchers direct traceability back to empirical claims and primary texts.

### [日本語]
本サブディレクトリは、**{title_ja}**（{title_en}）に関する学術文献を体系的に集積・索引化・分析するための研究知識ベースです。LLMエージェントがコンテキスト制約を超過することなく多角的な探索を行えるように設計されていると同時に、人間の研究者が論文の根底にある学術的主張（Claims）や一次資料へ即座にアクセスできるよう配慮されています。

---

## 2. Directory Layout (ディレクトリ構成)

- `00_INDEX.md`: Scope charter and operational guide. / 領域定義および運用手引き。
- `domain_config.yaml`: Automated tracking parameters and triage heuristics. / 自動収集パラメータおよび判定基準。
- `01_rough_index/`:
  - `batch_catalog.tsv`: Thematic distribution, record counts, and cloud pointers per batch. / 批次（バッチ）ごとの主題分布・レコード数一覧。
  - `paper_locator.tsv`: Fast $O(1)$ routing locator mapping IDs to text/PDF paths. / 論文IDとファイルパスを直結する高速ルケータ。
  - `*.jsonl`: Partition shards constrained to ~48–52 KiB per file. / 1ファイル約48〜52 KiBに最適化された文献メタデータ群。
- `02_raw_materials/`: Extracted plaintext (`TXT/`) and source PDFs (`PDF/`). / 抽出テキストおよび元版PDF。
- `03_deep_reading/`: Atomic claim graphs (`claims.jsonl`) and analytical notes. / 構造化主張リストおよび精読記録。
- `04_archive/`: Historical snapshots, scripts, and legacy manifests. / 過去の作業スナップショットおよびアーカイブ。

---

## 3. Operational Workflow for Agents (エージェント向け実行手順)

1. Read `01_rough_index/batch_catalog.tsv` to identify thematic shards matching your prompt. / プロンプトに関連する批次をカタログから特定する。
2. Ingest the matching `.jsonl` partition shard into active memory. / 該当する単一のJSONLバッチをコンテキストに読み込む。
3. Query `01_rough_index/paper_locator.tsv` for physical text (`02_raw_materials/TXT/`) or deep synthesis (`03_deep_reading/`). / 詳細な検証が必要な場合、ロケータを参照してテキストまたは精読ノートを取得する。
"""
    with open(domain_dir / "00_INDEX.md", "w", encoding="utf-8") as f:
        f.write(index_content)

    print(f"[✓] Successfully initialized domain '{name}'!")


def main():
    parser = argparse.ArgumentParser(description="LitNexus Domain Scaffolding Tool")
    parser.add_argument("--name", required=True, help="Directory name (e.g. Embodied_AI)")
    parser.add_argument("--title-en", required=True, help="English title of research domain")
    parser.add_argument("--title-ja", required=True, help="Japanese title of research domain")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent
    create_domain(args.name, args.title_en, args.title_ja, root_dir)


if __name__ == "__main__":
    main()

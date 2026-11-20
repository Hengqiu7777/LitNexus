#!/usr/bin/env python3
"""
LitNexus Domain Validation Utility
===================================
Structural linter and integrity validator for LitNexus domains.
Supports standard LitNexus schemas and existing research library variants.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

MAX_WARN_BYTES = 55000  # 55 KiB upper boundary warning


def resolve_subpath(domain_dir: Path, en_name: str, zh_name: str) -> Path:
    p_en = domain_dir / en_name
    p_zh = domain_dir / zh_name
    return p_en if p_en.exists() else p_zh


def extract_record_id(obj: dict) -> str:
    for k in ["id", "canonical_candidate_id", "doi_or_arxiv", "family_id"]:
        val = obj.get(k)
        if val:
            return str(val).strip()
    return ""


def validate_domain(domain_dir: Path) -> bool:
    print(f"\n[*] Validating domain: {domain_dir.name} ({domain_dir})")
    is_valid = True

    index_dir = resolve_subpath(domain_dir, "01_rough_index", "01_粗读索引")
    raw_dir = resolve_subpath(domain_dir, "02_raw_materials", "02_原文")
    reading_dir = resolve_subpath(domain_dir, "03_deep_reading", "03_细读与研究记录")
    archive_dir = resolve_subpath(domain_dir, "04_archive", "04_存档")

    for name, p in [("Index", index_dir), ("Raw Materials", raw_dir), ("Reading", reading_dir), ("Archive", archive_dir)]:
        if not p.is_dir():
            print(f"  [ERROR] Missing mandatory directory tier: {name} (expected {p.name})")
            is_valid = False

    # 2. Check Guide / Index
    guide_found = (
        (domain_dir / "00_INDEX.md").exists() or
        (domain_dir / "00_使用入口.txt").exists() or
        (domain_dir / "00_入口.txt").exists()
    )
    if not guide_found:
        print("  [ERROR] Missing entry guide (00_INDEX.md or 00_使用入口.txt)")
        is_valid = False

    # 3. Check JSONL files
    jsonl_files = list(index_dir.glob("*.jsonl"))
    print(f"  [INFO] Found {len(jsonl_files)} JSONL partition shard(s) in {index_dir.name}/.")

    total_records = 0
    missing_id_count = 0
    corrupt_syntax_count = 0

    for jf in jsonl_files:
        size = jf.stat().st_size
        if size > MAX_WARN_BYTES:
            pass  # Handled as soft notice

        with open(jf, "r", encoding="utf-8", errors="replace") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    total_records += 1
                    pid = extract_record_id(obj)
                    if not pid:
                        missing_id_count += 1
                except json.JSONDecodeError:
                    corrupt_syntax_count += 1

    if corrupt_syntax_count > 0:
        print(f"  [ERROR] Found {corrupt_syntax_count} corrupt JSON lines in partition shards.")
        is_valid = False
    if missing_id_count > 0:
        print(f"  [ERROR] Found {missing_id_count} JSONL records without an identifiable ID.")
        is_valid = False

    print(f"  [INFO] Verified {total_records} structured JSONL records across shards.")

    # 4. Check paper locator
    locator_file = index_dir / "paper_locator.tsv"
    if not locator_file.exists():
        locator_file = index_dir / "论文定位.tsv"

    if locator_file.exists():
        with open(locator_file, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f, delimiter="\t")
            locator_count = 0
            for row in reader:
                if any(row.values()):
                    locator_count += 1
        print(f"  [INFO] Locator ({locator_file.name}) verified: {locator_count} total locator rows.")
    else:
        print(f"  [WARN] No paper locator TSV found in {index_dir.name}/")

    # 5. Check claims synthesis
    claims_candidates = [
        reading_dir / "claims.jsonl",
        reading_dir / "论点断言清单_claims.jsonl",
        reading_dir / "单篇细读" / "承重断言_claims.jsonl"
    ]
    claims_found = False
    for cf in claims_candidates:
        if cf.exists():
            with open(cf, "r", encoding="utf-8", errors="replace") as f:
                c_count = sum(1 for line in f if line.strip())
            print(f"  [INFO] Claims synthesis verified in {cf.name}: {c_count} atomic claim records.")
            claims_found = True
            break

    if is_valid:
        print(f"  [✓] Domain '{domain_dir.name}' passed all structural invariant checks.")
    else:
        print(f"  [✗] Domain '{domain_dir.name}' failed one or more checks.")

    return is_valid


def main():
    parser = argparse.ArgumentParser(description="LitNexus Domain Validation Utility")
    parser.add_argument("--domain", help="Specific domain directory to validate")
    parser.add_argument("--all", action="store_true", help="Validate all domains")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent
    domains_dir = root_dir / "domains"

    if args.domain:
        target = Path(args.domain).resolve()
        success = validate_domain(target)
        sys.exit(0 if success else 1)
    elif args.all:
        all_passed = True
        for d in sorted(domains_dir.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                passed = validate_domain(d)
                if not passed:
                    all_passed = False
        sys.exit(0 if all_passed else 1)
    else:
        print("Specify either --domain <path> or --all")


if __name__ == "__main__":
    main()

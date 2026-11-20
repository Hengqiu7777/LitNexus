#!/usr/bin/env python3
"""
LitNexus Ingestion Helper Utility
==================================
Deterministic, atomic partition management and bibliographic ingestion engine.
Enforces the 48-52 KiB JSONL shard boundary and updates dual TSV indices.

Usage:
  python tools/ingest_helper.py --domain domains/HRI --entry '<JSON>' [--text-file path] [--pdf-file path]
  python tools/ingest_helper.py --domain domains/HRI --json-file entry.json [--text-file path] [--pdf-file path]
"""

import argparse
import csv
import json
import os
import shutil
import sys
from pathlib import Path

MAX_BATCH_BYTES = 51200  # ~50 KiB target threshold


def sanitize_tsv_field(val) -> str:
    if val is None:
        return ""
    s = str(val).replace("\t", " ").replace("\r", "").replace("\n", " ")
    return s.strip()


def load_locator_ids(locator_path: Path) -> set:
    if not locator_path.exists():
        return set()
    existing_ids = set()
    with open(locator_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if "id" in row:
                existing_ids.add(row["id"].strip())
    return existing_ids


def get_active_batch_file(index_dir: Path, domain_name: str, group: str) -> tuple[Path, int]:
    pattern = f"{domain_name}_{group}_*.jsonl"
    matching = sorted(index_dir.glob(pattern))
    if not matching:
        batch_num = 1
        return index_dir / f"{domain_name}_{group}_{batch_num:03d}.jsonl", batch_num

    last_file = matching[-1]
    name_parts = last_file.stem.split("_")
    try:
        batch_num = int(name_parts[-1])
    except ValueError:
        batch_num = len(matching)

    # Check size
    if last_file.stat().st_size >= MAX_BATCH_BYTES:
        batch_num += 1
        return index_dir / f"{domain_name}_{group}_{batch_num:03d}.jsonl", batch_num
    else:
        return last_file, batch_num


def count_lines(filepath: Path) -> int:
    if not filepath.exists():
        return 0
    with open(filepath, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def update_catalog(catalog_path: Path, index_dir: Path, domain_name: str):
    """Regenerates or updates the batch_catalog.tsv based on all existing JSONL shards."""
    records = []
    for jsonl_file in sorted(index_dir.glob("*.jsonl")):
        if not jsonl_file.is_file():
            continue
        parts = jsonl_file.stem.split("_")
        # e.g. HRI_include_001
        group = parts[1] if len(parts) >= 3 else "default"
        file_bytes = jsonl_file.stat().st_size

        rec_count = 0
        first_id = ""
        last_id = ""
        topic_counts = {}

        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    rec_count += 1
                    cur_id = obj.get("id", "")
                    if not first_id:
                        first_id = cur_id
                    last_id = cur_id

                    for t in obj.get("topical_tags", []):
                        topic_counts[t] = topic_counts.get(t, 0) + 1
                except json.JSONDecodeError:
                    continue

        topic_summary = ",".join(f"{k}:{v}" for k, v in topic_counts.items())
        rel_path = f"01_rough_index/{jsonl_file.name}"
        records.append({
            "file": rel_path,
            "index": domain_name,
            "existing_group": group,
            "records": rec_count,
            "bytes": file_bytes,
            "existing_topics_and_counts": topic_summary,
            "first_id": first_id,
            "last_id": last_id,
            "drive_url": ""
        })

    fieldnames = [
        "file", "index", "existing_group", "records", "bytes",
        "existing_topics_and_counts", "first_id", "last_id", "drive_url"
    ]
    with open(catalog_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(records)


def ingest(domain_dir: Path, entry: dict, text_file: Path | None = None, pdf_file: Path | None = None):
    domain_name = domain_dir.name
    index_dir = domain_dir / "01_rough_index"
    raw_dir = domain_dir / "02_raw_materials"
    reading_dir = domain_dir / "03_deep_reading"

    index_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "TXT").mkdir(parents=True, exist_ok=True)
    (raw_dir / "PDF").mkdir(parents=True, exist_ok=True)
    reading_dir.mkdir(parents=True, exist_ok=True)

    locator_path = index_dir / "paper_locator.tsv"
    catalog_path = index_dir / "batch_catalog.tsv"

    paper_id = str(entry.get("id", "")).strip()
    if not paper_id:
        raise ValueError("Payload must contain a non-empty 'id' field.")

    # 1. De-duplication check
    existing_ids = load_locator_ids(locator_path)
    if paper_id in existing_ids:
        print(f"[SKIP] Paper ID '{paper_id}' already indexed in {locator_path.name}.")
        return

    # 2. Material handling
    text_rel_path = ""
    pdf_rel_path = ""
    if text_file and Path(text_file).exists():
        dest_txt = raw_dir / "TXT" / f"{paper_id}.txt"
        shutil.copy2(text_file, dest_txt)
        text_rel_path = f"02_raw_materials/TXT/{paper_id}.txt"

    if pdf_file and Path(pdf_file).exists():
        dest_pdf = raw_dir / "PDF" / f"{paper_id}.pdf"
        shutil.copy2(pdf_file, dest_pdf)
        pdf_rel_path = f"02_raw_materials/PDF/{paper_id}.pdf"

    # 3. Determine Group & Batch
    group = entry.get("decision", "include").lower()
    if group not in ["include", "pending", "exclude"]:
        group = "include"

    batch_file, batch_num = get_active_batch_file(index_dir, domain_name, group)
    line_number = count_lines(batch_file) + 1

    # 4. Append JSONL entry
    with open(batch_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # 5. Append Locator entry
    reading_rel_path = ""
    if (reading_dir / f"{paper_id}.json").exists():
        reading_rel_path = f"03_deep_reading/{paper_id}.json"

    file_exists = locator_path.exists()
    fieldnames = [
        "id", "title", "year", "index", "batch", "line",
        "text_path", "pdf_path", "reading_path", "batch_url", "text_url", "pdf_url", "reading_url"
    ]
    with open(locator_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        if not file_exists or locator_path.stat().st_size == 0:
            writer.writeheader()
        writer.writerow({
            "id": sanitize_tsv_field(paper_id),
            "title": sanitize_tsv_field(entry.get("title", "")),
            "year": sanitize_tsv_field(entry.get("year", "")),
            "index": sanitize_tsv_field(domain_name),
            "batch": sanitize_tsv_field(f"01_rough_index/{batch_file.name}"),
            "line": line_number,
            "text_path": sanitize_tsv_field(text_rel_path),
            "pdf_path": sanitize_tsv_field(pdf_rel_path),
            "reading_path": sanitize_tsv_field(reading_rel_path),
            "batch_url": "",
            "text_url": "",
            "pdf_url": "",
            "reading_url": ""
        })

    # 6. Update Catalog
    update_catalog(catalog_path, index_dir, domain_name)

    # 7. Claims extraction if provided
    claims = entry.get("author_claims", [])
    if claims and group == "include":
        claims_file = reading_dir / "claims.jsonl"
        with open(claims_file, "a", encoding="utf-8") as f:
            for idx, c in enumerate(claims, 1):
                claim_record = {
                    "paper_id": paper_id,
                    "claim_id": f"{paper_id}-C{idx}",
                    "claim_text": c,
                    "topical_tags": entry.get("topical_tags", [])
                }
                f.write(json.dumps(claim_record, ensure_ascii=False) + "\n")

    print(f"[SUCCESS] Ingested '{paper_id}' into {batch_file.name}:L{line_number}")


def main():
    parser = argparse.ArgumentParser(description="LitNexus Ingestion Helper")
    parser.add_argument("--domain", required=True, help="Path to domain directory (e.g., domains/HRI)")
    parser.add_argument("--entry", help="JSON string representing the bibliographic record")
    parser.add_argument("--json-file", help="Path to JSON file containing the record")
    parser.add_argument("--text-file", help="Path to extracted plaintext file")
    parser.add_argument("--pdf-file", help="Path to original PDF file")

    args = parser.parse_args()

    domain_path = Path(args.domain).resolve()
    if not domain_path.exists():
        print(f"Error: Target domain directory '{domain_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    if args.json_file:
        with open(args.json_file, "r", encoding="utf-8") as f:
            record = json.load(f)
    elif args.entry:
        record = json.loads(args.entry)
    else:
        print("Error: Either --entry or --json-file must be provided.", file=sys.stderr)
        sys.exit(1)

    ingest(
        domain_dir=domain_path,
        entry=record,
        text_file=Path(args.text_file) if args.text_file else None,
        pdf_file=Path(args.pdf_file) if args.pdf_file else None
    )


if __name__ == "__main__":
    main()

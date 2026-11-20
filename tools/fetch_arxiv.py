#!/usr/bin/env python3
"""
LitNexus ArXiv Harvesting & Ingestion Engine
============================================
Autonomous literature tracker powered by the official arXiv API.
Reads domain search criteria from 'domain_config.yaml', fetches newly published
preprints, performs de-duplication, and dispatches ingestion.

Reference Architectures:
- arxiv-daily (GitHub Actions cron polling)
- PaperQA2 (evidence metadata & citation grounding)

Usage:
  python tools/fetch_arxiv.py --domain domains/HRI --days 7 --max-results 30
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

# Local import from tools
import ingest_helper

ARXIV_API_BASE = "https://export.arxiv.org/api/query"
XML_NAMESPACE = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def load_yaml_config(config_path: Path) -> dict:
    """Lightweight, zero-external-dependency YAML reader for basic key-value and list blocks."""
    config = {
        "arxiv_categories": [],
        "venues": [],
        "keywords_mandatory": [],
        "keywords_optional": [],
        "keywords_exclude": []
    }
    if not config_path.exists():
        return config

    current_list_key = None
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line and not line.startswith("-"):
                key = line.split(":")[0].strip()
                if key in config:
                    current_list_key = key
                else:
                    current_list_key = None
            elif line.startswith("-") and current_list_key:
                val = line.lstrip("-").strip().strip('"').strip("'")
                if val:
                    config[current_list_key].append(val)
    return config


def construct_arxiv_query(config: dict) -> str:
    queries = []
    # 1. Categories (e.g. cat:cs.RO OR cat:cs.AI)
    cats = config.get("arxiv_categories", [])
    if cats:
        cat_query = " OR ".join(f"cat:{c.strip()}" for c in cats)
        queries.append(f"({cat_query})")

    # 2. Mandatory keywords (in title or abstract)
    mandatory = config.get("keywords_mandatory", [])
    for kw in mandatory:
        kw = kw.strip()
        if kw:
            queries.append(f'(ti:"{kw}" OR abs:"{kw}")')

    if not queries:
        return "cat:cs.RO OR cat:cs.AI"

    return " AND ".join(queries)


def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def fetch_arxiv_records(query_str: str, max_results: int = 50) -> list[dict]:
    params = {
        "search_query": query_str,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    url = f"{ARXIV_API_BASE}?{urllib.parse.urlencode(params)}"
    print(f"[*] Querying arXiv API: {url}")

    req = urllib.request.Request(url, headers={"User-Agent": "LitNexus-Research-Harvester/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_data = response.read()
    except Exception as e:
        print(f"[ERROR] Failed to connect to arXiv API: {e}", file=sys.stderr)
        return []

    root = ET.fromstring(xml_data)
    entries = []

    for entry in root.findall("atom:entry", XML_NAMESPACE):
        id_elem = entry.find("atom:id", XML_NAMESPACE)
        raw_id = id_elem.text.strip() if id_elem is not None else ""
        # Extract canonical arXiv ID (e.g., '2405.16021' from 'http://arxiv.org/abs/2405.16021v1')
        match = re.search(r"abs/([0-9]+\.[0-9]+)(v[0-9]+)?", raw_id)
        arxiv_id = match.group(1) if match else raw_id.split("/")[-1]

        title_elem = entry.find("atom:title", XML_NAMESPACE)
        title = clean_text(title_elem.text) if title_elem is not None else ""

        summary_elem = entry.find("atom:summary", XML_NAMESPACE)
        summary = clean_text(summary_elem.text) if summary_elem is not None else ""

        published_elem = entry.find("atom:published", XML_NAMESPACE)
        pub_date = published_elem.text[:10] if published_elem is not None else ""
        year = int(pub_date[:4]) if pub_date else datetime.datetime.now().year

        authors = []
        for author in entry.findall("atom:author", XML_NAMESPACE):
            name = author.find("atom:name", XML_NAMESPACE)
            if name is not None and name.text:
                authors.append(clean_text(name.text))

        # Links (PDF / HTML)
        pdf_url = ""
        for link in entry.findall("atom:link", XML_NAMESPACE):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href", "")

        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        entries.append({
            "id": arxiv_id,
            "title": title,
            "authors": authors,
            "year": year,
            "published_date": pub_date,
            "venue": "arXiv",
            "abstract_excerpt": summary,
            "author_claims": [
                f"Core finding extracted from abstract: {summary[:180]}..."
            ],
            "conclusion_excerpt": "Automated ingestion via arXiv API. Pending deep analysis.",
            "topical_tags": ["Automated Ingestion", "arXiv Preprint"],
            "leads": [f"Trace primary citations on arXiv for {arxiv_id}"],
            "decision": "pending",  # Incoming papers default to 'pending' for human/agent review
            "pdf_url": pdf_url
        })

    return entries


def harvest_for_domain(domain_dir: Path, max_results: int = 30):
    config_file = domain_dir / "domain_config.yaml"
    config = load_yaml_config(config_file)
    query_str = construct_arxiv_query(config)

    print(f"[*] Starting harvest for domain: '{domain_dir.name}'")
    print(f"[*] Query String: {query_str}")

    records = fetch_arxiv_records(query_str, max_results=max_results)
    print(f"[*] Retrieved {len(records)} candidate preprints from arXiv.")

    locator_path = domain_dir / "01_rough_index" / "paper_locator.tsv"
    if not locator_path.exists():
        locator_path = domain_dir / "01_粗读索引" / "论文定位.tsv"

    existing_ids = ingest_helper.load_locator_ids(locator_path)

    new_count = 0
    skipped_count = 0

    for rec in records:
        pid = rec["id"]
        if pid in existing_ids:
            skipped_count += 1
            continue

        # Ingest new record
        try:
            ingest_helper.ingest(domain_dir=domain_dir, entry=rec)
            existing_ids.add(pid)
            new_count += 1
        except Exception as e:
            print(f"[ERROR] Failed to ingest {pid}: {e}", file=sys.stderr)

    print(f"\n[✓] Harvest completed for '{domain_dir.name}': {new_count} newly ingested, {skipped_count} skipped as duplicates.")


def main():
    parser = argparse.ArgumentParser(description="LitNexus arXiv Automated Harvester")
    parser.add_argument("--domain", required=True, help="Path to domain directory (e.g. domains/HRI)")
    parser.add_argument("--max-results", type=int, default=25, help="Maximum preprints to inspect")
    args = parser.parse_args()

    domain_path = Path(args.domain).resolve()
    if not domain_path.exists():
        print(f"Error: Target domain '{domain_path}' not found.", file=sys.stderr)
        sys.exit(1)

    harvest_for_domain(domain_path, max_results=args.max_results)


if __name__ == "__main__":
    main()

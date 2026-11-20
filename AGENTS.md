# LitNexus: Operational Directive for Autonomous Research Agents

> **Document Classification**: System Specification & Operational Protocol  
> **Target Audience**: Autonomous Language Model Agents, Research Swarms, Computational Assistants  
> **Language Standard**: Formal Academic English

---

## 1. System Mission and Conceptual Foundations

`LitNexus` is an agent-native literature repository engineered to overcome context-window saturation and citation hallucination in large language models. Unlike conventional bibliographic managers designed exclusively for human perception (e.g., Zotero, Mendeley), `LitNexus` provides a **hierarchically partitioned, progressive-disclosure substrate** optimized for programmatic navigation, systematic literature mapping, and automated evidence synthesis.

### Core Architectural Axiom: Hierarchical Information Scaling
A research corpus exceeding thousands of articles cannot be naively injected into a model's active working memory. `LitNexus` organizes scholarly assets across four sequential exploration strata:
1. **Catalog Layer (`01_rough_index/batch_catalog.tsv`)**: Macroscopic thematic clustering and partition inventory (~1–2k tokens).
2. **Batch Index Layer (`01_rough_index/*.jsonl`)**: Fixed-size partition shards (~48–52 KiB per file), encapsulating structured bibliographic attributes, author claims, and thematic descriptors.
3. **Locator Index Layer (`01_rough_index/paper_locator.tsv`)**: Deterministic $O(1)$ routing mapping unique document identifiers directly to physical and cloud storage pointers.
4. **Primary and Deep Evidence Layers (`02_raw_materials/`, `03_deep_reading/`)**: Extracted plaintext corpora, raw PDF binaries, and formalized thesis-claim graphs (`claims.jsonl`).

---

## 2. Invariant Rules of Engagement for Agents

When operating within any domain sub-repository, you must adhere strictly to the following operational invariants:

1. **Context Economy & Batch Integrity**:
   - Never ingest the entire `paper_locator.tsv` or unpartitioned catalogs into working memory.
   - Filter or stream search candidates by querying specific columns (`id`, `title`, `year`).
   - Maintain JSONL batch partitions strictly within the **48 KiB – 52 KiB** boundary. Never combine batches into monolithic files.

2. **Deterministic Tool Invocation for Ingestion**:
   - Never modify `.tsv` files or append `.jsonl` lines using unrestricted raw text editing tools.
   - Always execute updates through `tools/ingest_helper.py` to ensure atomic, delimiter-safe, and collision-free transactions.

3. **Verifiable Claim Attribution**:
   - When executing deep reading (`03_deep_reading/`), extracted claims must be anchored to verifiable page numbers, section headers, or verbatim quotes.
   - Paraphrasing must preserve the epistemic uncertainty (hedging, scope limitations) explicitly articulated by the original authors.

4. **Preservation of Lexical and Orthographic Precision**:
   - Maintain original nomenclature, mathematical notation, and multilingual terminology (e.g., English, Japanese) exactly as published.
   - Do not unilaterally reclassify, re-score, or truncate existing bibliographic records unless executing an explicit deduplication or remediation instruction.

---

## 3. Protocol for Autonomous Literature Ingestion

When tasked with expanding a domain or updating tracking feeds, execute the following state machine:

```
[Query Source] ──> [Filter & De-duplicate] ──> [Extract Core Signals] ──> [Batch Ingestion via Tool] ──> [Synthesize Claims]
```

### Step 3.1: Source Exploration
- Consult the target domain's configuration: `domains/<domain_name>/domain_config.yaml`.
- Query peer-reviewed proceedings, preprint servers (e.g., arXiv API, Semantic Scholar API), or configured RSS feeds matching the specified thematic filters and publication venues.

### Step 3.2: De-duplication and Eligibility Triage
- Extract document identity vectors: Canonical DOI, arXiv Identifier, or normalized title string.
- Check existence against `domains/<domain_name>/01_rough_index/paper_locator.tsv`. If an entry exists, skip or switch to deep-reading enrichment mode.
- Evaluate the document against the inclusion/exclusion criteria codified in `domain_config.yaml`:
  - `include`: Directly contributes to core conceptual or empirical mechanisms.
  - `pending`: Borderline relevance; preserved for secondary review.
  - `exclude`: Peripheral or out-of-scope; recorded to prevent redundant re-indexing.

### Step 3.3: Systematic Metadata and Claim Extraction
Generate a structured JSON entity adhering strictly to the schema:
```json
{
  "id": "<Canonical_ID_or_ArXiv_Tag>",
  "title": "<Verbatim Article Title>",
  "authors": ["<Author 1>", "<Author 2>"],
  "year": 2026,
  "venue": "<Conference or Journal Name>",
  "abstract_excerpt": "<Author Abstract>",
  "author_claims": [
    "<Primary assertion or empirical finding>",
    "<Secondary theoretical contribution>"
  ],
  "conclusion_excerpt": "<Key takeaway from concluding section>",
  "topical_tags": ["<Taxonomy_Category_1>", "<Taxonomy_Category_2>"],
  "leads": ["<Emergent question or referenced literature to track>"],
  "decision": "include"
}
```

### Step 3.4: Committal via Tooling
Invoke the deterministic ingestion engine:
```bash
python tools/ingest_helper.py \
  --domain domains/<domain_name> \
  --entry '<JSON_PAYLOAD>' \
  --text-file path/to/extracted.txt \
  --pdf-file path/to/raw.pdf
```

---

## 4. Query & Synthesis Protocol (How to Serve Human Researchers)

When a human user requests an academic survey, evidence lookup, or literature verification:

1. **Step 1 (Thematic Scoping)**: Read `domains/<domain_name>/01_rough_index/批次目录.tsv` to identify the most densely populated batches relevant to the target topic.
2. **Step 2 (Batch Reading)**: Load the corresponding single `.jsonl` batch file into context. Assess candidate papers based on `author_claims` and `conclusion_excerpt`.
3. **Step 3 (Pinpoint Retrieval)**: For high-priority papers, query `01_rough_index/论文定位.tsv` to obtain local text paths (`02_raw_materials/TXT/...`) or cloud URLs.
4. **Step 4 (Deep Synthesis)**: Extract specific empirical proof points, contrast opposing hypotheses, and synthesize findings with exact bibliographic citations.

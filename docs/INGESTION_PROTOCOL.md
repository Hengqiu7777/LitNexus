# LitNexus Literature Ingestion and Synthesis Protocol

> **Document Class**: Standard Operating Procedure (SOP)  
> **Target Role**: Autonomous Literature Ingestion Agents  
> **Language Standard**: Academic English

---

## 1. Overview and Operational Objective

This protocol governs the automated discovery, eligibility triage, structural extraction, partition allocation, and claim synthesis of scholarly papers ingested into the `LitNexus` ecosystem. Compliance ensures cross-domain consistency and long-term repository integrity.

---

## 2. Phase-by-Phase Execution Pipeline

```
┌─────────────────────────┐
│ 1. Discovery & Query   │ ── arXiv API / Semantic Scholar / DBLP / Crossref
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 2. De-duplication Gate  │ ── Canonical DOI / arXiv ID lookup against paper_locator.tsv
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 3. Two-Stage Triage     │ ── Stage I: Title/Keywords; Stage II: Abstract & Contributions
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 4. Structural Extract   │ ── Plaintext parsing, claim distillation, topical tagging
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 5. Partition Sharding   │ ── Commit via tools/ingest_helper.py (Enforces 48-52 KiB rule)
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│ 6. Claims Synthesis    │ ── Append falsifiable statements to 03_deep_reading/claims.jsonl
└─────────────────────────┘
```

---

## 3. Detailed Stage Specifications

### Stage 1: Discovery & Algorithmic Search
Agents must parse `domain_config.yaml` to identify:
- Primary preprint and publication venues (e.g., `cs.RO`, `cs.AI`, `cs.HC`, `ACM/IEEE HRI`, `RSS`, `CoRL`, `ICRA`).
- Mandatory keyword conjunctions and exclusions.
- Temporal horizons (e.g., papers published within the preceding $N$ days).

### Stage 2: Deterministic De-Duplication
Prior to processing, compute the canonical paper identifier:
- Prefer version-stripped arXiv identifier (e.g., `2405.16021`).
- Fallback to standardized DOI or normalized title hash (`SHA-256(lowercase(alphanumeric_only(title)))`).
- Execute a query on `domains/<domain_name>/01_rough_index/paper_locator.tsv`. If an exact match is identified, terminate execution for this candidate.

### Stage 3: Two-Stage Epistemic Triage
1. **Stage I (Rapid Heuristic Filtering)**:
   - Match against explicit positive/negative regex vectors defined in `domain_config.yaml`.
   - If clear divergence is established, assign decision `exclude` and record a concise rationale (`exclusion_reason`).
2. **Stage II (Methodological Rigor and Relevance Assessment)**:
   - Read author introduction and conclusion.
   - Evaluate whether the empirical or theoretical contributions advance the mechanisms defined in `00_INDEX.md`.
   - Assign classification:
     - `include`: Essential core literature directly informing domain mechanisms.
     - `pending`: Methodologically sound or adjacent works requiring human verification.
     - `exclude`: Off-topic or low-relevance manuscripts.

### Stage 4: Structural Extraction Schema
The agent must structure the extracted metadata into an immutable JSON document adhering to the following schema:

```json
{
  "id": "2405.16021",
  "title": "Robotic Social Navigation via Multi-Modal Foundation Models",
  "authors": ["Jane Doe", "John Smith"],
  "year": 2026,
  "venue": "IEEE Transactions on Robotics",
  "doi": "10.1109/TRO.2026.012345",
  "abstract_excerpt": "Direct verbatim excerpt of the primary abstract text...",
  "author_claims": [
    "Zero-shot vision-language-action policies reduce collision rates by 42% in crowded dynamic corridors.",
    "Explicit social compliance loss functions prevent agent freezing in bottleneck doorways."
  ],
  "conclusion_excerpt": "Verbatim excerpt of primary claims and recognized empirical limitations...",
  "topical_tags": ["Social Navigation", "VLA Models", "Shared Control"],
  "leads": ["Examine benchmark dataset proposed in Section 4.2 for transferability"],
  "decision": "include"
}
```

### Stage 5: Atomic Partition Allocation
Agents must never manipulate TSV/JSONL files directly with general string replacement. Ingestion must be dispatched via the system utility:

```bash
python tools/ingest_helper.py \
  --domain "domains/<domain_name>" \
  --entry '<JSON_PAYLOAD>' \
  --text-path "path/to/extracted.txt" \
  --pdf-path "path/to/source.pdf"
```

The utility automatically computes partition boundaries, increments batch indices when the 52 KiB ceiling is reached, and performs atomic row appends on `paper_locator.tsv` and `batch_catalog.tsv`.

### Stage 6: Claims Synthesis (For `include` Decisions)
For any paper triaged as `include`, the agent must distill at least one atomic, falsifiable claim into `domains/<domain_name>/03_deep_reading/claims.jsonl`:

```json
{
  "paper_id": "2405.16021",
  "claim_id": "2405.16021-C1",
  "claim_text": "Zero-shot VLA policies improve social navigation compliance in dense crowds relative to classical costmaps.",
  "evidence_type": "empirical_benchmark",
  "evidence_location": "Section 5.3, Table 2",
  "confidence": "high",
  "theoretical_mechanism": "Semantic Affordance Mapping"
}
```

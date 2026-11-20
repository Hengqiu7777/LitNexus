# LitNexus Architecture Specification

> **Document Class**: Technical Architecture and System Engineering Design  
> **Status**: Approved Foundation Specification  
> **Language Standard**: Academic English

---

## 1. Abstract and Theoretical Foundations

Large Language Models (LLMs) deployed as autonomous research assistants face a fundamental information-retrieval dilemma when interacting with expansive scholarly corpuses: the **Context Saturation Paradox**. While modern transformer architectures feature expanding context windows (e.g., $10^5$ to $10^6$ tokens), naive retrieval or unpartitioned corpus injection causes pronounced degradation in reasoning acuity, heightened latency, and susceptibility to the "lost-in-the-middle" phenomenon.

`LitNexus` resolves this challenge through **Stratified Knowledge Sharding**. By decomposing bibliographic repositories into deterministic, fixed-entropy batch partitions alongside an orthogonal dual-index routing plane, `LitNexus` guarantees that an agent can navigate thousands of scholarly works with $O(1)$ lookup complexity and sub-saturation context consumption.

---

## 2. Stratified Repository Topology

Each sub-repository ("Domain") under `domains/<domain_name>` represents an autonomous knowledge namespace adhering to a rigid 4-tier lifecycle structure:

```
domains/<domain_name>/
├── 00_INDEX.md                        # Domain boundary charter and taxonomy definitions
├── domain_config.yaml                 # Algorithmic scraping targets, keywords, and triage rules
├── 01_rough_index/                    # Stratified Index Plane
│   ├── batch_catalog.tsv              # Macroscopic batch index: metrics, themes, and cloud pointers
│   ├── paper_locator.tsv              # Deterministic routing locator (ID, paths, URLs)
│   └── <domain>_<group>_###.jsonl     # Fixed-entropy batch shards (~48-52 KiB per partition)
├── 02_raw_materials/                  # Primary Scholarly Data
│   ├── TXT/                           # Extracted high-density ASCII/UTF-8 plaintext
│   ├── PDF/                           # Original binary artifacts (or symbolic cloud stubs)
│   └── supplements/                   # Secondary citations, benchmark logs, and datasets
├── 03_deep_reading/                   # Epistemic Claim Synthesis
│   ├── claims.jsonl                   # Atomic assertions, empirical proofs, and epistemic qualifications
│   ├── thematic_navigation/           # Synthesized taxonomy overviews and conceptual maps
│   └── close_readings/                # Per-document analytical monographs
└── 04_archive/                        # Historical Provenance
    ├── raw_metadata.sqlite            # Compressed relational audit log (SQLite)
    └── snapshots.zip                  # Immutable historical code snapshots and artifacts
```

---

## 3. Sharding and Partitioning Algorithm

### 3.1 Partition Threshold Sizing ($\Delta B$)
A critical innovation of `LitNexus` is the explicit enforcement of partition granularity:
$$\Delta B \approx 48 \text{ KiB} \pm 4 \text{ KiB}$$

**Theoretical Justification**:
- An average structured JSONL bibliographic record consumes approximately $2.5 \text{ KiB}$.
- A partition of size $\Delta B \approx 50 \text{ KiB}$ encapsulates precisely $18 \text{ to } 22$ papers.
- In standard token representations (BPE), $50 \text{ KiB}$ corresponds to $\sim 11,000 \text{ to } 14,000$ tokens.
- This token volume fits comfortably within a single agent prompt invocation without exceeding standard reasoning margins, allowing the agent to evaluate multi-paper comparative hypotheses simultaneously without triggering cognitive degradation.

### 3.2 Partition Lifecycle and Transition Rules
1. Records are categorized by decision groups: `include`, `pending`, and `exclude`.
2. When a new record is ingested into group $G$, the active partition file `<domain>_<G>_<NNN>.jsonl` is checked.
3. If $\text{Size}(\text{ActivePartition}) + \text{Size}(\text{NewRecord}) > \Delta B_{\max}$ (52 KiB):
   - The active partition is marked immutable and closed.
   - Index $NNN \leftarrow NNN + 1$ is initialized.
   - The entry is appended as line 1 of the new shard.
4. `batch_catalog.tsv` is updated with aggregate topic distributions, total record count, byte volume, and start/end identifiers.

---

## 4. Hybrid Storage Model (Git vs. External Object Storage)

Scholarly corpora exhibit extreme divergence in data density:
- **High-Density Symbolic Assets**: JSONL indices, TSV mappings, extracted plaintext, and Markdown synthesis files have high semantic value per byte and must be versioned under Git.
- **Low-Density Binary Assets**: Multi-megabyte PDF binaries, SQLite snapshot dumps, and dataset tars rapidly exceed Git hosting thresholds (e.g., GitHub 1–2 GB recommendations).

### Hybrid Decoupling Scheme:
1. **Tracked in Git**:
   - `01_rough_index/` (All `.tsv` and `.jsonl` files)
   - `02_raw_materials/TXT/` (Plaintext extractions)
   - `03_deep_reading/` (All analytical syntheses and `claims.jsonl`)
   - Configuration files, documentation, and tools
2. **Externalized Object Storage (Google Drive / S3 / Lab NAS)**:
   - `02_raw_materials/PDF/`
   - `04_archive/` (SQLite snapshots, large archives)
3. **Linking Invariant**:
   - Every binary offloaded to external object storage is registered in `paper_locator.tsv` and `batch_catalog.tsv` under immutable content-addressed or cloud uniform resource identifiers (`cloud_url`, `pdf_url`).

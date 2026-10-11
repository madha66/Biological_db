# PathWeave — Bundled Dataset Verification & Statistics

## 1. Summary of Bundled Datasets
- **Primary Interaction Dataset**: `sample_interactions.csv` (5100 bytes, SHA256: `399809b1395231ac...`)
- **Inflammation Classification Dataset**: `inflammation_tags.json` (3344 bytes, SHA256: `fb6b6fb598bf9624...`)

## 2. Interaction Dataset (`sample_interactions.csv`)
- **Total Interaction Records**: 110
- **Total Attributes (Columns)**: 5 (`rna_id, rna_type, target_gene, evidence, source_db`)
- **Unique Regulatory RNAs**: 27
- **Unique Target Genes**: 41
- **Unique Biological Pairs (RNA–Target)**: 110
- **Duplicate Records (Identical Row)**: 0
- **Biological Pairs with Multiple Records**: 0

### RNA Molecular Class Breakdown
| RNA Class | Record Count | Percentage |
|---|---|---|
| miRNA | 63 | 57.3% |
| lncRNA | 36 | 32.7% |
| circRNA | 11 | 10.0% |

### Evidence Category Breakdown
| Evidence Level | Record Count | Percentage | Weight in Config |
|---|---|---|---|
| validated | 67 | 60.9% | 1.0 |
| predicted | 43 | 39.1% | 0.4 |

### Source Database Breakdown
| Upstream Repository | Record Count | Percentage | Target Types |
|---|---|---|---|
| miRTarBase | 43 | 39.1% | Mixed |
| LncRNA2Target | 36 | 32.7% | Mixed |
| starBase | 20 | 18.2% | Mixed |
| CircInteractome | 11 | 10.0% | Mixed |

### Biological Pairs with Multiple Evidence Records
The following biological pairs appear under more than one record due to differing evidence levels or source databases:
| RNA Identifier | Target Gene | Records | Evidence Levels | Sources |
|---|---|---|---|---|

## 3. Data Integrity & Missing Values
- **Missing values**: 0 in all columns.
- **Identifier formats**: Standard miRBase (`hsa-miR-*`), circBase (`hsa_circ_*`), and HGNC uppercase gene symbols (`TP53`, `TNF`, etc.).
- **Provenance Limitations**: The dataset is a static 110-line seed curation created during initial commit (`a6a439b`). Upstream database dump dates and release versioning tags are omitted in the file metadata.
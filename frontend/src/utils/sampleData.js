/**
 * Sample gene sets for the "Load Example" feature.
 */
export const SAMPLE_GENE_SETS = [
  {
    name: 'Cancer-related genes',
    organism: 'hsa',
    genes: 'TP53, BRCA1, EGFR, AKT1, PTEN, MYC',
    description: 'Well-known tumor suppressors and oncogenes frequently studied in cancer biology.',
  },
  {
    name: 'Immune signaling genes',
    organism: 'hsa',
    genes: 'TNF, IL6, STAT3, JAK2, NFKB1, IFNG, IL10, CD4',
    description: 'Key genes involved in immune response and cytokine signaling pathways.',
  },
  {
    name: 'Mixed (with invalid genes)',
    organism: 'hsa',
    genes: 'TP53, BRCA1, FAKEGENE1, EGFR, NOTREAL99, PTEN',
    description: 'Demonstrates partial-failure handling — two genes are intentionally invalid.',
  },
];

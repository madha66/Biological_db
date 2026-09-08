export default function AboutPage() {
  return (
    <div className="content-prose">
      <h2>About KEGGPathRank</h2>
      <p>
        KEGGPathRank is a Python-based system for ranking biologically relevant KEGG
        pathways from user-submitted gene sets. It bridges the gap between raw gene lists
        and biological pathway interpretation using rigorous statistical methods.
      </p>

      <h2>Methodology</h2>

      <h3>1. Gene Input & Preprocessing</h3>
      <p>
        Users submit a set of gene symbols (e.g., TP53, BRCA1, EGFR). The system trims whitespace,
        normalizes casing for KEGG lookups, and removes duplicates while preserving the original
        casing for display. Genes that cannot be mapped in KEGG are reported separately and do not
        block the analysis.
      </p>

      <h3>2. KEGG Pathway Mapping</h3>
      <p>
        Each valid gene is resolved to a KEGG gene ID using the KEGG REST API's <code>/find</code>
        endpoint, then mapped to all annotated pathways via the <code>/link/pathway</code> endpoint.
        This builds a bidirectional mapping between genes and pathways.
      </p>

      <h3>3. Pathway Representation Score</h3>
      <div className="formula-box">
        Pathway Score = (Input genes in pathway) / (Total valid input genes)
      </div>
      <p>
        This score measures how much of the user's gene set overlaps with a given pathway.
        A score of 1.0 means every valid input gene maps to that pathway. Note: representation
        alone does not imply statistical significance.
      </p>

      <h3>4. Fisher's Exact Test</h3>
      <p>
        For each pathway, a 2×2 contingency table is constructed:
      </p>
      <div className="formula-box">
        {'                  In pathway    Not in pathway\n'}
        {'Input genes          a               b\n'}
        {'Background genes     c               d'}
      </div>
      <p>
        Fisher's exact test (one-sided, testing for overrepresentation) computes the probability
        of observing at least as many input genes in the pathway as we did, under the null hypothesis
        of no association. The background universe is defined as the union of all genes across all
        KEGG pathways for the selected organism.
      </p>

      <h3>5. Benjamini–Hochberg FDR Correction</h3>
      <p>
        When testing many pathways simultaneously, the chance of false positives increases.
        The Benjamini–Hochberg procedure controls the false discovery rate (FDR) — the expected
        proportion of false discoveries among the pathways called significant. We apply this
        correction to all raw p-values and report adjusted p-values throughout.
      </p>

      <h3>6. Ranking Score</h3>
      <div className="formula-box">
        Ranking Score = Pathway Score × −log₁₀(Adjusted p-value)
      </div>
      <p>
        This formula combines representation (how many input genes overlap with the pathway)
        and statistical significance (how unlikely that overlap is by chance). A pathway with both
        high representation <em>and</em> strong statistical enrichment will rank highest. Pathways
        are sorted by this score in descending order.
      </p>

      <h3>7. Interpretation Guidelines</h3>
      <p>
        Results indicate which pathways are <strong>significantly enriched</strong> or
        <strong>strongly represented</strong> in the submitted gene set. They do <em>not</em>
        imply that a pathway causes any specific biological condition. A high ranking score
        means the pathway is <strong>associated with</strong> the submitted genes in a
        statistically meaningful way.
      </p>
      <p>
        The distinction between representation (raw gene overlap) and statistical enrichment
        (adjusted p-value) is important: a pathway can contain many of your input genes but not
        be statistically significant if it is a very large pathway (many genes overall), and
        vice versa.
      </p>

      <h2>Technology Stack</h2>
      <p>
        <strong>Backend:</strong> Python 3.11+, FastAPI, Pandas, SciPy, statsmodels<br />
        <strong>Frontend:</strong> React + Vite, Recharts<br />
        <strong>Data Source:</strong> KEGG REST API (https://rest.kegg.jp)<br />
        <strong>Visualization:</strong> Recharts (interactive), Matplotlib (static/reports)
      </p>

      <h2>Team</h2>
      <p>
        Madhan Kumar Kumaran — 23BCB0065<br />
        Sanjay Jaishankar — 23BCB0078<br />
        Sampanna Shalya — 23BCB0141
      </p>

      <h2>Limitations</h2>
      <p>
        • The background gene universe is an approximation (union of all pathway-annotated genes)
        rather than the complete genome. See <code>docs/LIMITATIONS.md</code> for details.<br />
        • KEGG pathway annotations may not be fully current; results depend on KEGG's database state.<br />
        • Gene symbols can be ambiguous across organisms — always select the correct organism.<br />
        • Overlapping pathways (shared genes) are tested independently; pathway-level correlations
        are not modeled.
      </p>
    </div>
  );
}

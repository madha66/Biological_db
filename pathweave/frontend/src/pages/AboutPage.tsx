import { motion } from 'framer-motion';

const sections = [
  {
    id: 'overview',
    title: 'What is PathWeave?',
    content: `PathWeave is a bioinformatics tool that expands a seed gene into a regulatory RNA neighborhood — following miRNA, lncRNA, and circRNA interactions — then maps the resulting gene set to KEGG pathways and ranks them by a multi-component enrichment score. The goal is to reveal which inflammatory pathways are driven not just by the seed gene itself, but by its broader RNA regulatory context.`,
  },
  {
    id: 'scoring',
    title: 'Scoring method',
    content: null,
    formula: true,
  },
  {
    id: 'evidence',
    title: 'Evidence weighting',
    content: `Each RNA–gene interaction is classified as validated (from miRTarBase, LncRNA2Target — experimentally confirmed) or predicted (from starBase/ENCORI, CircInteractome — computationally inferred). Validated interactions receive a base weight of 1.0; predicted interactions receive 0.4. When multiple independent RNAs support the same gene, the weight is boosted logarithmically:

w_g = base_evidence × (1 + log₂(n_independent_RNAs))

This rewards convergent evidence without double-counting RNAs that appear multiple times.`,
  },
  {
    id: 'null',
    title: 'Null model',
    content: `To measure how much the RNA layer adds beyond the seed gene's own pathways, PathWeave runs N iterations (default 200) of the same pipeline on random seeds of equal size. The resulting top-score distribution forms the null. The real seed's top score is compared against this distribution to compute an empirical p-value.

PathWeave also compares results with and without the seed gene, showing the RNA neighborhood's independent contribution.`,
  },
  {
    id: 'limitations',
    title: 'Known limitations',
    content: null,
    limitations: true,
  },
  {
    id: 'context',
    title: 'Relation to existing tools',
    content: `The individual components of PathWeave exist in other tools: pathway enrichment in Enrichr and DAVID, RNA-target databases in miRTarBase and starBase, inflammation classification in manually curated resources. PathWeave's contribution is the integration: weighting genes by RNA evidence before enrichment, applying a composite score, running a null model control, and classifying inflammation triggers in a single interactive workflow.`,
  },
];

const LIMITATIONS = [
  'The bundled demo dataset covers only a curated subset of interactions for TNF, IL6, NFKB1, TP53, and STAT3. Real-world usage requires plugging in full miRTarBase / ENCORI exports.',
  'KEGG pathway gene lists are organism-specific and reflect the current KEGG snapshot; results may differ as KEGG is updated.',
  'The null model uses random gene draws from KEGG\'s universe, which may not be the ideal background for all experiments.',
  'circRNA interactions are predominantly computational predictions — treat circRNA-supported pathways with extra caution.',
  'The composite score weighting (0.4/0.2/0.2/0.2) is configurable but not empirically validated against a benchmark dataset.',
  'The inflammation classification is keyword- and ID-based; edge cases and cross-category pathways may be misclassified.',
];

function FormulaSection() {
  return (
    <div className="space-y-4">
      <p className="text-slate-400 leading-relaxed">
        PathWeave uses a four-component composite score to rank pathways:
      </p>

      <div className="bg-bg-tertiary rounded-xl p-5 border border-border-subtle font-mono text-sm space-y-3">
        <div className="text-brand-teal">
          <span className="text-slate-400">Gene weight:</span>{' '}
          w_g = base × (1 + log₂(n_RNAs))
        </div>
        <div className="text-slate-500 text-xs">
          where base = 1.0 (validated) or 0.4 (predicted)
        </div>
        <div className="h-px bg-border-subtle" />
        <div>
          <span className="text-slate-400">Per pathway: Fisher exact test (one-sided)</span>
        </div>
        <div className="text-slate-400 text-xs pl-4 space-y-1">
          <div>a = |query ∩ pathway|   (in both)</div>
          <div>b = |query \ pathway|   (in query, not pathway)</div>
          <div>c = |pathway \ query|   (in pathway, not query)</div>
          <div>d = background − a − b − c</div>
        </div>
        <div className="h-px bg-border-subtle" />
        <div className="text-amber-400">
          FDR = Benjamini–Hochberg correction across all pathways
        </div>
        <div className="h-px bg-border-subtle" />
        <div className="text-brand-violet">
          <span className="text-slate-400">Composite score:</span>
        </div>
        <div className="pl-4 text-slate-300 space-y-1">
          <div>S = 0.4 · norm(−log₁₀ FDR)</div>
          <div>  + 0.2 · norm(log₂ odds ratio)</div>
          <div>  + 0.2 · norm(coverage)</div>
          <div>  + 0.2 · norm(evidence strength)</div>
        </div>
        <div className="text-slate-500 text-xs">
          norm() = min-max normalisation across all tested pathways
        </div>
        <div className="h-px bg-border-subtle" />
        <div className="text-slate-400">
          evidence_strength = Σ w_g(overlap) / Σ w_g(all)
        </div>
        <div className="h-px bg-border-subtle" />
        <div className="text-slate-400">
          Redundancy: cluster pathways with Jaccard(gene sets) ≥ 0.5; keep highest-scoring representative
        </div>
      </div>

      <p className="text-slate-500 text-sm">
        Weights are configurable in the Advanced options panel. The defaults (0.4 / 0.2 / 0.2 / 0.2) prioritise statistical significance while incorporating biological context.
      </p>
    </div>
  );
}

export function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-12 space-y-12">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-violet/10 border border-brand-violet/20 text-brand-violet text-xs font-semibold mb-4 tracking-wider uppercase">
          Methods & About
        </div>
        <h1 className="text-4xl font-bold text-white tracking-tight mb-3">
          How <span className="gradient-text">PathWeave</span> works
        </h1>
        <p className="text-lg text-slate-400">
          Transparent methods, honest limitations, and a clear description of what PathWeave adds beyond individual tools.
        </p>
      </motion.div>

      {sections.map((section, i) => (
        <motion.section
          key={section.id}
          id={section.id}
          className="space-y-4"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.08 }}
        >
          <h2 className="text-xl font-semibold text-white border-b border-border-subtle pb-3">
            {section.title}
          </h2>

          {section.formula ? (
            <FormulaSection />
          ) : section.limitations ? (
            <ul className="space-y-3">
              {LIMITATIONS.map((lim, j) => (
                <li key={j} className="flex gap-3 text-sm text-slate-400">
                  <span className="text-amber-400 flex-shrink-0 mt-0.5">⚠</span>
                  {lim}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-400 leading-relaxed whitespace-pre-line">{section.content}</p>
          )}
        </motion.section>
      ))}

      {/* Data sources */}
      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        <h2 className="text-xl font-semibold text-white border-b border-border-subtle pb-3 mb-4">
          Data sources & integration
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { name: 'KEGG', desc: 'Pathway gene sets and organism backgrounds', url: 'https://www.kegg.jp', status: 'Live API' },
            { name: 'miRTarBase', desc: 'Validated miRNA–target interactions', url: 'https://mirtarbase.cuhk.edu.cn', status: 'Bundled demo' },
            { name: 'starBase / ENCORI', desc: 'Predicted RNA interactions', url: 'https://starbase.sysu.edu.cn', status: 'Bundled demo' },
            { name: 'LncRNA2Target', desc: 'lncRNA–gene regulatory data', url: 'http://lncrna2target.ouc.edu.cn', status: 'Bundled demo' },
            { name: 'CircInteractome', desc: 'circRNA interaction predictions', url: 'https://circinteractome.nia.nih.gov', status: 'Bundled demo' },
          ].map((src) => (
            <a
              key={src.name}
              href={src.url}
              target="_blank"
              rel="noopener noreferrer"
              className="glass-card p-4 hover:border-brand-teal/30 transition-all group"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-semibold text-white group-hover:text-brand-teal transition-colors">{src.name}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{src.desc}</p>
                </div>
                <span className={`badge text-[10px] ${src.status === 'Live API' ? 'bg-green-400/10 border-green-400/20 text-green-400' : 'bg-slate-400/10 border-slate-400/20 text-slate-400'}`}>
                  {src.status}
                </span>
              </div>
            </a>
          ))}
        </div>
      </motion.section>
    </div>
  );
}

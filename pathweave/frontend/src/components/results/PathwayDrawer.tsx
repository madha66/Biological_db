import { motion, AnimatePresence } from 'framer-motion';
import { X, ExternalLink, Copy } from 'lucide-react';
import { toast } from 'sonner';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import type { PathwayResult } from '@/types/api';
import { INFLATION_TAG_COLORS, INFLATION_TAG_LABELS } from '@/types/api';

interface PathwayDrawerProps {
  pathway: PathwayResult | null;
  onClose: () => void;
}

export function PathwayDrawer({ pathway, onClose }: PathwayDrawerProps) {
  const handleCopy = () => {
    if (!pathway) return;
    const text = `PathWeave Result — ${pathway.pathway_name}
Composite score: ${pathway.composite_score.toFixed(4)}
FDR: ${pathway.fdr.toExponential(2)}
Odds ratio: ${pathway.odds_ratio.toFixed(2)}×
Overlap: ${pathway.overlap_count}/${pathway.pathway_size} genes (${(pathway.coverage * 100).toFixed(1)}%)
Evidence strength: ${(pathway.evidence_strength * 100).toFixed(1)}%
Overlapping genes: ${pathway.overlapping_genes.join(', ')}
KEGG: https://www.kegg.jp/pathway/${pathway.pathway_id}`;
    navigator.clipboard.writeText(text);
    toast.success('Summary copied to clipboard');
  };

  // Score breakdown data for stacked bar
  const breakdownData = pathway
    ? [
        {
          name: 'Score breakdown',
          fdr: parseFloat((-Math.log10(pathway.fdr || 1e-10) * 0.4 / 8).toFixed(3)),
          oddsRatio: parseFloat((Math.log2(Math.max(pathway.odds_ratio, 0.1)) * 0.2 / 3).toFixed(3)),
          coverage: parseFloat((pathway.coverage * 0.2).toFixed(3)),
          evidenceStrength: parseFloat((pathway.evidence_strength * 0.2).toFixed(3)),
        },
      ]
    : [];

  return (
    <AnimatePresence>
      {pathway && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black/40 z-40 no-print"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            aria-hidden="true"
          />
          {/* Drawer */}
          <motion.aside
            className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-bg-secondary border-l border-border-subtle z-50 overflow-y-auto shadow-2xl no-print"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            role="dialog"
            aria-label={`Pathway details: ${pathway.pathway_name}`}
            aria-modal="true"
          >
            {/* Header */}
            <div className="sticky top-0 bg-bg-secondary/95 backdrop-blur-sm border-b border-border-subtle p-5 flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <p className="font-mono text-[11px] text-slate-500 mb-1">{pathway.pathway_id}</p>
                <h2 className="text-base font-semibold text-white leading-tight">{pathway.pathway_name}</h2>
                {pathway.inflammation_tag && (
                  <span
                    className="badge mt-2 border text-[11px]"
                    style={{
                      backgroundColor: `${INFLATION_TAG_COLORS[pathway.inflammation_tag]}18`,
                      borderColor: `${INFLATION_TAG_COLORS[pathway.inflammation_tag]}40`,
                      color: INFLATION_TAG_COLORS[pathway.inflammation_tag],
                    }}
                  >
                    {INFLATION_TAG_LABELS[pathway.inflammation_tag]}
                  </span>
                )}
              </div>
              <button
                onClick={onClose}
                className="text-slate-400 hover:text-white transition-colors flex-shrink-0"
                aria-label="Close drawer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-5 space-y-6">
              {/* Score metrics */}
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'Composite score', value: pathway.composite_score.toFixed(4), color: 'text-brand-teal' },
                  { label: 'FDR', value: pathway.fdr.toExponential(2), color: pathway.fdr < 0.001 ? 'text-red-400' : pathway.fdr < 0.01 ? 'text-amber-400' : 'text-green-400' },
                  { label: 'Odds ratio', value: `${pathway.odds_ratio.toFixed(2)}×`, color: 'text-slate-300' },
                  { label: 'Coverage', value: `${(pathway.coverage * 100).toFixed(1)}%`, color: 'text-blue-400' },
                ].map((m) => (
                  <div key={m.label} className="bg-bg-tertiary rounded-xl p-3 border border-border-subtle">
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">{m.label}</p>
                    <p className={`font-mono text-lg font-bold ${m.color}`}>{m.value}</p>
                  </div>
                ))}
              </div>

              {/* Score breakdown bar */}
              <div>
                <p className="text-xs text-slate-400 mb-3 font-medium">Score component breakdown</p>
                <div style={{ height: 80 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={breakdownData} layout="vertical">
                      <XAxis type="number" domain={[0, 0.5]} hide />
                      <YAxis type="category" dataKey="name" hide />
                      <Tooltip
                        content={({ active, payload }) => {
                          if (!active || !payload?.length) return null;
                          return (
                            <div className="glass-card p-2 text-xs">
                              {payload.map((p, i) => (
                                <p key={String(p.dataKey ?? i)} style={{ color: p.fill }}>
                                  {String(p.name ?? p.dataKey)}: {(p.value as number).toFixed(3)}
                                </p>
                              ))}
                            </div>
                          );
                        }}
                      />
                      <Bar dataKey="fdr" stackId="a" fill="#0ECFCF" radius={0} name="FDR" />
                      <Bar dataKey="oddsRatio" stackId="a" fill="#7C3AED" name="Odds ratio" />
                      <Bar dataKey="coverage" stackId="a" fill="#3B82F6" name="Coverage" />
                      <Bar dataKey="evidenceStrength" stackId="a" fill="#10B981" name="Evidence" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex flex-wrap gap-3 mt-1">
                  {[
                    { label: 'FDR (40%)', color: '#0ECFCF' },
                    { label: 'Odds ratio (20%)', color: '#7C3AED' },
                    { label: 'Coverage (20%)', color: '#3B82F6' },
                    { label: 'Evidence (20%)', color: '#10B981' },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center gap-1.5 text-[10px] text-slate-400">
                      <div className="w-2 h-2 rounded-sm" style={{ backgroundColor: item.color }} />
                      {item.label}
                    </div>
                  ))}
                </div>
              </div>

              {/* Overlapping genes */}
              <div>
                <p className="text-xs font-medium text-slate-400 mb-2 flex items-center justify-between">
                  <span>Overlapping genes ({pathway.overlap_count}/{pathway.pathway_size})</span>
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {pathway.overlapping_genes.map((g) => (
                    <motion.span
                      key={g}
                      className="px-2 py-1 rounded-lg bg-bg-tertiary border border-border-subtle font-mono text-xs text-slate-300 cursor-default hover:border-brand-teal/30 hover:text-brand-teal transition-colors"
                      whileHover={{ scale: 1.05 }}
                    >
                      {g}
                    </motion.span>
                  ))}
                </div>
              </div>

              {/* Merged pathways */}
              {pathway.merged_pathway_names.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-slate-400 mb-2">
                    Merged pathways (Jaccard ≥ 0.5)
                  </p>
                  <div className="space-y-1.5">
                    {pathway.merged_pathway_names.map((name, i) => (
                      <div key={i} className="flex items-center gap-2 text-xs text-purple-300 bg-brand-violet/10 border border-brand-violet/20 rounded-lg px-3 py-2">
                        <span className="text-purple-400">≡</span>
                        {name}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-3 pt-2 border-t border-border-subtle">
                <a
                  href={`https://www.kegg.jp/pathway/${pathway.pathway_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary flex-1 justify-center text-xs"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  KEGG page
                </a>
                <button onClick={handleCopy} className="btn-secondary flex-1 justify-center text-xs">
                  <Copy className="w-3.5 h-3.5" />
                  Copy summary
                </button>
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}

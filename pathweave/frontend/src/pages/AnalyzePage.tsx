import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Search, ChevronDown, ChevronUp, Dna, Zap, Loader2, Beaker, Info,
} from 'lucide-react';

import { api } from '@/api/client';
import type { AnalyzeRequest, AnalysisOptions } from '@/types/api';
import { DEFAULT_OPTIONS } from '@/types/api';

const EXAMPLE_GENES = ['TNF', 'IL6', 'TP53', 'STAT3', 'NFKB1'];

const STAGE_STEPS = [
  'Expanding RNA network…',
  'Weighting genes…',
  'Mapping KEGG pathways…',
  'Enrichment & FDR correction…',
  'Merging redundancy…',
  'Running null-model control…',
  'Classifying inflammation…',
];

// Animated background threads
function HeroBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
      <svg className="absolute inset-0 w-full h-full opacity-20" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="heroGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#0ECFCF" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#7C3AED" stopOpacity="0.6" />
          </linearGradient>
        </defs>
        {/* Animated weaving threads */}
        {[...Array(8)].map((_, i) => (
          <motion.path
            key={i}
            d={`M${-100 + i * 120} 0 Q ${200 + i * 80} ${200 + i * 30} ${400 + i * 50} ${300 + i * 20} Q ${500 + i * 30} ${400 + i * 15} ${800 + i * 20} 600`}
            stroke="url(#heroGrad)"
            strokeWidth="1"
            fill="none"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.5 }}
            transition={{ duration: 3 + i * 0.5, delay: i * 0.3, ease: 'easeInOut' }}
          />
        ))}
        {/* Floating nodes */}
        {[
          { cx: 200, cy: 150, r: 4 },
          { cx: 450, cy: 280, r: 6 },
          { cx: 650, cy: 180, r: 3 },
          { cx: 120, cy: 400, r: 5 },
          { cx: 580, cy: 420, r: 4 },
        ].map((node, i) => (
          <motion.circle
            key={i}
            cx={node.cx}
            cy={node.cy}
            r={node.r}
            fill="url(#heroGrad)"
            animate={{ cy: [node.cy - 8, node.cy + 8, node.cy - 8] }}
            transition={{ duration: 4 + i, repeat: Infinity, ease: 'easeInOut' }}
          />
        ))}
      </svg>
    </div>
  );
}

function AutocompleteInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const fetchSuggestions = useCallback(
    async (q: string) => {
      if (q.length < 1) { setSuggestions([]); setOpen(false); return; }
      const data = await api.suggestGenes(q).catch(() => []);
      setSuggestions(data.map((d) => d.gene));
      setOpen(data.length > 0);
    },
    []
  );

  useEffect(() => {
    const t = setTimeout(() => fetchSuggestions(value), 200);
    return () => clearTimeout(t);
  }, [value, fetchSuggestions]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          id="seed-gene-input"
          className="input-field pl-10 text-base"
          placeholder="Enter a seed gene, e.g. TNF"
          value={value}
          onChange={(e) => onChange(e.target.value.toUpperCase())}
          onFocus={() => value.length > 0 && setOpen(true)}
          autoComplete="off"
          aria-label="Seed gene input"
          aria-autocomplete="list"
          aria-controls="gene-suggestions"
          aria-expanded={open}
        />
      </div>
      <AnimatePresence>
        {open && (
          <motion.ul
            id="gene-suggestions"
            role="listbox"
            className="absolute z-20 w-full mt-1 bg-bg-card border border-border-subtle rounded-xl shadow-lg overflow-hidden"
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15 }}
          >
            {suggestions.map((gene) => (
              <li
                key={gene}
                role="option"
                aria-selected={value === gene}
                className="px-4 py-2.5 font-mono text-sm text-slate-300 hover:bg-bg-hover cursor-pointer transition-colors"
                onClick={() => { onChange(gene); setOpen(false); }}
              >
                {gene}
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}

export function AnalyzePage() {
  const navigate = useNavigate();
  const [seedGene, setSeedGene] = useState('');
  const [geneListMode, setGeneListMode] = useState(false);
  const [geneListText, setGeneListText] = useState('');
  const [organism, setOrganism] = useState<'hsa' | 'mmu' | 'rno'>('hsa');
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [options, setOptions] = useState<AnalysisOptions>(DEFAULT_OPTIONS);
  const [jobId, setJobId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Poll job progress
  const { data: jobProgress } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => api.getJob(jobId!),
    enabled: !!jobId,
    refetchInterval: (q) => {
      if (!q.state.data) return 1000;
      const status = q.state.data.status;
      return status === 'running' || status === 'pending' ? 1000 : false;
    },
  });

  // Navigate to results when done
  useEffect(() => {
    if (jobProgress?.status === 'done') {
      navigate(`/results/${jobId}`, { state: { result: jobProgress.result } });
    }
    if (jobProgress?.status === 'error') {
      toast.error(`Analysis failed: ${jobProgress.error}`);
      setJobId(null);
      setIsSubmitting(false);
    }
  }, [jobProgress, jobId, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!seedGene && !geneListText.trim()) {
      toast.error('Please enter at least one gene.');
      return;
    }

    setIsSubmitting(true);
    try {
      const geneList = geneListMode
        ? geneListText.split(/[\n,\s]+/).map((g) => g.trim().toUpperCase()).filter(Boolean)
        : undefined;

      const req: AnalyzeRequest = {
        seed_gene: !geneListMode && seedGene ? seedGene : undefined,
        gene_list: geneList,
        organism,
        options,
      };
      const { job_id } = await api.analyze(req);
      setJobId(job_id);
      localStorage.setItem('pathweave_last_job', job_id);
    } catch (err: any) {
      toast.error(err.message || 'Failed to start analysis');
      setIsSubmitting(false);
    }
  };

  const handleDemo = async () => {
    setIsSubmitting(true);
    try {
      const { job_id } = await api.getDemo();
      setJobId(job_id);
      localStorage.setItem('pathweave_last_job', job_id);
    } catch (err: any) {
      toast.error(err.message || 'Failed to load demo');
      setIsSubmitting(false);
    }
  };

  const organisms = [
    { code: 'hsa', label: 'Human', sub: 'H. sapiens' },
    { code: 'mmu', label: 'Mouse', sub: 'M. musculus' },
    { code: 'rno', label: 'Rat', sub: 'R. norvegicus' },
  ];

  // Running state
  if (isSubmitting && jobId) {
    const stage = jobProgress?.stage || 'Queued';
    const percent = jobProgress?.percent || 0;
    const stageIdx = STAGE_STEPS.indexOf(stage);

    return (
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <motion.div
          className="w-full max-w-lg glass-card p-10 text-center"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <motion.div
            className="w-16 h-16 mx-auto mb-6 rounded-full bg-gradient-brand flex items-center justify-center"
            animate={{ rotate: 360 }}
            transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
          >
            <Dna className="w-8 h-8 text-white" />
          </motion.div>
          <h2 className="text-xl font-semibold text-white mb-2">{stage}</h2>
          <p className="text-slate-400 text-sm mb-6">Weaving the RNA network…</p>

          {/* Progress bar */}
          <div className="relative h-2 bg-bg-tertiary rounded-full overflow-hidden mb-6" aria-label={`Progress: ${percent}%`} role="progressbar" aria-valuenow={percent}>
            <motion.div
              className="absolute inset-y-0 left-0 bg-gradient-brand rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${percent}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>

          {/* Stage steps */}
          <div className="space-y-2 text-left">
            {STAGE_STEPS.map((step, i) => {
              const done = stageIdx > i;
              const current = stageIdx === i;
              return (
                <div key={step} className="flex items-center gap-3">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 transition-all ${done ? 'bg-brand-teal/20' : current ? 'bg-brand-violet/20' : 'bg-bg-tertiary'}`}>
                    {done ? (
                      <span className="text-brand-teal text-xs">✓</span>
                    ) : current ? (
                      <Loader2 className="w-3 h-3 text-brand-violet animate-spin" />
                    ) : (
                      <div className="w-1.5 h-1.5 rounded-full bg-border-bright" />
                    )}
                  </div>
                  <span className={`text-sm ${done ? 'text-slate-500 line-through' : current ? 'text-white' : 'text-slate-600'}`}>
                    {step}
                  </span>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Hero */}
      <section className="relative min-h-[90vh] flex items-center justify-center px-4 py-20 overflow-hidden">
        <HeroBackground />
        <div className="relative z-10 w-full max-w-3xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-teal/10 border border-brand-teal/20 text-brand-teal text-xs font-semibold mb-6 tracking-wider uppercase">
              <Dna className="w-3.5 h-3.5" />
              RNA-Regulatory Network Enrichment
            </div>
            <h1 className="text-5xl sm:text-6xl font-bold text-white tracking-tight leading-none mb-4">
              Path<span className="gradient-text">Weave</span>
            </h1>
            <p className="text-xl text-slate-400 font-light mb-2">
              From one gene to the whole inflammatory story.
            </p>
            <p className="text-sm text-slate-500 max-w-xl mx-auto mb-10">
              Enter a seed gene and let PathWeave trace its RNA regulatory neighborhood — miRNA, lncRNA, circRNA — map it to KEGG pathways, and reveal the inflammatory architecture behind the signal.
            </p>
          </motion.div>

          {/* Main input card */}
          <motion.div
            className="glass-card p-6 sm:p-8 text-left"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.15 }}
          >
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Gene input / gene list toggle */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-slate-300" htmlFor="seed-gene-input">
                    Seed gene
                  </label>
                  <button
                    type="button"
                    className="text-xs text-brand-teal hover:text-brand-teal/80 transition-colors"
                    onClick={() => setGeneListMode(!geneListMode)}
                  >
                    {geneListMode ? 'Back to single gene' : 'Paste gene list instead'}
                  </button>
                </div>

                <AnimatePresence mode="wait">
                  {geneListMode ? (
                    <motion.textarea
                      key="list"
                      id="seed-gene-input"
                      className="input-field resize-none h-28"
                      placeholder="Paste gene names separated by commas, spaces, or newlines&#10;e.g. TNF, IL6, NFKB1, STAT3"
                      value={geneListText}
                      onChange={(e) => setGeneListText(e.target.value)}
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 112 }}
                      exit={{ opacity: 0, height: 0 }}
                      aria-label="Gene list input"
                    />
                  ) : (
                    <motion.div
                      key="single"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                    >
                      <AutocompleteInput value={seedGene} onChange={setSeedGene} />
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Example chips */}
                {!geneListMode && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    <span className="text-xs text-slate-500">Try:</span>
                    {EXAMPLE_GENES.map((g) => (
                      <button
                        key={g}
                        type="button"
                        className="px-2.5 py-1 rounded-lg bg-bg-tertiary border border-border-subtle text-xs font-mono text-slate-400 hover:text-brand-teal hover:border-brand-teal/30 transition-all"
                        onClick={() => setSeedGene(g)}
                      >
                        {g}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Organism selector */}
              <div>
                <p className="text-sm font-medium text-slate-300 mb-2">Organism</p>
                <div className="flex gap-2" role="group" aria-label="Organism selection">
                  {organisms.map((org) => (
                    <button
                      key={org.code}
                      type="button"
                      className={`flex-1 py-2.5 rounded-xl border text-sm font-medium transition-all ${
                        organism === org.code
                          ? 'bg-brand-teal/10 border-brand-teal/40 text-brand-teal'
                          : 'bg-bg-tertiary border-border-subtle text-slate-400 hover:border-border-bright hover:text-slate-200'
                      }`}
                      onClick={() => setOrganism(org.code as 'hsa' | 'mmu' | 'rno')}
                      aria-pressed={organism === org.code}
                    >
                      <span className="block">{org.label}</span>
                      <span className="block text-xs opacity-60 font-normal">{org.sub}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Advanced options */}
              <div className="border-t border-border-subtle pt-4">
                <button
                  type="button"
                  className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-200 transition-colors w-full"
                  onClick={() => setAdvancedOpen(!advancedOpen)}
                  aria-expanded={advancedOpen}
                >
                  {advancedOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  Advanced options
                </button>

                <AnimatePresence>
                  {advancedOpen && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="pt-4 space-y-5">
                        {/* RNA types */}
                        <div>
                          <p className="text-xs font-medium text-slate-400 mb-2 flex items-center gap-1">
                            RNA types to include
                            <span title="Select which RNA categories to include in the regulatory neighborhood expansion.">
                              <Info className="w-3 h-3 cursor-help" />
                            </span>
                          </p>
                          <div className="flex flex-wrap gap-2">
                            {(['miRNA', 'lncRNA', 'circRNA'] as const).map((type) => {
                              const checked = options.include_types.includes(type);
                              return (
                                <button
                                  key={type}
                                  type="button"
                                  className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                                    checked
                                      ? 'bg-brand-teal/10 border-brand-teal/40 text-brand-teal'
                                      : 'bg-bg-tertiary border-border-subtle text-slate-500 hover:text-slate-300'
                                  }`}
                                  onClick={() =>
                                    setOptions((o) => ({
                                      ...o,
                                      include_types: checked
                                        ? o.include_types.filter((t) => t !== type)
                                        : [...o.include_types, type],
                                    }))
                                  }
                                  aria-pressed={checked}
                                >
                                  {type}
                                </button>
                              );
                            })}
                          </div>
                        </div>

                        {/* FDR threshold */}
                        <div>
                          <label className="text-xs font-medium text-slate-400 flex items-center justify-between mb-2">
                            <span>FDR threshold</span>
                            <span className="font-mono text-brand-teal">{options.fdr_threshold}</span>
                          </label>
                          <input
                            type="range"
                            min="0.01"
                            max="0.2"
                            step="0.01"
                            value={options.fdr_threshold}
                            onChange={(e) => setOptions((o) => ({ ...o, fdr_threshold: +e.target.value }))}
                            className="w-full"
                            aria-label="FDR threshold"
                          />
                        </div>

                        {/* Min overlap */}
                        <div>
                          <label className="text-xs font-medium text-slate-400 flex items-center justify-between mb-2">
                            <span>Min. gene overlap</span>
                            <span className="font-mono text-brand-teal">{options.min_overlap}</span>
                          </label>
                          <input
                            type="range"
                            min="1"
                            max="10"
                            step="1"
                            value={options.min_overlap}
                            onChange={(e) => setOptions((o) => ({ ...o, min_overlap: +e.target.value }))}
                            className="w-full"
                            aria-label="Minimum gene overlap"
                          />
                        </div>

                        {/* Null iterations */}
                        <div>
                          <label className="text-xs font-medium text-slate-400 flex items-center justify-between mb-2">
                            <span>Null model iterations</span>
                            <span className="font-mono text-brand-teal">{options.null_iterations}</span>
                          </label>
                          <input
                            type="range"
                            min="50"
                            max="500"
                            step="50"
                            value={options.null_iterations}
                            onChange={(e) => setOptions((o) => ({ ...o, null_iterations: +e.target.value }))}
                            className="w-full"
                            aria-label="Null model iterations"
                          />
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Actions */}
              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  type="submit"
                  className="btn-primary flex-1 justify-center py-3 text-base"
                  disabled={isSubmitting}
                  aria-label="Start PathWeave analysis"
                >
                  {isSubmitting ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Zap className="w-5 h-5" />
                  )}
                  Weave the pathway
                </button>
                <button
                  type="button"
                  className="btn-secondary justify-center py-3"
                  onClick={handleDemo}
                  disabled={isSubmitting}
                  aria-label="Load demo results for TNF"
                >
                  <Beaker className="w-4 h-4" />
                  Load demo (TNF)
                </button>
              </div>
            </form>
          </motion.div>

          {/* Feature highlights */}
          <motion.div
            className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            {[
              { icon: '🧬', title: 'RNA Neighborhood', desc: 'Expands seed genes via miRNA, lncRNA, and circRNA interactions' },
              { icon: '📊', title: 'Evidence Weighting', desc: 'Validated interactions outrank predicted; more RNAs = stronger signal' },
              { icon: '🔬', title: 'Null-Model Control', desc: 'Empirical p-values show what the RNA layer adds beyond the seed alone' },
            ].map((feat) => (
              <div key={feat.title} className="glass-card p-5 text-left">
                <div className="text-2xl mb-2">{feat.icon}</div>
                <h3 className="text-sm font-semibold text-white mb-1">{feat.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{feat.desc}</p>
              </div>
            ))}
          </motion.div>
        </div>
      </section>
    </div>
  );
}

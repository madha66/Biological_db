import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { ChevronDown, ChevronUp, Filter, SearchIcon } from 'lucide-react';
import type { PathwayResult } from '@/types/api';
import { INFLATION_TAG_COLORS, INFLATION_TAG_LABELS } from '@/types/api';

function fdrColor(fdr: number): string {
  if (fdr < 0.001) return 'text-red-400';
  if (fdr < 0.01) return 'text-amber-400';
  if (fdr < 0.05) return 'text-green-400';
  return 'text-slate-500';
}

function fdrLabel(fdr: number): string {
  if (fdr === 0) return '<1e-300';
  if (fdr < 0.001) return fdr.toExponential(1);
  return fdr.toFixed(3);
}

function ScoreBar({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-brand-teal to-brand-violet rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${Math.round(score * 100)}%` }}
          transition={{ duration: 0.8, delay: 0.1 }}
        />
      </div>
      <span className="text-xs font-mono text-slate-400 w-10 text-right">{score.toFixed(3)}</span>
    </div>
  );
}

function CoverageBar({ coverage }: { coverage: number }) {
  const pct = Math.round(coverage * 100);
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-16 h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-400/60 rounded-full"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-400">{pct}%</span>
    </div>
  );
}

function InflammationTag({ tag }: { tag: string | null }) {
  if (!tag) return null;
  const color = INFLATION_TAG_COLORS[tag] || '#6B7280';
  const label = INFLATION_TAG_LABELS[tag] || tag;
  return (
    <span
      className="badge text-[10px] font-medium border"
      style={{
        backgroundColor: `${color}18`,
        borderColor: `${color}40`,
        color,
      }}
    >
      {label}
    </span>
  );
}

interface ExpandedRowProps {
  pathway: PathwayResult;
}
function ExpandedRow({ pathway }: ExpandedRowProps) {
  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="px-4 pb-4 pt-0"
    >
      <div className="bg-bg-tertiary/50 rounded-xl p-4 space-y-3 border border-border-subtle">
        <div>
          <p className="text-xs text-slate-500 mb-2">Overlapping genes</p>
          <div className="flex flex-wrap gap-1.5">
            {pathway.overlapping_genes.map((g) => (
              <span key={g} className="px-2 py-0.5 rounded-md bg-bg-card border border-border-subtle font-mono text-xs text-slate-300">
                {g}
              </span>
            ))}
          </div>
        </div>
        {pathway.merged_pathway_names.length > 0 && (
          <div>
            <p className="text-xs text-slate-500 mb-1">Merged similar pathways</p>
            <div className="flex flex-wrap gap-1.5">
              {pathway.merged_pathway_names.map((n) => (
                <span key={n} className="px-2 py-0.5 rounded-md bg-brand-violet/10 border border-brand-violet/20 text-xs text-purple-300">{n}</span>
              ))}
            </div>
          </div>
        )}
        <div className="flex gap-4 text-xs text-slate-500">
          <span>Odds ratio: <strong className="text-white">{pathway.odds_ratio.toFixed(2)}</strong></span>
          <span>Evidence strength: <strong className="text-white">{(pathway.evidence_strength * 100).toFixed(1)}%</strong></span>
          <a
            href={`https://www.kegg.jp/pathway/${pathway.pathway_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-brand-teal hover:text-brand-teal/80 transition-colors"
          >
            KEGG page ↗
          </a>
        </div>
      </div>
    </motion.div>
  );
}

type SortKey = 'rank' | 'composite_score' | 'fdr' | 'odds_ratio' | 'coverage';

interface PathwayTableProps {
  pathways: PathwayResult[];
  onSelect: (p: PathwayResult) => void;
  selectedId?: string;
  expanded?: boolean;
}

export function PathwayTable({ pathways, onSelect, selectedId }: PathwayTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('rank');
  const [sortAsc, setSortAsc] = useState(true);
  const [search, setSearch] = useState('');
  const [filterTag, setFilterTag] = useState('');
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const allTags = Array.from(new Set(pathways.map((p) => p.inflammation_tag).filter(Boolean))) as string[];

  const displayed = useMemo(() => {
    let list = pathways;
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((p) =>
        p.pathway_name.toLowerCase().includes(q) ||
        p.overlapping_genes.some((g) => g.toLowerCase().includes(q))
      );
    }
    if (filterTag) {
      list = list.filter((p) => p.inflammation_tag === filterTag);
    }
    list = [...list].sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      return sortAsc ? (va as number) - (vb as number) : (vb as number) - (va as number);
    });
    return list;
  }, [pathways, search, filterTag, sortKey, sortAsc]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(key === 'rank'); }
  };

  const SortIcon = ({ k }: { k: SortKey }) => {
    if (sortKey !== k) return <ChevronUp className="w-3 h-3 opacity-20" />;
    return sortAsc ? <ChevronUp className="w-3 h-3 text-brand-teal" /> : <ChevronDown className="w-3 h-3 text-brand-teal" />;
  };

  function SortButton({ label, k }: { label: string; k: SortKey }) {
    return (
      <button
        className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-slate-400 hover:text-white transition-colors"
        onClick={() => handleSort(k)}
        aria-label={`Sort by ${label}`}
      >
        {label}
        <SortIcon k={k} />
      </button>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      {/* Toolbar */}
      <div className="p-4 flex flex-wrap gap-3 items-center border-b border-border-subtle">
        <div className="relative flex-1 min-w-40">
          <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
          <input
            type="text"
            className="input-field pl-8 py-2 text-xs"
            placeholder="Search pathways or genes…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search pathways"
          />
        </div>
        {allTags.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <button
              className={`px-2 py-1 rounded-lg text-xs transition-all ${!filterTag ? 'bg-bg-tertiary text-white' : 'text-slate-500 hover:text-white'}`}
              onClick={() => setFilterTag('')}
            >
              All
            </button>
            {allTags.map((tag) => (
              <button
                key={tag}
                className={`px-2 py-1 rounded-lg text-xs transition-all border ${
                  filterTag === tag ? 'border-current' : 'border-transparent text-slate-500 hover:text-white'
                }`}
                style={{ color: INFLATION_TAG_COLORS[tag] }}
                onClick={() => setFilterTag(filterTag === tag ? '' : tag)}
              >
                {INFLATION_TAG_LABELS[tag]}
              </button>
            ))}
          </div>
        )}
        <p className="text-xs text-slate-500">{displayed.length} pathways</p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full" role="table" aria-label="Ranked pathways">
          <thead className="border-b border-border-subtle">
            <tr className="text-left">
              <th className="px-4 py-3 w-12"><SortButton label="#" k="rank" /></th>
              <th className="px-4 py-3">Pathway</th>
              <th className="px-4 py-3 min-w-[180px]"><SortButton label="Score" k="composite_score" /></th>
              <th className="px-4 py-3"><SortButton label="FDR" k="fdr" /></th>
              <th className="px-4 py-3"><SortButton label="OR" k="odds_ratio" /></th>
              <th className="px-4 py-3 min-w-[120px]"><SortButton label="Coverage" k="coverage" /></th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3 w-8" />
            </tr>
          </thead>
          <tbody>
            {displayed.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-slate-500 text-sm">
                  No pathways match the current filters.
                </td>
              </tr>
            ) : (
              displayed.map((pw, idx) => {
                const isSelected = pw.pathway_id === selectedId;
                const isExpanded = expandedRow === pw.pathway_id;
                return (
                  <>
                    <motion.tr
                      key={pw.pathway_id}
                      className={`border-b border-border-subtle/50 cursor-pointer transition-colors ${
                        isSelected ? 'bg-brand-teal/5' : 'hover:bg-bg-hover/50'
                      }`}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: idx * 0.02 }}
                      onClick={() => onSelect(pw)}
                      role="row"
                      aria-selected={isSelected}
                    >
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">{pw.rank}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-start gap-2">
                          <div>
                            <p className="text-sm text-white font-medium leading-tight">{pw.pathway_name}</p>
                            <p className="font-mono text-[10px] text-slate-500 mt-0.5">{pw.pathway_id}</p>
                            {pw.merged_pathways.length > 0 && (
                              <span className="badge bg-brand-violet/10 border border-brand-violet/20 text-purple-300 mt-1 text-[9px]">
                                merged ×{pw.merged_pathways.length + 1}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3"><ScoreBar score={pw.composite_score} /></td>
                      <td className="px-4 py-3 font-mono text-sm">
                        <span className={fdrColor(pw.fdr)}>{fdrLabel(pw.fdr)}</span>
                      </td>
                      <td className="px-4 py-3 font-mono text-sm text-slate-300">
                        {pw.odds_ratio.toFixed(2)}×
                      </td>
                      <td className="px-4 py-3">
                        <div>
                          <CoverageBar coverage={pw.coverage} />
                          <p className="text-[10px] text-slate-500 mt-0.5">
                            {pw.overlap_count}/{pw.pathway_size} genes
                          </p>
                        </div>
                      </td>
                      <td className="px-4 py-3"><InflammationTag tag={pw.inflammation_tag} /></td>
                      <td className="px-4 py-3">
                        <button
                          className="text-slate-500 hover:text-white transition-colors"
                          onClick={(e) => { e.stopPropagation(); setExpandedRow(isExpanded ? null : pw.pathway_id); }}
                          aria-label={isExpanded ? 'Collapse' : 'Expand details'}
                        >
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>
                      </td>
                    </motion.tr>
                    {isExpanded && (
                      <tr key={`${pw.pathway_id}-expanded`}>
                        <td colSpan={8}>
                          <ExpandedRow pathway={pw} />
                        </td>
                      </tr>
                    )}
                  </>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

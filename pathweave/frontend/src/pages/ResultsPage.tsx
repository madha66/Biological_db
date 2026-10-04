import { useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import {
  Download, Share2, ArrowLeft,
  TrendingUp, Activity, Network, Layers, Zap,
} from 'lucide-react';

import { api } from '@/api/client';
import type { AnalysisResult, PathwayResult } from '@/types/api';
import { KPICards } from '@/components/results/KPICards';
import { PathwayTable } from '@/components/results/PathwayTable';
import { BubblePlot } from '@/components/results/BubblePlot';
import { InflammationPanel } from '@/components/results/InflammationPanel';
import { NullModelPanel } from '@/components/results/NullModelPanel';
import { NetworkView } from '@/components/results/NetworkView';
import { PathwayDrawer } from '@/components/results/PathwayDrawer';

const TABS = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'pathways', label: 'Pathways', icon: Layers },
  { id: 'network', label: 'Network', icon: Network },
  { id: 'inflammation', label: 'Inflammation', icon: TrendingUp },
  { id: 'null', label: 'Null Model', icon: Zap },
] as const;

type TabId = typeof TABS[number]['id'];

function SummaryBanner({ text }: { text: string }) {
  // Render **bold** markdown inline
  const parts = text.split(/\*\*(.*?)\*\*/g);
  return (
    <div className="glass-card p-5 border-l-2 border-brand-teal/50 flex gap-3 items-start" role="note">
      <div className="text-brand-teal flex-shrink-0 mt-0.5">✦</div>
      <p className="text-sm text-slate-300 leading-relaxed">
        {parts.map((part, i) =>
          i % 2 === 1 ? <strong key={i} className="text-white font-semibold">{part}</strong> : part
        )}
      </p>
    </div>
  );
}

function ResultsHeader({
  result,
  jobId,
}: {
  result: AnalysisResult;
  jobId: string;
}) {
  const navigate = useNavigate();

  const handleShare = async () => {
    const url = window.location.href;
    await navigator.clipboard.writeText(url);
    toast.success('Results URL copied to clipboard');
  };

  const orgLabels: Record<string, string> = { hsa: 'Human', mmu: 'Mouse', rno: 'Rat' };

  return (
    <div className="sticky top-16 z-40 bg-bg-primary/95 backdrop-blur-md border-b border-border-subtle no-print">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => navigate('/')}
            className="text-slate-400 hover:text-white transition-colors flex-shrink-0"
            aria-label="Back to analyze"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-mono font-semibold text-white text-sm">
              {result.seed_genes.join(', ')}
            </span>
            <span className="text-slate-500 text-xs">·</span>
            <span className="text-slate-400 text-xs">{orgLabels[result.organism]}</span>
            <span className="text-slate-500 text-xs">·</span>
            <span className="text-slate-500 text-xs">{result.summary.run_time_seconds}s</span>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={() => api.exportResults(jobId, 'csv')}
            className="btn-secondary text-xs py-1.5"
            aria-label="Export as CSV"
          >
            <Download className="w-3.5 h-3.5" />
            CSV
          </button>
          <button
            onClick={() => api.exportResults(jobId, 'json')}
            className="btn-secondary text-xs py-1.5"
            aria-label="Export as JSON"
          >
            <Download className="w-3.5 h-3.5" />
            JSON
          </button>
          <button onClick={handleShare} className="btn-secondary text-xs py-1.5" aria-label="Share results">
            <Share2 className="w-3.5 h-3.5" />
            Share
          </button>
        </div>
      </div>
    </div>
  );
}

function TabNav({ activeTab, onChange }: { activeTab: TabId; onChange: (t: TabId) => void }) {
  return (
    <nav className="flex gap-1 border-b border-border-subtle mb-6 overflow-x-auto" aria-label="Results tabs">
      {TABS.map(({ id, label, icon: Icon }) => {
        const active = activeTab === id;
        return (
          <button
            key={id}
            className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-all ${
              active
                ? 'border-brand-teal text-brand-teal'
                : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-border-bright'
            }`}
            onClick={() => onChange(id)}
            aria-selected={active}
            role="tab"
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        );
      })}
    </nav>
  );
}

function ResultsDashboard({ result, jobId }: { result: AnalysisResult; jobId: string }) {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [selectedPathway, setSelectedPathway] = useState<PathwayResult | null>(null);

  return (
    <div>
      <ResultsHeader result={result} jobId={jobId} />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Summary banner */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <SummaryBanner text={result.plain_summary} />
        </motion.div>

        {/* KPI cards */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-8"
        >
          <KPICards summary={result.summary} />
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          <TabNav activeTab={activeTab} onChange={setActiveTab} />

          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === 'overview' && (
                <div className="space-y-8">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <BubblePlot
                      pathways={result.ranked_pathways}
                      onSelect={setSelectedPathway}
                      selectedId={selectedPathway?.pathway_id}
                    />
                    <InflammationPanel
                      sources={result.inflammation_by_source}
                    />
                  </div>
                  <PathwayTable
                    pathways={result.ranked_pathways}
                    onSelect={setSelectedPathway}
                    selectedId={selectedPathway?.pathway_id}
                  />
                </div>
              )}
              {activeTab === 'pathways' && (
                <PathwayTable
                  pathways={result.ranked_pathways}
                  onSelect={setSelectedPathway}
                  selectedId={selectedPathway?.pathway_id}
                  expanded
                />
              )}
              {activeTab === 'network' && (
                <NetworkView
                  graph={result.graph}
                  onSelectPathway={(pid) => {
                    const pw = result.ranked_pathways.find((r) => r.pathway_id === pid);
                    if (pw) setSelectedPathway(pw);
                  }}
                />
              )}
              {activeTab === 'inflammation' && (
                <InflammationPanel
                  sources={result.inflammation_by_source}
                  expanded
                />
              )}
              {activeTab === 'null' && result.null_model && (
                <NullModelPanel
                  nullModel={result.null_model}
                  withSeedPathways={result.ranked_pathways.slice(0, 5)}
                  withoutSeedPathways={result.without_seed_pathways.slice(0, 5)}
                />
              )}
            </motion.div>
          </AnimatePresence>
        </motion.div>
      </div>

      {/* Pathway Detail Drawer */}
      <PathwayDrawer
        pathway={selectedPathway}
        onClose={() => setSelectedPathway(null)}
      />
    </div>
  );
}

export function ResultsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  // Try to get result from navigation state first (instant), then poll
  const stateResult = location.state?.result as AnalysisResult | undefined;

  const { data: jobData } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => api.getJob(jobId!),
    enabled: !!jobId && !stateResult,
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      return !status || status === 'running' || status === 'pending' ? 2000 : false;
    },
  });

  const result = stateResult || jobData?.result;
  const jobIdActual = jobId || '';

  if (!jobIdActual) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] text-slate-400">
        No job ID found.
      </div>
    );
  }

  if (!result) {
    const status = jobData?.status;
    if (status === 'error') {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 text-center px-4">
          <div className="text-4xl">⚠️</div>
          <h2 className="text-xl font-semibold text-white">Analysis failed</h2>
          <p className="text-slate-400 text-sm">{jobData?.error || 'An unknown error occurred.'}</p>
          <button onClick={() => navigate('/')} className="btn-primary">
            <ArrowLeft className="w-4 h-4" />
            Try again
          </button>
        </div>
      );
    }

    // Loading state
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full bg-gradient-brand mx-auto mb-4 animate-spin" style={{ animationDuration: '2s' }} />
          <p className="text-slate-400 text-sm">
            {jobData?.stage || 'Loading results…'}
          </p>
          {jobData?.percent ? (
            <div className="mt-3 w-48 mx-auto h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-brand rounded-full"
                style={{ width: `${jobData.percent}%` }}
              />
            </div>
          ) : null}
        </div>
      </div>
    );
  }

  return <ResultsDashboard result={result} jobId={jobIdActual} />;
}

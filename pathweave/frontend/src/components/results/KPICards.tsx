import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import type { SummaryStats } from '@/types/api';

function AnimatedNumber({ target, decimals = 0 }: { target: number; decimals?: number }) {
  const [value, setValue] = useState(target || 0);

  useEffect(() => {
    if (!target) {
      setValue(0);
      return;
    }
    const duration = 800;
    const steps = 30;
    const stepTime = duration / steps;
    let step = 0;

    const timer = setInterval(() => {
      step++;
      const progress = step / steps;
      const eased = 1 - Math.pow(1 - progress, 2);
      setValue(target * eased);
      if (step >= steps) {
        setValue(target);
        clearInterval(timer);
      }
    }, stepTime);

    return () => clearInterval(timer);
  }, [target]);

  return <span>{decimals > 0 ? value.toFixed(decimals) : Math.round(value).toLocaleString()}</span>;
}

interface KPICardProps {
  label: string;
  value: number;
  subtitle?: string;
  accent?: string;
  decimals?: number;
  delay?: number;
}

function KPICard({ label, value, subtitle, accent = 'text-brand-teal', decimals = 0, delay = 0 }: KPICardProps) {
  return (
    <motion.div
      className="kpi-card"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
    >
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</p>
      <p className={`text-3xl font-bold font-mono ${accent}`}>
        <AnimatedNumber target={value} decimals={decimals} />
      </p>
      {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
    </motion.div>
  );
}

export function KPICards({ summary }: { summary: SummaryStats }) {
  const pctBeyondNull = summary.n_pathways_significant > 0
    ? Math.round((summary.n_pathways_significant / Math.max(summary.n_pathways_tested, 1)) * 100)
    : 0;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      <KPICard
        label="Neighborhood genes"
        value={summary.n_neighborhood_genes}
        subtitle={`from ${summary.n_seed_genes} seed${summary.n_seed_genes > 1 ? 's' : ''}`}
        delay={0}
      />
      <KPICard
        label="miRNAs"
        value={summary.n_mirna}
        subtitle="regulatory"
        accent="text-blue-400"
        delay={0.05}
      />
      <KPICard
        label="lncRNAs"
        value={summary.n_lncrna}
        subtitle="regulatory"
        accent="text-purple-400"
        delay={0.1}
      />
      <KPICard
        label="circRNAs"
        value={summary.n_circrna}
        subtitle="regulatory"
        accent="text-pink-400"
        delay={0.15}
      />
      <KPICard
        label="Sig. pathways"
        value={summary.n_pathways_significant}
        subtitle={`of ${summary.n_pathways_tested} tested`}
        accent="text-brand-teal"
        delay={0.2}
      />
      <KPICard
        label="Signal enrichment"
        value={pctBeyondNull}
        subtitle="% pathways at FDR"
        accent="text-amber-400"
        delay={0.25}
      />
    </div>
  );
}

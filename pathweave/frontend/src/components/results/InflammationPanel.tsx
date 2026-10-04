import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer,
  PieChart, Pie, Cell, Tooltip,
} from 'recharts';
import type { InflammationSummary } from '@/types/api';

interface InflammationPanelProps {
  sources: InflammationSummary[];
  expanded?: boolean;
}

export function InflammationPanel({ sources, expanded = false }: InflammationPanelProps) {
  const [view, setView] = useState<'donut' | 'radar'>('donut');

  if (!sources.length) {
    return (
      <div className="glass-card p-8 flex items-center justify-center text-slate-500 text-sm">
        No inflammation categories found.
      </div>
    );
  }

  const data = sources.map((s) => ({
    name: s.label,
    value: s.count,
    color: s.color,
    category: s.category,
    top_pathways: s.top_pathways,
  }));

  const total = data.reduce((a, d) => a + d.value, 0);

  const RADIAN = Math.PI / 180;
  const renderCustomLabel = ({
    cx, cy, midAngle, innerRadius, outerRadius, value,
  }: any) => {
    const r = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + r * Math.cos(-midAngle * RADIAN);
    const y = cy + r * Math.sin(-midAngle * RADIAN);
    return value / total > 0.08 ? (
      <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={10} fontWeight="600">
        {Math.round((value / total) * 100)}%
      </text>
    ) : null;
  };

  return (
    <div className="glass-card p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300">Inflammation by trigger</h3>
        <div className="flex gap-1">
          {(['donut', 'radar'] as const).map((v) => (
            <button
              key={v}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${view === v ? 'bg-bg-tertiary text-white' : 'text-slate-500 hover:text-white'}`}
              onClick={() => setView(v)}
            >
              {v.charAt(0).toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="h-56" aria-label="Inflammation source distribution chart" role="img">
        <ResponsiveContainer width="100%" height="100%">
          {view === 'donut' ? (
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
                labelLine={false}
                label={renderCustomLabel}
                animationBegin={0}
                animationDuration={800}
              >
                {data.map((d) => (
                  <Cell key={d.category} fill={d.color} opacity={0.85} />
                ))}
              </Pie>
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.[0]) return null;
                  const d = payload[0].payload;
                  return (
                    <div className="glass-card p-3 text-xs">
                      <p className="font-semibold text-white" style={{ color: d.color }}>{d.name}</p>
                      <p className="text-slate-400">{d.value} pathway{d.value !== 1 ? 's' : ''}</p>
                      <p className="text-slate-400">{Math.round((d.value / total) * 100)}% of signal</p>
                    </div>
                  );
                }}
              />
            </PieChart>
          ) : (
            <RadarChart cx="50%" cy="50%" outerRadius={80} data={data}>
              <PolarGrid stroke="#1e2d4a" />
              <PolarAngleAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <Radar dataKey="value" stroke="#0ECFCF" fill="#0ECFCF" fillOpacity={0.2} />
            </RadarChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Category cards */}
      {(expanded ? sources : sources.slice(0, 3)).map((src, i) => (
        <motion.div
          key={src.category}
          className="flex items-start gap-3 p-3 rounded-xl bg-bg-tertiary/50 border border-border-subtle"
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.07 }}
        >
          <div
            className="w-3 h-3 rounded-full flex-shrink-0 mt-1"
            style={{ backgroundColor: src.color }}
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between mb-0.5">
              <p className="text-sm font-medium" style={{ color: src.color }}>{src.label}</p>
              <span className="text-xs font-mono text-slate-400">{src.count}</span>
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              {src.top_pathways.slice(0, 2).join(' · ')}
            </p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

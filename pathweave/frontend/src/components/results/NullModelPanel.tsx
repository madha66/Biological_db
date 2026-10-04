import { useRef, useEffect } from 'react';
import * as d3 from 'd3';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts';
import type { NullModelResult, PathwayResult } from '@/types/api';

interface NullModelPanelProps {
  nullModel: NullModelResult;
  withSeedPathways: PathwayResult[];
  withoutSeedPathways: PathwayResult[];
}

export function NullModelPanel({ nullModel, withSeedPathways, withoutSeedPathways }: NullModelPanelProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  // Build histogram data
  useEffect(() => {
    if (!svgRef.current || !nullModel.null_scores.length) return;

    const el = svgRef.current;
    const W = el.clientWidth || 480;
    const H = 220;
    const margin = { top: 16, right: 20, bottom: 44, left: 50 };
    const w = W - margin.left - margin.right;
    const h = H - margin.top - margin.bottom;

    d3.select(el).selectAll('*').remove();

    const scores = nullModel.null_scores;
    const xScale = d3.scaleLinear()
      .domain([0, Math.max(d3.max(scores) as number, nullModel.real_score) * 1.05])
      .range([0, w]);

    const bins = d3.bin().domain(xScale.domain() as [number, number]).thresholds(25)(scores);
    const yScale = d3.scaleLinear()
      .domain([0, d3.max(bins, (b: any) => b.length) as number])
      .range([h, 0]);

    const svg = d3.select(el).attr('viewBox', `0 0 ${W} ${H}`).attr('preserveAspectRatio', 'xMidYMid meet');
    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`);

    // Bars
    g.selectAll('rect')
      .data(bins)
      .join('rect')
      .attr('x', (b: any) => xScale(b.x0 as number) + 1)
      .attr('y', h)
      .attr('width', (b: any) => Math.max(xScale(b.x1 as number) - xScale(b.x0 as number) - 1, 0))
      .attr('height', 0)
      .attr('fill', '#0ECFCF')
      .attr('opacity', 0.3)
      .attr('rx', 2)
      .transition().duration(600).delay((_: any, i: number) => i * 10)
      .attr('y', (b: any) => yScale(b.length))
      .attr('height', (b: any) => h - yScale(b.length));

    // Real score line
    g.append('line')
      .attr('x1', xScale(nullModel.real_score)).attr('x2', xScale(nullModel.real_score))
      .attr('y1', 0).attr('y2', h)
      .attr('stroke', '#7C3AED').attr('stroke-width', 2.5)
      .attr('stroke-dasharray', '4,3');

    g.append('text')
      .attr('x', xScale(nullModel.real_score) + 5).attr('y', 14)
      .attr('fill', '#7C3AED').attr('font-size', '10px').attr('font-weight', '600')
      .text(`Real: ${nullModel.real_score.toFixed(3)}`);

    // Mean null line
    g.append('line')
      .attr('x1', xScale(nullModel.mean_null)).attr('x2', xScale(nullModel.mean_null))
      .attr('y1', 0).attr('y2', h)
      .attr('stroke', '#94a3b8').attr('stroke-width', 1)
      .attr('stroke-dasharray', '2,3').attr('opacity', 0.5);

    // Axes
    g.append('g')
      .attr('transform', `translate(0,${h})`)
      .call(d3.axisBottom(xScale).ticks(6))
      .call((ax: any) => {
        ax.selectAll('text').attr('fill', '#94a3b8').attr('font-size', '10px');
        ax.selectAll('line').attr('stroke', '#1e2d4a');
        ax.select('.domain').attr('stroke', '#1e2d4a');
      });

    g.append('g')
      .call(d3.axisLeft(yScale).ticks(4))
      .call((ax: any) => {
        ax.selectAll('text').attr('fill', '#94a3b8').attr('font-size', '10px');
        ax.selectAll('line').attr('stroke', '#1e2d4a');
        ax.select('.domain').attr('stroke', '#1e2d4a');
      });

    svg.append('text')
      .attr('x', margin.left + w / 2).attr('y', H - 4)
      .attr('text-anchor', 'middle').attr('fill', '#64748b').attr('font-size', '11px')
      .text('Top pathway composite score');

    svg.append('text')
      .attr('transform', `translate(12,${margin.top + h / 2}) rotate(-90)`)
      .attr('text-anchor', 'middle').attr('fill', '#64748b').attr('font-size', '11px')
      .text('Frequency');
  }, [nullModel]);

  // Comparison bar chart
  const comparisonData = withSeedPathways.slice(0, 5).map((pw) => {
    const withoutPw = withoutSeedPathways.find((p) => p.pathway_id === pw.pathway_id);
    return {
      name: pw.pathway_name.length > 22 ? pw.pathway_name.slice(0, 22) + '…' : pw.pathway_name,
      withSeed: parseFloat(pw.composite_score.toFixed(3)),
      withoutSeed: parseFloat((withoutPw?.composite_score || 0).toFixed(3)),
    };
  });

  return (
    <div className="space-y-6">
      {/* Histogram */}
      <div className="glass-card p-5">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-slate-300 mb-1">
            Null-model score distribution
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            Distribution of top pathway scores from {nullModel.null_scores.length} random-seed runs.
            The <span className="text-brand-violet">purple line</span> shows the real seed's score.
            This shows what the RNA network adds beyond a random gene selection.
          </p>
        </div>
        <svg ref={svgRef} className="w-full" style={{ height: 220 }} aria-label="Null model score distribution" role="img" />
        <div className="flex flex-wrap gap-6 mt-4 pt-4 border-t border-border-subtle">
          {[
            { label: 'Real top score', value: nullModel.real_score.toFixed(4), color: 'text-brand-violet' },
            { label: 'Mean null score', value: nullModel.mean_null.toFixed(4), color: 'text-slate-400' },
            { label: 'Empirical p-value', value: nullModel.empirical_pvalue.toFixed(4), color: 'text-brand-teal' },
            { label: 'Percentile', value: `${nullModel.percentile.toFixed(1)}th`, color: 'text-amber-400' },
          ].map((stat) => (
            <div key={stat.label}>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">{stat.label}</p>
              <p className={`font-mono text-base font-bold ${stat.color}`}>{stat.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* With vs without seed */}
      <div className="glass-card p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-1">
          With vs. without seed gene
        </h3>
        <p className="text-xs text-slate-500 mb-4 leading-relaxed">
          Comparison of pathway scores computed including the seed gene (
          <span className="text-brand-teal">teal</span>) versus excluding it (
          <span className="text-slate-400">grey</span>). The delta shows how much the seed's own pathways contribute.
        </p>
        <div style={{ height: 240 }} aria-label="With vs without seed comparison" role="img">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={comparisonData}
              layout="vertical"
              margin={{ top: 0, right: 20, bottom: 0, left: 10 }}
            >
              <XAxis
                type="number"
                domain={[0, 1]}
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                axisLine={{ stroke: '#1e2d4a' }}
                tickLine={{ stroke: '#1e2d4a' }}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={140}
                tick={{ fill: '#94a3b8', fontSize: 10 }}
                axisLine={{ stroke: '#1e2d4a' }}
                tickLine={false}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (!active || !payload?.length) return null;
                  return (
                    <div className="glass-card p-3 text-xs">
                      <p className="font-semibold text-white mb-1">{label}</p>
                      {payload.map((p, i) => (
                        <p key={String(p.dataKey ?? i)} style={{ color: p.color }}>
                          {p.dataKey === 'withSeed' ? 'With seed' : 'Without seed'}: {(p.value as number).toFixed(3)}
                        </p>
                      ))}
                    </div>
                  );
                }}
              />
              <Bar dataKey="withSeed" fill="#0ECFCF" opacity={0.8} name="With seed" radius={[0, 4, 4, 0]} />
              <Bar dataKey="withoutSeed" fill="#475569" opacity={0.8} name="Without seed" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

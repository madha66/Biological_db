import { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';
import type { PathwayResult } from '@/types/api';
import { INFLATION_TAG_COLORS, INFLATION_TAG_LABELS } from '@/types/api';

interface BubblePlotProps {
  pathways: PathwayResult[];
  onSelect: (p: PathwayResult) => void;
  selectedId?: string;
}

export function BubblePlot({ pathways, onSelect, selectedId }: BubblePlotProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<{
    x: number; y: number; pathway: PathwayResult;
  } | null>(null);

  useEffect(() => {
    if (!svgRef.current || !pathways.length) return;

    const el = svgRef.current;
    const W = el.clientWidth || 480;
    const H = 360;
    const margin = { top: 20, right: 20, bottom: 50, left: 60 };
    const w = W - margin.left - margin.right;
    const h = H - margin.top - margin.bottom;

    // Compute derived values
    const data = pathways.slice(0, 30).map((p) => ({
      ...p,
      negLogFdr: p.fdr > 0 ? -Math.log10(p.fdr) : 8,
      logOr: Math.log2(Math.max(p.odds_ratio, 0.1)),
    }));

    d3.select(el).selectAll('*').remove();

    const svg = d3
      .select(el)
      .attr('viewBox', `0 0 ${W} ${H}`)
      .attr('preserveAspectRatio', 'xMidYMid meet');

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const xScale = d3.scaleLinear()
      .domain([0, (d3.max(data, (d: any) => d.negLogFdr) as number) * 1.1])
      .range([0, w]);

    const yScale = d3.scaleLinear()
      .domain([0, (d3.max(data, (d: any) => d.logOr) as number) * 1.1])
      .range([h, 0]);

    const rScale = d3.scaleSqrt()
      .domain([0, d3.max(data, (d: any) => d.overlap_count) as number])
      .range([4, 22]);

    // Axes
    g.append('g')
      .attr('transform', `translate(0,${h})`)
      .call(d3.axisBottom(xScale).ticks(5).tickFormat((d) => `${d}`))
      .call((ax: any) => {
        ax.selectAll('text').attr('fill', '#94a3b8').attr('font-size', '10px');
        ax.selectAll('line').attr('stroke', '#1e2d4a');
        ax.select('.domain').attr('stroke', '#1e2d4a');
      });

    g.append('g')
      .call(d3.axisLeft(yScale).ticks(5).tickFormat((d) => `${d}`))
      .call((ax: any) => {
        ax.selectAll('text').attr('fill', '#94a3b8').attr('font-size', '10px');
        ax.selectAll('line').attr('stroke', '#1e2d4a');
        ax.select('.domain').attr('stroke', '#1e2d4a');
      });

    // Grid lines
    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale).ticks(5).tickSize(-w).tickFormat(() => ''))
      .call((ax: any) => {
        ax.selectAll('line').attr('stroke', '#1e2d4a').attr('stroke-dasharray', '2,3');
        ax.select('.domain').remove();
      });

    // FDR significance line at p=0.05
    const sigX = xScale(-Math.log10(0.05));
    g.append('line')
      .attr('x1', sigX).attr('x2', sigX)
      .attr('y1', 0).attr('y2', h)
      .attr('stroke', '#0ECFCF').attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,3').attr('opacity', 0.4);

    g.append('text')
      .attr('x', sigX + 4).attr('y', 12)
      .attr('fill', '#0ECFCF').attr('font-size', '9px').attr('opacity', 0.6)
      .text('FDR 0.05');

    // Axis labels
    svg.append('text')
      .attr('x', margin.left + w / 2).attr('y', H - 6)
      .attr('text-anchor', 'middle').attr('fill', '#64748b').attr('font-size', '11px')
      .text('−log₁₀(FDR)');

    svg.append('text')
      .attr('transform', `translate(14,${margin.top + h / 2}) rotate(-90)`)
      .attr('text-anchor', 'middle').attr('fill', '#64748b').attr('font-size', '11px')
      .text('log₂(Odds ratio)');

    // Bubbles
    const bubbles = g.selectAll<SVGCircleElement, typeof data[0]>('circle')
      .data(data, (d: any) => d.pathway_id)
      .join('circle')
      .attr('cx', (d: any) => xScale(d.negLogFdr))
      .attr('cy', (d: any) => yScale(d.logOr))
      .attr('r', 0)
      .attr('fill', (d: any) => `${INFLATION_TAG_COLORS[d.inflammation_tag || 'unclassified'] || '#0ECFCF'}88`)
      .attr('stroke', (d: any) => d.pathway_id === selectedId ? '#0ECFCF' : INFLATION_TAG_COLORS[d.inflammation_tag || 'unclassified'] || '#0ECFCF')
      .attr('stroke-width', (d: any) => d.pathway_id === selectedId ? 2 : 1)
      .attr('cursor', 'pointer')
      .attr('aria-label', (d: any) => d.pathway_name);

    bubbles.transition()
      .duration(600)
      .delay((_: any, i: number) => i * 20)
      .attr('r', (d: any) => rScale(d.overlap_count));

    bubbles
      .on('mouseenter', (event: any, d: any) => {
        d3.select(event.currentTarget).attr('stroke-width', 2.5);
        const rect = (svgRef.current as SVGSVGElement).getBoundingClientRect();
        setTooltip({
          x: event.clientX - rect.left,
          y: event.clientY - rect.top,
          pathway: d,
        });
      })
      .on('mouseleave', (event: any) => {
        d3.select(event.currentTarget).attr('stroke-width', (d: any) => d.pathway_id === selectedId ? 2 : 1);
        setTooltip(null);
      })
      .on('click', (_: any, d: any) => onSelect(d));
  }, [pathways, selectedId]);

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-semibold text-slate-300 mb-4" id="bubble-plot-title">
        Pathway enrichment landscape
      </h3>
      <div className="relative">
        <svg ref={svgRef} className="w-full" style={{ height: 360 }} aria-labelledby="bubble-plot-title" role="img" />
        {tooltip && (
          <div
            className="absolute z-10 glass-card p-3 text-xs pointer-events-none max-w-xs"
            style={{ left: tooltip.x + 12, top: tooltip.y - 40 }}
          >
            <p className="font-semibold text-white mb-1">{tooltip.pathway.pathway_name}</p>
            <div className="space-y-0.5 text-slate-400">
              <p>FDR: <span className="font-mono text-white">{tooltip.pathway.fdr.toExponential(2)}</span></p>
              <p>Odds ratio: <span className="font-mono text-white">{tooltip.pathway.odds_ratio.toFixed(2)}×</span></p>
              <p>Overlap: <span className="font-mono text-white">{tooltip.pathway.overlap_count}</span> genes</p>
              {tooltip.pathway.inflammation_tag && (
                <p>Category: <span style={{ color: INFLATION_TAG_COLORS[tooltip.pathway.inflammation_tag] }}>{tooltip.pathway.inflammation_tag}</span></p>
              )}
            </div>
          </div>
        )}
      </div>
      <div className="flex flex-wrap gap-3 mt-3 justify-center">
        {Object.entries({
          infection: '#F97316',
          autoimmunity: '#8B5CF6',
          metabolic: '#10B981',
          cancer: '#EF4444',
          tissue_damage: '#F59E0B',
        }).map(([tag, color]) => (
          <div key={tag} className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            {INFLATION_TAG_LABELS[tag] || tag}
          </div>
        ))}
      </div>
    </div>
  );
}

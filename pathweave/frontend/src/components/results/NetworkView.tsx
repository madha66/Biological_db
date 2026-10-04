import { useEffect, useRef, useState } from 'react';
import type { RegulationGraph } from '@/types/api';

// We use Cytoscape via dynamic import to avoid SSR issues
let CytoscapeModule: any = null;

interface NetworkViewProps {
  graph: RegulationGraph;
  onSelectPathway: (id: string) => void;
}

export function NetworkView({ graph, onSelectPathway }: NetworkViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<any>(null);
  const [layout, setLayout] = useState<'concentric' | 'cose' | 'breadthfirst'>('concentric');
  const [loaded, setLoaded] = useState(false);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; label: string } | null>(null);

  useEffect(() => {
    let mounted = true;
    import('cytoscape').then((cy) => {
      if (mounted) {
        CytoscapeModule = cy.default;
        setLoaded(true);
      }
    });
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (!loaded || !containerRef.current || !CytoscapeModule) return;

    // Build elements
    const elements: any[] = [];

    graph.gene_nodes.forEach((n) => {
      elements.push({
        data: {
          id: n.gene,
          label: n.gene,
          type: n.is_seed ? 'seed' : 'gene',
          weight: n.weight,
        },
      });
    });

    graph.rna_nodes.forEach((n) => {
      elements.push({
        data: {
          id: n.rna_id,
          label: n.rna_id.length > 16 ? n.rna_id.slice(0, 14) + '…' : n.rna_id,
          type: 'rna',
          rna_type: n.rna_type,
          evidence: n.evidence,
        },
      });
    });

    graph.pathway_nodes.slice(0, 10).forEach((n) => {
      elements.push({
        data: {
          id: n.pathway_id,
          label: n.pathway_name.length > 20 ? n.pathway_name.slice(0, 18) + '…' : n.pathway_name,
          type: 'pathway',
          score: n.composite_score,
        },
      });
    });

    graph.edges.forEach((e, i) => {
      elements.push({
        data: {
          id: `e${i}`,
          source: e.source,
          target: e.target,
          edge_type: e.edge_type,
          evidence: e.evidence,
        },
      });
    });

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const cy = CytoscapeModule({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node[type="seed"]',
          style: {
            'background-color': '#0ECFCF',
            'border-color': '#fff',
            'border-width': 3,
            'width': 50,
            'height': 50,
            'label': 'data(label)',
            'font-size': 12,
            'font-weight': '700',
            'color': '#fff',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-family': 'JetBrains Mono, monospace',
          },
        },
        {
          selector: 'node[type="gene"]',
          style: {
            'background-color': '#1e2a40',
            'border-color': '#2a3f5f',
            'border-width': 1.5,
            'width': 35,
            'height': 35,
            'label': 'data(label)',
            'font-size': 9,
            'color': '#94a3b8',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-family': 'JetBrains Mono, monospace',
          },
        },
        {
          selector: 'node[type="rna"][rna_type="miRNA"]',
          style: {
            'background-color': '#3B82F611',
            'border-color': '#3B82F6',
            'border-width': 1.5,
            'shape': 'diamond',
            'width': 30,
            'height': 30,
            'label': 'data(label)',
            'font-size': 8,
            'color': '#60a5fa',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'font-family': 'Inter, sans-serif',
          },
        },
        {
          selector: 'node[type="rna"][rna_type="lncRNA"]',
          style: {
            'background-color': '#A855F711',
            'border-color': '#A855F7',
            'border-width': 1.5,
            'shape': 'roundrectangle',
            'width': 32,
            'height': 20,
            'label': 'data(label)',
            'font-size': 8,
            'color': '#c084fc',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'font-family': 'Inter, sans-serif',
          },
        },
        {
          selector: 'node[type="rna"][rna_type="circRNA"]',
          style: {
            'background-color': '#EC489911',
            'border-color': '#EC4899',
            'border-width': 1.5,
            'shape': 'ellipse',
            'width': 26,
            'height': 26,
            'label': 'data(label)',
            'font-size': 8,
            'color': '#f472b6',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'font-family': 'Inter, sans-serif',
          },
        },
        {
          selector: 'node[type="pathway"]',
          style: {
            'background-color': '#7C3AED22',
            'border-color': '#7C3AED',
            'border-width': 2,
            'shape': 'hexagon',
            'width': 60,
            'height': 40,
            'label': 'data(label)',
            'font-size': 9,
            'color': '#c4b5fd',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-family': 'Inter, sans-serif',
            'text-wrap': 'wrap',
            'text-max-width': 55,
          },
        },
        {
          selector: 'edge[edge_type="rna_to_gene"][evidence="validated"]',
          style: {
            'line-color': '#0ECFCF55',
            'width': 1.5,
            'target-arrow-color': '#0ECFCF55',
            'target-arrow-shape': 'vee',
            'curve-style': 'bezier',
            'arrow-scale': 0.7,
            'line-style': 'solid',
          },
        },
        {
          selector: 'edge[edge_type="rna_to_gene"][evidence="predicted"]',
          style: {
            'line-color': '#0ECFCF33',
            'width': 1,
            'target-arrow-color': '#0ECFCF33',
            'target-arrow-shape': 'vee',
            'curve-style': 'bezier',
            'arrow-scale': 0.6,
            'line-style': 'dashed',
          },
        },
        {
          selector: 'edge[edge_type="gene_to_pathway"]',
          style: {
            'line-color': '#7C3AED44',
            'width': 1,
            'target-arrow-color': '#7C3AED44',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'arrow-scale': 0.7,
          },
        },
        {
          selector: ':selected',
          style: {
            'border-color': '#0ECFCF',
            'border-width': 3,
          },
        },
      ],
      layout: {
        name: layout,
        fit: true,
        padding: 30,
        ...(layout === 'concentric'
          ? {
            concentric: (node: any) => {
              const t = node.data('type');
              if (t === 'seed') return 3;
              if (t === 'rna') return 2;
              if (t === 'gene') return 1.5;
              return 1;
            },
            levelWidth: () => 1,
          }
          : {}),
      },
      userZoomingEnabled: true,
      userPanningEnabled: true,
      minZoom: 0.3,
      maxZoom: 3,
    });

    cy.on('tap', 'node[type="pathway"]', (evt: any) => {
      onSelectPathway(evt.target.id());
    });

    cy.on('mouseover', 'node', (evt: any) => {
      const pos = evt.renderedPosition;
      const data = evt.target.data();
      setTooltip({ x: pos.x, y: pos.y, label: data.label || data.id });
    });

    cy.on('mouseout', 'node', () => setTooltip(null));

    cyRef.current = cy;

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [graph, layout, loaded, onSelectPathway]);

  // Relayout when layout changes
  useEffect(() => {
    if (!cyRef.current) return;
    cyRef.current.layout({ name: layout, fit: true, padding: 30 }).run();
  }, [layout]);

  if (!loaded) {
    return (
      <div className="glass-card h-96 flex items-center justify-center text-slate-400 text-sm">
        Loading network…
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b border-border-subtle">
        <div>
          <h3 className="text-sm font-semibold text-slate-300">Regulatory network</h3>
          <p className="text-[11px] text-slate-500">Click pathway nodes to inspect. Solid edges = validated; dashed = predicted.</p>
        </div>
        <div className="flex items-center gap-2">
          {(['concentric', 'cose', 'breadthfirst'] as const).map((l) => (
            <button
              key={l}
              className={`px-2.5 py-1 rounded-lg text-xs transition-all ${layout === l ? 'bg-bg-tertiary text-white' : 'text-slate-500 hover:text-white'}`}
              onClick={() => setLayout(l)}
            >
              {l}
            </button>
          ))}
          <button
            className="btn-secondary text-xs py-1"
            onClick={() => cyRef.current?.fit(undefined, 30)}
          >
            Fit
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 px-4 pt-3 pb-0">
        {[
          { label: 'Seed gene', color: '#0ECFCF', shape: '●' },
          { label: 'Target gene', color: '#475569', shape: '●' },
          { label: 'miRNA', color: '#3B82F6', shape: '◆' },
          { label: 'lncRNA', color: '#A855F7', shape: '▪' },
          { label: 'circRNA', color: '#EC4899', shape: '●' },
          { label: 'Pathway', color: '#7C3AED', shape: '⬡' },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span style={{ color: item.color }}>{item.shape}</span>
            {item.label}
          </div>
        ))}
      </div>

      {/* Canvas */}
      <div className="relative">
        <div ref={containerRef} style={{ height: 480, background: 'transparent' }} aria-label="Regulatory network graph" role="img" />
        {tooltip && (
          <div
            className="absolute glass-card px-2 py-1 text-xs text-white pointer-events-none z-10"
            style={{ left: tooltip.x + 10, top: tooltip.y - 28 }}
          >
            {tooltip.label}
          </div>
        )}
      </div>
    </div>
  );
}

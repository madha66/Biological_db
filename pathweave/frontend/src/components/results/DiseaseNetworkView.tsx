import { useEffect, useRef, useState } from 'react';
import type { IntegratedNetwork } from '@/types/api';

interface DiseaseNetworkViewProps {
  network: IntegratedNetwork;
}

export function DiseaseNetworkView({ network }: DiseaseNetworkViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<any>(null);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    import('cytoscape').then((module) => {
      if (!mounted || !containerRef.current) return;
      const cytoscape = module.default;
      const elements = [
        ...network.nodes.map((node) => ({ data: { id: node.id, label: node.label, node_type: node.node_type } })),
        ...network.edges.map((edge, index) => ({
          data: { id: `edge-${index}`, source: edge.source, target: edge.target, edge_type: edge.edge_type },
        })),
      ];
      cyRef.current?.destroy();
      const cy = cytoscape({
        container: containerRef.current,
        elements,
        layout: { name: 'cose', animate: false },
        style: [
          { selector: 'node', style: { label: 'data(label)', 'font-size': 9, color: '#cbd5e1', 'text-valign': 'bottom', 'background-color': '#334155', width: 26, height: 26 } },
          { selector: 'node[node_type="gene"]', style: { 'background-color': '#0ecfcf' } },
          { selector: 'node[node_type="protein"]', style: { 'background-color': '#f59e0b' } },
          { selector: 'node[node_type="miRNA"]', style: { 'background-color': '#3b82f6', shape: 'diamond' } },
          { selector: 'node[node_type="lncRNA"]', style: { 'background-color': '#a855f7', shape: 'roundrectangle' } },
          { selector: 'node[node_type="disease"]', style: { 'background-color': '#ef4444', shape: 'hexagon' } },
          { selector: 'node[node_type="pathway"]', style: { 'background-color': '#7c3aed', shape: 'hexagon' } },
          { selector: 'edge', style: { width: 1, 'line-color': '#475569', 'target-arrow-color': '#64748b', 'target-arrow-shape': 'triangle', opacity: 0.7 } },
        ],
      });
      cy.on('tap', 'node', (event: any) => setSelected(event.target.data('id')));
      cyRef.current = cy;
    });
    return () => {
      mounted = false;
      cyRef.current?.destroy();
      cyRef.current = null;
    };
  }, [network]);

  if (network.nodes.length === 0) {
    return <p className="text-slate-500">No integrated network edges were returned.</p>;
  }
  return (
    <div>
      <div ref={containerRef} className="h-96 rounded-lg border border-border-subtle bg-bg-tertiary" aria-label="Interactive integrated biological network" />
      <p className="text-xs text-slate-500 mt-2">Drag nodes, zoom, pan, or select a node for details.</p>
      {selected && <p className="text-sm text-brand-teal mt-1">Selected node: <span className="font-mono">{selected}</span></p>}
    </div>
  );
}

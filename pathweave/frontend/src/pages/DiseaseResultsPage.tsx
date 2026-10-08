import { ArrowLeft } from 'lucide-react';
import type { ReactNode } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import type { DiseaseAnalysisResult } from '@/types/api';
import { DiseaseNetworkView } from '@/components/results/DiseaseNetworkView';

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="glass-card p-5">
      <h2 className="text-lg font-semibold text-white mb-4">{title}</h2>
      {children}
    </section>
  );
}

export function DiseaseResultsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const result = location.state?.result as DiseaseAnalysisResult | undefined;

  if (!result) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <p className="text-slate-400 mb-4">No disease analysis result was supplied.</p>
        <button className="btn-primary" onClick={() => navigate('/')}>Start an analysis</button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <button className="btn-secondary text-sm" onClick={() => navigate('/')}>
        <ArrowLeft className="w-4 h-4" /> New analysis
      </button>
      <div>
        <p className="text-xs uppercase tracking-wider text-brand-teal">Integrated disease explorer</p>
        <h1 className="text-3xl font-bold text-white mt-1">{result.inputs.join(', ')}</h1>
        <p className="text-slate-400 mt-2">
          Live associations from KEGG Disease and transcript metadata from Ensembl REST.
          {result.disease_query ? ` Filter: ${result.disease_query}` : ''}
        </p>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          ['Inputs', result.summary.input_count],
          ['Diseases', result.summary.disease_association_count],
          ['Pathways', result.summary.pathway_count],
          ['Relationships', result.summary.interaction_count],
        ].map(([label, value]) => (
          <div key={label} className="kpi-card">
            <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
            <p className="text-3xl font-bold font-mono text-brand-teal">{value}</p>
          </div>
        ))}
      </div>
      {result.warnings.length > 0 && (
        <div className="glass-card border-l-2 border-amber-400 p-4 text-sm text-amber-200">
          {result.warnings.map((warning) => <p key={warning}>{warning}</p>)}
        </div>
      )}
      <Section title="Input resolution">
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500 border-b border-border-subtle"><th className="py-2">Input</th><th>Type</th><th>Resolved identifier</th><th>Status</th><th>Source</th></tr></thead>
          <tbody>{result.input_resolutions.map((item) => (
            <tr key={item.original_input} className="border-b border-border-subtle/50 text-slate-300"><td className="py-2 font-mono">{item.original_input}</td><td>{item.detected_type}</td><td className="font-mono">{item.resolved_identifier || '—'}</td><td>{item.status}{item.warning ? `: ${item.warning}` : ''}</td><td>{item.source_db || '—'}</td></tr>
          ))}</tbody>
        </table></div>
      </Section>
      <Section title="Disease associations">
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500 border-b border-border-subtle">
            <th className="py-2">Input</th><th>Disease</th><th>Identifier</th><th>Source</th>
          </tr></thead>
          <tbody>{result.associations.map((item) => (
            <tr key={`${item.input_name}-${item.disease_id}`} className="border-b border-border-subtle/50 text-slate-300">
              <td className="py-2 font-mono">{item.input_name}</td><td>{item.disease_name}</td><td className="font-mono">{item.disease_id}</td><td>{item.source_db}</td>
            </tr>
          ))}</tbody>
        </table>{result.associations.length === 0 && <p className="text-slate-500">No associations matched this query.</p>}</div>
      </Section>
      <Section title="Pathways">
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500 border-b border-border-subtle"><th className="py-2">Pathway</th><th>Database</th><th>Input genes</th><th>Overlap</th></tr></thead>
          <tbody>{result.pathways.slice(0, 100).map((item) => (
            <tr key={item.pathway_id} className="border-b border-border-subtle/50 text-slate-300">
              <td className="py-2">{item.pathway_name} <span className="text-slate-500 font-mono">({item.pathway_id})</span></td><td>{item.source_db}</td><td className="font-mono">{item.input_genes.join(', ')}</td><td>{item.overlap_count}</td>
            </tr>
          ))}</tbody>
        </table></div>
      </Section>
      <Section title="Reactome pathways">
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500 border-b border-border-subtle"><th className="py-2">Input</th><th>Pathway</th><th>Reactome ID</th><th>Evidence</th></tr></thead>
          <tbody>{result.reactome_pathways.slice(0, 100).map((item) => (
            <tr key={`${item.input_gene}-${item.pathway_id}`} className="border-b border-border-subtle/50 text-slate-300"><td className="py-2 font-mono">{item.input_gene}</td><td>{item.pathway_name}</td><td className="font-mono">{item.pathway_id}</td><td>{item.evidence || 'Reactome'}</td></tr>
          ))}</tbody>
        </table>{result.reactome_pathways.length === 0 && <p className="text-slate-500">No Reactome pathways were returned.</p>}</div>
      </Section>
      <Section title="Gene Ontology biological processes">
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500 border-b border-border-subtle"><th className="py-2">Input</th><th>GO term</th><th>GO ID</th><th>Namespace</th></tr></thead>
          <tbody>{result.go_annotations.slice(0, 100).map((item) => (
            <tr key={`${item.input_gene}-${item.go_id}`} className="border-b border-border-subtle/50 text-slate-300"><td className="py-2 font-mono">{item.input_gene}</td><td>{item.term_name}</td><td className="font-mono">{item.go_id}</td><td>{item.namespace}</td></tr>
          ))}</tbody>
        </table>{result.go_annotations.length === 0 && <p className="text-slate-500">No Gene Ontology annotations were returned.</p>}</div>
      </Section>
      <Section title="Cross-database validation">
        <p className="text-xs text-slate-500 mb-3">Only exact normalized name matches are grouped; similar names with different wording are not claimed equivalent.</p>
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500 border-b border-border-subtle"><th className="py-2">Biological theme</th><th>KEGG</th><th>Reactome</th><th>GO</th><th>Supporting inputs</th></tr></thead>
          <tbody>{result.cross_validation.map((item) => (
            <tr key={item.theme} className="border-b border-border-subtle/50 text-slate-300"><td className="py-2">{item.theme}</td><td>{item.kegg_pathways.length ? '✓' : '—'}</td><td>{item.reactome_pathways.length ? '✓' : '—'}</td><td>{item.go_terms.length ? '✓' : '—'}</td><td className="font-mono">{item.supporting_inputs.join(', ')}</td></tr>
          ))}</tbody>
        </table>{result.cross_validation.length === 0 && <p className="text-slate-500">No exact normalized names were shared across databases.</p>}</div>
      </Section>
      <Section title="miRNA target relationships">
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500 border-b border-border-subtle"><th className="py-2">miRNA</th><th>Target gene</th><th>Evidence</th><th>Source</th></tr></thead>
          <tbody>{result.mirna_relationships.map((item) => (
            <tr key={`${item.rna}-${item.target_gene}`} className="border-b border-border-subtle/50 text-slate-300"><td className="py-2 font-mono">{item.rna}</td><td className="font-mono">{item.target_gene}</td><td>{item.evidence || item.evidence_category || '—'}</td><td>{item.source_db}</td></tr>
          ))}</tbody>
        </table>{result.mirna_relationships.length === 0 && <p className="text-slate-500">No curated miRNA target relationships were returned.</p>}</div>
      </Section>
      <Section title="lncRNA relationships">
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500 border-b border-border-subtle"><th className="py-2">lncRNA</th><th>Targets</th><th>Status</th><th>Source</th></tr></thead>
          <tbody>{result.lncrna_relationships.map((item) => (
            <tr key={item.lncrna} className="border-b border-border-subtle/50 text-slate-300"><td className="py-2 font-mono">{item.lncrna}</td><td>{item.target_genes.join(', ') || 'None returned'}</td><td>{item.status}</td><td>{item.source_db}</td></tr>
          ))}</tbody>
        </table>{result.lncrna_relationships.length === 0 && <p className="text-slate-500">No lncRNA relationships were returned.</p>}</div>
      </Section>
      <Section title="Protein interactions">
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500 border-b border-border-subtle"><th className="py-2">Source</th><th>Target</th><th>Score</th><th>Source</th></tr></thead>
          <tbody>{result.protein_interactions.slice(0, 100).map((item) => (
            <tr key={`${item.source_gene}-${item.target_gene}`} className="border-b border-border-subtle/50 text-slate-300"><td className="py-2 font-mono">{item.source_gene}</td><td className="font-mono">{item.target_gene}</td><td>{item.score == null ? '—' : item.score.toFixed(3)}</td><td>{item.source_db}</td></tr>
          ))}</tbody>
        </table>{result.protein_interactions.length === 0 && <p className="text-slate-500">No protein interactions were returned.</p>}</div>
      </Section>
      <Section title="Integrated network">
        <p className="text-sm text-slate-300">{result.network.nodes.length} nodes and {result.network.edges.length} deduplicated edges.</p>
        <div className="mt-3 flex flex-wrap gap-2">{Object.entries(result.network.nodes.reduce<Record<string, number>>((counts, node) => { counts[node.node_type] = (counts[node.node_type] || 0) + 1; return counts; }, {})).map(([type, count]) => <span key={type} className="px-2 py-1 rounded bg-bg-tertiary text-xs text-slate-300">{type}: {count}</span>)}</div>
        <div className="mt-4"><DiseaseNetworkView network={result.network} /></div>
      </Section>
      <Section title="Network clusters">
        <div className="space-y-3">{result.network_clusters.map((cluster) => <div key={cluster.cluster_id} className="rounded-lg border border-border-subtle p-3"><p className="text-sm font-semibold text-white">{cluster.cluster_id} <span className="text-slate-500 font-normal">({cluster.node_count} nodes)</span></p><p className="text-xs text-slate-400 mt-1">Members: {cluster.members.join(', ')}</p><p className="text-xs text-slate-400 mt-1">Pathways: {cluster.associated_pathways.join(', ') || 'None'}</p></div>)}</div>
      </Section>
      <Section title="Transcript information">
        <div className="overflow-x-auto"><table className="w-full text-sm">
          <thead><tr className="text-left text-slate-500 border-b border-border-subtle"><th className="py-2">Gene</th><th>Transcript</th><th>Type</th><th>Source</th></tr></thead>
          <tbody>{result.transcripts.slice(0, 100).map((item) => (
            <tr key={item.transcript_id} className="border-b border-border-subtle/50 text-slate-300"><td className="py-2 font-mono">{item.gene_symbol}</td><td className="font-mono">{item.transcript_id}</td><td>{item.transcript_type || '—'}</td><td>{item.source_db}</td></tr>
          ))}</tbody>
        </table></div>
      </Section>
      <Section title="Shared vs unique">
        <p className="text-sm text-slate-300"><strong className="text-brand-teal">Shared diseases:</strong> {result.shared_diseases.join(', ') || 'None'}</p>
        <p className="text-sm text-slate-300 mt-2"><strong className="text-brand-teal">Shared pathways:</strong> {result.shared_pathways.join(', ') || 'None'}</p>
        <div className="mt-4 space-y-2">{Object.entries(result.unique_diseases).map(([input, values]) => <p key={input} className="text-sm text-slate-400"><span className="font-mono text-white">{input}:</span> {values.join(', ') || 'No unique diseases'}</p>)}</div>
      </Section>
    </div>
  );
}

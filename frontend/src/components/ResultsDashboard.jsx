import { useState } from 'react';
import PathwayChart from './PathwayChart';
import PathwayTable from './PathwayTable';
import PathwayDetailModal from './PathwayDetailModal';

export default function ResultsDashboard({ data }) {
  const [selectedPathway, setSelectedPathway] = useState(null);

  const { input_summary, valid_genes, unmapped_genes, pathways, metadata } = data;

  return (
    <div style={{ marginTop: 'var(--space-6)' }}>

      {/* Summary Stats */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-value">{input_summary.total_submitted}</div>
          <div className="stat-label">Genes Submitted</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--color-success)' }}>{input_summary.valid_count}</div>
          <div className="stat-label">Valid Genes</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: input_summary.unmapped_count > 0 ? 'var(--color-warning)' : 'var(--color-text-muted)' }}>
            {input_summary.unmapped_count}
          </div>
          <div className="stat-label">Unmapped Genes</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{metadata.pathways_tested}</div>
          <div className="stat-label">Pathways Tested</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: 'var(--color-primary-600)' }}>{metadata.significant_pathways}</div>
          <div className="stat-label">Significant (p_adj &lt; 0.05)</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ fontSize: '1.25rem' }}>{metadata.background_universe_size.toLocaleString()}</div>
          <div className="stat-label">Background Universe</div>
        </div>
      </div>

      {/* Gene Status */}
      <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
        <div className="card-header">
          <h3 className="card-title">Gene Mapping Summary</h3>
          <p className="card-subtitle">
            Organism: {metadata.organism_name} ({metadata.organism})
          </p>
        </div>

        <div style={{ marginBottom: 'var(--space-4)' }}>
          <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>
            Valid Genes ({valid_genes.length})
          </p>
          <div className="gene-tags">
            {valid_genes.map(g => <span key={g} className="gene-tag">{g}</span>)}
          </div>
        </div>

        {unmapped_genes.length > 0 && (
          <div>
            <p style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-warning)', marginBottom: 'var(--space-2)' }}>
              Unmapped Genes ({unmapped_genes.length})
            </p>
            <div className="gene-tags">
              {unmapped_genes.map(g => <span key={g} className="gene-tag unmapped">{g}</span>)}
            </div>
          </div>
        )}
      </div>

      {/* Chart */}
      {pathways.length > 0 && (
        <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
          <div className="card-header">
            <h3 className="card-title">📊 Top Ranked Pathways</h3>
            <p className="card-subtitle">
              Horizontal bar chart showing top pathways by ranking score.
              Color indicates statistical significance (adjusted p-value).
            </p>
          </div>
          <PathwayChart pathways={pathways.slice(0, 15)} />
        </div>
      )}

      {/* Table */}
      {pathways.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Ranked Pathway Table</h3>
            <p className="card-subtitle">
              Click column headers to sort. Click a row to view pathway details.
              <span style={{ color: 'var(--color-text-muted)', fontStyle: 'italic' }}>
                {' '}Representation ≠ statistical enrichment — a pathway can have many genes but not be significant.
              </span>
            </p>
          </div>
          <PathwayTable pathways={pathways} onSelectPathway={setSelectedPathway} />
        </div>
      )}

      {pathways.length === 0 && (
        <div className="card">
          <div className="error-container">
            <div className="error-icon">🔍</div>
            <p style={{ color: 'var(--color-text-secondary)' }}>
              No pathways were found for the submitted gene set. This may indicate that the genes
              do not share annotated KEGG pathways, or the organism selection may be incorrect.
            </p>
          </div>
        </div>
      )}

      {/* Pathway Detail Modal */}
      {selectedPathway && (
        <PathwayDetailModal
          pathway={selectedPathway}
          onClose={() => setSelectedPathway(null)}
        />
      )}

      {/* Metadata footer */}
      <div style={{
        marginTop: 'var(--space-4)', fontSize: '0.75rem', color: 'var(--color-text-muted)',
        textAlign: 'center',
      }}>
        Analysis timestamp: {metadata.timestamp} &nbsp;|&nbsp;
        Formula: {metadata.ranking_formula}
      </div>
    </div>
  );
}

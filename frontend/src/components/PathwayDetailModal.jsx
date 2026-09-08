function formatPValue(p) {
  if (p < 0.0001) return p.toExponential(2);
  return p.toFixed(6);
}

export default function PathwayDetailModal({ pathway, onClose }) {
  if (!pathway) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '4px' }}>
              {pathway.pathway_name}
            </h2>
            <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
              {pathway.pathway_id}
            </p>
          </div>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="detail-grid" style={{ marginBottom: 'var(--space-6)' }}>
          <div className="detail-item">
            <span className="detail-label">Ranking Score</span>
            <span className="detail-value" style={{ color: 'var(--color-primary-600)', fontSize: '1.25rem', fontWeight: 700 }}>
              {pathway.ranking_score.toFixed(4)}
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Rank</span>
            <span className="detail-value">#{pathway.rank}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Input Genes Mapped</span>
            <span className="detail-value">{pathway.input_gene_count}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Total Pathway Genes</span>
            <span className="detail-value">{pathway.total_pathway_genes}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Pathway Score (Representation)</span>
            <span className="detail-value mono">{pathway.pathway_score.toFixed(6)}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Fisher's p-value (raw)</span>
            <span className="detail-value mono">{formatPValue(pathway.p_value)}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Adjusted p-value (BH-FDR)</span>
            <span className={`detail-value mono ${pathway.adjusted_p_value < 0.05 ? '' : ''}`}
              style={{ color: pathway.adjusted_p_value < 0.05 ? 'var(--color-success)' : 'var(--color-text-muted)' }}>
              {formatPValue(pathway.adjusted_p_value)}
              {pathway.adjusted_p_value < 0.05 && (
                <span className="badge badge-success" style={{ marginLeft: '8px' }}>Significant</span>
              )}
            </span>
          </div>
        </div>

        {/* Contributing genes */}
        <div style={{ marginBottom: 'var(--space-6)' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: 'var(--space-3)' }}>
            Contributing Genes ({pathway.contributing_genes.length})
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginBottom: 'var(--space-2)' }}>
            These input genes are associated with this pathway in KEGG.
          </p>
          <div className="gene-tags">
            {pathway.contributing_genes.map(g => (
              <span key={g} className="gene-tag">{g}</span>
            ))}
          </div>
        </div>

        {/* KEGG link */}
        <div style={{
          padding: 'var(--space-4)', background: 'var(--color-bg)', borderRadius: 'var(--radius-md)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <p style={{ fontSize: '0.8125rem', fontWeight: 600 }}>View on KEGG</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              Open this pathway on the KEGG website for detailed pathway maps.
            </p>
          </div>
          <a
            href={pathway.kegg_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary btn-sm"
          >
            Open KEGG →
          </a>
        </div>

        {/* Interpretation note */}
        <p style={{
          marginTop: 'var(--space-4)', fontSize: '0.6875rem', color: 'var(--color-text-muted)',
          fontStyle: 'italic', lineHeight: 1.6,
        }}>
          Note: This pathway is <strong>associated with</strong> the submitted gene set based on
          statistically significant enrichment analysis. This does not imply that the pathway
          causes any specific biological condition.
        </p>
      </div>
    </div>
  );
}

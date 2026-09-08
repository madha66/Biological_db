import { useNavigate } from 'react-router-dom';

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div>
      {/* Hero Section */}
      <section className="hero-section">
        <h1 className="hero-title">
          Rank Biologically Relevant<br />
          <span>KEGG Pathways</span> from Gene Sets
        </h1>
        <p className="hero-subtitle">
          Submit a set of gene identifiers and discover which biological pathways
          are most significantly enriched. Powered by Fisher's exact test,
          Benjamini–Hochberg FDR correction, and a transparent ranking algorithm.
        </p>
        <button className="btn btn-primary btn-lg" onClick={() => navigate('/analyze')}>
          🧬 Start Analysis
        </button>

        {/* Feature cards */}
        <div className="hero-features">
          <div className="hero-feature">
            <div className="hero-feature-icon">🔬</div>
            <h3>Statistical Rigor</h3>
            <p>Fisher's exact test with Benjamini–Hochberg FDR correction for reliable enrichment results.</p>
          </div>
          <div className="hero-feature">
            <div className="hero-feature-icon">📊</div>
            <h3>Transparent Ranking</h3>
            <p>Deterministic ranking formula combining pathway representation and statistical significance.</p>
          </div>
          <div className="hero-feature">
            <div className="hero-feature-icon">🌐</div>
            <h3>Multi-Organism</h3>
            <p>Support for Human, Mouse, Rat, Zebrafish, and Fruit fly via the KEGG REST API.</p>
          </div>
          <div className="hero-feature">
            <div className="hero-feature-icon">📈</div>
            <h3>Interactive Visualization</h3>
            <p>Explore ranked pathways through interactive charts and drill-down gene details.</p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section style={{ maxWidth: '800px', margin: '0 auto' }}>
        <h2 className="section-heading" style={{ textAlign: 'center', marginBottom: '2rem' }}>How It Works</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          {[
            { step: '1', title: 'Enter Genes', desc: 'Paste your gene symbols (e.g. TP53, BRCA1, EGFR) and select an organism.' },
            { step: '2', title: 'KEGG Mapping', desc: 'Genes are validated and mapped to KEGG pathways with comprehensive error handling.' },
            { step: '3', title: 'Enrichment Analysis', desc: "Fisher's exact test evaluates overrepresentation of input genes per pathway." },
            { step: '4', title: 'FDR Correction', desc: 'Benjamini–Hochberg correction controls for multiple hypothesis testing.' },
            { step: '5', title: 'Ranked Results', desc: 'Pathways are ranked by a combined score of representation and significance.' },
          ].map(item => (
            <div key={item.step} className="card" style={{ textAlign: 'center' }}>
              <div style={{
                width: '40px', height: '40px', borderRadius: '50%',
                background: 'linear-gradient(135deg, var(--color-primary-500), var(--color-primary-700))',
                color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 700, margin: '0 auto var(--space-3)',
              }}>{item.step}</div>
              <h3 style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: '0.25rem' }}>{item.title}</h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

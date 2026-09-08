const STEPS = [
  'Validating gene identifiers...',
  'Querying KEGG database...',
  'Computing statistical enrichment...',
  'Applying FDR correction & ranking...',
  'Preparing results...',
];

export default function LoadingState({ step = 0 }) {
  return (
    <div className="card" style={{ marginTop: 'var(--space-6)' }}>
      <div className="loading-overlay">
        <div className="spinner" />
        <p className="loading-text">Analyzing your gene set...</p>
        <div className="loading-steps">
          {STEPS.map((text, i) => (
            <div
              key={i}
              className={`loading-step ${i < step ? 'done' : i === step ? 'active' : ''}`}
            >
              <span>{i < step ? '✓' : i === step ? '●' : '○'}</span>
              {text}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

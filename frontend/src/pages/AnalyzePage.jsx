import { useState, useCallback } from 'react';
import GeneInput from '../components/GeneInput';
import ResultsDashboard from '../components/ResultsDashboard';
import LoadingState from '../components/LoadingState';
import { analyzeGenes } from '../services/api';

export default function AnalyzePage() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [loadingStep, setLoadingStep] = useState(0);

  const handleAnalyze = useCallback(async (genes, organism) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setLoadingStep(0);

    // Simulate step progression for UX
    const stepTimer = setInterval(() => {
      setLoadingStep(prev => Math.min(prev + 1, 4));
    }, 1500);

    try {
      const data = await analyzeGenes(genes, organism);
      setResults(data);
    } catch (err) {
      setError(err.message || 'An unexpected error occurred. Please try again.');
    } finally {
      clearInterval(stepTimer);
      setLoading(false);
    }
  }, []);

  const handleClear = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return (
    <div>
      <h1 className="section-heading" style={{ marginBottom: 'var(--space-2)' }}>
        Pathway Enrichment Analysis
      </h1>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', marginBottom: 'var(--space-6)' }}>
        Submit a set of gene identifiers to discover significantly enriched KEGG pathways.
      </p>

      {/* Gene Input Panel */}
      <GeneInput
        onAnalyze={handleAnalyze}
        onClear={handleClear}
        disabled={loading}
      />

      {/* Loading State */}
      {loading && <LoadingState step={loadingStep} />}

      {/* Error State */}
      {error && !loading && (
        <div className="card" style={{ marginTop: 'var(--space-6)' }}>
          <div className="error-container">
            <div className="error-icon">⚠️</div>
            <p className="error-message">{error}</p>
            <button className="btn btn-primary" onClick={() => setError(null)}>
              Dismiss & Try Again
            </button>
          </div>
        </div>
      )}

      {/* Results Dashboard */}
      {results && !loading && <ResultsDashboard data={results} />}
    </div>
  );
}

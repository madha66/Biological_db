import { useState } from 'react';
import { SAMPLE_GENE_SETS } from '../utils/sampleData';

const ORGANISMS = {
  hsa: 'Human (Homo sapiens)',
  mmu: 'Mouse (Mus musculus)',
  rno: 'Rat (Rattus norvegicus)',
  dre: 'Zebrafish (Danio rerio)',
  dme: 'Fruit fly (Drosophila melanogaster)',
};

export default function GeneInput({ onAnalyze, onClear, disabled }) {
  const [geneText, setGeneText] = useState('');
  const [organism, setOrganism] = useState('hsa');
  const [showExamples, setShowExamples] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!geneText.trim()) return;

    // Split on commas, whitespace, newlines, semicolons
    const genes = geneText
      .split(/[,;\s\n\r\t]+/)
      .map(g => g.trim())
      .filter(g => g.length > 0);

    if (genes.length === 0) return;
    onAnalyze(genes, organism);
  };

  const loadExample = (example) => {
    setGeneText(example.genes);
    setOrganism(example.organism);
    setShowExamples(false);
  };

  const handleClear = () => {
    setGeneText('');
    onClear();
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">🧬 Gene Input</h2>
        <p className="card-subtitle">
          Enter gene symbols separated by commas, spaces, or newlines. Select the organism, then click Analyze.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Organism selector */}
        <div className="form-group">
          <label className="form-label" htmlFor="organism-select">Organism</label>
          <select
            id="organism-select"
            className="form-select"
            value={organism}
            onChange={e => setOrganism(e.target.value)}
            disabled={disabled}
          >
            {Object.entries(ORGANISMS).map(([code, name]) => (
              <option key={code} value={code}>{name}</option>
            ))}
          </select>
        </div>

        {/* Gene textarea */}
        <div className="form-group">
          <label className="form-label" htmlFor="gene-textarea">Gene Symbols</label>
          <textarea
            id="gene-textarea"
            className="form-textarea"
            value={geneText}
            onChange={e => setGeneText(e.target.value)}
            placeholder={`Enter gene symbols, e.g.:\nTP53, BRCA1, EGFR, AKT1, PTEN, MYC\n\nor paste a multi-line list`}
            disabled={disabled}
          />
        </div>

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', alignItems: 'center' }}>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={disabled || !geneText.trim()}
          >
            {disabled ? '⏳ Analyzing...' : '🔬 Analyze'}
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleClear}
            disabled={disabled}
          >
            Clear
          </button>

          <div className="example-selector" style={{ position: 'relative' }}>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => setShowExamples(!showExamples)}
              disabled={disabled}
            >
              📋 Load Example Gene Set ▾
            </button>
            {showExamples && (
              <div className="example-menu">
                {SAMPLE_GENE_SETS.map((ex, i) => (
                  <div key={i} className="example-item" onClick={() => loadExample(ex)}>
                    <div className="example-item-name">{ex.name}</div>
                    <div className="example-item-desc">{ex.description}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}

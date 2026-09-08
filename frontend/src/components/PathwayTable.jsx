import { useState, useMemo } from 'react';

const COLUMNS = [
  { key: 'rank', label: 'Rank', align: 'center', width: '60px' },
  { key: 'pathway_id', label: 'Pathway ID', align: 'left', width: '120px' },
  { key: 'pathway_name', label: 'Pathway Name', align: 'left' },
  { key: 'input_gene_count', label: 'Input Genes', align: 'center', width: '100px' },
  { key: 'pathway_score', label: 'Pathway Score', align: 'right', width: '110px' },
  { key: 'p_value', label: 'Fisher p-value', align: 'right', width: '120px' },
  { key: 'adjusted_p_value', label: 'Adj. p-value', align: 'right', width: '120px' },
  { key: 'ranking_score', label: 'Ranking Score', align: 'right', width: '120px' },
];

function formatPValue(p) {
  if (p < 0.0001) return p.toExponential(2);
  return p.toFixed(4);
}

export default function PathwayTable({ pathways, onSelectPathway }) {
  const [sortKey, setSortKey] = useState('rank');
  const [sortAsc, setSortAsc] = useState(true);
  const [expandedRow, setExpandedRow] = useState(null);

  const sorted = useMemo(() => {
    const copy = [...pathways];
    copy.sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      if (typeof va === 'number') return sortAsc ? va - vb : vb - va;
      return sortAsc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
    });
    return copy;
  }, [pathways, sortKey, sortAsc]);

  const handleSort = (key) => {
    if (key === sortKey) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(key === 'rank' || key === 'pathway_name' || key === 'pathway_id');
    }
  };

  return (
    <div className="data-table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {COLUMNS.map(col => (
              <th
                key={col.key}
                onClick={() => handleSort(col.key)}
                className={sortKey === col.key ? 'sorted' : ''}
                style={{ textAlign: col.align, width: col.width }}
              >
                {col.label}
                {sortKey === col.key && (sortAsc ? ' ↑' : ' ↓')}
              </th>
            ))}
            <th style={{ width: '70px', textAlign: 'center' }}>Details</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map(pw => (
            <>
              <tr key={pw.pathway_id} style={{ cursor: 'pointer' }} onClick={() => onSelectPathway(pw)}>
                <td style={{ textAlign: 'center', fontWeight: 600 }}>{pw.rank}</td>
                <td className="cell-mono">{pw.pathway_id}</td>
                <td style={{ fontWeight: 500 }}>{pw.pathway_name}</td>
                <td style={{ textAlign: 'center' }}>
                  <span className="badge badge-info">{pw.input_gene_count}</span>
                </td>
                <td className="cell-score" style={{ textAlign: 'right' }}>{pw.pathway_score.toFixed(4)}</td>
                <td style={{ textAlign: 'right' }}>
                  <span className={`p-value-cell ${pw.p_value < 0.05 ? 'significant' : 'not-significant'}`}>
                    {formatPValue(pw.p_value)}
                  </span>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <span className={`p-value-cell ${pw.adjusted_p_value < 0.05 ? 'significant' : 'not-significant'}`}>
                    {formatPValue(pw.adjusted_p_value)}
                  </span>
                </td>
                <td className="cell-score" style={{ textAlign: 'right' }}>{pw.ranking_score.toFixed(4)}</td>
                <td style={{ textAlign: 'center' }}>
                  <button
                    className="expand-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      setExpandedRow(expandedRow === pw.pathway_id ? null : pw.pathway_id);
                    }}
                  >
                    {expandedRow === pw.pathway_id ? '▲' : '▼'} Genes
                  </button>
                </td>
              </tr>
              {expandedRow === pw.pathway_id && (
                <tr key={`${pw.pathway_id}-expand`}>
                  <td colSpan={COLUMNS.length + 1} style={{ padding: 0 }}>
                    <div className="expandable-content">
                      <p style={{ fontSize: '0.8125rem', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
                        Contributing genes ({pw.contributing_genes.length}):
                      </p>
                      <div className="gene-tags">
                        {pw.contributing_genes.map(g => (
                          <span key={g} className="gene-tag">{g}</span>
                        ))}
                      </div>
                    </div>
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
}

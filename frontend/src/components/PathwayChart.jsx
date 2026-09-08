import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

function getBarColor(adjPValue) {
  if (adjPValue < 0.001) return '#1a5276';
  if (adjPValue < 0.01) return '#2e86c1';
  if (adjPValue < 0.05) return '#5dade2';
  return '#aed6f1';
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: 'white', border: '1px solid #e2e8f0', borderRadius: '8px',
      padding: '12px 16px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
      fontSize: '0.8125rem', maxWidth: '320px',
    }}>
      <p style={{ fontWeight: 600, marginBottom: '4px' }}>{d.name}</p>
      <p style={{ color: '#64748b', fontSize: '0.75rem' }}>
        Ranking Score: <strong>{d.ranking_score.toFixed(4)}</strong><br />
        Pathway Score: {d.pathway_score.toFixed(4)}<br />
        Adjusted p-value: {d.adjusted_p_value.toExponential(2)}<br />
        Input genes: {d.input_gene_count} &nbsp;|&nbsp; Pathway genes: {d.total_pathway_genes}<br />
        Contributing: {d.contributing_genes.join(', ')}
      </p>
    </div>
  );
}

export default function PathwayChart({ pathways }) {
  // Prepare data for horizontal bar chart (reversed for display)
  const chartData = [...pathways]
    .reverse()
    .map(p => ({
      ...p,
      name: p.pathway_name.length > 38
        ? p.pathway_name.substring(0, 35) + '...'
        : p.pathway_name,
      fullName: p.pathway_name,
    }));

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 10, right: 60, left: 10, bottom: 10 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
          <XAxis
            type="number"
            label={{ value: 'Ranking Score', position: 'insideBottom', offset: -5, style: { fontSize: 12 } }}
            tick={{ fontSize: 11 }}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={260}
            tick={{ fontSize: 10.5 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="ranking_score" name="Ranking Score" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={index} fill={getBarColor(entry.adjusted_p_value)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div style={{
        display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '0.5rem',
        fontSize: '0.6875rem', color: 'var(--color-text-secondary)',
      }}>
        {[
          { color: '#1a5276', label: 'p_adj < 0.001' },
          { color: '#2e86c1', label: 'p_adj < 0.01' },
          { color: '#5dade2', label: 'p_adj < 0.05' },
          { color: '#aed6f1', label: 'p_adj ≥ 0.05' },
        ].map(({ color, label }) => (
          <span key={label} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: 12, height: 12, borderRadius: 3, background: color, display: 'inline-block' }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

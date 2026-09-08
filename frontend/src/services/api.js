/**
 * API service for communicating with the KEGGPathRank backend.
 * 
 * All backend HTTP calls are centralized here.
 */

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

/**
 * Run pathway enrichment analysis.
 * @param {string[]} genes - Gene symbols
 * @param {string} organism - KEGG organism code
 * @returns {Promise<Object>} Analysis response
 */
export async function analyzeGenes(genes, organism = 'hsa') {
  const resp = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ genes, organism }),
  });

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(
      err?.detail?.message || err?.message || `Analysis failed (HTTP ${resp.status})`
    );
  }

  return resp.json();
}

/**
 * Get detailed information about a specific pathway.
 * @param {string} pathwayId - KEGG pathway ID
 * @returns {Promise<Object>} Pathway details
 */
export async function getPathwayDetail(pathwayId) {
  const resp = await fetch(`${API_BASE}/pathway/${pathwayId}`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch pathway details (HTTP ${resp.status})`);
  }
  return resp.json();
}

/**
 * Check backend health status.
 * @returns {Promise<Object>} Health status
 */
export async function checkHealth() {
  const resp = await fetch(`${API_BASE}/health`);
  return resp.json();
}

/**
 * Get supported organisms.
 * @returns {Promise<Object>} Map of organism code → name
 */
export async function getOrganisms() {
  const resp = await fetch(`${API_BASE}/organisms`);
  return resp.json();
}

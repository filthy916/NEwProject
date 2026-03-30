const crypto = require('crypto');

// Simple in-memory proof vault. Replace with persistent DB in production.
const store = new Map();

function createProof(evidence) {
  const ts = new Date().toISOString();
  const payload = { evidence, ts };
  const hash = crypto.createHash('sha256').update(JSON.stringify(payload)).digest('hex');
  store.set(hash, payload);
  return { proofHash: hash, ts };
}

function verifyProof(hash) {
  return store.has(hash) ? { valid: true, payload: store.get(hash) } : { valid: false };
}

module.exports = { createProof, verifyProof, _store: store };

const fetch = require('node-fetch');
const proofVault = require('../services/proofVault');

module.exports = {
  id: 'cert-transparency',
  name: 'Cert Transparency (crt.sh)',
  description: 'Fetch certificates from crt.sh for a domain',
  run: async function (input) {
    const domain = input && input.domain;
    if (!domain) return { success: false, error: 'domain required' };
    try {
      const url = `https://crt.sh/?q=${encodeURIComponent(domain)}&output=json`;
      const resp = await fetch(url);
      if (!resp.ok) return { success: false, error: `upstream ${resp.status}` };
      const body = await resp.text();
      let entries = [];
      try { entries = JSON.parse(body); } catch (e) { entries = []; }
      const evidence = { rawResponse: body.slice(0, 10000), count: entries.length };
      const proof = proofVault.createProof({ moduleId: 'cert-transparency', action: 'fetch', input: { domain }, output: evidence });
      return { success: true, entries, evidence, proofHash: proof.proofHash };
    } catch (err) {
      return { success: false, error: String(err) };
    }
  }
};

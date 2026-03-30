require('dotenv').config();
const express = require('express');
const path = require('path');
const proofVault = require('./services/proofVault');
const authGate = require('./middleware/authGate');
const certaintyGate = require('./middleware/certaintyGate');

const app = express();
app.use(express.json());
app.use(authGate);

app.get('/api/health', (req, res) => res.json({ status: 'ok' }));

app.post('/api/modules', certaintyGate, async (req, res) => {
  const { module: moduleName, input } = req.body;
  if (!moduleName) return res.status(400).json({ error: 'module required' });
  try {
    const modPath = path.join(__dirname, 'modules', moduleName + '.js');
    const mod = require(modPath);
    const result = await mod.run(input || {});
    if (result && (result.evidence || result.rawResponse || result.proofHash)) {
      const proof = proofVault.createProof({ moduleId: mod.id || moduleName, input, output: result });
      result.proof = proof;
    }
    res.json({ success: true, module: moduleName, result, verifiedMode: req.verifiedMode });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, error: String(err) });
  }
});

app.post('/api/modules/batch', certaintyGate, async (req, res) => {
  const { modules } = req.body; // [{module, input}]
  if (!Array.isArray(modules)) return res.status(400).json({ error: 'modules array required' });
  const out = [];
  for (const m of modules) {
    try {
      const modPath = path.join(__dirname, 'modules', m.module + '.js');
      const mod = require(modPath);
      const result = await mod.run(m.input || {});
      if (result && (result.evidence || result.rawResponse || result.proofHash)) {
        const proof = proofVault.createProof({ moduleId: mod.id || m.module, input: m.input, output: result });
        result.proof = proof;
      }
      out.push({ module: m.module, success: true, result });
    } catch (err) {
      out.push({ module: m.module, success: false, error: String(err) });
    }
  }
  res.json({ results: out, verifiedMode: req.verifiedMode });
});

// AI analyze endpoint (uses certainty gate to detect verified mode)
app.post('/api/ai/analyze-threat', certaintyGate, async (req, res) => {
  // placeholder: in real code this would call AI services (Azure OpenAI / Groq)
  if (req.verifiedMode) {
    return res.json({ mode: 'verified', message: 'AI analysis placeholder (verified)' });
  }
  return res.json({ mode: 'discovery', message: 'AI analysis placeholder (discovery)' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log('CyberDork core listening on', PORT));

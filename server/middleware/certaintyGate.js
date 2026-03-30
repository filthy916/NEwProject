const proofVault = require('../services/proofVault');

module.exports = async function certaintyGate(req, res, next) {
  // If body contains proofHash, verify it and set req.verifiedMode
  const proofHash = req.body && req.body.proofHash || req.headers['x-proof-hash'] || req.query.proof_hash;
  if (!proofHash) {
    req.verifiedMode = false;
    return next();
  }
  const v = proofVault.verifyProof(proofHash);
  req.verifiedMode = v && v.valid;
  req.proofPayload = v && v.payload;
  return next();
};

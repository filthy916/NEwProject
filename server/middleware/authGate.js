require('dotenv').config();

module.exports = function authGate(req, res, next) {
  const access = process.env.ACCESS_CODE;
  const provided = req.headers['x-access-code'] || req.query.access_code || (req.body && req.body.access_code);
  if (!access) return next(); // no gate configured
  if (provided === access) return next();
  return res.status(401).json({ error: 'unauthorized' });
};

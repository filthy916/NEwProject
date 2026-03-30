const fetch = require('node-fetch');
const target = process.env.ACRG_TARGET || 'example.com';

(async () => {
  try {
    const resp = await fetch('http://localhost:3000/api/modules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ module: 'certTransparency', input: { domain: target } })
    });
    const json = await resp.json();
    console.log(JSON.stringify(json, null, 2));
    process.exit(0);
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
})();

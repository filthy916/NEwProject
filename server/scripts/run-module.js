const mod = require('../modules/certTransparency');

(async () => {
  try {
    const out = await mod.run({ domain: process.argv[2] || 'example.com' });
    console.log(JSON.stringify(out, null, 2));
    process.exit(0);
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
})();

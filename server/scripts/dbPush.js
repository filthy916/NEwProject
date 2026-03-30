const { Client } = require('pg');
require('dotenv').config();

const sql = `
CREATE TABLE IF NOT EXISTS proofs (
  proof_hash TEXT PRIMARY KEY,
  payload JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS findings (
  id SERIAL PRIMARY KEY,
  module_id TEXT NOT NULL,
  input JSONB,
  output JSONB,
  proof_hash TEXT REFERENCES proofs(proof_hash),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
`;

async function run() {
  const client = new Client({ connectionString: process.env.DATABASE_URL });
  try {
    await client.connect();
    await client.query(sql);
    console.log('DB: tables created/verified');
  } catch (err) {
    console.error('DB error', err);
    process.exit(1);
  } finally {
    await client.end();
  }
}

run();

#!/usr/bin/env node

const { spawn, spawnSync } = require("child_process");

const isWindows = process.platform === "win32";

function canRun(command, args = ["--version"]) {
  const result = spawnSync(command, args, {
    stdio: "ignore",
    shell: false,
  });
  return result.status === 0;
}

function resolveStartCommand() {
  if (canRun("uv")) {
    return {
      command: "uv",
      args: ["run", "--with-requirements", "requirements.txt", "python", "server.py"],
    };
  }

  const pythonCandidates = isWindows
    ? ["python", "py", "python3"]
    : ["python3", "python"];

  for (const cmd of pythonCandidates) {
    if (canRun(cmd)) {
      return { command: cmd, args: ["server.py"] };
    }
  }

  return null;
}

const startCommand = resolveStartCommand();

if (!startCommand) {
  console.error(
    "Unable to find a Python runtime. Install Python (or uv) and try again."
  );
  process.exit(1);
}

const child = spawn(startCommand.command, startCommand.args, {
  stdio: "inherit",
  shell: false,
  env: process.env,
});

child.on("exit", (code) => {
  process.exit(code ?? 1);
});

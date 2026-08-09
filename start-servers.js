const { spawn, execSync } = require('child_process');
const readline = require('readline');
const net = require('net');
const fs = require('fs');
const path = require('path');

// 1. Load env variables from root .env if it exists
function loadEnv() {
  const envPath = path.join(__dirname, '.env');
  if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, 'utf-8');
    for (const line of content.split('\n')) {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const parts = trimmed.split('=');
        if (parts.length >= 2) {
          const key = parts[0].trim();
          const value = parts.slice(1).join('=').trim();
          process.env[key] = value;
        }
      }
    }
  }
}

loadEnv();

const BACKEND_PORT = process.env.BACKEND_PORT ? parseInt(process.env.BACKEND_PORT, 10) : 8000;
const FRONTEND_PORT = process.env.FRONTEND_PORT ? parseInt(process.env.FRONTEND_PORT, 10) : 5173;

function checkPort(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        resolve(false); // Port is occupied
      } else {
        resolve(true); // Other error, assume port is not strictly occupied
      }
    });
    server.once('listening', () => {
      server.close();
      resolve(true); // Port is free
    });
    server.listen(port, '127.0.0.1');
  });
}

function getPidsForPort(port) {
  try {
    const output = execSync(`netstat -ano`).toString();
    const lines = output.split('\n');
    const pids = [];
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.includes('LISTENING')) continue;
      
      const parts = trimmed.split(/\s+/);
      if (parts.length >= 5 && parts[0].toUpperCase() === 'TCP') {
        const localAddr = parts[1];
        const lastColon = localAddr.lastIndexOf(':');
        if (lastColon !== -1) {
          const localPort = parseInt(localAddr.substring(lastColon + 1), 10);
          if (localPort === port) {
            const pid = parseInt(parts[parts.length - 1], 10);
            if (pid && !isNaN(pid)) {
              pids.push(pid);
            }
          }
        }
      }
    }
    return [...new Set(pids)];
  } catch (err) {
    return [];
  }
}

function killPid(pid) {
  try {
    console.log(`\x1b[33m[system] Attempting to kill process tree PID ${pid} occupying port...\x1b[0m`);
    if (process.platform === 'win32') {
      execSync(`taskkill /F /T /PID ${pid}`);
    } else {
      process.kill(pid, 'SIGKILL');
    }
    console.log(`\x1b[32m[system] Successfully killed PID ${pid}\x1b[0m`);
    return true;
  } catch (err) {
    console.log(`\x1b[33m[system] Process PID ${pid} could not be killed (may already be terminated).\x1b[0m`);
    return false;
  }
}

async function checkAndCleanPort(port) {
  let attempts = 0;
  while (attempts < 3) {
    const isFree = await checkPort(port);
    if (isFree) {
      return true;
    }
    console.log(`\x1b[33m[system] Port ${port} is occupied. Scanning for active processes...\x1b[0m`);
    const pids = getPidsForPort(port);
    if (pids.length === 0) {
      console.log(`\x1b[31m[system] Port ${port} is occupied, but no active PIDs could be found via netstat.\x1b[0m`);
      await new Promise(r => setTimeout(r, 1000));
      attempts++;
      continue;
    }
    for (const pid of pids) {
      killPid(pid);
    }
    await new Promise(r => setTimeout(r, 1000));
    attempts++;
  }
  return await checkPort(port);
}

function prefixLog(stream, prefix, colorCode) {
  const rl = readline.createInterface({ input: stream });
  rl.on('line', (line) => {
    console.log(`${colorCode}${prefix}\x1b[0m ${line}`);
  });
}

async function main() {
  console.log('\x1b[35m[system] Running port occupancy checks and cleaning up...\x1b[0m');
  
  const backendClean = await checkAndCleanPort(BACKEND_PORT);
  const frontendClean = await checkAndCleanPort(FRONTEND_PORT);

  if (!backendClean) {
    console.error(`\x1b[31m[ERROR] Port ${BACKEND_PORT} is already in use and could not be freed.\x1b[0m`);
    process.exit(1);
  }

  if (!frontendClean) {
    console.error(`\x1b[31m[ERROR] Port ${FRONTEND_PORT} is already in use and could not be freed.\x1b[0m`);
    process.exit(1);
  }

  // Synchronize frontend/.env's VITE_API_BASE_URL
  const frontendEnvPath = path.join(__dirname, 'frontend', '.env');
  try {
    fs.writeFileSync(frontendEnvPath, `VITE_API_BASE_URL=http://localhost:${BACKEND_PORT}\n`);
    console.log(`\x1b[32m[system] Synchronized frontend/.env with VITE_API_BASE_URL=http://localhost:${BACKEND_PORT}\x1b[0m`);
  } catch (err) {
    console.error(`\x1b[31m[system] Failed to sync frontend/.env: ${err.message}\x1b[0m`);
  }

  console.log(`\x1b[35m[system] Ports ${BACKEND_PORT} and ${FRONTEND_PORT} are free. Starting servers...\x1b[0m`);

  // Spawn backend (FastAPI uvicorn)
  const backendProcess = spawn(
    'uvicorn',
    ['app.main:app', '--host', '127.0.0.1', '--port', BACKEND_PORT.toString(), '--reload'],
    { 
      shell: true,
      env: {
        ...process.env,
        PORT: BACKEND_PORT.toString(),
        BACKEND_PORT: BACKEND_PORT.toString(),
        FRONTEND_PORT: FRONTEND_PORT.toString()
      }
    }
  );

  // Spawn frontend (Vite dev server)
  const frontendProcess = spawn(
    'npm',
    ['run', 'dev', '--prefix', 'frontend', '--', '--port', FRONTEND_PORT.toString(), '--strictPort'],
    { 
      shell: true,
      env: {
        ...process.env,
        BACKEND_PORT: BACKEND_PORT.toString(),
        FRONTEND_PORT: FRONTEND_PORT.toString()
      }
    }
  );

  // Set up prefix logging
  prefixLog(backendProcess.stdout, '[backend]', '\x1b[36m'); // Cyan
  prefixLog(backendProcess.stderr, '[backend]', '\x1b[36m'); // Cyan
  prefixLog(frontendProcess.stdout, '[frontend]', '\x1b[32m'); // Green
  prefixLog(frontendProcess.stderr, '[frontend]', '\x1b[32m'); // Green

  // Handle termination gracefully
  const cleanUp = () => {
    console.log('\n\x1b[35m[system] Terminating servers...\x1b[0m');
    if (process.platform === 'win32') {
      try {
        if (backendProcess && backendProcess.pid) {
          console.log(`\x1b[33m[system] Killing backend process tree (PID ${backendProcess.pid})...\x1b[0m`);
          execSync(`taskkill /F /T /PID ${backendProcess.pid}`);
        }
      } catch (err) {}
      try {
        if (frontendProcess && frontendProcess.pid) {
          console.log(`\x1b[33m[system] Killing frontend process tree (PID ${frontendProcess.pid})...\x1b[0m`);
          execSync(`taskkill /F /T /PID ${frontendProcess.pid}`);
        }
      } catch (err) {}
    } else {
      if (backendProcess) backendProcess.kill('SIGINT');
      if (frontendProcess) frontendProcess.kill('SIGINT');
    }
    process.exit();
  };

  process.on('SIGINT', cleanUp);
  process.on('SIGTERM', cleanUp);
}

main().catch((err) => {
  console.error('\x1b[31m[system] Startup failed:\x1b[0m', err);
  process.exit(1);
});

import { spawn } from 'node:child_process';
const children = [spawn('.venv/bin/python', ['-m', 'uvicorn', 'server:app', '--app-dir', 'research', '--reload', '--reload-dir', 'research', '--host', '127.0.0.1', '--port', '5192'], { stdio: 'inherit' }), spawn('node_modules/.bin/vite', [], { stdio: 'inherit' })];
let stopping = false;
function stop(code = 0) { if (stopping) return; stopping = true; children.forEach(child => child.kill('SIGTERM')); process.exitCode = code; }
for (const child of children) { child.on('error', error => { console.error(error.message); stop(1); }); child.on('exit', code => stop(code || 0)); }
process.on('SIGINT', () => stop()); process.on('SIGTERM', () => stop());

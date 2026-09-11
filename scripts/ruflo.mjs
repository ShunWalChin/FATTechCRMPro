import { spawn } from 'node:child_process';
import { existsSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const binary = resolve(root, '.local/tooling/node_modules/ruflo/bin/ruflo.js');
const workspace = resolve(root, '.local/engineering');
if (!existsSync(binary)) {
  console.error('Install pinned Ruflo: npm install --prefix .local/tooling --save-exact ruflo@3.41.2');
  process.exit(1);
}
mkdirSync(workspace, { recursive: true });
const child = spawn(process.execPath, [binary, ...process.argv.slice(2)], {
  cwd: workspace,
  stdio: 'inherit',
  windowsHide: true,
  env: { ...process.env, RUFLO_NO_SKILLS_SH: '1' },
});
child.on('error', (error) => { console.error(error.message); process.exit(1); });
child.on('exit', (code) => process.exit(code ?? 1));
process.on('SIGINT', () => child.kill('SIGINT'));
process.on('SIGTERM', () => child.kill('SIGTERM'));

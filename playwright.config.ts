import {defineConfig, devices} from '@playwright/test';
const python = process.env.E2E_PYTHON || (process.platform === 'win32' ? 'apps\\api\\.venv\\Scripts\\python.exe' : 'apps/api/.venv/bin/python');
export default defineConfig({
  testDir: './tests/e2e',
  // O servidor de desenvolvimento compila cada rota na primeira visita, e o workspace passou de
  // dezesseis para vinte telas. O que estourava o limite era compilacao, nao lentidao do produto:
  // baixar o limite de volta so devolveria falhas que passam quando rodam sozinhas.
  timeout: 90_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['html', {open: 'never'}]],
  use: {baseURL: 'http://127.0.0.1:3100', trace: 'retain-on-failure', screenshot: 'only-on-failure'},
  projects: [{name: 'chromium', use: {...devices['Desktop Chrome']}}],
  webServer: [
    {command: `${python} scripts/e2e-api.py`, url: 'http://127.0.0.1:8100/api/health', timeout: 90_000, reuseExistingServer: false},
    {command: 'npm run dev --workspace @fattech/web -- --port 3100', url: 'http://127.0.0.1:3100', timeout: 120_000,
      env: {API_INTERNAL_URL: 'http://127.0.0.1:8100', NEXT_PUBLIC_SITE_URL: 'http://127.0.0.1:3100'}, reuseExistingServer: false},
  ],
});

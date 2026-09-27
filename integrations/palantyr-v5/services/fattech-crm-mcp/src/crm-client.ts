/**
 * Cliente HTTP da superfície `/api/v1/agent/*` do FAT Tech CRM Pro.
 *
 * Regras de retentativa — decididas pelo efeito, não pela conveniência:
 *   - GET: pode repetir em 408/425/429/5xx e erro de rede (não muda estado).
 *   - POST: NUNCA repete sozinho. `act` grava um passo a cada chamada e `claim`
 *     move corridas para `planning`; repetir às cegas duplicaria passo ou
 *     prenderia corrida. O agente decide, com o erro na mão.
 *
 * Recusa do portão NÃO é erro: `POST /agent/act` devolve 200 com
 * `decision: refused | suggested | approval_required`. Só erro de protocolo
 * (401/403/404/409/422/5xx) vira `CrmHttpError`.
 */
import type { CrmConfig } from "./config.js";

export class CrmHttpError extends Error {
  constructor(
    readonly status: number,
    readonly detail: unknown,
    readonly method: string,
    readonly path: string,
  ) {
    super(`CRM ${method} ${path} → ${status}: ${typeof detail === "string" ? detail : JSON.stringify(detail)}`);
    this.name = "CrmHttpError";
  }
}

const RETRYABLE = new Set([408, 425, 429, 500, 502, 503, 504]);

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

export interface RunSummary {
  id: string;
  agent_id: string;
  mode: string;
  status: string;
  trigger_type: string;
  trigger_event_id: string;
  [key: string]: unknown;
}

export interface ActResult {
  run_id: string;
  seq: number;
  tool: string;
  decision: "allowed" | "refused" | "suggested" | "approval_required";
  refusal_reason: string;
  result_ref: string;
  result: unknown;
  step_id: string;
  nota: string;
}

export interface FinishPayload {
  status: "done" | "failed" | "degraded" | "refused";
  tokens_in?: number;
  tokens_out?: number;
  cost_cents?: number;
  error?: string;
}

export class CrmClient {
  constructor(
    private readonly config: CrmConfig,
    private readonly fetchImpl: FetchLike = globalThis.fetch.bind(globalThis),
    private readonly sleep: (ms: number) => Promise<void> = (ms) => new Promise((r) => setTimeout(r, ms)),
  ) {}

  get agentId(): string {
    return this.config.agentId;
  }

  // ---- leitura --------------------------------------------------------------

  catalog(): Promise<unknown> {
    return this.get("/api/v1/agent/tools");
  }

  /** Outra fila só é visível com escopo agent:observe e agents.read no CRM. */
  queue(agentId: string = this.config.agentId): Promise<unknown> {
    return this.get(`/api/v1/agent/${encodeURIComponent(agentId)}/queue`);
  }

  budget(): Promise<unknown> {
    return this.get(`/api/v1/agent/${encodeURIComponent(this.config.agentId)}/budget`);
  }

  run(runId: string): Promise<unknown> {
    return this.get(`/api/v1/agent/runs/${encodeURIComponent(runId)}`);
  }

  // ---- escrita (sem retentativa automática) ---------------------------------

  claim(limit: number): Promise<{ items: RunSummary[]; total: number; fila: unknown }> {
    return this.post("/api/v1/agent/runs/claim", { agent_id: this.config.agentId, limit });
  }

  openRun(input: { trigger_event_id: string; trigger_type: string; rationale: string; model?: string }): Promise<RunSummary & { replay: boolean }> {
    return this.post("/api/v1/agent/runs", { agent_id: this.config.agentId, ...input });
  }

  act(input: { run_id: string; tool: string; arguments: Record<string, unknown> }): Promise<ActResult> {
    return this.post("/api/v1/agent/act", input);
  }

  finish(runId: string, payload: FinishPayload): Promise<RunSummary> {
    return this.post(`/api/v1/agent/runs/${encodeURIComponent(runId)}/finish`, payload);
  }

  // ---- transporte -----------------------------------------------------------

  private headers(): Record<string, string> {
    return {
      Authorization: `Bearer ${this.config.apiKey}`,
      Accept: "application/json",
      "Content-Type": "application/json",
      "User-Agent": "palantyr-fattech-crm-mcp/1.0",
    };
  }

  private async get<T>(path: string): Promise<T> {
    const attempts = 3;
    let lastError: unknown;
    for (let attempt = 1; attempt <= attempts; attempt++) {
      try {
        return await this.request<T>("GET", path);
      } catch (error) {
        lastError = error;
        const retryable = error instanceof CrmHttpError ? RETRYABLE.has(error.status) : true;
        if (!retryable || attempt === attempts) throw error;
        await this.sleep(250 * 2 ** (attempt - 1));
      }
    }
    throw lastError;
  }

  private post<T>(path: string, body: unknown): Promise<T> {
    return this.request<T>("POST", path, body);
  }

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.config.timeoutMs);
    try {
      const response = await this.fetchImpl(`${this.config.baseUrl}${path}`, {
        method,
        headers: this.headers(),
        body: body === undefined ? undefined : JSON.stringify(body),
        signal: controller.signal,
        redirect: "error",
      });
      const text = await response.text();
      let parsed: unknown = text;
      if (text) {
        try {
          parsed = JSON.parse(text);
        } catch {
          parsed = text.slice(0, 2000);
        }
      }
      if (!response.ok) {
        const detail = (parsed as { detail?: unknown } | null)?.detail ?? parsed;
        throw new CrmHttpError(response.status, detail, method, path);
      }
      return parsed as T;
    } finally {
      clearTimeout(timer);
    }
  }
}

/**
 * Configuração lida do ambiente, validada uma vez na partida.
 *
 * Falha cedo e com motivo: um servidor MCP que sobe sem chave "funciona" até a
 * primeira chamada e devolve 401 no meio de uma corrida do agente. Melhor recusar
 * a partida — o `openclaw doctor` mostra o erro antes de qualquer turno.
 */
export interface CrmConfig {
  /** URL interna da API do CRM (rede Docker `fattechcrmpro-network`). */
  baseUrl: string;
  /** Chave de API do agente — escopo `agent:operate` + escopos das ferramentas. */
  apiKey: string;
  /** Identidade do agente no CRM (records.kind='agents'). Fixa por processo. */
  agentId: string;
  /** Timeout de cada requisição HTTP, em ms. */
  timeoutMs: number;
  /** Teto local de tentativas por minuto — defesa em profundidade; o teto real é do CRM. */
  maxActsPerMinute: number;
}

function required(env: NodeJS.ProcessEnv, name: string): string {
  const value = env[name]?.trim();
  if (!value) {
    throw new Error(`Variável obrigatória ausente: ${name}`);
  }
  return value;
}

function positiveInt(raw: string | undefined, fallback: number, name: string): number {
  if (raw === undefined || raw.trim() === "") return fallback;
  const value = Number(raw);
  if (!Number.isInteger(value) || value <= 0) {
    throw new Error(`${name} precisa ser inteiro positivo; recebido: ${raw}`);
  }
  return value;
}

export function loadCrmConfig(env: NodeJS.ProcessEnv = process.env): CrmConfig {
  const baseUrl = required(env, "FATTECH_CRM_BASE_URL").replace(/\/+$/, "");
  const parsed = new URL(baseUrl);
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error(`FATTECH_CRM_BASE_URL precisa ser http(s): ${baseUrl}`);
  }
  const agentId = required(env, "FATTECH_CRM_AGENT_ID");
  if (agentId.length > 36) {
    throw new Error("FATTECH_CRM_AGENT_ID excede 36 caracteres (limite do CRM)");
  }
  return {
    baseUrl,
    apiKey: required(env, "FATTECH_CRM_API_KEY"),
    agentId,
    timeoutMs: positiveInt(env.FATTECH_CRM_TIMEOUT_MS, 20_000, "FATTECH_CRM_TIMEOUT_MS"),
    maxActsPerMinute: positiveInt(env.FATTECH_CRM_MAX_ACTS_PER_MINUTE, 30, "FATTECH_CRM_MAX_ACTS_PER_MINUTE"),
  };
}

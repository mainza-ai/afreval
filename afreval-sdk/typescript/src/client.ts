// Client API shape for the AfrEval SaaS surface (Phase C — afreval-api).
// Mirrors the Python SDK: certify / securityReport / compliance.

export interface HarnessPins {
  afri_fertility_pin: string;
  afrobench_lite_pin: string;
  waxal_pin: string;
}

export interface CertRequest {
  modelId: string;
  waxalMacroWer: number;
  afrobenchLiteAccuracy: number;
  biasCorrectedJudgeScore: number;
  meanFertilityPremium: number;
  harnessPins: HarnessPins;
  weightsYaml: string;
}

export interface Cert {
  modelId: string;
  vertical: string;
  contextScore: number;
  linguisticFidelity: number;
  culturalSafety: number;
  structuralEconomics: number;
  pass: boolean;
  certSha256: string;
}

// Phase C API: the /v1/certify contract (auto-inputs pulls WER from the
// frozen QA baseline and the judge from §3.3 bias correction server-side).
export interface CertifyApiRequest {
  model_id: string;
  weights_yaml?: string;
  tokenizer_candidate?: string;
  auto_inputs?: boolean;
  bias_corrected_judge_score?: number;
}

export interface CertifyApiResponse {
  model: string;
  context_score: number;
  vectors: { linguistic_fidelity: number; cultural_safety: number; structural_economics: number };
  pass_: boolean;
  cert_sha256: string;
  bias_correction?: Record<string, unknown> | null;
  input_sources?: Record<string, string> | null;
  profile?: {
    languages: Record<string, { fertility: number; cpt: number; premium: number; wer?: number }>;
    scripts: Record<string, number>;
    dimensions: Record<string, number>;
    as_of: string;
    re_cert_after: string | null;
  } | null;
  methodology?: Record<string, unknown> | null;
  rubric_manifest?: Record<string, unknown> | null;
}

export interface SecurityReport {
  timestamp: string;
  totalVariants: number;
  totalBypasses: number;
  perSeam: Record<string, { total: number; bypasses: number; rate: number }>;
}

export class AfrevalClient {
  private readonly fetchImpl: typeof fetch;

  constructor(
    private readonly baseUrl: string,
    opts?: { fetch?: typeof fetch },
  ) {
    this.fetchImpl = opts?.fetch ?? fetch;
  }

  /** Full certification run via the Phase C API (auto-inputs by default). */
  async certifyApi(req: CertifyApiRequest): Promise<CertifyApiResponse> {
    return this.post("/v1/certify", req);
  }

  async securityReport(): Promise<SecurityReport> {
    return this.get("/v1/security");
  }

  async compliance(): Promise<{ exit: number; lines: string[]; current: boolean }> {
    return this.get("/v1/compliance");
  }

  async listCerts(): Promise<{ certifications: Array<Record<string, unknown>>; count: number }> {
    return this.get("/v1/certs");
  }

  async getCert(shaOrModel: string): Promise<Record<string, unknown>> {
    return this.get(`/v1/certs/${encodeURIComponent(shaOrModel)}`);
  }

  async diff(base: string, target: string): Promise<Record<string, unknown>> {
    return this.get(`/v1/diff?base=${encodeURIComponent(base)}&target=${encodeURIComponent(target)}`);
  }

  async staleCerts(): Promise<{ stale: Array<Record<string, unknown>>; count: number }> {
    return this.get("/v1/certs/stale");
  }

  private async post<T>(path: string, body: unknown): Promise<T> {
    const r = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      throw new Error(`POST ${path} failed: HTTP ${r.status}`);
    }
    return r.json() as Promise<T>;
  }

  private async get<T>(path: string): Promise<T> {
    const r = await this.fetchImpl(`${this.baseUrl}${path}`);
    if (!r.ok) {
      throw new Error(`GET ${path} failed: HTTP ${r.status}`);
    }
    return r.json() as Promise<T>;
  }
}

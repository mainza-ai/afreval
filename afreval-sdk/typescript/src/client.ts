// Client API shape for the AfrEval SaaS surface (not yet live — Phase 5).
// Mirrors the Python SDK: certify / score / securityReport.

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

  async certify(req: CertRequest): Promise<Cert> {
    return this.post("/v1/certify", req);
  }

  async securityReport(): Promise<SecurityReport> {
    return this.get("/v1/security");
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
